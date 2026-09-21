# Lab 1 作業指引 — section author brief

You are writing sections of a **task-oriented assignment guide** (Traditional Chinese, 台灣用語) for the homework in
`<repo>/lab1/lab1` (handout `<repo>/lab1/lab1.pdf`; read it with `pdftotext -layout`).
`<repo>` = `/Users/q12we34rt5/work/projects/verilog/computer-architecture`.

The guide lives in `<repo>/helper-web/lab1/lab1-guide/` and is a sibling of two finished courses:

- `../riscv-cpu-course/` — the concept course (22 chapters: ISA, datapath, control table, hazards, bypass, muldiv,
  riscvlong, testing). **It already explains the theory in depth.**
- `../verilog-course/` — basic Verilog.

**The guide is not a third course.** Its job: the reader is unfamiliar with this homework and wants to know *what to
do, in what order, in which file, with which command, and how to tell it is done*. Every section is a station on a
route: goal → files to touch → steps → how to verify (exact command + expected output) → common mistakes →
checklist → "想深入" links into the course. Keep theory to the minimum needed to act, then link to the course chapter.

## First, read

1. `../riscv-cpu-course/AGENT_BRIEF.md` — **all of its SVG conventions, CSS classes, "Verify your drawings", teaching
   rules and "Shared facts" apply here unchanged.** (Ignore its file/chapter-numbering specifics.)
2. `src/00-head.html` in this folder — CSS (same design system as the course + the guide-only components below).
3. The handout, and the real source files you talk about. Every fact about the code must be read from the source.
4. The course chapter(s) that cover your topic (listed in your task), so you link to them instead of repeating them,
   and so your terminology matches. Course chapter ids/titles:
   ch4 五級管線總覽 · ch5 控制表 · ch6 走一遍五道指令 · ch7 ALU 與分支條件 · ch8 加一道新指令的方法 (Obj 1) ·
   ch9 時空圖與 IPC · ch10 bubble/stall/squash · ch11 data hazard · ch12 control hazard · ch13 val/rdy 記憶體 ·
   ch14 Bypass · ch15 Bypass 控制邏輯與 load-use · ch16 用測試巨集驗證 bypass · ch17 乘除法器怎麼掛在管線上 ·
   ch18 mulh 家族 (Obj 2) · ch19 riscvlong (Obj 4) · ch20 從 .S 到 PASSED · ch21 除錯方法與速查表 · chA 控制表速查.
   Link as `<a href="../riscv-cpu-course/index.html#ch15">圖解課第 15 章</a>`.

## The user's hard requirement

**Every example must come with a picture whenever it can be drawn.** A "picture" here is an inline SVG `<figure>`
following the course conventions. For a guide, good figures are: route maps, file/directory trees with the files to
edit highlighted (`.af`), "which lines of the Makefile to uncomment" diagrams, tool-flow diagrams (.S → .elf → .vmh →
sim → .out), datapath excerpts with the affected mux/path highlighted (`.a`), pipeline time–space diagrams
(`pc`, `pc-hold`, `pc-bub`, `pc-kill`, `pc-fwd` cells), before/after comparisons, tarball structure. Text-only is
acceptable only for things like a shell command listing. Aim for roughly one figure per `<h3>`.

## Files

- You write exactly one file: `src/NN-name.html` (given in your task): a sequence of
  `<section class="ch" id="chN" data-part="…" data-nav="…">` fragments, nothing else. Do not touch other files.
- Section skeleton (same as the course, eyebrow wording differs):

```html
<!-- ============================================================ ch3 -->
<section class="ch" id="ch3" data-part="Objective 1" data-nav="短的目錄標題">
<p class="eyebrow">第 3 站 · Objective 1（35%）</p>
<h2>標題</h2>
…
</section>
```

- Cross-reference other guide sections with `<a href="#ch5">第 5 站</a>`. Guide sections (ids fixed):
  ch0 作業全貌與路線圖 · ch1 環境、目錄與第一次 build · ch2 工作循環：改→編→測→除錯 ·
  ch3 Obj 1 總覽與開工 · ch4 Obj 1 範例：照講義加 lh · ch5 Obj 1 各類指令攻略 ·
  ch6 Obj 2 mulh/mulhu/mulhsu · ch7 Obj 3 開工：setup.sh 與 Makefile · ch8 Obj 3 bypass 實作路線 ·
  ch9 Obj 4 riscvlong · ch10 Benchmark 評估 · ch11 打包繳交 · ch12 時程建議與最後總檢查.

## Guide-only components (CSS already exists)

```html
<!-- numbered procedure -->
<ol class="steps">
  <li><b>步驟標題</b><p>說明…</p><pre><code>% make check-asm-riscvstall</code></pre></li>
</ol>

<!-- persistent checklist: data-k must be globally unique, stable, lowercase, prefixed with your section id -->
<ul class="todo" data-title="完成檢查表">
  <li><label><input type="checkbox" data-k="ch3-read-table"><span>看懂控制表 20 個欄位各接到哪裡</span></label></li>
</ul>
<!-- compact grid variant, for per-instruction ticking -->
<ul class="todo grid" data-title="Register-Immediate（7 道）">
  <li><label><input type="checkbox" data-k="ch5-andi"><span>andi</span></label></li>
</ul>

<!-- pointer into the courses -->
<div class="more"><b>想深入</b><p><a href="../riscv-cpu-course/index.html#ch8">圖解課第 8 章</a>：……</p></div>
```

Also available from the course: `.note`, `.trap`, `.quiz`, `.tbl`, `.ex` + `.src` / `.src.mine`, `<pre><code>`
(no language class for shell/asm/Makefile; `language-verilog` for Verilog). Shell prompts use `% ` like the handout.
Each section should end with one `.todo` checklist (5–10 concrete, verifiable items) and one `.more` box.

## Academic-integrity rule (important — this site is pushed to a PUBLIC GitHub repo)

This is graded homework. **Do not publish solutions.** Specifically never print: a control-table row that is not
already in the shipped source or in the handout (the 11 shipped rows + the handout's `lh` row are fine); complete
`*_taken_Xhl` additions; complete bypass mux / bypass-select / load-use stall code; the modified multiplier; the
riscvlong integration code; finished mulh test vectors lists. What you *should* give: where to edit, what shape the
edit has (`示意範例` with `...` elisions and placeholder names the handout itself suggests, e.g. `rs1_X_byp_Dhl`,
`is_load_Xhl`), how to derive the values (which existing row to copy from, which columns differ and why), how to test,
what failure looks like. One fully worked derivation per *category* is acceptable only when the handout or shipped code
already reveals it; otherwise stop at "these N columns differ from row X; look up the values in 控制表速查".

## Verified facts about this repo (beyond the course brief's "Shared facts")

- State of the user's working copy: `riscvstall-CoreCtrl.v` has the `lh` row added (line 443) and `build/Makefile`
  has `riscv-lh.vmh` appended to `tests` and `-march=rv32imzicsr`. `riscvbyp/` and `riscvlong/` contain only
  `setup.sh`. Quote shipped code with line numbers from the actual files (verify with `sed -n`).
- Control table: `casez (ir_Dhl)` at CoreCtrl.v 411–470. 11 shipped rows (lui auipc addi ori add lw sw jal bne blt
  csrw); every other instruction is a commented-out stub `// \`RISCV_INST_MSG_XXX :cs={};`. Instructions to add for
  Obj 1: andi xori slti sltiu slli srli srai · sub sll slt sltu xor srl sra or and · lb lbu (lh) lhu sb sh · jalr ·
  beq bltu bge bgeu · mul div divu rem remu  (= 7+9+6+1+4+5 = 32, `lh` being the handout's example).
  Branches additionally need new `*_taken_Xhl` wires OR-ed into `any_br_taken_Xhl` (CoreCtrl.v 660–665);
  the six `branch_cond_*_Xhl` inputs already exist (CoreCtrl.v 58–63, CoreDpath.v 262–268).
  `br_*`, `pm_r`, `alu_*`, `md_*`, `mdm_*`, `ml_*`, `dmm_*` localparams all already exist (CoreCtrl.v 251–359).
- An instruction with no row → `cs` stays all-x → the assertion at CoreCtrl.v 876–889 prints
  `RTL-ERROR : ... Illegal instruction!` and `$finish`es after two in a row.
- Build system in THIS repo: `build/Makefile` itself compiles tests: `%.elf` from `tests/riscv/%.S`, → `.dump` →
  `.vmh` (rules at Makefile ~84–97), so for assembly tests it is enough to append `riscv-xxx.vmh` to `tests =`
  (Makefile 41–52) and run `make check-asm-riscvstall`. `VPATH` also looks in `tests/build/vmh` and
  `ubmark/build/vmh`. The handout's `tests/` configure → make → `../convert` flow also works (`tests/build/` exists
  here; it uses `tests/riscv/riscv.mk`, where all the non-shipped tests are commented out below a blank line and the
  three mulh ones are marked `# TODO:`). Benchmarks (`bmarks =`) have **no** build rule in `build/Makefile`: they need
  `ubmark/` configure → make → `../convert` (`ubmark/build/` does not exist yet in the user's copy).
- Test output (`build/riscv-lh-stall.out`): `*** PASSED ***` then STATS `status / num_cycles / num_inst / ipc`.
  `make check-asm-*` prints one `[ PASSED ]`/`[ FAILED ]`-style summary line per test via perl.
- Enabling riscvbyp / riscvlong in `build/Makefile` = uncomment **five** places each, all marked
  `# Enable these after running their setup.sh scripts.`: `subpkgs +=` (~69–70), `sim_incs += -I` (~117–118),
  `proc_template` (~178–179), `asm_template` (~214–215), `bmark_template` (~259–260). Verify exact line numbers.
- `riscvbyp/setup.sh`: rsync everything from `../riscvstall/` (except setup.sh), rename `riscvstall*` →
  `riscvbyp*`, `sed` the string inside every file. `riscvlong/setup.sh` does the same from `../riscvbyp/`.
  Consequence: re-running setup.sh later **overwrites** work in the target directory; fixes made later in riscvstall
  do not propagate automatically.
- `tests/riscv/riscv-mulh.S`, `-mulhu.S`, `-mulhsu.S` exist as stubs (`# TODO` between TEST_RISCV_BEGIN/END).
  `InstMsg.v` 147–149 (defines), 400–402 and 467–469 (disasm) have the three mulh lines commented out.
  `imuldiv-MulDivReqMsg.v` 30–34 defines FUNC_MUL..REMU = 3'd0..3'd4 (3-bit field, 5–7 free); its disasm `case` is
  near line 129. `imuldiv_IntMulDivIterative` routes `fn == MUL` to the multiplier, everything else to the divider
  (lines 32–39) — new mul functions must be routed to the multiplier too. The multiplier takes no `fn` today.
- `riscvstall-CoreDpathPipeMulDiv.v`: module `riscv_CoreDpathPipeMulDiv`, same req/resp ports as the iterative unit
  plus `stall_Xhl, stall_Mhl, stall_X2hl, stall_X3hl` inputs ("These need to be hooked up to something!"); it only
  knows MUL/DIV/DIVU/REM/REMU in `result0` (lines 139–145) — mulh family must be added there for riscvlong.
  It is already in `riscvstall.mk`'s source list but not instantiated anywhere.
- Handout section 6.1 list of files to modify: riscvstall-CoreCtrl.v, riscvstall-InstMsg.v ·
  imuldiv-IntMulIterative.v, imuldiv-IntMulDivIterative.v, imuldiv-MulDivReqMsg.v · riscvbyp-CoreCtrl.v,
  -CoreDpath.v, -Core.v · riscvlong-CoreCtrl.v, -CoreDpath.v, -Core.v, -CoreDpathPipeMulDiv.v.
- Tools on the user's machine (macOS): iverilog 12, gtkwave, riscv32-unknown-elf-gcc all installed and working.

## Style

Second person, direct, no filler, no emoji. Commands exactly as the user would type them. When you state an expected
output, it must be real (run it if cheap: `cd <repo>/lab1/lab1/build && make check-asm-riscvstall` works and is safe —
but **never modify anything under `<repo>/lab1/`**; it is the user's homework working copy. Read-only there.)

## Verify (mandatory)

```sh
cd <repo>/helper-web/lab1/lab1-guide
tools/figshot.sh src/NN-name.html          # → .figshot/NN-name/fig-K.png  (use FIGSHOT_OUT=.figshot-NN to avoid collisions)
```

Read every PNG, fix overlaps / clipping / wires through labels, iterate until clean; spot-check dark mode with the
`dark` argument. Do not run `./build.sh` (the coordinator does). Finish by reporting: sections written, number of
figures, anything you were unsure about or facts you could not verify.
