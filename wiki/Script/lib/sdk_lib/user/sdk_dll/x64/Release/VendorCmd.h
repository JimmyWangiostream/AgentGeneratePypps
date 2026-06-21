#ifndef __VENDER_CMD_H
#define __VENDER_CMD_H
//#include <iostream>
#include <vector>
#include <string>
/* cppcheck-suppress syntaxError ; "reason1, Skip for C/C++ Compatibility problem"*/
using namespace std;

// 使用一般標準SDK需關閉
#define CODEINT_AP  //(Pattern System SW)

//#define PRINT_FUNCTION_EXE_TIME
//#define PRINT_DEBUG_INFO

#ifdef CODEINT_AP
#define MAX_CODEINT_SRC_FILENAME_SIZE 1024
//log data struct
//vivi 2013-01-25 support output log msg 
typedef struct SendLogEntry_st{
	unsigned int logGroup_No;//log Group_No
	unsigned int logMSG_Type;//log MSG_Type
	unsigned int logMSG_No;//log MSG_No
	unsigned int srcline;
	unsigned int tcstreeline;
	unsigned int logtreeLevel; // log depth in tree, i.e. tree level
	unsigned int logFormatType;// log show format
	char pbfilename[MAX_CODEINT_SRC_FILENAME_SIZE];
	char *pbmsg;//point to msg
	unsigned int msglen;
	char *pbdata;// for private data
	unsigned int datalen;
} GuiLogEntry_t;

typedef int (* pflogData_callback_phison)(GuiLogEntry_t *pentry);

#define PrintLog		ShowLogToGUI
#define PrintDataLog	SetDataToGUI
#else

#define MAX_CODEINT_SRC_FILENAME_SIZE 1024
typedef struct SendLogEntry_st{
	unsigned int logGroup_No;//log Group_No
	unsigned int logMSG_Type;//log MSG_Type
	unsigned int logMSG_No;//log MSG_No
	unsigned int srcline;
	unsigned int tcstreeline;
	unsigned int logtreeLevel; // log depth in tree, i.e. tree level
	unsigned int logFormatType;// log show format
	char pbfilename[MAX_CODEINT_SRC_FILENAME_SIZE];
	char *pbmsg;//point to msg
	unsigned int msglen;
	char *pbdata;// for private data
	unsigned int datalen;
} GuiLogEntry_t;

typedef int (* pflogData_callback_phison)(GuiLogEntry_t *pentry);

#define SLASH_Unit		/
#define SLASH			SLASH_Unit/
//#define PrintLog(x)		printf("%s\n", x)            
#define PrintDataLog	SLASH  
#define PrintLog        SLASH
#endif

#define BIT0	    0x01
#define BIT1    	0x02
#define BIT2    	0x04
#define BIT3    	0x08
#define BIT4    	0x10
#define BIT5    	0x20
#define BIT6    	0x40
#define BIT7    	0x80

typedef unsigned int		UINT;
typedef unsigned char		UCHAR;
typedef unsigned long		ULONG;
typedef struct _DATA_HEADER_INFO_ DATA_HEADER_INFO;

typedef struct _GRW_Err
{
	BYTE byBG_Error;
	BYTE byBG_SubError;
	BYTE byBG_SK;
	BYTE byBG_ASC;
}GRW_Err;

typedef union _SDK_DCMD15_Arg{
	BYTE Data[12];
	struct {
		BYTE bChannelSel:2;
		BYTE fRsp_Suspend:1;
		BYTE fDCMD6_Hib_Enter:1;
		BYTE fDCMD6_Active_to_Sleep:1;
		BYTE fDCMD6_Sleep_to_Active:1;
		BYTE fDCMD6_Active_to_PowerDown:1;
		BYTE fDCMD6_PowerDown_to_Active:1;

		
		BYTE fActive_to_Idle:1;
		BYTE fIdle_to_Active:1;
		BYTE rsvd:6;
	} str;
}uSDK_DCMD15_Arg;

typedef union _SDK_DCMD15_Buf{
	BYTE Data[32];
	struct {
		DWORD dwRespToSuspend_Threshold;
		DWORD dwDCMD6Hib_Threshold; 
		DWORD dwActive_to_Sleep;
		DWORD dwSleep_to_Active;
		DWORD dwActive_to_PowerDown;
		DWORD dwPowerDown_to_Active;
		DWORD dwActive_to_Idle;
		DWORD dwIdle_to_Active;
	} str;
}uSDK_DCMD15_Buf;

typedef struct RW_Info_st
{
	BYTE		byAction;			// Write or Read
	BYTE		bySCSICmd;		// Write_6, Write_10, Write_16, Read_6, Read_10, Read_16
	BYTE		byLun;
	//BYTE		bySaveLBA;
	DWORD	LBA_H;
	DWORD	LBA_L;
	BYTE		byFUA;
	BYTE		byDPO;
	BYTE		byGroupNo;
	DWORD	dwDataLen;
	DWORD	dwDataPattern;	// Normal Write Data Pattern, ex: 0x5A5A5A5A, 0x5555AAAA			
	DWORD	dwDataBuf;		// Buffer Index, ex: INI_WRITE_BUF, INI_READ_BUF
	BYTE		byModeType;		// Auto/Manual Mode, CRC32 Enable, Pattern Enable, Ring Enable
	BYTE		byPatternMode;	// 0: Increase, 1:Decrease, 2:Fix, 3:Random
	BYTE		byAddTag;			// PTN_ADDTAG
	BYTE    byLBA_MarkCRC_En;
	BYTE    bySameTaskTag_En;
	DWORD	dwLoopTag;		// Loop Count
	DWORD    dwTimeOut;		// 設定給 TesterFW 的TimeOut
	DWORD	dwMaxBusyTime;
	DWORD	dwTotalBusyTime;
	DWORD	dwExpectDataLen;
	DWORD	dwAssignLB;
	BYTE		byTaskAtt;		// Task attribute (ordered, head of queue)
	BYTE		byCP;			// command priority
	BYTE		byTaskTag;
	BYTE		byWKLun;			// Well-Known Lun
	BYTE		byCmdOrder;		// 記錄cmd被執行完成的順序
	BYTE     byLBAMark_CheckSum;	// 只用 4 Bytes 的 LBA Mark Gen CheckSum
	DWORD	dwDataCRC;	// for read boot CRC_Enable
	UINT64   u64CheckSum;
	BYTE byRDPROTECT; //UFS support
	// Sean, for GRW return fail RSP/SK/ASC
	GRW_Err stBG_ErrCode;
	// Edison, for data map using ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	DWORD dwIsINTHit;
	DWORD dwStartLBA_Ptn;
	DWORD dwRWType;
	BYTE bCmpCurData;

	bool operator==(const BYTE TaskTag) const
	{
		return byTaskTag == TaskTag;
	}

	bool operator==(const GRW_Err stbg_errcode) const
	{
		return (stBG_ErrCode.byBG_Error != stbg_errcode.byBG_Error);
	}	
}RW_Info_t;

#if 1   //UFS4.0 Feature for PS2321
#pragma pack(push) /* push current alignment to stack */
#pragma pack(1) /* set alignment to 1 byte boundary */
typedef struct __MPHY_EYE_MONITOR_PARAM
{
    UINT32 u8Action : 8;
    UINT32 isPeer : 1;     // 1: Peer(Device),   0: Local(Host)
    UINT32 isHS : 1;       // 1: HS,     0: LS
    UINT32 isRateB : 1;    // 1: RateB,  0: RateA
    UINT32 isLANE1 : 1;    // 1: LANE1,  0: LANE0
    UINT32 isScramble : 1; // 1: enable 0: disable
    UINT32 u3Gear : 3;
    UINT32 u2BeforeAdapt : 2;    	// Perform ADAPT setup before test. 0: FollowSpec, 1: disable, 2:enable
    UINT32 u2TestAdapt : 2;			// Adapt setup for test. 0: FollowSpec, 1: disable, 2:enable
    UINT32 u7TargetTestCnt : 7;
} MPHY_EYE_MONITOR_PARAM;

typedef struct __MPHY_EYE_MONITOR_ELEMENT
{
    INT32 s32Timing;
    INT32 s32Voltage;
    INT32 u32ErrCnt;
    INT32 u32TestCnt;
}MPHY_EYE_MONITOR_ELEMENT;

typedef struct __MPHY_EYE_MONITOR_RESULT
{
    union
    {
        UINT8 mResult[512];
        struct
        {
            UINT8 u8Err;                              //[0]
            UINT8 u8SubErr;                           //[1]
            UINT8 u8FailStep;                         //[2]
            UINT8 u8Rsvd1;                            //[3]
            // For MPHY Debug
            UINT32 u32L0_RO_CURR_SSLMS_C0_C1_BK1;     //[4:7]
            UINT32 u32L0_RO_CURR_SSLMS_C2_C3_BK1;     //[8:11]
            UINT32 u32L0_RO_CURR_SSLMS_C4_C5_BK1;     //[12:15]
            UINT32 u32L0_RO_CURR_SUM_C1_C2_BK1;       //[16:19]
            UINT32 u32L0_RO_CURR_SUM_C3_C4_BK1;       //[20:23]
            UINT32 u32L0_RO_CURR_SUM_C5_TOT_BK1;      //[24:27]
            UINT32 u32L1_RO_CURR_SSLMS_C0_C1_BK1;     //[28:31]
            UINT32 u32L1_RO_CURR_SSLMS_C2_C3_BK1;     //[32:35]
            UINT32 u32L1_RO_CURR_SSLMS_C4_C5_BK1;     //[36:39]
            UINT32 u32L1_RO_CURR_SUM_C1_C2_BK1;       //[40:43]
            UINT32 u32L1_RO_CURR_SUM_C3_C4_BK1;       //[44:47]
            UINT32 u32L1_RO_CURR_SUM_C5_TOT_BK1;      //[48:51]

            UINT32 u32L0_RO_CURR_SSLMS_C0_C1_BK2;     //[52:55]
            UINT32 u32L0_RO_CURR_SSLMS_C2_C3_BK2;     //[56:59]
            UINT32 u32L0_RO_CURR_SSLMS_C4_C5_BK2;     //[60:63]
            UINT32 u32L0_RO_CURR_SUM_C1_C2_BK2;       //[64:67]
            UINT32 u32L0_RO_CURR_SUM_C3_C4_BK2;       //[68:71]
            UINT32 u32L0_RO_CURR_SUM_C5_TOT_BK2;      //[72:75]
            UINT32 u32L1_RO_CURR_SSLMS_C0_C1_BK2;     //[76:79]
            UINT32 u32L1_RO_CURR_SSLMS_C2_C3_BK2;     //[80:83]
            UINT32 u32L1_RO_CURR_SSLMS_C4_C5_BK2;     //[84:87]
            UINT32 u32L1_RO_CURR_SUM_C1_C2_BK2;       //[88:91]
            UINT32 u32L1_RO_CURR_SUM_C3_C4_BK2;       //[92:95]
            UINT32 u32L1_RO_CURR_SUM_C5_TOT_BK2;      //[96:99]
        };
    };

    MPHY_EYE_MONITOR_ELEMENT mData[127 * 127];
} MPHY_EYE_MONITOR_RESULT;
#define MPHY_EYE_MONITOR_RESULT_LEN         sizeof(MPHY_EYE_MONITOR_RESULT)

#pragma pack(pop) /* restore original alignment from stack */
#endif

enum	
{
	READ=0,					//	0 
	WRITE,					//	1 	
	HPB_READ,				//	2
	DYNAMIC_HPB_READ,		//  3
	PRE_PROCESS_HPB_READ	//  4
};

enum eResult_Code
{
    RET_STATUS_PASS	= 0,			
    RET_STATUS_FAIL	= 1,			
    RET_STATUS_UNSUPPORT_ON_2806 = 2,	
    RET_STATUS_UNSUPPORT_ON_2807 = 3,	
};

enum TESTERINFO_FLAG : unsigned int
{
    TESTERINFO_FLAG_UNKNOWN = 0,
    TESTERINFO_FLAG_PTN_START = 0x1,			//bit0
    TESTERINFO_FLAG_PTN_END = 0x2,				//bit1
    TESTERINFO_FLAG_PERFORMANCE_END = 0x4,		//bit2
};

enum eDll_Init_Result
{
    DLL_INIT_PASS					= 0,			
    DLL_INIT_FAIL_VID				= 1,
    DLL_INIT_FAIL_NOT_SDK_FW		= 2,
    DLL_INIT_FAIL_HANDSHAKE			= 3,
    DLL_INIT_FAIL_DLL_VERSION		= 4,
    DLL_INIT_FAIL_AUTHENTICATION	= 5,    
    DLL_INIT_FAIL_TRANGLECERT	    = 6,
    DLL_INIT_FAIL_REMOTECERTV1	    = 7,
    DLL_INIT_FAIL_REMOTECERTV2	    = 8,
    DLL_INIT_FAIL_PROMOTEAUTH	    = 9,
    DLL_INIT_FAIL_LICENSEBINAUTH    = 10,
    DLL_INIT_FAIL_OTHERS	= 0xFF,    	
};

//=========================================================
//CMD Seqeunce
#define RET_STATUS_PASS  0		
#define RET_STATUS_FAIL	 1

#define SDRAM_64M       0x04000000
#define CMD_START_ADDR  0x00000000
#define DATA_START_ADDR 0x02000000
#define ENTRY_SIZE      72
#define DUMMY_SIZE      56
#define SIZE_8K         0x2000

#define ENTRY_OPT_WAIT_QEUEUE     0x0001
#define ENTRY_OPT_PATTERN_INC     (0x0000 << 2)
#define ENTRY_OPT_PATTERN_DEC     (0x0001 << 2)
#define ENTRY_OPT_PATTERN_FIX     (0x0002 << 2)
#define ENTRY_OPT_PATTERN_RND     (0x0003 << 2)
#define ENTRY_OPT_ADD_TAG         (0x0001 << 4)
#define ENTRY_OPT_DATA_IN_OUT     (0x0001 << 6)
#define ENTRY_OPT_CRC32_CMP       (0x0001 << 8)

#define SEQ_OPT_RECORD_TIME       0x01
#define SEQ_OPT_RECORD_RESP       (0x01 << 1)
#define SEQ_OPT_DATA_IN_OUT       (0x01 << 2)       //if  any entry using DATA_IN_OUT, enable this BIT

#define ELK_DATA_LENGTH	1600	// For API GetSDKTesterInternalInfo

class CVendorCmd { 
#ifdef CODEINT_AP
	unsigned char CmdIdx;
	unsigned int SrcLine;

#endif
public:
#ifdef CODEINT_AP
	pflogData_callback_phison 	pFlogDataCallBackFunc_;	//vivi 2013-01-25 support output log msg 
#endif
	CVendorCmd();
private:
	BYTE PT2321_CMD_SEQ_Repackage_Monitor(BYTE *pbyResultBuf, BYTE *pbyInfoBuf, DWORD dwBlockCnt, DWORD dwDataBlockCnt);
	int MeasureICCS_Current(double* p_ICCS , UCHAR cur_measure_lv, int CH_SEL, BYTE Avg_Cnt = 0, BYTE Conversion_Time = 0);
	int MeasureICCS_Voltage(double* p_ICCS , int CH_SEL);
    int MeasureICCS_Current_Foreground(double* p_ICCS , int CH_SEL,int Loop,int Delay); 
    int GetSlop_Current(double* p_Slop,double ICCS, int CH_SEL);
    int GetTesterICCSCurrent(int CH_SEL , UCHAR Measure_LV_Sel , double AvgCurrentStep , double* p_AvgStep);
    int GetTesterSlopCurrent(int CH_SEL , UCHAR Measure_LV_Sel , double ICCSCurrent , double* p_AvgCurrentStep);
    double CounterICCSCurrent(int Measure_LV_Sel , double* M_I_Current_Value_Array , double* T_I_Step_Array , double AvgStep);
    double CounterSlopCurrent(int Measure_LV_Sel , double* M_I_Current_Value_Array , double* T_I_Step_Array , double ICCSCurrent);
    void CounterRecordSlopArray(double* M_I_Current_Value_Array , double* T_I_Step_Array , double* SlopArray);
    int InitialTesterRecordInfo(void);
    int Load_INI_Setting(void);
    int CSV_Folder_Create(void);
    int get_pc_ip(void);
    int CSV_Output(void);
    int get_hub_info(void);
    int get_tester_info(void);
    int usb_env_output(void);
    int usb_env_check(void);
    int JSON_Output(void);
    int json_post(void); 
    int License_Expired_InTester(BYTE *License_Expired,BYTE *pbyHostInfoBuf);
#if defined(REMOTE_CERT)
    int Dll_RemoteCertV1(BYTE *pbyDirectReadPage,BYTE *pbyHostInfoBuf);
#endif
#if defined(TRIANGLE_CERT)
    int Dll_TriangleCert(BYTE *pbyDirectReadPage,BYTE *pbyHostInfoBuf);
#endif
#if defined(REMOTE_CERT_V2)
    int Dll_RemoteCertV2(BYTE *pbyDirectReadPage,BYTE *pbyHostInfoBuf, BYTE *pbyeFuseInfoBuf, BYTE *pbyFlashSettingInfoBuf);
#endif
#if defined(BOOT_CODE_VENDOR_CHECK)
    int Dll_VendorCheck(BYTE *pbyFlashSettingInfoBuf);
#endif
    
	FILE *pFile;
	FILE *pFileCmd_Seq;
	BYTE bLogFlag;
    UINT16 SDK_SN;

	// The copy and assignment operations of objects are prohibited.
	CVendorCmd(const CVendorCmd& other); // private copy constructor , not implement to Prevent external code from accessing these functions.
    CVendorCmd& operator=(const CVendorCmd& other); // private disable operator= , not implement to Prevent external code from accessing these functions.
public:
	//===Global Variable===
	HANDLE hHWD;
    DWORD targetDisk;
#if defined(PROMOTE_AUTH) 
    BYTE Dll_PormoteAuth(DWORD* dwLicenseDay);
    BYTE Get_PromoteDemeFeature(UINT32 *DemoFeature);
#endif
#if defined(LICENSE_BIN_AUTH)    
    BYTE Dll_CheckLicenseDate(DWORD *dwLicenseDay);
	BYTE Dll_LocalLicenseCheck(DWORD *dwLicenseDay);
#endif
#if defined(REMOTE_CERT_V2)
    BYTE SDK_Auth_SetHosts(const char** host_list, size_t host_count);
#endif
	//=========API=========
    void PrintLogSDK(char *cStr, DWORD GroupNo = 0, DWORD MsgType = 0, DWORD MsgNo = 0, BYTE byPrintOnConsoleEn = 0x00);
	void PrintBufferSDK(BYTE *pbyDataBuff,DWORD Lenght, BYTE ColLength, BYTE byPrintOnConsoleEn, BYTE byLogType);
    void Get_Dll_Version(UCHAR *Version);
    BYTE SetHandle(HANDLE Handle,DWORD dwDrive = 0);
	WORD GetHubInfo(char* pTesterID, WORD* pPort, WORD* pVID, WORD* pPID, WORD* pUsbVer, char* pHubID);
    BYTE Dll_Initial(BYTE byDllVersionCheck = 0);
    BYTE Set_LinkStartup_Mode(BYTE byResetMode);
    BYTE HostInitial(BYTE Mode);
    BYTE HostLinkStartup();
    BYTE PowerChange(DWORD dwMode, DWORD dwGear, DWORD dwLane, DWORD dwHsRate, DWORD FC0ProtectionTimeOut, DWORD TC0ReplayTimeOut, DWORD AFC0ReqTimeOut, DWORD FC1ProtectionTimeOut, DWORD TC1ReplayTimeOut, DWORD AFC1ReqTimeOut);
    BYTE DME_Set(DWORD dwAttrSetType, DWORD dwMIB_Val, DWORD dwSel, DWORD dwMIB_Attr, DWORD *apb_Result);
    BYTE DME_Get(DWORD dwAttrSetType, DWORD dwSel, DWORD dwMIB_Attr, DWORD *apb_Result, DWORD *apl_Val);
    BYTE HibernateEnter();
    BYTE HibernateExit();
    BYTE MPHYEyeMonitor(MPHY_EYE_MONITOR_PARAM* pEMParam, MPHY_EYE_MONITOR_RESULT* pEMResult);
    BYTE Reset_N(BYTE pbyOption,DWORD dwDelayTime);
    BYTE Read_ROM_Code(BYTE bySel,WORD *pwLength,BYTE *pbyReadData);
    BYTE Write_ROM_Code(BYTE bySel,WORD wLength,BYTE *pbyWriteData);
    BYTE Read_DME_Reg(BYTE bySel,WORD *pwLength,BYTE *pbyReadData);
    BYTE Write_DME_Reg(BYTE bySel,WORD pwLength,BYTE *pbyWriteData);
    BYTE Send_Cmd(void *pHeader, void *pTran, void *Payload, DWORD dwPayloadLen, DWORD dwTimeOut, DWORD dwAction, DWORD dwPatternMode, DWORD dwPatternTag, DWORD dwSeed_H = 0, DWORD dwSeed_L = 0, BYTE byLBA4K_AddTag = 0, BYTE dwModeSelect_Check = 1);
    BYTE DataPayloadXfer(DWORD dwAction, BYTE *pbyDataBuf, DWORD dwDataLen);
    BYTE Get_DevResp(BYTE *pbyResBuf);
    BYTE DataInOutXfer(DWORD dwLUN, DWORD dwTaskTag, DWORD dwDataSegLen, DWORD dwBufOffset, DWORD dwDataCnt, DWORD dwSegCnt, DWORD dwRW, BYTE *pbyDataBuf,BYTE byIID = 0);
    BYTE Get_HostInfo(BYTE *pbyDataBuf, BYTE byOperateFlag = 0);
    BYTE Get_HostFW_Info(BYTE byOption, BYTE* pbyResBuf);
    BYTE Get_HostReg(BYTE pbyRegIndex, BYTE *pbyDataBuf);
	BYTE Set_HostReg(BYTE bySel, WORD wRegIndex, BYTE byValue);
    BYTE Clear_DoneQueue(BYTE pbyType, BYTE pbyClearItem);
    BYTE Set_Debug_Cmd(BYTE pbyIndex, BYTE *pbyArgBuf, BYTE pbyTimeOut, BYTE *pbyBuffer);
    BYTE Get_Debug_Cmd(BYTE pbyIndex, BYTE *pbyBuffer);
    BYTE Debug_Cmd_Monitor(BYTE pbyIndex, BYTE *pbyArgBuf, BYTE *pbyBuffer);
    BYTE Generate_PTNG_Data(DWORD dwLUN, DWORD dwReadTaskTag, DWORD dwLBA, DWORD dwDataByte, DWORD dwDataCnt, BYTE *pbyWriteBuf, BYTE *pbyReadBuf);
    BYTE OnSwitchRefClk(double RefClk);
    BYTE DME_Req(DWORD dwOption, BYTE byLaneCnt = 0);
    BYTE Group_Read_Write(BYTE *pbyBuf);
    BYTE Monitor(BYTE *pbyBuf, BYTE Option, BYTE BlockCount = 0);
	BYTE Monitor(vector<RW_Info_t>& vRW_Info, BYTE *pbyBuf, BYTE Option, BYTE BlockCount = 0);
    BYTE PowerControl(BYTE OnOffValue, BYTE Channel_SEL);
    BYTE SwitchVoltageValue(double Voltage, BYTE Channel_SEL, BYTE VCC_Discharge_Level = 0);
    BYTE ForceBootCode(BYTE Mode,WORD SL_Delay,BYTE LL_Delay,BYTE SLL_Delay,BYTE SLH_Delay);
    BYTE ResetN_Key(BYTE Mode,BYTE Option);
    BYTE ResetN_VendorCMD(BYTE Direction, BYTE Block_Cnt, BYTE *ArgumentPage, BYTE *Data);
    BYTE Measure_Current(BYTE Channel_SEL,BYTE *Data, BYTE Option = 0, BYTE Avg_Cnt = 0, BYTE Conversion_Time = 0);
	BYTE Measure_Current_UserDefine(BYTE Channel_SEL, WORD Count, BYTE *Data);
	BYTE Measure_Voltage(BYTE Channel_SEL,BYTE *Data);
	BYTE AotoManualModeSelect_Check(BYTE *pHeader, BYTE *pTran, DWORD dwAction);

    char* GetSDKTesterInternalInfo();

    DWORD Software_CRC(BYTE *s, WORD len, BYTE lsb_first_in, DWORD last_crc);
	
	//Performacne Measurement function
	BYTE Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf);
    BYTE GenericEHS_Performance(BYTE* pArgBuffer, BYTE* byAddrBuffer, BYTE* pbyBuf, BYTE* pbyInfoBuf, BYTE* pbyEhsInfoBuf);
	BYTE RPMB_Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf = NULL);
	BYTE EN_Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf);
	BYTE Performance(BYTE *ArgBuffer, BYTE *byAddrBuffer, BYTE *pbyBuf, DWORD dwDataLength, BYTE byRPMBTest);
	BYTE HPB_ReadPerformance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf);
	BYTE HPB_EN_Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf);
	BYTE Adv_RPMB_Performance(BYTE *pbyArgBuf, BYTE *pbyAddrBuf, BYTE *pbyResultBuf, BYTE *pbyInfoBuf);
		
	BYTE Send_CMD_SEQ(BYTE *pbyCMDBuf, BYTE byQD, BYTE byOption,DWORD dwCmdBlockCnt,DWORD dwDataBlockCnt, DWORD dwTimeout = 0, BYTE byExtOption = 0, unsigned long long FixPattern = 0x5A5A5A5A5A5A5A5A);
    BYTE Send_CMD_SEQ(char *sFileName, BYTE byQD, BYTE byOption,DWORD dwCmdBlockCnt,DWORD dwDataBlockCnt, DWORD dwTimeout = 0);
	BYTE Send_CMD_SEQ_EHS(BYTE *pbyDataBuf, DWORD dwDataBlockCnt);
	BYTE CMD_SEQ_GetEHS(BYTE *pbyEHSBuf, DWORD dwDataBlockCnt);
	BYTE CMD_SEQ_Monitor(BYTE *pbyResultBuf, BYTE *pbyInfoBuf, DWORD dwBlockCnt, DWORD dwDataBlockCnt, UINT PollingTime = 0);
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
	//SCMD Index 4
	BYTE SCMD_UART(BYTE *pbyArgBuf);
    // Get SCMD execution result information    
    BYTE SCMD_Get_Info(BYTE bySCMD_Idx, BYTE *pbyInfoBuf);

    BYTE HPB_Activate(BYTE *pbyArgBuf);
	BYTE HPB_AutoSetting(BYTE *pbyArgBuf);
	BYTE HPB_Reset();
	BYTE HPB_GetEntry(BYTE *pbyArgBuf,BYTE *pbyEntry);	
	BYTE HPB_Dump_Table(BYTE *pbyArgBuf, BYTE *pbyTableBuf);
	BYTE HPB_Dump_BitMap(BYTE *pbyArgBuf, BYTE *pbyBitMapBuf);	
	BYTE HPB_Result(BYTE * pbyInfoBuf, BYTE * pbyTableInfoBuf);

    BYTE SDK_Track_Activate(BYTE *pbyArgBuf);
    BYTE SDK_Track_Reset();
	BYTE SDK_Track_Result(BYTE * pbyInfoBuf);
	BYTE SDK_Track_Change2BigEndian(BYTE * pbyInfoBuf);
    BYTE SDK_Track_Parsing(BYTE * pbyInfoBuf);
    BYTE SDK_Track_List(BYTE Item, DWORD dwTimeStampStart,DWORD dwTimeStampEnd, DWORD *Count, BYTE * pbyInfoBuf);

	BYTE debug_fw_event_activate(BYTE ais_open);
	BYTE debug_fw_event_result(BYTE* pby_info_buf);
	BYTE debug_fw_event_reset();
	BYTE DME_REG_Set(DWORD offset, BYTE value);
    BYTE DME_REG_Get(DWORD offset, BYTE *result);
		
	BYTE ForceBootMode();

    BYTE USB_Send_SCSI_CMD(BYTE *ArgBuf);
	BYTE USB_Send_SCSI_CMD_Get_Handle(BYTE *ArgBuf);
    BYTE USB_BulkIn(BYTE *rbuf, DWORD dwBuffLen);
    BYTE USB_BulkOut(BYTE *rbuf, DWORD dwBuffLen);
    BYTE USB_PowerCycling(BYTE Activate, BYTE GapAftPwrOn, BYTE GapAftPwrOff, BYTE PwrOnDischargeGap);
    BYTE USB_State_Reset();
    BYTE USB_State_Check();
    BYTE USB_State_Get(BYTE *pbyDataBuf);
    BYTE USB_Reset_MCU();

    BYTE SDRAM_Access_Erase(DWORD dwAddr,DWORD dwLen,DWORD dwPattern);
    BYTE SDRAM_Access_Compare(DWORD dwAddr,DWORD dwLen,DWORD dwPattern);
    BYTE SDRAM_Access_Write(BYTE *rbuf,DWORD dwAddr,DWORD dwLen);
    BYTE SDRAM_Access_Read(BYTE *rbuf,DWORD dwAddr,DWORD dwLen);
    BYTE SDRAM_Fail_LED_Blink();
    BYTE SDRAM_Fail_LED_Reset();
    void Cal_sha2_hmac(unsigned char* key, int keylen, unsigned char* input, int ilen, unsigned char* output, int is224);
	
    void Log_FASetting(BYTE byLogSetting, char* cStrFolderName, char* cStrFileName, DWORD faLogLine);
    void Log_FADump(void);
    void LogSetting(BYTE byLogSetting, char* cStrFolderName, char* cStrFileName);
    BYTE Direct_Read_Page(BYTE* pbyInfoBuf);
private:
    BYTE USB_BulkIn_DBUF(BYTE *rbuf, DWORD dwBuffLen, DWORD dwOffset);
	BYTE USB_BulkOut_DBUF(BYTE *rbuf, DWORD dwBuffLen, DWORD dwOffset);
    BYTE UFS_Data_In(void *RespBuffer, UCHAR *pbyBuffer);
    BYTE UFS_Response(void *RespBuffer);
    void PrintLogTime(time_t timerStart, time_t timerEnd,const char *funcName);


#if defined(_PHISON_LIB)
public:
    BYTE UFS_Send_Twice_SW(BYTE bySwitch);
#endif

#ifdef CODEINT_AP
public:
	//============================================================================================================================================================
	// For CODEINT System
	//============================================================================================================================================================
	void SetLogDataCallBackUI(pflogData_callback_phison 	pFlogDataCallBackFunc);
private:
	void SetSourceLine(unsigned int srcline);

	void ShowLogToGUI(char* logmsg, unsigned int GroupNo, unsigned int MsgType, unsigned int MsgNo);
	void SetDataToGUI(char* logmsg, unsigned int GroupNo, unsigned int MsgType, unsigned int MsgNo, char* databuf, unsigned int datasize);
	//============================================================================================================================================================
#endif
};

extern int nVendorCmd;
int fnVendorCmd(void);

/* Release Note 修改版本在 VendorCmd.cpp 檔案
    V2.75Modify  2020/05/6
    1. Add HPB performance mode 4 (L2P Dynamic)
    2. Update drive log API(function not enable)
    3. Add drive log parsing API(function not enable)
    4. 更新版號至2.75
    Code Reviewer: Matt
    
    V2.74Modify  2020/04/15
    1. 加入SDK Track Function，功能尚未開啟，Call function都會回傳PASS，尚無實際功能
    2. 更新版號至2.74
    Code Reviewer: Matt
    
    V2.73Modify  2020/04/08
    1. 更新Read_DME_Reg，新增PS2808 MPHY Reg 讀取
    2. 更新版號至2.73
    Code Reviewer: Matt
    
    V2.72Modify  2020/03/30
    1. 更新Performance_SDRAM() for RPMB Test
    2. 更新版號至2.72
    Code Reviewer: Jason
    
    V2.71Modify  2020/03/26
    1. 更新HPB Function
    2. 更新版號至2.71
    Code Reviewer: Matt
    
    V2.70Modify  2020/03/17
    1. 更新HPB Function，功能開啟
    2. 更新版號至2.70
    Code Reviewer: Matt
    
    V2.69 Modify  2020/03/10
    1. 加入HPB Function，功能尚未開啟，Call function都會回傳PASS，尚無實際功能
    2. 更新版號至2.69
    Code Reviewer: Matt
    
    V2.68 Modify  2020/02/14
    (1) [P2] VendorCmd.cpp : Fixed CMD SEQ monitor display issue (Jason)
    (2) [P2] VendorCmd.cpp : add AotoManualModeSelect_Check() for normal send cmd (Darren)
    1. 修正CMD SEQ monitor 在response fail 時沒有正確顯示的問題
    2. 新增判斷normal send cmd 的時候Auto Mode 和Manual Mode 交錯使用的錯誤
    3. 更新版號至2.68
    Code Reviewer: Jason & Matt
    
    V2.67 Modify by Matt 2020/02/12
    (1) [P2] VendorCmd.cpp : Support Normal RPMB Performance Test
    1.2808支援RPMB Performance Test
    Code Reviewer: Jason
    
    V2.66 Modify by Jason 2020/01/02
    (1) [P2] VendorCmd.cpp : Fixed CMD SEQ test unit ready delay time issue
    1.修正CMD SEQ 的test unit ready function 其中Entry delay被反覆轉換造成時間異常的問題
    Code Reviewer: Matt 
    
    V2.65 Modify by Matt 2019/11/27
    (1) [P2] VendorCmd.cpp : Merge newest CMD SEQ code from YMTC sample code
    合併CMD SEQ SDK lib from YMTC lib
    Code Reviewer: Jason 


	V2.64 Modify by Jason 2019/11/27
	(1) [P2] VendorCmd.cpp : Fix ps2808 little endian issue of DCMD18 
	Code Reviewer: Matt 

    V2.63 Modify by Jason 2019/11/7
	(1) [P2] VendorCmd.cpp : Add Read_DME_Reg api
	Code Reviewer: Matt 
	
	 V2.62 Modify by Jason 2019/10/21
	(1) [P2] VendorCmd.cpp : Enhance Performance_SDRAM function to prevent Old pattern bring 0 memory mode, Default use SDRAM mode if pattern bring 0
	Code Reviewer: Jason 
	
    V2.61 Modify by Jason 2019/10/08
	(1) [P2] VendorCmd.cpp : Fixed measure current issue on PS2808
	Code Reviewer: Matt
	
	V2.60 Modify by Matt 2019/10/02
	(1) [P2] SCSI.cpp/SCSI.h/VendorCmd.cpp: Add external memory mode for Performance
	Code Reviewer: Jason

	V2.59 Modify by Matt 2019/09/27
	(1) [P2] SCSI.cpp/SCSI.h: Add Direct Read function to get port number
	(1) [P2] VendorCmd.cpp: Fixed Enhance Performance function issue and Correct the flow to get port number
	Code Reviewer: Jason

     V2.58 Modify by Jason 2019/09/19
 	(1) [P1] VendorCmd.cpp : Modify CMD_SEQ_RESP_SWAP_FOR_PS2808 for TM dummy response
 	(2) [P1] VendorCmd.cpp/VendorCmd.h : Add Send_CMD_SEQ timeout
	Code Reviewer: Matt

	V2.57 Modify by Harrison 2019/09/05
	(1) [P1] VendorCmd.cpp : Modify CMD_SEQ_Monitor for get data info
	Code Reviewer: Jason

    V2.56 Modify by Jason 2019/08/01
	1.[P1] VendorCmd.cpp : Modify buffer size for PT2808 access register 
	Code reviewer : Matt
	
    V2.55 Modify by Jason 2019/07/24
	1.[P1] VendorCmd.cpp : Modify DCMD function ,parameter reverse to Little-endian for 2808 Use(big-endianto little-endian problem)
	Code reviewer : Matt
    
    V2.54 Modify by Matt 2019/07/19
	(1) [P1] VendorCmd.cpp : Add Little-End/Big-End flow in performance lib func
	performance支援2808格式
	Code Reviewer: Jason
	
    V2.53 Modify by Jason 2019/07/18
	1.[P1] SCSI.cpp/SCSI.h : Modify CMD Sequence function for 2808 Use(little-end to big-end problem)
	2.[P1] VendorCmd.cpp/VendorCmd.h : Modify CMD Sequence function for 2808 Use(little-end to big-end problem)
	Code reviewer : Matt
	
	V2.52 Modify by Matt 2019/07/04
	1.[P1] SCSI.cpp/SCSI.h : Modify performance function for 2808 Use(little-end to big-end problem)
	2.[P1] VendorCmd.cpp/VendorCmd.h : Modify performance function for 2808 Use(little-end to big-end problem)
	Code reviewer : Harrison

    V2.51 Modify by Jason 2019/07/01
	1.[P1] Add get port No. for check ReGetHandle() is right
	Code reviewer : matt
    
    V2.50 Modify by Jason 2019/06/21
	1.[P1] Add DCMD13 timeout setting check, can't over USB timeout 30s
	Code reviewer : matt

	V2.49 Modify by Harrison 2019/05/13
	1.Add Customer SEQ CMD function

	V2.48 Modify by Matt 2019/05/08
	1.Add MeasureICCS_Voltage function

	V2.47 Modify by Matt 2019/05/07
	1.Delete timeout mechinism when RstN Tunning
	
	V2.46 Modify by Harrison 2019/04/29
	1.Add SCMD_Unipro_Error_Inject instead DCMD4
	2.Add SCMD_GPIO_Trigger instead DCMD16
	3.Add SCMD_DME_Error_Count instead DCMD17
	4.Add SCMD_SPOR instead DCMD7

	V2.45 Modify by Matt 2019/04/18
	1. Modify some rsp value to bigEndian in Get_Debug_Cmd for DCMD12 and DCMD14(get dcmd resp)
	
	V2.44 Modify by Matt 2019/03/27
	1. Enhance Error handling of Enhance_Performance Finction 
	
    V2.43 Modify by Jason 2019/03/27
	1. Add DCMD18 Power state detect
	
	V2.42 Modify by Matt 2019/03/18
	1. Add Performance Enhance function

	V2.41 Modify by Sean 2019/03/08
	1. Modify DCMD15 measure current
	
	V2.40 Modify by Sean 2019/02/25
	1. Fix DCMD10 latency little <-> big endian issue for PS2808
	
	V2.39 Modify by Sean 2019/02/13
	1. Add show last rsp TaskTag in Group_Read_Write
	2. Copy Debug/VendorCmd.lib to /VendorCmd.lib
	
	V2.38 Modify by Matt 2019/01/24
	1. Should alway get back the performance result whatever the performance is pass or fail. (Enhance performance error handling)
	
    V2.37 Modify by Jason 2019/01/04
	1. CMD SEQ add load file soluction

	V2.36 Modify by Matt 2018/12/20
	1. Modify the SendCMD of SDK Lib for 2808 New feature(Seed and LBA4K_AddTag)

	V2.35 Modify by Sean 2018/12/19
	1. Remove power change Byte0 (device id no use) for PS2808
	2. Fix big endian issue in DCMD5 (set and get) for PS2808

	V2.34 Modify by Sean 2018/12/13
	1. fix cmd upiu is modify by SDK issue in 2808 (little endian to big endian)
	2. move 8313BB ECO disable only in 2806

	V2.33 Modify by Sean 2018/12/10
	1. fix access reg buffer from 512 to 2048 issue in 2808
	2. add DCMD4 check in 2808

	V2.32 Modify by Sean 2018/11/16
	1. fix DCMD14 buffer data from 512B to 8KB issue

	V2.31 Modify by Matt
	1.Merge CMD Sequence Function to newest

	V2.30 Modify by Sean 2018/10/08
	1. DCMD5 Add 1st read data

    V2.29 Modify by Sean 2018/10/02
    1. Add time stamp in print msg
    2. Add GRW Error struct
    
    V2.28 Modify by Jason 2018/09/27
    1.Add Read/Write ROM Code function
        -For PCS, PMA0,PMA1 Read/Write

    V2.27 Modify by Jason 2018/09/25
	1.Modify Measure Current function
	    -Add measure current forground mode

    V2.26 Modify by Jason 2018/09/12
    1.Support PS2808
    2.Modify DCMD15
	3.Modify Measure Current function

    V2.23 Modify by Jason 2018/03/21
    1.新增Reset Tester log
    2.減少Monitor Fail時的retry次數至3次

    V2.22 Modify by Matt 2018/02/23
    1.新增Performance API

    V2.21 Modify by Jason 2018/02/02
    1.修正Set Handle 未帶入 Driver時會Fail的問題
    2.新增電流數值轉換函式
    3.Define return statue
    
    V2.20 Modify by Jason 2018/01/18
    1.已找出io timeout root cause，將Timeout 設定調回30s
    2.新增Workaround，解決因訊號不良造成USB被提早踢除的問題
    3.新增電流量測功能

	V2.19 Modify by Jason 2017/12/29 
	1.因Win10 會發送額外的USB INT0進來，導至Host會卡住13S~16S
	  暫時先將USB Timeout設定為180s。

    V2.19 Modify by Sean 2017/12/19    配合SDK FW v3.11.6 or 2807 FW使用
	1.加入2806, 2807判斷from Get_HostInfo, 並取消HW_QUERY_WRITE_BUG define

    V2.18 Modify by Jason 2017/11/14    配合SDK FW v3.11.6使用
	1.DataInOut_Xfer,新增IID參數設定
	2.Get_DevResp , 新增ECO Disable檢查機制

    V2.17 Modify by Jason 2017/11/1     配合SDK FW v3.11.3使用
	1.修改RSTN Tuning 流程，加快Tuning 速度

	V2.16 Modify by Jason 2017/11/1  
	1.修正RST VendorCMD write 沒有正常帶入Buffer 的問題
	2.修正SDK Dll print log使用錯誤導致crash問題

    V2.15 Modify by Jason 2017/10/18    配合SDK FW v3.10.3使用
    1.新增RST Tuning Loop由AP帶入
    2.新增RST Tuning Window 數值顯示
    
    V2.14 Modify by Jason 2017/10/17
    1.修改RST VendorCMD 可以讀取超過512Byte的資料
    
    
    V2.13 Modify by Jason 2017/10/17
    1.修正ECO Disable參考位置錯誤的問題 

    V2.12 Modify by Jason 2017/10/05
    1.Add Reset_N Send Key function
    2.Add Reset_N Authentication function
    3.Add Reset_N VendorCMD function

    V2.11 Modify by Jason 2017/9/25
    1.Add Reset_N Key Turning function
    2.Add Reset_N Enable function
    
    V2.10 Modify by Jason 2017/9/19
    1.Add Nop out with ECO Disable on PS2806

    V2.09 Modify by Jason 2017/9/15
    1.Add Force Boot Mode API parameter for delay test
    
    V.2.08 Modify by Jason 2017/9/13
    1.Add Force Boot Mode API

    V.2.07 Modify by Jason 2017/5/10
    1.Monitor add retry 50 times function
    2.Imprement DCMD send 512 Byte buffer to Teser
    3.Fixed Power mode change with wrong value issue
        - 錯誤的值會導至Teser TX/ RX Termination沒設定成1
    4.DataInOutXfer 加入判定Offset數值，如果超過72M就從0讀取資料
    5.擴充Monitor TmpBuff，避免發生溢位問題

    V.2.06 Modify by YX 2017/3/14
    1.Modify SCSI Error Code data type from BYTE to UINT 
    2.Fixed when Generate_PTNG_Data() response timeout issue

    V.2.05 Modify by Jason 2017/2/21
	1.Add debug info in getHostInfo
	2.Add SCSI Error Code display
	3.Add SCSI retry count display
	4.Fixed Send SCSI CMD return wrong error code issue

	V.2.04 Modify by YX 2016/12/09
	1. Modify Clear Done Queue by set SOFT_RST_GP Register.
	2. Add log display function execute time . Can close by define

    V.2.03 Modify by YX 2016/10/24
    1. Add Clear Done Queue and Error Handle for check HW register.

    V.2.02 Modify by YX 2016/10/20
    1. Check enable termination when Fast or Fast Auto mode.

    V.2.01 Modify by YX 2016/08/11
    1. Modify OnSwitchRefClk from FPGA to ASIC version

    V.2.01 Modify by YX 2016/07/26
    1. Modify Power Change to Separate TxRx argument.
    2. Add user define unipro timeout.

    V.2.00 Modify by YX 2016/07/13
    1. Version change from 1.xx to 2.0 due to dll verification.
    2. Add Dll_Initial for Dll verification
    3. Modify all function execute through Dll function.
    4. Add Power Control and SwitchVoltageValue.
    5. Remove Set Timeout Value function
	
    V.1.21 Modify by YX 2016/06/23
    1. Add DCMD6 SSU Hibernate Debug Command

    V.1.20 Modify by YX 2016/06/15
    1. Add Group Read Write and Monitor Function. 

    V.1.11 Modify by YX 2016/05/13
    1. Add DME_Req (EndPointReset, Reset, Enable, Test mode).

    V.1.10 Modify by YX 2016/05/11
    1. Add OnSwitchRefClk function.
    2. Add check Hardware query write bug if payload not more than 16 Byte or aligned 4B.
    3. Add modify bus idle timeout when send command.
    4. Modify set timeout value flow.

    V.1.09 Modify by YX 2016/04/13
    1. Fixed retry not function when status ERROR_GEN_FAILURE cause AP get information.
    2. Modify Generate_PTNG_Data function to match user requirement.

    V.1.08 Modify by YX 2016/04/06
    1. Add pattern generate debug function.
    2. Fixed Get_DevResp wrong buffer.
    3. Fixed clear done queue wrong register id.
    4. Add clear all done queue.

    V.1.07 Modify by YX 2016/03/29
    1. Modify method send data log to UI
    2. Modify Get_DevResp function return error when host hang or header error.

    V.1.06_1 Modify by YX 2015/12/31
    1. Modify Set_Debug_Cmd description.

    V.1.06 Modify by YX 2015/12/28
    1. Add Get_Debug_Cmd to get Debug Info.

    V.1.05 Modify by YX 2015/11/23
    1. Modify Clear_Tag_DQ function to Clear_DoneQueue for clear done queue tag and clear done queue LUN.
    2. Add set timeout value
    3. Add Set Debug Command function

    V.1.04 Modify by YX 2015/11/11
    1. Add Clear_Tag_DQ() function
    2. Modify Get_HostInfo for Queue status information.

    V.1.03 Modify by YX 2015/10/16:
    1. Separate HostLink startup from hostinitial.
    2. Modify name from Get_response() to Get_DevResp()
    3. Add Get_HostInfo() function to retrieve host information.

    V.1.02 Modify by YX 2015/10/06:
    1. Merge UFS SDK with latest branch API(SVN6671).
    2. Modified UFS_HEADER_OFFSET from 8 to 16.
    3. Add error code for Get_Response.

    V.1.01 Modify by YX 2015/09/22:
    1. Merge UFS SDK with latest branch API(SVN6656).
*/

#endif //#define __VENDER_CMD_H