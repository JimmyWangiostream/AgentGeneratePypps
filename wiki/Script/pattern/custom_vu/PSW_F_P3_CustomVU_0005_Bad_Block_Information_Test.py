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

ENG2_WA = True

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting = api.get_flash_setting()
        pass

    def step1(self) -> None:
        logger.flow(1, 'issue VU 405E to get bad block information')
        _, self.VU_DATA = project_api.issue_405E_to_get_bad_block_information()
        dumpfile("vu405E.bin", self.VU_DATA)
        pass

    def step2(self) -> None:
        logger.flow(2, 'find bbt block')
        bbt_pca, self.bbt_block_data = self.find_bbt_block()
        dumpfile("bbt_block_data.bin",self.bbt_block_data)
        pass

    def step3(self) -> None:
        logger.flow(3, 'calculate bbt')
        self.BB_DATA = self.calculate_bbt(self.bbt_block_data)
        logger.info(f"Total = {len(self.BB_DATA)}")
        for bbt in self.BB_DATA:
            logger.info(f'VB = {hex(bbt["Block"])}, CePlane = {hex(bbt["CE"] * self.flash_setting.Plane_Per_Die + bbt["Plane"])}')
    
    def step4(self) -> None:
        logger.flow(4, 'check criteria')
        total_BB_count = int.from_bytes(self.VU_DATA[0:4], 'little')
        if total_BB_count != len(self.BB_DATA):
            logger.error_lb(f'check total_BB_count of VU')
            logger.error_fp(f'expect total_BB_count from BB Table equal to MicronVU, but BB Table value = {len(self.BB_DATA)}, MicronVU value = {total_BB_count}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        start = 4
        VU_DATA_map:Dict[int,List[int]] = {}
        for idx in range(total_BB_count):
            BB_retirement_reason = project_api.BB_retirement_reason(self.VU_DATA[start + idx*8: start + idx*8 +4])
            PBA = project_api.PBA_format(self.VU_DATA[start + 4 + idx*8: start + 4 + idx*8 +4])
            if not PBA.blockNum.value in VU_DATA_map:
                VU_DATA_map[PBA.blockNum.value] = []
            VU_DATA_map[PBA.blockNum.value].append((PBA.CePlane.value >> 3))
            BlkType = project_api.BBRetirementReaspnBlkType(BB_retirement_reason.BlkType.value)
            Type = project_api.BBRetirementReaspnType(BB_retirement_reason.Type.value)
            if BB_retirement_reason.BlkType.value != 0 or BB_retirement_reason.Type.value != 0:
                logger.info(f'idx = {idx}, BlkType = {BlkType} ({BlkType.name}), Type = {Type} ({Type.name})')
        for bbt in self.BB_DATA:
            CePlane = bbt["CE"] * self.flash_setting.Plane_Per_Die + bbt["Plane"]
            if (bbt["Block"] not in VU_DATA_map) or (CePlane not in VU_DATA_map[bbt["Block"]]):
                logger.error_lb(f'check BB of block {hex(bbt["Block"])} match data of VU')
                logger.error_fp(f"expect Block:{hex(bbt['Block'])} and CePlane:{CePlane} from BB Table in data MicronVU, but can't find, result Fail!")
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
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

    def calculate_bbt(self, payload:bytearray) -> List[Dict[str, int]]:
        total_bb_cnt = 0
        bbt_map = []
        for ce in range(self.flash_setting.Max_Fdevice):
            data = payload[api.DATA_SIZE_4K_BYTE * ce : api.DATA_SIZE_4K_BYTE * (ce + 1)]
            for block in range(self.fw_geometry.l52_total_vb_count):
                for plane in range(self.flash_setting.Plane_Per_Die):
                    offset = block * (self.flash_setting.Plane_Per_Die//2) + plane//2
                    bad_type = (data[offset] >> 4*(plane%2)) & 0xF
                    if bad_type & api.BIT2:
                        total_bb_cnt += 1
                        bbt_map.append({
                            'Block':block,
                            'CE':ce,
                            'Plane':plane
                        })
        return bbt_map


run = Pattern().run
if __name__ == "__main__":
    run()