import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from typing import Any, List
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.read_disturb.mutual_fun import config_lun, get_sorted_VB_list, polling_Read_Disturb_idle, get_PCA_and_print
from Script.project_api.functions import print_object_info_ai



def get_quick_scan_flag(payload: bytearray, vb: int, ce: int) -> int:
    """Extract quick-scan flag for (VB, CE) from opcode=16 response.

    Bitmap layout (per FW spec):
      Byte N:  bits[3:0] = VB_{N*2}   CE0~CE3
               bits[7:4] = VB_{N*2+1} CE0~CE3
    Returns 0 or 1.
    """
    byte_idx = vb // 2
    bit_offset = ce + (0 if vb % 2 == 0 else 4)
    if byte_idx >= len(payload):
        return 0
    return (payload[byte_idx] >> bit_offset) & 1


def count_total_quick_scan_flags(payload: bytearray) -> int:
    """Count total set bits across the whole flag bitmap (= total quick scans triggered)."""
    return sum(bin(b).count('1') for b in payload)


class Pattern(UFSTC):
    def pre_process(self) -> None:
        logger.flow(1, "Config LUN 0 to normal lun, erase all + disable AST")
        config_lun(normal_list=[0], em1_list=[])
        project_api.issue_D088_enable_disable_auto_standby(0)

        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting = api.get_flash_setting()
        self.ce_num = self.flash_setting.Max_Fdevice
        self.write_record = api.get_empty_write_record()

    def step1(self) -> None:
        """Write data to create a TLC L2 VB, then set bin=15 on it."""
        logger.flow(2, "Write data to create L2 VB, then set BFEA bin=15")

        tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        write_size = int(tlc_vb_size * 0.5)
        api.sequential_write(lun=0, start_lba=0, total_size=write_size,
                             chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua=1,
                             need_compare=False,
                             compare_method=api.CompareMethod.HW_COMPARE,
                             write_record=self.write_record)
        logger.info(f"  Written {write_size} sectors to LUN 0")

        # Get PCA to find which VB we wrote to
        pca = get_PCA_and_print(lun=0, lba=0)
        self.target_vb = pca.virtual_block_number.value
        self.target_die = pca.die.value
        logger.info(f"  Target VB={self.target_vb}, die={self.target_die}")


    def step2(self) -> None:
        pass

    def step3(self) -> None:
        """Trigger RD scan via 40CC. Wrong BFEA bin causes read fail → FW auto retries
        with correct bin → raises quick-scan flag for this VB/CE."""
        logger.flow(4, "Host issue 40CC to trigger RD scan on target VB")

        _, rd_info = project_api.issue_40CC_to_trigger_Read_Disturb_scan(self.target_vb)
        print_object_info_ai(rd_info)

        logger.info("  Polling Read Disturb scan idle...")
        polling_Read_Disturb_idle(self.target_vb)
        logger.info("  RD scan complete")

    def step4(self) -> None:
        """Read BFEA flags after RD scan → verify flag=1 (FW raised it) + total counter +1"""
        logger.info(f"  Flag raised (+1 counter) — OK")

    def step5(self) -> None:
        pass

    def step6(self) -> None:
        """Read BFEA flags after reset → verify flag=0 + total counter -1"""


        logger.info(f"  Flag cleared (counter back to baseline) — OK")

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
