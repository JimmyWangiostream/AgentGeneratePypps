from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.project_api.erase_program_fail.structs import PhysicalAddressInformation
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.pattern.sgm.mutual_fun import open_card
from Script.pattern.program_fail import program_fail_api

# VC-38 (14.f)
# Program fail, selection new PB succeed on the first try, in normal area and searched in the earlyreplacement pool. FW should be update BB table and no assert. (Page_BB <= LWP of PB_BB)
# Boundary case.


class Pattern(UFSTC):
    def pre_process(self) -> None:
        while True:
            logger.flow(1, 'Perform sequential writes until the first empty SLC page is reached.')
            resp, open_vb_info = get_open_vb_info()
            open_vb: OpenVBInfo = OpenVBInfo(open_vb_info.payload.copy())
            physical_page = open_vb.TLC_L2.first_empty_physical_page.value

            if physical_page >= 3308:
                break

            start_lba = 0
            data_len = 16
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=0, lba=start_lba, length=data_len, fua=1)
            ExecuteCMD.enqueue(write10)
            ExecuteCMD.send(clear_on_success=False)
            ExecuteCMD.clear()

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

        ce = 0
        plane = 0

        logger.flow(3, 'Issue VU C012 to create program fail. (Make L2 PF.)')
        info = PhysicalAddressInformation()
        info.BlockInfoList_0_die.value = ce
        info.BlockInfoList_0_plane.value = plane
        info.BlockInfoList_0_block.value = logical_VB
        info.BlockInfoList_0_page.value = logical_page
        info.BlockInfoList_0_tg_bitmap.value = 0
        project_api.issue_C012_to_create_program_erase_fail(info, fail_type=3)

        logger.info('Record target BB information.')
        target_data_L2 = {'Block': info.BlockInfoList_0_block.value, 'CE': info.BlockInfoList_0_die.value, 'Plane': info.BlockInfoList_0_plane.value}

        logger.flow(4, 'Perform sequential writes, then trigger an program failure.')
        start_lba = 0
        data_len = api.WRITE_10_MAX_BLOCK_LEN
        write10 = ExecuteCMD.Write10()
        write10.assign(lun=0, lba=start_lba, length=data_len, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

        logger.flow(5, 'Issue VU 4013 to get BE fail status.')
        project_api.issue_4013_to_get_BE_fail_status()

        logger.flow(6, 'Issue VU 405E to get bad block information again and verity BBT.')
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

        pass

    def post_process(self) -> None:
        open_card()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
