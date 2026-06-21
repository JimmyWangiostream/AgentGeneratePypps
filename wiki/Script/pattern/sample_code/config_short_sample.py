import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api.descriptors.configuration_desc.functions import print_config, push_write_config
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b2_conf_desc_continue = 1
        config_descs[0].units[0].l4_num_alloc_units -= 4

        # config lun8, 16, 24 to have 1AU
        for i in range(1, 4):
            config_descs[i].header.b2_conf_desc_continue = 1
            config_descs[i].units[0].b0_lu_enable = 1
            config_descs[i].units[0].l4_num_alloc_units = 1
            config_descs[i].units[0].b9_logical_block_size = 0xc
        config_descs[3].header.b2_conf_desc_continue = 0

        for i in range(4):
            push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()

        config_descs = api.get_config_descriptors(print=True)


        # only print out specific index
        print_config(config_descs[0], index=0)

    def post_process(self) -> None:
        pass

run = Pattern().run
if __name__ == "__main__":
    run()