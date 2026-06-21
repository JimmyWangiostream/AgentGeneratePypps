from abc import ABC, abstractmethod
import struct
import bitstruct
import csv
import os
# from Script.api.struct_helper import *

class UserModeTimeOut():
    def __init__(self) -> None:
        self.cmd_total_time_write = 0
        self.cmd_total_time_read = 0
        self.cmd_total_time_erase = 0
        self.cmd_total_time_write = 0
        self.cmd_total_time_read = 0
        self.cmd_total_time_erase = 0
        self.cmd_total_time_discard = 0
        self.cmd_total_time_format_unit = 0
        self.cmd_total_time_purge = 0
        self.cmd_total_time_purge_kic = 0
        self.cmd_total_time_purge_kic_logical = 0
        self.cmd_total_time_purge_perf_precondition = 0
        self.cmd_total_time_vendor_readwrite = 0
        self.cmd_total_time_nop_out = 0
        self.cmd_total_time_boot_wlu_ready = 0
        self.cmd_total_time_device_ready_w_boot = 0
        self.cmd_total_time_device_ready_wo_boot = 0
        self.cmd_total_time_device_ready_wo_boot_spor = 0
        self.cmd_total_time_device_ready_after_lu_cong = 0
        self.cmd_total_time_test_unit_ready = 0
        self.cmd_total_time_security_protocol_out = 0
        self.cmd_total_time_security_protocol_in = 0
        self.cmd_total_time_write_flag = 0
        self.cmd_total_time_read_flag = 0
        self.cmd_total_time_write_attribute = 0
        self.cmd_total_time_read_attribute = 0
        self.cmd_total_time_set_desc = 0
        self.cmd_total_time_get_desc = 0
        self.cmd_total_time_ssu_start_unit = 0
        self.cmd_total_time_ssu_stop_unit = 0
        self.cmd_total_time_ssu_sleep = 0
        self.cmd_total_time_ssu_powerdown = 0
        self.cmd_total_time_ssu_active = 0
        self.cmd_total_time_ssu_sleep_vccoff_2_active = 0
        self.cmd_total_time_ssu_sleep_2_active = 0
        self.cmd_total_time_ssu_powerdown_2_active = 0
        self.cmd_total_time_abort_task = 0
        self.cmd_total_time_abort_task_set = 0
        self.cmd_total_time_clear_task_set = 0
        self.cmd_total_time_lu_reset = 0
        self.cmd_total_time_query_task = 0
        self.cmd_total_time_query_task_set = 0
        self.cmd_total_time_inquiry = 0
        self.cmd_total_time_write_buffer = 0
        self.cmd_total_time_read_buffer = 0
        self.cmd_total_time_verify_10 = 0
        self.cmd_total_time_pre_fetch = 0
        self.cmd_total_time_mode_sense = 0
        self.cmd_total_time_sync_cache = 0
        self.cmd_total_time_mode_select = 0
        self.cmd_total_time_report_luns = 0
        self.cmd_total_time_readcapacity = 0
        self.cmd_total_time_request_sense = 0
        self.cmd_total_time_send_diagnostic = 0
        self.cmd_total_time_group_read_write = 0
        self.cmd_total_time_hibernateenter = 0
        self.cmd_total_time_hibernateexit = 0
        self.cmd_total_time_linkstartup = 0
        self.cmd_total_time_fdev_init_timeout = 0
        self.cmd_total_time_fdev_init_afterspor = 0
        self.cmd_total_time_fbarrier = 0
        self.cmd_total_time_after_por_ssu_timeout = 0
        self.cmd_total_time_platform_criteria_ssu_timeout = 0
        self.cmd_total_time_exe_cmd_timeout = 0
        self.specific_case_maxwritechunksizewhenqdfull = 0
        self.specific_case_linkstartupaftersoftrestsporwhenwb = 0
        self.specific_case_getgcinfovu = 0
        self.specific_case_testunitreadyafterinitflowwhengc = 0
        self.specific_case_force_refresh = 0
        self.specific_case_firstwriteafterspor = 0
        self.cmd_max_busy_time_write_busy = 0
        self.cmd_max_busy_time_read_busy = 0
        self.cmd_max_busy_time_write_buffer_busy = 0
        self.cmd_max_busy_time_read_buffer_busy = 0
        self.cmd_max_busy_time_sec_protocol_out_busy = 0
        self.cmd_max_busy_time_sec_protocol_in_busy = 0
        self.cmd_max_busy_time_unmap_busy = 0
        self.sdk_dcmd13_timeout_standard_cmd_timeout = 0
        self.sdk_dcmd13_timeout_vendor_cmd_timeout = 0
        self.sdk_dcmd13_timeout_group_rw_timeout = 0
        self.sdk_dcmd13_timeout_nop_out_timeout = 0
        self.sdk_dcmd13_timeout_hiber_enter_timeout = 0
        self.sdk_dcmd13_timeout_hiber_exit_timeout = 0
        self.sdk_dcmd13_timeout_link_start_up_timeout = 0
        self.sdk_dcmd13_timeout_pwr_mode_chg_timeout = 0
        self.sdk_dcmd13_timeout_current_timeout = 0
        self.sdk_dcmd13_timeout_1st_read_lun_ready_timeout = 0
        self.sdk_dcmd13_timeout_boot_lun_ready_timeout = 0
        self.sdk_dcmd13_timeout_fdev_init_timeout = 0
        self.sdk_dcmd13_timeout_rstn_afterpwrreset_delay = 0
        self.sdk_dcmd13_timeout_rstn_sendkey_timeout = 0
        self.sdk_dcmd13_timeout_rstn_authcmd_timeout = 0
        self.sdk_dcmd13_timeout_rstn_authdata_timeout = 0
        self.sdk_dcmd13_timeout_ssu_timeout = 0
        self.sdk_dcmd13_timeout_dcmd10_process1_timeout = 0
        self.sdk_dcmd13_timeout_hpb_reset_timeout = 0
        self.sdk_dcmd13_timeout_linkstart_poweronreq_timeout = 0
        self.sdk_dcmd13_timeout_linkstart_resetreq_timeout = 0
        self.sdk_dcmd13_timeout_linkstart_enableeq_timeout = 0
        self.sdk_dcmd13_timeout_linkstart_linkupreq_timeout = 0
        self.sdk_dcmd13_timeout_linkstartup_hwlinkup_polling_timeout = 0
        self.sdk_dcmd13_timeout_all_timeout_multiplenum = 0

    def read_timeout_setting_form_csv(self, project_name: str) -> None:

        target_path = os.path.abspath(os.path.join(__file__, '..'))

        file_path = os.path.join(target_path, 'UserMode.csv')

        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            
            header = next(csv_reader)

            col_idx = 0
            target_col = 0
            default_col = 0

            for cell in header:
                if cell == project_name:
                    target_col = col_idx
                    break
                elif cell == "default":
                    default_col = col_idx

                col_idx += 1

            # 沒找到專案，用default欄
            if target_col == 0:
                target_col = default_col

            # 建立欄位對應關係
            field_mapping = {
                "Cmd_Total_Time.Write": "cmd_total_time_write",
                "Cmd_Total_Time.Read": "cmd_total_time_read",
                "Cmd_Total_Time.Erase": "cmd_total_time_erase",
                "Cmd_Total_Time.Discard": "cmd_total_time_discard",
                "Cmd_Total_Time.Format_Unit": "cmd_total_time_format_unit",
                "Cmd_Total_Time.Purge": "cmd_total_time_purge",
                "Cmd_Total_Time.Purge_KIC": "cmd_total_time_purge_kic",
                "Cmd_Total_Time.Purge_KIC_Logical": "cmd_total_time_purge_kic_logical",
                "Cmd_Total_Time.Purge_Perf_precondition": "cmd_total_time_purge_perf_precondition",
                "Cmd_Total_Time.Vendor_ReadWrite": "cmd_total_time_vendor_readwrite",
                "Cmd_Total_Time.Nop_Out": "cmd_total_time_nop_out",
                "Cmd_Total_Time.Boot_WLU_Ready": "cmd_total_time_boot_wlu_ready",
                "Cmd_Total_Time.Device_Ready_W_Boot": "cmd_total_time_device_ready_w_boot",
                "Cmd_Total_Time.Device_Ready_WO_Boot": "cmd_total_time_device_ready_wo_boot",
                "Cmd_Total_Time.Device_Ready_WO_Boot_SPOR": "cmd_total_time_device_ready_wo_boot_spor",
                "Cmd_Total_Time.Device_Ready_After_LU_Cong": "cmd_total_time_device_ready_after_lu_cong",
                "Cmd_Total_Time.Test_Unit_Ready": "cmd_total_time_test_unit_ready",
                "Cmd_Total_Time.Security_Protocol_Out": "cmd_total_time_security_protocol_out",
                "Cmd_Total_Time.Security_Protocol_In": "cmd_total_time_security_protocol_in",
                "Cmd_Total_Time.Write_Flag": "cmd_total_time_write_flag",
                "Cmd_Total_Time.Read_Flag": "cmd_total_time_read_flag",
                "Cmd_Total_Time.Write_Attribute": "cmd_total_time_write_attribute",
                "Cmd_Total_Time.Read_Attribute": "cmd_total_time_read_attribute",
                "Cmd_Total_Time.Set_Desc": "cmd_total_time_set_desc",
                "Cmd_Total_Time.Get_Desc": "cmd_total_time_get_desc",
                "Cmd_Total_Time.SSU_Start_Unit": "cmd_total_time_ssu_start_unit",
                "Cmd_Total_Time.SSU_Stop_Unit": "cmd_total_time_ssu_stop_unit",
                "Cmd_Total_Time.SSU_Sleep": "cmd_total_time_ssu_sleep",
                "Cmd_Total_Time.SSU_PowerDown": "cmd_total_time_ssu_powerdown",
                "Cmd_Total_Time.SSU_Active": "cmd_total_time_ssu_active",
                "Cmd_Total_Time.SSU_Sleep_VccOff_2_Active": "cmd_total_time_ssu_sleep_vccoff_2_active",
                "Cmd_Total_Time.SSU_Sleep_2_Active": "cmd_total_time_ssu_sleep_2_active",
                "Cmd_Total_Time.SSU_PowerDown_2_Active": "cmd_total_time_ssu_powerdown_2_active",
                "Cmd_Total_Time.Abort_Task": "cmd_total_time_abort_task",
                "Cmd_Total_Time.Abort_Task_Set": "cmd_total_time_abort_task_set",
                "Cmd_Total_Time.Clear_Task_Set": "cmd_total_time_clear_task_set",
                "Cmd_Total_Time.LU_Reset": "cmd_total_time_lu_reset",
                "Cmd_Total_Time.Query_Task": "cmd_total_time_query_task",
                "Cmd_Total_Time.Query_Task_Set": "cmd_total_time_query_task_set",
                "Cmd_Total_Time.Inquiry": "cmd_total_time_inquiry",
                "Cmd_Total_Time.Write_Buffer": "cmd_total_time_write_buffer",
                "Cmd_Total_Time.Read_Buffer": "cmd_total_time_read_buffer",
                "Cmd_Total_Time.Verify_10": "cmd_total_time_verify_10",
                "Cmd_Total_Time.Pre_Fetch": "cmd_total_time_pre_fetch",
                "Cmd_Total_Time.Mode_Sense": "cmd_total_time_mode_sense",
                "Cmd_Total_Time.Sync_Cache": "cmd_total_time_sync_cache",
                "Cmd_Total_Time.Mode_Select": "cmd_total_time_mode_select",
                "Cmd_Total_Time.Report_Luns": "cmd_total_time_report_luns",
                "Cmd_Total_Time.ReadCapacity": "cmd_total_time_readcapacity",
                "Cmd_Total_Time.Request_Sense": "cmd_total_time_request_sense",
                "Cmd_Total_Time.SEND_DIAGNOSTIC": "cmd_total_time_send_diagnostic",
                "Cmd_Total_Time.Group_Read_Write": "cmd_total_time_group_read_write",
                "Cmd_Total_Time.HibernateEnter": "cmd_total_time_hibernateenter",
                "Cmd_Total_Time.HibernateExit": "cmd_total_time_hibernateexit",
                "Cmd_Total_Time.LinkStartup": "cmd_total_time_linkstartup",
                "Cmd_Total_Time.fDev_Init_Timeout": "cmd_total_time_fdev_init_timeout",
                "Cmd_Total_Time.fDev_Init_AfterSPOR": "cmd_total_time_fdev_init_afterspor",
                "Cmd_Total_Time.Fbarrier": "cmd_total_time_fbarrier",
                "Cmd_Total_Time.After_POR_SSU_Timeout": "cmd_total_time_after_por_ssu_timeout",
                "Cmd_Total_Time.Platform_Criteria_SSU_Timeout": "cmd_total_time_platform_criteria_ssu_timeout",
                "Cmd_Total_Time.Exe_Cmd_Timeout": "cmd_total_time_exe_cmd_timeout",
                "Specific_Case.MaxWriteChunkSizeWhenQDFull": "specific_case_maxwritechunksizewhenqdfull",
                "Specific_Case.LinkStartupAfterSoftRestSPORWhenWB": "specific_case_linkstartupaftersoftrestsporwhenwb",
                "Specific_Case.GetGCInfoVU": "specific_case_getgcinfovu",
                "Specific_Case.TestUnitReadyAfterInitFlowWhenGC": "specific_case_testunitreadyafterinitflowwhengc",
                "Specific_Case.Force_Refresh": "specific_case_force_refresh",
                "Specific_Case.FirstWriteAfterSPOR": "specific_case_firstwriteafterspor",
                "Cmd_Max_Busy_Time.Write_Busy": "cmd_max_busy_time_write_busy",
                "Cmd_Max_Busy_Time.Read_Busy": "cmd_max_busy_time_read_busy",
                "Cmd_Max_Busy_Time.Write_Buffer_Busy": "cmd_max_busy_time_write_buffer_busy",
                "Cmd_Max_Busy_Time.Read_Buffer_Busy": "cmd_max_busy_time_read_buffer_busy",
                "Cmd_Max_Busy_Time.Sec_Protocol_Out_Busy": "cmd_max_busy_time_sec_protocol_out_busy",
                "Cmd_Max_Busy_Time.Sec_Protocol_In_Busy": "cmd_max_busy_time_sec_protocol_in_busy",
                "Cmd_Max_Busy_Time.Unmap_Busy": "cmd_max_busy_time_unmap_busy",
                "SDK_DCMD13_Timeout.Standard_Cmd_Timeout": "sdk_dcmd13_timeout_standard_cmd_timeout",
                "SDK_DCMD13_Timeout.Vendor_CMD_Timeout": "sdk_dcmd13_timeout_vendor_cmd_timeout",
                "SDK_DCMD13_Timeout.GROUP_RW_Timeout": "sdk_dcmd13_timeout_group_rw_timeout",
                "SDK_DCMD13_Timeout.NOP_OUT_Timeout": "sdk_dcmd13_timeout_nop_out_timeout",
                "SDK_DCMD13_Timeout.Hiber_Enter_Timeout": "sdk_dcmd13_timeout_hiber_enter_timeout",
                "SDK_DCMD13_Timeout.Hiber_Exit_Timeout": "sdk_dcmd13_timeout_hiber_exit_timeout",
                "SDK_DCMD13_Timeout.Link_Start_Up_Timeout": "sdk_dcmd13_timeout_link_start_up_timeout",
                "SDK_DCMD13_Timeout.Pwr_Mode_Chg_Timeout": "sdk_dcmd13_timeout_pwr_mode_chg_timeout",
                "SDK_DCMD13_Timeout.Current_Timeout": "sdk_dcmd13_timeout_current_timeout",
                "SDK_DCMD13_Timeout.1st_Read_LUN_Ready_Timeout": "sdk_dcmd13_timeout_1st_read_lun_ready_timeout",
                "SDK_DCMD13_Timeout.Boot_LUN_Ready_Timeout": "sdk_dcmd13_timeout_boot_lun_ready_timeout",
                "SDK_DCMD13_Timeout.fDev_Init_Timeout": "sdk_dcmd13_timeout_fdev_init_timeout",
                "SDK_DCMD13_Timeout.RSTn_AfterPwrReset_Delay": "sdk_dcmd13_timeout_rstn_afterpwrreset_delay",
                "SDK_DCMD13_Timeout.RSTn_SendKey_Timeout": "sdk_dcmd13_timeout_rstn_sendkey_timeout",
                "SDK_DCMD13_Timeout.RSTn_AuthCMD_Timeout": "sdk_dcmd13_timeout_rstn_authcmd_timeout",
                "SDK_DCMD13_Timeout.RSTn_AuthData_Timeout": "sdk_dcmd13_timeout_rstn_authdata_timeout",
                "SDK_DCMD13_Timeout.SSU_Timeout": "sdk_dcmd13_timeout_ssu_timeout",
                "SDK_DCMD13_Timeout.DCMD10_process1_timeout": "sdk_dcmd13_timeout_dcmd10_process1_timeout",
                "SDK_DCMD13_Timeout.HPB_reset_timeout": "sdk_dcmd13_timeout_hpb_reset_timeout",
                "SDK_DCMD13_Timeout.LinkStart_PowerOnREQ_Timeout": "sdk_dcmd13_timeout_linkstart_poweronreq_timeout",
                "SDK_DCMD13_Timeout.LinkStart_ResetREQ_Timeout": "sdk_dcmd13_timeout_linkstart_resetreq_timeout",
                "SDK_DCMD13_Timeout.LinkStart_EnableEQ_Timeout": "sdk_dcmd13_timeout_linkstart_enableeq_timeout",
                "SDK_DCMD13_Timeout.LinkStart_LinkUpREQ_Timeout": "sdk_dcmd13_timeout_linkstart_linkupreq_timeout",
                "SDK_DCMD13_Timeout.LinkStartUp_HWLinkup_Polling_Timeout": "sdk_dcmd13_timeout_linkstartup_hwlinkup_polling_timeout",
                "SDK_DCMD13_Timeout.All_Timeout_MultipleNum": "sdk_dcmd13_timeout_all_timeout_multiplenum"
            }        

            for row in csv_reader:
                row_name = row[0]  # 第一欄是名稱
                row_value = row[target_col]  # 目標欄位的值

                # 根據名稱對應到結構體參數
                if row_name in field_mapping:
                    field_name = field_mapping[row_name]
                    setattr(usermode_timeout, field_name, int(row_value)*1000)
    
    from Script.api.cmd_seq.protocols import IsCmdUpiuEntry

    def set_cmd_timeout(self, cmd: IsCmdUpiuEntry) -> None:
        from Script.api.cmd_seq.cmds import Write6, Write10, Write16

        if isinstance(cmd, (Write6, Write10, Write16)):
            cmd.param.l50_timeout = usermode_timeout.cmd_total_time_write

usermode_timeout = UserModeTimeOut()



