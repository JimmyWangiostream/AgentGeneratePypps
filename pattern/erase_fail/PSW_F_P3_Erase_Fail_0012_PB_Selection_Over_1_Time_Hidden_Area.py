from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.project_api.erase_program_fail.structs import PhysicalAddressInformation
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.lib.sdk_lib.user.exception import G_TIMEOUT_ALL
from Script.pattern.sgm.mutual_fun import open_card

# VC-18 (5.c)
# Erase fail, selection new PB failed over 1 times, in hidden area case. FW stuck.


class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.flow(1, 'Issue VU 40C1 to get open VB information, extract the L2 VB from the result.')
        resp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        L2_vb = open_vb_information.L2_Open_logical_VB_Host_TLC_number.value

        logger.flow(2, 'Issue VU 40DC to get next open VB information, extract the next L2 VB from the result.')
        resp, next_open_vb_information = project_api.issue_40DC_to_get_next_open_vb_information(0)
        L2_vb_next = next_open_vb_information.DM_NORMAL_HOST_VB.value


        ce = 0
        plane = 0

        logger.flow(3, 'Issue VU 40D6 to get predicted next 2 replacement block. (For hidden area.)')
        resp, VU_DATA_40D6 = project_api.issue_40D6_to_get_predicted_next_n_replacement_block(ce=ce, plane=plane, next_n=2, pool_type=2, is_CIS=0, pf_on_open_data=0)
        next_replacement_block_1 = (int.from_bytes(VU_DATA_40D6[0:4], byteorder='little') & 0xFFFFFFE0) >> 5
        next_replacement_plane_1 = (int.from_bytes(VU_DATA_40D6[0:4], byteorder='little') & 0x1C) >> 2
        next_replacement_ce_1 = (int.from_bytes(VU_DATA_40D6[0:4], byteorder='little') & 0x03)
        next_replacement_block_2 = (int.from_bytes(VU_DATA_40D6[4:8], byteorder='little') & 0xFFFFFFE0) >> 5
        next_replacement_plane_2 = (int.from_bytes(VU_DATA_40D6[4:8], byteorder='little') & 0x1C) >> 2
        next_replacement_ce_2 = (int.from_bytes(VU_DATA_40D6[4:8], byteorder='little') & 0x03)

        logger.flow(4, 'Issue VU C012 to create erase fail. (Make L2 EF,1st BBT EF, and 2nd BBT EF.)')
        info = PhysicalAddressInformation()
        info.BlockInfoList_0_die.value = ce
        info.BlockInfoList_0_plane.value = plane
        info.BlockInfoList_0_block.value = L2_vb_next
        info.BlockInfoList_0_page.value = 0
        info.BlockInfoList_0_tg_bitmap.value = 0
        info.BlockInfoList_1_die.value = next_replacement_ce_1
        info.BlockInfoList_1_plane.value = next_replacement_plane_1
        info.BlockInfoList_1_block.value = next_replacement_block_1
        info.BlockInfoList_1_page.value = 0
        info.BlockInfoList_1_tg_bitmap.value = 0
        info.BlockInfoList_2_die.value = next_replacement_ce_2
        info.BlockInfoList_2_plane.value = next_replacement_plane_2
        info.BlockInfoList_2_block.value = next_replacement_block_2
        info.BlockInfoList_2_page.value = 0
        info.BlockInfoList_2_tg_bitmap.value = 0
        project_api.issue_C012_to_create_program_erase_fail(info, fail_type=1, block_info_list_count=3)

        logger.flow(5, 'Perform sequential writes until the L2 VB changes, then trigger an erase failure.')
        start_lba = 0

        while True:
            data_len = api.WRITE_10_MAX_BLOCK_LEN
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=0, lba=start_lba, length=data_len, fua=1)
            ExecuteCMD.enqueue(write10)

            try:
                ExecuteCMD.send(clear_on_success=False, skip_response_check=True)

            except G_TIMEOUT_ALL:
                logger.flow(6, 'Check hit FW assert 0x510.')
                if api.get_fw_assert_number() == 0x510:
                    logger.info('Get FW assert no 0x510.')
                    return
                else:
                    logger.error('FW should be stuck.')
                    raise SIGHTING_RESPONSE_UNEXPECTED

            ExecuteCMD.clear()

            resp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
            L2_vb_new = open_vb_information.L2_Open_logical_VB_Host_TLC_number.value

            if L2_vb_new != L2_vb:
                logger.error('FW should be stuck.')
                raise SIGHTING_RESPONSE_UNEXPECTED
            else:
                start_lba += data_len

        pass

    def post_process(self) -> None:
        ExecuteCMD.clear()

        open_card()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
