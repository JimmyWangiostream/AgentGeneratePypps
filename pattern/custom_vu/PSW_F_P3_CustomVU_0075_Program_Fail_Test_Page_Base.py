from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.project_api.erase_program_fail.structs import PhysicalAddressInformation
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import Dict, List
from Script.pattern.sgm.mutual_fun import open_card


class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.flow(1, 'Issue VU to get open VB information, extract the L2 VB & first empty physical page from the result.')
        resp, open_vb_info = get_open_vb_info()
        open_vb: OpenVBInfo = OpenVBInfo(open_vb_info.payload.copy())
        logical_VB = open_vb.TLC_L2.logical_vb.value
        physical_page = open_vb.TLC_L2.first_empty_physical_page.value

        logger.flow(2, 'Issue VU 405E to get bad block information.')
        logger.info('Record BB count.')
        resp, VU_DATA_405E = project_api.issue_405E_to_get_bad_block_information()
        BB_count = int.from_bytes(VU_DATA_405E[0:4], byteorder='little')
        BB_data = self.calculate_bbt(VU_DATA_405E)

        # Transfer physical page to logical page.
        region_max_wl = [540, 556, 1108]
        if physical_page < 1620:
            logical_page = physical_page // 3
        elif physical_page < 1652:
            logical_page = (physical_page - 1620) // 2
            logical_page += region_max_wl[0]
        elif physical_page < 3308:
            logical_page = (physical_page - 1652) // 3
            logical_page += region_max_wl[1]
        elif physical_page < 3312:
            logical_page = (physical_page - 3308) // 1
            logical_page += region_max_wl[2]

        logger.flow(3, 'Issue VU C012 to create program fail.')
        info = PhysicalAddressInformation()
        info.BlockInfoList_0_die.value = 0
        info.BlockInfoList_0_plane.value = 0
        info.BlockInfoList_0_block.value = logical_VB
        info.BlockInfoList_0_page.value = logical_page + 1
        info.BlockInfoList_0_tg_bitmap.value = 0
        project_api.issue_C012_to_create_program_erase_fail(info, fail_type=3)

        logger.info('Record target BB information.')
        target_data = {'Block': info.BlockInfoList_0_block.value, 'CE': info.BlockInfoList_0_die.value, 'Plane': info.BlockInfoList_0_plane.value}

        logger.flow(4, 'Perform sequential writes, then trigger an program failure.')
        start_lba = 0
        data_len = api.WRITE_10_MAX_BLOCK_LEN * 16
        write16 = ExecuteCMD.Write16()
        write16.assign(lun=0, lba=start_lba, length=data_len, fua=1)
        ExecuteCMD.enqueue(write16)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

        logger.flow(5, 'Issue VU 4013 to get BE fail status.')
        resp, status = project_api.issue_4013_to_get_BE_fail_status()

        if status.fail_type.value != 1:
            logger.error('Compare fail type failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info('Check fail type. [Pass]')

        if status.fail_times.value == 0:
            logger.error('Compare fail times failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info('Check fail times. [Pass]')

        if status.time_0_die.value != info.BlockInfoList_0_die.value:
            logger.error('Compare die failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info('Check die. [Pass]')

        if status.time_0_plane.value != info.BlockInfoList_0_plane.value:
            logger.error('Compare plane failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info('Check plane. [Pass]')

        if status.time_0_block.value != info.BlockInfoList_0_block.value:
            logger.error('Compare block failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info('Check block. [Pass]')

        if status.time_0_page.value != info.BlockInfoList_0_page.value:
            logger.error('Compare page failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info('Check page. [Pass]')

        if status.time_0_tg_bitmap.value != info.BlockInfoList_0_tg_bitmap.value:
            logger.error('Compare tg bitmap failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info('Check TG bitmap. [Pass]')

        logger.flow(6, 'Issue VU 405E to get bad block information again and verity BBT.')
        resp, VU_DATA_405E_new = project_api.issue_405E_to_get_bad_block_information()
        BB_count_new = int.from_bytes(VU_DATA_405E_new[0:4], byteorder='little')
        BB_data_new = self.calculate_bbt(VU_DATA_405E_new)

        if BB_count_new != BB_count + 1:
            logger.error('Compare BB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info('Check bad block count. [Pass]')

        find = [d for d in BB_data_new if target_data.items() <= d.items()]

        if not find:
            logger.error('Compare BBT failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info('Check target BB information in BBT. [Pass]')

        pass

    def post_process(self) -> None:
        open_card()
        pass

    def calculate_bbt(self, payload: bytearray) -> List[Dict[str, int]]:
        bbt_map = []

        for index in range(4, 0x1000, 8):
            BB_info = payload[index + 4:index + 8]
            BB_Block = int.from_bytes(BB_info[0:2], byteorder='little')
            BB_CE = int.from_bytes(BB_info[2:3], byteorder='little')
            BB_Plane = int.from_bytes(BB_info[3:4], byteorder='little') >> 3

            if BB_Block != 0:
                bbt_map.append({
                    'Block': BB_Block,
                    'CE': BB_CE,
                    'Plane': BB_Plane
                })

        return bbt_map


run = Pattern().run
if __name__ == "__main__":
    run()
