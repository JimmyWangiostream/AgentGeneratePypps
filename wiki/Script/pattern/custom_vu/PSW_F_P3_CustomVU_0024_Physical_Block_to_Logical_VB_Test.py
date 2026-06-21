import package_root
from typing import cast
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from typing import TypeAlias, cast, List, TypedDict
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.vendor_cmd.structs import PCA
from Script.api.ufs_api.descriptors.configuration_desc.structs import ConfigDescriptor310, ConfigDescriptor400, ConfigDescriptor410
from enum import Enum, auto
from Script.project_api.custom_vu.lba_convert_vu import Logical_VB
from Script.project_api.custom_vu.lba_convert_vu import issue_40C9_to_get_logical_vb
from Script.api.ufs_api.vendor_cmd.functions import *

ENG2_WA = True

class RemapEntry(TypedDict):
    vb: int
    remap_vb: int

class BbrEntry(TypedDict):
    ce: int
    pln: int
    vb: int
    pb: int

class VBMapEntry(TypedDict):
    logical_vb: int          # 由 remap_table 產生的 logical VB
    physical_vb: int         # 來源的 physical VB (pb)
    ce:int                   # 對應的 CE
    plane: int               # 對應的 plane
    plnId: int               # 對應 40C9 plnId

ConfigDescriptorUnion: TypeAlias = ConfigDescriptor310 | ConfigDescriptor400 | ConfigDescriptor410

class Pattern(UFSTC):

    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        _, self.debug_info = api.get_debug_info()
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        self.remap_list: List[RemapEntry] = []
        self.bbr_list: List[BbrEntry] = []
        pass

    def step1(self) -> None:
        logger.flow(1, f'Fetch BBR table')
        self.find_bbr_table()

        logger.flow(2, f'Fetch REMAP table')
        self.find_remap_table()

        logger.flow(3, f'Iterate pb from 20 to total_vb_count to map:pb → BBR VB (BBR Table) → BBR VB (REMAP Table) → VB')
        vb_map_list: List[VBMapEntry] = []
        for blk in range(20, self.fw_geometry.l52_total_vb_count):
            physical_vb = blk
            bbr_entry = next((entry for entry in self.bbr_list if entry['pb'] == physical_vb), None)
            if bbr_entry != None:
                plnId = bbr_entry['ce']*6+bbr_entry['pln']
                bbr_vb = bbr_entry['vb']
                logical_vb= next((entry['vb'] for entry in self.remap_list if entry['remap_vb'] == bbr_vb), None)
                if logical_vb != None:
                    vb_map_list.append({
                        'logical_vb':logical_vb, 
                        'physical_vb': physical_vb, 
                        'ce': bbr_entry['ce'],
                        'plane': bbr_entry['pln'],
                        'plnId': plnId
                    })
                    vb_map_entry = vb_map_list[-1]
                    logger.info(f'{len(vb_map_list)}: pb= {physical_vb}, vb = {logical_vb}, ce = {vb_map_entry["ce"]} plane = {vb_map_entry["plane"]} plnId = {vb_map_entry["plnId"]}')   
        
        
        for entry in vb_map_list:
            logger.flow(4, f'Issue Micron 40C9 VU to get logical VB from physical VB')
            pb = entry['physical_vb']
            plnId = entry['plnId']
            _, vb = issue_40C9_to_get_logical_vb(pb, plnId)
            logger.info(f'Issue 40C9: pb= {pb}, vb = {vb.logical_vb.value}, plnId = {plnId}')

            logger.flow(5, f'Compare vb from 40C9 VU with logical_vb from remap table')
            logical_vb = entry['logical_vb']
            if(vb.logical_vb.value != logical_vb):
                logger.error_lb(f'Issue 40C9 VU to get logical VB from physical VB')
                logger.error_fp(f'Expected logical vb = {logical_vb}, but logical vb = {vb.logical_vb.value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def post_process(self) -> None:
        pass


    # self.fw_geometry.l52_total_vb_count
    def find_bbr_table(self) -> None:
        direct_read_pca = PCA()
        bbt_spare = bytearray([0xFF, 0xFF, 0xFF, 0xFF, 0x8B])
        for block in range(20):
            for ce in range(self.flash_setting.Max_Fdevice):
                for plane in range(self.flash_setting.Plane_Per_Die):
                    (data, spare) = self.get_direct_read(ce, plane, block, 0, 0)
                    if spare[0:5] == bbt_spare and (spare[128] & 0x10) == 0 :
                        logger.info(f'find BBT block: {block}')
                        bbr_raw = bytearray()
                        for i in range(2):
                            (data, spare) = self.get_direct_read(ce=ce, plane=plane, block=block, page=2, offset=i)
                            bbr_raw.extend(data)
                        plane_shift = 3
                        for ce in range(self.flash_setting.Max_Fdevice):
                            for pln in range(self.flash_setting.Plane_Per_Die):
                                start_bbr_index = (((ce << plane_shift) + pln)) * 256
                                bbr_table = bbr_raw[start_bbr_index:start_bbr_index+256]
                                for i in range(0,127,2):
                                    if(struct.unpack("<H",bbr_table[i * 2:(i*2)+2])[0]!=0xffff):
                                        self.bbr_list.append({
                                            'ce':ce,
                                            'pln':pln,
                                            'vb':struct.unpack("<H",bbr_table[i * 2+2:(i*2)+2+2])[0],
                                            'pb':struct.unpack("<H",bbr_table[i * 2:(i*2)+2])[0]
                                        })
                                        entry = self.bbr_list[-1]
                                        logger.info(f'[bbr_table] ce: {entry["ce"]}, plane: {entry["pln"]}, vvb: {entry["vb"]}, pb: {entry["pb"]}')
                        return
        pass

    def find_remap_table(self)->None:
        remap_table = self.get_remapped_vb()
        for vb in range(self.fw_geometry.l52_total_vb_count):
            self.remap_list.append({
                'vb': vb, 
                'remap_vb':struct.unpack("<H",remap_table[vb * 2:(vb*2)+2])[0]
            })
            entry = self.remap_list[-1]
            logger.info(f'[remap_table] vvb: {entry["remap_vb"]}, vb: {entry["vb"]}')
        pass
    

    def get_remapped_vb(self)-> bytearray:
        _, remap_buf = api.read_Xmemory(sram_address=self.debug_info.VB_list_remap_address.value)
        dumpfile('remapped_vb_data.bin', remap_buf)
        return remap_buf
    
    def get_direct_read(self, ce:int, plane:int, block:int, page:int, offset:int)-> tuple[bytearray, bytearray]:
        fpage = page*32 + offset*8
        direct_read_pca = PCA()
        direct_read_pca.l0_op = 0x20000
        direct_read_pca.b4_mode = 1 #SLC
        direct_read_pca.b5_ce = ce
        direct_read_pca.b6_plane = plane
        direct_read_pca.b11_block_h = (block>>8) & 0xFF
        direct_read_pca.b10_block_l = block & 0xFF
        direct_read_pca.l12_fpage = fpage
        payload = api.direct_read(pca=direct_read_pca, block_count=4, include_FW_spare=True)
        spare = payload[4 * DATA_SIZE_4K_BYTE:4 * DATA_SIZE_4K_BYTE + DATA_SIZE_4K_BYTE]
        data = payload[:4 * DATA_SIZE_4K_BYTE]
        logger.info(f'Block = {(direct_read_pca.b11_block_h<<8) | (direct_read_pca.b10_block_l)}, mode = {direct_read_pca.b4_mode}, CE = {direct_read_pca.b5_ce}, Plane = {direct_read_pca.b6_plane}, fPage = {fpage}')
        return data, spare


run = Pattern().run
if __name__ == "__main__":
    run()

