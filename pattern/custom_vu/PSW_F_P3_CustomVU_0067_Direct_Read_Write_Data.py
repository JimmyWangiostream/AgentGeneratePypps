from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.api.ufs_api.defines.bit_define import *


class Pattern(UFSTC):
    def pre_process(self) -> None:
        flash_setting = get_flash_setting()
        self.max_die = flash_setting.Max_Fdevice
        self.max_plane = flash_setting.Plane_Per_Die
        pass

    def step1(self) -> None:
        logger.flow(1, 'Normal Test. (SLC mode, SLC page)')
        pattern_array = [0xABCDABCD, 0x5A5A5A5A, 0xA5A5A5A5, 0x12341234, 0x55AA55AA, 0xAA55AA55]
        MAX_PAGE = 1103

        block_start = 100
        block_end = 100

        pattern = pattern_array[0]

        for die in range(0, self.max_die):
            for plane in range(0, self.max_plane):
                logger.flow(2, 'Issue VU 40F6 to direct erase target block & CE & plane.')
                resp, data_erase = project_api.issue_40F6_to_erase_in_direct_nand_mode_1(BIT(die), BIT(plane), block_start, block_end, 1)

                for page in range(0, MAX_PAGE, 10):
                    page_start = page // 3 * 3
                    page_end = page_start + 2

                    logger.flow(3, 'Issue VU 40F7 to direct write target block & CE & plane.')
                    resp, data_write = project_api.issue_40F7_to_write_raw_data_in_direct_nand_mode(BIT(die), BIT(plane), block_start, block_end, page_start, page_end, 1, pattern)

                    logger.flow(4, 'Issue VU 40F8 to direct read target block & CE & plane.')
                    resp, data_read = project_api.issue_40F8_to_read_in_direct_nand_mode(BIT(die), BIT(plane), block_start, block_end, page_start, page_end, 1)

                    logger.flow(5, 'Compare direct write and read data.')
                    pattern_data = bytearray(pattern.to_bytes(4, 'little')) * 4096

                    for i in range(0, page_end - page_start + 1):
                        read_page = data_read[i * (16384 + 64): (i + 1) * 16384 + i * 64]

                        if pattern_data != read_page:
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass

    def step2(self) -> None:
        logger.flow(1, 'Normal Test. (TLC mode, SLC / MLC / TLC page)')
        pattern_array = [0xABCDABCD, 0x5A5A5A5A, 0xA5A5A5A5, 0x12341234, 0x55AA55AA, 0xAA55AA55]
        MAX_PAGE = 3311

        block_start = 100
        block_end = 100

        pattern = pattern_array[0]

        for die in range(0, self.max_die):
            for plane in range(0, self.max_plane):
                logger.flow(2, 'Issue VU 40F6 to direct erase target block & CE & plane.')
                resp, data_erase = project_api.issue_40F6_to_erase_in_direct_nand_mode_1(BIT(die), BIT(plane), block_start, block_end, 0)

                for page in range(0, MAX_PAGE, 10):
                    if 0 <= page < 1620:
                        page_start = page // 3 * 3
                        page_end = page_start + 2
                    elif 1620 <= page < 1652:
                        page_start = 1620 + (page - 1620) // 2 * 2
                        page_end = page_start + 1
                    elif 1652 <= page < 3308:
                        page_start = 1652 + (page - 1652) // 3 * 3
                        page_end = page_start + 2
                    elif 3308 <= page < 3312:
                        page_start = page
                        page_end = page_start

                    logger.flow(3, 'Issue VU 40F7 to direct write target block & CE & plane.')
                    resp, data_write = project_api.issue_40F7_to_write_raw_data_in_direct_nand_mode(BIT(die), BIT(plane), block_start, block_end, page_start, page_end, 0, pattern)

                    logger.flow(4, 'Issue VU 40F8 to direct read target block & CE & plane.')
                    resp, data_read = project_api.issue_40F8_to_read_in_direct_nand_mode(BIT(die), BIT(plane), block_start, block_end, page_start, page_end, 0)

                    logger.flow(5, 'Compare direct write and read data.')
                    pattern_data = bytearray(pattern.to_bytes(4, 'little')) * 4096

                    for i in range(0, page_end - page_start + 1):
                        read_page = data_read[i * (16384 + 64): (i + 1) * 16384 + i * 64]

                        if pattern_data != read_page:
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
