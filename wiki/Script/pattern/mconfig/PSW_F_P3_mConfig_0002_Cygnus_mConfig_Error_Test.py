import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.defines import UPIUResponse, ScsiStatus
from Script.api.cmd_seq.response import CommandResponse, get_scsi_status_str, get_sense_key_str, get_asc_ascq_description
from typing import Union
from Script.pattern.mconfig.mutual_fun import *
from Script.project_api.functions import print_object_info_ai


class Pattern(UFSTC):
    def pre_process(self) -> None:
        config_lun()
        self.mConfig_in_FW_HW_BIN_offset = 0x5000
        self.pConfig_in_FW_HW_BIN_offset = 0x5400
        # flashsettingdata = api.get_flash_setting()
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()
        self.hw_setting.backup()
        pass

    def step1(self) -> None:
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
        current_bin = api.api.search_ffu_bin(api.api.FFUBinType.FW_HW_BIN, api.api.FFUSvnType.CURRENT_SVN_BIN, True)
        compatible_enable = current_bin[0x50]
        mConfig_in_bin, pConfig_in_bin = get_m_p_config_in_FW_HW_BIN(current_bin, offset)
        compare_payload(mConfig_pConfig_dict=mConfig, payload=mConfig_in_bin.payload.copy())
        compare_payload(mConfig_pConfig_dict=pConfig, payload=pConfig_in_bin.payload.copy())
        error_OTP = [145, 146, 147, 148]
        error_OTP.remove(mConfig_in_vu_bkup.OTP_value.value)
        mConfig_in_vu_bkup.payload[0:7] = "MCONFIG".encode("ascii")
        pConfig_in_vu_bkup.payload[0:7] = "PCONFIG".encode("ascii")
        
        ffu_case = [1,2,7,8,9,12]
        max_case = 11 if not compatible_enable else 12
        for case in range(1, max_case+1):
            logger.info(f'======================= test case {case} =======================') #ENG2
            ffu_info_before = project_api.issue_4077_to_report_FFU_patch_count()
            print_object_info_ai(ffu_info_before)
            temp_mConfig = project_api.mConfig(mConfig_in_vu_bkup.payload.copy())
            temp_pConfig = project_api.pConfig(pConfig_in_vu_bkup.payload.copy())
            temp_HW_page = self.hw_setting._backup_data[offset: offset + 0x1000].copy()
            temp_bin = current_bin.copy()
            temp_mConfig.payload[0:7] = "MCONFIG".encode("ascii")
            temp_pConfig.payload[0:7] = "PCONFIG".encode("ascii")
            
            logger.flow(2, 'HW Setting Enable FFU update / same SVN')
            if case in ffu_case: #FFU case
                self.hw_setting.set_to_device(api.HwSettingField.FFU_FEATURE, api.FFUFeature.FFU_SAMVE_SVN_BACKWARD_EN)
            
            logger.flow(3, 'mConfig Test Case')
            error_value = random.randint(1, 0xFF)
            error_value2 = random.randint(1, 0xFF)
            erroe_case = True
            if case == 1:
                logger.info('mConfig Case 1: write FFU bin with wrong OTP value for mconfig') #ENG2
                temp_bin[self.mConfig_in_FW_HW_BIN_offset + 8 + offset] = error_value
                temp_bin = api.codesign_ffu_bin(ffu_bin=temp_bin, ffu_bin_type=api.FFUBinType.FW_HW_BIN, include_mconfig=True)
                erroe_case = False
                self.send_FFU_and_check_response(temp_bin, error_case=erroe_case)
            elif case == 2:
                logger.info('mConfig Case 2: write FFU bin with wrong OTP value for pconfig') #ENG2
                temp_bin[self.pConfig_in_FW_HW_BIN_offset + 8 + offset] = error_value
                temp_bin = api.codesign_ffu_bin(ffu_bin=temp_bin, ffu_bin_type=api.FFUBinType.FW_HW_BIN, include_mconfig=True)
                erroe_case = False
                self.send_FFU_and_check_response(temp_bin, error_case=erroe_case)
            elif case == 3:
                logger.info('mConfig Case 3: C056 mConfig_VU with wrong OTP value with mconfig') #ENG2, use 0x09
                temp_mConfig.OTP_value.value = error_OTP[random.randint(0,len(error_OTP)-1)]
                self.set_mConfig_pConfig_data_and_check_resp(input=temp_mConfig, error_case = erroe_case)
            elif case == 4:
                logger.info('mConfig Case 4: C056 mConfig_VU with wrong OTP value with pconfig') #ENG2, use 0x09
                temp_pConfig.OTP_value.value = error_OTP[random.randint(0,len(error_OTP)-1)]
                self.set_mConfig_pConfig_data_and_check_resp(input=temp_pConfig, error_case = erroe_case)
            elif case == 5:
                logger.info('mConfig Case 5: C056 mConfig_VU with corr OTP value  byte[12]option = 3')
                self.set_mConfig_pConfig_data_and_check_resp(input=0x3, error_case = erroe_case)
            elif case == 6:
                logger.info('mConfig Case 5: C056 mConfig_VU with corr  OTP value  byte[12]option = 0xFF')
                self.set_mConfig_pConfig_data_and_check_resp(input=0xFF, error_case = erroe_case)
            elif case == 7:
                logger.info('mConfig Case 7: write FFU bin with unchangeable mconfig (File Signature)') #ENG2
                temp_bin[self.mConfig_in_FW_HW_BIN_offset + offset] = error_value
                temp_bin = api.codesign_ffu_bin(ffu_bin=temp_bin, ffu_bin_type=api.FFUBinType.FW_HW_BIN, include_mconfig=True)
                self.send_FFU_and_check_response(temp_bin, error_case = erroe_case)
            elif case == 8:
                logger.info('mConfig Case 8: write FFU bin with unchangeable pconfig (File Signature)') #ENG2
                temp_bin[self.pConfig_in_FW_HW_BIN_offset + offset] = error_value
                temp_bin = api.codesign_ffu_bin(ffu_bin=temp_bin, ffu_bin_type=api.FFUBinType.FW_HW_BIN, include_mconfig=True)
                self.send_FFU_and_check_response(temp_bin, error_case = erroe_case)
            elif case == 9:
                logger.info('mConfig Case 9: write FFU bin with unchangeable both mconfig and pconfig (File Signature)') #ENG2
                temp_bin[self.mConfig_in_FW_HW_BIN_offset + offset] = error_value
                temp_bin[self.pConfig_in_FW_HW_BIN_offset + offset] = error_value2
                temp_bin = api.codesign_ffu_bin(ffu_bin=temp_bin, ffu_bin_type=api.FFUBinType.FW_HW_BIN, include_mconfig=True)
                self.send_FFU_and_check_response(temp_bin, error_case = erroe_case)
            elif case == 10:
                logger.info('mConfig Case 10: C056 mConfig_VU with unchangeable mconfig(File Signature)') #ENG2, use 0x09
                temp_mConfig.Name_1.value = error_value
                self.set_mConfig_pConfig_data_and_check_resp(input=temp_mConfig, error_case = erroe_case)
            elif case == 11:
                logger.info('mConfig Case 11: C056 mConfig_VU with unchangeable pconfig(File Signature)') #ENG2, use 0x09
                temp_pConfig.Name_1.value = error_value
                self.set_mConfig_pConfig_data_and_check_resp(input=temp_pConfig, error_case = erroe_case)
            elif case == 12:
                logger.info('mConfig Case 12: write FFU bin with incompatible FFU BIN')
                compatible_value_offset = 0xC01C
                temp_bin[compatible_value_offset] += 1
                temp_bin = api.codesign_ffu_bin(ffu_bin=temp_bin, ffu_bin_type=api.FFUBinType.FW_HW_BIN, include_mconfig=True)
                self.send_FFU_and_check_response(temp_bin, error_case = erroe_case)

            logger.flow(4, 'check FFU count by vu4077')
            ffu_info_after = project_api.issue_4077_to_report_FFU_patch_count()
            print_object_info_ai(ffu_info_after)
            if case in ffu_case: #FFU case
                if ffu_info_after.patch_Trial_Count.value != ffu_info_before.patch_Trial_Count.value +1:
                    logger.error_lb(f'check FFU patch_Trial_Count')
                    logger.error_fp(f'expect patch_Trial_Count increase after FFU, but before value = {ffu_info_before.patch_Trial_Count.value}, current value = {ffu_info_after.patch_Trial_Count.value}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                if erroe_case:
                    if ffu_info_after.patch_Success_Count.value != ffu_info_before.patch_Success_Count.value:
                        logger.error_lb(f'check FFU patch_Success_Count')
                        logger.error_fp(f'expect patch_Success_Count not increase after FFU, but before value = {ffu_info_before.patch_Success_Count.value}, current value = {ffu_info_after.patch_Success_Count.value}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
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
            ffustatus = api.FFUStatus(api.read_attribute(idn=api.AttributeIDN.DEVICE_FFU_STATUS))
            logger.info(f'FFU statue = {ffustatus} ({ffustatus.name})')
            if case in [1, 2]:
                if ffustatus != api.FFUStatus.MICROCODE_VERSION_MISMATCH:
                    logger.error_lb("check FFU status after write FFU with wrong OTP")
                    logger.error_fp(
                        f"expect FFU status = 4 (MICROCODE_VERSION_MISMATCH), "
                        f"but got {ffustatus} ({ffustatus.name})"
                    )
                    raise SIGHTING_FFU_STATUS_UNEXPECTED
        
            logger.flow(5, 'Host issue 4056 get mConfig data as mConfig_VU') #only mconfig, pconfig use 0x83
            _, mConfig_in_vu = project_api.get_mConfig_data()
            _, pConfig_in_vu = project_api.get_pConfig_data()
            compare_mConfig_data(get_mConfig=mConfig_in_vu, set_mConfig=mConfig_in_vu_bkup)
            compare_pConfig_data(get_pConfig=pConfig_in_vu, set_pConfig=pConfig_in_vu_bkup)
            
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
        pass

    def post_process(self) -> None:
        pass

    def set_mConfig_pConfig_data_and_check_resp(self,input:Union[project_api.mConfig, project_api.pConfig, int], error_case:bool = False) -> None:
        # logger.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
        if isinstance(input, project_api.mConfig):
            response = project_api.set_mConfig_data(mConfig=input, keep_error=error_case)
        elif isinstance(input, project_api.pConfig):
            response = project_api.set_pConfig_data(pConfig=input, keep_error=error_case)
        elif isinstance(input, int):
            response =  project_api.issue_C056_to_set_mConfig_data(set_option=input, payload=bytearray(4096), keep_error=error_case)
        else:
            raise PATTERN_ASSERT_ATTR_NOT_FOUND
        if error_case:
            if not (response.upiu.b6_response == UPIUResponse.TARGET_FAILURE and response.upiu.b7_status == ScsiStatus.CHECK_CONDITION):
                logger.error_lb(f'issue set mconfig data with wrong parameter')
                logger.error_fp(f'expect response fail, but status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}')
                raise SIGHTING_RESPONSE_UNEXPECTED
        pass
    
    def send_FFU_and_check_response(self, bin_buff: bytearray, error_case:bool = False) -> None:
        chunksize = len(bin_buff)
        bin_offset = 0
        if error_case:
            write_buffer = ExecuteCMD.WriteBuffer()
            write_buffer.assign(lun=0, mode=0x0E, buffer_id=0, buffer_offset=bin_offset, length=chunksize, vendor=False)
            write_buffer.data = bin_buff[bin_offset:]
            cmd = ExecuteCMD.enqueue(write_buffer)
            try:
                ExecuteCMD.send(clear_on_success=False)
                response = ExecuteCMD.read_response(cmd)
            except DLL_RESPONSE_ERROR:
                response = ExecuteCMD.read_response(cmd)
                logger.warning(f"lun = {response.upiu.b2_lun}, task_tag = {hex(response.upiu.b3_tasktag)},  response = {get_cmd_response_byte_str(response)}, status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}")
                ExecuteCMD.clear()
            if not (response.upiu.b6_response == UPIUResponse.TARGET_FAILURE and response.upiu.b7_status == ScsiStatus.CHECK_CONDITION):
                logger.error_lb(f'issue FFW write buffer with wrong parameter m/p config')
                logger.error_fp(f'expect response fail, but status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}')
                raise SIGHTING_RESPONSE_UNEXPECTED
        else:
            api.send_ffu_write_buffer(chunksize=chunksize, bin_offset=bin_offset, bin_buff=bin_buff)
        return

run = Pattern().run
if __name__ == "__main__":
    run()