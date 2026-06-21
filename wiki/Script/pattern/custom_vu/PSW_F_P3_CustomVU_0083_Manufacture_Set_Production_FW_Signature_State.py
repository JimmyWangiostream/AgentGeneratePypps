import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.project_api.erase_program_fail.structs import PhysicalAddressInformation
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.api.ufs_api import *
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd

def issue_data_in_vu_check_error(vu_id:str)->None:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = int(vu_id[2:],16)
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)

    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=True)
    if not (response.upiu.b6_response == api.UPIUResponse.TARGET_FAILURE and 
        response.upiu.b7_status == api.ScsiStatus.CHECK_CONDITION and
        response.b32_sense_data.b12_asc == 0x24):
            logger.error('Compare expected rsp invalid in cdb')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    ExecuteCMD.clear()   

def issue_no_data_vu_check_error(vu_id:str)->None:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = int(vu_id[2:],16)
    vu.b1_func.value = 0xD0
    vu.d8_split_pkg_index.value = 0
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=True)
    if not (response.upiu.b6_response == api.UPIUResponse.TARGET_FAILURE and 
        response.upiu.b7_status == api.ScsiStatus.CHECK_CONDITION and
        response.b32_sense_data.b12_asc == 0x24):
            logger.error('Compare expected rsp invalid in cdb')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL    
    ExecuteCMD.clear()   
def issue_data_out_vu_check_error(vu_id:str)->None:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = int(vu_id[2:],16)
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)
    payload = bytearray(4096) 
    
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= payload, keep_error=True)
    if not (response.upiu.b6_response == api.UPIUResponse.TARGET_FAILURE and 
        response.upiu.b7_status == api.ScsiStatus.CHECK_CONDITION and
        response.b32_sense_data.b12_asc == 0x24):
            logger.error('Compare expected rsp invalid in cdb')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    ExecuteCMD.clear()   
    
def issue_vu_illegal_test()->None:
    no_data_list = [
    "D00D","D00E","D00F","D010","D012","D014","D017","D018","D019","D01C",
    "D048","D04A","D04B","D04C","D060","D073","D074","D077","D078","D079",
    "D07A","D07C","D080","D083","D085","D089","D08B","D08C","D08E","D091",
    "D098","D0A0","D0A2","D0A3","D0A4","D0B1","D0E2","D0F4","D0FB","D0FC",
    "D0FE"
    ]
    for no_data_vu in no_data_list:
        issue_no_data_vu_check_error(no_data_vu)
    data_in_list = [
    "400F","4010","4011","4012","4013","4014","4023","4026","4027","4028",
    "4029","402C","402E","4047","4048","4049","404A","404B","404F","4055",
    "4056","4057","405A","405B","4060","4064","4066","4067","406A","406D",
    "4070","4071","4073","4076","4083","408D","4093","409D","409E","40A1",
    "40A8","40B1","40B6","40BB","40C2","40C3","40C5","40CC","40D1","40D2",
    "40D4","40D6","40D7","40DA","40DB","40DD","40E3","40E4","40E6","40E7",
    "40EE","40F0","40F2","40F3","40F5","40F6","40F7","40F8","40F9","4003",
    "4004"
    ]
    for data_in_vu in data_in_list:
        issue_data_in_vu_check_error(data_in_vu)
    data_out_list = [
    "C012","C04A","C04B","C04E","C04F","C056","C060","C071","C072","C083",
    "C084","C085","C087","C088","C08A","C08B","C08C","C0A0","C0BC","C0E0",
    "C0E1","C0E3","C0F0","C0F4","C0F6","C0F7"
    ]
    for data_out_vu in data_out_list:
        issue_data_out_vu_check_error(data_out_vu)
class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.flow(1, 'issue_40E2_to_get_device_state')
        _, device_state, NumOfRemainingStateChanges = project_api.issue_40E2_to_get_device_state()
        if device_state == 0:
            resp = project_api.issue_406D_get_VB_list_info()
        else:
            #rsp , GetNandTemperature = project_api.issue_4021_get_nand_temperature()
            logger.flow(2,'Start Test for disable vu')
            issue_vu_illegal_test()
    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
