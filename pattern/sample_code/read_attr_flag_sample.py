import package_root
from typing import cast
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.info('push to cmd list, cmd gap would be lower')
        read_attr = ExecuteCMD.ReadAttribute().assign(idn=api.AttributeIDN.REF_CLK_FREQ).enqueue()
        set_flag = ExecuteCMD.SetFlag().assign(idn=api.FlagIDN.WRITEBOOSTER_EN).enqueue()
        read_flag = ExecuteCMD.ReadFlag().assign(idn=api.FlagIDN.WRITEBOOSTER_EN).enqueue()
        clear_flag = ExecuteCMD.ClearFlag().assign(idn=api.FlagIDN.WRITEBOOSTER_EN).enqueue()
        ExecuteCMD.send(clear_on_success=False)

        rsp = cast(api.QueryResponse, ExecuteCMD.read_response(read_attr))
        idn, index, selector, val = api.parse_read_attr_rsp(rsp)
        logger.info(f'{idn=},{index=},{selector=},{val=}')

        rsp = cast(api.QueryResponse, ExecuteCMD.read_response(set_flag))
        idn, index, selector, val = api.parse_flag_rsp(rsp)
        logger.info(f'{idn=},{index=},{selector=},{val=}')

        rsp = cast(api.QueryResponse, ExecuteCMD.read_response(read_flag))
        idn, index, selector, val = api.parse_flag_rsp(rsp)
        logger.info(f'{idn=},{index=},{selector=},{val=}')

        rsp = cast(api.QueryResponse, ExecuteCMD.read_response(clear_flag))
        idn, index, selector, val = api.parse_flag_rsp(rsp)
        logger.info(f'{idn=},{index=},{selector=},{val=}')
        ExecuteCMD.clear()

    def step2(self) -> None:
        logger.info('api send cmd directly (but cmd gap would be bigger)')
        api.write_attribute(idn=api.AttributeIDN.BOOT_LUN_EN, val=api.BootLUNID.BOOT_LUN_A)
        api.read_attribute(idn=api.AttributeIDN.BOOT_LUN_EN)
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.read_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.toggle_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()