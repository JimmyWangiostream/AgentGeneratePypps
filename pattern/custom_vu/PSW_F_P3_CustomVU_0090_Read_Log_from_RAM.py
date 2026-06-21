import package_root
from collections import Counter
from typing import cast
from Script import api
from Script import project_api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.exception import *
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.project_api.custom_vu.read_log import issue_4082_read_log

_param = api.shared.param

LOG_UNIT_SIZE = 0x20
EXPECTED_UNIT_COUNT = 0x4000 // LOG_UNIT_SIZE
REQUIRED_NEW_LOG_IDS = {
    39: "EVENT_SOFTBIT",
    43: "EVENT_READ_DISTURB_REFRESH",
    45: "EVENT_RAID_RECOVERY",
    54: "EVEN_UFS_WRITE",
}


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.before_units: list[tuple[int, int, int]] = []
        self.after_units: list[tuple[int, int, int]] = []
        self.total_au = _param.gGeometry.q4_total_raw_device_capacity // (
            _param.gGeometry.l13_segment_size * _param.gGeometry.b17_allocation_unit_size
        )
        self.slc_lun, self.tlc_lun = self.config_lun(
            slc_au=self.total_au // 2,
            tlc_au=self.total_au // 2,
        )

        self.fw_geometry = api.get_fw_geometry()
        self.SLC_VB_4K_SIZE = (self.fw_geometry.l84_vb_size_u0 * 512) // api.DATA_SIZE_4K_BYTE

    def step1(self) -> None:
        logger.flow(1, "[Before] Read VU 4082 log headers from RAM")
        _, payload = issue_4082_read_log()
        self.before_units = self.dump_log_headers(payload, stage="before")

    def step2(self) -> None:
        logger.flow(2, "Trigger rain recovery event")
        self.trigger_rain_recovery_event()

    def step3(self) -> None:
        logger.flow(3, "[After] Read VU 4082 log headers from RAM")
        _, payload = issue_4082_read_log()
        self.after_units = self.dump_log_headers(payload, stage="after")
        added_log_ids = self.report_new_log_ids(self.before_units, self.after_units)
        self.check_expected_added_log_ids(added_log_ids)
    
    def post_process(self) -> None:
        pass

    def trigger_rain_recovery_event(self) -> None:
        logger.info("Step 1: Stop refresh to allow UECC injection")
        project_api.issue_C088_to_start_or_stop_refresh(
            bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue
        )

        logger.info("Step 2: Write data to SLC LUN 0 to create VB for UECC injection")
        self.write_data(
            lun=self.slc_lun,
            start_lba=0,
            len=api.WRITE_10_MAX_BLOCK_LEN,
            total_len=self.SLC_VB_4K_SIZE // 2,
        )

        logger.info("Step 3: Get PCA and inject UECC")
        pca = self.get_PCA_and_print(lun=self.slc_lun, lba=0)
        self.inject_UECC(pca, SLC_enable=True)

        logger.info("Step 4: Read to trigger UECC")
        self.read_data(lun=self.slc_lun, start_lba=0, len=1, total_len=1)

        logger.info("Step 5: Check booking queue has entries")
        _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
        booking_count = booking_q_before.LogicalVBNumberInBookingQueue.value
        logger.info(f"Booking queue entries before StartRefresh = {booking_count}")
        if booking_count == 0:
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION("Rain recovery did not enqueue any booking queue entry")

        logger.info("Step 6: Start refresh execution (triggers RAIN recovery)")
        project_api.issue_C088_to_start_or_stop_refresh(
            bParameter0=project_api.VUC088Paremeter.StartRefresh
        )

    def dump_log_headers(self, payload: bytearray, stage: str) -> list[tuple[int, int, int]]:
        total_units = len(payload) // LOG_UNIT_SIZE
        logger.info(
            f"[{stage}] VU 4082 payload size = {len(payload)} bytes, total_units = {total_units}, "
            f"expected_units = {EXPECTED_UNIT_COUNT}"
        )

        units: list[tuple[int, int, int]] = []
        for unit_index in range(total_units):
            start = unit_index * LOG_UNIT_SIZE
            timestamp = int.from_bytes(payload[start:start + 4], 'little')
            log_id = int.from_bytes(payload[start + 6:start + 8], 'little')
            units.append((unit_index, log_id, timestamp))

        logger.info(f"[{stage}] Dumped {len(units)} log headers from VU 4082 payload")
        return units

    def report_new_log_ids(
        self,
        before_units: list[tuple[int, int, int]],
        after_units: list[tuple[int, int, int]],
    ) -> dict[int, int]:
        logger.flow(4, "Compare VU 4082 before/after results")
        before_log_id_count = Counter(log_id for _, log_id, _ in before_units)
        after_log_id_count = Counter(log_id for _, log_id, _ in after_units)

        added_log_ids: list[tuple[int, int]] = []
        for log_id, count in after_log_id_count.items():
            added_count = count - before_log_id_count.get(log_id, 0)
            if added_count > 0:
                added_log_ids.append((log_id, added_count))

        if not added_log_ids:
            logger.info("No additional log_id found after rain recovery trigger")
            return {}

        for log_id, added_count in sorted(added_log_ids):
            event_name = REQUIRED_NEW_LOG_IDS.get(log_id, "UNKNOWN")
            logger.info(f"added_log_id={log_id} ({event_name}), added_count={added_count}")

        return {log_id: added_count for log_id, added_count in added_log_ids}

    def check_expected_added_log_ids(self, added_log_ids: dict[int, int]) -> None:
        logger.flow(5, "Check required new log IDs")

        found_log_ids: list[int] = []
        missing_log_ids: list[int] = []
        for log_id, event_name in REQUIRED_NEW_LOG_IDS.items():
            if log_id in added_log_ids:
                logger.info(f"found_log_id={log_id}, event={event_name}, added_count={added_log_ids[log_id]}")
                found_log_ids.append(log_id)
            else:
                logger.info(f"missing_log_id={log_id}, event={event_name}")
                missing_log_ids.append(log_id)

        required_count = len(REQUIRED_NEW_LOG_IDS)
        found_count = len(found_log_ids)
        logger.info(f"Found {found_count}/{required_count} required new log IDs")

        if not found_log_ids:
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION(
                f"No required new log IDs found after rain recovery trigger. Missing log IDs: {missing_log_ids}"
            )

    def write_data(self, lun: int, start_lba: int, len: int, total_len: int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            write10 = ExecuteCMD.Write10()
            logger.info(f"start lba = {start_lba}, len = {len}")
            write10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(write10)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

    def read_data(self, lun: int, start_lba: int, len: int, total_len: int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(read10)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

    def config_lun(self, slc_au: int, tlc_au: int) -> tuple[int, int]:
        config_descs = api.get_config_descriptors(print=True)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xC
                config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                if (table * 8 + unit) == 0:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                    config_descs[table].units[unit].l4_num_alloc_units = slc_au
                elif (table * 8 + unit) == 1:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[table].units[unit].l4_num_alloc_units = tlc_au

        config_descs[3].header.b2_conf_desc_continue = 0
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
        config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = _param.gGeometry.l79_write_booster_buffer_max_n_alloc_units
        for i in range(4):
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        ExecuteCMD.clear()

        unit_desc_idxes: list[int] = []
        for lun in range(0, _param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        for lun in range(_param.gMaxNumberLU):
            if _param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
        return 0, 1

    def get_PCA_and_print(self, lun: int, lba: int) -> project_api.physical_address_info:
        _, pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=lba)
        vb = pca.virtual_block_number.value
        die = pca.die.value
        plane = pca.plane.value
        block = pca.physical_block_number_w_BBT.value
        page = pca.page.value
        logger.info(
            f"Lun{lun}, LBA = {lba}: VB = {vb}, PhyBlock = {block}, CE = {die}, Plane = {plane}, Page = {page}"
        )
        return pca

    def inject_UECC(self, pca: project_api.physical_address_info, SLC_enable: bool = False) -> None:
        die = pca.die.value
        plane = pca.plane.value
        block = pca.physical_block_number_w_BBT.value
        page = pca.page.value
        logger.info(
            f"Inject UECC: PhyBlock = {block}, CE = {die}, Plane = {plane}, Page = {page}, "
            f"SLC_enable = {SLC_enable}"
        )
        if SLC_enable:
            direct_write_payload = bytearray(api.DATA_SIZE_16K_BYTE)
        else:
            direct_write_payload = bytearray(api.DATA_SIZE_20K_BYTE * 3)
        for i in range(len(direct_write_payload)):
            direct_write_payload[i] = 0xAA
        project_api.issue_C060_to_write_raw_data(
            Ce=die,
            Block=block,
            Plane=plane,
            Page=page,
            SLC_Enable=SLC_enable,
            Ecc_Enable=1,
            datapayload=direct_write_payload,
        )


run = Pattern().run
if __name__ == "__main__":
    run()
