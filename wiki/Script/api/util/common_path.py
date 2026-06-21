from os import makedirs, path
from datetime import datetime
from typing import Final

class CommonPath:
    ### ----- Fixed Location ------ ###
    root: Final[str] = path.abspath(__file__).split('Script')[0]
    ini: Final[str] = path.join(root, 'ini')
    tcsp: Final[str] = path.join(root, 'tcsp')
    report: Final[str] = path.join(root, 'report')
    ### ----- Location Decided by Caller ----- ###
    development_report: str = ''
    mp_tool: str = ''

    @staticmethod
    def init(port_num: int, ptn_name: str, dev_report_path: str, mp_tool_path: str) -> None:
        """
        Obtain member values
        """
        port_str = f'P{port_num}'
        CommonPath.development_report = dev_report_path
        CommonPath.mp_tool = mp_tool_path
        makedirs(CommonPath.development_report, exist_ok=True)
        