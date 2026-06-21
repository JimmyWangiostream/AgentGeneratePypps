from .exception import *

dme_error_code_table = {
    1: (INVALID_MIB_ATTRIBUTE, "Invalid MIB attribute"),
    2: (INVALID_MIB_ATTRIBUTE_VALUE, "Invalid MIB attribute value"),
    3: (READ_ONLY_MIB_ATTRIBUTE, "Read only MIB attribute"),
    4: (WRITE_ONLY_MIB_ATTRIBUTE, "Write only MIB attribute"),
    5: (BAD_INDEX, "Bad Index"),
    6: (LOCKED_MIB_ATTRIBUTE, "Locked MIB attribute"),
    7: (BAD_TEST_FEATURE_INDEX, "Bad test feature index"),
    8: (PEER_COMMUNICATION_FAILURE, "Peer communication failure"),
    9: (BUSY, "Busy"),
    10: (DME_FAILURE, "DME Failure")
}

major_error_codes = {
    0x00: (DLL_PASS, "Pass"),
    0x04: (DLL_SET_PURGE_STATUS_ATTRIBUTE_FAIL, "Enhance Performance set purge status attribute fail"),
    0x05: (DLL_READ_PURGE_STATUS_ATTRIBUTE_FAIL, "Enhance Performance read purge status attribute fail"),
    0x06: (DLL_WAIT_PURGE_STATUS_IDLE_TIMEOUT, "Enhance Performance wait purge status idle timeout (3600s)"),
    0x07: (DLL_CTRL_CTAG_ERROR, "CQ CTag & SQ CTag are not the same, V6 only"),
    0x08: (DLL_CTRL_VALID_BITMAP_ERROR, "SQ Data validation fail when aligned to 4K, V6 only"),
    0x09: (DLL_CTRL_LCA_ERROR, "CQ LCA & SQ LCA are not the same, V6 only"),
    0x0A: (DLL_CTRL_TX_E3D4K_ERROR, "E3D4K calculated by BMU & CQ E3D4k are not same, V6 only"),
    0x0B: (DLL_CTRL_AXI_RRESP_ERROR, "Allocate CQ DBUF Fail, V6 only"),
    0x0C: (DLL_CTRL_VALIDATE_ERROR, "CQ Data validation fail, V6 only"),
    0x0D: (DLL_CTRL_AXI_BRESP_ERROR, "Allocate SQ DBUF Fail, V6 only"),
    0x0E: (DLL_CTRL_RX_ERROR1, "RX_ERROR: (UPIU) Data Buffer Offset + Data Transfer Count > expect data length (Data In / RTT), V6 Only"),
    0x0F: (DLL_CTRL_RX_ERROR2, "RX_ERROR: (UPIU) Data_Segment_Length not match payload received (Data In), V6 Only"),
    0x10: (DLL_CTRL_RX_ERROR3, "RX_ERROR: rx command not match any command in done queue  (Task_Tag, LUN, IID), V6 Only"),
    0x11: (DLL_CTRL_RX_ERROR4, "RX_ERROR: Invalid Transaction_Type received     (TT unknown   /   RTT match READ command in done queue   /   DATA_IN match WRITE command in done queue), V6 Only"),
    0x12: (DLL_CTRL_RX_ERROR5, "RX_ERROR: rx command header length less than 32B, V6 Only"),
    0x13: (DLL_CTRL_RX_ERROR6, "RX_ERROR: receive rx command header without rx_eom when the rx command without data, V6 Only"),
    0x14: (DLL_CTRL_RX_ERROR7, "CTRL Unknown Error"),
    0x37: (DLL_USB_RESET, "USB Driver Reset, USB issue"),
    0x63: (DLL_NO_CARD_ISSUE, "Maybe the card is not properly placed or has poor contact."),
    0x81: (DLL_TYPE_ERROR, "None"),
    0x82: (DLL_TIMEOUT, "Not receive any response"),
    0x83: (DLL_STATUS_FAIL, "None"),
    0x84: (DLL_REJECT, "None"),
    0x85: (DLL_TASK_RESPONSE, "None"),
    0x86: (DLL_PATTERN_ERROR, "PTNG fail"),
    0x87: (DLL_PATTERN_2_ERROR, "HW compare fail"),
    0x88: (DLL_EXCEPTION, "Detail info refer Exception Error Code REF"),
    0x89: (DLL_UM_ERR, "None"),
    0x90: (DLL_CTRL_ERROR, "CQ CTRL Error"),
    0x8A: (DLL_RESPONSE_ERROR, "Receive response statue is not pass"),
    0x8B: (DLL_POWER_CYCLE, "SPOR occurred"),
    0x8C: (DLL_START_STOP_ERROR, "None"),
    0x8D: (DLL_CMD_FIFO_FULL, "maybe device is close rx, so host can’t send CMD to device"),
    0x8F: (DLL_FW_EXCEPTION, "None"),
    0x93: (DLL_CRC32_COMPARE_FAIL, "CMD SEQ compare CRC32 fail"),
    0x95: (DLL_CMD_SEQ_SCRIPT_ERROR, "CMD sequence list with illegal setting"),
    0x96: (DLL_CMD_SEQ_DOUT_ERROR, "Maybe entry option data in/out setting not correct"),
    0x97: (DLL_CMD_SEQ_RESPONSE_CHECK_FAIL, "Maybe CMD SEQ with TM CMD but option not active TM setting"),
    0x98: (DLL_HPB_FUNCTION_ERROR1, "Execute HPB error during CMD SEQ, dump HPB result to get detail info"),
    0x99: (DLL_HPB_FUNCTION_ERROR2, "Execute HPB error during performance, dump HPB result to get detail info"),
    0x9A: (DLL_HPB_MANUAL_UPDATE_TABLE_ERROR, "HPB manual update table fail, dump HPB result to get detail info"),
    0x9D: (DLL_CMD_SEQ_DIN_ERROR, "Maybe entry option data in/out setting not correct"),
    0x9E: (DLL_CLEAR_DONE_QUEUE_FAIL, "Tester HW issue"),
    0x9F: (DLL_DMA_ERROR, "Tester HW issue"),
    0xA0: (DLL_BG_ERROR_RETRYCNT, "GROUP_RW 當收到 RESP_UPIU 帶有 SCSI_Status_Task_Set_Full 則會進行 BG_RETRY，並且BG_ERROR_RETRYCNT++"),
    0xA1: (DLL_TESTER_SOFT_RESET_FAIL, "Tester HW issue"),
    0xA2: (DLL_BKOPS_POR, "BKOPS por occured"),
    0xA3: (DLL_OUT_OF_TRANSFER_LENGTH, "Transfer length out of range"),
    0xA4: (DLL_TIMEOUT_SETTING_ERROR, "Timeout setting overflow (> 0xFFFFFF)"),
    0xA5: (DLL_DATA_OVER_SIZE, "Data超出SDAM的上限"),
    0xA6: (DLL_CRC32_COMPARE_ERROR, "After CRC32 compare fail, clear Q timeout. (1s)"),
    0xA7: (DLL_HW_COMPARE_ERROR, "After HW compare fail, clear Q timeout. (1s)"),
    0xA8: (DLL_DBUF_OVER_SIZE, "Auto mode allocate memory > 64K (V6 Only)"),
    0xA9: (DLL_UFS_HOST_CTRL_INFO_ERROR, "UFS Host CTRL INFO Error (0x07 - 0x14)"),
    0xE6: (DLL_H8_SDU_NOP_OUT_FAIL, "NOP OUT Fail after H8 Exit when DCMD23 is active"),
    0xFF: (DLL_CMD_SEQ_FEATURE_ERROR, "Detail info refer CMD SEQ Feature Error Code")
}

pwr_cycle_codes = {
    0x00: (POWER_CYCLING_FAIL, "none"),
    0x01: (POWER_CYCLING_FAIL, "LinkStartUp fail , detail refer Unipro ERR Code & Other ERR Code"),
    0x0C: (POWER_CYCLING_FAIL, "EndPointReset Error"),
    0x0D: (POWER_CYCLING_FAIL, "Clear done queue timeout (1s)"),
    0x04: (POWER_CYCLING_FAIL, "Power cycle failed due to unknown reason"),
    0x07: (POWER_CYCLING_FAIL, "0x07, CTRL Error, V6 Only, refer UFS SDK Note 4 - Major Error Code"),
    0x08: (POWER_CYCLING_FAIL, "0x08, CTRL Error, V6 Only, refer UFS SDK Note 4 - Major Error Code"),
    0x09: (POWER_CYCLING_FAIL, "0x09, CTRL Error, V6 Only, refer UFS SDK Note 4 - Major Error Code"),
    0x10: (POWER_CYCLING_FAIL, "0x10, CTRL Error, V6 Only, refer UFS SDK Note 4 - Major Error Code"),
    0x11: (POWER_CYCLING_FAIL, "0x11, CTRL Error, V6 Only, refer UFS SDK Note 4 - Major Error Code"),
    0x12: (POWER_CYCLING_FAIL, "0x12, CTRL Error, V6 Only, refer UFS SDK Note 4 - Major Error Code"),
    0x13: (POWER_CYCLING_FAIL, "0x13, CTRL Error, V6 Only, refer UFS SDK Note 4 - Major Error Code"),
    0x14: (POWER_CYCLING_FAIL, "0x14, CTRL Error, V6 Only, refer UFS SDK Note 4 - Major Error Code")
}

switch_vltage_codes = {
    0x00: (SWITCH_VOLTAGE_FAIL, "Switch Voltage Fail (VCC)"),
    0x01: (SWITCH_VOLTAGE_FAIL, "Switch Voltage Fail (VCCQ)"),
    0x02: (SWITCH_VOLTAGE_FAIL, "Switch Voltage Fail (VCCQ2)"),
}

switch_ref_clk_codes = {
    0x03: (SWITCH_REFERENCE_CLOCK_FAIL, "Switch Reference Clock Fail")
}

spd_change_codes = {
    0x09: (SPEED_CHANGE_FAIL, "Speed Change Fail , detail refer Unipro ERR Code & Other ERR Code")
}

init_flow_codes = {
    0x01: (INITIAL_FLOW_FAIL, "LinkStartUp fail , detail refer Unipro ERR Code & Other ERR Code"),
    0x02: (INITIAL_FLOW_FAIL, "Nop out fail"),
    0x03: (INITIAL_FLOW_FAIL, "Set init flag fail"),
    0x04: (INITIAL_FLOW_FAIL, "Read init flag fail"),
    0x05: (INITIAL_FLOW_FAIL, "Read flag timeout(fix 5s, can not set manually)"),
}

triiger_gpio = {
    0x00: (TRIGGER_GPIO, "None")
}

hiber_codes = {
    0x0A: (HIBERNATE, "Hibernate enter fail"),
    0x0B: (HIBERNATE, "Hibernate exit fail")
}

test_unit_rdy_codes = {
    0x06: (TEST_UNIT_READY, "Test unit ready no response"),
    0x07: (TEST_UNIT_READY, "Test unit ready polling timeout, if timeout setting > 10s, would trigger bus idle timeou first")
}

pwr_ctrl_codes = {
    0x00: (POWER_CONTROL, "None")
}

rdy_dev_init_flag_codes = {
    0x02: (READY_DEVICE_INIT_FLAG, "Nop Out Timeout, if timeout setting > 10s, would trigger bus idle timeou first")
}

nop_out_nop_in_codes = {
    0x0B: (PUSH_NOP_OUT_AND_POLLING_NOP_IN, "Nop Out Timeout, if timeout setting > 10s, would trigger bus idle timeou first")
}

excep_error_code_ref = {
    0x01: (G_XFER_OUT_OF_RANGE, "Data buffer offset + data transfer count > Expected data length"),
    0x02: (G_RX_SEG_LEN_ERR, "RX Segment length not match payload received"),
    0x04: (G_RSP_NEQ_DONEQ, "Response Mismatch (e.g. LUN or Task tag)"),
    0x08: (G_INVALID_TRANS_TYPE, "Invalid transaction type"),
    0x10: (G_HDR_LEN_ERR, "Header Length is less than 32Byte"),
    0x20: (G_TIMEOUT_ALL, "Timeout Occurred"),
    0x21: (CMD_LEVEL_TIMEOUT, "CMD Sequence CMD level timeout occured")
}

#not use now
exception_0x88 = {
    0x00: (PERFORMANCE_IDLE_TIMEOUT, "Performance timeout becasuse no cmd res over 8 mins"),
    0x21: (FW_TIMEOUT, "FW Timeout")
}