# UFS 4.1JESD220G Conversion Results

- Total pages: 542
- Total chapters: 73
- Marker converted: 542 pages
- Vision API redo: 541 pages
- Vision image descriptions: 225 pages

## Chapters

### Title Page (pages 1-3)

**File:** `01_title_page.md`

此章節為JEDEC標準JESD220G的標題頁，涵蓋通用快閃儲存(UFS)版本4.1的技術規範文件基本資訊。包含標準編號、版本資訊、發布日期(2024年12月)、版權聲明、以及文件目錄結構，提供UFS 4.1標準文件的整體框架和法律條款說明。

**Keywords:** UFS, JEDEC, JESD220G, Universal Flash Storage, technical specification, version 4.1

### Table of Contents (pages 4-22)

**File:** `02_table_of_contents.md`

本章節提供JEDEC標準220G通用快閃記憶體存儲(UFS) 4.1版本技術規範的完整目錄索引。涵蓋UFS架構概述、電氣特性、重置與電源管理、MIPI PHY和UniPro層、UTP傳輸協定層、SCSI指令集、安全特性、功能描述以及描述符定義等核心主題的頁碼對照。此目錄可協助快速定位UFS 4.1標準中特定技術細節、協定層級、指令規範和實作要求的相關章節。

**Keywords:** UFS, JEDEC, table of contents, universal flash storage, technical specification, protocol layers

### 3 Terms and Definitions (pages 23-26)

**File:** `03_3_terms_and_definitions.md`

此章節定義了UFS (Universal Flash Storage)標準中的核心術語、縮寫和命名約定。涵蓋SCSI相關概念（如應用客戶端、設備伺服器、邏輯單元）、資料結構（如命令描述符區塊、協議資訊單元）、以及技術規範中使用的關鍵字（如強制性、可選、保留等）的精確定義。

**Keywords:** UFS, SCSI, terminology, definitions, acronyms, technical specifications

### 4 Introduction (pages 27-28)

**File:** `04_4_introduction.md`

此章節介紹通用快閃記憶體存儲(UFS)標準的基本概念和特性，包括設備的一般特性、介面規格和功能特性。涵蓋UFS的分層架構(UCS/UTP/UIC)、目標應用裝置、電源供應規格、訊號傳輸方式，以及NAND管理功能如開機操作、寫入保護和安全操作等核心功能。

**Keywords:** UFS, Universal Flash Storage, MIPI M-PHY, SCSI, NAND management, mobile storage

### 5 UFS Architecture Overview (pages 29-39)

**File:** `05_5_ufs_architecture_overview.md`

本章節介紹通用快閃記憶體儲存(UFS)架構的整體概覽，包含三層式通訊架構：應用層(UAP)、傳輸協定層(UTP)和互連層(UIC)。內容涵蓋各層的功能、服務存取點、設備管理器、任務管理器，以及基於MIPI UniPro和M-PHY的底層實作。本章節能回答UFS系統架構組成、各層間通訊機制、設備啟動流程，以及與SCSI命令集整合等相關問題。

**Keywords:** UFS Architecture, UTP, UIC, MIPI UniPro, SCSI, Service Access Points

### 6 UFS Electrical: Clock, Reset, Signals And Supplies (pages 40-53)

**File:** `06_6_ufs_electrical_clock_reset_signals_and_supplies.md`

本章節涵蓋UFS（通用快閃記憶體儲存）設備的電氣特性規範，包括電源供應(VCC、VCCQ、VCCQ2)、重置信號(RST_n)、參考時鐘(REF_CLK)、差分資料信號(DIN/DOUT)等訊號定義與電氣參數。詳細說明各種訊號的電壓範圍、時序要求、ESD規範、電源啟動時序，以及參考時鐘在不同HS-Gear模式下的頻率配置與閘控管理。

**Keywords:** UFS, electrical, power supplies, reset signal, reference clock, differential signals, ESD

### 7 Reset, Power-Up And  Power-Down (pages 54-76)

**File:** `07_7_reset_power-up_and_power-down.md`

本章節詳細說明UFS設備的重置、上電和斷電相關規範。涵蓋五種重置類型（電源重置、硬體重置、EndPointReset、邏輯單元重置、主機UniPro溫重置）的操作流程與時序參數，以及電源上下電的電壓斜坡要求與設備電源模式管理。此章節可回答UFS設備重置機制、電源管理策略和各種重置對設備狀態影響的相關問題。

**Keywords:** reset, power-up, power-down, power modes, hardware reset, endpoint reset

### 8 UFS UIC Layer: MIPI M-PHY (pages 77-80)

**File:** `08_8_ufs_uic_layer_mipi_m-phy.md`

本章節介紹UFS UIC層中MIPI M-PHY的技術規格，包含終端設置、驅動電平、PHY狀態機、HS/PWM突發模式、適應序列和PHY屬性配置。此章節回答有關UFS物理層實作、M-TX/M-RX配置參數、支援的傳輸速率檔位以及電氣特性的技術問題。

**Keywords:** MIPI M-PHY, UFS physical layer, termination, HS-GEAR, PWM-GEAR, PHY attributes

### 9 UFS UIC Layer: MIPI Unipro (pages 81-89)

**File:** `09_9_ufs_uic_layer_mipi_unipro.md`

本章節描述了UFS UIC層中MIPI UniPro協議的實作規範，包括UniPro與UFS傳輸協議層之間的資料平面和控制平面介面定義。涵蓋了UniPro架構模型、服務原語、地址映射機制、以及UFS專用的UniPro選項和參數配置要求。

**Keywords:** MIPI UniPro, UIC Layer, Transport Protocol Interface, Device Management Entity, CPort, Service Primitives

### 10.2.3 UniPro (pages 90-93)

**File:** `10_1023_unipro.md`

本章節詳細說明了 UFS（Universal Flash Storage）協議中的 UniPro 傳輸層實作，包括 UPIU（UFS Protocol Information Units）封包格式、資料分組機制、以及各種交易類型的定義。涵蓋了命令執行階段、資料流控制、以及 SCSI 命令在 UniPro 網路上的傳輸方式，可回答關於 UFS 協議結構、封包大小限制、交易碼定義等技術問題。

**Keywords:** UniPro, UPIU, UFS Protocol, data pacing, transaction codes, SCSI commands

### 10.6.2 Basic Header Format (pages 94-101)

**File:** `11_1062_basic_header_format.md`

本章節詳細說明UPIU（UFS Protocol Information Unit）基本標頭格式的完整規格，包含交易類型、標誌位元、LUN、任務標籤、發起者ID、命令集類型等各個欄位的定義和編碼方式。此章節可回答關於UPIU標頭結構、欄位意義、資料封包格式、擴充標頭段落(EHS)和資料段落配置等技術問題。

**Keywords:** UPIU, header format, transaction type, task tag, initiator ID, data segment

### 10.7.1 COMMAND UPIU (pages 102-104)

**File:** `12_1071_command_upiu.md`

本章節詳細說明UFS協定中的COMMAND UPIU格式與規範，包括基本標頭結構、標誌定義、資料傳輸長度設定等內容。此章節可回答關於COMMAND UPIU的結構組成、標誌位元設定、資料傳輸方向控制，以及與SCSI指令服務請求相關的技術問題。

**Keywords:** COMMAND UPIU, UFS Protocol, SCSI command, data transfer, flags, CDB

### 10.7.2 RESPONSE UPIU (pages 105-116)

**File:** `13_1072_response_upiu.md`

此章節詳細描述 UFS 標準中的 RESPONSE UPIU 格式與功能，說明目標設備如何向啟動器回報指令執行結果。涵蓋 RESPONSE UPIU 的基本標頭結構、狀態碼、錯誤處理旗標、資料傳輸計數以及 SCSI 感測資料格式，可回答關於 UFS 指令回應機制、錯誤狀態回報和資料傳輸狀態的相關問題。

**Keywords:** RESPONSE UPIU, UFS protocol, SCSI status, error handling, sense data, data transfer

### 10.7.3 DATA OUT UPIU (pages 117-120)

**File:** `14_1073_data_out_upiu.md`

本章節詳細說明 DATA OUT UPIU 的格式與運作機制，涵蓋從啟動裝置到目標裝置的資料寫入傳輸協定。內容包括 UPIU 標頭格式、各欄位定義（如資料緩衝區偏移、資料傳輸計數）、亂序傳輸規則，以及 SCSI 寫入交易的具體實作範例。

**Keywords:** DATA OUT UPIU, data transfer, write operation, UPIU header, data segment, out of order sequencing

### 10.7.4 DATA IN UPIU (pages 121-126)

**File:** `15_1074_data_in_upiu.md`

本章節詳細說明UFS協議中DATA IN UPIU的結構和功能，包括基本標頭格式、各欄位定義（如資料緩衝區偏移、資料傳輸計數、提示控制等）以及資料從目標裝置到啟動器裝置的傳輸機制。該章節涵蓋順序和非順序資料傳輸、重傳機制、以及SCSI讀取命令的特殊要求，可回答關於UFS資料輸入傳輸協議實作的相關問題。

**Keywords:** DATA IN UPIU, UFS protocol, data transfer, UPIU header, retransmission, SCSI READ

### 10.7.5 READY TO TRANSFER UPIU (pages 127-132)

**File:** `16_1075_ready_to_transfer_upiu.md`

本章節描述READY TO TRANSFER UPIU的詳細規格，這是目標設備在準備接收資料區塊時發出的協定封包，特別用於需要資料輸出傳輸的SCSI命令（如寫入命令）。章節涵蓋UPIU的基本標頭格式、各欄位定義、資料緩衝區偏移量、傳輸計數、提示控制機制，以及順序和重傳的資料傳輸範例。

**Keywords:** READY TO TRANSFER UPIU, data out transfer, SCSI write command, data buffer offset, hint control, retransmission

### 10.7.6 TASK MANAGEMENT REQUEST UPIU (pages 133-135)

**File:** `17_1076_task_management_request_upiu.md`

此章節詳細說明UFS規格中的任務管理請求UPIU（TASK MANAGEMENT REQUEST UPIU）格式和功能。涵蓋任務管理請求的基本標頭結構、各種任務管理功能（如中止任務、重置邏輯單元等）、以及輸入參數的定義和使用方式，可回答關於UFS任務管理協議實作的相關問題。

**Keywords:** TASK MANAGEMENT REQUEST UPIU, SCSI Architecture Model, Task Management Functions, Basic Header, Input Parameters, UFS protocol

### 10.7.7 TASK MANAGEMENT RESPONSE UPIU (pages 136-138)

**File:** `18_1077_task_management_response_upiu.md`

本章節詳述了TASK MANAGEMENT RESPONSE UPIU的規範，這是目標設備回應任務管理請求的協議單元。涵蓋了回應UPIU的結構格式、基本標頭欄位定義，以及任務管理服務回應代碼的詳細說明。此章節可協助解答關於UFS任務管理回應機制、UPIU封包格式及各種任務管理功能完成狀態的問題。

**Keywords:** task management, response UPIU, UFS protocol, SCSI architecture, task abort, service response codes

### 10.7.8 QUERY REQUEST UPIU (pages 139-151)

**File:** `19_1078_query_request_upiu.md`

本章節詳細說明 QUERY REQUEST UPIU 的結構與功能，這是用於在主機和目標裝置之間傳輸非標準用戶資料的協議。章節涵蓋了查詢功能的各種操作碼，包括讀取和寫入描述符、屬性和旗標的具體實作方式。此文件可回答關於 UPIU 封包格式、交易特定欄位定義、以及各種查詢操作的參數設定等技術問題。

**Keywords:** QUERY REQUEST UPIU, descriptors, attributes, flags, opcode, transaction specific fields

### 10.7.9 QUERY RESPONSE UPIU (pages 152-163)

**File:** `20_1079_query_response_upiu.md`

此章節詳細說明了QUERY RESPONSE UPIU的格式和功能，它是UFS協議中Target設備回應Initiator設備QUERY REQUEST的通信單元。涵蓋各種操作碼的回應格式，包括讀寫描述符、屬性和標誌的操作，以及相應的錯誤碼和交易特定欄位定義。

**Keywords:** QUERY RESPONSE UPIU, UFS protocol, descriptor operations, attribute operations, flag operations, transaction specific fields

### 10.7.10 REJECT UPIU (pages 164-166)

**File:** `21_10710_reject_upiu.md`

此章節詳細說明REJECT UPIU的格式與使用規則，包括基本標頭結構、各欄位定義以及設備何時應發送REJECT UPIU。主要涵蓋無效交易類型的處理機制、UPIU封包的錯誤回應格式，以及不同錯誤情況下的適當回應類型選擇。

**Keywords:** REJECT UPIU, Transaction Type, Basic Header, Error Handling, UPIU Format, E2E Status

### 10.7.11 NOP OUT UPIU (pages 167-168)

**File:** `22_10711_nop_out_upiu.md`

此章節說明NOP OUT UPIU的格式和用途，這是一種用於檢測發起設備與目標設備之間連接狀態的協定單元。章節詳細描述了NOP OUT UPIU的結構表格、基本標頭格式，以及各個欄位（如Task Tag、Transaction Type、Flags、Data Segment Length）的具體規範和數值要求。

**Keywords:** NOP OUT UPIU, connection check, basic header, task tag, transaction type, JEDEC standard

### 10.7.12 NOP IN UPIU (pages 169-170)

**File:** `23_10712_nop_in_upiu.md`

此章節詳細說明了UFS協議中NOP IN UPIU的格式和欄位定義，包括基本標頭結構、交易類型、標誌位元、任務標籤、回應欄位等具體規範。本章節可回答關於NOP IN UPIU封包格式、各欄位值設定規則，以及目標裝置如何回應NOP OUT UPIU的相關問題。

**Keywords:** NOP IN UPIU, Basic Header, Transaction Type, Task Tag, Response Field, UPIU Format

### 10.7.13 Data Out Transfer Rules (pages 171-189)

**File:** `24_10713_data_out_transfer_rules.md`

本章節詳細規範了 UFS 裝置中資料輸出傳輸的 RTT (Ready To Transfer) 規則，包含三項主要規則：主機對每個 RTT 請求只能傳送一個 DATA OUT UPIU、裝置不得產生超過主機能力的待處理 RTT 數量，以及資料傳輸必須按照 RTT 順序進行。此外還介紹了無序資料傳輸機制、邏輯單元定義與定址方式，協助解答 UFS 裝置間資料傳輸協定、效能最佳化、錯誤處理機制等相關問題。

**Keywords:** UFS, RTT, data transfer, UPIU, logical units, out of order transfer

### 10.9.7 Data Transfer SCSI Transport Protocol Services (pages 190-193)

**File:** `25_1097_data_transfer_scsi_transport_protocol_services.md`

本章節詳細說明UFS（Universal Flash Storage）系統中SCSI傳輸協議的資料傳輸服務機制。涵蓋了讀取和寫入操作中的資料傳輸協議服務，包括Send Data-In、Data-In Delivered、Receive Data-Out和Data-Out Received等四種核心服務的實作規格和參數定義。此章節可回答關於UFS裝置與主機間資料傳輸協議、I_T_L_Q連接管理、以及SCSI命令執行過程中資料緩衝區處理的相關問題。

**Keywords:** SCSI transport protocol, UFS data transfer, Data-In service, Data-Out service, I_T_L_Q nexus, UniPro delivery

### 10.9.8  Task Management Function Procedure Calls (pages 194-199)

**File:** `26_1098_task_management_function_procedure_calls.md`

本章詳細說明SCSI任務管理功能程序呼叫的實作方式，包括中止任務、中止任務集合、清除任務集合、邏輯單元重置、查詢任務等六種任務管理功能。章節涵蓋各種任務管理功能的具體操作程序、服務回應類型、以及相關的SCSI傳輸協定服務請求與確認機制。

**Keywords:** task management, SCSI transport protocol, abort task, logical unit reset, query task, nexus

### 10.9.9 Query Function Transport Protocol Services (pages 200-202)

**File:** `27_1099_query_function_transport_protocol_services.md`

本章節說明UFS查詢功能傳輸協定服務，定義了用於讀取和設定UFS裝置層級暫存器與參數的查詢功能（非SCSI標準的一部分）。涵蓋四種主要的傳輸協定服務：發送查詢請求、接收查詢請求、查詢功能執行回應，以及接收查詢功能執行確認，包括其參數定義和訊息流程。

**Keywords:** UFS, Query Function, Transport Protocol Services, Device Manager, JEDEC Standard, SCSI

### 11 UFS Application (UAP) Layer – SCSI Commands (pages 203-204)

**File:** `28_11_ufs_application_uap_layer_scsi_commands.md`

本章節定義了UFS應用層(UAP)的SCSI命令集，包括通用命令層(UCL)架構、命令描述符區塊(CDB)格式，以及UFS設備必須支援的強制性SCSI命令清單。涵蓋UFS原生命令集與SCSI命令集的區別，詳細說明各種讀寫、容量查詢、安全協定等命令的操作碼和支援要求。

**Keywords:** UFS, SCSI commands, command descriptor block, CDB, operation code, UAP layer

### 11.3.2 INQUIRY Command (pages 205-207)

**File:** `29_1132_inquiry_command.md`

本章節描述UFS裝置中INQUIRY命令的實作規範，包含命令資料塊格式、重要產品資料(VPD)和標準INQUIRY資料的處理方式。內容涵蓋INQUIRY命令的資料回應格式、各欄位定義以及UFS裝置必須支援的特定參數設定。

**Keywords:** INQUIRY command, SCSI commands, UFS device, vital product data, standard inquiry data, command data block

### 11.3.3 MODE SELECT (10) Command (pages 208-209)

**File:** `30_1133_mode_select_10_command.md`

本章節詳述UFS裝置中MODE SELECT (10)命令的操作機制，包括命令參數設定、資料傳輸流程以及模式頁面管理。內容涵蓋命令CDB結構、PF和SP位元的功能說明，以及透過RTT UPIU進行資料傳輸的程序，可回答關於UFS裝置參數配置和模式選擇命令實作的相關問題。

**Keywords:** MODE SELECT, UFS command, mode pages, SCSI parameters, data transfer, UPIU

### 11.3.4 MODE SENSE (10) Command (pages 210-213)

**File:** `31_1134_mode_sense_10_command.md`

本章節詳細說明UFS設備中MODE SENSE (10)命令的規格和實作細節。涵蓋命令參數定義、頁面控制功能、資料傳輸機制以及狀態回應處理，包括支援的模式頁面類型和錯誤處理機制。此章節可回答關於MODE SENSE命令格式、參數設定、資料傳輸流程和錯誤狀態處理的相關問題。

**Keywords:** MODE SENSE, command parameters, page control, data transfer, status response, UFS

### 11.3.6 READ (10) Command (pages 214-215)

**File:** `32_1136_read_10_command.md`

此章節詳細說明UFS儲存裝置的READ (10)命令規格，包括命令描述區塊(CDB)的結構定義、各個參數欄位的功能說明，以及資料傳輸流程和狀態回應機制。涵蓋邏輯區塊位址、傳輸長度、快取控制參數(DPO/FUA)、群組編號等關鍵概念，適用於回答UFS讀取命令實作、參數配置和錯誤處理相關問題。

**Keywords:** READ command, UFS, CDB, logical block address, data transfer, UPIU

### 11.3.7 READ (16) Command (pages 216-217)

**File:** `33_1137_read_16_command.md`

本章節詳細說明UFS儲存裝置中READ (16)命令的技術規格，包括命令描述符區塊(CDB)的位元組結構、各參數欄位的定義與功能。涵蓋資料傳輸流程、狀態回應處理，以及各種錯誤條件的處理方式，適用於需要了解UFS讀取操作實作細節的開發者。

**Keywords:** READ command, UFS, CDB, LOGICAL BLOCK ADDRESS, TRANSFER LENGTH, UPIU, status response

### 11.3.8 READ CAPACITY (10) Command (pages 218-220)

**File:** `34_1138_read_capacity_10_command.md`

此章節詳細說明READ CAPACITY (10)命令的規格，包括命令結構、參數格式和狀態回應。涵蓋了如何查詢UFS裝置的邏輯單元容量，以及8位元組容量資料的傳輸格式和錯誤處理機制。

**Keywords:** READ CAPACITY, UFS command, logical block address, capacity data, UPIU, status response

### 11.3.9 READ CAPACITY (16) Command (pages 221-225)

**File:** `35_1139_read_capacity_16_command.md`

本章節詳細說明UFS規範中READ CAPACITY (16)命令的實作，包括命令結構、參數資料格式和狀態回應。該章節解釋如何查詢邏輯單元容量、區塊大小、精簡配置參數等儲存裝置特性，以及相關的錯誤處理機制。

**Keywords:** READ CAPACITY, UFS command, logical unit capacity, block size, thin provisioning, parameter data

### 11.3.12 REPORT LUNS Command (pages 226-230)

**File:** `36_11312_report_luns_command.md`

本章節說明REPORT LUNS命令的詳細規格，包括命令結構、參數設定、資料回應格式和LUN定址方法。涵蓋標準邏輯單元和知名邏輯單元(W-LUN)的定址格式，以及UFS中不同類型LUN的識別方式。

**Keywords:** REPORT LUNS, logical unit, W-LUN, addressing format, UFS, SCSI command

### 11.3.13 VERIFY (10) Command (pages 231-232)

**File:** `37_11313_verify_10_command.md`

本章節詳細說明UFS裝置中VERIFY (10)命令的實作規格，包括命令描述區塊(CDB)格式、參數定義以及狀態回應機制。涵蓋邏輯區塊位址驗證、驗證長度設定、快取寫入要求，以及各種錯誤狀況的處理方式，可回答關於UFS存儲媒體驗證操作的技術問題。

**Keywords:** VERIFY command, UFS device, logical block verification, CDB format, medium verification, status response

### 11.3.14 WRITE (6) Command (pages 233-234)

**File:** `38_11314_write_6_command.md`

本章節詳細說明了UFS儲存裝置中WRITE (6)命令的技術規格，包含命令格式、參數定義、資料傳輸流程及狀態回應機制。涵蓋邏輯區塊位址設定、傳輸長度參數、UPIU封包處理方式，以及各種錯誤狀態的處理規範，適用於需要了解UFS寫入操作實作細節的技術問題。

**Keywords:** WRITE command, UFS, logical block address, data transfer, UPIU, status response

### 11.3.15 WRITE (10) Command (pages 235-237)

**File:** `39_11315_write_10_command.md`

本章詳細說明UFS規格中的WRITE (10)命令，包括命令格式、參數定義和資料傳輸流程。涵蓋命令描述塊(CDB)的各個欄位說明、DPO/FUA等控制參數、邏輯區塊位址和傳輸長度設定，以及GROUP NUMBER用於標識系統資料特性和Context ID的功能。

**Keywords:** WRITE command, UFS, logical blocks, data transfer, CDB parameters, GROUP NUMBER

### 11.3.16 WRITE (16) Command (pages 238-240)

**File:** `40_11316_write_16_command.md`

本章節詳細說明UFS存儲規範中的WRITE(16)命令，包含命令描述符塊(CDB)的格式定義、各個參數欄位的功能說明，以及資料傳輸流程和狀態回應機制。此章節能回答關於WRITE(16)命令結構、參數配置、執行流程和錯誤處理等技術問題。

**Keywords:** WRITE command, UFS, CDB, data transfer, logical block, UPIU

### 11.3.17 REQUEST SENSE Command (pages 241-242)

**File:** `41_11317_request_sense_command.md`

本章節詳細說明了REQUEST SENSE命令的規格，該命令用於從UFS設備伺服器獲取感測資料，包含錯誤或異常狀況資訊以及設備當前操作狀態。章節涵蓋了命令格式、三層錯誤代碼結構（Sense Key、ASC、ASCQ）、資料回應格式，以及各種狀態回應處理方式。

**Keywords:** REQUEST SENSE, UFS command, sense data, error handling, device status, SCSI protocol

### 11.3.18 FORMAT UNIT Command (pages 243-244)

**File:** `42_11318_format_unit_command.md`

本章節詳細說明FORMAT UNIT命令的規格和操作流程，包括命令的CDB格式、參數設定、資料傳輸方式以及狀態回應機制。此章節可回答關於儲存裝置格式化操作、邏輯區塊映射、缺陷管理以及命令執行狀態處理的相關問題。

**Keywords:** FORMAT UNIT, logical blocks, medium formatting, defect management, UPIU, status response

### 11.3.19 PRE-FETCH (10) Command (pages 245-249)

**File:** `43_11319_pre-fetch_10_command.md`

本章節詳細說明了PRE-FETCH (10)和PRE-FETCH (16)命令的規格，包括命令結構、參數定義、資料傳輸和狀態回應機制。此章節還涵蓋了SECURITY PROTOCOL IN命令的實作細節，可回答關於UFS裝置中預取操作和安全協定處理的技術問題。

**Keywords:** PRE-FETCH, SECURITY PROTOCOL IN, UFS commands, logical block address, cache management, JEDEC UFS

### 11.3.22 SECURITY PROTOCOL OUT Command (pages 250-251)

**File:** `44_11322_security_protocol_out_command.md`

此章節說明SECURITY PROTOCOL OUT命令的規格，包括命令格式、參數定義和資料傳輸機制。涵蓋了安全協議欄位、傳輸長度設定、以及命令執行的狀態回應處理，可回答有關UFS裝置安全協議命令實作的相關問題。

**Keywords:** SECURITY PROTOCOL OUT, UFS command, data transfer, JEDEC UFS, security protocol, command status response

### 11.3.23 SEND DIAGNOSTIC Command (pages 252-253)

**File:** `45_11323_send_diagnostic_command.md`

本章節詳細說明SEND DIAGNOSTIC命令的規格，該命令用於要求設備伺服器對SCSI目標設備或邏輯單元執行診斷操作。內容涵蓋命令的CDB格式、各種診斷參數設定（包括自我測試代碼、參數格式等），以及資料傳輸流程和狀態回應處理。

**Keywords:** SEND DIAGNOSTIC, SCSI, self-test, diagnostic operations, CDB format, status response

### 11.3.24 SYNCHRONIZE CACHE (10) Command (pages 254-257)

**File:** `46_11324_synchronize_cache_10_command.md`

本章節詳細介紹 SYNCHRONIZE CACHE (10) 和 SYNCHRONIZE CACHE (16) 命令的技術規格，包括命令格式、參數定義、資料傳輸行為及狀態回應。這些命令用於確保指定的邏輯區塊將最新資料值記錄到儲存媒體上，涵蓋了 IMMED 位元、邏輯區塊位址、區塊數量等關鍵參數的使用方式和錯誤處理機制。

**Keywords:** SYNCHRONIZE CACHE, logical blocks, IMMED, command parameters, status response, UFS device

### 11.3.26 UNMAP Command (pages 258-261)

**File:** `47_11326_unmap_command.md`

本章節詳細說明UFS儲存裝置中UNMAP指令的規格與實作，該指令用於將邏輯區塊位址(LBA)進行解除映射(去配置)操作。涵蓋UNMAP指令格式、參數列表結構、區塊描述符定義，以及指令傳輸流程和狀態回應機制，主要適用於支援精簡佈建(Thin Provisioning)的邏輯單元。

**Keywords:** UNMAP command, thin provisioning, LBA deallocation, block descriptor, parameter list, UFS storage

### 11.3.27 READ BUFFER Command (pages 262-267)

**File:** `48_11327_read_buffer_command.md`

本章節說明 READ BUFFER 命令的詳細規格，該命令用於測試邏輯單元緩衝記憶體、測試服務傳遞子系統完整性、下載微碼以及檢索錯誤歷史記錄和統計資訊。涵蓋命令格式、模式欄位值（包含資料模式和錯誤歷史模式）、錯誤歷史目錄結構，以及命令狀態回應的處理方式。

**Keywords:** READ BUFFER command, buffer memory testing, error history, microcode download, UFS storage, JEDEC standard

### 11.3.28 WRITE BUFFER Command (pages 268-272)

**File:** `49_11328_write_buffer_command.md`

本章節說明WRITE BUFFER命令的詳細規格，涵蓋緩衝區記憶體測試、韌體更新和錯誤統計等功能。內容包含命令參數定義、模式欄位值、Field Firmware Update (FFU) 流程，以及資料傳輸和狀態回應的處理機制。

**Keywords:** WRITE BUFFER, Field Firmware Update, FFU, microcode download, buffer memory, UFS command

### 11.4.1 Mode Page Overview (pages 273-277)

**File:** `50_1141_mode_page_overview.md`

本章節描述UFS裝置中模式頁面(Mode Pages)的概述，包括MODE SELECT和MODE SENSE命令所使用的模式頁面結構。涵蓋模式頁面/子頁面代碼的分配、模式參數清單格式、模式參數標頭的詳細規格，以及Page_0和子頁面兩種不同的模式頁面格式定義。

**Keywords:** mode pages, MODE SELECT, MODE SENSE, page codes, subpage format, mode parameter header

### 11.4.2 UFS Supported Pages (pages 278-286)

**File:** `51_1142_ufs_supported_pages.md`

本章節定義了UFS設備支援的模式頁面，包含控制模式頁面、讀寫錯誤復原模式頁面和快取模式頁面等規格。文件詳細說明各模式頁面的預設值、參數定義、欄位描述，以及重要產品資料(VPD)頁面的格式與實作要求。

**Keywords:** UFS, mode pages, control mode page, error recovery, caching, VPD pages

### 11.5.4 Mode Page Policy VPD Page (pages 287-289)

**File:** `52_1154_mode_page_policy_vpd_page.md`

本章節說明模式頁面策略VPD頁面，詳細描述如何指示邏輯單元支援的每個模式頁面所採用的策略。內容包括模式頁面策略描述符的結構、多邏輯單元共享(MLUS)位元的功能，以及不同模式頁面策略代碼的定義。

**Keywords:** Mode Page Policy, VPD Page, MLUS, Policy Descriptor, Logical Unit, SCSI

### 12.2.2.4 Purge Operation (pages 290-292)

**File:** `53_12224_purge_operation.md`

本章節描述UFS設備中的清除操作(Purge Operation)，說明如何從未使用的物理區塊中移除所有資料以防範晶片層級攻擊。詳細介紹了RPMB清除操作的特殊變體，包括其執行機制、對其他操作的影響，以及在UFS4.0中作為強制功能的要求。

**Keywords:** purge operation, RPMB purge, secure removal, physical blocks, UFS4.0, die level attacks

### 12.2.3.3 Purge Operation (pages 293-295)

**File:** `54_12233_purge_operation.md`

本章節詳細說明UFS儲存裝置中的清除操作(Purge Operation)實作機制，包括fPurgeEnable旗標和bPurgeStatus屬性的運作方式、狀態機轉換，以及裝置抹除(Wipe Device)和安全模式配置等相關功能。此章節可回答關於UFS清除操作的控制流程、錯誤處理機制、以及安全資料移除相關的技術問題。

**Keywords:** purge operation, UFS, fPurgeEnable, bPurgeStatus, wipe device, provisioning type

### 12.2.3.6 bSecureRemovalType Parameter (pages 296-298)

**File:** `55_12236_bsecureremovaltype_parameter.md`

本章節說明UFS裝置中bSecureRemovalType參數的定義與資料保護機制，包括清除操作時的不同安全移除方式(如覆寫、擦除等)，以及邏輯單元層級的寫入保護模式。同時介紹了RPMB(重放保護記憶體區塊)的實作方式，提供經過驗證和重放保護的資料存取功能。

**Keywords:** bSecureRemovalType, data protection, write protection, RPMB, secure removal, purge operation

### 12.4.3.1 RPMB Resources (pages 299-310)

**File:** `56_12431_rpmb_resources.md`

此章節詳細說明了RPMB（Replay Protected Memory Block）資源的技術規格與組成要素。涵蓋了驗證金鑰、寫入計數器、結果暫存器、資料區域以及安全寫入保護配置區塊等核心組件的規格定義，並包含MAC計算演算法、訊息格式與請求/回應類型等實作細節，適用於需要了解UFS設備RPMB功能實作與安全認證機制的技術問題。

**Keywords:** RPMB, authentication, MAC, write protection, security, UFS

### 12.4.3.7 RPMB Operation Result (pages 311-313)

**File:** `57_12437_rpmb_operation_result.md`

本章節說明RPMB（Replay Protected Memory Block）操作結果的結構和編碼定義，包括結果欄位的兩位元組組成、寫入計數器狀態指示以及各種操作狀態碼。涵蓋了從操作成功到各種失敗情況（如認證失敗、計數器失敗、地址失敗等）的完整結果代碼定義，並提供了正常RPMB模式下訊息資料框架的實作結構。

**Keywords:** RPMB, operation result, result codes, write counter, authentication failure, message data frame

### 12.4.5.1 Advanced RPMB Message (pages 314-315)

**File:** `58_12451_advanced_rpmb_message.md`

本章節詳細說明Advanced RPMB訊息的結構與實作方式，包含訊息格式、EHS欄位組織架構、以及Advanced RPMB Meta Information的詳細欄位定義。內容涵蓋訊息大小規格、MAC/KEY處理、以及各種欄位如Request/Response Message Type、Nonce、Write Counter等的配置方式。

**Keywords:** Advanced RPMB, EHS field, message structure, meta information, MAC/KEY, UPIU

### 12.4.6.1 CDB Format of SECURITY PROTOCOL IN/OUT Commands (pages 316-320)

**File:** `59_12461_cdb_format_of_security_protocol_inout_commands.md`

本章節定義了SECURITY PROTOCOL IN/OUT命令的命令描述符塊(CDB)格式，用於RPMB(Replay Protected Memory Block)操作。詳細說明了各個位元組欄位的設置，包括操作代碼、安全協定欄位值(00h和ECh)、RPMB協定ID對應的區域映射，以及支援的安全協定清單和憑證資料的參數格式。

**Keywords:** CDB format, SECURITY PROTOCOL, RPMB, UFS, command descriptor block, security protocol

### 12.4.7.1 Request Type Message Delivery (pages 321-322)

**File:** `60_12471_request_type_message_delivery.md`

本章節詳細說明RPMB（Replay Protected Memory Block）操作中的請求類型訊息傳遞機制，包括如何使用SECURITY PROTOCOL OUT命令來傳送各種RPMB請求訊息。涵蓋不同RPMB訊息類型的資料傳輸長度規格、一般RPMB與進階RPMB的差異，以及完整的訊息傳遞流程和通訊協定細節。

**Keywords:** RPMB, SECURITY PROTOCOL OUT, message delivery, data transfer, authentication, UFS

### 12.4.7.2 Response Type Message Delivery (pages 323-324)

**File:** `61_12472_response_type_message_delivery.md`

本章節說明JEDEC標準中RPMB（Replay Protected Memory Block）回應型訊息的傳遞機制，包括如何使用SECURITY_PROTOCOL_IN命令來請求和接收來自RPMB區域的資料。涵蓋了不同RPMB操作類型的預期資料傳輸長度規格、Normal RPMB與Advanced RPMB模式的差異，以及完整的訊息傳遞流程和資料結構定義。

**Keywords:** RPMB, SECURITY_PROTOCOL_IN, response message, data transfer, authentication, JEDEC

### 12.4.7.3 RPMB Operations in Normal RPMB Mode (pages 325-344)

**File:** `62_12473_rpmb_operations_in_normal_rpmb_mode.md`

本章節涵蓋RPMB（Replay Protected Memory Block）在正常模式下的操作規範，包括認證金鑰程式設計、計數器值讀取、認證資料寫入和讀取等四大核心功能。詳細說明了使用SECURITY PROTOCOL命令進行RPMB操作的完整流程、資料框架結構、錯誤處理機制和MAC驗證程序。

**Keywords:** RPMB, authentication, security protocol, MAC verification, write counter, data protection

### 12.4.7.4 RPMB Operations in Advanced RPMB Mode (pages 345-373)

**File:** `63_12474_rpmb_operations_in_advanced_rpmb_mode.md`

本章節詳細說明在進階 RPMB 模式下的操作流程，包括身份驗證金鑰程式設計、讀取計數器值和經身份驗證的資料寫入等三種主要操作。涵蓋了使用 SECURITY PROTOCOL OUT/IN 命令的完整通訊協定，以及各種錯誤處理和 MAC 驗證機制。

**Keywords:** Advanced RPMB, authentication key, write counter, SECURITY PROTOCOL, MAC verification, data write

### 13 UFS Functional Descriptions (pages 374-381)

**File:** `64_13_ufs_functional_descriptions.md`

本章節詳細說明UFS的啟動功能，包含啟動配置、初始化程序、和啟動代碼下載過程。涵蓋雙啟動邏輯單元(Boot LU A/B)配置、系統啟動時的分階段初始化流程、以及相關描述符和屬性設定。此文件可回答關於UFS設備啟動機制、啟動邏輯單元管理、以及系統初始化序列的技術問題。

**Keywords:** UFS boot, boot configuration, logical units, initialization process, boot code download, device descriptors

### 13.2 Logical Unit Management (pages 382-391)

**File:** `65_132_logical_unit_management.md`

本章節涵蓋UFS設備中邏輯單元管理的詳細內容，包括邏輯單元的配置參數、內存類型、寫入保護機制等功能。該章節可回答關於如何配置邏輯單元數量、大小、內存類型以及RPMB區域設定等技術問題。

**Keywords:** logical unit management, UFS configuration, memory organization, boot logical unit, RPMB, write protection

### 13.4 Host Device Interaction (pages 392-437)

**File:** `66_134_host_device_interaction.md`

本章節說明UFS裝置與主機之間的互動機制，涵蓋效能與可靠性改善功能。內容包括邏輯單元間的優先權管理、背景操作模式、電源管理、動態容量調整等關鍵特性。此章節可回答有關UFS裝置佇列優先權設定、背景操作狀態監控、電源關閉通知機制，以及動態容量管理實作等相關問題。

**Keywords:** UFS, host device interaction, command queue priority, background operations, power management, dynamic capacity

### 13.6 Production State Awareness (PSA) (pages 438-441)

**File:** `67_136_production_state_awareness_psa.md`

本章節詳細說明UFS裝置的生產狀態感知(PSA)功能，該功能讓UFS裝置能根據其生產狀態調整內部操作行為。章節涵蓋PSA流程的完整操作步驟，包括預載資料的管理、狀態轉換機制，以及從裝置焊接前到焊接後的狀態管理，並提供詳細的流程圖和狀態機圖說明。

**Keywords:** Production State Awareness, PSA, UFS device, soldering, pre-loading, state machine

### 14 UFS Descriptors, Flags And Attributes (pages 442-486)

**File:** `68_14_ufs_descriptors_flags_and_attributes.md`

本章節詳細說明UFS（通用快閃記憶體存儲）中的描述符、標誌和屬性的規格定義，包括各種描述符類型（設備、配置、單元等）的格式、存取方式和參數設定。此文件回答了有關UFS描述符結構、查詢請求機制、配置管理和設備參數設定等技術問題。

**Keywords:** UFS descriptors, query request, UPIU, device configuration, logical units, SCSI

### 14.2 Flags (pages 487-491)

**File:** `69_142_flags.md`

此章節涵蓋了UFS設備中標誌（Flags）的定義和規範，包含標誌的存取屬性（讀取、寫入、持續性、揮發性等）以及各種系統標誌的詳細說明。本章節可回答關於UFS標誌類型、存取控制、設備初始化、寫入保護、背景操作、韌體更新控制、WriteBooster功能等相關問題。

**Keywords:** flags, access properties, device initialization, write protection, background operations, WriteBooster, UFS

### 14.3 Attributes (pages 492-520)

**File:** `70_143_attributes.md`

本章節詳細說明屬性(Attributes)的定義與使用方式，屬性是代表特定數值範圍的可讀寫參數，例如最大數據封包大小。內容涵蓋屬性的存取特性、各種屬性的詳細定義表格、以及屬性在UFS設備中的配置和管理方式。

**Keywords:** attributes, access properties, UFS device, parameters, read write, configuration

### Annex B (Informative) Reference Clock Measurement Procedure (pages 521-524)

**File:** `71_annex_b_informative_reference_clock_measurement_procedure.md`

此章節描述UFS標準中參考時鐘量測程序的技術規範，包含隨機抖動(Random Jitter)和確定性抖動(Deterministic Jitter)的量測方法。涵蓋了不同參考時鐘頻率的最大抖動限制、測試設備需求、測試程序步驟，以及HS-LSS模式下參考時鐘自動檢測的實作範例，可解答UFS系統時鐘品質驗證相關問題。

**Keywords:** reference clock, jitter measurement, random jitter, deterministic jitter, DSO, UFS testing

### Annex D (Informative) Board Design Guideline (pages 525-528)

**File:** `72_annex_d_informative_board_design_guideline.md`

本章節提供UFS 4.0系統板設計指南，包括電源域(VCC/VCCQ/VCCQ2)的阻抗規格、電容配置建議，以及Buck型與LDO型PMIC的噪聲預算分配。內容涵蓋系統板PCB模擬所需的輸入參數、最大允許阻抗值、頻率響應特性和電壓噪聲餘量建議，可協助工程師進行UFS系統板的電源完整性設計。

**Keywords:** UFS 4.0, PCB design, power integrity, impedance specification, PMIC, noise budget

### Annex E (Informative) Differences Between Revisions (pages 529-542)

**File:** `73_annex_e_informative_differences_between_revisions.md`

本章節為附錄E，詳細記錄了JESD220G標準與其前版本之間的差異比較，包括從JESD220F到JESD220G的新增功能（如設備級異常事件、主機發起的碎片整理、WriteBooster緩衝區調整等）、規範引用更新，以及對已定義功能的修改。此章節同時追溯了歷史版本間的變化，涵蓋電氣特性、協議改進、安全功能增強等技術規格演進。

**Keywords:** revision differences, JESD220G, UFS standard, version changes, feature additions, specification updates
