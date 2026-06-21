# 系統專有名詞簡易說明

## 使用說明
本文件用於協助 AI 理解 UFS（Universal Flash Storage）系統相關 log。
當 log 中出現以下名詞時，請依本說明進行語意解讀。

## 專有名詞與定義
- **UFS**：Universal Flash Storage，裝置使用的嵌入式快閃儲存系統與通訊協定
- **GC**：Garbage Collection，UFS 內部回收無效資料的正常背景行為
- **FTL**：Flash Translation Layer，負責邏輯位址與實體快閃位址轉換
- **WL**：Wear Leveling，平均分散寫入以延長快閃壽命的機制
- **LUN**：Logical Unit Number，UFS 中的邏輯儲存單元
- **BKOPS**：Background Operations，UFS 在背景執行的維護工作（如 GC、WL）
- **H8**：UFS Link Hibernate 省電狀態
- **Hibern8**：UFS Link Hibernate 省電狀態
- **UIC**：UFS Interconnect Command，用於控制 UFS link 的指令
- **PA**：Physical Adapter，UFS 實體層相關設定或狀態
- **DL**：Data Link Layer，負責資料傳輸可靠性的協定層
- **NAND**：實體快閃記憶體，用於儲存實際資料
- **SLC**：Single-Level Cell，速度快且耐用的 NAND 類型
- **MLC**：Multi-Level Cell，較高密度的 NAND 類型
- **TLC**：Triple-Level Cell，更高密度但寫入壽命較短的 NAND
- **WB**：Write Booster，以 SLC 模式使用的 TLC/QLC 區域，用來提升效能
- **EOL**：End Of Life，儲存裝置接近或達到壽命上限
- **Thermal Throttling**：因溫度過高而自動降低效能
- **Read Disturb**：因頻繁讀取造成的資料可靠性問題
- **Flush**：要求 UFS 將快取資料實際寫入 NAND
- **QD**：Queue Depth，同時掛在 UFS 裝置上的 I/O 請求數量
- **Link Startup**：UFS 主機與裝置建立連線的流程
- **Power Mode Change**：UFS 切換效能或省電模式
- **SPO**: Security Protocol Out，RPMB相關的SCSI CMD
- **SPI**: Security Protocol In，RPMB相關的SCSI CMD
- **BG_Step**: SDK定義CMD的發送狀態
- **BG_Error**: SDK定義CMD的發送後的Error
- **BG_Sub_Error**: SDK定義CMD的發送後的Error細節
- **BG_SK**: SDK定義CMD的發送後的收到的Sense Key
- **BG_ASC**: SDK定義CMD的發送後的收到的ASC
- **DCMD**：SDK 封裝好的 CMD Flow，主要用於 UFS 除錯、測試與壓力驗證
  - **DCMD0 (0x00)**：DOUT_DIN_CNT_STOP，For DOUT and DIN stop test
  - **DCMD1 (0x01)**：PAUSE_TASK_MNGT，For RTT pause test
  - **DCMD2 (0x02)**：OVER_UNDER_FLOW，For overflow and underflow test
  - **DCMD3 (0x03)**：BUS_IDLE_DET，Bus idle detect
  - **DCMD4 (0x04)**：UNIPRO_ERROR_INJECT，Error inject for Unipro
  - **DCMD5 (0x05)**：MEASURE_INIT_FLOW，Execute device initial flow
  - **DCMD6 (0x06)**：SSU_HIBERNATE_FLOW，SSU and Hibernate test
  - **DCMD7 (0x07)**：INTERRUPT_DEBUG，For SPOR test
  - **DCMD8 (0x08)**：INIT_SPOR_DEBUG，Device initial flow(same as DCMD5) with SPOR test (timer detect type)
  - **DCMD9 (0x09)**：PURGE_SPOR_DEBUG，SPOR test for device purge
  - **DCMD10 (0x0A)**：RESP_EXE_DEBUG，Receive response and quickly execute process 1 and process 2
  - **DCMD11 (0x0B)**：SUSPEND_TEST_DEBUG，Suspend stress test
  - **DCMD12 (0x0C)**：LINK_SPEED_STRESS_DEBUG，Link and speed change stress loop test
  - **DCMD13 (0x0D)**：TIMEOUT_SETTING，Set and Get SDK timeout
  - **DCMD14 (0x0E)**：POWER_CHANGE_STRESS，Power change stress test (speed change & hibernate)
  - **DCMD15 (0x0F)**：Reserved，保留未使用
  - **DCMD16 (0x10)**：GPIO_DEBUG，Set GPIO value
  - **DCMD17 (0x11)**：DME_ERROR_DEBUG，DME Error Count Debug
  - **DCMD18 (0x12)**：Reserved，保留未使用
  - **DCMD19 (0x13)**：BKOPS_SPOR_DEBUG，Tester to detect device BKOPS and execute SPOR test
  - **DCMD20 (0x14)**：KEEP_SEND_CMD_DEBUG，Done Q & Rsp Queue 間格超過 1ms Tester 自動送出 Read Flag Cmd，防止 device 進入 Idle 造成 performance drop
  - **DCMD21 (0x15)**：Inactive_HPB_Table_debug，Inactive Tester HPB Region
  - **DCMD23 (0x17)**：ADVANCED_OPTION_DEBUG，此DCMD主要是作為開關使用，開啟後可以啟動相對應的特殊需求

