#pragma once

#ifdef VENDORCMD_EXPORTS
#define VENDORCMD_API __declspec(dllexport)
#else
#define VENDORCMD_API __declspec(dllimport)
#endif

#ifdef __cplusplus
extern "C" {
#endif
	VENDORCMD_API void* CVendorCmd_Create(void);
	VENDORCMD_API void CVendorCmd_Delete(void* pVCmd);
#if defined(REMOTE_CERT) && defined(OPPO)
    VENDORCMD_API BYTE SDK_Auth_SetHosts(void* pVCmd, const char** host_list, size_t host_count);
#endif
    VENDORCMD_API void Get_Dll_Version(void* pVCmd, UCHAR* Version);
#ifdef KIC
    VENDORCMD_API BYTE Dll_CheckLicenseDate(void* pVCmd, DWORD* dwLicenseDay);

    VENDORCMD_API BYTE Dll_LocalLicenseCheck(void* pVCmd, DWORD* dwLicenseDay);
#endif

    VENDORCMD_API BYTE SetHandle(void* pVCmd, HANDLE hHWD, DWORD dwDrive);

#ifdef PPS_API
    VENDORCMD_API WORD GetHubInfo(void* pVCmd, char* pTesterID, WORD* pPort, WORD* pVID, WORD* pPID, WORD* pUsbVer, char* pHubID);
#endif

    VENDORCMD_API BYTE Dll_Initial(void* pVCmd, BYTE byDllVersionCheck);

    VENDORCMD_API BYTE HostInitial(void* pVCmd, BYTE Mode);

#ifdef FEATURE_UFS_40
    VENDORCMD_API BYTE Set_LinkStartup_Mode(void* pVCmd, BYTE byResetMode);
#endif

    VENDORCMD_API BYTE HostLinkStartup(void* pVCmd);

#if defined(PPS_API)
    VENDORCMD_API BYTE Send_Cmd(void* pVCmd, void* pHeader, void* pTran, void* Payload, DWORD dwPayloadLen, DWORD dwTimeOut, DWORD dwAction, DWORD dwPatternMode, DWORD dwPatternTag, DWORD dwSeed_H, DWORD dwSeed_L, BYTE byLBA4K_AddTag);
#else
    VENDORCMD_API BYTE Send_Cmd(void* pVCmd, void* pHeader, void* pTran, void* Payload, DWORD dwPayloadLen, DWORD dwTimeOut, DWORD dwAction, DWORD dwPatternMode, DWORD dwPatternTag, BYTE dwModeSelect_Check);
#endif
    VENDORCMD_API BYTE PowerChange(void* pVCmd, DWORD dwMode, DWORD dwGear, DWORD dwLane, DWORD dwHsRate, DWORD FC0ProtectionTimeOut, DWORD TC0ReplayTimeOut, DWORD AFC0ReqTimeOut, DWORD FC1ProtectionTimeOut, DWORD TC1ReplayTimeOut, DWORD AFC1ReqTimeOut);
    VENDORCMD_API BYTE DME_Set(void* pVCmd, DWORD dwAttrSetType, DWORD dwMIB_Val, DWORD dwSel, DWORD dwMIB_Attr, DWORD* apb_Result);
    VENDORCMD_API BYTE DME_Get(void* pVCmd, DWORD dwAttrSetType, DWORD dwSel, DWORD dwMIB_Attr, DWORD* apb_Result, DWORD* apl_Val);
    VENDORCMD_API BYTE HibernateEnter(void* pVCmd);
    VENDORCMD_API BYTE HibernateExit(void* pVCmd);

#ifdef EYE_DIAGRAM
    VENDORCMD_API BYTE MPHYEyeMonitor(void* pVCmd, MPHY_EYE_MONITOR_PARAM* pEMParam, MPHY_EYE_MONITOR_RESULT* pEMResult);
#endif
    VENDORCMD_API BYTE Reset_N(void* pVCmd, BYTE Option, DWORD dwDelayTime);
#ifdef FEATURE_PCSPMA
    VENDORCMD_API BYTE Read_DME_Reg(void* pVCmd, BYTE bySel, WORD* pwLength, BYTE* pbyReadData);
#endif
    VENDORCMD_API BYTE DataPayloadXfer(void* pVCmd, DWORD dwAction, BYTE* pbyDataBuf, DWORD dwDataLen);
    VENDORCMD_API BYTE Get_DevResp(void* pVCmd, BYTE* pbyResBuf);
    VENDORCMD_API BYTE DataInOutXfer(void* pVCmd, DWORD dwLUN, DWORD dwTaskTag, DWORD dwDataSegLen, DWORD dwBufOffset, DWORD dwDataCnt, DWORD dwSegCnt, DWORD dwRW, BYTE* pbyDataBuf, BYTE byIID);    
#if defined(PPS_API)
    VENDORCMD_API BYTE Get_HostInfo(void* pVCmd, BYTE* pbyDataBuf, BYTE byOperateFlag);
#else
    VENDORCMD_API BYTE Get_HostInfo(void* pVCmd, BYTE* pbyDataBuf);
#endif

#if !(defined(PPS_API) || defined(MICRON) || defined(KIC) || defined(XITC))
    VENDORCMD_API BYTE Get_HostFW_Info(void* pVCmd, BYTE byOption, BYTE* pbyResBuf);
#endif
#if defined(PPS_API)
    VENDORCMD_API BYTE Get_HostReg(void* pVCmd, BYTE pbyRegIndex, BYTE* pbyDataBuf);
#endif
    VENDORCMD_API BYTE Clear_DoneQueue(void* pVCmd, BYTE pbyType, BYTE pbyClearItem);
#if defined(PPS_API)
    VENDORCMD_API BYTE Set_Debug_Cmd(void* pVCmd, BYTE pbyIndex, BYTE* pbyArgBuf, BYTE pbyTimeOut, BYTE* pbyBuffer);
    VENDORCMD_API BYTE Get_Debug_Cmd(void* pVCmd, BYTE pbyIndex, BYTE* pbyBuffer);
    VENDORCMD_API BYTE Debug_Cmd_Monitor(void* pVCmd, BYTE pbyIndex, BYTE* pbyArgBuf, BYTE* pbyBuffer);
#endif
    VENDORCMD_API BYTE Generate_PTNG_Data(void* pVCmd, DWORD dwLUN, DWORD dwReadTaskTag, DWORD dwLBA, DWORD dwDataByte, DWORD dwDataCnt, BYTE* pbyWriteBuf, BYTE* pbyReadBuf);
    VENDORCMD_API BYTE OnSwitchRefClk(void* pVCmd, double RefClk);
#if defined(PPS_API)
    VENDORCMD_API BYTE DME_Req(void* pVCmd, DWORD dwOption, BYTE byLaneCnt);
#else
    VENDORCMD_API BYTE DME_Req(void* pVCmd, DWORD dwOption);
#endif
#if !(defined(MICRON) || defined(XITC))
    VENDORCMD_API BYTE Group_Read_Write(void* pVCmd, BYTE* pbyBuf);
#endif
#if !(defined(MICRON) || defined(XITC))
#if defined(PPS_API)
    VENDORCMD_API BYTE Monitor(void* pVCmd, vector<RW_Info_t>& vRW_Info, BYTE* pbyBuf, BYTE Option, BYTE BlockCount);
    //VENDORCMD_API BYTE Monitor(void* pVCmd, BYTE* pbyBuf, BYTE Option, BYTE BlockCount);
#else
    VENDORCMD_API BYTE Monitor(void* pVCmd, BYTE* pbyBuf, BYTE Option);
#endif
#endif
    VENDORCMD_API BYTE PowerControl(void* pVCmd, BYTE OnOffValue, BYTE Channel_SEL);
    VENDORCMD_API BYTE SwitchVoltageValue(void* pVCmd, double Voltage, BYTE Channel_SEL, BYTE VCC_Discharge_Level);
    VENDORCMD_API BYTE ForceBootCode(void* pVCmd, BYTE Mode, WORD SL_Delay, BYTE LL_Delay, BYTE SLL_Delay, BYTE SLH_Delay);
    VENDORCMD_API void Cal_sha2_hmac(void* pVCmd, unsigned char* key, int keylen, unsigned char* input, int ilen, unsigned char* output, int is224);
#ifdef PPS_API
    VENDORCMD_API BYTE ResetN_Key(void* pVCmd, BYTE Mode, BYTE Option);
    VENDORCMD_API BYTE ResetN_VendorCMD(void* pVCmd, BYTE Direction, BYTE Block_Cnt, BYTE* ArgumentPage, BYTE* Data);
    VENDORCMD_API BYTE Measure_Current(void* pVCmd, BYTE Channel_SEL, BYTE* Data, BYTE Option);
    VENDORCMD_API BYTE Measure_Current_UserDefine(void* pVCmd, BYTE Channel_SEL, WORD Count, BYTE* Data);
#elif defined(MICRON) || defined(KIC)
    VENDORCMD_API BYTE Measure_Current(void* pVCmd, BYTE Channel_SEL, BYTE* Data, BYTE Option);
#else
    VENDORCMD_API BYTE Measure_Current(void* pVCmd, BYTE Channel_SEL, BYTE* Data, BYTE Option, BYTE Avg_Cnt, BYTE Conversion_Time);
#endif
    VENDORCMD_API BYTE Measure_Voltage(void* pVCmd, BYTE Channel, BYTE* pbyBuff);
#if defined(PPS_API)
    VENDORCMD_API char* GetSDKTesterInternalInfo(void* pVCmd);
#endif
    VENDORCMD_API DWORD Software_CRC(void* pVCmd, BYTE* s, WORD len, BYTE lsb_first_in, DWORD last_crc);
#ifdef FEATURE_PERFORMANCE
#if defined(PPS_API) || defined(KIC)
    VENDORCMD_API BYTE Performance(void* pVCmd, BYTE* pbyArgBuf, BYTE* pbyAddrBuf, BYTE* pbyResultBuf, BYTE* pbyInfoBuf);
#if defined(PPS_API)
    //VENDORCMD_API BYTE Performance(void* pVCmd, BYTE* ArgBuffer, BYTE* byAddrBuffer, BYTE* pbyBuf, DWORD dwDataLength, BYTE byRPMBTest);
#endif
#else
    VENDORCMD_API BYTE Performance(void* pVCmd, stPERFORMANCE_ARG* pArgBuffer, BYTE* byAddrBuffer, BYTE* pbyBuf, BYTE* pbyInfoBuf);
#endif
#endif

#if defined(FEATURE_UFS_40) && defined(FEATURE_PERFORMANCE)
    VENDORCMD_API BYTE Adv_RPMB_Performance(void* pVCmd, BYTE* pbyArgBuf, BYTE* pbyAddrBuf, BYTE* pbyResultBuf, BYTE* pbyInfoBuf);
#ifdef PPS_API
    VENDORCMD_API BYTE GenericEHS_Performance(void* pVCmd, BYTE* pArgBuffer, BYTE* byAddrBuffer, BYTE* pbyBuf, BYTE* pbyInfoBuf, BYTE* pbyEhsInfoBuf);
#else
    VENDORCMD_API BYTE GenericEHS_Performance(void* pVCmd, stPERFORMANCE_GENERIC_EHS_ARG* pArgBuffer, BYTE* byAddrBuffer, BYTE* pbyBuf, BYTE* pbyInfoBuf, BYTE* pbyEhsInfoBuf);
#endif
#endif
#ifdef FEATURE_PERFORMANCE
    VENDORCMD_API BYTE RPMB_Performance(void* pVCmd, BYTE* pbyArgBuf, BYTE* pbyAddrBuf, BYTE* pbyResultBuf, BYTE* pbyInfoBuf);
    VENDORCMD_API BYTE EN_Performance(void* pVCmd, BYTE* pbyArgBuf, BYTE* pbyAddrBuf, BYTE* pbyResultBuf, BYTE* pbyInfoBuf);
    VENDORCMD_API BYTE HPB_ReadPerformance(void* pVCmd, BYTE* pbyArgBuf, BYTE* pbyAddrBuf, BYTE* pbyResultBuf, BYTE* pbyInfoBuf);
#if defined(PPS_API)
    VENDORCMD_API BYTE HPB_EN_Performance(void* pVCmd, BYTE* pbyArgBuf, BYTE* pbyAddrBuf, BYTE* pbyResultBuf, BYTE* pbyInfoBuf);
#endif
#endif

#ifdef PPS_API
    VENDORCMD_API BYTE Send_CMD_SEQ(void* pVCmd, BYTE* pbyCMDBuf, BYTE byQD, BYTE byOption, DWORD dwCmdBlockCnt, DWORD dwDataBlockCnt, DWORD dwTimeout, BYTE byExtOption, unsigned long long FixPattern);
    //VENDORCMD_API BYTE Send_CMD_SEQ(void* pVCmd, char* sFileName, BYTE byQD, BYTE byOption, DWORD dwCmdBlockCnt, DWORD dwDataBlockCnt, DWORD dwTimeout);
#else
    VENDORCMD_API BYTE Send_CMD_SEQ(void* pVCmd, BYTE* pbyCMDBuf, BYTE byQD, BYTE byOption, DWORD dwCmdBlockCnt, DWORD dwDataBlockCnt, DWORD dwTimeout, unsigned long long FixPattern, BYTE byExtOption);
#endif

#ifdef FEATURE_UFS_40
    VENDORCMD_API BYTE Send_CMD_SEQ_EHS(void* pVCmd, BYTE* pbyDataBuf, DWORD dwDataBlockCnt);
    VENDORCMD_API BYTE CMD_SEQ_GetEHS(void* pVCmd, BYTE* pbyEHSBuf, DWORD dwDataBlockCnt);
#endif
    VENDORCMD_API BYTE CMD_SEQ_Monitor(void* pVCmd, BYTE* pbyResultBuf, BYTE* pbyInfoBuf, DWORD dwBlockCnt, DWORD dwDataBlockCnt, UINT PollingTime);
#ifdef PPS_API
    VENDORCMD_API BYTE Get_SDRAM_Data(void* pVCmd, BYTE* pbyDataBuf, DWORD dwBlockCnt);
#endif
#ifdef FEATURE_PCSPMA
    VENDORCMD_API BYTE DME_REG_Set(void* pVCmd, DWORD offset, BYTE value);
    VENDORCMD_API BYTE DME_REG_Get(void* pVCmd, DWORD offset, BYTE* result);
#endif
#ifdef PPS_API
    VENDORCMD_API BYTE SCMD_Unipro_Error_Inject(void* pVCmd, BYTE* pbyArgBuf);
#endif
#if !(defined(MICRON) || defined(XITC))
    VENDORCMD_API BYTE SCMD_GPIO_Trigger(void* pVCmd, BYTE* pbyArgBuf);
#ifndef KIC
    VENDORCMD_API BYTE SCMD_DME_Error_Count(void* pVCmd, BYTE* pbyArgBuf);
#endif
    VENDORCMD_API BYTE SCMD_SPOR(void* pVCmd, BYTE* pbyArgBuf);
    VENDORCMD_API BYTE SCMD_Get_Info(void* pVCmd, BYTE bySCMD_Idx, BYTE* pbyInfoBuf);
#endif
#if defined(OPPO) || defined(POWERSTORAGE) || defined(FCST) || defined(HSG_SE)|| defined(KIC)
    VENDORCMD_API BYTE SCMD_SetCmdTimeout(void* pVCmd, BYTE* pbyParaBuf, BYTE* pbyArgBuf);
#endif
#if defined(OPPO)
    VENDORCMD_API BYTE SCMD_VDT(void* pVCmd, BYTE* pbyArgBuf);
#endif
#ifdef PPS_API
    VENDORCMD_API BYTE SCMD_UART(void* pVCmd, BYTE* pbyArgBuf);
#endif
#ifndef XITC
    VENDORCMD_API BYTE HPB_Activate(void* pVCmd, BYTE* pbyArgBuf);
    VENDORCMD_API BYTE HPB_AutoSetting(void* pVCmd, BYTE* pbyArgBuf);
    VENDORCMD_API BYTE HPB_Reset(void* pVCmd);
    VENDORCMD_API BYTE HPB_GetEntry(void* pVCmd, BYTE* pbyArgBuf, BYTE* pbyEntry);
#endif
#ifndef XITC
#ifndef KIC
    VENDORCMD_API BYTE HPB_Dump_Table(void* pVCmd, BYTE* pbyArgBuf, BYTE* pbyTableBuf);
    VENDORCMD_API BYTE HPB_Dump_BitMap(void* pVCmd, BYTE* pbyArgBuf, BYTE* pbyBitMapBuf);
#endif
    VENDORCMD_API BYTE HPB_Result(void* pVCmd, BYTE* pbyInfoBuf, BYTE* pbyTableInfoBuf);
#endif
#if !(defined(KIC) || defined(XITC) || defined(MICRON))
    VENDORCMD_API BYTE SDK_Track_Activate(void* pVCmd, BYTE* pbyArgBuf);
    VENDORCMD_API BYTE SDK_Track_Reset(void* pVCmd);
    VENDORCMD_API BYTE SDK_Track_Result(void* pVCmd, BYTE* pbyInfoBuf);
#endif
#ifdef PPS_API
    VENDORCMD_API BYTE SDK_Track_Parsing(void* pVCmd, BYTE* pbyInfoBuf);
    VENDORCMD_API BYTE SDK_Track_List(void* pVCmd, BYTE Item, DWORD dwTimeStampStart, DWORD dwTimeStampEnd, DWORD* Count, BYTE* pbyInfoBuf);
    VENDORCMD_API BYTE debug_fw_event_activate(void* pVCmd, BYTE ais_open);
    VENDORCMD_API BYTE debug_fw_event_result(void* pVCmd, BYTE* pby_info_buf);
    VENDORCMD_API BYTE debug_fw_event_reset(void* pVCmd);
    VENDORCMD_API BYTE Direct_Read_Page(void* pVCmd, BYTE* pbyInfoBuf);
#endif
    VENDORCMD_API BYTE ForceBootMode(void* pVCmd);
#ifdef CODEINT_AP
    VENDORCMD_API void SetLogDataCallBackUI(void* pVCmd, pflogData_callback_phison pFlogDataCallBackFunc);
#endif
#ifndef KIC
    VENDORCMD_API void PrintLogSDK(void* pVCmd, char* cStr, BYTE byPrintOnConsoleEn, BYTE byLogType);
    VENDORCMD_API void PrintBufferSDK(void* pVCmd, BYTE* pbyDataBuff, DWORD Lenght, BYTE ColLength, BYTE byPrintOnConsoleEn, BYTE byLogType);
#endif  //KIC
#ifdef FEATURE_SDK_VERIFICATION
    VENDORCMD_API BYTE SDRAM_Access_Erase(void* pVCmd, DWORD dwAddr, DWORD dwLen, DWORD dwPattern);
    VENDORCMD_API BYTE SDRAM_Access_Compare(void* pVCmd, DWORD dwAddr, DWORD dwLen, DWORD dwPattern);
    VENDORCMD_API BYTE SDRAM_Access_Write(void* pVCmd, BYTE* rbuf, DWORD dwAddr, DWORD dwLen);
    VENDORCMD_API BYTE SDRAM_Access_Read(void* pVCmd, BYTE* rbuf, DWORD dwAddr, DWORD dwLen);
#endif
    VENDORCMD_API void Log_FASetting(void* pVCmd, BYTE byLogSetting, char* cStrFolderName, char* cStrFileName, DWORD faLogLine);
    VENDORCMD_API void Log_FADump(void* pVCmd);
    VENDORCMD_API void LogSetting(void* pVCmd, unsigned char byLogSetting, char* cStrFolderName, char* cStrFileName);
#ifdef __cplusplus
}
#endif