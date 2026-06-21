import inspect
from .._hal.exception import DLL_ERROR ,CommonLibErrorBase, error_data

if False:
    class _CommonLibMetaError(type):
        i = 0
        def __new__(mcs, clsname, bases, attrs):
            _CommonLibMetaError.i += 1
            return super().__new__(mcs, clsname, bases, attrs)


    class CommonLibBaseError(Exception):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.value: int | None = None

        @property
        def name(self):
            currframe = inspect.currentframe()
            if currframe is None:
                raise ValueError("frame not found")
            matchs = [name for name, instance in currframe.f_globals.items() if instance is type(self)]
            return matchs[0] if matchs else None
        
        def __str__(self):
            return f"[{self.name}]: " + super().__str__()
        

    _g_error_code_id: int = 0
    def error_code():
        global _g_error_code_id
        name = f"ErrorCode{_g_error_code_id}"
        t: type[CommonLibBaseError] = type(name, (CommonLibBaseError,), {})
        t.value = _g_error_code_id
        _g_error_code_id += 1
        return t

    #FW_ERROR = error_code()
    #L2_NODE_UNEXPECTED = error_code()
    #SYSTEM_BLOCK_ERROR = error_code()
    #WRONG_PARAMETER = error_code()


# -----------------------------
# pylint: disable=invalid-name
# The exceptions here are treated as error code, which should follow the naming convension of enum.
# -----------------------------

#class CommonLibErrorBase(Exception): pass

# Auxiliary
class WRONG_PARAMETER(CommonLibErrorBase): pass

# HW
class DUT_NOT_DETECT(CommonLibErrorBase): pass
class POWER_SHORT(CommonLibErrorBase): pass
class USB_RESET(CommonLibErrorBase): pass
# CMD fail
class CMD_R1B_TIMEOUT(CommonLibErrorBase): pass
class CMD_AND_WAIT_TRANS_STATE_ERROR(CommonLibErrorBase): pass
class CMD_CRC7_ERROR(CommonLibErrorBase): pass
class CMD_NO_RESP(CommonLibErrorBase): pass
class CMD_INDEX_OF_R2R3_ERROR(CommonLibErrorBase): pass
class CMD1_NO_RESP(CommonLibErrorBase): pass
class CMD_RESP_ERROR(CommonLibErrorBase): pass
class CMD1_TIMEOUT(CommonLibErrorBase): pass
class CMD8_ERROR(CommonLibErrorBase): pass

# Exception raised if DLL return value != 0
#class DLL_ERROR(CommonLibErrorBase): pass

# DME
class INVALID_MIB_ATTRIBUTE(DLL_ERROR): pass
class INVALID_MIB_ATTRIBUTE_VALUE(DLL_ERROR): pass
class READ_ONLY_MIB_ATTRIBUTE(DLL_ERROR): pass
class WRITE_ONLY_MIB_ATTRIBUTE(DLL_ERROR): pass
class BAD_INDEX(DLL_ERROR): pass
class LOCKED_MIB_ATTRIBUTE(DLL_ERROR): pass
class BAD_TEST_FEATURE_INDEX(DLL_ERROR): pass
class PEER_COMMUNICATION_FAILURE(DLL_ERROR): pass
class BUSY(DLL_ERROR): pass
class DME_FAILURE(DLL_ERROR): pass

# Major Error Code
class DLL_PASS(DLL_ERROR): pass
class DLL_SET_PURGE_STATUS_ATTRIBUTE_FAIL(DLL_ERROR): pass
class DLL_READ_PURGE_STATUS_ATTRIBUTE_FAIL(DLL_ERROR): pass
class DLL_WAIT_PURGE_STATUS_IDLE_TIMEOUT(DLL_ERROR): pass
class DLL_CTRL_CTAG_ERROR(DLL_ERROR): pass
class DLL_CTRL_VALID_BITMAP_ERROR(DLL_ERROR): pass
class DLL_CTRL_LCA_ERROR(DLL_ERROR): pass
class DLL_CTRL_TX_E3D4K_ERROR(DLL_ERROR): pass
class DLL_CTRL_AXI_RRESP_ERROR(DLL_ERROR): pass
class DLL_CTRL_VALIDATE_ERROR(DLL_ERROR): pass
class DLL_CTRL_AXI_BRESP_ERROR(DLL_ERROR): pass
class DLL_CTRL_RX_ERROR1(DLL_ERROR): pass
class DLL_CTRL_RX_ERROR2(DLL_ERROR): pass
class DLL_CTRL_RX_ERROR3(DLL_ERROR): pass
class DLL_CTRL_RX_ERROR4(DLL_ERROR): pass
class DLL_CTRL_RX_ERROR5(DLL_ERROR): pass
class DLL_CTRL_RX_ERROR6(DLL_ERROR): pass
class DLL_CTRL_RX_ERROR7(DLL_ERROR): pass
class DLL_USB_RESET(DLL_ERROR): pass
class DLL_NO_CARD_ISSUE(DLL_ERROR): pass
class DLL_TYPE_ERROR(DLL_ERROR): pass
class DLL_TIMEOUT(DLL_ERROR): pass
class DLL_STATUS_FAIL(DLL_ERROR): pass
class DLL_REJECT(DLL_ERROR): pass
class DLL_TASK_RESPONSE(DLL_ERROR): pass
class DLL_PATTERN_ERROR(DLL_ERROR): pass
class DLL_PATTERN_2_ERROR(DLL_ERROR): pass
class DLL_EXCEPTION(DLL_ERROR): pass
class DLL_UM_ERR(DLL_ERROR): pass
class DLL_CTRL_ERROR(DLL_ERROR): pass
class DLL_CTRL_ERR(DLL_ERROR): pass
class DLL_RESPONSE_ERROR(DLL_ERROR): pass
class DLL_POWER_CYCLE(DLL_ERROR): pass
class DLL_START_STOP_ERROR(DLL_ERROR): pass 
class DLL_CMD_FIFO_FULL(DLL_ERROR): pass
class DLL_FW_EXCEPTION(DLL_ERROR): pass
class DLL_CRC32_COMPARE_FAIL(DLL_ERROR): pass
class DLL_CMD_SEQ_SCRIPT_ERROR(DLL_ERROR): pass
class DLL_CMD_SEQ_DOUT_ERROR(DLL_ERROR): pass 
class DLL_CMD_SEQ_RESPONSE_CHECK_FAIL(DLL_ERROR): pass
class DLL_HPB_FUNCTION_ERROR1(DLL_ERROR): pass
class DLL_HPB_FUNCTION_ERROR2(DLL_ERROR): pass
class DLL_HPB_MANUAL_UPDATE_TABLE_ERROR(DLL_ERROR): pass
class DLL_CMD_SEQ_DIN_ERROR(DLL_ERROR): pass
class DLL_CLEAR_DONE_QUEUE_FAIL(DLL_ERROR): pass
class DLL_DMA_ERROR(DLL_ERROR): pass
class DLL_BG_ERROR_RETRYCNT(DLL_ERROR): pass
class DLL_TESTER_SOFT_RESET_FAIL(DLL_ERROR): pass
class DLL_BKOPS_POR(DLL_ERROR): pass
class DLL_OUT_OF_TRANSFER_LENGTH(DLL_ERROR): pass
class DLL_TIMEOUT_SETTING_ERROR(DLL_ERROR): pass
class DLL_DATA_OVER_SIZE(DLL_ERROR): pass
class DLL_CRC32_COMPARE_ERROR(DLL_ERROR): pass
class DLL_HW_COMPARE_ERROR(DLL_ERROR): pass
class DLL_DBUF_OVER_SIZE(DLL_ERROR): pass
class DLL_UFS_HOST_CTRL_INFO_ERROR(DLL_ERROR): pass
class DLL_H8_SDU_NOP_OUT_FAIL(DLL_ERROR): pass
class DLL_CMD_SEQ_FEATURE_ERROR(DLL_ERROR): pass

# CMD SEQ Feature Error Code
class POWER_CYCLING_FAIL(DLL_ERROR): pass
class SWITCH_VOLTAGE_FAIL(DLL_ERROR): pass
class SWITCH_REFERENCE_CLOCK_FAIL(DLL_ERROR): pass
class SPEED_CHANGE_FAIL(DLL_ERROR): pass
class INITIAL_FLOW_FAIL(DLL_ERROR): pass
class TRIGGER_GPIO(DLL_ERROR): pass
class HIBERNATE(DLL_ERROR): pass
class TEST_UNIT_READY(DLL_ERROR): pass
class POWER_CONTROL(DLL_ERROR): pass
class READY_DEVICE_INIT_FLAG(DLL_ERROR): pass
class PUSH_NOP_OUT_AND_POLLING_NOP_IN(DLL_ERROR): pass

# Exception Error Code REF
class G_XFER_OUT_OF_RANGE(DLL_ERROR): pass
class G_RX_SEG_LEN_ERR(DLL_ERROR): pass
class G_RSP_NEQ_DONEQ(DLL_ERROR): pass
class G_INVALID_TRANS_TYPE(DLL_ERROR): pass
class G_HDR_LEN_ERR(DLL_ERROR): pass
class G_TIMEOUT_ALL(DLL_ERROR): pass
class FW_TIMEOUT_FAIL(DLL_ERROR): pass

# ErrorCode = 0x88
class CMD_LEVEL_TIMEOUT(DLL_ERROR): pass
class FW_TIMEOUT(DLL_ERROR): pass
class PERFORMANCE_IDLE_TIMEOUT(DLL_ERROR): pass

# others
class OOR_ISSUE(DLL_ERROR): pass