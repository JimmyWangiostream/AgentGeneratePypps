import random

from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.project_api.erase_program_fail.structs import PhysicalAddressInformation
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.pattern.refresh.mutual_fun import get_VB_group
from Script.pattern.sgm.mutual_fun import open_card
from Script.pattern.program_fail import program_fail_api

# VC-35 (13.g)
# Program fail, selection new PB succeed on the second try, in normal area and searched in the latereplacement pool (shared for dynamic). FW should be update BB table and no assert.


class Pattern(UFSTC):
    def pre_process(self) -> None:
        # Find current revoke VB.
        ftl_vb_list_data = get_VB_group(show=True)
        revoke_group = [k for k, v in ftl_vb_list_data.items() if v.get('group') == project_api.VB_GROUP.REVOKE_BLK]

        while True:
            logger.flow(1, 'Issue VU 40C1 to get open VB information, extract the L2 VB from the result.')
            resp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
            L2_vb = open_vb_information.L2_Open_logical_VB_Host_TLC_number.value

            logger.flow(2, 'Issue VU 40DC to get next open VB information, extract the next L2 VB from the result.')
            resp, next_open_vb_information = project_api.issue_40DC_to_get_next_open_vb_information(0)
            L2_vb_next = next_open_vb_information.DM_NORMAL_HOST_VB.value

            logger.flow(3, 'Issue VU 405E to get bad block information.')
            logger.info('Record BB count.')
            resp, VU_DATA_405E = project_api.issue_405E_to_get_bad_block_information()
            BB_count = int.from_bytes(VU_DATA_405E[0:4], byteorder='little')

            logger.flow(4, 'Issue VU 40D6 to get predicted next 1 replacement block.')
            resp, VU_DATA_40D6 = project_api.issue_40D6_to_get_predicted_next_n_replacement_block(ce=0, plane=0, next_n=1, pool_type=1, is_CIS=0, pf_on_open_data=0)
            next_replacement_block = int.from_bytes(VU_DATA_40D6[0:4], byteorder='little')

            if next_replacement_block not in revoke_group:
                break

            logger.flow(5, 'Issue VU C012 to create erase fail. (Make L2 EF.)')
            info = PhysicalAddressInformation()
            info.BlockInfoList_0_die.value = 0
            info.BlockInfoList_0_plane.value = 0
            info.BlockInfoList_0_block.value = L2_vb_next
            info.BlockInfoList_0_page.value = 0
            info.BlockInfoList_0_tg_bitmap.value = 0
            project_api.issue_C012_to_create_program_erase_fail(info, fail_type=1)

            logger.info('Record target BB information.')
            target_data_L2 = {'Block': info.BlockInfoList_0_block.value, 'CE': info.BlockInfoList_0_die.value, 'Plane': info.BlockInfoList_0_plane.value}

            logger.flow(6, 'Perform sequential writes until the L2 VB changes, then trigger an erase failure.')
            start_lba = 0

            while True:
                data_len = api.WRITE_10_MAX_BLOCK_LEN
                write10 = ExecuteCMD.Write10()
                write10.assign(lun=0, lba=start_lba, length=data_len, fua=1)
                ExecuteCMD.enqueue(write10)
                ExecuteCMD.send(clear_on_success=False)
                ExecuteCMD.clear()

                resp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
                L2_vb_new = open_vb_information.L2_Open_logical_VB_Host_TLC_number.value

                if L2_vb_new != L2_vb:
                    break
                else:
                    start_lba += data_len

            logger.flow(7, 'Issue VU 4013 to get BE fail status.')
            project_api.issue_4013_to_get_BE_fail_status()

            logger.flow(8, 'Issue VU 405E to get bad block information again and verity BBT.')
            resp, VU_DATA_405E_new = project_api.issue_405E_to_get_bad_block_information()
            BB_count_new = int.from_bytes(VU_DATA_405E_new[0:4], byteorder='little')
            BB_data_new = program_fail_api.calculate_bbt(VU_DATA_405E_new)

            if BB_count_new != BB_count + 1:
                logger.error('Compare BB count failure.')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            find = [d for d in BB_data_new if target_data_L2.items() <= d.items()]

            if not find:
                logger.error('Compare BBT failure. (L2)')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(9, 'Iterate through flows 1 ~ 8 until 40D6 to get the predicted next replacement block which is in the revoke group.')

        pass

    def step1(self) -> None:
        logger.flow(1, 'Issue VU 40C1 to get open VB information, extract the LIST VB from the result.')
        resp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        LIST_vb = open_vb_information.List_Block_VB_number_logical.value

        logger.flow(2, 'Issue VU 40DC to get next open VB information, extract the next LIST VB from the result.')
        resp, next_open_vb_information = project_api.issue_40DC_to_get_next_open_vb_information(0)
        LIST_vb_next = next_open_vb_information.List.value

        logger.flow(3, 'Issue VU 405E to get bad block information.')
        logger.info('Record BB count.')
        resp, VU_DATA_405E = project_api.issue_405E_to_get_bad_block_information()
        BB_count = int.from_bytes(VU_DATA_405E[0:4], byteorder='little')

        ce = 0
        plane = 0

        logger.flow(4, 'Issue VU 40D6 to get predicted next 1 replacement block.')
        resp, VU_DATA_40D6 = project_api.issue_40D6_to_get_predicted_next_n_replacement_block(ce=0, plane=0, next_n=1, pool_type=1, is_CIS=0, pf_on_open_data=0)
        next_replacement_block = int.from_bytes(VU_DATA_40D6[0:4], byteorder='little')

        logger.flow(5, 'Issue VU C012 to create program fail. (Make LIST PF, next replacement block PF.)')
        info = PhysicalAddressInformation()
        info.BlockInfoList_0_die.value = ce
        info.BlockInfoList_0_plane.value = plane
        info.BlockInfoList_0_block.value = LIST_vb_next
        info.BlockInfoList_0_page.value = 0
        info.BlockInfoList_0_tg_bitmap.value = 0
        info.BlockInfoList_1_die.value = ce
        info.BlockInfoList_1_plane.value = plane
        info.BlockInfoList_1_block.value = next_replacement_block
        info.BlockInfoList_1_page.value = 0
        info.BlockInfoList_1_tg_bitmap.value = 0
        project_api.issue_C012_to_create_program_erase_fail(info, fail_type=0, block_info_list_count=2)

        logger.info('Record target BB information.')
        target_data_LIST = {'Block': info.BlockInfoList_0_block.value, 'CE': info.BlockInfoList_0_die.value, 'Plane': info.BlockInfoList_0_plane.value}
        target_data_replace = {'Block': info.BlockInfoList_1_block.value, 'CE': info.BlockInfoList_1_die.value, 'Plane': info.BlockInfoList_1_plane.value}

        logger.flow(6, 'Perform random writes until the LIST VB changes, then trigger an program failure.')
        while True:
            data_len = api.WRITE_10_MAX_BLOCK_LEN
            start_lba = random.randint(0, shared.param.gLUCapacity[0] - data_len)
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=0, lba=start_lba, length=data_len, fua=1)
            ExecuteCMD.enqueue(write10)
            ExecuteCMD.send(clear_on_success=False, skip_response_check=True)
            ExecuteCMD.clear()

            resp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
            LIST_vb_new = open_vb_information.List_Block_VB_number_logical.value

            if LIST_vb_new != LIST_vb:
                break

        logger.flow(7, 'Issue VU 4013 to get BE fail status.')
        project_api.issue_4013_to_get_BE_fail_status()

        logger.flow(8, 'Issue VU 405E to get bad block information again and verity BBT.')
        resp, VU_DATA_405E_new = project_api.issue_405E_to_get_bad_block_information()
        BB_count_new = int.from_bytes(VU_DATA_405E_new[0:4], byteorder='little')
        BB_data_new = program_fail_api.calculate_bbt(VU_DATA_405E_new)

        if BB_count_new != BB_count + 2:
            logger.error('Compare BB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        find = [d for d in BB_data_new if target_data_LIST.items() <= d.items()]

        if not find:
            logger.error('Compare BBT failure. (LIST)')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        find = [d for d in BB_data_new if target_data_replace.items() <= d.items()]

        if not find:
            logger.error('Compare BBT failure. (replacement)')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass

    def post_process(self) -> None:
        open_card()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
