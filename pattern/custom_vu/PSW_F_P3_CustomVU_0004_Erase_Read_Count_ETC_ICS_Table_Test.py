import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
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
from typing import Any

ENG2_WA = True

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        _, self.debug_info = api.get_debug_info()
        dumpfile('debug_info.bin', self.debug_info.payload)
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestWBLun = 2
        self.config_lun(normal_list=[self.TestNormalLun, self.TestWBLun], em1_list=[self.TestEM1Lun])
        self.write_record = api.get_empty_write_record()
        pass
    
    def step1(self) -> None:
        logger.flow(1, 'check Index 0: get EC table. (extract valid erase count for each physical VB)')
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        self.erase_cnt_of_vb, self.erase_cnt_for_hidden_physical_block, _ = project_api.get_all_VB_erase_count()
        _, erase_cnt_buffer = api.read_Xmemory(sram_address=self.debug_info.VB_list_cycle_address.value)
                
        for vb in range(self.fw_geometry.l52_total_vb_count):
            erase_cnt = int.from_bytes(erase_cnt_buffer[vb*4 : (vb+1)*4], 'little')
            if self.erase_cnt_of_vb[vb] != erase_cnt:
                dumpfile('erase_cnt_buffer_from_SRAM.bin', erase_cnt_buffer)
                logger.error_lb(f'check erase cnt of VB{vb}')
                logger.error_fp(f'expect EC from SRAM equal to MicronVU, but SRAM value = {erase_cnt}, MicronVU value = {self.erase_cnt_of_vb[vb]}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        for idx in range(len(self.erase_cnt_for_hidden_physical_block)):
            hidden_blk_ec = int.from_bytes(self.flash_setting_buffer[2284 + idx*4 : 2284 + (idx+1)*4], 'little')
            if self.erase_cnt_for_hidden_physical_block[idx] != hidden_blk_ec:
                dumpfile('self.flash_setting_buffer.bin', erase_cnt_buffer)
                logger.error_lb(f'check erase cnt of hidden_block{idx}')
                logger.error_fp(f'expect hidden block EC from FlashSetting equal to MicronVU, but FlashSetting value = {hidden_blk_ec}, MicronVU value = {self.erase_cnt_for_hidden_physical_block[idx]}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    def step2(self) -> None:
        logger.flow(2, 'check Index 1: get RC table (raw data). Return RAM content where RC table is stored')
        logger.info('ENG1 not support, skip this flow')
        pass
    def step3(self) -> None:
        logger.flow(3, 'check Index 2: get L2P VB table (raw data). Return RAM content where physical VB table is stored.')
        self.physical_block_index_of_vb = project_api.get_VB_to_PB_mapping()
        _, all_remap_table = api.get_remap_table()
        for vb in range(self.fw_geometry.l52_total_vb_count):
            remap_vb = int.from_bytes(all_remap_table[vb*2 : (vb+1)*2], 'little')
            if self.physical_block_index_of_vb[vb] != remap_vb:
                dumpfile('all_remap_table.bin', all_remap_table)
                logger.error_lb(f'check VB to PB mapping of VB{vb}')
                logger.error_fp(f'expect remap from SRAM equal to MicronVU, but SRAM value = {remap_vb}, MicronVU value = {self.physical_block_index_of_vb[vb]}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    def step4(self) -> None:
        logger.flow(4, 'check Index 3: get CIS VB table (raw data). Return RAM content where CIS table is stored')
        self.fw_code_physical_address = project_api.get_FW_code_physical_address_information()
        CIS_Block1 = {
            'Channel': 0,
            'CE': self.flash_setting_buffer[52],
            'Plane': self.flash_setting_buffer[32],
            'Block': self.flash_setting_buffer[30] << 8 | self.flash_setting_buffer[31],
            'Page': 0
        }
        CIS_Block2 = {
            'Channel': 0,
            'CE': self.flash_setting_buffer[53],
            'Plane': self.flash_setting_buffer[54],
            'Block': self.flash_setting_buffer[33] << 8 | self.flash_setting_buffer[34],
            'Page': 0
        }
        self.check_CIS_code(self.fw_code_physical_address.CISCode1, CIS_Block1, 'CIS_Block1')
        self.check_CIS_code(self.fw_code_physical_address.CISCode2, CIS_Block2, 'CIS_Block2')
        valid_plane_bitmap = api.read_fw_value("gwFwTmpCodeVbPlnBitmap")
        if self.fw_code_physical_address.TempCodeValidPlaneBitmap.value != valid_plane_bitmap:
            logger.error_lb(f'check TempCodeValidPlaneBitmap ')
            logger.error_fp(f'expect fw_value gwFwTmpCodeVbPlnBitmap equal to MicronVU, but fw value = {valid_plane_bitmap}, MicronVU value = {self.fw_code_physical_address.TempCodeValidPlaneBitmap.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        for i in range(12):
            gaFwTmpCodeBlkPackAddr = api.read_fw_value(f"gaFwTmpCodeBlkPackAddr[{i}]")
            TempCodePhysicalAddress = int.from_bytes(self.fw_code_physical_address.TempCodePhysicalAddress[i].payload, 'little')
            if TempCodePhysicalAddress != gaFwTmpCodeBlkPackAddr:
                logger.error_lb(f'check TempCodePhysicalAddress[{i}] ')
                logger.error_fp(f'expect fw_value gaFwTmpCodeBlkPackAddr equal to MicronVU, but fw value = {gaFwTmpCodeBlkPackAddr}, MicronVU value = {TempCodePhysicalAddress}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    def step5(self) -> None:
        logger.flow(5, 'check Index 5: get System all sub VB versions')
        logger.info('ENG1 not support, skip this flow')
        pass
    def step6(self) -> None:
        logger.flow(6, 'check Index 6: get BBT sub VB info')
        self.bbt_sub_vb_info = project_api.get_BBT_physical_block_information()
        bbt_pca, _ = self.find_bbt_block()
        bbt_block = bbt_pca.b11_block_h << 8 | bbt_pca.b10_block_l
        if self.bbt_sub_vb_info.Sub_VB_version.value != bbt_block:
            logger.error_lb(f'check Current_BBT Sub_VB_version')
            logger.error_fp(f'expect finded BBT Sub_VB_version equal to MicronVU, but finded value = {bbt_block}, MicronVU value = {self.bbt_sub_vb_info.Sub_VB_version.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.bbt_sub_vb_info.First_empty_page.value != 9:
            logger.error_lb(f'check Current_BBT First_empty_page')
            logger.error_fp(f'expect finded BBT First_empty_page equal to MicronVU, but finded value = {9}, MicronVU value = {self.bbt_sub_vb_info.First_empty_page.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.bbt_sub_vb_info.BBT_block_count.value != 1:
            logger.error_lb(f'check Current_BBT BBT_block_count')
            logger.error_fp(f'expect finded BBT BBT_block_count equal to MicronVU, but finded value = {1}, MicronVU value = {self.bbt_sub_vb_info.BBT_block_count.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.bbt_sub_vb_info.Block.value != bbt_block:
            logger.error_lb(f'check Current_BBT Block')
            logger.error_fp(f'expect finded BBT Block equal to MicronVU, but finded value = {bbt_block}, MicronVU value = {self.bbt_sub_vb_info.Block.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.bbt_sub_vb_info.CE.value != bbt_pca.b5_ce:
            logger.error_lb(f'check Current_BBT CE')
            logger.error_fp(f'expect finded BBT CE equal to MicronVU, but finded value = {bbt_pca.b5_ce}, MicronVU value = {self.bbt_sub_vb_info.CE.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.bbt_sub_vb_info.plane.value != bbt_pca.b6_plane:
            logger.error_lb(f'check Current_BBT plane')
            logger.error_fp(f'expect finded BBT plane equal to MicronVU, but finded value = {bbt_pca.b6_plane}, MicronVU value = {self.bbt_sub_vb_info.plane.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    def step7(self) -> None:
        logger.flow(7, 'check Index 7: get EC table (raw data). Return RAM content where EC table is stored')
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=int(self.tlc_vb_size*2.5), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=int(self.slc_vb_size*2.5), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.sequential_write(lun=self.TestWBLun, start_lba=0, total_size=int(self.slc_vb_size*2.5), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)        
        pointer = project_api.get_PT_physical_block_information()
        all_vb_type = project_api.get_all_VB_type()
        self.ftl_vb_list_data = self.get_VB_group(show=False)
        for vb, info in self.ftl_vb_list_data.items():
            group = project_api.VB_GROUP(info['group'])
            access_mode = info['access_mode']
            temp = copy.deepcopy(all_vb_type[vb])
            # temp = project_api.VBTypeInfo(bytearray(4))
            temp.VB_index.value = vb
            if group in [project_api.VB_GROUP.RAIN_SWAP_NO_OBR_BLK,
                        project_api.VB_GROUP.RAIN_SWAP_TLC_CURSOR_BLK,
                        project_api.VB_GROUP.RAIN_SWAP_NO_OBR_SLC_L2_SLC,
                        project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_SLC,
                        project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_TLC]:
                temp.VB_IS_RAIN_SWAP.value = 1
            if group in [project_api.VB_GROUP.PTE_POOL,
                        project_api.VB_GROUP.CURRENT_PTE]:
                temp.VB_IS_PTE.value = 1
            if vb == self.bbt_sub_vb_info.Block.value:
                temp.VB_IS_BBT.value = 1
            if vb == pointer.logicalvb.value:
                temp.VB_IS_Pointer.value = 1
                
            if group in [project_api.VB_GROUP.LIST_BLK,
                            project_api.VB_GROUP.TMP_CODE_BLK,
                            project_api.VB_GROUP.CURRENT_PTE,
                            project_api.VB_GROUP.LOG_TAB_BLK,
                            project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_TLC,
                            project_api.VB_GROUP.RAIN_SWAP_NO_OBR_BLK,
                            project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_SLC,
                            project_api.VB_GROUP.RAIN_SWAP_NO_OBR_SLC_L2_SLC,
                            project_api.VB_GROUP.DRVLOG_BLK,
                            project_api.VB_GROUP.LIST_INDEX_BLK]:
                temp.VB_type.value = 16
            if group in [project_api.VB_GROUP.REVOKE_BLK,
                        project_api.VB_GROUP.HIDDEN_BLK_USE,
                        project_api.VB_GROUP.CURRENT_L1]:
                temp.VB_type.value = 20
            if group in [project_api.VB_GROUP.CURRENT_L2_SLC]:
                temp.VB_type.value = 14
            if group in [project_api.VB_GROUP.CURRENT_L2_MLC]:
                if access_mode:
                    temp.VB_type.value = 20
                else:
                    temp.VB_type.value = 11
            if group in [project_api.VB_GROUP.USED_BLK_POOL_SLC]:
                temp.VB_type.value = 1
            if group in [project_api.VB_GROUP.USED_BLK_POOL_MLC]:
                if access_mode:
                    temp.VB_type.value = 3
                else:
                    temp.VB_type.value = 2
            if group in [project_api.VB_GROUP.FREE_BLK_QUEUE_SLC]:
                temp.VB_type.value = 6
            if group in [project_api.VB_GROUP.FREE_BLK_QUEUE_TABLE]:
                temp.VB_type.value = 15
            if group in [project_api.VB_GROUP.FREE_BLK_QUEUE_MLC]:
                temp.VB_type.value = 0
            self.compare_VB_type_criteria(raw_value=all_vb_type[vb], expect_value=temp, VB=vb)
            pass
        pass
    def step8(self) -> None:
        logger.flow(8, 'check Index 9: ICS bad block')
        self.ics_bad_block = project_api.get_ics_bad_block()
        for vb in range(self.fw_geometry.l52_total_vb_count):
            if self.ics_bad_block.ICSBadBlocks[vb].VB_index.value != vb:
                logger.error_lb(f'check VB index of ICSBadBlocks')
                logger.error_fp(f'expect VB index arrange in order, please check dump data, expect value = {vb}, MicronVU value = {self.ics_bad_block.ICSBadBlocks[vb].VB_index.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL            
        rsp, ics_table_payload = api.get_ics_table()
        for idx in range(self.fw_geometry.l52_total_vb_count):
            ics = api.ICSUnit(ics_table_payload, idx*4, (idx+1)*4 -1)
            if ics.ICS_block_index.value == 0xFFFF:
                break
            vb = ics.ICS_block_index.value
            if self.ics_bad_block.ICSBadBlocks[vb].invalid_VB_plane.value != ics.Invalid_logical_plane.value:
                dumpfile('ics_table.bin', ics_table_payload)
                logger.error_lb(f'check invalid_VB_plane of VB{vb}')
                logger.error_fp(f'expect ICS table invalid_VB_plane equal to MicronVU, but finded value = {ics.Invalid_logical_plane.value}, MicronVU value = {self.ics_bad_block.ICSBadBlocks[vb].invalid_VB_plane.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    def step9(self) -> None:
        logger.flow(9, 'check Index 10: get Version (input param: logic VB number; output param: VB version)')
        logger.info('ENG1 not support, skip this flow')
        pass
    def step10(self) -> None:
        logger.flow(10, 'check Index 14: get PTE region number (from PTE cache)')
        logger.info('ENG1 not support, skip this flow')
        pass
    def step11(self) -> None:
        logger.flow(11, 'check Index 15: get EC TLC table (raw data). Return RAM content where EC TLC table is stored.  (If exists otherwise it is equal to #7 option)')
        logger.info('ENG1 not support, skip this flow')
        pass

    def post_process(self) -> None:
        pass
    
    def find_bbt_block(self) -> tuple[api.PCA, bytearray]:
        direc_read_pca = PCA()
        for block in range(self.fw_geometry.l52_total_vb_count):
            for ce in range(self.flash_setting.Max_Fdevice):
                for plane in range(self.flash_setting.Plane_Per_Die):
                    direc_read_pca.l0_op = 0x20000
                    direc_read_pca.b4_mode = 1 #SLC
                    direc_read_pca.b5_ce = ce
                    direc_read_pca.b6_plane = plane
                    direc_read_pca.b11_block_h = (block>>8) & 0xFF
                    direc_read_pca.b10_block_l = block & 0xFF
                    direc_read_pca.l12_fpage = 0
                    dire_read_payload = api.direct_read(pca=direc_read_pca, block_count=4, include_FW_spare=True)
                    logger.info(f'Block = {(direc_read_pca.b11_block_h<<8) | (direc_read_pca.b10_block_l)}, mode = {direc_read_pca.b4_mode}, CE = {direc_read_pca.b5_ce}, Plane = {direc_read_pca.b6_plane}, fPage = {direc_read_pca.l12_fpage}({direc_read_pca.l12_fpage>>5}<<5), lmu = {direc_read_pca.b20_lmu}, FW_Sapre = {dire_read_payload[api.DATA_SIZE_4K_BYTE*4 + 4]}')
                    if dire_read_payload[api.DATA_SIZE_4K_BYTE*4 + 4] == 0x8B:
                        return direc_read_pca, dire_read_payload
                    if block>=20:
                        logger.error_lb(f'issue direct read to find BBT block')
                        logger.error_fp(f'expect BBT block < 20, but current block = {block}, result Fail!')
                        raise SIGHTING_PBA_UNEXPECTED
        return direc_read_pca, bytearray(0)
        

    def check_CIS_code(self, CISCode:project_api.CISCode, CISBlock:Dict[str, int], string:str) -> None:
        Channel = CISBlock.get('Channel', 0)
        CE = CISBlock.get('CE', 0)
        Plane = CISBlock.get('Plane', 0)
        Block = CISBlock.get('Block', 0)
        Page = CISBlock.get('Page', 0)
        if CISCode.Channel.value != Channel:
            logger.error_lb(f'check {string} physical address')
            logger.error_fp(f'expect Channel from FlashSetting equal to MicronVU, but FlashSetting value = {Channel}, MicronVU value = {CISCode.Channel.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if CISCode.CE.value != CE:
            logger.error_lb(f'check {string} physical address')
            logger.error_fp(f'expect CE from FlashSetting equal to MicronVU, but FlashSetting value = {CE}, MicronVU value = {CISCode.CE.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if CISCode.Plane.value != Plane:
            logger.error_lb(f'check {string} physical address')
            logger.error_fp(f'expect Plane from FlashSetting equal to MicronVU, but FlashSetting value = {Plane}, MicronVU value = {CISCode.Plane.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if CISCode.Block.value != Block:
            logger.error_lb(f'check {string} physical address')
            logger.error_fp(f'expect Block from FlashSetting equal to MicronVU, but FlashSetting value = {Block}, MicronVU value = {CISCode.Block.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if CISCode.Page.value != Page:
            logger.error_lb(f'check {string} physical address')
            logger.error_fp(f'expect Page from FlashSetting equal to MicronVU, but FlashSetting value = {Page}, MicronVU value = {CISCode.Page.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    
    def get_VB_group(self, show:bool = False) -> Dict[int, Dict[str, int]]:
        fw_geometry = api.get_fw_geometry()
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'access_mode': {'pos': 6, 'len': 2, 'mask': 0x3}, 
            'dirty': {'pos': 8, 'len': 1, 'mask': 0x1}, 
            'partition': {'pos': 9, 'len': 2, 'mask': 0x3}, 
        }
        response, rep_data = api.get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break

            ftl_vb_list_data.update({vb : {k: (((rep_data[vb*4]|rep_data[vb*4+1]<<8) >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        if show:
            for vb, info in ftl_vb_list_data.items():
                group = info['group']
                access_mode = info['access_mode']
                partition = info['partition']
                logger.info(f'VB {vb} grouptype = {group} ({project_api.VB_GROUP(group).name}), access_mode = {access_mode}, partition = {partition}')
        return ftl_vb_list_data
    
    def compare_VB_type_criteria(self, raw_value: Any, expect_value: Any, VB:int) -> None:
        raw_fields = [
            (name, field) for name, field in raw_value.__dict__.items()
            if hasattr(field, "start_bit") and hasattr(field, "end_bit") and hasattr(field, "value")
        ]
        raw_fields.sort(key=lambda kv: kv[1].start_bit)
        expect_fields = [
            (name, field) for name, field in expect_value.__dict__.items()
            if hasattr(field, "start_bit") and hasattr(field, "end_bit") and hasattr(field, "value")
        ]
        expect_fields.sort(key=lambda kv: kv[1].start_bit)
        for (name0, raw), (name1, expect) in zip(
                                    raw_fields,
                                    expect_fields,
                                ):
            if hasattr(raw, "value") and hasattr(expect, "value") and name0 == name1:
                if raw.value != expect.value:
                    group = project_api.VB_GROUP(self.ftl_vb_list_data[VB]['group'])
                    access_mode = self.ftl_vb_list_data[VB]['access_mode']
                    logger.info(f'====== VB {VB} VB_GROUP = {group} ({group.name}), access_mode = {access_mode}, check VB Type ======')
                    logger.error_lb(f'check {name0}')
                    logger.error_fp(f'expect {name0} = {expect.value}, but current value = {raw.value}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            pass
        
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