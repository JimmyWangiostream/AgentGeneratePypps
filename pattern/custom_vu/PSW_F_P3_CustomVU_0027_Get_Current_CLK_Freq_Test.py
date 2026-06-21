import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from typing import cast
from Script.api import shared
from Script.api.ufs_api import *
from Script.api.cmd_seq import QueryResponse
from Script.api.ufs_api.vendor_cmd.structs import FwGeometry
from typing import Callable
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_data_in_vcmd


class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass
    def step1(self) -> None:
  
        logger.flow(1, 'Send VU 40EE Test')
        data = project_api.issue_40EE_to_get_current_clk_freq()

        logger.flow(2, 'Check clock tree group2 CPU (MHz) = 667')
        self.compare_value(data.clk_tree_grp2_cpu.value, 667)

        logger.flow(3, 'Check clock tree group3 BUF (system) (MHz) = 200')
        self.compare_value(data.clk_tree_grp3_buf.value, 200)

        logger.flow(4, 'Check clock tree group3 COP0 (MHz) = 200')
        self.compare_value(data.clk_tree_grp3_cop0.value, 200)

        logger.flow(5, 'Check domain 12 LDPC Dec clk (MHz) = 266')
        self.compare_value(data.domain_12_ldpc_dec_clk.value, 266)

        logger.flow(6, 'Check domain 13 LDPC Enc clk (MHz) = 266')
        self.compare_value(data.domain_13_ldpc_enc_clk.value,266)

        logger.flow(7, 'Check domain 15 ONFI PHY MDLL (MHz) = 1600')
        self.compare_value(data.domain_15_onfi_phy_mdll.value, 1600)

    def compare_value(self, value:int,expect_value:int) -> None:
        if value != expect_value:
            logger.error(f'Expect ={expect_value}, but = {value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'val = {value}')

    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()