import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.mconfig.mutual_fun import *
import time
from Script.project_api.functions import print_object_info_ai


class Pattern(UFSTC):
    def pre_process(self) -> None:
        config_lun()
        self.mConfig_in_FW_HW_BIN_offset = 0x5000
        self.pConfig_in_FW_HW_BIN_offset = 0x5400
        _flash_setting = api.get_flash_setting()
        self.max_ce = _flash_setting.Max_Fdevice
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()
        self.hw_setting.backup()
        pass

    def step1(self) -> None:
        HW_page_offset = 0
        if self.hw_setting.ce_num == 1:
            HW_page_offset = 0
        elif self.hw_setting.ce_num == 2:
            HW_page_offset = DATA_SIZE_4K_BYTE
        elif self.hw_setting.ce_num == 4:
            HW_page_offset = DATA_SIZE_8K_BYTE
        elif self.hw_setting.ce_num == 8:
            HW_page_offset = DATA_SIZE_12K_BYTE
        
        offset = 0
        
        _, mConfig_in_vu_bkup = project_api.get_mConfig_data()
        _, pConfig_in_vu_bkup = project_api.get_pConfig_data()
        index, mConfig, pConfig = load_mConfig_pConfig_from_xlsx(OTP_value = mConfig_in_vu_bkup.OTP_value.value)
        if index == 1:
            offset = 0
        elif index == 2:
            offset = DATA_SIZE_4K_BYTE
        elif index == 3:
            offset = DATA_SIZE_8K_BYTE
        elif index == 4:
            offset = DATA_SIZE_12K_BYTE
        
        logger.flow(1, 'search bin and get mconfig follow mConfig Format in FFU bin')
        # current_bin = bytearray(4096)
        current_bin = api.api.search_ffu_bin(api.api.FFUBinType.FW_HW_BIN, api.api.FFUSvnType.CURRENT_SVN_BIN, True)
        mConfig_in_bin, pConfig_in_bin = get_m_p_config_in_FW_HW_BIN(current_bin, offset)
        PRL = get_PRL_in_FW_HW_BIN(current_bin)
        compare_payload(mConfig_pConfig_dict=mConfig, payload=mConfig_in_bin.payload.copy())
        compare_payload(mConfig_pConfig_dict=pConfig, payload=pConfig_in_bin.payload.copy())

        
        logger.flow(1, 'issue 4056 mconfig data & pconfig data are same as xlsx')
        compare_payload(mConfig_pConfig_dict=mConfig, payload=mConfig_in_vu_bkup.payload.copy())
        compare_payload(mConfig_pConfig_dict=pConfig, payload=pConfig_in_vu_bkup.payload.copy())

        ffu_case = [1,2,3]
        for case in range(1, 6+1):
            logger.info(f'======================= test case {case} =======================') #ENG2
            response, health_report_before = project_api.issue_40FE_to_read_enhanced_health_report()
            project_api.clear_event_logs()
            ffu_info_before = project_api.issue_4077_to_report_FFU_patch_count()
            print_object_info_ai(ffu_info_before)
            temp_mConfig = project_api.mConfig(mConfig_in_vu_bkup.payload.copy())
            temp_pConfig = project_api.pConfig(pConfig_in_vu_bkup.payload.copy())
            temp_HW_page = self.hw_setting._backup_data[HW_page_offset: HW_page_offset + 0x1000].copy()
            temp_bin = current_bin.copy()
            temp_mConfig.payload[0:7] = "MCONFIG".encode("ascii")
            temp_pConfig.payload[0:7] = "PCONFIG".encode("ascii")
            
            logger.flow(2, 'HW Setting Enable FFU update / same SVN')
            if case in ffu_case: #FFU case
                self.hw_setting.set_to_device(api.HwSettingField.FFU_FEATURE, api.FFUFeature.FFU_SAMVE_SVN_BACKWARD_EN)
                api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = True)
            
            logger.flow(3, 'mConfig Test Case')
            randversion = random.randint(1, 0xFF)
            if case == 1:
                logger.info('mConfig Case 1: write FFU bin') #ENG2
                temp_bin = api.codesign_ffu_bin(ffu_bin=temp_bin, ffu_bin_type=api.FFUBinType.FW_HW_BIN, include_mconfig=True)
                api.send_ffu_write_buffer(len(temp_bin), 0, temp_bin)
                temp_mConfig, temp_pConfig = get_m_p_config_in_FW_HW_BIN(temp_bin, offset)
            elif case == 2:
                logger.info('mConfig Case 2: write FFU bin  mConfig_VU with changeable (mconfig version)') #ENG2
                temp_bin[self.mConfig_in_FW_HW_BIN_offset+7+offset] = randversion
                temp_bin = api.codesign_ffu_bin(ffu_bin=temp_bin, ffu_bin_type=api.FFUBinType.FW_HW_BIN, include_mconfig=True)
                api.send_ffu_write_buffer(len(temp_bin), 0, temp_bin)
                temp_mConfig, temp_pConfig = get_m_p_config_in_FW_HW_BIN(temp_bin, offset)
            elif case == 3:
                logger.info('mConfig Case 3: write FFU bin  mConfig_VU with changeable (pconfig version)') #ENG2
                temp_bin[self.pConfig_in_FW_HW_BIN_offset+7+offset] = randversion
                temp_bin = api.codesign_ffu_bin(ffu_bin=temp_bin, ffu_bin_type=api.FFUBinType.FW_HW_BIN, include_mconfig=True)
                api.send_ffu_write_buffer(len(temp_bin), 0, temp_bin)
                temp_mConfig, temp_pConfig = get_m_p_config_in_FW_HW_BIN(temp_bin, offset)
            elif case == 4:
                logger.info('mConfig Case 4: C056 mConfig_VU with changeable mconfig (mconfig version)') #ENG2, use 0x09
                temp_mConfig.mConfig_Version.value = randversion
                project_api.set_mConfig_data(mConfig=temp_mConfig)
            elif case == 5:
                logger.info('mConfig Case 5: C056 mConfig_VU with changeable pconfig ([config version)') #ENG2, use 0x09
                temp_pConfig.pConfig_version.value = randversion
                project_api.set_pConfig_data(pConfig=temp_pConfig)
            elif case == 6:
                logger.info('mConfig Case 6: C056 mConfig_VU moconfig in write FFU bin') #ENG2, use 0x09
                project_api.set_HW_page_config_data(data_payload=temp_HW_page)

            logger.flow(4, 'check FFU count by vu4077')
            ffu_info_after = project_api.issue_4077_to_report_FFU_patch_count()
            print_object_info_ai(ffu_info_after)
            if case in ffu_case: #FFU case
                if ffu_info_after.patch_Trial_Count.value != ffu_info_before.patch_Trial_Count.value +1:
                    logger.error_lb(f'check FFU patch_Trial_Count')
                    logger.error_fp(f'expect patch_Trial_Count increase after FFU, but before value = {ffu_info_before.patch_Trial_Count.value}, current value = {ffu_info_after.patch_Trial_Count.value}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                if ffu_info_after.patch_Success_Count.value != ffu_info_before.patch_Success_Count.value +1:
                    logger.error_lb(f'check FFU patch_Success_Count')
                    logger.error_fp(f'expect patch_Success_Count increase after FFU, but before value = {ffu_info_before.patch_Success_Count.value}, current value = {ffu_info_after.patch_Success_Count.value}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                if ffu_info_after.patch_Trial_Count.value != ffu_info_before.patch_Trial_Count.value or ffu_info_after.patch_Success_Count.value != ffu_info_before.patch_Success_Count.value:
                    logger.error_lb(f'check FFU patch_Trial_Count, patch_Success_Count')
                    logger.error_fp(f'expect patch_Trial_Count and patch_Success_Count not increase, \
                        but patch_Trial_Count before value = {ffu_info_before.patch_Trial_Count.value}, current value = {ffu_info_after.patch_Trial_Count.value}, \
                            patch_Success_Count before value = {ffu_info_before.patch_Success_Count.value}, current value = {ffu_info_after.patch_Success_Count.value}, \
                            result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
            logger.flow(4, 'Host issue init flow with HWReset or ResetN')
            resetmode = random.choice([api.Dcmd5ResetType.HW_RESET, api.Dcmd5ResetType.RESET_N])
            api.init_tester_to_unit_ready(resetmode=resetmode)
            ffustatus = api.read_attribute(idn=api.AttributeIDN.DEVICE_FFU_STATUS)
            logger.info(f'FFU statue = {ffustatus} ({api.FFUStatus(ffustatus).name})')
            
            if case in ffu_case: #FFU case
                logger.flow(4, 'check FFU event log')
                patch_trial_count = 1
                patch_success_count_0x202 = 1
                patch_release_date_0x204 = None
                patch_release_year_0x206 = None
                ffu_fail_count = 0
                self.check_FFU_info_in_heatlth_report(health_report_before, patch_trial_count, patch_success_count_0x202, patch_release_date_0x204, patch_release_year_0x206, ffu_fail_count)
                eventCnt = health_report_before.patch_success_count_0x202.value + health_report_before.ffu_fail_count.value + 1
                oldVer = int.from_bytes(temp_bin[0x100:0x102], 'big')
                newVer = int.from_bytes(temp_bin[0x100:0x102], 'big')
                self.check_FFU_event_log(eventCnt=eventCnt, oldVer=oldVer, newVer=newVer)
            

            if case == 6:
                logger.flow(5, 'Host get HW page and check data') #only mconfig, pconfig use 0x83
                _, HW_page_vu = project_api.get_HW_page_config_data()
                self.hw_setting.update_from_device()
                if self.hw_setting._data[HW_page_offset: HW_page_offset + 0x1000] != HW_page_vu:
                    dumpfile('hw_setting.bin', self.hw_setting._data[HW_page_offset: HW_page_offset + 0x1000])
                    dumpfile('4056.bin', HW_page_vu)
                    logger.error_lb(f'check HW_page after setting')
                    logger.error_fp(f'data conpare fail, please check dump file')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                logger.flow(5, 'Host issue 4056 get mConfig data as mConfig_VU') #only mconfig, pconfig use 0x83
                _, mConfig_in_vu = project_api.get_mConfig_data()
                _, pConfig_in_vu = project_api.get_pConfig_data()
                compare_mConfig_data(get_mConfig=mConfig_in_vu, set_mConfig=temp_mConfig)
                compare_pConfig_data(get_pConfig=pConfig_in_vu, set_pConfig=temp_pConfig)
            
        
            logger.flow(6, 'recover mConfig pConfig')
            mConfig_in_vu_bkup.payload[0:7] = "MCONFIG".encode("ascii")
            pConfig_in_vu_bkup.payload[0:7] = "PCONFIG".encode("ascii")
            self.hw_setting.recover()
            project_api.set_mConfig_data(mConfig=mConfig_in_vu_bkup)
            project_api.set_pConfig_data(pConfig=pConfig_in_vu_bkup)
            api.init_tester_to_unit_ready(resetmode=resetmode)
            _, mConfig_in_vu = project_api.get_mConfig_data()
            _, pConfig_in_vu = project_api.get_pConfig_data()
            compare_mConfig_data(get_mConfig=mConfig_in_vu, set_mConfig=mConfig_in_vu_bkup)
            compare_pConfig_data(get_pConfig=pConfig_in_vu, set_pConfig=pConfig_in_vu_bkup)
            
            response, health_report = project_api.issue_40FE_to_read_enhanced_health_report()
            if health_report.prl.value != PRL:
                logger.error_lb(f'check prl in health report')
                logger.error_fp(f'expect prl equal to health report(prl), but health report value = {health_report.prl.value}, expected value = {PRL}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            if health_report.fw_current_prl.value != PRL:
                logger.error_lb(f'check prl in health report')
                logger.error_fp(f'expect prl equal to health report(fw_current_prl), but health report value = {health_report.fw_current_prl.value}, expected value = {PRL}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def step2(self) -> None:
        access_vendor_mode()
        for flow in range(7, 10+1):
            fw_value_str = ""
            flow_str = ""
            if flow == 7:
                fw_value_str = "gUfsApiStruct.mconfig->m_reserved_9"
                flow_str = "L1 mconfig Test"
            elif flow == 8:
                fw_value_str = "gUfsApiStruct.mconfig->p_reserved_9[0]"
                flow_str = "L1 pconfig Test"
            elif flow == 9:
                fw_value_str = "gUfsApiStruct.mconfig->m_reserved_9"
                flow_str = "L2 mconfig Test"
            elif flow == 10:
                fw_value_str = "gUfsApiStruct.mconfig->p_reserved_9[0]"
                flow_str = "L2 pconfig Test"
                
            logger.flow(flow, flow_str)
            addr = api.get_fw_address(fw_value_str)
            if not addr:
                logger.error_lb(f'read fw addr : {fw_value_str}')
                logger.error_fp(f'addr is None, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            addr = addr.address
            logger.info(f"read fw addr: {fw_value_str},  addr = {addr} (0x{addr:X})")
            _, data = api.read_Xmemory(sram_address=addr)
            logger.info(f"read X memory: addr = {addr} (0x{addr:X}), value = {int.from_bytes(data[0:4],'little')}")
        
            payload = bytearray(data)
            randvalue = random.randint(0, 0xFE)
            
            payload[0:4] = (randvalue).to_bytes(4, 'little')
            api.write_Xmemory(sram_address=addr, data_buffer=payload)
            if flow <= 8:
                ats_times = self.get_ast_times()
                time.sleep(15)
                ats_times_after = self.get_ast_times()
                if ats_times_after <= ats_times:
                    logger.error_lb(f'check ats_times should increase')
                    logger.error_fp(f'expect ats_times increased, but current value = {ats_times_after}, before value = {ats_times}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
                ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
                ExecuteCMD.send(QD=1,clear_on_success=True)
        
            _, data_after = api.read_Xmemory(sram_address=addr)
            value_after = int.from_bytes(data_after[0:4], 'little')
            logger.info(f"read X memory: addr = {addr} (0x{addr:X}), value = {value_after}")
            if value_after != randvalue:
                dumpfile('data_after.bin',data_after)
                dumpfile('data.bin',data)
                logger.error_lb(f'check addr value after {flow_str}')
                logger.error_fp(f'expect value match set value {randvalue}, but current value = {int.from_bytes(data_after[0:4],"little")}, before value = {int.from_bytes(data[0:4],"little")}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL        
        pass
    
    def post_process(self) -> None:
        pass
    
    def get_ast_times(self) -> int:
        payload_get = project_api.get_smart_info()
        offset_ats_timer = 0x4a8
        data_size_byte = 8
        ats_times_payload = payload_get[offset_ats_timer: offset_ats_timer + data_size_byte]
        ats_times = int.from_bytes(ats_times_payload, 'little')
        logger.info(f'ats_times = {ats_times}')
        dumpfile('smart_info.bin',payload_get)
        return ats_times
    
    def check_FFU_event_log(self, eventCnt:int, oldVer:int, newVer:int) -> None:
        def compare_data(errors: list[str], struct: Any, field: Any, expected: int) -> None:
            name = "?"
            for attr_name, attr_val in struct.__dict__.items():
                if attr_val is field:
                    name = attr_name
                    break
            actual = field.value
            if actual == expected:
                return
            errors.append(f"{name}: expected={expected}, actual={actual}")
        logger.flow(8, "Check event log 0x0007")

        outputs = project_api.issue_find_event_log_by_id(0x0007, project_api.EventLogPriority.HighPriority)
        logger.info(f"Found {len(outputs)} 0x0007 entries")
        if len(outputs) == 0:
            logger.error_lb(f'Check event log 0x0007(FFUEventILog) — not found')
            logger.error_fp(f'event log 0x0007 not found after FFU, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        for buf in reversed(outputs):
            ev = project_api.FFUEventILog(buf, project_api.SPECIFIC_LOG_INFO_OFFSET)
            ev.print_all()

            errors: list[str] = []
            compare_data(errors, ev, ev.eventCnt, eventCnt)
            compare_data(errors, ev, ev.oldVer, oldVer)
            compare_data(errors, ev, ev.newVer, newVer)
            compare_data(errors, ev, ev.logType, 0xFF)

            if errors:
                for err in errors:
                    logger.warning(f"    {err}")
                logger.error_lb(f'Check event log 0x0007(FFUEventILog) — params mismatch')
                logger.error_fp(f'event log 0x0007 params mismatch, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            break
        return
    
    def check_FFU_info_in_heatlth_report(self, before_health:project_api.ReadEnhanceHealthReport, 
                                         patch_trial_count:Optional[int] = None, 
                                         patch_success_count_0x202:Optional[int] = None, 
                                         patch_release_date_0x204:Optional[int] = None, 
                                         patch_release_year_0x206:Optional[int] = None, 
                                         ffu_fail_count:Optional[int] = None, 
                                         ) -> None:
        def get_fields_lsit(any_struct: Any) -> list[tuple[Any, Any]]:
            raw_fields = [
                (name, field) for name, field in any_struct.__dict__.items()
                if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
            ]
            raw_fields.sort(key=lambda kv: kv[1].start_offset)
            return raw_fields
            
        def print_struct_different(before_struct: Any, after_struct: Any) -> None:
            before_fields = get_fields_lsit(before_struct)
            current_fields = get_fields_lsit(after_struct)            
            for (name0, raw), (name1, expect) in zip(
                                        before_fields,
                                        current_fields,
                                    ):
                if hasattr(raw, "value") and hasattr(expect, "value") and name0 == name1:
                    if raw.value != expect.value:
                        logger.info(f'{name0}: {raw.value} (0x{raw.value:X}) -> {expect.value} (0x{expect.value:X})')
                pass
        
        def check_value_modify(before_struct: Any, after_struct: Any, string:str, expect_modify:Optional[int] = None) -> None:
            if expect_modify == None:
                return
            before_fields = get_fields_lsit(before_struct)
            current_fields = get_fields_lsit(after_struct)            
            for (name0, current), (name1, before) in zip(
                                        current_fields,
                                        before_fields,
                                    ):
                if name0 == string:
                    value = current.value
                    value_before = before.value
                    if value_before - value != expect_modify:
                        logger.error_lb(f'check {string} value')
                        logger.error_fp(f'expect {string} modify {expect_modify}, but current value = {value}, before value = {value_before}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    return
                pass
        response, health_report = project_api.issue_40FE_to_read_enhanced_health_report()
        print_struct_different(before_health, health_report)
        check_value_modify(before_health, health_report, "patch_trial_count", patch_trial_count)
        check_value_modify(before_health, health_report, "patch_success_count_0x202", patch_success_count_0x202)
        check_value_modify(before_health, health_report, "patch_release_date_0x204", patch_release_date_0x204)
        check_value_modify(before_health, health_report, "patch_release_year_0x206", patch_release_year_0x206)
        check_value_modify(before_health, health_report, "ffu_fail_count", ffu_fail_count)
        before_health = health_report

run = Pattern().run
if __name__ == "__main__":
    run()