import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD, shared
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from typing import Dict, List, cast, Optional
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from time import sleep
from typing import Any, Dict
from Script.lib.sdk_lib.user.exception import G_TIMEOUT_ALL
from Script.project_api.custom_vu.secded_vu.define import ErrorInjection

ENG2_WA = True


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.config_lun(normal_list=[0], em1_list=[])
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()
        self.fw_debug_mode_bkup = self.hw_setting.get_local_val(api.HwSettingField.FW_DEBUG_MODE)
        self.hw_setting.set_local_val(api.HwSettingField.FW_DEBUG_MODE, 0)
        self.hw_setting.set_to_device()

        # 各 ErrorInjection type 對應的 SRAM address range（用於 baseline / inject 後驗證）
        self.sram_test_address: Dict[ErrorInjection, int] = {}
        for error_injection in ErrorInjection:
            if error_injection == ErrorInjection.DISABLE_ERROR_INJECTION:
                continue
            elif error_injection == ErrorInjection.FIP_SRAM:
                addr = 0xF8E40000
            elif error_injection == ErrorInjection.RS_SRAM:
                addr = random.randint(0, 0)
            elif error_injection == ErrorInjection.COP0_SRAM:
                addr = random.randint(0x4C100000, 0x4C1FFFFF)
            elif error_injection == ErrorInjection.COP1_SRAM:
                addr = random.randint(0x4C200000, 0x4C2FFFFF)
            elif error_injection == ErrorInjection.BMU_SRAM:
                addr = random.randint(0xF8F0C000, 0xF8F0CFFF)
            elif error_injection == ErrorInjection.DBUF_SRAM:
                addr = random.randint(0xF8F81600, 0xF8F816FF)
            elif error_injection == ErrorInjection.SEC_SRAM:
                addr = random.randint(0xF8F81000, 0xF8F810FF)
            self.sram_test_address[error_injection] = addr
        pass

    def _get_first_enabled_lun(self) -> int:
        enablelun = 0
        for lunidx in range(shared.param.gMaxNumberLU):
            if shared.param.gUnit[lunidx].b3_lu_enable:
                enablelun = lunidx
                break
        return enablelun

    # ================================================================
    #  Private helpers
    # ================================================================

    def _handle_assert_and_recover(self, expected_assert_list: List[int]) -> None:
        """G_TIMEOUT_ALL 發生後：清 queue → 檢查 assert number 是否在預期清單中 → HW reset 回復"""
        ExecuteCMD.clear()
        assert_number = api.get_fw_assert_number()
        if assert_number not in expected_assert_list:
            logger.error_lb(f'check FW assert number after {self.__class__.__name__}')
            logger.error_fp(
                f'Enable assert, and send TM, expect assert number in '
                f'{[f"0x{x:04X}" for x in expected_assert_list]}, '
                f'but get = 0x{assert_number:04X}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f"FW assert number = 0x{assert_number:04X}, as expected")
        api.init_tester_to_unit_ready(
            resetmode=api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET),
            powerdown=False)

    def _inject_write_read_and_expect_assert(self, op_code: ErrorInjection) -> None:
        """通用流程：inject(keep_error=True) → sequential_write → read_compare → expect assert"""
        logger.info(f"issue 40BD to inject {op_code.name} error")
        project_api.issue_40BD_to_inject_SER_SECDED_event(
            opCode=op_code, keep_error=True)

        lun = self._get_first_enabled_lun()
        logger.info(f"sequential_write (lun={lun}) after {op_code.name} error injection")
        write_record = api.get_empty_write_record()
        api.sequential_write(lun=lun, start_lba=0,
                             total_size=api.BLOCK4K_SIZE_1G_BYTE,
                             chunk_size=api.WRITE_10_MAX_BLOCK_LEN,
                             fua=0, need_compare=False,
                             compare_method=api.CompareMethod.HW_COMPARE,
                             write_record=write_record)

        logger.info(f"read_compare after {op_code.name} error injection")
        api.read_compare(write_record=write_record)

    def _expect_read_success(self, error_type: ErrorInjection, addr: int) -> None:
        """預期 read_Xmemory 成功 (TARGET_SUCCESS / GOOD)"""
        response, data = read_Xmemory(sram_address=addr, keep_error=True)
        if response.upiu.b6_response != api.UPIUResponse.TARGET_SUCCESS:
            logger.error_lb(f'read_Xmemory after {error_type.name} (0x{addr:X})')
            logger.error_fp(
                f'expect TARGET_SUCCESS, but get response = {response.upiu.b6_response}, '
                f'status = {get_scsi_status_str(response)}, '
                f'sense_key = {get_sense_key_str(response)}, '
                f'asc = {get_asc_ascq_description(response)}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    # ================================================================
    #  Step 1 — DISABLE_ERROR_INJECTION (baseline, no assert)
    # ================================================================

    def step1(self) -> None:
        logger.flow(1, "DISABLE_ERROR_INJECTION: inject disable and read all SRAM regions")
        project_api.issue_40BD_to_inject_SER_SECDED_event(
            opCode=ErrorInjection.DISABLE_ERROR_INJECTION, keep_error=True)

        logger.info("read all SRAM regions, expect all succeed")
        for error_type, addr in self.sram_test_address.items():
            logger.info(f"read_Xmemory(0x{addr:X}) — {error_type.name}")
            self._expect_read_success(error_type, addr)
        pass

    # ================================================================
    #  Step 2 — RS_SRAM: inject error → host write → host read → assert
    # ================================================================

    def step2(self) -> None:
        logger.flow(2, "RS_SRAM: inject error, host write, host read, expect FW assert then HW reset")
        try:
            self._inject_write_read_and_expect_assert(ErrorInjection.RS_SRAM)
        except G_TIMEOUT_ALL:
            pass
        self._handle_assert_and_recover(expected_assert_list=[0xF501])

    # ================================================================
    #  Step 3 — COP0_SRAM: inject error → host write → host read → assert
    # ================================================================

    def step3(self) -> None:
        logger.flow(3, "COP0_SRAM: inject error, host write, host read, expect FW assert then HW reset")
        try:
            self._inject_write_read_and_expect_assert(ErrorInjection.COP0_SRAM)
        except G_TIMEOUT_ALL:
            pass
        self._handle_assert_and_recover(expected_assert_list=[0xF500])

    # ================================================================
    #  Step 4 — COP1_SRAM: inject error → host write → host read → assert
    # ================================================================

    def step4(self) -> None:
        logger.flow(4, "COP1_SRAM: inject error, host write, host read, expect FW assert then HW reset")
        try:
            self._inject_write_read_and_expect_assert(ErrorInjection.COP1_SRAM)
        except G_TIMEOUT_ALL:
            pass
        self._handle_assert_and_recover(expected_assert_list=[0xF502, 0xF503, 0xF504])

    # ================================================================
    #  Step 5 — BMU_SRAM: inject error → host write → host read → assert
    # ================================================================

    def step5(self) -> None:
        logger.flow(5, "BMU_SRAM: inject error, host write, host read, expect FW assert then HW reset")
        try:
            self._inject_write_read_and_expect_assert(ErrorInjection.BMU_SRAM)
        except G_TIMEOUT_ALL:
            pass
        self._handle_assert_and_recover(expected_assert_list=[0xF501])

    # ================================================================
    #  Step 6 — DBUF_SRAM: inject error → host write → host read → assert
    # ================================================================

    def step6(self) -> None:
        logger.flow(6, "DBUF_SRAM: inject error, host write, host read, expect FW assert then HW reset")
        try:
            self._inject_write_read_and_expect_assert(ErrorInjection.DBUF_SRAM)
        except G_TIMEOUT_ALL:
            pass
        self._handle_assert_and_recover(expected_assert_list=[0xF502, 0xF503, 0xF504])

    # ================================================================
    #  Step 7 — SEC_SRAM: inject → write_Xmemory 3 probes → at least one must assert
    # ================================================================

    def step7(self) -> None:
        logger.flow(7, "SEC_SRAM: inject error, write_Xmemory 3 probes, at least one must assert")
        
        try:
            project_api.issue_40BD_to_inject_SER_SECDED_event(
                    opCode=ErrorInjection.SEC_SRAM, keep_error=True)
            set_addr_dict = {0xF8F82810:0,
                                0xF8F83010:0,
                                0xF8F83810:0}
            logger.info(f"write_memory: {set_addr_dict}")
            self.write_memory_addr(set_addr_dict=set_addr_dict)

            # sec_probe_addresses = [0xF8F82810, 0xF8F83010, 0xF8F83810]
            # any_asserted = False
            # for idx, addr in enumerate(sec_probe_addresses):
            #     logger.info(f"write_Xmemory(0x{addr:X}) — probe {idx + 1}/3")
            #     data = bytearray(4096)
            #     response = write_Xmemory(sram_address=addr, data_buffer=data, keep_error=False)
            #     logger.info(f"probe 0x{addr:X} completed without assert")
        except G_TIMEOUT_ALL:
            logger.info(f"probe triggered FW assert")
            pass
        self._handle_assert_and_recover(expected_assert_list=[0xF500])
        pass

    # ================================================================
    #  Step 8 — FIP_SRAM: inject error → host write → host read → assert
    # ================================================================

    def step0(self) -> None:
        logger.flow(8, "FIP_SRAM: inject error, host write, host read, expect FW assert then HW reset")
        try:
            self._inject_write_read_and_expect_assert(ErrorInjection.FIP_SRAM)
        except G_TIMEOUT_ALL:
            pass
        self._handle_assert_and_recover(expected_assert_list=[0xF500])

    # ================================================================

    def post_process(self) -> None:
        self.hw_setting.update_from_device()
        self.hw_setting.set_local_val(api.HwSettingField.FW_DEBUG_MODE, self.fw_debug_mode_bkup)
        self.hw_setting.set_to_device()
        pass
    

    def write_memory_addr(self, set_addr_dict: Dict[int, int] = {}) -> None:
        data_out = bytearray(DATA_SIZE_4K_BYTE)
        count = len(set_addr_dict)
        if count > 511:
            count = 511
        data_out[1] = count & 0xFF
        data_out[2] = (count >> 8) & 0xFF
        base = 4
        for idx, (addr, value) in enumerate(set_addr_dict.items()):
            if idx >= count:
                break
            offset = base + idx * 8
            data_out[offset : offset + 4] = addr.to_bytes(4, 'little')
            data_out[offset + 4 : offset + 8] = value.to_bytes(4, 'little')            
        write_memory(data_buffer=data_out)
        
    def config_lun(self, normal_list:List[int], em1_list:List[int]) -> None:
        selector = 0x00
        length = 0xE6
        Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
        EM1_total_AU = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, Total_AU_Count//(len(normal_list) + len(em1_list)) * len(em1_list))
        normal_total_AU = Total_AU_Count//(len(normal_list) + len(em1_list)) * len(normal_list)
        for index in range(4):
            cmd = ExecuteCMD.WriteDescriptor()
            cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

            desc = api.ConfigDescriptor310()
            desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            desc.header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
            desc.header.b4_descr_access_en = api.DescrAccessEn.DISABLE
            desc.header.b5_init_power_mode = api.InitPowerMode.ACTIVE
            desc.header.b6_high_priority_lun = api.HighPriorityLUN.ALL_LUN_SAME_PRIORITY
            desc.header.b7_secure_removal_type = api.SecureRemovalType.BY_PHYSICAL_ERASE
            desc.header.b8_init_active_icc_level = api.InitActiveICCLevel.LVL_00
            desc.header.w9_periodic_rtc_update = 0
            desc.header.b11_hpb_control = 0
            desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE
            desc.header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
            desc.header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
            desc.header.l18_num_shared_write_booster_buffer_alloc_units = shared.param.gGeometry.l79_write_booster_buffer_max_n_alloc_units if index==0 else 0

            
            for unit_idx in range(8):
                lun = index * 8 + unit_idx
                if lun in normal_list:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                    desc.units[unit_idx].l4_num_alloc_units = (normal_total_AU) // len(normal_list)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif lun in em1_list:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = (EM1_total_AU) // len(em1_list)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                else:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.DISABLE
                    desc.units[unit_idx].l4_num_alloc_units = 0
                    desc.units[unit_idx].b9_logical_block_size = 0

            cmd.set_desc(desc)
            ExecuteCMD.enqueue(cmd)
            ExecuteCMD.send()
        unit_desc_idxes:List[int] = []
        for lun in range(0, shared.param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        for lun in range(shared.param.gMaxNumberLU):
            if shared.param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send()
        return


run = Pattern().run
if __name__ == "__main__":
    run()
