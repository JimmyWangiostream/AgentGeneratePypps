from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.project_api.erase_program_fail.structs import PhysicalAddressInformation
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.pattern.sgm.mutual_fun import open_card
from Script.pattern.program_fail import program_fail_api

# VC-29 (12.e)
# Program fail, selection new PB succeed on the first try, in hidden area case. FW should be update BB table and no assert.


class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.flow(1, 'Issue VU 40C1 to get open VB information, extract the L2 VB from the result.')
        resp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        L2_vb = open_vb_information.L2_Open_logical_VB_Host_TLC_number.value

        logger.flow(2, 'Issue VU 405E to get bad block information.')
        logger.info('Record BB count.')
        resp, VU_DATA_405E = project_api.issue_405E_to_get_bad_block_information()
        BB_count = int.from_bytes(VU_DATA_405E[0:4], byteorder='little')

        ce = 0
        plane = 0

        logger.flow(3, 'Issue VU 40D6 to get predicted next 1 replacement block. (For hidden area.)')
        resp, VU_DATA_40D6 = project_api.issue_40D6_to_get_predicted_next_n_replacement_block(ce=ce, plane=plane, next_n=1, pool_type=2, is_CIS=0, pf_on_open_data=0)
        next_replacement_block = (int.from_bytes(VU_DATA_40D6[0:4], byteorder='little') & 0xFFFFFFE0) >> 5
        next_replacement_plane = (int.from_bytes(VU_DATA_40D6[0:4], byteorder='little') & 0x1C) >> 2
        next_replacement_ce = (int.from_bytes(VU_DATA_40D6[0:4], byteorder='little') & 0x03)

        logger.flow(4, 'Issue VU C012 to create program fail. (Make L2 PF, BBT PF.)')
        info = PhysicalAddressInformation()
        info.BlockInfoList_0_die.value = ce
        info.BlockInfoList_0_plane.value = plane
        info.BlockInfoList_0_block.value = L2_vb
        info.BlockInfoList_0_page.value = 0
        info.BlockInfoList_0_tg_bitmap.value = 0
        info.BlockInfoList_1_die.value = next_replacement_ce
        info.BlockInfoList_1_plane.value = next_replacement_plane
        info.BlockInfoList_1_block.value = next_replacement_block
        info.BlockInfoList_1_page.value = 0
        info.BlockInfoList_1_tg_bitmap.value = 0
        project_api.issue_C012_to_create_program_erase_fail(info, fail_type=0, block_info_list_count=2)

        logger.info('Record target BB information.')
        target_data_L2 = {'Block': info.BlockInfoList_0_block.value, 'CE': info.BlockInfoList_0_die.value, 'Plane': info.BlockInfoList_0_plane.value}
        target_data_BBT = {'Block': info.BlockInfoList_1_block.value, 'CE': info.BlockInfoList_1_die.value, 'Plane': info.BlockInfoList_1_plane.value}

        logger.flow(5, 'Perform sequential writes, then trigger an program failure.')
        start_lba = 0
        data_len = api.WRITE_10_MAX_BLOCK_LEN
        write10 = ExecuteCMD.Write10()
        write10.assign(lun=0, lba=start_lba, length=data_len, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

        logger.flow(6, 'Issue VU 4013 to get BE fail status.')
        project_api.issue_4013_to_get_BE_fail_status()

        logger.flow(7, 'Issue VU 405E to get bad block information again and verity BBT.')
        resp, VU_DATA_405E_new = project_api.issue_405E_to_get_bad_block_information()
        BB_count_new = int.from_bytes(VU_DATA_405E_new[0:4], byteorder='little')
        BB_data_new = program_fail_api.calculate_bbt(VU_DATA_405E_new)

        if BB_count_new != BB_count + 2:
            logger.error('Compare BB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        find = [d for d in BB_data_new if target_data_L2.items() <= d.items()]

        if not find:
            logger.error('Compare BBT failure. (L2)')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        find = [d for d in BB_data_new if target_data_BBT.items() <= d.items()]

        if not find:
            logger.error('Compare BBT failure. (BBT)')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass

    def post_process(self) -> None:
        open_card()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
