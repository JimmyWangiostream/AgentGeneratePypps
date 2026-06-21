import random

from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import Dict, List
from Script.pattern.sgm.mutual_fun import open_card, open_card_basic


class Info:
    def __init__(self, CE: int, Plane: int, Block: int):
        self.CE: int = CE
        self.Plane: int = Plane
        self.Block: int = Block


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.flash_setting = api.get_flash_setting()
        pass

    def step1(self) -> None:
        logger.flow(1, 'Issue VU 40C7 to get bad block information.')
        logger.info('Record early pool physical VB count.')
        resp, VU_DATA_40C7 = project_api.issue_40C7_to_get_bad_block_info(0, 0)
        early_pool_physical_VB_count = VU_DATA_40C7.early_pool_physical_VB_count.value

        logger.flow(2, 'Issue VU 405E to get bad block information.')
        logger.info('Record BB count and data.')
        resp, VU_DATA_405E = project_api.issue_405E_to_get_bad_block_information()
        BB_count = int.from_bytes(VU_DATA_405E[0:4], byteorder='little')
        BB_data = self.calculate_bbt(VU_DATA_405E)

        logger.flow(3, 'Generate random bad block (BB) information for testing.')
        info_list = []
        total_loops = random.randint(5, 10)
        counter = 0

        while counter < total_loops:
            random_ce = random.randint(0, self.flash_setting.Max_Fdevice - 1)
            random_plane = random.randint(0, self.flash_setting.Plane_Per_Die - 1)
            random_block = random.randint(0, self.flash_setting.Max_PB - 1)

            new_info = Info(CE=random_ce, Plane=random_plane, Block=random_block)

            info_list.append(new_info)

            counter += 1

        logger.flow(4, 'Compare the generated data with the current BBT info and filter out duplicates.')
        bbt_set = {(d['CE'], d['Plane'], d['Block']) for d in BB_data}
        info_list = [
            info for info in info_list
            if (info.CE, info.Plane, info.Block) not in bbt_set
        ]
        info_set = {(d.CE, d.Plane, d.Block) for d in info_list}

        logger.flow(5, 'Convert the BB list into a bytearray.')
        temp = self.transfer(info_list)

        logger.flow(6, 'Issue VU C0BC to write bad block information.')
        project_api.issue_C0BC_to_write_BB_information(temp)

        logger.flow(7, 'MP.')
        open_card_basic()

        logger.flow(8, 'Verify the written data against the BBT.')
        resp, VU_DATA_405E = project_api.issue_405E_to_get_bad_block_information()
        BB_count_new = int.from_bytes(VU_DATA_405E[0:4], byteorder='little')
        BB_data_new = self.calculate_bbt(VU_DATA_405E)

        bbt_set_new = {(d['CE'], d['Plane'], d['Block']) for d in BB_data_new}

        if BB_count_new != BB_count + len(info_list):
            logger.error('Compare BB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        if not info_set.issubset(bbt_set_new):
            logger.error('Compare BB info failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(9, 'Verify that the early pool count is correct.')
        resp, VU_DATA_40C7 = project_api.issue_40C7_to_get_bad_block_info(0, 0)
        early_pool_physical_VB_count_new = VU_DATA_40C7.early_pool_physical_VB_count.value

        if early_pool_physical_VB_count_new != early_pool_physical_VB_count + len(info_list):
            logger.error('Compare early pool physical VB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass

    def post_process(self) -> None:
        open_card()
        pass

    def calculate_bbt(self, payload: bytearray) -> List[Dict[str, int]]:
        bbt_map = []
        bbt_cnt = int.from_bytes(payload[0:4], byteorder='little')

        for index in range(0, bbt_cnt, 1):
            BB_info = payload[(index * 8) + 8:(index * 8) + 16]
            BB_Block = int.from_bytes(BB_info[0:3], byteorder='little')
            BB_CE_Plane = int.from_bytes(BB_info[3:4], byteorder='little') >> 3
            BB_CE = BB_CE_Plane // 6
            BB_Plane = BB_CE_Plane % 6

            bbt_map.append({'Block': BB_Block, 'CE': BB_CE, 'Plane': BB_Plane})

        return bbt_map

    def transfer(self, info_list: list[Info]) -> bytearray:
        flash_bytes = bytearray()

        ce_groups: dict[int, list[Info]] = {0: [], 1: [], 2: [], 3: []}
        for info in info_list:
            if info.CE in ce_groups:
                ce_groups[info.CE].append(info)

        for ce in sorted(ce_groups.keys()):
            records = ce_groups[ce]

            if not records:
                continue

            die_marker = 0xFFF0 + ce
            flash_bytes.append(die_marker & 0xFF)
            flash_bytes.append((die_marker >> 8) & 0xFF)

            for info in records:
                composite_val = ((info.Block & 0x1FFF) << 3) | (info.Plane & 0x07)

                flash_bytes.append(composite_val & 0xFF)
                flash_bytes.append((composite_val >> 8) & 0xFF)

        flash_bytes.append(0xFF)
        flash_bytes.append(0xFF)
        flash_bytes = flash_bytes.ljust(0x4000, b'\x00')

        return flash_bytes


run = Pattern().run
if __name__ == "__main__":
    run()
