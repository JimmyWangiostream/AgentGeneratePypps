from Script import api
from Script.project_api.structs import VbListFmt

def create_get_vb_info() -> api.GetVBInfo[VbListFmt]:
    return api.GetVBInfo(VbListFmt, 4)
