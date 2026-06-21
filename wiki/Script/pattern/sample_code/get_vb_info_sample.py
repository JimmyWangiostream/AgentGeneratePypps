import package_root
from Script import api, project_api
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):

    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        vb_info_api = project_api.create_get_vb_info()

        # access vb info fields #
        vb_info = vb_info_api.get_info()
        logger.info(f'vb0 group = {vb_info[0].group.value}')

        # valid count of vb #
        valid_cnts = vb_info_api.get_valid_count(access_vendor=False)
        logger.info(f'vb0 valid count = {valid_cnts[0]}')
        
        # vb remap #
        remaps = vb_info_api.get_remap_table(access_vendor=False)
        logger.info(f'vb0 remap to vb{remaps[0]}')

        # vb group size #
        grp_sizes = vb_info_api.get_group_size(access_vendor=False)
        logger.info(f'Group size of {project_api.VB_GROUP.USED_BLK_POOL_MLC.name}({project_api.VB_GROUP.USED_BLK_POOL_MLC}) = {grp_sizes[project_api.VB_GROUP.USED_BLK_POOL_MLC]}')

        # print vb #
        vb_info_api.show(access_vendor=False)

        # only print vb that valid count is not zero #
        vb_info_api.show(print_valid_cnt_zero_vb=False, access_vendor=False)

        # dump vb #
        vb_info_api.dumpfile(access_vendor=False)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
