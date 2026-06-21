import math
import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.api.ufs_api.defines.bit_define import *
from Script.api.ufs_api.defines.constant_define import *
from typing import List, cast, Any, Callable
from enum import Enum, IntEnum
from Script.project_api.custom_vu.get_params_of_ftl_status_vu import PowerLossFlag, OpenDataVBType, OpenSystemVBType
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api import vendor_cmd
from Script.project_api.reh.functions import issue_40F9_to_get_rr_number_and_error_bits, issue_D014_to_set_last_table_content, issue_D014_to_set_read_recovery_module, iter_reh_steps
import random
import math
import time
from Script.project_api.reh.functions import \
    READ_LAST_TABLE_TYPE, \
    create_read_last_ref_table, \
    get_page_range_by_type, \
    issue_409E_to_get_error_bit_numbers
from Script.project_api.custom_vu.do_power_loss_analysing_vu.functions import *

_sdk = shared.sdk
class VERIFY_METHOD(Enum):
    EQUAL       = 0
    GREATER     = 1
    NOT_EQUAL   = 2
class NAND_MODE(Enum):
    TLC_BLOCK       = 0
    SLC_BLOCK       = 1
class BlockCase(IntEnum):
    TLC_Open = 0
    TLC_Closed = 1
    SLC_Open = 2
    SLC_Closed = 3
class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        self.total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.au_to_node = (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size * 512 ) // api.DATA_SIZE_4K_BYTE
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting = api.get_flash_setting()
        self.write_record =  api.get_empty_write_record()
        logger.info(f'total vb count = {self.fw_geometry.l52_total_vb_count}')
        self.TLC_VB_4K_SIZE = (self.fw_geometry.l88_vb_size_u1 * 512) // api.DATA_SIZE_4K_BYTE
        self.SLC_VB_4K_SIZE = (self.fw_geometry.l84_vb_size_u0 * 512) // api.DATA_SIZE_4K_BYTE
        self.TLC_PB_AU_SIZE = self.fw_geometry.l16_vb_size_pb_d1 // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.SLC_PB_AU_SIZE = self.fw_geometry.l20_vb_size_pb_d2 // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.TLC_VB_AU_SIZE = self.fw_geometry.l88_vb_size_u1 // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.SLC_VB_AU_SIZE = self.fw_geometry.l84_vb_size_u0 // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        logger.info(f'total au = {self.total_au}')
        _, self.mConfig_in_vu = project_api.get_mConfig_data()
        hw_setting = api.HwSetting.get_instance()
        hw_setting.update_from_device()
        self.ce = self.flash_setting.Max_Fdevice
        self.plane = self.flash_setting.Plane_Per_Die
        self.suspend_scale = hw_setting.get_local_val(api.HwSettingField.SUSPEND_SCALE)
        self.suspend_timer = hw_setting.get_local_val(api.HwSettingField.SUSPEND_TIMER)
        self.ats_time = (self.suspend_scale * self.suspend_timer) / 1000
        self.tlc_ce_page = self.flash_setting.Plane_Per_Die * 4 * 3
        self.slc_ce_page = self.flash_setting.Plane_Per_Die * 4 
        self.tlc_max_page = 3311
        self.slc_max_page = 1103
        self.ce_page = self.flash_setting.Plane_Per_Die * 4
        self.MANDATORY_WL = self.mConfig_in_vu.MANDATORY_WL_15.value
        pass
    def check_vb_in_which_group(self,vb_number:int) -> str:
        _, payload = get_vb_info()
        vb_info = project_api.VBInfo()
        vb_number_info = {k: ((int.from_bytes(payload[vb_number * 4:vb_number*4 + 4], 'little') >>
                        v['pos']) & v['mask']) for k, v in vb_info.VB_LIST_DATA_FORMAT.items()}
        target_index = vb_number_info['group']
        target_group_list = [vb_grp_name for vb_grp_name, vb_grp_index in project_api.VBList().vb_group_list().items() if vb_grp_index == target_index]
        logger.info(f' vb number = {vb_number} is in {target_group_list[0]}')
        return target_group_list[0]
    def test_discardCount(self)->None:
        self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=self.TLC_VB_4K_SIZE // 2)
        self.unmap_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=1)
    def test_eraseCount(self)->None:
        self.write_data(lun=self.slc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=self.TLC_VB_4K_SIZE // 2)
        self.unmap_data(lun=self.slc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=1)

    def test_SliceRefreshDone(self) -> None:
        total_len = self.TLC_VB_4K_SIZE 
        self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        _, vu_pca = project_api.issue_4051_to_get_physical_address(luID=self.tlc_lun, lba=0)
        vb = vu_pca.virtual_block_number.value
       
        vb_list = [vb]
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.LowPriority)
        self.polling_bkops_idle()
    
    def test_RefreshCnt(self)->None:
        logger.info(1,'Set refresh unit = 1, refresh method = 1')
        api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=1)
        api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=1)

        dev_desc = self.pattern_get_device_health_descriptor()
        refreshProgress_step = int.from_bytes(dev_desc[41:45])
        resfreshCount_step = int.from_bytes(dev_desc[37:41])
        logger.info(f'refreshprogress = {refreshProgress_step}, refreshCount = {resfreshCount_step}')
        total_len = self.TLC_VB_4K_SIZE // 2
        
        logger.info(2,'write 1/2 tlc vb ')
        self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)

        logger.flow(3,'Enable refresh and polling refresh status = 3')
        api.set_flag(api.FlagIDN.REFRESH_EN)
        start_time_inner = time.time()
        while True:
            self.check_timeout(start_time=start_time_inner,timeout_min=15)
            val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
            if val == 3:
                break
            elif val == 1:
                continue
            else:
                logger.error_lb(f'check bRefreshStatus until 03h')
                logger.error_fp(f'Expect refresh status = 03h, but = {val}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
        dev_desc = self.pattern_get_device_health_descriptor()
        refreshProgress_step1 = int.from_bytes(dev_desc[41:45])
        resfreshCount_step1 = int.from_bytes(dev_desc[37:41])
        logger.info(f'refreshprogress = {refreshProgress_step1}, refreshCount = {resfreshCount_step1}')
        pass
    def get_target_vb_list(self, group:int)-> List[int]:
        retval = 0
        vb_list = []
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'access_mode': {'pos': 6, 'len': 2, 'mask': 0x3}, 
            'dirty': {'pos': 8, 'len': 1, 'mask': 0x1}, 
        }
        response, rep_data = get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break

            ftl_vb_list_data.update({vb : {k: (((rep_data[vb*4]|rep_data[vb*4+1]<<8) >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        used_mlc_cout = 0
        map_vb_cnt = {} # type: ignore
        logger.info(f'[show all vb info at begin]')
        for vb, vb_info in ftl_vb_list_data.items():
            last_type = vb_info['group']
            dirtybit = vb_info['dirty']
            if last_type in map_vb_cnt:
                map_vb_cnt[last_type] += 1
            else:
                map_vb_cnt[last_type] = 1
            logger.info(f'[vb = {vb}, group type = {last_type}, dirtybit = {dirtybit}]')
            if last_type == group:
                vb_list.append(vb)
        for k,v in map_vb_cnt.items():
            logger.info(f'group type = {k}, cnt = {v}]')
        logger.info(f'get target vb list of vb {group} cnt = {len(vb_list)}')
        return vb_list
    def test_bfea_finish_scan_vb(self) -> None:
        _, mConfig_in_vu = project_api.get_mConfig_data()
        self.FB_SCAN_WL_MIN = mConfig_in_vu.FB_SCAN_WL_MIN.value
        self.PB_SCAN_PAGE = mConfig_in_vu.PB_SCAN_PAGE.value
        self.FB_SCAN_WL_MAX = mConfig_in_vu.FB_SCAN_WL_MAX.value
        self.PB_SCAN_ENABLE_PAGE_GAP = mConfig_in_vu.PB_SCAN_ENABLE_PAGE_GAP.value
        logger.info(f'self.FB_SCAN_WL_MIN = {self.FB_SCAN_WL_MIN}, self.PB_SCAN_PAGE = {self.PB_SCAN_PAGE}, self.FB_SCAN_WL_MAX = {self.FB_SCAN_WL_MAX}, self.PB_SCAN_ENABLE_PAGE_GAP = {self.PB_SCAN_ENABLE_PAGE_GAP}')
        
        logger.flow(2,'erase all card + disable ATS') 
        start_lba = 0
        data_len = 65535
        _param = shared.param
        continue_push_unmap = True
        while continue_push_unmap:
            start_lba = min(start_lba, _param.gLUCapacity[self.tlc_lun])
            if (start_lba + data_len) > _param.gLUCapacity[self.tlc_lun]:
                data_len = _param.gLUCapacity[self.tlc_lun] - start_lba
                continue_push_unmap = False
            logger.info(f'unmap, start_lba = {start_lba}, data_len = {data_len}')
            unmap = ExecuteCMD.Unmap()
            unmap.assign(lun=self.tlc_lun, lba=start_lba, length=data_len)
            ExecuteCMD.enqueue(unmap)      
            start_lba += data_len
        ExecuteCMD.send(clear_on_success=True)
        idn = api.FlagIDN.PURGE_EN
        set_flag = ExecuteCMD.SetFlag().assign(idn).enqueue()
        ExecuteCMD.send(clear_on_success=True)
        timeout_min = 0
        timeout_sec = 2000
        start_time = time.time()
        polling_cnt = 0
        while True:
            if self.check_timeout(start_time, timeout_min, timeout_sec):
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            purge_status = api.read_attribute(idn=api.AttributeIDN.PURGE_STATUS)
            polling_cnt += 1
            logger.info(f'purge status = {purge_status}, polling count = {polling_cnt}')
            if purge_status == 0x03:
                logger.info(f'purge status = {purge_status}, complete')
                break
        pass
        logger.info(f'disable ats')
        project_api.issue_D088_enable_disable_auto_standby(0)
        logger.flow(3,'write 3 TLC VB')
        self.write_data(self.tlc_lun, start_lba=0, len = WRITE_10_MAX_BLOCK_LEN, total_len = self.TLC_VB_4K_SIZE * 3)
        free_vb_list = self.get_target_vb_list(17)
        pca = api.lba_to_pba(self.tlc_lun, 0)
        vb = pca.w10_block.value
        ce = pca.b5_ce.value
        self.test_vb = vb
        self.test_ce = ce  
        logger.flow(6,'Issue 40B0 bfea scan')
        min_bin = 0xFFFFFFFF
        for ce in range(self.flash_setting.Max_Fdevice):
            logger.info(f'40B0 option = 3, vb = {self.test_vb}, ce = {ce}')
            payload = project_api.issue_40B0_Bfea_Scan(3, self.test_vb, ce, 0)
            output = int.from_bytes(payload[0:4], byteorder='little')  
            logger.info(f'result = {output}')
            if min_bin > output:
                min_bin = output
        self.min_bin_val = min_bin  
        logger.flow(7,f'Get min bin from vb {self.test_vb} from all ce = {self.min_bin_val}')
        logger.flow(8,'Issue 40B0 VUC to BFEA Scan to set timer')
        self.setting_timer_minutes = 1
        if self.min_bin_val <= 1:
            grp = 0
        elif self.min_bin_val <= 8:
            grp = 1
        elif self.min_bin_val <= 15:
            grp = 2
        self.grp = grp            
        logger.info(f'grp = {self.grp}')
        self.time_gap_min = 20
        logger.info(f'40B0 opcode = 9, grp = {grp}, timer minute = {self.time_gap_min - self.setting_timer_minutes}')
        project_api.issue_40B0_Bfea_Scan(9, grp, (20  - self.setting_timer_minutes) * 60, 0) # will be 20 * 60 - 1*60 = 19 * 60 (sec)
        logger.flow(9,f'idle {self.setting_timer_minutes} min')
        time.sleep(self.setting_timer_minutes * 60)
        self.polling_bfea_idle()

    def push_spor(self, delay:int) -> None:
        power_cycle = ExecuteCMD.CmdSeqPowerCycle()
        power_cycle.set_option(mode=api.PowerCycleMode.ALL_POWER_DOWN, wait_queue_empty=True, delay_time=delay)
        ExecuteCMD.enqueue(power_cycle)
        for channel in range(1,3 +1):
            power_ctrl = ExecuteCMD.CmdSeqPowerControl()
            power_ctrl.set_option(
                mode=1,
                channel=channel,
                spendtime=500,
                ramptime=100,
                wait_queue_empty=True,
                delay_time=100
            )
            ExecuteCMD.enqueue(power_ctrl)

        power_cycle = ExecuteCMD.CmdSeqPowerCycle()
        power_cycle.set_option(mode=api.PowerCycleMode.LINK_START_UP, wait_queue_empty=True, delay_time=delay)
        ExecuteCMD.enqueue(power_cycle)
        nop = ExecuteCMD.CmdSeqPushNopOutPollNopIn()
        nop.set_option(timeout=5000, wait_queue_empty=True, delay_time=100)
        ExecuteCMD.enqueue(nop)  
    def test_spor_write_fail_count(self) -> None:
        total_len = 4096*1
        self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)

        open_vb = self.get_and_print_open_vb_information()
        vb = open_vb.PTE_Block_VB_number_logical.value
        logger.info(f'before vb = {vb}')
        fep = open_vb.PTE_block_First_free_physical_page.value
        
        self.flipbit_on_PTE_smart()
        testlun = 0
        cmd_count = random.randint(10, 32)
        min_lun = self.tlc_lun
        max_lun = self.tlc_lun
        min_lba = 0
        max_lba = self._param.gLUCapacity[self.tlc_lun]
        min_size = api.BLOCK4K_SIZE_64M_BYTE
        max_size = api.BLOCK4K_SIZE_128M_BYTE
        self.random_write_spor(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                    need_compare=True, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        logger.flow(6, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
            
        # cmd_count = random.randint(10, 32)
        # min_lun = self.tlc_lun
        # max_lun = self.tlc_lun
        # min_lba = 0
        # max_lba = 4096*1
        # min_size = api.BLOCK4K_SIZE_64M_BYTE
        # max_size = api.BLOCK4K_SIZE_128M_BYTE
        # api.random_write_spor(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
        #             need_compare=True, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        # logger.flow(6, f'HW reset without SSU')
        # api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        # 
        return
    def test_apl_book_vb_count(self, field_name:str) -> None:
        #_ = self.write_1_VB_with_SPOR(lun=self.tlc_lun)

        before = self.get_40C3_value(field_name)
        lba = 0
        chunk_size = api.BLOCK4K_SIZE_128M_BYTE
        vb_size = self.TLC_VB_4K_SIZE
        datalen = self.TLC_VB_4K_SIZE//2
        # api.sequential_write(lun=self.tlc_lun, start_lba=lba, total_size=datalen, chunk_size=chunk_size, fua = 1,
        #                     need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        lba += datalen
        apl_created = False
        delay = 100000
        #project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)

        before = self.get_40C3_value(field_name)
        logger.info("============= create APL ================")
        while not apl_created:
            temp_write_record = api.get_empty_write_record()
            write10 = ExecuteCMD.Write10()
            chunk_size = api.BLOCK4K_SIZE_64K_BYTE
            write10.assign(lun=self.tlc_lun, lba=lba, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX)
            ExecuteCMD.enqueue(write10)
            self.push_spor(delay=delay)
            ExecuteCMD.send(clear_on_success=False)
            for cmd in ExecuteCMD._cmd_list:
                api.save_write_info_by_cmd(cmd, temp_write_record)
            ExecuteCMD.clear()
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
            
            #project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
            try:
                api.read_compare(temp_write_record, api.CompareMethod.SW_COMPARE)
                delay -= 50000
                if delay<0:
                    raise SIGHTING_RESPONSE_UNEXPECTED
            except DLL_CRC32_COMPARE_FAIL:
                ExecuteCMD.clear()
                apl_created = True
                
                
            lba+=chunk_size
        

        #api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        chunk_size = api.BLOCK4K_SIZE_128M_BYTE
        api.sequential_write(lun=self.tlc_lun, start_lba=lba, total_size=vb_size, chunk_size=chunk_size, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        pca = self.get_PCA_and_print(lun=self.tlc_lun, lba=lba)
        logger.flow(2, 'Inject UECC in each VB type')
        self.inject_UECC(pca=pca, SLC_enable=False)

        logger.flow(3, 'SPOR')
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
        after = self.get_40C3_value(field_name)
        self.compare_value(after-before,expect_value=1,desc=field_name)
        return

    def check_timeout(self,start_time: float, timeout_min: int, timeout_sec:int=0) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_min * 60 + timeout_sec:
            return True
        else:
            return False
        
    def polling_bfea_idle(self)-> None:
        timeout_min = 0
        timeout_sec = 2000
        start_time = time.time()   
        logger.info(f'polling_bfea_idle')  
        while True:
            if self.check_timeout(start_time, timeout_min, timeout_sec):
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            payload = project_api.issue_40B0_Bfea_Scan(5,0,0,0)
            output = int.from_bytes(payload[0:4], byteorder='little')      
            if output != 1:
                logger.info(f'output = {output}, continue polling')
                time.sleep(1)
            else:
                logger.info(f'output = {output}, already idle')
                break  
    def test_read_disturb_trigger_num(self) -> None:
        #project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        api.sequential_write(lun=self.slc_lun, start_lba=0, total_size=self.SLC_VB_4K_SIZE, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        def read_LBA_repeatedly(lun:int, lba:int, read_times:int) -> None:
            for _ in range(read_times):
                read10 = ExecuteCMD.Read10()
                read10.assign(lun=lun, lba=lba, length=1, fua=1)
                ExecuteCMD.enqueue(read10)
            ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
            return
        pageline = self.ce * self.plane * 4
        wl = self.MANDATORY_WL & 0x1FF
        lba =  wl * pageline + 1
        _,pca = project_api.issue_4051_to_get_physical_address(self.slc_lun, lba=lba)
        read_cnt_of_vb_before = project_api.get_all_VB_read_count()
        vb = pca.virtual_block_number.value
        set_RC_TH_Value = read_cnt_of_vb_before[vb] + 1
        project_api.set_specific_VB_read_count_threshold(VB_Num=vb, RC_TH_Value=set_RC_TH_Value)
        times = random.randint(10,100)
        
        read_LBA_repeatedly(lun=self.slc_lun, lba = lba, read_times=times)

        def trigger_read_scan_UECC(lun:int, lba:int, SLC_enable:bool) -> None:
            pca = self.get_PCA_and_print(lun=lun, lba=lba)
            #pca.page.value = self.MANDATORY_WL
            self.inject_UECC(pca=pca, SLC_enable=SLC_enable)
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=lun, lba=lba, length=1, fua=1)
            ExecuteCMD.enqueue(read10)
            ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
            ExecuteCMD.clear()
            pass
        
        trigger_read_scan_UECC(self.slc_lun, lba=lba, SLC_enable=True)

        _, self.booking_q = project_api.issue_40C5_to_get_booking_queue()
        logger.info(self.booking_q.LogicalVBNumberInBookingQueue.value)

        for idx, bq in enumerate(self.booking_q.BookingQueueVB):
            logger.info(f'booking user = {bq.TheBookingUser}')
        #project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        self.polling_bkops_idle()
        pass

    def set_ec(self, set_ec:bytearray) -> None:
        total_VB_count = self.fw_geometry.l52_total_vb_count
        data = bytearray(b'\xFF' * 0x4000)
        del set_ec[total_VB_count*4:]
        data[:len(set_ec)] = set_ec

        api.ufs_api.vendor_cmd.access_vendor_mode()
        vuc = ExecuteCMD.VendorCmdWrite()
        vuc.assign(length=api.DATA_SIZE_16K_BYTE, cmd_index=api.VendorCmd.GET_FW_GEOMETRY, cmd_set_type=0x0F)
        vuc.upiu.u16_cdb.b2_rsvd = api.VendorCmdRuleCdb2.CMD_IN_CDB
        vuc.upiu.u16_cdb.b6_cmd2 = 4
        vuc.data = data
        vuc.enqueue()
        ExecuteCMD.send()    
    def set_nand_temp(self, set_temp:int) -> None:
        temp_set = 65536 + set_temp if set_temp < 0 else set_temp
        set_nand_temp = project_api.SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 1
        set_nand_temp.NAND_TEMPERATURE_DIE_0.value = temp_set
        if self.flash_setting.Max_Fdevice >= 2:
            set_nand_temp.NAND_TEMPERATURE_DIE_1.value = temp_set
        if self.flash_setting.Max_Fdevice >= 4:
            set_nand_temp.NAND_TEMPERATURE_DIE_2.value = temp_set
            set_nand_temp.NAND_TEMPERATURE_DIE_3.value = temp_set
        set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0  
        set_nand_temp.UC_TERMAL_SENSOR_1.value = temp_set
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
    def get_xtemp_parameter(self) -> tuple[int,int,int,int,int]:
        rsp, mconfig = project_api.get_mConfig_data()
        XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
        XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
        XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
        XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
        XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
        logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
        logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')

        if mconfig.XTEMP_ENABLE_PEC.value < 2 or mconfig.XTEMP_ENABLE_PEC.value > 10:
            mconfig.XTEMP_ENABLE_PEC.value = 10
            mconfig.payload[0:7] = "MCONFIG".encode("ascii")
            project_api.set_mConfig_data(mConfig=mconfig)

            rsp, mconfig = project_api.get_mConfig_data()
            XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
            XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
            XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
            XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
            XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
            logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
            logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')
        return XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2
    def test_counterDeltaT1(self) -> None:
        XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2 = self.get_xtemp_parameter()
        idle_wait_detect_temp = XTEMP_TIME_DETECTION_VALUE

        logger.flow(3, f'Set all VB EC as (XTEMP_ENABLE_PEC * 100) = {XTEMP_ENABLE_PEC * 100} (enable XTEMP condition)')
        set_ec_value = XTEMP_ENABLE_PEC * 100
        value_bytes = set_ec_value.to_bytes(4, byteorder='little', signed=False)
        data = bytearray(b'\xFF' * 0x4000)
        data[:(self.fw_geometry.l52_total_vb_count * 4)] = value_bytes * self.fw_geometry.l52_total_vb_count
        self.set_ec(data)

        logger.flow(4, 'HW reset to enable XTEMP algorithm')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

        logger.flow(5, f'Issue VU 0xD08A to set NAND temperature to XTEMP_Refresh_T1 - 1 = {XTEMP_REFRESH_T2 + 1}, changing Tstatus to "Hot Risky"')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T1 - 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow(5, f'Issue VU 0xD08A to set NAND temperature to safe zone')
        self.set_nand_temp(set_temp=(XTEMP_REFRESH_T1 + XTEMP_TEMP_BUFFER + 1))
        time.sleep(idle_wait_detect_temp)

    def test_counterDeltaT2(self) -> None:
        XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2 = self.get_xtemp_parameter()
        idle_wait_detect_temp = XTEMP_TIME_DETECTION_VALUE

        logger.flow(3, f'Set all VB EC as (XTEMP_ENABLE_PEC * 100) = {XTEMP_ENABLE_PEC * 100} (enable XTEMP condition)')
        set_ec_value = XTEMP_ENABLE_PEC * 100
        value_bytes = set_ec_value.to_bytes(4, byteorder='little', signed=False)
        data = bytearray(b'\xFF' * 0x4000)
        data[:(self.fw_geometry.l52_total_vb_count * 4)] = value_bytes * self.fw_geometry.l52_total_vb_count
        self.set_ec(data)

        logger.flow(4, 'HW reset to enable XTEMP algorithm')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

        logger.flow(5, f'Issue VU 0xD08A to set NAND temperature to XTEMP_Refresh_T2 + 2 = {XTEMP_REFRESH_T2 + 1}, changing Tstatus to "Hot Risky"')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2 + 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow(5, f'Issue VU 0xD08A to set NAND temperature to safe zone')
        self.set_nand_temp(set_temp=(XTEMP_REFRESH_T1 + XTEMP_REFRESH_T2) //2)
        time.sleep(idle_wait_detect_temp)
    
    def test_reh_book_vb_count(self) -> None:
            
        #project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        gparam = api.shared.param
        write_record = api.get_empty_write_record()

        logger.info('Sequential write 1 TLC VB size')
        lun = 0
        length = self.TLC_VB_4K_SIZE
        api.sequential_write(lun=self.tlc_lun, start_lba=0, total_size=length, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
        lba = 0
        logger.info(f'Issue 4051 VUC to get PBA from selected LBA = {lba} ')
        _,pca = project_api.issue_4051_to_get_physical_address(lun, lba=lba)

        logger.info(f'Issue D014 to gen read fail')
        _ = issue_D014_to_set_read_recovery_module(
            die = pca.die.value, 
            bigIndex=6, 
            smallIndex=1, 
            nandMode=NAND_MODE.TLC_BLOCK.value, 
            isSpeciBlock=1, 
            block=pca.virtual_block_number.value, 
            isPSA=0)
        
        logger.info(f'Issue host read 4K size')
        ExecuteCMD.Read10().assign(lun=lun, lba=lba, length=1, fua=0).enqueue()
        ExecuteCMD.send()
        ExecuteCMD.clear()

    def test_gc_info(self, field_name:str, method:VERIFY_METHOD=VERIFY_METHOD.EQUAL, expected_val:int=0) -> None:
        
        before = self.get_40C3_value(field_name)
        logger.flow(1, 'Issue 40C1 get open vb')
        
        
        if field_name == "GCOpenVBCount":
            total_len = self.TLC_VB_4K_SIZE // 2
            lun=self.tlc_lun
            #vb = self.open_vb_information_Normal.L2_Open_logical_VB_Host_TLC_number.value
        elif field_name == "EM1GCOpenVBCount":
            #vb = self.open_vb_information_Normal.open_logical_VB_number_for_EM1_L2_Host.value
            total_len = self.SLC_VB_4K_SIZE // 2
            lun=self.slc_lun
        
        elif field_name == "GCTLCDataSize_NORMAL" or field_name == "GCTLCDummySize_NORMAL":
            api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            total_len = self.TLC_VB_4K_SIZE
            lun=self.tlc_lun
            
        elif field_name == "GCSLCDataSize_EM1" or field_name == "GCSLCDummySize_EM1":
            total_len = self.SLC_VB_4K_SIZE
            lun=self.slc_lun

        elif field_name == "GCSLCDataSize_NORMAL" or field_name == "GCSLCDummySize_NORMAL":
            api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            lun=self.tlc_lun
            total_len = self.SLC_VB_4K_SIZE
            
        self.write_data(lun=lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        _, pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=0)
        vb_list = [pca.virtual_block_number.value]
        time.sleep(1)

        logger.flow(2, 'Issue D0FD to disable bkops')
        #project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x00) #disable bg
        #project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x02) #disable fg
        
        logger.flow(2, 'Issue C087 to push vb to force refresh')
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.LowPriority)
        
        after = self.get_40C3_value(field_name)
        self.compare_value(after - before, expected_val, desc=field_name,method=method)

        logger.flow(2, 'Issue D0FD to enable bkops and polling bkops = 0')
        #project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x01) #enable bg
        #project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x03) #enable fg

        self.polling_bkops_idle()

    
    def RPMB_write_data(self, total_len:int) -> None:
        vendor_cmd.access_vendor_mode()
        vendor_cmd.vuc_clear_rpmb_key(api.RPMBRegion.REGION_0)
        rpmb = RPMB(api.RPMBRegion.REGION_0)
        try:
            write_counter = rpmb.rpmb_read_counter()
        except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
            logger.info("Flow = RPMB key is cleared")
            rpmb.rpmb_key_programming()
        start_lba = 0
        while total_len:
            data_len = min(total_len, 256)
            rpmb.rpmb_write_data(start_lba=start_lba, data_len=data_len)
            start_lba += data_len
            total_len -= data_len
    def check_ics(self,input_pca: PCA)-> bool:
        read_pca = PCA()
        read_pca = input_pca
        ics_bad_block = project_api.get_ics_bad_block()
        vb = read_pca.b10_block_l + (read_pca.b11_block_h << 8)
        if ics_bad_block.ICSBadBlocks[vb].VB_index.value == vb:
            index_ics_plane = ics_bad_block.ICSBadBlocks[vb].invalid_VB_plane.value
            logger.info(f'index_ics_plane : {index_ics_plane}')
        if index_ics_plane != input_pca.b5_ce * self.flash_setting.Plane_Per_Die + input_pca.b6_plane:
            return False
        else:
            return True
    def inject_UECC_PCA(self,pca:PCA) -> None:
        logger.info(f'Inject UECC: Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}(pageline = {pca.l12_fpage>>5}), lmu = {pca.b20_lmu}')
        block = (pca.b11_block_h<<8) | (pca.b10_block_l)
        ce = pca.b5_ce
        plane = pca.b6_plane
        if pca.b4_mode == 0: #for system and hidden
            pca.b4_mode = 1
        mode = pca.b4_mode
        if pca.b4_mode==1:
            page = pca.l12_fpage>>5
            dire_read_payload = bytearray(DATA_SIZE_16K_BYTE)
        else:
            page = (pca.l12_fpage>>5) * 3
            dire_read_payload = bytearray(DATA_SIZE_16K_BYTE*3)
        for i in range(len(dire_read_payload)):
            dire_read_payload[i] = 0xAA
        _ = project_api.issue_C060_to_write_raw_data(Ce=ce, Plane=plane, Block=block, Page=page, SLC_Enable=int(mode==1),Ecc_Enable=1, datapayload=dire_read_payload)
        return
    def injectUECC_from_FEP(self,vb: int, fep: int, startoffset: int, num:int)-> PCA:
        ce_num = self.flash_setting.Max_Fdevice
        plane_num = self.flash_setting.Plane_Per_Die
        ce_plane_num = ce_num * plane_num
        uecc_pca = PCA()
        cnt = 1
        while num != 0:
            uecc_pca.b10_block_l = vb & 0xFF
            uecc_pca.b11_block_h = (vb >> 8) & 0xFF
            uecc_pca.b5_ce = ((fep - cnt)  % ce_plane_num) // plane_num
            uecc_pca.b6_plane = ((fep - cnt)  % ce_plane_num) % plane_num
            uecc_pca.l12_fpage = ((fep - cnt) // ce_plane_num) << 5
            if not self.check_ics(uecc_pca) :
                if startoffset <= 0:
                    self.inject_UECC_PCA(uecc_pca)
                    num = num-1
                else:
                    startoffset = startoffset -1
            cnt = cnt +1
        return uecc_pca
    def count_diff_bytes(self, a: bytearray, b: bytearray) -> int:
       
        #先比較共同長度的部分
        diff = sum(x != y for x, y in zip(a, b))

        #再把長度差額加進去（多出的部份必定不同）
        diff += abs(len(a) - len(b))
        return diff
    def random_write_spor(self,cmd_count: int, min_lun: int, max_lun: int, min_lba: int, max_lba: int, min_size: int, max_size: int, need_compare: bool, 
                  compare_method: int, write_record: List[List[api.WriteRecordNode]]) -> None:
        #_log.info("function - random_write()")

        _param = shared.param

        if max_lba < min_lba:
            raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_LBA_SIZE_CHECK_ERROR
        elif (max_lun > _param.gMaxNumberLU-1) or (max_lun < min_lun):
            raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_LUN_CHECK_ERROR
        elif (cmd_count < 1) or (cmd_count > 256):
            raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_CMD_CNT_CHECK_ERROR
        else:

            _max_lba = 0    # 只有外面傳進來的 max_lba 有機會會被改掉，所以另外定一個參數，下一個loop才不會有問題

            for _ in range(1, cmd_count + 1):

                random_lun_count = 0

                if min_lun == max_lun:
                    lun = min_lun
                else:
                    while True:
                        lun = random.randint(min_lun, max_lun)

                        random_lun_count += 1
                        if random_lun_count > 100:                        
                            raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT                         

                        if _param.gUnit[lun].b3_lu_enable:
                            break

                if max_lba >= _param.gLUCapacity[lun]:
                    _max_lba = _param.gLUCapacity[lun]

                if min_size != max_size:
                    data_len = random.randint(min_size, max_size)
                else:
                    data_len = min_size

                if data_len >= _param.gLUCapacity[lun]:
                    data_len = _param.gLUCapacity[lun]

                if (_max_lba - data_len) < min_lba:
                    start_lba = min_lba
                else:
                    start_lba = random.randint(min_lba, _max_lba - data_len)

                if (start_lba + data_len) > _param.gLUCapacity[lun]:
                    start_lba = _param.gLUCapacity[lun] - data_len

                write10 = ExecuteCMD.Write10()
                write10.assign(lun=lun, lba=start_lba, length=data_len, fua=0)

                ExecuteCMD.enqueue(write10)

            dcmd7_arg = api.set_dcmd7_arg()
            dcmd7_arg.activate = api.Dcmd7Activate.EN
            #dcmd7_arg.detect_type = api.Dcmd7DetectType.BUSY_TIME_DETECT
            dcmd7_arg.detect_type = api.Dcmd7DetectType.RESPONSE_DETECT
            dcmd7_arg.reset_type = api.Dcmd7ResetType.HW_RESET        
            dcmd7_arg.detect_time = 10
            dcmd7_arg.response_detect_count = cmd_count
            dcmd7_arg.response_detect_delay_time = 10

            # dcmd7_arg.gap_time = 500
            # dcmd7_arg.response_detect_count = 600
            # dcmd7_arg.response_detect_delay_time = 700

            api.set_debug_cmd7(dcmd7_arg, 0)

            try:
                ExecuteCMD.send()
            except api.DLL_POWER_CYCLE as e:
                _sdk.clear_done_queue(api.HostDoneQueueType.ALL_DONE_QUEUE_ERR_HANDLE, 0)
            ExecuteCMD.clear()
            dcmd7_arg.activate = api.Dcmd7Activate.DIS
            api.set_debug_cmd7(dcmd7_arg, 0)

            dcmd7_rsp = api.get_debug_cmd7()

            if dcmd7_rsp.status == api.Dcmd7Status.PASS:
                if dcmd7_rsp.interrupt_status == api.Dcmd7InterruptStatus.SUCCESS:
                    logger.info("SPOR Interrupt Success, SOPR Occur!")
                else:
                    logger.info("SPOR Interrupt Fail!")

            if (need_compare):
                pass
    def issue_40D1_to_get_system_init_time_stamp(self) -> bytearray:
        #_log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
        vu = micron_vendor_cmd()
        vu.b0_opcode.value = 0xD1
        vu.b1_func.value = 0x40
        vu.w2_transfer_length.value = 4096
        vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  
        response, payload = send_data_in_vcmd(micron_vendor_cmd=vu)
        return payload
    def flip_bits_one_per_byte(
        self, 
        raw: bytearray,
        *,
        total_bits: int = 500,
        block_index: int = 0,
        seed: int | None = None,
    ) -> List[int]:
        """
        在 *raw* 中的第 ``block_index`` 個 4 KB 區塊內，隨機翻轉 ``total_bits`` 個位元。
        - 每個 byte 只會翻 1 個 bit（使用 ``random.sample`` 產生不重複的 byte 索引）。
        - ``block_index = 0`` → 位元組 0  ~ 4095（原本行為）。
        - ``block_index = 1`` → 位元組 4096 ~ 8191（第 2 個 4 KB）。
        - 以此類推...

        參數
        ----------
        raw : bytearray
            會被原位元 (in‑place) 修改的緩衝區。
        total_bits : int, default 500
            要翻轉的位元數目。必須 ≤ 本區塊可用的 byte 數（每個 byte 最多 1 個 bit）。
        block_index : int, default 0
            想要操作的 4 KB 區塊編號，從 0 開始計算。
        seed : int | None
            若提供，會以此 seed 建立 ``random.Random``，讓測試可重現。

        回傳
        -------
        List[int]
            所有被翻轉的全域 bit 索引（0‑based），方便列印或除錯。
        """
        if total_bits < 0:
            raise ValueError("total_bits 必須為非負整數")
        if block_index < 0:
            raise ValueError("block_index 必須為非負整數")

        # 1️⃣ 计算本区块的起始 / 结束 byte
        block_start = block_index * 4096                     # 第 N 個 4 KB 的起點
        if block_start >= len(raw):
            raise ValueError(
                f"指定的 block_index ({block_index}) 超出 raw 的長度 "
                f"(len={len(raw)} bytes)。"
            )
        # 本区块实际可用的 byte 数（若 raw 在此处就截断了）
        max_bytes = min(4096, len(raw) - block_start)

        if total_bits > max_bytes:
            raise ValueError(
                f"欲翻轉的位元數 ({total_bits}) 大於本 4 KB 區塊可用的 byte 數 "
                f"({max_bytes})。每個 byte 只能翻 1 個 bit。"
            )

        # 2️⃣ 隨機抽樣不重複的 byte 索引（相對於整個 raw 的絕對位置）
        rng = random.Random(seed)
        byte_indices = rng.sample(
            range(block_start, block_start + max_bytes), total_bits
        )

        # 3️⃣ 為每個選中的 byte 隨機挑一個 bit (0~7) 並翻轉
        flipped_bit_positions: List[int] = []
        for b_idx in byte_indices:
            bit_off = rng.randint(0, 7)                 # 0~7 之間的整數
            global_bit_idx = b_idx * 8 + bit_off        # 全域 bit 索引
            flipped_bit_positions.append(global_bit_idx)

            # XOR 使該位元翻轉
            raw[b_idx] ^= 1 << bit_off

        # 4️⃣ 返回排序好的 bit 索引（方便列印）
        flipped_bit_positions.sort()
        return flipped_bit_positions
    def print_bit_positions(self, indices: List[int], *, title: str = "") -> None:
        if title:
            logger.info("\n=== " + title + " ===")
        logger.info(f"{'bit_idx':>8}  {'byte_idx':>8}  {'bit_in_byte':>11}")
        logger.info("-" * 30)
        for idx in sorted(indices):
            byte_idx = idx // 8
            bit_in_byte = idx % 8          # LSB 為 0
            logger.info(f"{idx:8d}  {byte_idx:8d}  {bit_in_byte:11d}")
    def flipbit_on_PTE(self)->None:
        #self.config_lun()

        ce_num = self.flash_setting.Max_Fdevice
        plane_num = self.flash_setting.Plane_Per_Die
        ce_plane_num = ce_num * plane_num
        slc_ce_page = self.flash_setting.Plane_Per_Die * 4
        #api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=int(slc_ce_page), chunk_size=slc_ce_page, fua = 1,
        #                 need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        logger.flow(1, f'GET Open vb information by VU 0x40C1')
        get_open_vb = self.get_and_print_open_vb_information()
        testlba = 0
        isSLC = 1
        logger.flow(2, f'GET LUN {self.tlc_lun}，LBA {testlba} physical address by VU 0x4051')
        _,micron_pca = project_api.issue_4051_to_get_physical_address(self.tlc_lun, testlba)
        micron_pca.die.value = 0
        micron_pca.plane.value = 0
        micron_pca.virtual_block_number.value = get_open_vb.PTE_Block_VB_number_logical.value
        micron_pca.page.value = 0

        cnt = 1
        while True:
            micron_pca.die.value = ((get_open_vb.PTE_block_First_free_physical_page.value - cnt)  % ce_plane_num) // plane_num
            micron_pca.plane.value = ((get_open_vb.PTE_block_First_free_physical_page.value - cnt)  % ce_plane_num) % plane_num  
            micron_pca.page.value = ((get_open_vb.PTE_block_First_free_physical_page.value - cnt) // ce_plane_num) #<< 5 assert 0x5E8D
            ics_bad_block = project_api.get_ics_bad_block()
            vb = micron_pca.virtual_block_number.value
            if ics_bad_block.ICSBadBlocks[vb].VB_index.value == vb:
                index_ics_plane = ics_bad_block.ICSBadBlocks[vb].invalid_VB_plane.value
                logger.info(f'index_ics_plane : {index_ics_plane}')
            if index_ics_plane != micron_pca.die.value * plane_num + micron_pca.plane.value:
                break
            cnt+=1


        logger.flow(3, f'VU 4060 read raw data on LBA {testlba} with ECC on')
        _, raw_data = project_api.issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=0)
        dumpfile("read_raw_data.bin", raw_data)
        flip_data = copy.deepcopy(raw_data)
        flipBitCount = 100
        flipbit = flipBitCount
        flipped = self.flip_bits_one_per_byte(flip_data, total_bits=flipbit, block_index=0) 
        diffcount = self.count_diff_bytes(raw_data, flip_data)
        logger.info(f'LP different count ={diffcount} after flip bits {flipbit}')

        self.print_bit_positions(flipped, title=f"{flipbit} bits position")
        logger.info(f"Flip first {flipbit} bits – done")
        logger.info(f"raw_data_flip = {len(flip_data)}") 
        write_payload = flip_data 
        #erase
        logger.flow(3, 'issue D060 to erase original data')
        project_api.issue_D060_to_erase_specific_block(Ce=micron_pca.die.value,Plane=micron_pca.plane.value,Block=micron_pca.virtual_block_number.value,SlcEnable=isSLC, psaEnable = 0)

        #write raw data
        dumpfile(f"write_raw_data.bin", write_payload)
        _ = project_api.issue_C060_to_write_raw_data(Ce=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC,Ecc_Enable=0, datapayload=write_payload)

        #read raw data
        _, raw_data_1 = project_api.issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.die.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=1, Scrambler_Enable=1, PSA_Enable=0)
        raw_data_11 = copy.deepcopy(raw_data_1)
        # diffcount = self.count_diff_bytes(raw_dataLP, raw_data_11)
        diffcount = self.count_diff_bytes(raw_data, raw_data_1)
        logger.info(f'LP different count ={diffcount}')
        dumpfile(f"FW_FLOW_READ.bin", raw_data_1)

        logger.flow(13, f'Issue 409E VUC with ECC information = 1 to get error bit numbers')
        _, output_409E = issue_409E_to_get_error_bit_numbers()
        error_bits_409E = [output_409E.errorBitNumber1.value, output_409E.errorBitNumber2.value, output_409E.errorBitNumber3.value, output_409E.errorBitNumber4.value]
        logger.info(f'409E error bits ={error_bits_409E}')

        _, raw_data_after_flip = project_api.issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.die.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=0)
        dumpfile(f"pageLP_after.bin", raw_data_after_flip)
        diffcount = self.count_diff_bytes(raw_data, raw_data_after_flip)
        logger.info(f'LP different count ={diffcount}')
        pass
    def flipbit_on_PTE_smart(self)->None:

        ce_num = self.flash_setting.Max_Fdevice
        plane_num = self.flash_setting.Plane_Per_Die
        ce_plane_num = ce_num * plane_num
        slc_ce_page = self.flash_setting.Plane_Per_Die * 4
        #api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=int(slc_ce_page), chunk_size=slc_ce_page, fua = 1,
        #                 need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        logger.flow(1, f'GET Open vb information by VU 0x40C1')
        get_open_vb = self.get_and_print_open_vb_information()
        testlba = 0
        isSLC = 1
        logger.flow(2, f'GET LUN {self.tlc_lun}，LBA {testlba} physical address by VU 0x4051')
        _,micron_pca = project_api.issue_4051_to_get_physical_address(self.tlc_lun, testlba)
        micron_pca.die.value = 0
        micron_pca.plane.value = 0
        micron_pca.virtual_block_number.value = get_open_vb.PTE_Block_VB_number_logical.value
        micron_pca.page.value = 0

        cnt = 1
        while True:
            micron_pca.die.value = ((get_open_vb.PTE_block_First_free_physical_page.value - cnt)  % ce_plane_num) // plane_num
            micron_pca.plane.value = ((get_open_vb.PTE_block_First_free_physical_page.value - cnt)  % ce_plane_num) % plane_num  
            micron_pca.page.value = ((get_open_vb.PTE_block_First_free_physical_page.value - cnt) // ce_plane_num) #<< 5 assert 0x5E8D
            ics_bad_block = project_api.get_ics_bad_block()
            vb = micron_pca.virtual_block_number.value
            if ics_bad_block.ICSBadBlocks[vb].VB_index.value == vb:
                index_ics_plane = ics_bad_block.ICSBadBlocks[vb].invalid_VB_plane.value
                logger.info(f'index_ics_plane : {index_ics_plane}')
            if index_ics_plane != micron_pca.die.value * plane_num + micron_pca.plane.value:
                break
            cnt+=1
        pagelist:List[bytearray] = []
        for idx_page in range(0,micron_pca.page.value+1):
            if idx_page == micron_pca.page.value:
                logger.flow(3, f'VU 4060 read raw data on page {idx_page} with ECC off')
                _, raw_data = project_api.issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=0)
                dumpfile("read_raw_data.bin", raw_data)
                flip_data = copy.deepcopy(raw_data)
                flipBitCount = 100
                flipbit = flipBitCount
                flipped = self.flip_bits_one_per_byte(flip_data, total_bits=flipbit, block_index=0) 
                diffcount = self.count_diff_bytes(raw_data, flip_data)
                logger.info(f'LP different count ={diffcount} after flip bits {flipbit}')

                self.print_bit_positions(flipped, title=f"{flipbit} bits position")
                logger.info(f"Flip first {flipbit} bits – done")
                logger.info(f"raw_data_flip = {len(flip_data)}") 
                write_payload = flip_data 
                pagelist.append(flip_data)
            else:
                logger.flow(3, f'VU 4060 read raw data on page {idx_page} with ECC off')
                _, raw_data_nonflip = project_api.issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=idx_page, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=0)
                dumpfile("read_raw_data_nonflop.bin", raw_data_nonflip)
                pagelist.append(raw_data_nonflip)

        #erase
        logger.flow(3, 'issue D060 to erase original data')
        project_api.issue_D060_to_erase_specific_block(Ce=micron_pca.die.value,Plane=micron_pca.plane.value,Block=micron_pca.virtual_block_number.value,SlcEnable=isSLC, psaEnable = 0)

        #write raw data
        for idx_page in range(0,micron_pca.page.value+1):
            write_payload = pagelist[idx_page]
            #dumpfile(f"write_raw_data.bin", write_payload)
            _ = project_api.issue_C060_to_write_raw_data(Ce=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=idx_page, SLC_Enable=isSLC,Ecc_Enable=0, datapayload=write_payload)

        #read raw data
        _, raw_data_1 = project_api.issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=1, Scrambler_Enable=1, PSA_Enable=0)
        raw_data_11 = copy.deepcopy(raw_data_1)
        # diffcount = self.count_diff_bytes(raw_dataLP, raw_data_11)
        diffcount = self.count_diff_bytes(raw_data, raw_data_1)
        logger.info(f'LP different count ={diffcount}')
        dumpfile(f"FW_FLOW_READ.bin", raw_data_1)

        logger.flow(13, f'Issue 409E VUC with ECC information = 1 to get error bit numbers')
        _, output_409E = issue_409E_to_get_error_bit_numbers()
        error_bits_409E = [output_409E.errorBitNumber1.value, output_409E.errorBitNumber2.value, output_409E.errorBitNumber3.value, output_409E.errorBitNumber4.value]
        logger.info(f'409E error bits ={error_bits_409E}')

        _, raw_data_after_flip = project_api.issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=0)
        dumpfile(f"pageLP_after.bin", raw_data_after_flip)
        diffcount = self.count_diff_bytes(raw_data, raw_data_after_flip)
        logger.info(f'LP different count ={diffcount}')
        pass
    def test_oneShotTableDefragCount(self, field_name:str) -> None:
        #project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        for i in range(3):
            pte_update_spor_occurred = False
            before = self.get_40C3_value(field_name)
            total_len = 4096*1
            self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)

            open_vb = self.get_and_print_open_vb_information()
            vb = open_vb.PTE_Block_VB_number_logical.value
            logger.info(f'before vb = {vb}')
            fep = open_vb.PTE_block_First_free_physical_page.value
            
            self.flipbit_on_PTE_smart()
            testlun = 0
            cmd_count = random.randint(10, 32)
            min_lun = self.tlc_lun
            max_lun = self.tlc_lun
            min_lba = 0
            max_lba = self._param.gLUCapacity[self.tlc_lun]
            min_size = api.BLOCK4K_SIZE_64M_BYTE
            max_size = api.BLOCK4K_SIZE_128M_BYTE
            self.random_write_spor(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=True, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            
            #rsp, lwpcheck_raw = issue_409D_to_do_power_loss_analysing(opcode,pca.b5_ce,pca.b6_plane,vb,1,startpage,stoppage)
            logger.flow(6, f'HW reset without SSU')
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
            open_vb = self.get_and_print_open_vb_information()
            after_vb = open_vb.PTE_Block_VB_number_logical.value
            logger.info(f'after vb = {after_vb}')
            if vb != after_vb:
                logger.info(f'vb = {after_vb}')
            payloadbuf = self.issue_40D1_to_get_system_init_time_stamp()
            por_flag = int.from_bytes(payloadbuf[88:92], byteorder='little')
            print(por_flag)
            if (por_flag & BIT6) >0:
                print(por_flag)
                pte_update_spor_occurred = True
            
            if pte_update_spor_occurred == True:
                after = self.get_40C3_value(field_name)
                self.compare_value(after-before,expect_value=1,desc=field_name)
            else:
                after = self.get_40C3_value(field_name)
                self.compare_value(after-before,expect_value=0,desc=field_name)
        
    def test_spor_recovery_count(self) -> None:
        api.sequential_write(lun=self.slc_lun, start_lba=0, total_size=api.BLOCK4K_SIZE_100M_BYTE, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        open_vb = self.get_and_print_open_vb_information()
        
        vb = open_vb.open_logical_VB_number_for_EM1_L2_Host.value
        fep = open_vb.first_free_physical_page_of_EM1_L2_Host_VB.value
        self.injectUECC_from_FEP(vb,fep,startoffset=0,num=1)
        logger.flow(6, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        
        return
    def test_xTempColdToHotStatCounter(self) -> None:
        XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2 = self.get_xtemp_parameter()
        idle_wait_detect_temp = XTEMP_TIME_DETECTION_VALUE

        logger.flow(3, f'Set all VB EC as (XTEMP_ENABLE_PEC * 100) = {XTEMP_ENABLE_PEC * 100} (enable XTEMP condition)')
        set_ec_value = XTEMP_ENABLE_PEC * 100
        value_bytes = set_ec_value.to_bytes(4, byteorder='little', signed=False)
        data = bytearray(b'\xFF' * 0x4000)
        data[:(self.fw_geometry.l52_total_vb_count * 4)] = value_bytes * self.fw_geometry.l52_total_vb_count
        self.set_ec(data)

        logger.flow(4, 'HW reset to enable XTEMP algorithm')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

        logger.flow(5, f'Issue VU 0xD08A to set NAND temperature to XTEMP_Refresh_T1 -1 = {XTEMP_REFRESH_T1 - 1}, changing Tstatus to "Cold Risky"')
       
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T1 - 1)
        time.sleep(idle_wait_detect_temp)
        
        logger.flow(6, f'write 1 tlc vb')
        total_len = self.TLC_VB_4K_SIZE
        self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)

        logger.flow(7, f'Issue VU 0xD08A to set NAND temperature to XTEMP_Refresh_T2 + 1 = {XTEMP_REFRESH_T2 + 1}, changing Tstatus to "Hot Risky"')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2 + 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow(7, f'Issue VU 0xD08A to set NAND temperature to safe zone')
        self.set_nand_temp(set_temp=(XTEMP_REFRESH_T2 +  XTEMP_REFRESH_T1) // 2)
        time.sleep(idle_wait_detect_temp)
        
        self.polling_bkops_idle()
    def test_xTempHotToColdStatCounter(self) -> None:
        XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2 = self.get_xtemp_parameter()
        idle_wait_detect_temp = XTEMP_TIME_DETECTION_VALUE

        logger.flow(3, f'Set all VB EC as (XTEMP_ENABLE_PEC * 100) = {XTEMP_ENABLE_PEC * 100} (enable XTEMP condition)')
        set_ec_value = XTEMP_ENABLE_PEC * 100
        value_bytes = set_ec_value.to_bytes(4, byteorder='little', signed=False)
        data = bytearray(b'\xFF' * 0x4000)
        data[:(self.fw_geometry.l52_total_vb_count * 4)] = value_bytes * self.fw_geometry.l52_total_vb_count
        self.set_ec(data)

        logger.flow(4, 'HW reset to enable XTEMP algorithm')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

        logger.flow(5, f'Issue VU 0xD08A to set NAND temperature to XTEMP_Refresh_T2 + 1 = {XTEMP_REFRESH_T2 + 1}, changing Tstatus to "Hot Risky"')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2 + 2)
        time.sleep(idle_wait_detect_temp)

        logger.flow(6, f'write 1 tlc vb')
        total_len = self.TLC_VB_4K_SIZE // 2
        self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)

        logger.flow(7, f'Issue VU 0xD08A to set NAND temperature to XTEMP_Refresh_T1 - 1 = {XTEMP_REFRESH_T1 - 1}, changing Tstatus to "Cold Risky"')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T1 - 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow(8, f'Issue VU 0xD08A to set NAND temperature to safe zone')
        self.set_nand_temp(set_temp=(XTEMP_REFRESH_T2 +  XTEMP_REFRESH_T1) // 2)
        time.sleep(idle_wait_detect_temp)

    def enter_exit_h8(self) -> None:
        f = ExecuteCMD.CmdSeqHibernate() 
        f.set_option(
            hibernate_enter=1,
            hibernate_exit=0,
            loopcount=1,
            delayafterenter=0,
            delayafterexit=0,
            wait_queue_empty=True,
            delay_time=0
        )
        
        ExecuteCMD.enqueue(f)
        ExecuteCMD.send(clear_on_success=True)
        ExecuteCMD.clear()
        time.sleep(60)
        f = ExecuteCMD.CmdSeqHibernate() 
        f.set_option(
            hibernate_enter=0,
            hibernate_exit=1,
            loopcount=1,
            delayafterenter=0,
            delayafterexit=0,
            wait_queue_empty=True,
            delay_time=0
        )
        
        ExecuteCMD.enqueue(f)
        ExecuteCMD.send(clear_on_success=True)
        ExecuteCMD.clear()
    def test_device_sleep_h8_time(self) -> None:
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.send(QD=1,clear_on_success=True)
        ExecuteCMD.clear()
        time.sleep(120)
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.send(QD=1,clear_on_success=True)
        ExecuteCMD.clear()
    def test_media_scan_finished_instance_num(self) -> None:
        api.sequential_write(lun=self.tlc_lun, start_lba=0, total_size=self.TLC_VB_4K_SIZE, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        param = project_api.micron_vu_C085_param_with_data()
        param.last_scan_spend_time = 10
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)
        time.sleep(10)
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
    def test_media_scan_finished_ScanVB(self) -> None:
        api.sequential_write(lun=self.tlc_lun, start_lba=0, total_size=self.TLC_VB_4K_SIZE, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        param = project_api.micron_vu_C085_param_with_data()
        #param.last_scan_spend_time = 54000 + 0x100  #15hour
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)
        i = 0
        while True:
            param.last_scan_spend_time = 0x1000000 + 0x100 * i 
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)
            time.sleep(10)
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            logger.info(f'i = {i}, status = {payload.media_scan_status.value}, finished = {payload.finish_group_num.value}, curr scan vb = {payload.cur_scan_vb.value},curr scan page = {payload.cur_scan_page.value}, curr_scan_group = {payload.scan_group.value}, scan count = {payload.scan_cnt.value}')
            i += 1
            if payload.scan_group.value == 22:
                break
    def test_media_scan_push_queue(self) -> None:
        api.sequential_write(lun=self.tlc_lun, start_lba=0, total_size=self.TLC_VB_4K_SIZE, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        pca = self.get_PCA_and_print(lun=self.tlc_lun, lba=0)
        self.inject_UECC(pca,SLC_enable=False)
        param = project_api.micron_vu_C085_param_with_data()
        #param.last_scan_spend_time = 54000 + 0x100  #15hour
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)
        i = 0
        while True:
            param.last_scan_spend_time = 0x1000000 + 0x100 * i  
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)
            time.sleep(10)
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            logger.info(f'i = {i}, status = {payload.media_scan_status.value}, finished = {payload.finish_group_num.value}, curr scan vb = {payload.cur_scan_vb.value},curr scan page = {payload.cur_scan_page.value}, curr_scan_group = {payload.scan_group.value}, scan count = {payload.scan_cnt.value}')
            i += 1
            if  payload.scan_group.value == 22:
                break
    def test_table_defrag_source_vb(self) -> None:
        total_len = self.TLC_VB_4K_SIZE 
        self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        _, vu_pca = project_api.issue_4051_to_get_physical_address(luID=self.tlc_lun, lba=0)
        vb = vu_pca.PPT_virtual_block_number.value
        logger.info(f'table vb before = {vb}')
        open_vb = self.get_and_print_open_vb_information()
        vb = open_vb.PTE_Block_VB_number_logical.value
        fep = open_vb.PTE_block_First_free_physical_page.value
        vb_list = [vb]
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.TableVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.MediumPriority)
        self.polling_bkops_idle()
        _, vu_pca = project_api.issue_4051_to_get_physical_address(luID=self.tlc_lun, lba=0)
        vb = vu_pca.PPT_virtual_block_number.value
        logger.info(f'table vb after = {vb}')

    def check_apl_status(self,status:int, total_len:int,data:List[List[project_api.AplInfo]], vb_type:str="")-> None:
        for ce in range(self.ce):
            for plane in range(self.plane):
                apl_status = data[ce][plane]
                logger.info(f'ce = {ce}, plane = {plane}')
                self.print_object_info_ai(apl_status)
                if vb_type == "PTE":
                    self.compare_value(apl_status.last_written_page.value,0xFFFFFFFF,desc="last_written_page",method=VERIFY_METHOD.NOT_EQUAL)
                    self.compare_value(apl_status.apl_status_of_host_vb.value,expect_value=0xFFFFFFFF,desc="apl_status_of_host_vb", method=VERIFY_METHOD.NOT_EQUAL)
                    self.compare_value(apl_status.apl_status_of_first_empty_page.value,expect_value=0xFFFFFFFF,desc="apl_status_of_first_empty_page", method=VERIFY_METHOD.NOT_EQUAL)
                else:
                    if ce == 0 : #write 1 ce page only ce = 0 have value
                        self.compare_value(apl_status.last_written_page.value,expect_value=total_len // self.ce_page - 1,desc="last_written_page")
                    else:
                        self.compare_value(apl_status.last_written_page.value,expect_value=0xFFFF,desc="last_written_page")
                    self.compare_value(apl_status.apl_status_of_host_vb.value,expect_value=status,desc="apl_status_of_host_vb")
                    self.compare_value(apl_status.apl_status_of_first_empty_page.value,expect_value=status,desc="apl_status_of_first_empty_page")
       
    def test_system_vb(self, vb_type:OpenSystemVBType) -> None:
        total_len = self.TLC_VB_4K_SIZE
        self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)

        logger.flow(6, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        
        data_40C3 = project_api.issue_40C3_to_get_params_of_ftl_status()
        
        open_system_vb = data_40C3.open_system_vb[vb_type]
        self.print_object_info_ai(open_system_vb)
        
        if vb_type == OpenSystemVBType.PT:
            response = project_api.issue_40C6_get_single_open_block(open_block_type = project_api.open_block_type_list.Pointer_to_Index_block, absolute_plane_identifier= 0, dump_payload= True)                        
            subinfo2 = project_api.SubVBInfo(response.data)
            
        elif vb_type == OpenSystemVBType.INDEX:
            response = project_api.issue_40C6_get_single_open_block(open_block_type = project_api.open_block_type_list.Index, absolute_plane_identifier= 0, dump_payload= True)                        
            subinfo2 = project_api.SubVBInfo(response.data)
        
        self.compare_value(open_system_vb.ftl_system_info_vb_number.value,expect_value=subinfo2.logicalvb.value, desc="ftl_system_info_vb_number")
        self.compare_value(open_system_vb.ftl_system_info_die_number.value,expect_value=subinfo2.CE.value, desc="ftl_system_info_die_number")
        self.compare_value(open_system_vb.ftl_system_info_start_plane.value,expect_value=subinfo2.plane.value, desc="ftl_system_info_start_plane")

    def test_table_vb(self) -> None:
        
        for i in range(15):
            pte_update_spor_occurred = False
            total_len = 4096*1
            self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)

            data_40C1 = self.get_and_print_open_vb_information()
            vb = data_40C1.PTE_Block_VB_number_logical.value
            logger.info(f'before vb = {vb}')
            fep = data_40C1.PTE_block_First_free_physical_page.value

            self.flipbit_on_PTE_smart()
            testlun = 0
            cmd_count = random.randint(10, 32)
            min_lun = self.tlc_lun
            max_lun = self.tlc_lun
            min_lba = 0
            max_lba = self._param.gLUCapacity[self.tlc_lun]
            min_size = api.BLOCK4K_SIZE_64M_BYTE
            max_size = api.BLOCK4K_SIZE_128M_BYTE
            self.random_write_spor(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=True, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            
            logger.flow(6, f'HW reset without SSU')
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
            open_vb = self.get_and_print_open_vb_information()
            after_vb = open_vb.PTE_Block_VB_number_logical.value
            logger.info(f'after vb = {after_vb}')
            if vb != after_vb:
                logger.info(f'vb = {after_vb}')
            payloadbuf = self.issue_40D1_to_get_system_init_time_stamp()
            por_flag = int.from_bytes(payloadbuf[88:92], byteorder='little')
            print(por_flag)
            if (por_flag & BIT6) >0:
                print(por_flag)
                pte_update_spor_occurred = True
            
            if pte_update_spor_occurred == True:
                data_40C3 = project_api.issue_40C3_to_get_params_of_ftl_status()
                
                table_vb = data_40C3.table_vb
                self.print_object_info_ai(table_vb)
                
                self.compare_value(table_vb.table_vb_number.value,expect_value=data_40C1.PTE_Block_VB_number_logical.value, desc="table_vb_number")
                self.compare_value(table_vb.first_free_pp_in_table_vb.value,0xFFFFFFFF, desc="first_free_pp_in_table_vb",method=VERIFY_METHOD.NOT_EQUAL)
        
                self.check_apl_status(status = 0, total_len =total_len, data=table_vb.apl_status_list,vb_type="PTE")
            else:
                logger.info(f'not spor when updating pte')
    def test_open_data_gc_vb(self,vb_type:OpenDataVBType) -> None:
        # project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        # project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x00)
        # project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x02)
        if vb_type == OpenDataVBType.DM_NORMAL_DEFRAG_VB:
            total_len = self.tlc_ce_page
            total_len = self.TLC_VB_4K_SIZE
            lun=self.tlc_lun
            slc_mode = 0
            slc_enable = False
            stoppage = self.tlc_max_page
            
        elif vb_type == OpenDataVBType.DM_EM1_DEFRAG_VB:
            total_len = self.slc_ce_page
            total_len = self.SLC_VB_4K_SIZE
            lun=self.slc_lun
            slc_mode = 1
            slc_enable = True
            stoppage = self.slc_max_page
        self.write_data(lun=lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        time.sleep(2)
        
        _, data = project_api.issue_4051_to_get_physical_address(luID=lun,lba= 0)
        pca = self.get_PCA_and_print(lun=lun, lba=0)
        vb_before = data.virtual_block_number.value
        #name = self.check_vb_in_which_group(vb_before)
        logger.info(f'before init vb = {vb_before}')
        data_40C3 = project_api.issue_40C3_to_get_params_of_ftl_status()
        if vb_type == OpenDataVBType.DM_NORMAL_DEFRAG_VB:
            logger.info(f'GCTLCDataSize_NORMAL before C087 = {data_40C3.GCTLCDataSize_NORMAL.value}')
        else:
            logger.info(f'GCSLCDataSize_EM1 before C087 = {data_40C3.GCSLCDataSize_EM1.value}')
        vb_list = [data.virtual_block_number.value]
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.LowPriority)
       
        data_40C3 = project_api.issue_40C3_to_get_params_of_ftl_status()
        if vb_type == OpenDataVBType.DM_NORMAL_DEFRAG_VB:
            logger.info(f'GCTLCDataSize_NORMAL before init = {data_40C3.GCTLCDataSize_NORMAL.value}')
        else:
            logger.info(f'GCSLCDataSize_EM1 before init = {data_40C3.GCSLCDataSize_EM1.value}')
        open_data = data_40C3.open_data_vb[vb_type]
        self.print_object_info_ai(open_data)
        logger.flow(6, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)

        data_40C3 = project_api.issue_40C3_to_get_params_of_ftl_status()
        if vb_type == OpenDataVBType.DM_NORMAL_DEFRAG_VB:
            logger.info(f'GCTLCDataSize_NORMAL after init = {data_40C3.GCTLCDataSize_NORMAL.value}')
        else:
            logger.info(f'GCSLCDataSize_EM1 after init = {data_40C3.GCSLCDataSize_EM1.value}')
        open_data = data_40C3.open_data_vb[vb_type]
        self.print_object_info_ai(open_data)
        self.check_value_exist(open_data.host_logic_vb_number.value, "host_logic_vb_number")
        self.check_value_exist(open_data.host_physical_vb_number.value, "host_logic_vb_number")
        self.check_value_exist(open_data.vb_is_slc.value, "vb_is_slc")
        self.check_value_exist(open_data.host_vb_first_free_pp.value, "host_vb_first_free_pp")
        self.check_value_exist(open_data.host_vb_last_valid_page.value, "host_vb_last_valid_page")
        self.check_value_exist(open_data.host_vb_last_stable_page.value, "host_vb_last_stable_page")

        for ce in range(self.ce):
            for plane in range(self.plane):
                apl_status = data_40C3.open_data_vb[vb_type].apl_status_list[ce][plane]
                logger.info(f'ce = {ce}, plane = {plane}')
                self.print_object_info_ai(apl_status)

                self.check_value_exist(apl_status.last_written_page.value, "last_written_page")
                self.check_value_exist(apl_status.apl_status_of_host_vb.value, "apl_status_of_host_vb")
                self.check_value_exist(apl_status.apl_status_of_first_empty_page.value, "apl_status_of_first_empty_page")
                
        self.polling_bkops_idle()

        # _, data_40C1 = project_api.issue_40C1_to_get_open_vb_information()
        # self.print_object_info_ai(data_40C1)
        # pca = self.get_PCA_and_print(lun=lun, lba=0)
        # _, data = project_api.issue_4051_to_get_physical_address(luID=lun,lba= 0)
        # vb_after = data.virtual_block_number.value
        # logger.info(f'after init vb = {vb_after}')
        
        # data_40C3 = project_api.issue_40C3_to_get_params_of_ftl_status()
        
        # _, data = project_api.issue_4051_to_get_physical_address(luID=lun,lba= 0)
        # pca = self.get_PCA_and_print(lun=lun, lba=0)
        # vb_after = data.virtual_block_number.value
        # logger.info(f'after init vb = {vb_after}')

        # open_data = data_40C3.open_data_vb[vb_type]
        # self.print_object_info_ai(open_data)
        # self.check_apl_status(data.virtual_block_number.value, slcmode=0,startpage=0,stoppage=stoppage,status = 0, total_len =total_len, data=open_data.apl_status_list)
        
        #project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        # project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x01)
        # project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x03)
        #self.polling_bkops_idle()
        

    def get_dummy_size(self,total_len:int, slc_mode:int)->int:
        if slc_mode == 1:
            dummy = 0 if (total_len % 4 == 0) else (4 - total_len % 4)
        else:
            dummy = 0 if (total_len % self.tlc_ce_page == 0) else (self.tlc_ce_page - total_len % self.tlc_ce_page)
        return dummy
    def test_open_data_vb(self, vb_type:OpenDataVBType) -> None:
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        if vb_type == OpenDataVBType.DM_NORMAL_HOST_VB:
            total_len = self.tlc_ce_page
            lun=self.tlc_lun
            slcmode = 0
            slc_enable = False
            stoppage = self.tlc_max_page
            
        elif vb_type == OpenDataVBType.DM_NORMAL_SHARE_VB_0:
            total_len = self.slc_ce_page
            lun=self.slc_lun
            slcmode = 1
            slc_enable = True
            stoppage = self.slc_max_page
        else:
            api.set_flag(api.FlagIDN.WRITEBOOSTER_EN)
            total_len = self.slc_ce_page
            lun=self.tlc_lun
            slcmode = 1
            slc_enable = True
            stoppage = self.slc_max_page

        self.write_data(lun=lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        
        _, data = project_api.issue_4051_to_get_physical_address(luID=lun,lba= 0)
        pca = self.get_PCA_and_print(lun=lun, lba=0)
        logger.info(f'vb = {data.virtual_block_number.value}')

        logger.flow(6, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        
        data_40C1  = self.get_and_print_open_vb_information()
        data_40C3 = project_api.issue_40C3_to_get_params_of_ftl_status()
        
        open_data = data_40C3.open_data_vb[vb_type]
        self.print_object_info_ai(open_data)
        

        if vb_type == OpenDataVBType.DM_NORMAL_HOST_VB:
            self.compare_value(open_data.host_logic_vb_number.value,expect_value=data_40C1.L2_Open_logical_VB_Host_TLC_number.value, desc="host_logic_vb_number")
            self.compare_value(open_data.host_physical_vb_number.value,expect_value=data_40C1.open_Remap_VB_number_for_L2_Open_logical_VB_Host_TLC.value, desc="host_physical_vb_number")
            self.compare_value(open_data.vb_is_slc.value,expect_value=0, desc="vb_is_slc")

            self.compare_value(open_data.host_vb_last_stable_page.value,expect_value=0,desc="host_vb_last_stable_page")
        elif vb_type == OpenDataVBType.DM_NORMAL_SHARE_VB_0:
            self.compare_value(open_data.host_logic_vb_number.value,expect_value=data_40C1.open_logical_VB_number_for_EM1_L2_Host.value, desc="host_logic_vb_number")
            self.compare_value(open_data.host_physical_vb_number.value,expect_value=data_40C1.open_Remap_VB_number_for_EM1_L2_Host.value, desc="host_physical_vb_number")
            self.compare_value(open_data.vb_is_slc.value,expect_value=1, desc="vb_is_slc")
            
        else:
            self.compare_value(open_data.host_logic_vb_number.value,expect_value=data_40C1.open_logical_VB_number_for_Write_Booster_WB_L2.value, desc="host_logic_vb_number")
            self.compare_value(open_data.host_physical_vb_number.value,expect_value=data_40C1.open_Remap_VB_number_for_Write_Booster_WB_L2.value, desc="host_physical_vb_number")
            self.compare_value(open_data.vb_is_slc.value,expect_value=1, desc="vb_is_slc")
        
        self.compare_value(open_data.host_vb_first_free_pp.value,expect_value=total_len //4, desc="host_vb_first_free_pp")

        self.compare_value(open_data.host_vb_last_valid_page.value,expect_value=total_len //4,desc="host_vb_last_valid_page")
        self.compare_value(open_data.host_vb_last_stable_page.value,expect_value=0,desc="host_vb_last_stable_page")

        
        logger.info(f'vb = {data.virtual_block_number.value}')
        self.check_apl_status(status = 0, total_len =total_len, data=open_data.apl_status_list)
    
    def step1(self) -> None:
        
        logger.flow(1, "Config slc lun au = 1/2 total au , tlc lun au = 1/2 total au")
        self.slc_lun, self.tlc_lun = self.config_lun(slc_au=self.total_au // 2,tlc_au=self.total_au // 2)

        logger.flow(1, 'check offset[0:3] buffer size')
        self.check_value("buffer_size", 6144)

        logger.flow(2, 'check offset[4:7] Power loss flag')
        self.check_value("power_loss_flag", 0xFFFFFFFF, VERIFY_METHOD.NOT_EQUAL)

        logger.flow(2, 'check APL info')
        self.test_open_data_vb(OpenDataVBType.DM_NORMAL_HOST_VB)
        self.test_open_data_vb(OpenDataVBType.DM_NORMAL_SHARE_VB_0)
        self.test_open_data_vb(OpenDataVBType.DM_NORMAL_WB_VB_0)

        # self.test_open_data_gc_vb(OpenDataVBType.DM_NORMAL_DEFRAG_VB) 
        # self.test_open_data_gc_vb(OpenDataVBType.DM_EM1_DEFRAG_VB) 
        
        #[shall test]
        #self.test_table_vb()

        #[pass]
        self.test_system_vb(OpenSystemVBType.PT)
        #[fail]
        #self.test_system_vb(OpenSystemVBType.INDEX)

        #[pass]
        logger.flow(1, "test hostSLCDataSize_NORMAL")
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        total_len = self.SLC_VB_4K_SIZE // 2
        dummy = self.get_dummy_size(total_len=total_len,slc_mode=1)
        test_hostSLCDataSize_NORMAL = lambda:self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        self.verify_40C3_value("hostSLCDataSize_NORMAL",test_hostSLCDataSize_NORMAL, times=1, expected_delta=total_len+dummy)
        
        logger.flow(2, "test hostTLCDataSize_WriteBooster")
        self.verify_40C3_value("hostTLCDataSize_WriteBooster",test_hostSLCDataSize_NORMAL, times=1, expected_delta=total_len+dummy)
        
        logger.flow(2, "test hostSLCOpenVBCount")
        self.check_value("hostSLCOpenVBCount",expect_value=1)

        logger.flow(3, "test hostSLCDataSize_EM1")
        test_hostSLCDataSize_EM1 = lambda:self.write_data(lun=self.slc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        self.verify_40C3_value("hostSLCDataSize_EM1",test_hostSLCDataSize_EM1, times=1, expected_delta=total_len+dummy)
        
        logger.flow(4, "test hostSLCDataSize_EM1 RPMB")
        total_len = 4
        dummy = self.get_dummy_size(total_len=total_len, slc_mode = 1)
        test_hostSLCDataSize_RPMB = lambda:self.RPMB_write_data(total_len=total_len)
        self.verify_40C3_value("hostSLCDataSize_EM1",test_hostSLCDataSize_RPMB, times=1, expected_delta=total_len+dummy)

        logger.flow(5, "test hostSLCDataSize_RPMB")
        self.verify_40C3_value("hostSLCDataSize_RPMB",test_hostSLCDataSize_RPMB, times=1, expected_delta=total_len+dummy)
        
        logger.flow(5, "test EM1OpenVBCount")
        self.check_value("EM1OpenVBCount",expect_value=1)

        #[fail]
        logger.flow(6, "test hostTLCDataSize_NORMAL")
        # api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        # total_len = self.TLC_VB_4K_SIZE // 2
        # test_hostTLCDataSize_NORMAL = lambda:self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        # dummy = self.get_dummy_size(total_len=total_len,slc_mode=0)
        # self.verify_40C3_value("hostTLCDataSize_NORMAL",test_hostTLCDataSize_NORMAL, times=1, expected_delta=(self.TLC_VB_4K_SIZE // 2) + dummy)
        
        logger.flow(6, "test hostTLCOpenVBCount")
        self.check_value("hostTLCOpenVBCount",expect_value=1)

        #[fail]
        logger.flow(6, "test GCSLCDataSize_NORMAL")
        #self.test_gc_info("GCSLCDataSize_NORMAL", VERIFY_METHOD.GREATER, expected_val=0) 
        
        #[fail]
        logger.flow(6, "test GCSLCDataSize_EM1")
        #self.test_gc_info("GCSLCDataSize_EM1", VERIFY_METHOD.GREATER, expected_val=0)
        
        #[fail]
        logger.flow(6, "GCTLCDataSize_NORMAL")
        #self.test_gc_info("GCTLCDataSize_NORMAL",VERIFY_METHOD.GREATER, expected_val=0)
        pass

        # #[pass]
        logger.flow(7, "test hostSLCDummySize_NORMAL")
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        total_len = self.SLC_VB_4K_SIZE // 2
        dummy = self.get_dummy_size(total_len=total_len, slc_mode = 1)
        test_hostTLCDataSize_NORMAL = lambda:self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        self.verify_40C3_value("hostSLCDummySize_NORMAL",test_hostTLCDataSize_NORMAL, times=1, expected_delta=dummy)

        # #[pass]
        logger.flow(8, "test hostSLCDummySize_EM1")
        total_len = self.SLC_VB_4K_SIZE // 2
        dummy = self.get_dummy_size(total_len=total_len, slc_mode = 1)
        test_hostSLCDataSize_EM1 = lambda:self.write_data(lun=self.slc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        self.verify_40C3_value("hostSLCDummySize_EM1",test_hostSLCDataSize_EM1, times=1, expected_delta=dummy)
        
        # #[fail]
        logger.flow(9, "test hostSLCDummySize_RPMB")
        total_len = 4
        dummy = self.get_dummy_size(total_len=total_len, slc_mode = 1)
        test_hostSLCDataSize_RPMB = lambda:self.RPMB_write_data(total_len=total_len)
        #self.verify_40C3_value("hostSLCDummySize_RPMB",test_hostSLCDataSize_RPMB, times=1, expected_delta=dummy)
        
        # #[fail]
        logger.flow(10, "test hostTLCDummySize_NORMAL")
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        total_len = (self.TLC_VB_4K_SIZE // 2)
        dummy = self.get_dummy_size(total_len=total_len, slc_mode = 0)
        test_hostTLCDataSize_NORMAL = lambda:self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        #self.verify_40C3_value("hostTLCDummySize_NORMAL",test_hostTLCDataSize_NORMAL, times=1, expected_delta=dummy)
        
        # #[pass]
        logger.flow(11, "test hostTLCDummySize_WriteBooster")
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        total_len = self.SLC_VB_4K_SIZE // 2
        dummy = self.get_dummy_size(total_len=total_len, slc_mode = 1)
        test_hostTLCDataSize_NORMAL = lambda:self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        self.verify_40C3_value("hostTLCDummySize_WriteBooster",test_hostTLCDataSize_NORMAL, times=1, expected_delta=dummy)
        
        #[fail]
        # logger.flow(6, "test GCSLCDummySize_NORMAL")
        # self.test_gc_info("GCSLCDummySize_NORMAL", VERIFY_METHOD.GREATER, expected_val=0)
        
        # logger.flow(6, "test GGCSLCDummySize_EM1")
        # self.test_gc_info("GCSLCDummySize_EM1", VERIFY_METHOD.GREATER, expected_val=0)
        
        # logger.flow(6, "test GCTLCDummySize_NORMAL")
        # self.test_gc_info("GCTLCDummySize_NORMAL", VERIFY_METHOD.GREATER, expected_val=0)
        
        # api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        # self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=self.TLC_VB_4K_SIZE // 2)        
        # self.write_data(lun=self.slc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=self.SLC_VB_4K_SIZE // 2)
        
        #[fail]
        logger.flow(6, "Test GCOpenVBCount")
        #self.test_gc_info("GCOpenVBCount", expected_val=1)
        
        #[fail]
        logger.flow(6, "Test EM1GCOpenVBCount")
        #self.test_gc_info("EM1GCOpenVBCount", expected_val=1)

        #[pass]   fail????
        logger.flow(6, "Test oneShotTableDefragCount")
        #self.test_oneShotTableDefragCount("oneShotTableDefragCount")

        #[fail]
        logger.flow(6, "Test sliceTableDefragCount")
        self.verify_40C3_value("sliceTableDefragCount",self.test_table_defrag_source_vb, times=1, expected_delta=1)
        
        #[not yet]
        logger.flow(6, "Test maxHostGCCadence")
        #self.check_value("maxHostGCCadence", expect_value=0, method=VERIFY_METHOD.GREATER)
        logger.flow(6, "Test maxTableGCCadence")
        #self.check_value("maxTableGCCadence", expect_value=0, method=VERIFY_METHOD.GREATER)
        
        logger.flow(6, "Test discardCount")
        self.verify_40C3_value("discardCount",self.test_discardCount, times=1, expected_delta=1)
        
        logger.flow(6, "Test eraseCount")
        self.verify_40C3_value("eraseCount",self.test_eraseCount, times=1, expected_delta=1)
        
        logger.flow(6, "Test wipeDeviceCount")
        test_wipecount = lambda:self.clear_card()
        self.verify_40C3_value("wipeDeviceCount",test_wipecount, times=1, expected_delta=1)
        
        logger.flow(6, "Test hostSlcECCount")
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=self.SLC_VB_4K_SIZE // 2)
        ec_cnt = self.get_vb_ec_cnt(lun=self.tlc_lun, lba=0) 
        self.check_value("hostSlcECCount", ec_cnt)

        logger.flow(6, "hostTlcECCount")
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=self.TLC_VB_4K_SIZE // 2)
        ec_cnt = self.get_vb_ec_cnt(lun=self.tlc_lun, lba=0) 
        self.check_value("hostTlcECCount", ec_cnt)

        logger.flow(6, "Test EM1ECCount")
        self.write_data(lun=self.slc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=self.SLC_VB_4K_SIZE // 2)
        ec_cnt = self.get_vb_ec_cnt(lun=self.slc_lun,lba=0) 
        self.check_value("EM1ECCount", ec_cnt)

        #[pass]
        logger.flow(6, "Test FTLECCount")
        pt = project_api.get_PT_physical_block_information()
        self.check_value("FTLECCount" , pt.erase_cnt.value)
        
        #[fail]  #43C 
        logger.flow(6, "Test RefreshCnt")
        #self.verify_40C3_value("RefreshCnt",self.test_RefreshCnt, times=1,expected_delta=0,method=VERIFY_METHOD.GREATER)

        #[pass]
        logger.flow(6, "Test Read_Disturb_Trigger_Num")
        self.verify_40C3_value("Read_Disturb_Trigger_Num",self.test_read_disturb_trigger_num, times=1, expected_delta=1)
       
        #[fail]
        logger.flow(6, "Test Media_Scan_finished_Instance_Num")
        #self.verify_40C3_value("Media_Scan_finished_Instance_Num",self.test_media_scan_finished_instance_num, times=1, expected_delta=1)
        
        #[pass]
        logger.flow(6, "Test mediaScanFinishScanVB")
        #self.verify_40C3_value("mediaScanFinishScanVB",self.test_media_scan_finished_ScanVB, times=1, expected_delta=0, method=VERIFY_METHOD.GREATER)
        
        logger.flow(6, "Test mediaScanBookVbCount")
        #self.verify_40C3_value("mediaScanBookVbCount",self.test_media_scan_push_queue, times=1, expected_delta=1)
        
        #[shall verify]
        # self.clear_card()
        logger.flow(6, "Test media_scan_trigger_vb_total_count")
        #self.verify_40C3_value("media_scan_trigger_vb_total_count",self.test_media_scan_finished_ScanVB, times=1, expected_delta=0, method=VERIFY_METHOD.GREATER)
        
        #[fail]
        logger.flow(6, "Test counterDeltaT1")
        #self.verify_40C3_value("counterDeltaT1",self.test_counterDeltaT1, times=1, expected_delta=1)
        
        logger.flow(6, "Test counterDeltaT2")
        #self.verify_40C3_value("counterDeltaT2",self.test_counterDeltaT2, times=1, expected_delta=1)
        
        #[fail - opposite]
        logger.flow(6, "Test xTempColdToHotStatCounter")
        #self.verify_40C3_value("xTempColdToHotStatCounter", self.test_xTempColdToHotStatCounter, times=1, expected_delta=1)
        
        logger.flow(6, "Test xTempHotToColdStatCounter")
        #self.verify_40C3_value("xTempHotToColdStatCounter", self.test_xTempHotToColdStatCounter, times=1, expected_delta=1)
        
        
        #[pass]
        logger.flow(6, "Test idleTimeAndHybernate")
        test_idle = lambda : time.sleep(60)
        self.verify_40C3_value("idleTimeAndHybernate", test_idle, times = 1, expected_delta = 1)
        test_hibernate = lambda : self.enter_exit_h8()
        self.verify_40C3_value("idleTimeAndHybernate", test_hibernate, times = 1, expected_delta = 1)
        
        #[pass]
        logger.flow(6, "Test refreshCountDone")
        self.verify_40C3_value("refreshCountDone", self.test_RefreshCnt,times=1,expected_delta=0, method=VERIFY_METHOD.GREATER)
        
        #[fail]
        logger.flow(6, "Test sliceRefreshDone")
        self.verify_40C3_value("sliceRefreshDone", self.test_SliceRefreshDone,times=1,expected_delta=1)

        #[pass]
        logger.flow(6, "Test bfeaFinishScanVB")
        self.verify_40C3_value("bfeaFinishScanVB",self.test_bfea_finish_scan_vb, times=1,expected_delta=0, method=VERIFY_METHOD.GREATER)
        
        #[pass]
        logger.flow(6, "Test rehBookVbCount")
        self.verify_40C3_value("rehBookVbCount",self.test_reh_book_vb_count, times=1, expected_delta=1)
        
        #[pass]
        logger.flow(6, "Test read_disturb_scan_trigger_VB_total_count")
        self.verify_40C3_value("read_disturb_scan_trigger_VB_total_count",self.test_read_disturb_trigger_num, times=1, expected_delta=1)   
        
        #[pass]
        logger.flow(6, "Test Table_defrag_source_VB")
        self.verify_40C3_value("Table_defrag_source_VB",self.test_table_defrag_source_vb, times=1, expected_delta=1)
        
        logger.flow(6, "Test Total_slice_table_defrag_count")
        #self.verify_40C3_value("Total_slice_table_defrag_count",self.test_table_defrag_source_vb, times=1, expected_delta=1)
        
        #[pass]
        logger.flow(6, "Test Total_one_shot_table_defrag_count")
        self.test_oneShotTableDefragCount("Test Total_one_shot_table_defrag_count")

        #[pass]
        logger.flow(6, "Test read_disturb_scan_trigger_VB_total_count")
        self.verify_40C3_value("read_disturb_scan_trigger_VB_total_count",self.test_read_disturb_trigger_num, times=1, expected_delta=1)
        
        #[pass]
        logger.flow(6, "Test bbtCurSubVBIdx")
        self.bbt_sub_vb_info = project_api.get_BBT_physical_block_information()
        self.check_value("bbtCurSubVBIdx", self.bbt_sub_vb_info.CE.value * 6 + self.bbt_sub_vb_info.plane.value)
        
        #[pass]
        logger.flow(6, "Test bbtFirstFreePP")
        self.check_value("bbtFirstFreePP", self.bbt_sub_vb_info.First_empty_page.value)
        
        logger.flow(6, "Test write_data_volume_25MB")
        test_write_data_volume_25MB = lambda:self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=BLOCK4K_SIZE_1M_BYTE * 25)
        self.verify_40C3_value("write_data_volume_25MB",test_write_data_volume_25MB, times=1, expected_delta=1)

        logger.flow(6, "Test write_data_volume_4KB")
        test_write_data_volume_4KB = lambda:self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=BLOCK4K_SIZE_4K_BYTE)
        self.verify_40C3_value("write_data_volume_4KB",test_write_data_volume_4KB, times=1, expected_delta=1)

        #[how to verify]
        logger.flow(6, "Test read_reclaim_count")
        #self.verify_40C3_value("read_reclaim_count", self.test_read_disturb_trigger_num,times=1,expected_delta=1)
        
        #[pass]
        logger.flow(6, "Test read_data_volume_25MB")
        test_read_data_volume_25MB = lambda:self.read_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=BLOCK4K_SIZE_1M_BYTE * 25)
        self.verify_40C3_value("read_data_volume_25MB",test_read_data_volume_25MB, times=1, expected_delta=1)

        logger.flow(6, "Test read_data_volume_4KB")
        test_read_data_volume_4KB = lambda:self.read_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=BLOCK4K_SIZE_4K_BYTE)
        self.verify_40C3_value("read_data_volume_4KB",test_read_data_volume_4KB, times=1, expected_delta=1)
        
        logger.flow(6, "Test SLC_read_reclaim_count")
        #self.check_value("SLC_read_reclaim_count", 1)
        logger.flow(6, "Test TLC_read_reclaim_count")
        #self.check_value("TLC_read_reclaim_count" , 1)
        logger.flow(6, "Test EM1_read_reclaim_count")
        #self.check_value("EM1_read_reclaim_count", 1)
        
        #[pass]
        logger.flow(6, "Test clean_init_count")
        test_clean_init_count = lambda:api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
        self.verify_40C3_value("clean_init_count",test_clean_init_count, times=1, expected_delta=1)

        logger.flow(6, "Test dirty_init_count")
        test_dirty_init_count = lambda:api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
        self.verify_40C3_value("dirty_init_count",test_dirty_init_count, times=1, expected_delta=1)

        #[fail]
        logger.flow(6, "Test SPOR_write_fail_count")
        #test_spor_write_fail_count = lambda: self.write_1_VB_with_SPOR()
        #self.verify_40C3_value("SPOR_write_fail_count",test_spor_write_fail_count, times=1, expected_delta=1)
        
        #[pass]
        logger.flow(6, "Test SPOR_recovery_count")
        self.verify_40C3_value("SPOR_recovery_count",self.test_spor_recovery_count, times=1, expected_delta=1)
        
        #[pass]
        logger.flow(6, "Test write_EM1_data_volume_25MB")
        test_em1_data_volume_25MB = lambda:self.write_data(lun=self.slc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=BLOCK4K_SIZE_1M_BYTE * 25)
        
        logger.flow(12, "test write_EM1_data_volume_25MB")
        self.verify_40C3_value("write_EM1_data_volume_25MB",test_em1_data_volume_25MB, times=1, expected_delta=1)
        
        # [maybe change]
        logger.flow(6, "Test write_EM1_data_volume_4KB")
        test_em1_data_volume_4KB = lambda:self.write_data(lun=self.slc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=BLOCK4K_SIZE_4K_BYTE)
        self.verify_40C3_value("write_EM1_data_volume_4KB",test_em1_data_volume_4KB, times=1, expected_delta=1)
        
        #[pass]
        logger.flow(6, "Test WRITTEN_WB_100M")
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        test_written_wb_100m = lambda:self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=BLOCK4K_SIZE_1M_BYTE * 100)
        self.verify_40C3_value("WRITTEN_WB_100M",test_written_wb_100m, times=1, expected_delta=1)

        logger.flow(6, "Test WRITTEN_NORMAL_100M")
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        test_written_normal_100m = lambda:self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=BLOCK4K_SIZE_1M_BYTE * 100)
        self.verify_40C3_value("WRITTEN_NORMAL_100M",test_written_normal_100m,  times=1, expected_delta=1)
        
        #[pass]
        logger.flow(6, "Test DEVICE_ON_TIME")
        for i in range(500):
            self.read_data(lun=self.tlc_lun, start_lba = 0, len =1, total_len =1 )
        self.check_value("DEVICE_ON_TIME", expect_value=0, method=VERIFY_METHOD.GREATER)
        
        logger.flow(6, "Test HOST_WRITE_COMMAND_COUNT_LOWER(WB)")
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        total_card_4K = self.total_au * 1024
        total_len = (self._param.gLUCapacity[self.tlc_lun] * 10) // 100
        if total_len % 4096 != 0:
            total_len = total_len + 4096 - total_len % 4096
        test_host_write_cmd_cnt = lambda:self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        self.verify_40C3_value("HOST_WRITE_COMMAND_COUNT_LOWER",test_host_write_cmd_cnt,  times=1, expected_delta=math.ceil(total_len/WRITE_10_MAX_BLOCK_LEN))
        
        logger.flow(6, "Test VALID_CNT(TLC)")
        self.verify_40C3_value("VALID_CNT",test_host_write_cmd_cnt,  times=1, expected_delta=math.ceil(total_len/total_card_4K))
        
        logger.flow(6, "Test HOST_READ_COMMAND_COUNT_LOWER(TLC)")
        test_host_read_cmd_cnt = lambda:self.read_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=BLOCK4K_SIZE_4K_BYTE)
        self.verify_40C3_value("HOST_READ_COMMAND_COUNT_LOWER",test_host_read_cmd_cnt,  times=1, expected_delta=1)
        
    
        logger.flow(14, "Test HOST_WRITE_COMMAND_COUNT_LOWER(WB)")
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        test_host_write_cmd_cnt = lambda:self.write_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        self.verify_40C3_value("HOST_WRITE_COMMAND_COUNT_LOWER",test_host_write_cmd_cnt,  times=1, expected_delta=math.ceil(total_len/WRITE_10_MAX_BLOCK_LEN))
        
        #[fail]
        logger.flow(14, "Test VALID_CNT(WB)")
        #self.verify_40C3_value("VALID_CNT",test_host_write_cmd_cnt,  times=1, expected_delta=math.ceil(total_len/total_card_4K))
        
        logger.flow(14, "Test HOST_READ_COMMAND_COUNT_LOWER(WB)")
        test_host_read_cmd_cnt = lambda:self.read_data(lun=self.tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=BLOCK4K_SIZE_4K_BYTE)
        self.verify_40C3_value("HOST_READ_COMMAND_COUNT_LOWER",test_host_read_cmd_cnt,  times=1, expected_delta=1)
        
        logger.flow(14, "Test HOST_WRITE_COMMAND_COUNT_LOWER(EM1)")
        total_len = (self._param.gLUCapacity[self.slc_lun] * 50) // 100
        if total_len % 4096 != 0:
            total_len = total_len + 4096 - total_len % 4096
        test_host_write_cmd_cnt = lambda:self.write_data(lun=self.slc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        self.verify_40C3_value("HOST_WRITE_COMMAND_COUNT_LOWER",test_host_write_cmd_cnt,  times=1, expected_delta=math.ceil(total_len/WRITE_10_MAX_BLOCK_LEN))
        
        #[fail]
        # logger.flow(14, "test VALID_CNT(EM1)")
        # self.verify_40C3_value("VALID_CNT",test_host_write_cmd_cnt,  times=1, expected_delta=math.ceil(total_len/total_card_4K))
        # test_host_read_cmd_cnt = lambda:self.read_data(lun=self.slc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=BLOCK4K_SIZE_4K_BYTE)
        
        logger.flow(15, "test HOST_READ_COMMAND_COUNT_LOWER(EM1)")
        self.verify_40C3_value("HOST_READ_COMMAND_COUNT_LOWER",test_host_read_cmd_cnt,  times=1, expected_delta=1)
        
        #[pass]
        logger.flow(6, "Test HOST_WRITE_COMMAND_COUNT_UPPER")
        self.check_value("HOST_WRITE_COMMAND_COUNT_UPPER", expect_value=0)

        logger.flow(6, "Test HOST_READ_COMMAND_COUNT_UPPER")
        self.check_value("HOST_READ_COMMAND_COUNT_UPPER", expect_value=0)
        
        #[pass]
        logger.flow(16, "test DEVICE_SLEEP_H8_TIME")
        self.verify_40C3_value("DEVICE_SLEEP_H8_TIME",self.test_device_sleep_h8_time,  times=1, expected_delta=2)

        pass
    def check_vb_in_specific_pool(self,vb_number:int, vb_group_name:str) ->bool:
        vb_info = project_api.VBInfo()
        vb_list = []
        for vb, info in vb_info.list.items():
            if project_api.VBList().vb_group_list()[vb_group_name] == info['group']:
                vb_list.append(vb)
                logger.debug('vb = %d' % vb)
                logger.debug('partition = %d' % info['partition'])
        logger.info(f'{vb_group_name} vb list, len = {len(vb_list)}')
        if vb_number in vb_list:
            return True
        return False
    def trigger_pte_gc(self,lun:int, vb_number:int) -> None:
        gc_trigger = False

        start_time = time.time()
        timeout_min = 120

        while(gc_trigger == False):
            if self.check_timeout(start_time, timeout_min):
                logger.error(f'Cannot create system vb GC in {timeout_min} min')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            total_write_len = api.WRITE_10_MAX_BLOCK_LEN
            startlba = random.randint(0, self._param.gLUCapacity[lun]-1-total_write_len)

            self.write_data(lun=lun,start_lba=startlba,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_write_len)
            gc_trigger = self.check_vb_in_specific_pool(vb_number,"FREE_BLK_QUEUE_TABLE")
            if gc_trigger == True:
                logger.info('vb number gc to free block')

        # start_time = time.time()
        # while(True):
        #     if self.check_timeout(start_time, timeout_min):
        #         logger.error(f'Cannot reuse system vb in {timeout_min} min')
        #         raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
        #     total_write_len = api.WRITE_10_MAX_BLOCK_LEN
        #     startlba = random.randint(0, self._param.gLUCapacity[lun]-1-total_write_len)

        #     self.write_data(lun=lun,start_lba=startlba,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_write_len)
        #     if not self.check_vb_in_specific_pool(vb_number,"FREE_BLK_QUEUE_TABLE"):
        #         logger.info('random write -> vb goto free table group -> write -> check vb not in free table queue')
        #         break

    def polling_bkops_idle(self) -> None:
        start_time_inner = time.time()
        while True:
            self.check_timeout(start_time=start_time_inner,timeout_min=15)
            bkops_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
            if bkops_status == 0:
                break
            time.sleep(1)
    def print_object_info_ai(self,object: Any, extra_dump:bool = False) -> None:
        logger.info(f'================= [{object.__class__.__name__}]=================', extra_dump=extra_dump)
        fields = [
            (name, field) for name, field in object.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        from collections import defaultdict
        offset_groups = defaultdict(list)
        for name, field in fields:
            offset_groups[field.start_offset].append((name, field))
        filtered = []
        for offset, items in offset_groups.items():
            if len(items) > 1:
                items = [(n, f) for n, f in items if n != "d12_reserved"]
            filtered.extend(items)
        filtered.sort(key=lambda kv: kv[1].start_offset)
        for name, field in filtered:
            logger.info(
                f'Byte[{field.start_offset}:{field.end_offset}]: {name} = {field.value} (0x{field.value:X})',
                extra_dump=extra_dump
        )
    def get_and_print_open_vb_information(self) -> project_api.OpenVBInformation:
        rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        self.print_object_info_ai(open_vb_information)
        return open_vb_information   
        
    def polling_Read_Disturb_idle(self,vb:int) -> None:
        start_time = time.time()
        timeout_min = 5
        while 1:
            _, infofation = project_api.issue_40CB_to_get_total_Read_Count_and_Flush_RC_table_threshold(LogicalVB=vb)
            if infofation.IsScanTaskIdle.value == 1:
                break
            current_time = time.time()
            if (current_time - start_time) >= timeout_min * 60:
                    logger.error_lb('Polling Read Disturb done in 1 min')
                    logger.error_fp(f'Expect Read Disturb done in 1 min but not, current IsScanTaskIdle =  {infofation.IsScanTaskIdle.value}')
                    raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            time.sleep(1)
    def get_40C3_value(self, field_name:str) -> int:
        logger.flow(1, 'Issue VU 40C3 to get params of ftl status.')
        data = project_api.issue_40C3_to_get_params_of_ftl_status()
        val = int(getattr(data, field_name).value)
        logger.info(f'{field_name} = {val}')
        return val
    def check_value_exist(self,value:int,desc:str)->None:
        if value == 0xFFFFFFFF:
            logger.error(f'Expect {desc} != 0xFFFFFFFF, but not')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'{desc} val = {value}')
    def compare_value(self,value:int,expect_value:int, desc:str, method:VERIFY_METHOD=VERIFY_METHOD.EQUAL) -> None:
        if method == VERIFY_METHOD.EQUAL:
            if value != expect_value:
                logger.error(f'Expect {desc}={expect_value}, but = {value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        elif method == VERIFY_METHOD.NOT_EQUAL:
            if value == expect_value:
                logger.error(f'Expect {desc}!={expect_value}, but = {value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            if value <= expect_value:
                logger.error(f'Expect {desc} > 0, but = {value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'{desc} diff val = {value}')
    def verify_40C3_value(self,field_name:str,action:Callable[[], None], times:int, expected_delta:int,method:VERIFY_METHOD=VERIFY_METHOD.EQUAL) -> None:
        before = self.get_40C3_value(field_name)
        for i in range(times):
            action()
        after = self.get_40C3_value(field_name)
        self.compare_value(after - before, expected_delta, field_name, method)
        
    def unmap_data(self, lun:int, start_lba:int, len:int, total_len:int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            unmap = ExecuteCMD.Unmap()
            unmap.assign(lun=lun, lba=start_lba, length=len)
            ExecuteCMD.enqueue(unmap)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
    def post_process(self) -> None:
        pass
    def get_vb_ec_cnt(self, lun:int, lba:int) -> int:
        _, vu_pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=lba)
        vb_number = vu_pca.virtual_block_number.value
        rsp, data_payload = project_api.issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=project_api.VU4097Paremeter.GET_EC_TABLE)
        erase_cnt_from_vu = int.from_bytes(data_payload[vb_number*4 : (vb_number + 1)*4], 'little')
        logger.info(f'vb number = {vb_number}, ec = {erase_cnt_from_vu}')
        return erase_cnt_from_vu
    def clear_card(self) -> None:
        format_unit = ExecuteCMD.FormatUnit()
        format_unit.assign(lun=0, longlist=0, cmplist=0)
        ExecuteCMD.enqueue(format_unit)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
    def write_data(self, lun:int, start_lba:int, len:int, total_len:int) -> None:
        logger.info(f'lun = {lun}, start lba = {start_lba}, total len = {total_len}')
        while total_len > 0:
            len = min(total_len, len)
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=lun, lba=start_lba, length=len, fua=1)
            ExecuteCMD.enqueue(write10)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
    def config_lun(self,slc_au:int, tlc_au:int) -> tuple[int,int]:

        config_descs = api.get_config_descriptors(print=True)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xc
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
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = shared.param.gGeometry.l79_write_booster_buffer_max_n_alloc_units 
        for i in range(4):
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        ExecuteCMD.clear()

        unit_desc_idxes:List[int] = []
        for lun in range(0, self._param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()
        #test unit ready all enable lun
        for lun in range(self._param.gMaxNumberLU):
            if self._param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
        slc_lun = 0
        tlc_lun = 1
        return (slc_lun, tlc_lun)
    def pattern_get_device_health_descriptor(self) ->  bytearray:
        idn = api.DescriptorIDN.DEVICE_HEALTH
        index = 0x00
        selector = 0x00
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(api.QueryResponse, ExecuteCMD.read_response(cmd_index))
        ExecuteCMD.clear()
        return resp.data
    def check_value(self,field_name:str,expect_value:int, method:VERIFY_METHOD=VERIFY_METHOD.EQUAL) -> None:
        value = self.get_40C3_value(field_name)
        if method == VERIFY_METHOD.EQUAL:
            if value != expect_value:
                logger.error_lb(f'check {field_name} value')
                logger.error_fp(f'Expect {field_name}={expect_value}, but = {value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
        elif method == VERIFY_METHOD.NOT_EQUAL:
            if value == expect_value:
                logger.error_lb(f'check {field_name} value')
                logger.error_fp(f'Expect {field_name} != {expect_value}, but = {value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            if value <= expect_value:
                logger.error_lb(f'check {field_name} value')
                logger.error_fp(f'Expect {field_name} > {expect_value}, but = {value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def get_PCA_and_print(self,lun: int, lba: int) -> project_api.physical_address_info:
        _, pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=lba)
        vb = pca.virtual_block_number.value
        Die = pca.die.value
        Plane = pca.plane.value
        Block = pca.physical_block_number_w_BBT.value
        Page = pca.page.value
        logger.info(f'Lun{lun}, LBA = {lba}: VB = {vb}, PhyBlock = {Block}, CE = {Die}, Plane = {Plane}, Page = {Page}')
        return pca
    def read_data(self,lun:int, start_lba:int, len:int, total_len:int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(read10)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
    def read_LBA_repeatedly(self,lun:int, lba:int, read_times:int) -> None:
        for _ in range(read_times):
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=lun, lba=lba, length=1, fua=1)
            ExecuteCMD.enqueue(read10)
        ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
        return
    def inject_UECC(self,pca:project_api.physical_address_info, SLC_enable:bool = False) -> None:
        vb = pca.virtual_block_number.value
        Die = pca.die.value
        Plane = pca.plane.value
        Block = pca.physical_block_number_w_BBT.value
        Page = pca.page.value
        logger.info(f'Inject UECC: PhyBlock = {Block}, CE = {Die}, Plane = {Plane}, Page = {Page}, SLC_enable = {SLC_enable}')
        if SLC_enable:
            dire_write_payload = bytearray(DATA_SIZE_16K_BYTE)
        else:
            dire_write_payload = bytearray(DATA_SIZE_20K_BYTE*3)
        for i in range(len(dire_write_payload)):
            dire_write_payload[i] = 0xAA
        _ = project_api.issue_C060_to_write_raw_data(Ce=Die,Block=Block,Plane=Plane, Page=Page,SLC_Enable=SLC_enable,Ecc_Enable=1, datapayload=dire_write_payload)
        return
run = Pattern().run
if __name__ == "__main__":
    run()
