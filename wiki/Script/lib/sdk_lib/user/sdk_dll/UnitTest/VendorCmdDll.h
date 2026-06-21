#ifndef __VENDER_CMD_DLL_H
#define __VENDER_CMD_DLL_H
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

using namespace std;

#ifdef PHISON_UNIT_TEST
class IVendor_Cmd_Dll
{
public:
	virtual ~IVendor_Cmd_Dll() {}
	virtual BYTE HibernateEnter() = 0;
	virtual BYTE HibernateExit() = 0;
	virtual BYTE HPB_Reset() = 0;
	virtual BYTE Measure_Current(BYTE Channel_SEL, BYTE *Data, BYTE Option = 0, BYTE Loop = 0, WORD Delay = 0) = 0;
	virtual BYTE Measure_Voltage(BYTE Channel_SEL, BYTE *Data, BYTE Option = 0, BYTE Loop = 0, WORD Delay = 0) = 0;
	virtual BYTE Monitor(vector<RW_Info_t>& vRW_Info, BYTE *pbyBuf, BYTE Option, BYTE BlockCount = 0) = 0;
	virtual BYTE OnSwitchRefClk(double RefClk) = 0;
	virtual BYTE Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf) = 0;
	virtual BYTE Performance(BYTE *ArgBuffer, BYTE *byAddrBuffer, BYTE *pbyBuf, DWORD dwDataLength, BYTE byRPMBTest) = 0;
	virtual BYTE RPMB_Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf) = 0;
	virtual BYTE Generate_PTNG_Data(DWORD dwLUN, DWORD dwReadTaskTag, DWORD dwLBA, DWORD dwDataByte, DWORD dwDataCnt, BYTE *pbyWriteBuf, BYTE *pbyReadBuf) = 0;
	virtual BYTE Reset_N(BYTE Option, DWORD dwDelayTime) = 0;
	virtual BYTE ResetN_VendorCMD(BYTE Direction, BYTE Block_Cnt, BYTE *ArgumentPage, BYTE *Data) = 0;
	virtual BYTE Send_CMD_SEQ(BYTE *pbyCMDBuf, BYTE byQD, BYTE byOption, DWORD dwCmdBlockCnt, DWORD dwDataBlockCnt, DWORD dwTimeout = 0, BYTE byExtOption = 0) = 0;
	virtual BYTE Send_CMD_SEQ(char *sFileName, BYTE byQD, BYTE byOption, DWORD dwCmdBlockCnt, DWORD dwDataBlockCnt, DWORD dwTimeout = 0) = 0;
	virtual BYTE SDK_Track_Result(BYTE * pbyInfoBuf) = 0;
};
#endif

#ifdef PHISON_UNIT_TEST
class  CVendorCmdDll : public IVendor_Cmd_Dll
#else
class VENDORCMD_API CVendorCmdDll
#endif
{
#ifdef CODEINT_AP
	unsigned char CmdIdx;
	unsigned int SrcLine;

#endif
public:
#ifdef CODEINT_AP
	pflogData_callback_phison 	pFlogDataCallBackFunc_;	//vivi 2013-01-25 support output log msg 
#endif
    //===Global Variable===
    HANDLE hHWD;

    //=========API=========
    void Get_Dll_Version(UCHAR *Version);
    BYTE SetHandle(HANDLE hHWD,DWORD dwDrive = 0);
    WORD GetHubInfo(char* pTesterID, WORD* pPort, WORD* pVID, WORD* pPID, WORD* pUsbVer, char* pHubID);
    BYTE Dll_Initial();
    BYTE HostInitial(BYTE Mode);
    BYTE HostLinkStartup();
    BYTE PowerChange(DWORD dwMode, DWORD dwGear, DWORD dwLane, DWORD dwHsRate, DWORD FC0ProtectionTimeOut, DWORD TC0ReplayTimeOut, DWORD AFC0ReqTimeOut, DWORD FC1ProtectionTimeOut, DWORD TC1ReplayTimeOut, DWORD AFC1ReqTimeOut);
    BYTE DME_Set(DWORD dwAttrSetType, DWORD dwMIB_Val, DWORD dwSel, DWORD dwMIB_Attr, DWORD *apb_Result);
    BYTE DME_Get(DWORD dwAttrSetType, DWORD dwSel, DWORD dwMIB_Attr, DWORD *apb_Result, DWORD *apl_Val);
    BYTE HibernateEnter();
    BYTE HibernateExit();
    BYTE Reset_N(BYTE Option,DWORD dwDelayTime);
    BYTE Read_DME_Reg(BYTE bySel,WORD *pwLength,BYTE *pbyReadData);
    BYTE Send_Cmd(void *pHeader, void *pTran, void *Payload, DWORD dwPayloadLen, DWORD dwTimeOut, DWORD dwAction, DWORD dwPatternMode, DWORD dwPatternTag, DWORD dwSeed_H = 0, DWORD dwSeed_L = 0, BYTE byLBA4K_AddTag = 0);
    BYTE DataPayloadXfer(DWORD dwAction, BYTE *pbyDataBuf, DWORD dwDataLen);
    BYTE Get_DevResp(BYTE *pbyResBuf);
    BYTE DataInOutXfer(DWORD dwLUN, DWORD dwTaskTag, DWORD dwDataSegLen, DWORD dwBufOffset, DWORD dwDataCnt, DWORD dwSegCnt, DWORD dwRW, BYTE *pbyDataBuf, BYTE byIID = 0);
    BYTE Get_HostInfo(BYTE *pbyDataBuf, BYTE byOperateFlag = 0);
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
    BYTE PowerControl(BYTE OnOffValue, BYTE Channel_SEL);
    BYTE SwitchVoltageValue(double Voltage, BYTE Channel_SEL, BYTE VCC_Discharge_Level = 0);
	BYTE ForceBootCode(BYTE Mode, WORD SL_Delay, BYTE LL_Delay, BYTE SLL_Delay, BYTE SLH_Delay);
	BYTE ResetN_Key(BYTE Mode, BYTE Option);
	BYTE ResetN_VendorCMD(BYTE Direction, BYTE Block_Cnt, BYTE *ArgumentPage, BYTE *Data);
	BYTE Measure_Current(BYTE Channel_SEL,BYTE *Data, BYTE Option = 0,BYTE Loop = 0,WORD Delay = 0);
	BYTE Measure_Current_UserDefine(BYTE Channel_SEL,WORD Count, BYTE *Data);
	BYTE Measure_Voltage(BYTE Channel_SEL,BYTE *Data,BYTE Option = 0,BYTE Loop = 0,WORD Delay = 0);
    BYTE Environment_Data_Insert(const char* key, const char* value);
    BYTE Environment_Data_Insert(const char* key, unsigned int value);
    BYTE Environment_Data_Insert(const char* key, int value);
    BYTE Environment_Data_Insert(const char* key, long value);
    BYTE Environment_Data_Insert(const char* key, double value);
    BYTE Environment_Data_Insert(const char* key, bool value);
    DWORD Software_CRC(BYTE *s, WORD len, BYTE lsb_first_in, DWORD last_crc);

	//Performacne Measurement function
	BYTE Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf);
	BYTE RPMB_Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf);
	BYTE EN_Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf);
    BYTE Performance(BYTE *ArgBuffer, BYTE *byAddrBuffer, BYTE *pbyBuf, DWORD dwDataLength, BYTE byRPMBTest);
	BYTE HPB_ReadPerformance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf);

	BYTE Send_CMD_SEQ(BYTE *pbyCMDBuf, BYTE byQD, BYTE byOption, DWORD dwCmdBlockCnt, DWORD dwDataBlockCnt, DWORD dwTimeout = 0, BYTE byExtOption = 0);
    BYTE Send_CMD_SEQ(char *sFileName, BYTE byQD, BYTE byOption, DWORD dwCmdBlockCnt, DWORD dwDataBlockCnt, DWORD dwTimeout = 0);
    BYTE CMD_SEQ_Monitor(BYTE *pbyResultBuf, BYTE *pbyInfoBuf, DWORD dwBlockCnt, DWORD dwDataBlockCnt);
    BYTE Get_SDRAM_Data(BYTE *pbyDataBuf, DWORD dwBlockCnt);

	/*************************************************************************
	* description: Special CMD function
	*************************************************************************/
    //SCMD Index 0
	BYTE SCMD_Unipro_Error_Inject(BYTE *pbyArgBuf);
    //SCMD Index 1
    BYTE SCMD_GPIO_Trigger(BYTE *pbyArgBuf);
    //SCMD Index 2
    BYTE SCMD_DME_Error_Count(BYTE *pbyArgBuf);
    //SCMD Index 3
	BYTE SCMD_SPOR(BYTE *pbyArgBuf);
	BYTE SCMD_Get_Info(BYTE bySCMD_Idx, BYTE *pbyInfoBuf);
	BYTE SCMD_UART(BYTE *pbyArgBuf);

    BYTE HPB_Activate(BYTE *pbyArgBuf);
    BYTE HPB_AutoSetting(BYTE *pbyArgBuf);
	BYTE HPB_Reset();
    BYTE HPB_GetEntry(BYTE *pbyArgBuf, BYTE *pbyEntry);
    BYTE HPB_Dump_Table(BYTE *pbyArgBuf, BYTE *pbyTableBuf);
    BYTE HPB_Dump_BitMap(BYTE *pbyArgBuf, BYTE *pbyBitMapBuf);
    BYTE HPB_Result(BYTE * pbyInfoBuf, BYTE * pbyTableInfoBuf);

    BYTE SDK_Track_Activate(BYTE *pbyArgBuf);
    BYTE SDK_Track_Reset();
    BYTE SDK_Track_Result(BYTE * pbyInfoBuf);
    BYTE SDK_Track_Parsing(BYTE * pbyInfoBuf);
    BYTE SDK_Track_List(BYTE Item, DWORD dwTimeStampStart,DWORD dwTimeStampEnd, DWORD *Count, BYTE * pbyInfoBuf);

    BYTE debug_fw_event_activate(BYTE ais_open);
	BYTE debug_fw_event_result(BYTE* pby_info_buf);
	BYTE debug_fw_event_reset();

	BYTE ForceBootMode();
	//void Cal_sha2_hmac(unsigned char *key, int keylen, unsigned char *input, int ilen, unsigned char *output, int is224);

#ifdef CODEINT_AP
public:
	//============================================================================================================================================================
	// For CODEINT System
	//============================================================================================================================================================
	void SetLogDataCallBackUI(pflogData_callback_phison 	pFlogDataCallBackFunc);
#endif
};

#endif   //__VENDER_CMD_DLL_H
