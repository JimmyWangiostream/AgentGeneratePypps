import random
from typing import List, Tuple, cast
import package_root
from Script import api
from Script import project_api
from Script.api.ufs_api.defines.bit_define import BIT10
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines.constant_define import *
from Script.api.exception import *
from Script.lib.sdk_lib.user.exception import DLL_RESPONSE_ERROR
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.project_api.custom_vu.lba_convert_vu.functions import issue_4052_to_get_logical_address
from Script.project_api.custom_vu.read_log.functions import issue_4080_read_log_from_nand
from Script.project_api.reh.functions import get_page_range_by_type
from Script.project_api.reh.structs import BLOCK_PAGE_TYPE, PAGE_TYPE, PAGE_TYPE_MAP
from Script.project_api.vth_sweep.functions import convert_page_to_page_order, issue_401D_to_get_vt_distribution
from Script.pattern.rain.mutual_fun import *

_sdk = api.shared.sdk

EVENT_LOG_TRANSFER_LENGTH = 0x4000
EVENT_LOG_HEADER_SIZE = 8
COMMON_INFO_OFFSET = EVENT_LOG_HEADER_SIZE
COMMON_INFO_SIZE = 1024
SYSTEM_STATUS_INFO_OFFSET = COMMON_INFO_OFFSET + COMMON_INFO_SIZE
SYSTEM_STATUS_INFO_SIZE = 512
HOST_SSR_INFO_OFFSET = SYSTEM_STATUS_INFO_OFFSET + SYSTEM_STATUS_INFO_SIZE
HOST_SSR_INFO_SIZE = 1024
SPECIFIC_LOG_INFO_OFFSET = HOST_SSR_INFO_OFFSET + HOST_SSR_INFO_SIZE

EVENT_BE_VT_LOG_ID = 0x6004
EVENT_VT_DIFF_COUNT_OFFSET = 28
EVENT_VT_DIFF_COUNT_SIZE = (0xDA * 4)

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.param = api.shared.param
        self.geometry_desc = api.get_geometry_descriptor()
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        self.fw_geometry = api.get_fw_geometry()
        self.total_au_size = int(self.geometry_desc.q4_total_raw_device_capacity / self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size)
        self.total_capacity_4K = int(self.geometry_desc.q4_total_raw_device_capacity/8)
        self.au_size = (self.total_au_size)//2
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.write_record = api.get_empty_write_record()
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.set_LUN_configuration()
        pass

    def step1(self) -> None:

        logger.flow(1, f'Issue C088 to stop refresh')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)

        lun = self.TestNormalLun
        length = 3*self.tlc_vb_size
        
        logger.flow(2, f'Sequence write data {length} blocks for LUN{lun}')
        api.sequential_write(lun=lun, start_lba=0, total_size=length, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        page_type_range = [ PAGE_TYPE.PAGE_SLC_LP, PAGE_TYPE.PAGE_MLC_LP, PAGE_TYPE.PAGE_TLC_LP]
        # page_type_range = [ PAGE_TYPE.PAGE_TLC_LP, PAGE_TYPE.PAGE_SLC_LP]
        for page_type in page_type_range:

            logger.flow(3, f'Issue 4080 to clear event log')
            self.clear_event_logs()
            baseline_count = self.get_event_log_count()
            logger.info(f'Event log count = {baseline_count}')

            isSLC = False
            
            lba = random.randint(0, length)

            logger.flow(4, f'Issue 4051 to get physical address')
            _, pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=lba)
            die = pca.die.value
            plane = pca.plane.value
            block = pca.virtual_block_number.value
            pca.offset.value = 0
            offset = pca.offset.value
            page = get_page_range_by_type(page_type)
            page_order = convert_page_to_page_order(page, isSLC)

            logger.info(f'4051 pca die= {die}, plane ={plane}, block={block}, page = {page}, offset = {offset}' )

            logger.info(f'Random select page = {page} for {page_type.label}' )

            logger.flow(5, f'Issue 4052 VUC to get LBA form PBA')
            _, la = issue_4052_to_get_logical_address(die, plane, block, page, offset)
            logger.info(f'page = {page}, offset = {pca.offset.value}, lun = {la.lun.value}, lba = {la.lba.value}')
            
            if not (la.lun.value == lun and la.lba.value >=0 and la.lba.value < length):
                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
            
            pca.page.value = page
            lba = la.lba.value
            wl, sb = self.get_wl_sb_number_by_page_on_TLC(page, page_type)
            
            logger.info(f'Lun{lun}, LBA = {lba}: CE = {die}, Plane = {plane}, wl ={wl}, PhyBlock = {block}, Page = {page}, offset = {offset}')

            logger.flow(6, f'Inject UECC for LUN{lun}, LBA{lba}')
            inject_UECC(pca, SLC_enable=False)

            logger.flow(7, f'Issue host read data for LUN{lun}, LBA{lba}')
            ExecuteCMD.Read10().assign(lun=lun, lba=lba, length=1, fua=1).enqueue()
            ExecuteCMD.send()
            
            logger.flow(8, f'Issue C060 to check UECC status for LBA{lba}')
            _ = direct_read_raw_data_and_check_status(pca=pca, SLC_enable=False, expect_status= project_api.ReadStatus.UECC, REH_Enable=True)

            vt_list:List[bytearray] = []

            # same failed WL and SB
            logger.flow(9, f'Get Vth dump on same failed WL{wl} and SB (1VT)')
            _, vt = issue_401D_to_get_vt_distribution(die, plane, block, page_order, isSLC, 0xFF, 0, 0xDA, 0)
            logger.info(f'dump vt{len(vt_list)}: wl={wl}, page_order={page_order}, page={page}')
            vt_list.append(vt)
            # remaining SBs on failed WL
            logger.flow(10, f'Collect Vth dump for the remaining SBs on the failed WL{wl} (3VTs)')
            for s in range(4):
                if s != sb:
                    new_page = self.get_page_number_by_wl_on_TLC(wl, s)
                    new_page_order = convert_page_to_page_order(new_page, isSLC)
                    _, vt = issue_401D_to_get_vt_distribution(die, plane, block, new_page_order, isSLC, 0xFF, 0, 0xDA, 0)
                    logger.info(f'dump vt{len(vt_list)}: wl={wl}, page_order={new_page_order}, page={new_page}')
                    vt_list.append(vt)
            # failed WL -1
            logger.flow(11, f'Collect Vth dump on the failed WL{wl}-1 and same plane, include the failed SB and the next ones')
            if wl >0 :
                s = sb
                while s < 4:
                    new_page = self.get_page_number_by_wl_on_TLC(wl-1, s)
                    new_page_order = convert_page_to_page_order(new_page, isSLC)
                    _, vt = issue_401D_to_get_vt_distribution(die, plane, block, new_page_order, isSLC, 0xFF, 0, 0xDA, 0)
                    logger.info(f'dump vt{len(vt_list)}: wl={wl-1}, page_order={new_page_order}, page={new_page}')
                    vt_list.append(vt)
                    s +=1
            # failed WL +1
            logger.flow(12, f'Collect Vth dump on the failed WL{wl}+1 and same plane, include the failed SB and the previous ones')
            if wl < 277:
                s = 0
                while s <= sb:
                    new_page = self.get_page_number_by_wl_on_TLC(wl+1, s)
                    new_page_order = convert_page_to_page_order(new_page, isSLC)
                    _, vt = issue_401D_to_get_vt_distribution(die, plane, block, new_page_order, isSLC, 0xFF, 0, 0xDA, 0)
                    logger.info(f'dump vt{len(vt_list)}: wl={wl+1}, page_order={new_page_order}, page={new_page}')
                    vt_list.append(vt)
                    s +=1
            # same failed WL and SB, remaining planes
            logger.flow(13, f'Collect Vth dump for the remaining planes on same failed WL{wl} and SB (5VTs)')
            for p in range(self.flash_setting.Plane_Per_Die):
                if p != plane:
                    _, vt = issue_401D_to_get_vt_distribution(die, p, block, page_order, isSLC, 0xFF, 0, 0xDA, 0)
                    logger.info(f'dump vt{len(vt_list)}: wl={wl}, page_order={page_order}, page={page}, plane={p}')
                    vt_list.append(vt)

            logger.flow(14, f"Issue 4080 to find event log VT with log id = 0x{EVENT_BE_VT_LOG_ID:04X}")
            current_count = self.wait_for_event_log_count_increase(baseline_count)
            if current_count > 0:
                event_vt_dict = self.find_event_log(EVENT_BE_VT_LOG_ID, current_count)

            logger.flow(15, f"Compare VT diff count from VU 401D with the one from the event log")
            if len(event_vt_dict) > 0:
                self.compare_VT_diff_count(vt_list, event_vt_dict)
            else:
                logger.error_fp(f'Expected the event log VT count to be greater than zero , but the check failed')
                raise SIGHTING_RESPONSE_UNEXPECTED
            
        logger.flow(16,"Issue C088 to start refresh execution")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)

        pass

    def set_LUN_configuration(self) -> None:
        config_desc = api.get_config_descriptors(print = True)
        lun_num_per_desc = 8
        
        for index in range(int(self.max_number_lu/lun_num_per_desc)):
            config_desc[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            config_desc[index].header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
            for unit in range(lun_num_per_desc):
                config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.DISABLE
                config_desc[index].units[unit].l4_num_alloc_units = 0
                config_desc[index].units[unit].b9_logical_block_size = 0
                if index == 0 and unit == self.TestNormalLun: # LUN 0
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = self.au_size
                    config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index ==0 and unit == self.TestEM1Lun :# LUN1
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_desc[index].units[unit].l4_num_alloc_units = self.au_size if self.au_size < self.geometry_desc.l44_enhanced1_max_n_alloc_u else self.geometry_desc.l44_enhanced1_max_n_alloc_u
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
            
            push_write_config(config_desc[index], index=index)

        ExecuteCMD.send()

        self.update_unit_desc()
        self.update_device_desc()

        test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                test_unit_ready.set_option(lun=lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send()

        pass

    def update_unit_desc(self) -> None:
        unit_desc_idxes:List[int] = []
        for lun in range(self.param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

    def update_device_desc(self) -> None:
        device_descriptor = ExecuteCMD.ReadDescriptor()
        device_descriptor.assign(idn=api.DescriptorIDN.DEVICE)
        index = ExecuteCMD.enqueue(device_descriptor)
        ExecuteCMD.send(clear_on_success=False)
        api.update_descriptor(idn=api.DescriptorIDN.DEVICE, index=0, response=cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

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
            dire_write_payload = bytearray(DATA_SIZE_16K_BYTE*3)
        for i in range(len(dire_write_payload)):
            dire_write_payload[i] = 0xAA
        _ = project_api.issue_C060_to_write_raw_data(Ce=Die,Block=Block,Plane=Plane, Page=Page,SLC_Enable=SLC_enable,Ecc_Enable=1, datapayload=dire_write_payload)
        pass

    def read_data(self,lun:int, start_lba:int, len:int, total_len:int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(read10)
            start_lba += len
            total_len -= len

        ExecuteCMD.send()
    
    def get_wl_sb_number_by_page_on_TLC(self, page:int, page_type:int) -> Tuple[int, int]:
        logical_page_base   = [0, 1620, 1652, 3308]
        logical_page_size   = [1620, 32, 1656, 4]
        wl_base             = [0, 135, 139, 277]
        wl_size             = [135, 4, 138, 1] #有些 plane 的最後一個 page 是存 bitmap parity 不會轉 LBA
        wl = 0
        sb = 0
        if page_type == PAGE_TYPE.PAGE_SLC_LP :
            shared_page_num = 1
            wl_page_num = shared_page_num * 4
            if page >= logical_page_base[3] and  page < logical_page_base[3]+logical_page_size[3]:
                region =3
            else:
                logger.error(f'unexpected page value - page type ={page_type}, page = {page}')
                raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        elif page_type == PAGE_TYPE.PAGE_MLC_LP or page_type == PAGE_TYPE.PAGE_MLC_UP:
            shared_page_num = 2
            wl_page_num = shared_page_num * 4
            if page >= logical_page_base[1] and  page < logical_page_base[1]+logical_page_size[1]:
                region = 1
            else:
                logger.error(f'unexpected page value - page type ={page_type}, page = {page}')
                raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        elif page_type == PAGE_TYPE.PAGE_TLC_LP or page_type == PAGE_TYPE.PAGE_TLC_UP or page_type == PAGE_TYPE.PAGE_TLC_XP:
            shared_page_num = 3
            wl_page_num = shared_page_num * 4
            if page >= logical_page_base[0] and  page < logical_page_base[0]+logical_page_size[0]:
                region = 0
            elif page >= logical_page_base[2] and  page < logical_page_base[2]+logical_page_size[2]:
                region = 2
            else:
                logger.error(f'unexpected page value - page type ={page_type}, page = {page}')
                raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        else:
            logger.error(f'unexpected value - page type ={page_type}')
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        
        wl = wl_base[region] + (page - logical_page_base[region])//wl_page_num
        sb = int(((page - logical_page_base[region])/shared_page_num) % 4)
        return wl, sb
    
    def get_page_number_by_wl_on_TLC(self, wl:int, sb:int)-> int:
        logical_page_base   = [0, 1620, 1652, 3308]
        logical_page_size   = [1620, 32, 1656, 4]
        wl_base             = [0, 135, 139, 277]
        wl_size             = [135, 4, 138, 1] #有些 plane 的最後一個 page 是存 bitmap parity 不會轉 LBA

        if wl == wl_base[3]: #SLC
            index = 3
            shared_page_num = 1
            lmu = 0
        elif wl >= wl_base[1] and wl < wl_base[1]+wl_size[1]: # MLC 
            index = 1
            shared_page_num = 2
            lmu = 0
        elif wl >= wl_base[0] and wl < wl_base[0]+wl_size[0]: #TLC
            index = 0
            shared_page_num = 3
            lmu = 0
        elif wl >= wl_base[2] and wl < wl_base[2]+wl_size[2]: #TLC
            index = 2
            shared_page_num = 3
            lmu = 0

        page = logical_page_base[index] + ((wl-wl_base[index])*4*shared_page_num) +sb * shared_page_num+ lmu
        return page
    
    def get_event_log_count(self) -> int:
        _, output = issue_4080_read_log_from_nand(
            para_0=0,
            para_1=0,
            para_2=0,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )
        count = int.from_bytes(output[0:4], byteorder="little")
        logger.info(f"event log count = {count}")
        return count

    def clear_event_logs(self) -> None:
        issue_4080_read_log_from_nand(
            para_0=0,
            para_1=0xFFFFFFFF,
            para_2=0,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )

    def read_event_log_by_index(self, event_index: int) -> bytearray:
        _, output = issue_4080_read_log_from_nand(
            para_0=0,
            para_1=1,
            para_2=event_index,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )
        return output

    def wait_for_event_log_count_increase(
        self,
        baseline_count: int,
        retry_count: int = 10,
        sleep_sec: float = 1.0,
    ) -> int:
        for retry in range(retry_count):
            current_count = self.get_event_log_count()
            if current_count > baseline_count:
                return current_count
            logger.info(f"Event log is not ready yet, retry = {retry + 1}/{retry_count}")
            time.sleep(sleep_sec)
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION(f"Event log count did not increase from baseline count {baseline_count}")
    
    def find_event_log(self, find_log_id: int,count: int) -> Dict[int, bytearray]:
        vt_diff_dict : Dict[int, bytearray] = {}
        i = 0
        for idx in range(count):
            output = self.read_event_log_by_index(idx)
            log_index = int.from_bytes(output[0: 4], byteorder="little")
            log_id = int.from_bytes(output[SPECIFIC_LOG_INFO_OFFSET: SPECIFIC_LOG_INFO_OFFSET+4], byteorder="little")
            logger.info(f"Read event index = {log_index} and log id= 0x{log_id:04X}")
            if log_id == find_log_id:
                offset = SPECIFIC_LOG_INFO_OFFSET+EVENT_VT_DIFF_COUNT_OFFSET
                vt_diff_dict[i] = bytearray(output[offset: offset + EVENT_VT_DIFF_COUNT_SIZE])
                i+=1
        return vt_diff_dict
    
    def compare_VT_diff_count(self, vt_list:List[bytearray], event_vt_dict:Dict[int, bytearray])->None:
        for i in range(len(vt_list)):
            vt = self.covert_vt_to_diff_list(vt_list[i])
            event_vt = self.covert_bytearray_to_list(event_vt_dict[i])
            logger.info(f'401D dump vt len = {len(vt)}, event log vt len = {len(event_vt)}')
            if vt != event_vt :
                logger.info(f'VT{i} diff count from VU 401D = {vt}')
                logger.info(f'VT{i} diff count from event log = {event_vt}')
                logger.error_lb('Compare VT diff count from VU 401D with the one from the event log')
                logger.error_fp(f'Expected VT diff count from VU 401D to equal the count from event log in VT{i}, but the comparison failed')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def covert_bytearray_to_list(self, b:bytearray)->List[int]:
        int_list = []
        for i in range(0, len(b), 4):
            value = int.from_bytes(b[i:i+4], byteorder='little')
            int_list.append(value)
        return int_list

    def covert_vt_to_diff_list(self, vt: bytearray)-> List[int]:
        int_list = self.covert_bytearray_to_list(vt)

        diff_list = []
        for i in range(1, 0xDA+1):
            diff = int_list[i] - int_list[i-1]
            diff_list.append(diff)

        return diff_list

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()