import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.read_disturb.mutual_fun import *
from Script.project_api.functions import print_object_info_ai
from typing import Optional

class Pattern(UFSTC):
    def pre_process(self) -> None:
        leave_inhibition_mode()
        self.fw_geometry = api.get_fw_geometry()
        self.write_record = api.get_empty_write_record()
        _, self.debug_info = api.get_debug_info()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestWBLun = 2
        config_lun(normal_list=[self.TestNormalLun, self.TestWBLun], em1_list=[self.TestEM1Lun])
        self.startLBA: Dict[int, int] = {self.TestNormalLun: 0, self.TestEM1Lun:0, self.TestWBLun:0}
        _, self.mConfig_in_vu = project_api.get_mConfig_data()
        response, self.health_report_before = project_api.issue_40FE_to_read_enhanced_health_report()
        pass

    def step1(self) -> None:
        logger.flow(1, f"write data to create TLC/SLC/WB block")
        total_size = int(self.tlc_vb_size*2.5)
        lun = self.TestNormalLun
        api.sequential_write(lun=lun, start_lba=self.startLBA[lun], total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.startLBA[lun] += total_size
        total_size = int(self.slc_vb_size*2.5)
        lun = self.TestEM1Lun
        api.sequential_write(lun=lun, start_lba=self.startLBA[lun], total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.startLBA[lun] += total_size
        
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
        total_size = int(self.slc_vb_size*2.5)
        lun = self.TestWBLun
        api.sequential_write(lun=lun, start_lba=self.startLBA[lun], total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.startLBA[lun] += total_size
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        pass
    
    def step2(self) -> None:
        logger.flow(2, f"issue VU C088 to stop refresh")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        pass
                
    def step3(self) -> None:
        logger.flow(3, f"set some RC of VB = 0xFFFFFFFF (MAX_VALUE)")
        read_cnt_of_vb_before = project_api.get_all_VB_read_count()
        self.sorted_VB_list_dict_before = get_sorted_VB_list()
        self.refresh_vbs = []
        data_payload = bytearray(4096)
        self.set_vb_list = []
        
        self.VB_type_LUT = {
            i: key
            for key, lst in self.sorted_VB_list_dict_before.items()
            for i in lst
        }

        type_to_field = {
            project_api.VBListNum.CURRENT_L2_EM1:     'read_disturb_refresh_start_count_em1',
            project_api.VBListNum.USED_BLK_POOL_EM1:  'read_disturb_refresh_start_count_em1',
            project_api.VBListNum.CURRENT_L2_TLC:     'read_disturb_refresh_start_count_normal_tlc',
            project_api.VBListNum.USED_BLK_POOL_TLC:  'read_disturb_refresh_start_count_normal_tlc',
            project_api.VBListNum.CURRENT_L2_TLC_WB:  'read_disturb_refresh_start_count_normal_slc',
            project_api.VBListNum.USED_BLK_POOL_TLC_WB: 'read_disturb_refresh_start_count_normal_slc',
            project_api.VBListNum.PTE_POOL:           'read_disturb_refresh_start_count_table',
            project_api.VBListNum.CURRENT_PTE:        'read_disturb_refresh_start_count_table',
        }
        self.expected_refresh_increase = {v: 0 for v in set(type_to_field.values())}

        for type, vb_list in self.sorted_VB_list_dict_before.items():
            if type in type_to_field:
                self.set_vb_list += vb_list
                self.expected_refresh_increase[type_to_field[type]] += len(vb_list)
        for vb in range(self.fw_geometry.l52_total_vb_count):
            if vb in self.set_vb_list:
                set_value = 0xFFFFFFFF-1
                logger.info(f"Set RC of VB {vb} = 0x{set_value:X}, Oringinal type: {self.VB_type_LUT.get(vb, project_api.VBListNum.OTHER).name}")
                data_payload[vb*4:(vb+1)*4] = (set_value).to_bytes(4, 'little')
                self.refresh_vbs.append(vb)
            else:
                data_payload[vb*4:(vb+1)*4] = read_cnt_of_vb_before[vb].to_bytes(4, 'little')
        project_api.set_all_VB_read_count(data_payload=data_payload)
        
        read_cnt_of_vb = project_api.get_all_VB_read_count()
        for vb in range(self.fw_geometry.l52_total_vb_count):
            if vb in self.refresh_vbs and read_cnt_of_vb[vb] != set_value:
                logger.error_lb(f'check erase cnt of VB {vb}')
                logger.error_fp(f'expect RC from VU4097 equal to {set_value}, but VU value = {read_cnt_of_vb[vb]}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f"Expected refresh start count increase: {self.expected_refresh_increase}")
        pass
    
    def step4(self) -> None:
        logger.flow(4, f"Reading data leads to an increase in RC.")
        api.read_compare(write_record = self.write_record)
        read_cnt_of_vb = project_api.get_all_VB_read_count()
        for vb in range(self.fw_geometry.l52_total_vb_count):
            if vb in self.refresh_vbs:
                logger.info(f"RC of VB {vb} = 0x{read_cnt_of_vb[vb]:X}, Oringinal type: {self.VB_type_LUT.get(vb, project_api.VBListNum.OTHER).name}")
        pass
    
    def step5(self) -> None:
        logger.flow(5, f"issue VU 40C5 to check the refresh booking queue")
        _, booking_q = project_api.issue_40C5_to_get_booking_queue()
        if booking_q.LogicalVBNumberInBookingQueue.value == 0:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after RC[VB] reaches max value 0xFFFFFFFF')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is not 0, but current value = {booking_q.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        for idx, VBs in enumerate(booking_q.BookingQueueVB):
            vb = VBs.LogicalVBNumber.value
            Priority_bit = project_api.BookingUser(VBs.TheBookingUser.value & 0x700)
            if Priority_bit == project_api.BookingUser.BOOKING_IN_HP:
                Priority = project_api.VUC087Paremeter.HighPriority
            elif Priority_bit == project_api.BookingUser.BOOKING_IN_MP:
                Priority = project_api.VUC087Paremeter.MediumPriority
            else:
                Priority = project_api.VUC087Paremeter.LowPriority
            TheBookingUser = project_api.BookingUser(VBs.TheBookingUser.value & project_api.BookingUser.MAX_BOOKING_USER_COUNT-1)
            logger.info(f'BookingQ[{idx}]: VB {vb}, TheBookingUser: {TheBookingUser.name} ({Priority.name}), Oringinal type: {self.VB_type_LUT.get(vb, project_api.VBListNum.OTHER).name}')
            expect_user = project_api.BookingUser.RD_SCAN_BOOKING_1
            expect_priority = project_api.VUC087Paremeter.HighPriority
            if vb not in self.refresh_vbs:
                logger.error_lb(f'check vb {vb} after Booking')
                logger.error_fp(f'VB {vb} is {Priority_bit.name},  but not in expect list {self.refresh_vbs}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if expect_user != TheBookingUser or expect_priority != Priority:
                logger.error_lb(f'check vb {vb} after Booking')
                logger.error_fp(f'expect VB {vb} is {expect_user.name} ({expect_priority.name}),  but current is {TheBookingUser.name} ({Priority.name}), result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                pass     
            self.refresh_vbs.remove(vb)
        if self.refresh_vbs:
            logger.error_lb(f'check all vb book in refresh booking queue')
            logger.error_fp(f'expect VBs {self.refresh_vbs} is booked, but not found in 40C5, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            pass
        
    def step6(self) -> None:
        logger.flow(6, f"issue VU C088 to start refresh and polling bkops idle")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        polling_bkops_idle()
        pass

    def step7(self) -> None:
        logger.flow(7, f"issue VU 40FE to check health report value after refresh")
        response, health_report = project_api.issue_40FE_to_read_enhanced_health_report()
        self.print_struct_different(self.health_report_before, health_report)
        self.check_value_increase(self.health_report_before, health_report, 'read_disturb_refresh_start_count_em1', self.expected_refresh_increase['read_disturb_refresh_start_count_em1'])
        self.check_value_increase(self.health_report_before, health_report, 'read_disturb_refresh_start_count_normal_tlc', self.expected_refresh_increase['read_disturb_refresh_start_count_normal_tlc'])
        self.check_value_increase(self.health_report_before, health_report, 'read_disturb_refresh_start_count_normal_slc', self.expected_refresh_increase['read_disturb_refresh_start_count_normal_slc'])
        self.check_value_increase(self.health_report_before, health_report, 'read_disturb_refresh_start_count_table', self.expected_refresh_increase['read_disturb_refresh_start_count_table'])
        pass
    
    def check_value_increase(self, before_value: Any, cur_value: Any, string:str, expected_increase: Optional[int] = None) -> None:
        current_fields = [
            (name, field) for name, field in cur_value.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        current_fields.sort(key=lambda kv: kv[1].start_offset)
        before_fields = [
            (name, field) for name, field in before_value.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        before_fields.sort(key=lambda kv: kv[1].start_offset)
        
        for (name0, current), (name1, before) in zip(
                                    current_fields,
                                    before_fields,
                                ):
            if name0 == string:
                value = current.value
                value_before = before.value
                if expected_increase is not None:
                    actual_increase = value - value_before
                    if actual_increase != expected_increase:
                        logger.error_lb(f'check {string} increase amount')
                        logger.error_fp(f'expect {string} increased by {expected_increase}, but actual increase = {actual_increase}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    if value <= value_before:
                        logger.error_lb(f'check {string} should increase')
                        logger.error_fp(f'expect {string} increased, but current value = {value}, before value = {value_before}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                return
            pass


    def print_struct_different(self, before_value: Any, after_value: Any) -> None:
        raw_fields = [
            (name, field) for name, field in before_value.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        raw_fields.sort(key=lambda kv: kv[1].start_offset)
        expect_fields = [
            (name, field) for name, field in after_value.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        expect_fields.sort(key=lambda kv: kv[1].start_offset)
        
        for (name0, raw), (name1, expect) in zip(
                                    raw_fields,
                                    expect_fields,
                                ):
            if hasattr(raw, "value") and hasattr(expect, "value") and name0 == name1:
                if raw.value != expect.value:
                    logger.info(f'{name0}: {raw.value} (0x{raw.value:X}) -> {expect.value} (0x{expect.value:X})')
            pass
    
    def post_process(self) -> None:
        pass
    
    

run = Pattern().run
if __name__ == "__main__":
    run()