// 下列 ifdef 區塊是建立巨集以協助從 DLL 匯出的標準方式。
// 這個 DLL 中的所有檔案都是使用命令列中所定義 CURMEASUREDLL_EXPORTS 符號編譯的。
// 在命令列定義的符號。任何專案都不應定義這個符號
// 這樣一來，原始程式檔中包含這檔案的任何其他專案
// 會將 CURMEASUREDLL_API 函式視為從 DLL 匯入的，而這個 DLL 則會將這些符號視為
// 匯出的。
#ifdef CURMEASUREDLL_EXPORTS
#define CURMEASUREDLL_API __declspec(dllexport)
#else
#define CURMEASUREDLL_API __declspec(dllimport)
#endif

// 這個類別是從 CurMeasureDll.dll 匯出的
class CURMEASUREDLL_API CCurMeasureDll {
//class CCurMeasureDll {
public:
	CCurMeasureDll();
	~CCurMeasureDll();
	BYTE SetHandle(HANDLE handle, DWORD drive);
	int MeasureBoard_Init(int port_num);
	int MeasureBoard_PwrCtl(BYTE enable);
	int MeasureBoard_Start(double sample_time_us, BYTE pwr1_ctl, BYTE pwr2_ctl, BYTE pwr3_Ctl);
    int MeasureBoard_Stop(unsigned int &sample_count);
	int MeasureBoard_GetResult(BYTE *pbuf, unsigned int sample_count);
	int MeasureBoard_SwitchVoltageValue(unsigned short voltage, BYTE channel_sel);
};
