import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.refresh.mutual_fun import get_VB_group
from Script.project_api.custom_vu.media_scan_vu.structs import *
from Script.pattern.apl_system_rebuild.mutual_fun import *
from Script.project_api.refresh_vu.define import VUC087VB_type

test_blk_type = [
    project_api.VB_GROUP.CURRENT_L2_MLC.value,
    project_api.VB_GROUP.CURRENT_L1.value,
    project_api.VB_GROUP.CURRENT_L2_SLC.value,
    project_api.VB_GROUP.CURRENT_PTE.value,
    project_api.VB_GROUP.LOG_TAB_BLK.value,
    #project_api.VB_GROUP.RAIN_SWAP_NO_OBR_SLC_L2_SLC.value,
    #project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_SLC.value,
    #project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_TLC.value,
    #-------------------------------------------------------- 
    project_api.VB_GROUP.USED_BLK_POOL_MLC.value,
    project_api.VB_GROUP.USED_BLK_POOL_SLC.value
]

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.write_record = api.get_empty_write_record()
        self.flash_setting = api.get_flash_setting()
        self.fw_geometry = api.get_fw_geometry()
        self.geometry_desc = api.get_geometry_descriptor()
        self.max_ce = self.flash_setting.Max_Fdevice
        self.max_plane = self.flash_setting.Plane_Per_Die
        pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        self.TLC_WL_block = pageline_block * 4 * 3
        self.SLC_WL_block = pageline_block * 4
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.Total_AU_Count = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size)
        self.vb_type=VUC087VB_type.HostVB
        pass

    def step1(self) -> None:

#=================================================================================================
        #aleardy booking refreshQ should skip scan (after init)
#=================================================================================================

        for blk_type in test_blk_type:

            logger.flow(1, 'vuC08B disable media scan')
            response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

            logger.flow(2, f'config lun and create {project_api.VB_GROUP(blk_type).name} blk ')
            self.config_lun_and_create_target_blk(blk_type)

            target_vb = self.get_target_vb_list(blk_type)
            ftl_vb_list_data_before = get_VB_group()
            if project_api.VB_GROUP(ftl_vb_list_data_before[target_vb]["group"]) != blk_type:
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(3, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
            project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)

            logger.flow(4, f'issue C087 to enqueue as High Priority refresh')
            project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=self.vb_type, VB_list=[target_vb], booking_user=project_api.VUC087Paremeter.HighPriority)

            logger.flow(5, f'issue 40C5 to check if the Booking Queue is correct')
            _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
            if booking_q_before.LogicalVBNumberInBookingQueue.value != 1:
                logger.error_lb(f'check LogicalVBNumberInBookingQueue after C087')
                logger.error_fp(f'expect LogicalVBNumberInBookingQueue is 1, but current value = {booking_q_before.LogicalVBNumberInBookingQueue.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if (booking_q_before.BookingQueueVB[0].value & project_api.BookingUser.VU_REFRESH != project_api.BookingUser.VU_REFRESH) or \
                (booking_q_before.BookingQueueVB[0].value & project_api.BookingUser.BOOKING_IN_HP != project_api.BookingUser.BOOKING_IN_HP):
                logger.error_lb(f'check BookingQueueVB after C087')
                logger.error_fp(f'expect BookingQueueVB[0] is VU_REFRESH and BOOKING_IN_MP, but current value = {booking_q_before.BookingQueueVB[0].value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            for idx, vb in enumerate(booking_q_before.BookingQueueVB):
                logger.info(f'BookingQ[{idx}]: VB {vb.LogicalVBNumber.value}')
                if vb.LogicalVBNumber.value != target_vb:
                    logger.error(f'BookingQ_VB not vb{target_vb}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(6, f'enable media scan')
            response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

            logger.flow(7, f'idle trigger media scan')
            spend_time_set = 0x1000000
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = spend_time_set
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)
            
            while 1:
                time.sleep(5)

                resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
                scan_vb = payload.cur_scan_vb.value
                scan_page = payload.cur_scan_page.value
                scan_group = payload.scan_group.value
                logger.info(f'scan_vb={scan_vb}, scan_page={scan_page}, scan_group={scan_group}')
                if scan_vb == 0xFFFFFFFF and scan_page == 0xFFFFFFFF:
                    logger.flow(8, f'check target vb should skip scan')
                    ftl_vb_list_data = get_VB_group()
                    for scanned_vb in payload.scanned_blocks:
                        group_idx=ftl_vb_list_data[scanned_vb]["group"]
                        logger.info('scan_vb=%d, group_idx=%d', scanned_vb, group_idx)
                        if scanned_vb == target_vb:
                            logger.error(f'target vb={target_vb} should skip scan')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    break

        pass

    def post_process(self) -> None:
        pass

    def get_target_vb_list(self, group:int)-> int:
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
            return vb_list[0]

    def config_lun_and_create_target_blk(self, target_blk:int=0)->None:

        self.config_lun()

        if target_blk == project_api.VB_GROUP.CURRENT_L2_MLC.value:
            logger.info('create CURRENT_L2_MLC')
            api.sequential_write(lun=0, start_lba=0, total_size=self.TLC_WL_block, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            self.vb_type=project_api.VUC087VB_type.HostVB
            
        elif target_blk == project_api.VB_GROUP.CURRENT_L1.value:
            logger.info('create CURRENT_L1')
            api.sequential_write(lun=0, start_lba=0, total_size=BLOCK4K_SIZE_16K_BYTE, chunk_size=BLOCK4K_SIZE_16K_BYTE, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)            
            self.vb_type=project_api.VUC087VB_type.HostVB

        elif target_blk == project_api.VB_GROUP.CURRENT_L2_SLC.value:
            logger.info('create CURRENT_L2_SLC')
            api.sequential_write(lun=1, start_lba=0, total_size=self.SLC_WL_block, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            self.vb_type=project_api.VUC087VB_type.HostVB

        elif target_blk == project_api.VB_GROUP.CURRENT_PTE.value:
            logger.info('create CURRENT_PTE')
            #4096 node才會flush pte
            api.sequential_write(lun=0, start_lba=0, total_size=4096, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)            
            self.vb_type=project_api.VUC087VB_type.TableVB
        
        elif target_blk == project_api.VB_GROUP.LOG_TAB_BLK.value:
            logger.info('create LOG_TAB_BLK')
            api.sequential_write(lun=0, start_lba=0, total_size=BLOCK4K_SIZE_12M_BYTE, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)            
            self.vb_type=project_api.VUC087VB_type.TableVB

        elif target_blk == project_api.VB_GROUP.RAIN_SWAP_NO_OBR_SLC_L2_SLC.value:
            logger.info('create RAIN_SWAP_NO_OBR_SLC_L2_SLC')
            api.sequential_write(lun=1, start_lba=0, total_size=self.SLC_WL_block, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)            
            self.vb_type=project_api.VUC087VB_type.TableVB
        
        elif target_blk == project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_SLC.value:
            logger.info('create RAIN_SWAP_NO_OBR_TLC_L2_SLC')
            api.sequential_write(lun=0, start_lba=0, total_size=self.TLC_WL_block, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)            
            self.vb_type=project_api.VUC087VB_type.TableVB

        elif target_blk == project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_TLC.value:
            logger.info('create RAIN_SWAP_NO_OBR_TLC_L2_TLC')
            api.sequential_write(lun=0, start_lba=0, total_size=self.TLC_WL_block, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)            
            self.vb_type=project_api.VUC087VB_type.TableVB
        
        elif target_blk == project_api.VB_GROUP.USED_BLK_POOL_MLC.value:
            logger.info('create USED_BLK_POOL_MLC')
            api.sequential_write(lun=0, start_lba=0, total_size=2*self.tlc_vb_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            self.vb_type=project_api.VUC087VB_type.HostVB

        elif target_blk == project_api.VB_GROUP.USED_BLK_POOL_SLC.value:
            logger.info('create USED_BLK_POOL_SLC')
            api.sequential_write(lun=1, start_lba=0, total_size=2*self.slc_vb_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            self.vb_type=project_api.VUC087VB_type.HostVB

        pass

    def config_lun(self) -> None:
        selector = 0x00
        length = 0xE6
        Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
        EM1_total_AU = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, Total_AU_Count//2)
        normal_total_AU = Total_AU_Count//2
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
                if lun ==0:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                    desc.units[unit_idx].l4_num_alloc_units = normal_total_AU
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif lun==1:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = EM1_total_AU
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