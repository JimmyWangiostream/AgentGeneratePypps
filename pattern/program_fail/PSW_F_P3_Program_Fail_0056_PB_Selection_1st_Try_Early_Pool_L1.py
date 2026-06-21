import random

from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.project_api.erase_program_fail.structs import PhysicalAddressInformation
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.pattern.sgm.mutual_fun import open_card
from Script.pattern.program_fail import program_fail_api

# VC-30 (12.f)
# Program fail, selection new PB succeed on the first try, in normal area and searched in the earlyreplacement pool. FW should be update BB table and no assert.


class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.flow(1, 'Issue VU 40C1 to get open VB information, extract the L1 VB from the result.')
        resp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        L1_vb = open_vb_information.L1_open_VB_S_CHUNK_logical_number.value

        logger.flow(2, 'Issue VU 40DC to get next open VB information, extract the next L1 VB from the result.')
        resp, next_open_vb_information = project_api.issue_40DC_to_get_next_open_vb_information(0)
        L1_vb_next = next_open_vb_information.DM_NORMAL_HOST_VB.value

        logger.flow(3, 'Issue VU 405E to get bad block information.')
        logger.info('Record BB count.')
        resp, VU_DATA_405E = project_api.issue_405E_to_get_bad_block_information()
        BB_count = int.from_bytes(VU_DATA_405E[0:4], byteorder='little')

        ce = 0
        plane = 0

        logger.flow(4, 'Issue VU C012 to create program fail. (Make L1 PF.)')
        info = PhysicalAddressInformation()
        info.BlockInfoList_0_die.value = ce
        info.BlockInfoList_0_plane.value = plane
        info.BlockInfoList_0_block.value = L1_vb_next
        info.BlockInfoList_0_page.value = 0
        info.BlockInfoList_0_tg_bitmap.value = 0
        project_api.issue_C012_to_create_program_erase_fail(info, fail_type=0)

        logger.info('Record target BB information.')
        target_data_L1 = {'Block': info.BlockInfoList_0_block.value, 'CE': info.BlockInfoList_0_die.value, 'Plane': info.BlockInfoList_0_plane.value}

        logger.flow(5, 'Perform random writes until the L1 VB changes, then trigger an program failure.')
        while True:
            data_len = 16
            start_lba = random.randint(0, shared.param.gLUCapacity[0] - data_len)
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=0, lba=start_lba, length=data_len, fua=1)
            ExecuteCMD.enqueue(write10)
            ExecuteCMD.send(clear_on_success=False, skip_response_check=True)
            ExecuteCMD.clear()

            resp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
            L1_vb_new = open_vb_information.L1_open_VB_S_CHUNK_logical_number.value

            if L1_vb_new != L1_vb:
                break

        logger.flow(6, 'Issue VU 4013 to get BE fail status.')
        project_api.issue_4013_to_get_BE_fail_status()

        logger.flow(7, 'Issue VU 405E to get bad block information again and verity BBT.')
        resp, VU_DATA_405E_new = project_api.issue_405E_to_get_bad_block_information()
        BB_count_new = int.from_bytes(VU_DATA_405E_new[0:4], byteorder='little')
        BB_data_new = program_fail_api.calculate_bbt(VU_DATA_405E_new)

        if BB_count_new != BB_count + 1:
            logger.error('Compare BB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        find = [d for d in BB_data_new if target_data_L1.items() <= d.items()]

        if not find:
            logger.error('Compare BBT failure. (L1)')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass

    def post_process(self) -> None:
        open_card()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
