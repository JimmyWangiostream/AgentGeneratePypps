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
        open_card()

        self.flash_setting = api.get_flash_setting()
        pass

    def step1(self) -> None:
        # Perform the initial value test after the MP operation.
        logger.flow(1, 'Issue VU 405E to get bad block information.')
        logger.info('Record BB count.')
        resp, VU_DATA_405E = project_api.issue_405E_to_get_bad_block_information()
        BB_count = int.from_bytes(VU_DATA_405E[0:4], byteorder='little')
        BB_data = self.calculate_bbt(VU_DATA_405E)

        logger.flow(2, 'Issue VU 40C7 to get bad block information.')
        pb = 0
        plane = 0
        resp, BB_info = project_api.issue_40C7_to_get_bad_block_info(pb, plane)
        self.later_VB_count = BB_info.later_VB_count.value
        self.later_VB_max_count = BB_info.later_VB_max_count.value
        self.later_program_fail_VB_max_count = BB_info.later_program_fail_VB_max_count.value
        self.later_erase_fail_VB_max_count = BB_info.later_erase_fail_VB_max_count.value
        early_pool_physical_VB_count = BB_info.early_pool_physical_VB_count.value

        if self.later_VB_count != 0:
            logger.error('Compare later VB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        if self.later_program_fail_VB_max_count != 0:
            logger.error('Compare later program fail VB max count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        if self.later_erase_fail_VB_max_count != 0:
            logger.error('Compare later erase fail VB max count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        if BB_count != early_pool_physical_VB_count:
            logger.error('Compare early pool physical VB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        for block in range(0, self.flash_setting.Max_PB):
            for ce in range(0, self.flash_setting.Max_Fdevice):
                for plane in range(0, self.flash_setting.Plane_Per_Die):
                    target_data = {'Block': block, 'CE': ce, 'Plane': plane}

                    resp, BB_info = project_api.issue_40C7_to_get_bad_block_info(block, plane)
                    status = BB_info.status.value
                    replaced_physical_block = BB_info.replaced_physical_block.value

                    find = [d for d in BB_data if target_data.items() <= d.items()]

                    if find:
                        if status != 1:
                            logger.error('Compare BBT and status failure.')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        if replaced_physical_block == 0xFFFFFFFF:
                            logger.error('Compare replaced physical block failure.')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    else:
                        if status != 0:
                            logger.error('Compare BBT and status failure.')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        if replaced_physical_block != 0xFFFFFFFF:
                            logger.error('Compare replaced physical block failure.')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass

    def step2(self) -> None:
        # Perform the erase fail test after the MP operation.
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

        logger.flow(4, 'Issue VU C012 to create erase fail.')
        info = PhysicalAddressInformation()
        info.BlockInfoList_0_die.value = 0
        info.BlockInfoList_0_plane.value = 0
        info.BlockInfoList_0_block.value = L2_vb_next
        info.BlockInfoList_0_page.value = 0
        info.BlockInfoList_0_tg_bitmap.value = 0
        project_api.issue_C012_to_create_program_erase_fail(info, fail_type=1)

        logger.flow(5, 'Perform sequential writes until the L2 VB changes, then trigger an erase failure.')
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

        resp, status = project_api.issue_4013_to_get_BE_fail_status(1)

        logger.flow(6, 'Issue VU 405E to get bad block information again and verity BBT.')
        resp, VU_DATA_405E_new = project_api.issue_405E_to_get_bad_block_information()
        BB_count_new = int.from_bytes(VU_DATA_405E_new[0:4], byteorder='little')

        if BB_count_new != BB_count + 1:
            logger.error('Compare BB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(7, 'Issue VU 40C7 to get bad block information.')
        pb = 0
        plane = 0
        resp, BB_info = project_api.issue_40C7_to_get_bad_block_info(pb, plane)
        later_VB_count_new = BB_info.later_VB_count.value
        later_VB_max_count_new = BB_info.later_VB_max_count.value
        later_erase_fail_VB_max_count_new = BB_info.later_erase_fail_VB_max_count.value

        if later_VB_count_new != self.later_VB_count + 1:
            logger.error('Compare later VB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        if later_VB_max_count_new != self.later_VB_max_count - 1:
            logger.error('Compare later VB max count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        if later_erase_fail_VB_max_count_new != self.later_erase_fail_VB_max_count + 1:
            logger.error('Compare later erase fail VB max count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        self.later_VB_count += 1
        self.later_VB_max_count -= 1

        pass

    def step3(self) -> None:
        # Perform the program fail test after the MP operation.
        logger.flow(1, 'Issue VU 40C1 to get open VB information, extract the L2 VB from the result.')
        resp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        L2_vb = open_vb_information.L2_Open_logical_VB_Host_TLC_number.value

        logger.flow(2, 'Issue VU 405E to get bad block information.')
        logger.info('Record BB count.')
        resp, VU_DATA_405E = project_api.issue_405E_to_get_bad_block_information()
        BB_count = int.from_bytes(VU_DATA_405E[0:4], byteorder='little')

        logger.flow(3, 'Issue VU C012 to create program fail.')
        info = PhysicalAddressInformation()
        info.BlockInfoList_0_die.value = 0
        info.BlockInfoList_0_plane.value = 0
        info.BlockInfoList_0_block.value = L2_vb
        info.BlockInfoList_0_page.value = 0
        info.BlockInfoList_0_tg_bitmap.value = 0
        project_api.issue_C012_to_create_program_erase_fail(info, fail_type=0)

        logger.flow(4, 'Perform sequential writes, then trigger an program failure.')
        start_lba = 0
        data_len = api.WRITE_10_MAX_BLOCK_LEN
        write10 = ExecuteCMD.Write10()
        write10.assign(lun=0, lba=start_lba, length=data_len, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

        resp, status = project_api.issue_4013_to_get_BE_fail_status(1)

        logger.flow(5, 'Issue VU 405E to get bad block information again and verity BBT.')
        resp, VU_DATA_405E_new = project_api.issue_405E_to_get_bad_block_information()
        BB_count_new = int.from_bytes(VU_DATA_405E_new[0:4], byteorder='little')

        if BB_count_new != BB_count + 1:
            logger.error('Compare BB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(6, 'Issue VU 40C7 to get bad block information.')
        pb = 0
        plane = 0
        resp, BB_info = project_api.issue_40C7_to_get_bad_block_info(pb, plane)
        later_VB_count_new = BB_info.later_VB_count.value
        later_VB_max_count_new = BB_info.later_VB_max_count.value
        later_program_fail_VB_max_count_new = BB_info.later_program_fail_VB_max_count.value

        if later_VB_count_new != self.later_VB_count + 1:
            logger.error('Compare later VB count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        if later_VB_max_count_new != self.later_VB_max_count - 1:
            logger.error('Compare later VB max count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        if later_program_fail_VB_max_count_new != self.later_program_fail_VB_max_count + 1:
            logger.error('Compare later program fail VB max count failure.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

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
