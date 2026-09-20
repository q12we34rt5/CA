# 符號解釋撰寫說明（給撰寫 explanations/*.json 的 agent）

## 背景

`../../../lab1/lab1/` 是計算機結構課的 Lab 1：一個 5-stage pipelined RISC-V CPU（`riscvstall/`，
用 stall 處理 hazard），加上迭代式乘除法器（`imuldiv/`）與 Batten 課程的共用元件庫
（`vc/` = Verilog Components），以及 testbench（`Testbench.v`, `Pattern.v`, `*-sim.v`, `*.t.v`）。

使用者是 **Verilog 與這份作業的初學者**，看不懂大量縮寫，也不知道每個符號在幹嘛。
我們在做一個「符號速查網頁」：使用者輸入符號名稱，網頁顯示 (1) 它出現在哪些地方
（這部分由 `build.py` 自動產生，**你不用管**）、(2) 命名拆解、(3) 它具體是做什麼的。
**你負責 (2) 和 (3)**。

同一個名字在不同 module 裡是不同的 entity（例如每個 module 的 `clk`、Core / Ctrl / Dpath
各自的 `stall_Xhl`），各自需要符合該 module 情境的解釋。

## 你要做的事

1. 先讀 `glossary.json`（本資料夾）——這是全站統一的縮寫對照，你的拆解要與它一致。
2. 讀你被分配到的 worklist 檔（`worklist/<檔名>.json`）：裡面列出該來源檔「每一個」需要
   解釋的 entity，含 `key`、種類、宣告、出現的行號。
3. **完整讀過對應的 Verilog 原始檔**（以及理解它所需的相關檔案，例如它 include 的檔、
   instantiate 它的上層、它 instantiate 的下層）。解釋必須根據實際程式碼，不可以憑名字猜。
4. 為 worklist 裡的 **每一個 key** 寫一筆解釋，輸出到 `explanations/` 底下。

## 輸出格式

檔名：`explanations/<worklist 檔名去掉 .json>.partN.json`（N = 1, 2, 3…）。
**每個 part 檔最多約 50 個 entity**，寫完一個 part 就存檔再寫下一個（避免單次輸出過長）。
每個檔案都是合法 JSON（UTF-8），格式：

```json
{
  "entities": {
    "<worklist 裡的 key，一字不差>": {
      "sum": "一句話摘要（繁體中文，約 15–40 字）",
      "naming": [
        ["dmemreq", "data memory request", "資料記憶體請求"],
        ["msg", "message", "訊息"],
        ["to_bits", "to bits", "打包成 bits"]
      ],
      "desc": "2–5 句的具體說明（見下）"
    }
  }
}
```

### `naming`（命名拆解）
- 把名字依底線 / 大小寫切成有意義的片段，**每一段都要列**，格式 `[片段, 英文全稱, 中文意思]`。
- 片段照原名順序、保留原本大小寫；pipeline 後綴寫成一段（例如 `["Xhl", "eXecute stage, high-level", "執行階段的訊號"]`）。
- 名字本身就是完整單字（如 `clk`→clock、`reset`）也要列一段。單一字母（`a`, `b`, `i`, `n`, `y`）
  要講清楚在這裡代表什麼。
- instance 名稱（如 `imemreq_msg_to_bits`）一樣拆解。

### `sum`
- 一句話講「它是什麼」。會顯示在搜尋結果清單裡，用來區分同名的不同 entity，
  所以要帶出這個 module 的情境（例如「riscv_CoreCtrl 輸出給 dpath 的 X 階段 ALU 功能碼」，
  而不是只寫「ALU 功能碼」）。

### `desc`（最重要）
針對「在這個 module 裡」具體說明，儘量涵蓋：
- **是什麼**：訊號 / 參數 / macro / module / instance 的角色，幾 bit、值各代表什麼
  （例如 `2'd0`=pc+4、`1`=寫）。
- **從哪來**：誰驅動它（哪個 `assign` / `always` / 哪個 instance 的 output / 上層傳進來）。
- **去哪裡**：誰使用它、用來決定什麼。
- **什麼時候重要**：例如「stall 時保持不變」、「reset 時為 1」、「只在握手成功的那個 cycle 有意義」。
- macro：展開成什麼、參數意義、典型用法（舉一個實際使用處）。include guard 直接說明是 include guard。
- module：功能、主要 port 分組、在整個設計裡被誰 instantiate。
- instance：它是哪個 module 的實例、在這裡負責什麼、接了哪些重要訊號。
- localparam 編碼常數：值是多少、代表哪個選項、被誰比對 / 用在解碼表哪一欄。
- testbench / 測試用符號：說明它在測試流程裡的角色即可，可以比較簡短。
- `kind` 為 `implicit`（使用了但沒宣告）、`unknown`（port 所屬 module 的原始檔不在 repo 裡）、
  `hier-unresolved`（階層式路徑解析不到）的 entity：照實說明這個狀況，並根據使用處推測用途。
  例如 `riscv_CoreCtrl` 的 `stats_en` / `num_inst` / `num_cycles` 被 sim 檔用階層路徑存取，
  但 CoreCtrl 裡目前沒有宣告——要明講。

寫作規則：
- **繁體中文**，專有名詞與訊號名保留英文。語氣像助教對初學者解釋，不要空話
  （不要寫「這是一個重要的訊號」這種沒有資訊量的句子）。
- 提到其他符號時用反引號包起來，例如 `` `stall_Dhl` ``、`` `VC_MEM_REQ_MSG_SZ` ``、
  `` `vc_MemReqMsgToBits` ``（網頁會把反引號內的符號變成可點擊的連結，所以**名字要拼對，
  macro 不要加前面的 ` 符號**）。
- 不要寫行號（行號會隨使用者改 code 變動，網頁會自動顯示）。
- 不確定的事情不要編；可以說「從程式碼看來…」。
- 同一組相似符號（例如 `br_beq`, `br_bne`…）每個都要有自己的條目，可以簡短，但值與意義要各自正確。

## 完成前自我檢查

在 `symbol-lookup/` 目錄下執行：

```
python3 build.py --check -v | grep -A400 '<你的來源檔路徑>'
```

確認你負責的來源檔 missing 為 0（該檔不再出現在 missing 清單中），且沒有 “invalid JSON”
或屬於你的 “stale explanation keys”。**不要修改 build.py、index.html、glossary.json、worklist/、
其他 agent 的 explanations 檔，也不要動 `../../../lab1/lab1/` 裡的任何原始碼。** 不要執行不帶 `--check` 的 build.py。

最後回報：你寫了哪些 part 檔、各幾筆、check 結果，以及你在程式碼中發現的任何可疑之處
（例如未宣告的訊號、看起來像 bug 的地方）。
