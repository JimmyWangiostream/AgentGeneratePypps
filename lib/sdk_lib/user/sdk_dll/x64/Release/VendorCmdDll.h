#include <Windows.h>
#include <string>
#include <ntddscsi.h>
#include <vector>
#include "VendorCmd.h"
#ifdef VENDORCMD_EXPORTS
#define VENDORCMD_API __declspec(dllexport)
#else
#define VENDORCMD_API __declspec(dllimport)
#endif
class VENDORCMD_API CVendorCmdDll
{
#ifdef CODEINT_AP
	unsigned char CmdIdx;
	unsigned int SrcLine;
#endif
public:
#ifdef CODEINT_AP
	pflogData_callback_phison pFlogDataCallBackFunc_;	//vivi 2013-01-25 support output log msg
#endif
    //===Global Variable===
    HANDLE hHWD;
    //=========API=========
/**
 * @brief Get current library’s information.
 *
 * @param[out] Version Version buffer.
 * - Version[0] = ‘v’
 * - Version[1] = Main version
 * - Version[2] = Second version
 * - Version[3] = Year
 * - Version[4] = Month
 * - Version[5] = Date
 */
    void Get_Dll_Version(UCHAR *Version);
/**
 * @brief Set specific tester handle for library to access tester.
 *
 * @param[in] hHWD Tester Handle.
 * @param[in] Drive Logic Number.
 * @retval 0 Pass
 * @retval 1 Fail
 */
    BYTE SetHandle(HANDLE hHWD,DWORD dwDrive = 0);
    WORD GetHubInfo(char* pTesterID, WORD* pPort, WORD* pVID, WORD* pPID, WORD* pUsbVer, char* pHubID);
    BYTE Dll_Initial(BYTE byDllVersionCheck = 0);
    BYTE HostInitial(BYTE Mode);
    BYTE HostLinkStartup();
    BYTE Set_LinkStartup_Mode(BYTE byResetMode);
    BYTE PowerChange(DWORD dwMode, DWORD dwGear, DWORD dwLane, DWORD dwHsRate, DWORD FC0ProtectionTimeOut, DWORD TC0ReplayTimeOut, DWORD AFC0ReqTimeOut, DWORD FC1ProtectionTimeOut, DWORD TC1ReplayTimeOut, DWORD AFC1ReqTimeOut);
    BYTE DME_Set(DWORD dwAttrSetType, DWORD dwMIB_Val, DWORD dwSel, DWORD dwMIB_Attr, DWORD *apb_Result);
    BYTE DME_Get(DWORD dwAttrSetType, DWORD dwSel, DWORD dwMIB_Attr, DWORD *apb_Result, DWORD *apl_Val);
    BYTE HibernateEnter();
    BYTE HibernateExit();
    BYTE MPHYEyeMonitor(MPHY_EYE_MONITOR_PARAM* pEMParam, MPHY_EYE_MONITOR_RESULT* pEMResult);
    BYTE Reset_N(BYTE Option,DWORD dwDelayTime);
    BYTE Read_DME_Reg(BYTE bySel,WORD *pwLength,BYTE *pbyReadData);
    BYTE Send_Cmd(void *pHeader, void *pTran, void *Payload, DWORD dwPayloadLen, DWORD dwTimeOut, DWORD dwAction, DWORD dwPatternMode, DWORD dwPatternTag, DWORD dwSeed_H = 0, DWORD dwSeed_L = 0, BYTE byLBA4K_AddTag = 0);
    BYTE DataPayloadXfer(DWORD dwAction, BYTE *pbyDataBuf, DWORD dwDataLen);
    BYTE Get_DevResp(BYTE *pbyResBuf);
    BYTE DataInOutXfer(DWORD dwLUN, DWORD dwTaskTag, DWORD dwDataSegLen, DWORD dwBufOffset, DWORD dwDataCnt, DWORD dwSegCnt, DWORD dwRW, BYTE *pbyDataBuf, BYTE byIID = 0);
	BYTE Get_HostInfo(BYTE* pbyDataBuf, BYTE byOperateFlag = 0);
    BYTE Get_HostReg(BYTE pbyRegIndex, BYTE *pbyDataBuf);
    BYTE Clear_DoneQueue(BYTE pbyType, BYTE pbyClearItem);
    BYTE Set_Debug_Cmd(BYTE pbyIndex, BYTE *pbyArgBuf, BYTE pbyTimeOut, BYTE *pbyBuffer);
    BYTE Get_Debug_Cmd(BYTE pbyIndex, BYTE *pbyBuffer);
    BYTE Debug_Cmd_Monitor(BYTE pbyIndex, BYTE *pbyArgBuf, BYTE *pbyBuffer);
    BYTE Generate_PTNG_Data(DWORD dwLUN, DWORD dwReadTaskTag, DWORD dwLBA, DWORD dwDataByte, DWORD dwDataCnt, BYTE *pbyWriteBuf, BYTE *pbyReadBuf);
    BYTE OnSwitchRefClk(double RefClk);
    BYTE DME_Req(DWORD dwOption, BYTE byLaneCnt = 0);
    BYTE Group_Read_Write(BYTE *pbyBuf);
    BYTE Monitor(vector<RW_Info_t>& vRW_Info, BYTE *pbyBuf, BYTE Option, BYTE BlockCount = 0);
	BYTE Monitor(BYTE* pbyBuf, BYTE Option, BYTE BlockCount = 0);
    BYTE PowerControl(BYTE OnOffValue, BYTE Channel_SEL);
    BYTE SwitchVoltageValue(double Voltage, BYTE Channel_SEL, BYTE VCC_Discharge_Level = 0);
	BYTE ForceBootCode(BYTE Mode, WORD SL_Delay, BYTE LL_Delay, BYTE SLL_Delay, BYTE SLH_Delay);
	DWORD Software_CRC(BYTE* s, WORD len, BYTE lsb_first_in, DWORD last_crc);
	BYTE ResetN_Key(BYTE Mode, BYTE Option);
	BYTE ResetN_VendorCMD(BYTE Direction, BYTE Block_Cnt, BYTE *ArgumentPage, BYTE *Data);
	BYTE Measure_Current(BYTE Channel_SEL, BYTE* Data, BYTE Option = 0);
	BYTE Measure_Current_UserDefine(BYTE Channel_SEL, WORD Count, BYTE* Data);
	BYTE Measure_Voltage(BYTE Channel,BYTE *pbyBuff);
    char* GetSDKTesterInternalInfo(void);
	//Performacne Measurement function
	BYTE Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf);
	BYTE Performance(BYTE *ArgBuffer, BYTE *byAddrBuffer, BYTE *pbyBuf, DWORD dwDataLength, BYTE byRPMBTest);
	BYTE Adv_RPMB_Performance(BYTE* pbyArgBuf, BYTE* pbyAddrBuf, BYTE* pbyResultBuf, BYTE* pbyInfoBuf);
	BYTE GenericEHS_Performance(BYTE* pArgBuffer, BYTE* byAddrBuffer, BYTE* pbyBuf, BYTE* pbyInfoBuf, BYTE* pbyEhsInfoBuf);
	BYTE RPMB_Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE* pbyInfoBuf = NULL);
	BYTE EN_Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf);
	BYTE HPB_EN_Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf);
	BYTE DME_REG_Set(DWORD offset, BYTE value);
    BYTE DME_REG_Get(DWORD offset, BYTE *result);
	/*************************************************************************
	* description: Special CMD function
	*************************************************************************/
	BYTE SCMD_Unipro_Error_Inject(BYTE *pbyArgBuf);	//SCMD Index 0
    BYTE SCMD_GPIO_Trigger(BYTE *pbyArgBuf);	//SCMD Index 1
    BYTE SCMD_DME_Error_Count(BYTE *pbyArgBuf);	//SCMD Index 2
	BYTE SCMD_SPOR(BYTE *pbyArgBuf);	//SCMD Index 3
	BYTE SCMD_Get_Info(BYTE bySCMD_Idx, BYTE *pbyInfoBuf);
	BYTE SCMD_UART(BYTE* pbyArgBuf);
	BYTE Send_CMD_SEQ(BYTE* pbyCMDBuf, BYTE byQD, BYTE byOption, DWORD dwCmdBlockCnt, DWORD dwDataBlockCnt, DWORD dwTimeout = 0, BYTE byExtOption = 0, unsigned long long FixPattern = 0x5A5A5A5A5A5A5A5A);
	BYTE Send_CMD_SEQ(char* sFileName, BYTE byQD, BYTE byOption, DWORD dwCmdBlockCnt, DWORD dwDataBlockCnt, DWORD dwTimeout = 0);
	BYTE Send_CMD_SEQ_EHS(BYTE* pbyDataBuf, DWORD dwDataBlockCnt);
	BYTE CMD_SEQ_GetEHS(BYTE* pbyEHSBuf, DWORD dwDataBlockCnt);
	BYTE CMD_SEQ_Monitor(BYTE* pbyResultBuf, BYTE* pbyInfoBuf, DWORD dwCmdBlockCnt, DWORD dwDataBlockCnt, UINT PollingTime = 0);
	BYTE Get_SDRAM_Data(BYTE* pbyDataBuf, DWORD dwBlockCnt);
    BYTE HPB_Activate(BYTE *pbyArgBuf);
    BYTE HPB_AutoSetting(BYTE *pbyArgBuf);
	BYTE HPB_Reset();
    BYTE HPB_GetEntry(BYTE *pbyArgBuf, BYTE *pbyEntry);
    BYTE HPB_Dump_Table(BYTE *pbyArgBuf, BYTE *pbyTableBuf);
	BYTE HPB_Result(BYTE* pbyInfoBuf, BYTE* pbyTableInfoBuf);
    BYTE HPB_Dump_BitMap(BYTE *pbyArgBuf, BYTE *pbyBitMapBuf);
	BYTE HPB_ReadPerformance(BYTE* pbyArgBuf, BYTE* pbyAddrBuf, BYTE* pbyResultBuf, BYTE* pbyInfoBuf);
	BYTE ForceBootMode();
	void Cal_sha2_hmac(unsigned char* key, int keylen, unsigned char* input, int ilen, unsigned char* output, int is224);
    BYTE SDK_Track_Activate(BYTE *pbyArgBuf);
    BYTE SDK_Track_Reset();
    BYTE SDK_Track_Result(BYTE * pbyInfoBuf);
    BYTE SDK_Track_Parsing(BYTE * pbyInfoBuf);
    BYTE SDK_Track_List(BYTE Item, DWORD dwTimeStampStart,DWORD dwTimeStampEnd, DWORD *Count, BYTE * pbyInfoBuf);
    BYTE debug_fw_event_activate(BYTE ais_open);
	BYTE debug_fw_event_result(BYTE* pby_info_buf);
	BYTE debug_fw_event_reset();
	BYTE Direct_Read_Page(BYTE* pbyInfoBuf);
	void Log_FASetting(BYTE byLogSetting, char* cStrFolderName, char* cStrFileName, DWORD faLogLine);
	void Log_FADump(void);
	void LogSetting(BYTE byLogSetting, char* cStrFolderName, char* cStrFileName);
	void PrintLogSDK(char* cStr, BYTE byPrintOnConsoleEn, BYTE byLogType);
	void PrintBufferSDK(BYTE* pbyDataBuff, DWORD Lenght, BYTE ColLength, BYTE byPrintOnConsoleEn, BYTE byLogType);
#ifdef CODEINT_AP
public:
	//============================================================================================================================================================
	// For CODEINT System
	//============================================================================================================================================================
	void SetLogDataCallBackUI(pflogData_callback_phison pFlogDataCallBackFunc);
#endif
};
