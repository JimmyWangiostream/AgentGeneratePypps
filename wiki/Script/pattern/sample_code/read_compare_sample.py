import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        write_record_1 = api.get_empty_write_record()

        ExecuteCMD.Write10().assign(lun=1, lba=1, length=3, fua=0).enqueue()
        ExecuteCMD.Write10().assign(lun=1, lba=2, length=100, fua=0).enqueue()
        ExecuteCMD.Unmap().assign(lun=1, lba=1, length=1).set_option(wait_queue_empty=True).enqueue()

        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, write_record_1)
        ExecuteCMD.clear()

        # Primary using hw compare and use crc cmp to unmapped zone
        api.read_compare(write_record_1, api.CompareMethod.HW_COMPARE)

        # all compare with crc
        api.read_compare(write_record_1, api.CompareMethod.SW_COMPARE)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()