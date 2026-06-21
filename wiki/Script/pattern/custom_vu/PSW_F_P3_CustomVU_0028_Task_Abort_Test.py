import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script import Result
from Script.api.exception import *
from typing import cast
from Script.api import shared
from Script.api.ufs_api import *
from Script.api.cmd_seq import QueryResponse
from Script.api.ufs_api.vendor_cmd.structs import FwGeometry
from typing import Callable
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_data_in_vcmd
from typing import List
from Script.api.ufs_api.upiu import structs
import copy
from Script.lib import sdk_lib as lib
_sdk = shared.sdk


class TestCase(IntEnum):
    ONLY_WRITE = 0
    ONLY_READ = 1
    ONLY_VERIFY = 2
    ONLY_OTHER = 3
    RANDOM = 4

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        self.region_id = RPMBRegion.REGION_0
        self.total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        pass
    def step1(self) -> None:
        shared.sdk.clear_done_queue(HostDoneQueueType.ALL_DONE_QUEUE_ERR_HANDLE, 0)
        logger.flow(1, 'Precondition')
        logger.flow("1-1", 'Config multi lun (32 lun, mem = random(em1, normal), au = total au / 32)')
        self.config_lun()
        logger.flow("1-2", 'Send mode sense get all 32 lun control page')
        self.control_page_data_list = self.get_mode_sense_data()
        logger.flow("1-3", 'rpmb region 0 program key')
        rpmb = RPMB(RPMBRegion.REGION_0)
        try:
            write_counter = rpmb.rpmb_read_counter()
        except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
            key_is_cleared = True
            logger.info("Flow = RPMB key is cleared")
            rpmb.rpmb_key_programming()


        for tm_func in [TaskManagementFunction.ABORT_TASK, TaskManagementFunction.ABORT_TASK_SET, TaskManagementFunction.CLEAR_TASK_SET, TaskManagementFunction.LU_RESET]:
            logger.flow("2-0", f'TM = {tm_func._name_}')

            logger.flow(2, 'Send VU D0B0 to enable assert Test')
            project_api.issue_D0B0_to_switch_abort_task_assert(enable=1)
            cmd_queue : List[int] = []

            logger.flow(3, 'Push random scsi cmd with task management')
            self.random_scsi(tm_func=tm_func,case=TestCase.RANDOM)

            logger.flow(4, 'Send cmd and expect trigger assert')
            self.send_cmd(cmd_queue)

            logger.flow(5, 'Check fw assert number')
            assert_number = api.get_fw_assert_number()
            if assert_number != 0xF400:
                logger.error(f'Enable assert, and send TM, expect get assert number = 0xF400, but get = {format(assert_number, "04X")}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(6, 'random unipro reset / endpoint reset expect fail')
            reset_type = random.choice([Dcmd5ResetType.UNIPRO_RESET, Dcmd5ResetType.ENDPOINT_RESET])
            self.expect_reset_fail(reset_type)

            logger.flow(7, 'power cycle')
            api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)
            response, self.health_report = project_api.issue_40FE_to_read_enhanced_health_report() 
            if (self.health_report.latest_assert_or_panic_triggered.value != 0xF400) or (self.health_report.total_panic_count.value == 0):
                logger.error(f'Enable assert, and send TM, self.health_report.latest_assert_or_panic_triggered.value({format(self.health_report.latest_assert_or_panic_triggered.value, "04X")}) != 0xF400\
                             self.health_report.total_panic_count {self.health_report.total_panic_count.value} = 0')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL      
            #self.clear_assert_page()
            logger.flow(8, 'Check fw assert number')
            assert_number = api.get_fw_assert_number()
            if assert_number != 0x0:
                logger.error(f'Enable assert, and send TM, after clear assert number , expect get assert number = 0x0, but get = {format(assert_number, "04X")}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(9, 'Push random scsi cmd with task management')
            abort_list = self.random_scsi(tm_func=tm_func,case=TestCase.RANDOM)
            if tm_func == TaskManagementFunction.LU_RESET:
                _, tm_idx = abort_list[-1]
                upiu = cast(CommandUpiu[Any], ExecuteCMD._cmd_list[tm_idx].upiu)
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(upiu.b2_lun, wait_queue_empty=True)
                ExecuteCMD.enqueue(test_unit_ready)
            logger.flow(10, 'Send cmd expect pass') 
            ExecuteCMD.send(clear_on_success=False)
            ExecuteCMD.clear()

            ###########################################################
            logger.flow(11, 'Send VU D0B0 to disable assert Test')
            project_api.issue_D0B0_to_switch_abort_task_assert(enable=0)

            logger.flow(12, 'Send VU 40F0 to get task abort hit information')
            
            for case in TestCase:
                data_40F0_backup = project_api.issue_40F0_to_get_task_abort_hit_information()
                self.print_40F0(data_40F0_backup)
                logger.flow(13, f'Case = {case.name}')
                logger.flow(13, 'Push random scsi with task management')
                abort_list = self.random_scsi(tm_func=tm_func,case=case)

                if tm_func == TaskManagementFunction.LU_RESET:
                    _, tm_idx = abort_list[-1]
                    upiu = cast(structs.CommandUpiu[Any], ExecuteCMD._cmd_list[tm_idx].upiu)
                    test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                    test_unit_ready.set_option(upiu.b2_lun, wait_queue_empty=True)
                    ExecuteCMD.enqueue(test_unit_ready)

                logger.flow(13, 'Send cmd') 
                abort_w_cnt = 0
                abort_r_cnt = 0
                abort_other_cnt = 0
                verify_cnt = 0
                ExecuteCMD.send(timeout=api.UniformTimeout(val=30000, unit=api.TimeResolution.ms), clear_on_success=False)
                for target_index, tm_index in abort_list:
                    abort = api.check_if_target_is_aborted(target_index, tm_index)
                    if abort == False:
                        target_upiu = cast(CommandUpiu[Any], ExecuteCMD._cmd_list[target_index].upiu)
                        
                        cmd = target_upiu.u16_cdb.to_bytes()[0]
                        if cmd == ScsiCmd.WRITE_6 or cmd == ScsiCmd.WRITE_10 or cmd == ScsiCmd.WRITE_16:
                            abort_w_cnt += 1
                        elif cmd == ScsiCmd.READ_6 or cmd == ScsiCmd.READ_10 or cmd == ScsiCmd.READ_16:
                            abort_r_cnt += 1
                        elif cmd == ScsiCmd.VERIFY_10:
                            abort_other_cnt += 1
                            verify_cnt += 1
                        else:
                            abort_other_cnt += 1
                        logger.info(f'index = {target_index} is aborted by tm index = {tm_index}')
                    
                ExecuteCMD.clear()
                
                logger.info(f'abort write = {abort_w_cnt}, abort read = {abort_r_cnt}, verify cnt = {verify_cnt}, abort other cnt = {abort_other_cnt}')
                total_abort_cnt = abort_w_cnt + abort_r_cnt + abort_other_cnt
                logger.flow(14, 'Send VU 40F0 to get task abort hit information')
                data_40F0 = project_api.issue_40F0_to_get_task_abort_hit_information()

                logger.flow(15, 'Check 40F0 value is as expect')
                self.print_40F0(data_40F0)
                diff = data_40F0.num_of_write_cmd_been_abort.value - data_40F0_backup.num_of_write_cmd_been_abort.value
                if diff != abort_w_cnt:
                    logger.error(f'Expect 40F0 num of write cmd been abort increase {abort_w_cnt}, but increase {diff}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                diff = data_40F0.num_of_read_cmd_been_abort.value - data_40F0_backup.num_of_read_cmd_been_abort.value
                if diff != abort_r_cnt:
                    logger.error(f'Expect 40F0 num of read cmd been abort increase {abort_r_cnt}, but increase {diff}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                diff = data_40F0.num_of_other_cmd_been_abort.value - data_40F0_backup.num_of_other_cmd_been_abort.value
                if diff != abort_other_cnt:
                    logger.error(f'Expect 40F0 num of other cmd been abort increase {abort_other_cnt}, but increase {diff}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                diff = data_40F0.total_number_of_abort_cmd.value - data_40F0_backup.total_number_of_abort_cmd.value
                if diff != total_abort_cnt:
                    logger.error(f'Expect 40F0 num of abort cmd increase {total_abort_cnt}, but increase {diff}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

                diff = data_40F0.verify_abort_cmd_wait.value - data_40F0_backup.verify_abort_cmd_wait.value
                if diff != verify_cnt:
                    logger.error(f'Expect 40F0 verify abort cmd wait increase {verify_cnt}, but increase {diff}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

                if data_40F0.verify_abort_rw_done_wait.value != 0:
                    logger.error(f'Expect 40F0 verify_abort_rw_done_wait =0, but = {data_40F0.verify_abort_rw_done_wait.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                if data_40F0.verify_abort_flush_done_wait.value  != 0:
                    logger.error(f'Expect 40F0 verify_abort_flush_done_wait =0, but = {data_40F0.verify_abort_flush_done_wait.value }')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                if data_40F0.verify_abort_data_check_done_wait.value != 0:
                    logger.error(f'Expect 40F0 verify_abort_data_check_done_wait =0, but = {data_40F0.verify_abort_data_check_done_wait.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                if data_40F0.verify_abort_repsonse_down_wait.value != 0:
                    logger.error(f'Expect 40F0 verify_abort_repsonse_down_wait =0, but = {data_40F0.verify_abort_repsonse_down_wait.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

                if data_40F0.l24_rev.value != 0:
                    logger.error(f'Expect 40F0 l24_rev =0, but = {data_40F0.l24_rev.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                if data_40F0.l36_rev.value  != 0:
                    logger.error(f'Expect 40F0 l24_rev =0, but = {data_40F0.l24_rev.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                if data_40F0.num_of_cmd_still_in_HW_queue.value < data_40F0_backup.num_of_cmd_still_in_HW_queue.value :
                    logger.error(f'Expect 40F0 num_of_cmd_still_in_HW_queue not less than 40F0 backup, but backup = {data_40F0_backup.num_of_cmd_still_in_HW_queue.value}, current = {data_40F0.num_of_cmd_still_in_HW_queue.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

                if data_40F0.abort_read_during_cmd_analysis_stage.value < data_40F0_backup.abort_read_during_cmd_analysis_stage.value :
                    logger.error(f'Expect 40F0 abort_read_during_cmd_analysis_stage not less than 40F0 backup, but backup = {data_40F0_backup.abort_read_during_cmd_analysis_stage.value}, current = {data_40F0.abort_read_during_cmd_analysis_stage.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

                if data_40F0.abort_read_during_dtm_read_queue_status_report_stage.value < data_40F0_backup.abort_read_during_dtm_read_queue_status_report_stage.value :
                    logger.error(f'Expect 40F0 abort_read_during_cmd_analysis_stage not less than 40F0 backup, but backup = {data_40F0_backup.abort_read_during_dtm_read_queue_status_report_stage.value}, current = {data_40F0.abort_read_during_dtm_read_queue_status_report_stage.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

                if data_40F0.abort_write_during_cmd_analysis_stage.value < data_40F0_backup.abort_write_during_cmd_analysis_stage.value  :
                    logger.error(f'Expect 40F0 abort_write_during_cmd_analysis_stage not less than 40F0 backup, but backup = {data_40F0_backup.abort_write_during_cmd_analysis_stage.value }, current = {data_40F0.abort_write_during_cmd_analysis_stage.value }')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                if data_40F0.abort_write_during_dtm_write_queue_status_report_stage.value< data_40F0_backup.abort_write_during_dtm_write_queue_status_report_stage.value :
                    logger.error(f'Expect 40F0 abort_write_during_dtm_write_queue_status_report_stage not less than 40F0 backup, but backup = {data_40F0_backup.abort_write_during_dtm_write_queue_status_report_stage.value}, current = {data_40F0.abort_write_during_dtm_write_queue_status_report_stage.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                if data_40F0.abort_write_after_dataout_fill_write_cache.value < data_40F0_backup.abort_write_after_dataout_fill_write_cache.value :
                    logger.error(f'Expect 40F0 abort_write_after_dataout_fill_write_cache not less than 40F0 backup, but backup = {data_40F0_backup.abort_write_after_dataout_fill_write_cache.value}, current = {data_40F0.abort_write_after_dataout_fill_write_cache.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                if data_40F0.abort_cmd_but_it_may_send_response_at_last.value < data_40F0_backup.abort_cmd_but_it_may_send_response_at_last.value :
                    logger.error(f'Expect 40F0 abort_cmd_but_it_may_send_response_at_last not less than 40F0 backup, but backup = {data_40F0_backup.abort_cmd_but_it_may_send_response_at_last.value}, current = {data_40F0.abort_cmd_but_it_may_send_response_at_last.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                data_40F0_backup = copy.deepcopy(data_40F0)

        pass
    def expect_reset_fail(self,reset_type:Dcmd5ResetType) ->None:
        try:
            api.init_tester_to_unit_ready(reset_type)
        except Exception as e:               
            print(f"reset fail: {e!r}")
        else:
            raise DCMD5_LINK_STARTUP_FAIL

    def print_40F0(self,output:project_api.VU_40F0_struct) -> None:
        logger.info(f'num_of_cmd_still_in_HW_queue = {output.num_of_cmd_still_in_HW_queue.value}')
        logger.info(f'num_of_read_cmd_been_abort  = {output.num_of_read_cmd_been_abort.value}')
        logger.info(f'num_of_write_cmd_been_abort  = {output.num_of_write_cmd_been_abort.value}')
        logger.info(f'num_of_other_cmd_been_abort  = {output.num_of_other_cmd_been_abort.value}')
        logger.info(f'abort_read_during_cmd_analysis_stage  = {output.abort_read_during_cmd_analysis_stage.value}')
        logger.info(f'nabort_read_during_dtm_read_queue_status_report_stage  = {output.abort_read_during_dtm_read_queue_status_report_stage.value}')
        logger.info(f'l24_rev  = {output.l24_rev.value}')
        logger.info(f'abort_write_during_cmd_analysis_stage = {output.abort_write_during_cmd_analysis_stage.value}')
        logger.info(f'abort_write_during_dtm_write_queue_status_report_stage  = {output.abort_write_during_dtm_write_queue_status_report_stage.value}')
        logger.info(f'l36_rev  = {output.l36_rev.value}')
        logger.info(f'abort_write_after_dataout_fill_write_cache  = {output.abort_write_after_dataout_fill_write_cache.value}')
        logger.info(f'abort_cmd_but_it_may_send_response_at_last  = {output.abort_cmd_but_it_may_send_response_at_last.value}')
        logger.info(f'total_number_of_abort_cmd  = {output.total_number_of_abort_cmd.value}')
        logger.info(f'verify_abort_cmd_wait  = {output.verify_abort_cmd_wait.value}')
        logger.info(f'verify_abort_rw_done_wait  = {output.verify_abort_rw_done_wait.value}')
        logger.info(f'verify_abort_flush_done_wait  = {output.verify_abort_flush_done_wait.value}')
        logger.info(f'verify_abort_data_check_done_wait  = {output.verify_abort_data_check_done_wait.value}')
        logger.info(f'verify_abort_repsonse_down_wait  = {output.verify_abort_repsonse_down_wait.value}')

    def get_mode_sense_data(self) -> List[bytearray]:
        control_page_data_list = []
        for lun in range(32):
            f = ExecuteCMD.ModeSense10()
            f.assign(lun=lun,pc=0,page_code=0xA,subpage_code=0,length=0x14)
            ExecuteCMD.enqueue(f)
            ExecuteCMD.send(clear_on_success=False)
            rsp = ExecuteCMD.read_response(0)
            control_page_data_list.append(rsp.data)
            ExecuteCMD.clear()
        return control_page_data_list
    def send_cmd(self, cmd_queue:List[int]) -> None:
        try:
            ExecuteCMD.send(clear_on_success=False)
            response = ExecuteCMD.read_response(cmd_queue[-1])
        except (api.ApiErrorBase, api.sdk_lib.CommonLibErrorBase) as e:
            errcode = e.__class__.__name__
            result = Result(is_ok=False, err_code=errcode)
            logger.error(f"Pattern Result: [FAIL]. Error Code = {errcode}")
        ExecuteCMD.clear()
        
    def push_write_6(self) -> int:
        lun = random.randint(0,31)
        length = random.randint(1,WRITE_6_MAX_BLOCK_LEN)
        f = ExecuteCMD.Write6()
        f.assign(lun=lun, lba=0, length=length)
        return ExecuteCMD.enqueue(f)
    def push_write_10(self) -> int:
        lun = random.randint(0,31)
        length = random.randint(1,WRITE_10_MAX_BLOCK_LEN)
        f = ExecuteCMD.Write10()
        f.assign(lun=lun, lba=0, length=length,fua=0)
        return ExecuteCMD.enqueue(f)
    def push_write_16(self) -> int:
        lun = random.randint(0,31)
        length = random.randint(1,min(self._param.gLUCapacity[lun],WRITE_16_MAX_BLOCK_LEN))
        f = ExecuteCMD.Write16()
        f.assign(lun=lun, lba=0, length=1,fua=0)
        return ExecuteCMD.enqueue(f)
    def push_read_6(self) -> int:
        lun = random.randint(0,31)
        length = random.randint(1,READ_6_MAX_BLOCK_LEN)
        f = ExecuteCMD.Read6()
        f.assign(lun=lun, lba=0, length=1)
        return ExecuteCMD.enqueue(f)
    def push_read_10(self) -> int:
        lun = random.randint(0,31)
        length = random.randint(1,READ_10_MAX_BLOCK_LEN)
        f = ExecuteCMD.Read10()
        f.assign(lun=lun, lba=0, length=1)
        return ExecuteCMD.enqueue(f)
    def push_read_16(self) -> int:
        lun = random.randint(0,31)
        length = random.randint(1,min(self._param.gLUCapacity[lun],READ_16_MAX_BLOCK_LEN))
        f = ExecuteCMD.Read16()
        f.assign(lun=lun, lba=0, length=1)
        return ExecuteCMD.enqueue(f)
    def push_unmap(self) -> int:
        lun = random.randint(0,31)
        length = random.randint(1,self._param.gLUCapacity[lun])  #too big?
        f = ExecuteCMD.Unmap()
        f.assign(lun=lun, lba=0, length=length)
        return ExecuteCMD.enqueue(f)
    
    def push_read_capacity_10(self) -> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.ReadCapacity10()
        f.assign(lun=lun)
        return ExecuteCMD.enqueue(f)

    def push_read_capacity_16(self) -> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.ReadCapacity16()
        f.assign(lun=lun,alloc_length=0x20)
        return ExecuteCMD.enqueue(f)
    def push_write_buffer(self) -> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.WriteBuffer()
        f.assign(lun=lun,mode=WriteBufferMode.DATA,buffer_id=0,buffer_offset=0,length=DATA_SIZE_4K_BYTE)
        return ExecuteCMD.enqueue(f)

    def push_read_buffer(self) -> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.ReadBuffer()
        f.assign(lun=lun,mode=ReadBufferMode.DATA,buffer_id=0,buffer_offset=0,length=DATA_SIZE_4K_BYTE) 
        return ExecuteCMD.enqueue(f)
    
    def push_sync_cache_10(self) -> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.SyncCache10()
        f.assign(lun=lun, immed=0, lba=0, length=0)
        return ExecuteCMD.enqueue(f)

    def push_sync_cache_16(self) -> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.SyncCache16()
        f.assign(lun=lun, immed=0, lba=0, length=0)
        return ExecuteCMD.enqueue(f)

    def push_report_luns(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.ReportLUNs()
        f.assign(lun=lun,sel_report=0,length=(8+32*8)) #too big?
        return ExecuteCMD.enqueue(f)

    def push_verify(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.Verify10()
        f.assign(lun=lun,lba=0,length=BLOCK4K_SIZE_4K_BYTE) #too big?
        return ExecuteCMD.enqueue(f)

    def push_ssu(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.StartStopUnit()
        f.assign(lun=lun,immed=0,power_condition=0, no_flush=0,start=1) #too big?
        return ExecuteCMD.enqueue(f)

    def push_inquiry(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.Inquiry()
        f.assign(lun=lun) 
        return ExecuteCMD.enqueue(f)

    def push_formart_unit(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.FormatUnit()
        f.assign(lun=lun) 
        return ExecuteCMD.enqueue(f)

    def push_prefetch_10(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.PreFetch10()
        f.assign(lun=lun, immed=0,lba=0,length=1) 
        return ExecuteCMD.enqueue(f)

    def push_prefetch_16(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.PreFetch16()
        f.assign(lun=lun, immed=0,lba=0,length=1) 
        return ExecuteCMD.enqueue(f)

    def push_test_unit_ready(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.TestUnitReady()
        f.assign(lun=lun) 
        return ExecuteCMD.enqueue(f)

    def push_send_diagnostic(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.SendDiagnostic()
        f.assign(lun=lun,selftest_code=0,pf=0,selftest=0,dev=0,unit=0,length=0) 
        return ExecuteCMD.enqueue(f)

    def push_protocol_in(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.SecurityProtocolIn()
        f.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512)
        return ExecuteCMD.enqueue(f)

    def push_protocol_out(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.SecurityProtocolOut()
        f.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512)
        return ExecuteCMD.enqueue(f)

    def push_mode_sense(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.ModeSense10()
        f.assign(lun, pc=0,page_code=0xA,subpage_code=0,length=0x14)
        return ExecuteCMD.enqueue(f)

    def push_mode_select(self)-> int:
        lun = random.randint(0,31)
        f = ExecuteCMD.ModeSelect10()
        f.assign(lun,sp=0,length=0x14)
        f.data = self.control_page_data_list[lun]
        return ExecuteCMD.enqueue(f)
    
    def push_task_management(self, target_idx:int, tm_func:TaskManagementFunction) -> int:
        target = ExecuteCMD._cmd_list[target_idx]
        target.upiu = cast(CommandUpiu[Any], target.upiu)
        target_lun = target.upiu.b2_lun
        target_tasktag = target.upiu.b3_tasktag
        target_iid = target.upiu.b4_iid
        tm = ExecuteCMD.TaskManagement()
        tm.assign(lun=target_lun, iid=target_iid, task_management_function=tm_func,
                    target_lun=target_lun, target_tasktag=target_tasktag, target_iid=target_iid)
        return ExecuteCMD.enqueue(tm)
    
    
    def random_scsi(self, tm_func:TaskManagementFunction,case:int) -> List[tuple[int,int]]:
        
        abort_list = []
        TOTAL_CMDS = 3 
        if case == TestCase.ONLY_WRITE:
            cmd_pool = [self.push_write_6,self.push_write_10, self.push_write_16]
        elif case == TestCase.ONLY_READ:
            cmd_pool = [self.push_read_6,self.push_read_10, self.push_read_16]
        elif case == TestCase.ONLY_VERIFY:
            cmd_pool = [self.push_verify]
        elif case == TestCase.ONLY_OTHER:
            cmd_pool = [self.push_unmap,self.push_write_buffer,self.push_read_buffer,self.push_read_capacity_10,
                        self.push_read_capacity_16,self.push_sync_cache_10, self.push_report_luns,
                        self.push_ssu,self.push_inquiry,self.push_prefetch_10,self.push_prefetch_16, self.push_sync_cache_16, 
                        self.push_test_unit_ready,self.push_protocol_in,self.push_protocol_out, 
                        self.push_mode_sense,self.push_mode_select, self.push_formart_unit, self.push_send_diagnostic] #
        elif case == TestCase.RANDOM:
            cmd_pool = [self.push_write_6, self.push_write_10, self.push_read_6, self.push_read_10,
                        self.push_unmap,self.push_write_buffer,self.push_read_buffer,self.push_read_capacity_10,
                        self.push_read_capacity_16,self.push_sync_cache_10, self.push_report_luns,
                        self.push_ssu,self.push_inquiry,self.push_prefetch_10,
                        self.push_test_unit_ready,self.push_protocol_in,self.push_protocol_out, self.push_write_16,self.push_read_16, self.push_sync_cache_16, self.push_prefetch_16, 
                        self.push_mode_sense,self.push_mode_select,self.push_verify, self.push_formart_unit, self.push_send_diagnostic]  #
        
        possible_positions = list(range(1, TOTAL_CMDS))          
        tm_positions: List[int] = []

        #first_tm = random.choice(possible_positions)
        first_tm = TOTAL_CMDS - 1
        tm_positions.append(first_tm)
     
        logger.info(f"TM positions: {tm_positions}")
        
        prev_info: str = ""       
        pre_cmd_idx = -1
        pre_cmd_idexes : list[int] = []
        pre_cmd_luns : list[int] = []
        for idx in range(TOTAL_CMDS):
            if idx in tm_positions:
                cmd = cast(CommandUpiu[Any], ExecuteCMD._cmd_list[pre_cmd_idx].upiu)
                tm_lun = cmd.b2_lun
                tm_idx = self.push_task_management(pre_cmd_idx, tm_func)                     
                if tm_func == TaskManagementFunction.ABORT_TASK:
                    abort_list.append((pre_cmd_idx, tm_idx))
                    logger.info(
                        f"idx={idx}: TM executed (prev_idx={pre_cmd_idx}, tm_idx={tm_idx})"
                    )
            else:
                push_cmd = random.choice(cmd_pool)
                pre_cmd_idx = push_cmd()
                cmd = cast(CommandUpiu[Any], ExecuteCMD._cmd_list[pre_cmd_idx].upiu)
                pre_cmd_idexes.append(pre_cmd_idx)
                pre_cmd_luns.append(cmd.b2_lun)
                
        if tm_func == TaskManagementFunction.ABORT_TASK_SET or tm_func == TaskManagementFunction.CLEAR_TASK_SET or tm_func == TaskManagementFunction.LU_RESET:
            for idx, lun in enumerate(pre_cmd_luns):
                if lun == tm_lun:
                    abort_list.append((pre_cmd_idexes[idx], tm_idx))
                    logger.info(
                        f"TM executed (prev_idx={pre_cmd_idexes[idx]}, tm_idx={tm_idx})"
                    )
        return abort_list

    def config_lun(self) -> None:
    
        config_descs = api.get_config_descriptors(print=True)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xc
                config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                config_descs[table].units[unit].b0_lu_enable = 1
                config_descs[table].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1 if random.randint(0, 1) else api.MemoryType.NORMAL
                config_descs[table].units[unit].l4_num_alloc_units = self.total_au // self._param.gMaxNumberLU
        
        config_descs[3].header.b2_conf_desc_continue = 0
        config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0
        for i in range(4):
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        ExecuteCMD.clear()

        unit_desc_idxes:List[int] = []
        for lun in range(0, self._param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            update_descriptor(DescriptorIDN.UNIT, index, cast(QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        #test unit ready all enable lun
        for lun in range(self._param.gMaxNumberLU):
            if self._param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

    def compare_value(self, value:int,expect_value:int) -> None:
        if value != expect_value:
            logger.error(f'Expect ={expect_value}, but = {value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'val = {value}')
    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()