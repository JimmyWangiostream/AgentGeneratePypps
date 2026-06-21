1|---
2|title: PF023_0215-Normalized-TestFlow
3|type: normalized-test-flow
4|tags: [test-flow, ufs, pf023_0215, scsi-cmd, refresh, attribute, flag]
5|description: >
6|  PF023_0215 Refresh Operation Test — 完整驗證 Refresh 功能：屬性 HW Reset 持久性、
7|  Refresh 狀態機 (Idle→InProgress→Success→Stopped)、Queue 非空時的 Refresh 行為、
8|  LUN reconfig 後計數保留、以及不支援時的錯誤處理。
9|sources:
10|  - JIRA: PF023_0215 (SYSTCUFS-34)
11|  - UFS Spec: JESD220H Section 13.4.15 (Refresh Operation), Section 14.2 (Flags), Section 14.3 (Attributes)
12|---
13|
14|# PF023_0215 正規化 Test Flow（SCSI CMD 単位）
15|
16|## 測試目標
17|
18|完整驗證 UFS Refresh 操作的所有面向：
19|- **屬性持久性**：Refresh_Frequency / Refresh_Method / bRefreshUnit 在 HW Reset 後的正確性
20|- **Refresh 狀態機**：Idle(0) → InProgress(1) → Stopped(2) / Success(3) / Stopped_Queue(4)
21|- **Queue 非空時的行為**：Refresh Enable 在命令佇列非空時應被停止 (Status=4)
22|- **Progress 與 TotalCount**：dRefreshProgress 清除後不變、完成後 TotalCount +1
23|- **LUN Reconfig 後計數保留**
24|- **不支援時的錯誤處理**：所有 Refresh 操作應回 FAIL
25|
26|## 測試架構
27|
28|```
29|├── Phase 0: Refresh 支援檢查
30|│   └── Step 0.1: QUERY Read Attribute (bUFSFeaturesSupport) — Check Refresh bit → Expected: Refresh bit == 1, 否則 NOT SUPPORTED
31|│
32|├── [若支援 Refresh]
33|│   │
34|│   ├── Phase 1: 屬性持久性驗證（HW Reset 前後）
35|│   │   ├── Step 1.1: QUERY Write Attribute (Refresh_Frequency) → Expected: QUERY RESPONSE Success
36|│   │   ├── Step 1.2: HW Reset → Expected: Reset device success
37|│   │   └── Step 1.3: QUERY Read Attribute (Refresh_Frequency) — verify → Expected: value matches Step 1.1
38|│   │   │
39|│   │   ├── Step 1.4: QUERY Write Attribute (Refresh_Method = 01h, 02h) → Expected: QUERY RESPONSE Success
40|│   │   ├── Step 1.5: HW Reset → Expected: Reset device success
41|│   │   └── Step 1.6: QUERY Read Attribute (Refresh_Method) — verify → Expected: value matches Step 1.4
42|│   │   │
43|│   │   ├── Step 1.7: QUERY Write Attribute (bRefreshUnit = 0, 1) → Expected: QUERY RESPONSE Success
44|│   │   ├── Step 1.8: HW Reset → Expected: Reset device success
45|│   │   └── Step 1.9: QUERY Read Attribute (bRefreshUnit) — verify → Expected: value matches Step 1.7
46|│   │   │
47|│   │   └── Step 1.10: QUERY Read Attribute (dRefreshProgress) — Monitor → Expected: progress reflects bRefreshUnit
48|│   │
49|│   ├── Phase 2: Refresh 狀態機驗證 (Idle → Success)
50|│   │   ├── Step 2.1: WRITE(10) + UNMAP — Precondition → Expected: GOOD Status
51|│   │   ├── Step 2.2: QUERY Set Flag (fRefreshEnable, 0x07) → Expected: QUERY RESPONSE Success
52|│   │   ├── Step 2.3: QUERY Read Attribute (bRefreshStatus) — expect 0 or 1 → Expected: bRefreshStatus == 0x00 or 0x01
53|│   │   ├── Step 2.4: QUERY Clear Flag (fRefreshEnable) → Expected: QUERY RESPONSE Success
54|│   │   ├── Step 2.5: QUERY Read Attribute (bRefreshStatus) — expect 2 → Expected: bRefreshStatus == 0x02
55|│   │   ├── Step 2.6: QUERY Set Flag (fRefreshEnable) → Expected: QUERY RESPONSE Success
56|│   │   ├── Step 2.7: sleep(20000ms) → Expected: 等待 Refresh 完成
57|│   │   ├── Step 2.8: QUERY Read Attribute (bRefreshStatus) — poll until 3 → Expected: bRefreshStatus == 0x03 (Success)
58|│   │   └── Step 2.9: QUERY Clear Flag (fRefreshEnable) → Expected: QUERY RESPONSE Success
59|│   │
60|│   ├── Phase 3: Queue 非空時的 Refresh 行為
61|│   │   ├── Step 3.1: WRITE(10) — Full card (queue) → Expected: (queued)
62|│   │   ├── Step 3.2: QUERY Set Flag (fRefreshEnable) → Expected: QUERY RESPONSE Success
63|│   │   ├── Step 3.3: Send Write + Refresh Enable → Expected: Write: GOOD Status
64|│   │   ├── Step 3.4: QUERY Read Attribute (bRefreshStatus) — expect 4 → Expected: bRefreshStatus == 0x04
65|│   │   ├── Step 3.5: QUERY Read Attribute (dRefreshProgress) — save → Expected: 記錄 progress 值
66|│   │   ├── Step 3.6: QUERY Clear Flag (fRefreshEnable) → Expected: QUERY RESPONSE Success
67|│   │   └── Step 3.7: QUERY Read Attribute (dRefreshProgress) — compare → Expected: progress unchanged
68|│   │
69|│   ├── Phase 4: dRefreshTotalCount 驗證
70|│   │   ├── Step 4.1: QUERY Read Attribute (dRefreshTotalCount) — save → Expected: 記錄 baseline
71|│   │   ├── Step 4.2: QUERY Set Flag (fRefreshEnable) → Expected: QUERY RESPONSE Success
72|│   │   ├── Step 4.3: QUERY Read Attribute (dRefreshProgress) — poll 100% → Expected: dRefreshProgress == 100%
73|│   │   ├── Step 4.4: QUERY Read Attribute (dRefreshTotalCount) → Expected: baseline + 1
74|│   │   └── Step 4.5: QUERY Read Attribute (dRefreshProgress) → Expected: dRefreshProgress == 0
75|│   │
76|│   └── Phase 5: LUN Reconfig 後計數保留
77|│       ├── Step 5.1: QUERY Write Descriptor — Reconfig → Expected: QUERY RESPONSE Success
78|│       └── Step 5.2: QUERY Read Attribute (dRefreshTotalCount) → Expected: value unchanged
79|│
80|└── [若不支援 Refresh — Phase 6: 錯誤處理]
81|    ├── Step 6.1: QUERY Write Attribute (Refresh_Frequency) — expect FAIL → Expected: QUERY RESPONSE Failure
82|    ├── Step 6.2: QUERY Write Attribute (Refresh_Method) — expect FAIL → Expected: QUERY RESPONSE Failure
83|    ├── Step 6.3: QUERY Set Flag (fRefreshEnable) — expect FAIL → Expected: QUERY RESPONSE Failure
84|    ├── Step 6.4: QUERY Clear Flag (fRefreshEnable) — expect FAIL → Expected: QUERY RESPONSE Failure
85|    ├── Step 6.5: QUERY Read Attribute (bRefreshStatus) — expect FAIL → Expected: QUERY RESPONSE Failure
86|    ├── Step 6.6: QUERY Read Attribute (dRefreshProgress) — expect FAIL → Expected: QUERY RESPONSE Failure
87|    └── Step 6.7: QUERY Read Attribute (dRefreshTotalCount) — expect FAIL → Expected: QUERY RESPONSE Failure
88|```
89|
90|---
91|
92|## Phase 0 — Refresh 支援檢查
93|
94|### Step 0.1: 檢查 Refresh 支援
95|
96|**UFS QUERY**: `READ ATTRIBUTE (bUFSFeaturesSupport)`
97|
98|**目的**: 確認 UFS Spec >= 3.0 且 bUFSFeaturesSupport 的 Refresh bit 為 1。
99|
100|| Field | Value |
101||-------|-------|
102|| Opcode | 0x03（READ ATTRIBUTE） |
103|| IDN | bUFSFeaturesSupport |
104|
105|**Expected**: Refresh bit == 1。
106|
107|**若支援**: 繼續 Phase 1。
108|
109|**若不支援**: 跳至 Phase 6（錯誤處理）。
110|
111|**UFS SPEC Reference**: JESD220H Section 14.3
112|
113|---
114|
115|## Phase 1 — 屬性持久性驗證
116|
117|### Step 1.1: 設定 Refresh_Frequency
118|
119|**UFS QUERY**: `WRITE ATTRIBUTE (Refresh_Frequency)`
120|
121|| Field | Value |
122||-------|-------|
123|| Opcode | 0x04（WRITE ATTRIBUTE） |
124|| IDN | Refresh_Frequency |
125|| Value | 依 SPEC 合法值 |
126|
127|**Expected**: `QUERY RESPONSE Success`。
128|
129|---
130|
131|### Step 1.2: HW Reset
132|
133|**操作**: HW_RESET（硬體重置）。
134|
135|**目的**: 驗證 Refresh_Frequency 屬性在 HW Reset 後是否正確保留。
136|
137|---
138|
139|### Step 1.3: 驗證 Refresh_Frequency 持久性
140|
141|**UFS QUERY**: `READ ATTRIBUTE (Refresh_Frequency)`
142|
143|| Field | Value |
144||-------|-------|
145|| Opcode | 0x03（READ ATTRIBUTE） |
146|| IDN | Refresh_Frequency |
147|
148|**Expected**: 值與 Step 1.1 設定的相同（Reset 後保持）。
149|
150|---
151|
152|### Step 1.4: 設定 Refresh_Method
153|
154|**UFS QUERY**: `WRITE ATTRIBUTE (Refresh_Method)`
155|
156|| Field | Value |
157||-------|-------|
158|| Opcode | 0x04（WRITE ATTRIBUTE） |
159|| IDN | Refresh_Method |
160|| Value | 0x01（先測）, 然後 0x02 |
161|
162|**Expected**: `QUERY RESPONSE Success`。
163|
164|---
165|
166|### Step 1.5: HW Reset
167|
168|**操作**: HW_RESET。
169|
170|---
171|
172|### Step 1.6: 驗證 Refresh_Method 持久性
173|
174|**UFS QUERY**: `READ ATTRIBUTE (Refresh_Method)`
175|
176|| Field | Value |
177||-------|-------|
178|| Opcode | 0x03（READ ATTRIBUTE） |
179|| IDN | Refresh_Method |
180|
181|**Expected**: 值與 Step 1.4 設定的相同。
182|
183|---
184|
185|### Step 1.7: 設定 bRefreshUnit
186|
187|**UFS QUERY**: `WRITE ATTRIBUTE (bRefreshUnit)`
188|
189|| Field | Value |
190||-------|-------|
191|| Opcode | 0x04（WRITE ATTRIBUTE） |
192|| IDN | bRefreshUnit |
193|| Value | 0x00（先測 Minimum）, 然後 0x01（Whole Device） |
194|
195|**Expected**: `QUERY RESPONSE Success`。
196|
197|---
198|
199|### Step 1.8: HW Reset
200|
201|**操作**: HW_RESET。
202|
203|---
204|
205|### Step 1.9: 驗證 bRefreshUnit 持久性
206|
207|**UFS QUERY**: `READ ATTRIBUTE (bRefreshUnit)`
208|
209|| Field | Value |
210||-------|-------|
211|| Opcode | 0x03（READ ATTRIBUTE） |
212|| IDN | bRefreshUnit |
213|
214|**Expected**: 值與 Step 1.7 設定的相同。
215|
216|---
217|
218|### Step 1.10: 監控 dRefreshProgress
219|
220|**UFS QUERY**: `READ ATTRIBUTE (dRefreshProgress)`
221|
222|| Field | Value |
223||-------|-------|
224|| Opcode | 0x03（READ ATTRIBUTE） |
225|| IDN | dRefreshProgress |
226|
227|**目的**: 使用不同的 bRefreshUnit 值觀察 dRefreshProgress 的變化行為。
228|
229|**Expected**: Progress 值依據 Refresh Unit 設定而不同。
230|
231|---
232|
233|## Phase 2 — Refresh 狀態機驗證
234|
235|### Step 2.1: Precondition
236|
237|**SCSI CMD**: `WRITE(10) (2Ah)` + `UNMAP (42h)`
238|
239|| Field | Value |
240||-------|-------|
241|| WRITE Opcode | 0x2A |
242|| UNMAP Opcode | 0x42 |
243|| LBA | 0 ~ total card capacity |
244|
245|**目的**: Random write + UNMAP，為後續 Purge 相關測試做準備。
246|
247|**Expected**: `GOOD Status`。
248|
249|---
250|
251|### Step 2.2: 啟用 Refresh
252|
253|**UFS QUERY**: `SET FLAG (fRefreshEnable, 0x07)`
254|
255|| Field | Value |
256||-------|-------|
257|| Opcode | 0x02（SET FLAG） |
258|| IDN | 0x07（fRefreshEnable） |
259|
260|**Expected**: `QUERY RESPONSE Success`。
261|
262|**UFS SPEC Reference**: JESD220H Section 14.2
263|
264|---
265|
266|### Step 2.3: 讀取 Refresh Status（Idle 或 In Progress）
267|
268|**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, 0x2C)`
269|
270|| Field | Value |
271||-------|-------|
272|| Opcode | 0x03（READ ATTRIBUTE） |
273|| IDN | 0x2C（bRefreshStatus） |
274|
275|**Expected**: bRefreshStatus == 0x00（Idle）或 0x01（In Progress）。
276|
277|---
278|
279|### Step 2.4: 停用 Refresh
280|
281|**UFS QUERY**: `CLEAR FLAG (fRefreshEnable, 0x07)`
282|
283|| Field | Value |
284||-------|-------|
285|| Opcode | 0x05（CLEAR FLAG） |
286|| IDN | 0x07（fRefreshEnable） |
287|
288|**Expected**: `QUERY RESPONSE Success`。
289|
290|---
291|
292|### Step 2.5: 驗證 Refresh Status = Stopped
293|
294|**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, 0x2C)`
295|
296|| Field | Value |
297||-------|-------|
298|| Opcode | 0x03（READ ATTRIBUTE） |
299|| IDN | 0x2C（bRefreshStatus） |
300|
301|**Expected**: bRefreshStatus == 0x02（Stopped — Clear Enable 後停止）。
302|
303|---
304|
305|### Step 2.6: 再次啟用 Refresh
306|
307|**UFS QUERY**: `SET FLAG (fRefreshEnable, 0x07)`
308|
309|| Field | Value |
310||-------|-------|
311|| Opcode | 0x02（SET FLAG） |
312|| IDN | 0x07（fRefreshEnable） |
313|
314|**Expected**: `QUERY RESPONSE Success`。
315|
316|---
317|
318|### Step 2.7: 等待 Refresh 完成
319|
320|**操作**: sleep(20000ms)。
321|
322|**目的**: 給予裝置足夠時間完成 Refresh 操作。
323|
324|---
325|
326|### Step 2.8: 輪詢 Refresh Status 至 Success
327|
328|**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, 0x2C)`
329|
330|| Field | Value |
331||-------|-------|
332|| Opcode | 0x03（READ ATTRIBUTE） |
333|| IDN | 0x2C（bRefreshStatus） |
334|
335|**Expected**: bRefreshStatus == 0x03（Refresh Completed Successfully）。
336|
337|**若尚未完成**: 持續輪詢，超過上限次數則判定 FAIL。
338|
339|---
340|
341|### Step 2.9: 停用 Refresh Enable
342|
343|**UFS QUERY**: `CLEAR FLAG (fRefreshEnable, 0x07)`
344|
345|| Field | Value |
346||-------|-------|
347|| Opcode | 0x05（CLEAR FLAG） |
348|| IDN | 0x07（fRefreshEnable） |
349|
350|**Expected**: `QUERY RESPONSE Success`。
351|
352|---
353|
354|## Phase 3 — Queue 非空時的 Refresh
355|
356|### Step 3.1: 寫入命令（Queue，尚未送出）
357|
358|**SCSI CMD**: `WRITE(10) (2Ah)`
359|
360|| Field | Value |
361||-------|-------|
362|| Opcode | 0x2A |
363|| LBA | 0 ~ total card capacity |
364|| Data Size | 1 block |
365|
366|**目的**: 將 Write 命令放入命令佇列，但尚未送出給裝置。
367|
368|---
369|
370|### Step 3.2: 啟用 Refresh（併行）
371|
372|**UFS QUERY**: `SET FLAG (fRefreshEnable, 0x07)`
373|
374|| Field | Value |
375||-------|-------|
376|| Opcode | 0x02（SET FLAG） |
377|| IDN | 0x07（fRefreshEnable） |
378|
379|**Expected**: `QUERY RESPONSE Success`。
380|
381|---
382|
383|### Step 3.3: 同時送出 Write + Refresh Enable
384|
385|**操作**: 將 Step 3.1 的 Write CMD 與 Step 3.2 的 Refresh Enable 同時發送。
386|
387|**目的**: 模擬 Queue 非空時觸發 Refresh 的情境。
388|
389|---
390|
391|### Step 3.4: 驗證 Refresh Status = Stopped (Queue)
392|
393|**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, 0x2C)`
394|
395|| Field | Value |
396||-------|-------|
397|| Opcode | 0x03（READ ATTRIBUTE） |
398|| IDN | 0x2C（bRefreshStatus） |
399|
400|**Expected**: bRefreshStatus == 0x04（Stopped — Queue 非空時被停止）。
401|
402|---
403|
404|### Step 3.5: 記錄 dRefreshProgress
405|
406|**UFS QUERY**: `READ ATTRIBUTE (dRefreshProgress)`
407|
408|| Field | Value |
409||-------|-------|
410|| Opcode | 0x03（READ ATTRIBUTE） |
411|| IDN | dRefreshProgress |
412|
413|**目的**: 記錄目前的 Refresh Progress 值，暫存為 `saved_progress`。
414|
415|---
416|
417|### Step 3.6: 停用 Refresh
418|
419|**UFS QUERY**: `CLEAR FLAG (fRefreshEnable, 0x07)`
420|
421|| Field | Value |
422||-------|-------|
423|| Opcode | 0x05（CLEAR FLAG） |
424|| IDN | 0x07（fRefreshEnable） |
425|
426|**Expected**: `QUERY RESPONSE Success`。
427|
428|---
429|
430|### Step 3.7: 驗證 dRefreshProgress 不變
431|
432|**UFS QUERY**: `READ ATTRIBUTE (dRefreshProgress)`
433|
434|| Field | Value |
435||-------|-------|
436|| Opcode | 0x03（READ ATTRIBUTE） |
437|| IDN | dRefreshProgress |
438|
439|**Expected**: 值與 Step 3.5 的 `saved_progress` 相同（Clear 後 Progress 不應被清除）。
440|
441|---
442|
443|## Phase 4 — dRefreshTotalCount 驗證
444|
445|### Step 4.1: 記錄 Refresh Total Count
446|
447|**UFS QUERY**: `READ ATTRIBUTE (dRefreshTotalCount)`
448|
449|| Field | Value |
450||-------|-------|
451|| Opcode | 0x03（READ ATTRIBUTE） |
452|| IDN | dRefreshTotalCount |
453|
454|**目的**: 記錄目前的 Total Count，暫存為 `baseline_total`。
455|
456|---
457|
458|### Step 4.2: 啟用 Refresh
459|
460|**UFS QUERY**: `SET FLAG (fRefreshEnable, 0x07)`
461|
462|| Field | Value |
463||-------|-------|
464|| Opcode | 0x02（SET FLAG） |
465|| IDN | 0x07（fRefreshEnable） |
466|
467|**Expected**: `QUERY RESPONSE Success`。
468|
469|---
470|
471|### Step 4.3: 輪詢 dRefreshProgress 至 100%
472|
473|**UFS QUERY**: `READ ATTRIBUTE (dRefreshProgress)`
474|
475|| Field | Value |
476||-------|-------|
477|| Opcode | 0x03（READ ATTRIBUTE） |
478|| IDN | dRefreshProgress |
479|
480|**Expected**: dRefreshProgress 達到 100%。
481|
482|---
483|
484|### Step 4.4: 驗證 dRefreshTotalCount 遞增
485|
486|**UFS QUERY**: `READ ATTRIBUTE (dRefreshTotalCount)`
487|
488|| Field | Value |
489||-------|-------|
490|| Opcode | 0x03（READ ATTRIBUTE） |
491|| IDN | dRefreshTotalCount |
492|
493|**Expected**: dRefreshTotalCount == `baseline_total + 1`。
494|
495|---
496|
497|### Step 4.5: 驗證 dRefreshProgress 歸零
498|
499|**UFS QUERY**: `READ ATTRIBUTE (dRefreshProgress)`
500|
501|