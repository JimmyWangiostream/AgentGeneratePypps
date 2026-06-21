from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.api.exception import *
from typing import Dict, List
from Script.api.ufs_api.vendor_cmd.functions import *


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting = api.get_flash_setting()
        pass

    def step1(self) -> None:
        logger.flow(1, 'Issue VU 40C8 to get bad block count.')
        resp, self.VU_DATA = project_api.issue_40C8_to_get_bad_blocks_count()
        pass

    def step2(self) -> None:
        logger.flow(2, 'Find BBT block & BB data. (Direct read find spare mark 0x8B.)')
        bbt_pca, self.bbt_block_data = self.find_bbt_block()

        self.BB_DATA = self.calculate_bbt(self.bbt_block_data)
        logger.info(f"Total = {len(self.BB_DATA)}")

        for bbt in self.BB_DATA:
            logger.info(f'VB = {bbt["Block"]}')
            logger.info(f'CePlane = {bbt["CE"] * self.flash_setting.Plane_Per_Die + bbt["Plane"]}')

        pass

    def step3(self) -> None:
        logger.info('Verify VU 40C8.')
        total_CePlane = int.from_bytes(self.VU_DATA[0:4], 'little')

        offset = 4
        register_byte = 4
        total_BB_count = sum(sum(self.VU_DATA[i: i + register_byte]) for i in range(offset, offset + total_CePlane * register_byte, register_byte))

        logger.flow(3, 'Check total BB count. (40C8 result == BB data)')
        if total_BB_count != len(self.BB_DATA):
            logger.error_lb(f'check total_BB_count of VU')
            logger.error_fp(f'expect total_BB_count from BB Table equal to MicronVU, but BB Table value = {len(self.BB_DATA)}, MicronVU value = {total_BB_count}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info(f'Total bad block count = {total_BB_count}')
            logger.info(f'Bad block table info = {len(self.BB_DATA)}')
            logger.info('Check total bad block count [Pass]')

        logger.flow(4, 'Check BB count by CePlane. (40C8 result == BB data)')
        CePlane_VU = []
        for i in range(offset, offset + total_CePlane * register_byte, register_byte):
            CePlane_VU.append(int.from_bytes(self.VU_DATA[i: i + register_byte], 'little'))

        CePlane_BBT = [0] * total_CePlane
        for bbt in self.BB_DATA:
            index = int(bbt["CE"] * self.flash_setting.Plane_Per_Die + bbt["Plane"])
            CePlane_BBT[index] += 1

        if CePlane_VU != CePlane_BBT:
            logger.error_fp(f'expect CePlane from BBT equal to MicronVU, but compare fail!')
            logger.error_lb(f'CePlane_VU = {CePlane_VU}')
            logger.error_lb(f'CePlane_BBT = {CePlane_BBT}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            for index in range(len(CePlane_VU)):
                logger.info(f'VU CePlane[{index}] bad block count = {CePlane_VU[index]}')
                logger.info(f'BBT CePlane[{index}] bad block count = {CePlane_BBT[index]}')
                logger.info('Check CePlane bad block count [Pass]')

        pass

    def post_process(self) -> None:
        pass

    def find_bbt_block(self) -> tuple[api.PCA, bytearray]:
        direct_read_pca = PCA()
        for block in range(self.fw_geometry.l52_total_vb_count):
            for ce in range(self.flash_setting.Max_Fdevice):
                for plane in range(self.flash_setting.Plane_Per_Die):
                    direct_read_pca.l0_op = 0x20000
                    direct_read_pca.b4_mode = 1
                    direct_read_pca.b5_ce = ce
                    direct_read_pca.b6_plane = plane
                    direct_read_pca.b11_block_h = (block >> 8) & 0xFF
                    direct_read_pca.b10_block_l = block & 0xFF
                    direct_read_pca.l12_fpage = 0
                    dire_read_payload = api.direct_read(pca=direct_read_pca, block_count=4, include_FW_spare=True)
                    logger.info(f'Block = {(direct_read_pca.b11_block_h << 8) | (direct_read_pca.b10_block_l)}')
                    logger.info(f'mode = {direct_read_pca.b4_mode}')
                    logger.info(f'CE = {direct_read_pca.b5_ce}')
                    logger.info(f'Plane = {direct_read_pca.b6_plane}')
                    logger.info(f'fPage = {direct_read_pca.l12_fpage}({direct_read_pca.l12_fpage >> 5} << 5)')
                    logger.info(f'lmu = {direct_read_pca.b20_lmu}')
                    logger.info(f'FW_Sapre = {dire_read_payload[api.DATA_SIZE_4K_BYTE * 4 + 4]}')
                    if dire_read_payload[api.DATA_SIZE_4K_BYTE * 4 + 4] == 0x8B:
                        return direct_read_pca, dire_read_payload
                    if block >= 20:
                        logger.error_lb(f'issue direct read to find BBT block')
                        logger.error_fp(f'expect BBT block < 20, but current block = {block}, result Fail!')
                        raise SIGHTING_PBA_UNEXPECTED
        return direct_read_pca, bytearray(0)

    def calculate_bbt(self, payload: bytearray) -> List[Dict[str, int]]:
        total_bb_cnt = 0
        bbt_map = []
        for ce in range(self.flash_setting.Max_Fdevice):
            data = payload[api.DATA_SIZE_4K_BYTE * ce: api.DATA_SIZE_4K_BYTE * (ce + 1)]
            for block in range(self.fw_geometry.l52_total_vb_count):
                for plane in range(self.flash_setting.Plane_Per_Die):
                    offset = block * (self.flash_setting.Plane_Per_Die // 2) + plane // 2
                    bad_type = (data[offset] >> 4 * (plane % 2)) & 0xF
                    if bad_type & api.BIT2:
                        total_bb_cnt += 1
                        bbt_map.append({
                            'Block': block,
                            'CE': ce,
                            'Plane': plane
                        })
        return bbt_map


run = Pattern().run
if __name__ == "__main__":
    run()
