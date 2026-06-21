import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from typing import Any, List, Tuple
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.rain.mutual_fun import *
from Script.project_api.functions import print_object_info_ai

DEBUG_RAW_DATA = False

class Pattern(UFSTC):  
    def pre_process(self) -> None:
        self.TestNormalLun, self.TestEM1Lun, self.TestWBLun, self.flash_setting, self.fw_geometry = rain_pattern_precondition()
        self.max_ce, self.max_plane, self.max_pageline = get_geometry_parameter()
        self.write_record = api.get_empty_write_record()
        self.UECC_pca: List[Tuple[int, project_api.physical_address_info, bool, int]] = []
        response, self.health_report_before = project_api.issue_40FE_to_read_enhanced_health_report()

        pass

    def _build_expected_list(self) -> None:
        """Build expected list from current UECC_pca (called by step8/step9)."""
        self.expected: list[dict[str, Any]] = []
        for lun, pca, slc_en, lba in self.UECC_pca:
            logical_page = self.transfer_physical_page_to_logical_page(pca.page.value, slc_en)
            self.expected.append({
                "lun": lun,
                "lba": lba,
                "vb":    pca.virtual_block_number.value,
                "die":   pca.die.value,
                "block": pca.physical_block_number_w_BBT.value,
                "plane": pca.plane.value,
                "page": pca.page.value,
                "logical_page": logical_page,
                "slc_en": bool(slc_en),
                "found": False,
            })
            logger.info(f"  Expect: {self.expected[-1]}")

    def compare_data(self, errors: list[str], struct: Any, field: Any, expected: int) -> None:
        """Compare a struct field's .value against expected. Appends to errors if mismatch.
        Label is auto-detected from the struct's attribute name."""
        # Find the field's attribute name from the struct
        name = "?"
        for attr_name, attr_val in struct.__dict__.items():
            if attr_val is field:
                name = attr_name
                break
        actual = field.value
        if actual == expected:
            return
        errors.append(f"{name}: expected={expected}, actual={actual}")

    def step1(self) -> None:
        logger.flow(1, 'Write TLC to create TLC L2')
        logger.info('Write data until the flush Swap condition and SPOR')
        lun = self.TestNormalLun
        testMode=TestMode.TEST_TLC
        last_lba, cursor = write_data_more_than_N_pageline(pageline_cnt=6, lun=lun, testMode=testMode, write_record=self.write_record)
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
        total_size = api.BLOCK4K_SIZE_32M_BYTE
        chunksize = api.WRITE_10_MAX_BLOCK_LEN
        logger.info('continue writing data until the sync point')
        api.sequential_write(lun=lun, start_lba=last_lba+1, total_size=total_size, chunk_size=chunksize, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        last_lba += total_size - 1
        lba = last_lba // 2
        self.UECC_pca.append((lun, get_PCA_and_print(lun=lun, lba=lba), False, lba))
        pass

    def step2(self) -> None:
        logger.flow(2, 'Write WB to create WB L2')
        logger.info('Write data until the flush Swap condition and SPOR')
        lun = self.TestWBLun
        testMode=TestMode.TEST_WB
        last_lba, cursor = write_data_more_than_N_pageline(pageline_cnt=6, lun=lun, testMode=testMode, write_record=self.write_record)
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
        total_size = api.BLOCK4K_SIZE_32M_BYTE
        chunksize = api.WRITE_10_MAX_BLOCK_LEN
        logger.info('continue writing data until the sync point')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.sequential_write(lun=lun, start_lba=last_lba+1, total_size=total_size, chunk_size=chunksize, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        last_lba += total_size - 1
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        lba = last_lba // 2
        self.UECC_pca.append((lun, get_PCA_and_print(lun=lun, lba=lba), True, lba))
        pass
    
    def step3(self) -> None:
        logger.flow(3, 'Write EM1 data to create SLC L2')
        logger.info('Write data until the flush Swap condition and SPOR')
        lun = self.TestEM1Lun
        testMode=TestMode.TEST_SLC
        last_lba, cursor = write_data_more_than_N_pageline(pageline_cnt=6, lun=lun, testMode=testMode, write_record=self.write_record)
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
        total_size = api.BLOCK4K_SIZE_32M_BYTE
        chunksize = api.WRITE_10_MAX_BLOCK_LEN
        logger.info('continue writing data until the sync point')
        api.sequential_write(lun=lun, start_lba=last_lba+1, total_size=total_size, chunk_size=chunksize, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        last_lba += total_size - 1
        lba = last_lba // 2
        self.UECC_pca.append((lun, get_PCA_and_print(lun=lun, lba=lba), True, lba))
        pass

    def step4(self) -> None:
        logger.flow(4, 'Inject UECC in each VB type')
        new_pca_list: list[tuple[int, project_api.physical_address_info, bool, int]] = []
        for lun, pca, slc_en, lba in self.UECC_pca:
            actual_pca = inject_UECC(pca=pca, SLC_enable=slc_en)
            dire_read_payload = direct_read_raw_data_and_check_status(pca=actual_pca, SLC_enable=slc_en, expect_status=project_api.ReadStatus.UECC)
            new_pca_list.append((lun, actual_pca, slc_en, lba))
        self.UECC_pca = new_pca_list
        pass

    def step5(self) -> None:
        logger.flow(5, 'SPOR')
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
        
    def step6(self) -> None:
        logger.flow(6, 'Check InitUECCEventLog from SPOR + Compare data')
        # Build expected list from UECC injection parameters
        init_expected: list[dict[str, Any]] = []
        for lun, pca, slc_en, lba in self.UECC_pca:
            init_expected.append({
                "vb":    pca.virtual_block_number.value,
                "die":   pca.die.value,
                "block": pca.physical_block_number_w_BBT.value,
                "plane": pca.plane.value,
                "page":  pca.page.value,
                "found": False,
            })
        
        # Capture 0x300C written during SPOR power-on before clear_event_logs
        outputs = project_api.issue_find_event_log_by_id(0x300C, project_api.EventLogPriority.HighPriority)
        logger.info(f"Found {len(outputs)} 0x300C entries (from SPOR power-on)")

        for exp in init_expected:
            for buf in reversed(outputs):
                ev = project_api.InitUECCEventLog(buf, project_api.SPECIFIC_LOG_INFO_OFFSET)
                print_object_info_ai(ev)
                
                # Match by block + plane
                if ev.block.value != exp["block"] or ev.planeIdx.value != exp["plane"]:
                    continue
                
                errors: list[str] = []
                if ev.log_id.value != 0x300C:
                    errors.append(f"log_id: expected=0x300C, actual=0x{ev.log_id.value:04X}")
                if ev.logVB.value != exp["vb"]:
                    errors.append(f"logVB: expected={exp['vb']}, actual={ev.logVB.value}")
                if ev.pageline.value != exp["page"]:
                    errors.append(f"pageline: expected={exp['page']}, actual={ev.pageline.value}")
                if ev.planeIdx.value != exp["plane"]:
                    errors.append(f"planeIdx: expected={exp['plane']}, actual={ev.planeIdx.value}")
                
                if errors:
                    logger.warning(f"  Block {exp['block']} matched but params wrong:")
                    for e in errors:
                        logger.warning(f"    {e}")
                    logger.error_lb(f'Check event log 0x300C(InitUECCEventLog) — params mismatch')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    exp["found"] = True
                    logger.info(f"  VB={exp['vb']}, Block={exp['block']}, plane={exp['plane']} — OK")
                break
        
        missing = [exp for exp in init_expected if not exp["found"]]
        if missing:
            for exp in missing:
                logger.warning(f"  NOT found in 0x300C: VB={exp['vb']}, Block={exp['block']}")
        
        project_api.clear_event_logs()
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        read_compare_rain_result(write_record=self.write_record)
        
    def step7(self) -> None:
        logger.flow(7, f"issue VU 40C5 to check the refresh booking queue")
        VB_list = [pca.virtual_block_number.value for lun, pca, slc_en, lba in self.UECC_pca]
        check_UECC_refresh_booking_Q(VB_list=VB_list)
        pass
    
    def step8(self) -> None:
        logger.flow(8, f"check RAIN counter in health report")
        check_RAIN_cnt_in_heatlth_report(self.health_report_before,
                                            d1_open_raind_recovery_ok_count = True,
                                            d3_open_raind_recovery_ok_count = True
                                        )
        pass
    
    def step9(self) -> None:
        logger.flow(9, "Check event log 0x6001(BeUeccEvent) — all 3 injected UECC locations recorded")
        self._build_expected_list()

        outputs = project_api.issue_find_event_log_by_id(0x6001, project_api.EventLogPriority.HighPriority)
        logger.info(f"Found {len(outputs)} 0x6001 entries")

        for exp in self.expected:
            for buf in reversed(outputs):
                ev = project_api.BeUeccEvent(buf, project_api.SPECIFIC_LOG_INFO_OFFSET)
                ev.print_all()

                ev_blocks = [ev.block_0.value, ev.block_1.value, ev.block_2.value,
                             ev.block_3.value, ev.block_4.value, ev.block_5.value]
                if exp["block"] not in ev_blocks or exp["logical_page"] != ev.page_info_bits.page.value:
                    continue

                # Block+page matched → validate all other parameters
                errors: list[str] = []

                # block[N]: fail at plane N, all others must be 0xFFFF
                for i in range(6):
                    if i == exp["plane"]:
                        if ev_blocks[i] != exp["block"]:
                            errors.append(f"block_{i}: expected={exp['block']}, actual={ev_blocks[i]}")
                    else:
                        if ev_blocks[i] != 0:
                            errors.append(f"block_{i}: expected=0xFFFF, actual={ev_blocks[i]}")
                # self.compare_data(errors, ev.realUeccInfo, ev.realUeccInfo.hostLun, exp["lun"])
                self.compare_data(errors, ev, ev.die, exp["die"])
                self.compare_data(errors, ev, ev.startPlane, exp["plane"])
                self.compare_data(errors, ev.flags_bits, ev.flags_bits.slcMode, exp["slc_en"])
                self.compare_data(errors, ev.flags_bits, ev.flags_bits.ueccType, 2)  # 0=soft, 1=fake, 2=real

                if errors:
                    logger.warning(f"  Block {exp['block']} (0x{exp['block']:X}) matched but params wrong:")
                    for err in errors:
                        logger.warning(f"    {err}")
                    logger.error_lb(f'Check event log 0x6001(BeUeccEvent) — params mismatch')
                    logger.error_fp(f'event log 0x6001 params mismatch for VB={exp["vb"]}, Block={exp["block"]}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    exp["found"] = True
                    logger.info(f"  VB={exp['vb']}, Block={exp['block']} (0x{exp['block']:X}), die={exp['die']}, lun={exp['lun']}")
                break  # move to next expected entry

        missing = [exp for exp in self.expected if not exp["found"]]
        if missing:
            for exp in missing:
                logger.warning(f"  NOT found in 0x6001: {exp}")
            logger.error_lb(f'Check event log 0x6001(BeUeccEvent) — not found')
            vb_list = [f'VB={exp["vb"]}, Block={exp["block"]}' for exp in missing]
            logger.error_fp(f'event log 0x6001 not found for {"; ".join(vb_list)}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def step10(self) -> None:
        logger.flow(10, "Check event log 0x3011(RainRecoveryEventLog) — all 3 injected UECC locations recorded")

        self._build_expected_list()

        outputs = project_api.issue_find_event_log_by_id(0x3011, project_api.EventLogPriority.LowPriority)
        logger.info(f"Found {len(outputs)} 0x3011 entries")

        for exp in self.expected:
            for buf in reversed(outputs):
                ev = project_api.RainRecoveryEventLog(buf, project_api.SPECIFIC_LOG_INFO_OFFSET)
                print_object_info_ai(ev)

                ev_blocks = [ev.errblock_0.value, ev.errblock_1.value,
                             ev.errblock_2.value, ev.errblock_3.value,
                             ev.errblock_4.value, ev.errblock_5.value]
                if exp["block"] not in ev_blocks or exp["page"] != ev.pageLine.value:
                    continue

                # Block+page matched → validate all other parameters
                errors: list[str] = []

                # errblock[N]: fail at plane N, all others must be 0xFFFF
                for i in range(6):
                    if i == exp["plane"]:
                        if ev_blocks[i] != exp["block"]:
                            errors.append(f"errblock_{i}: expected={exp['block']}, actual={ev_blocks[i]}")
                    else:
                        if ev_blocks[i] != 0xFFFF:
                            errors.append(f"errblock_{i}: expected=0xFFFF, actual={ev_blocks[i]}")

                self.compare_data(errors, ev, ev.die, exp["die"])
                self.compare_data(errors, ev, ev.errType, 0)  # 0=read UECC, 1=program fail
                self.compare_data(errors, ev, ev.logVB, 0xFFFF)
                self.compare_data(errors, ev, ev.pvb, 0xFFFF)

                # pageInfo: upper bits = logical page, lower 2 bits = lmu
                expected_pageInfo = exp["logical_page"] << 2
                if ev.pageInfo.value != expected_pageInfo:
                    errors.append(f"pageInfo: expected=0x{expected_pageInfo:X} (logical_page={exp['logical_page']}, lmu=0), actual=0x{ev.pageInfo.value:X}")

                self.compare_data(errors, ev, ev.recovResult, 0)  # 0=decode OK
                self.compare_data(errors, ev, ev.openVbFlag, 1)  # 0=close VB, 1=open L2 FBP
                self.compare_data(errors, ev, ev.vbType, exp["slc_en"])  # 0=TLC, 1=SLC
                self.compare_data(errors, ev, ev.parityPosition, 2)  # 0=data block, 1=parity buffer, 2=swap
                self.compare_data(errors, ev, ev.abnormalUECCPhy, 0)  # 0=正常, 1=decode read data page error

                if errors:
                    logger.warning(f"  Block {exp['block']} (0x{exp['block']:X}) matched but params wrong:")
                    for err in errors:
                        logger.warning(f"    {err}")
                    logger.error_lb(f'Check event log 0x3011(RainRecoveryEventLog) — params mismatch')
                    logger.error_fp(f'event log 0x3011 params mismatch for VB={exp["vb"]}, Block={exp["block"]}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    exp["found"] = True
                    logger.info(f"  VB={exp['vb']}, Block={exp['block']} (0x{exp['block']:X}), die={exp['die']}, lun={exp['lun']}")
                break

        missing = [exp for exp in self.expected if not exp["found"]]
        if missing:
            for exp in missing:
                logger.warning(f"  NOT found in 0x3011: {exp}")
            logger.error_lb(f'Check event log 0x3011(RainRecoveryEventLog) — not found')
            vb_list = [f'VB={exp["vb"]}, Block={exp["block"]}' for exp in missing]
            logger.error_fp(f'event log 0x3011 not found for {"; ".join(vb_list)}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def step11(self) -> None:
        logger.flow(11, f"issue VU 40E5 to check the BBT")
        VB_list = [pca.virtual_block_number.value for lun, pca, slc_en, lba in self.UECC_pca]
        check_BB_retirementafter_refresh(VB_list = VB_list, expect_reason=project_api.BBRetirementReaspnType.READ_SCAN_UECC)
        pass

    def post_process(self) -> None:
        pass
    
    def transfer_physical_page_to_logical_page(self, physical_page:int, slc_en:int = False) -> int:
        if slc_en:
            return physical_page
        region_max_wl = [540, 556, 1108]
        if physical_page < 1620:
            logical_page = physical_page // 3
        elif physical_page < 1652:
            logical_page = (physical_page - 1620) // 2
            logical_page += region_max_wl[0]
        elif physical_page < 3308:
            logical_page = (physical_page - 1652) // 3
            logical_page += region_max_wl[1]
        elif physical_page < 3312:
            logical_page = (physical_page - 3308) // 1
            logical_page += region_max_wl[2]
        return logical_page

run = Pattern().run
if __name__ == "__main__":
    run()