# RISC-V CPU 圖解課 — chapter author brief

You are writing chapters of an **advanced, diagram-first course** (Traditional Chinese, 台灣用語) that teaches the
RISC-V ISA and the 5-stage pipelined CPU of `lab1`. It is the sequel to the finished basic course in
`../verilog-course/` ("every line of Verilog is a circuit"). The reader:

- has finished the basic course: knows wire/reg, mux = `?:`, `always @(posedge clk)` = flip-flops, FSM,
  val/rdy handshake basics, pipeline register with enable, the `_Dhl/_Xhl` suffix convention;
- **does not know RISC-V or computer architecture** (pipelining, hazards, bypassing are new);
- is working on the lab in `<repo>/lab1/lab1` (handout: `<repo>/lab1/lab1.pdf`, use `pdftotext -layout`).
  `<repo>` = `/Users/q12we34rt5/work/projects/verilog/computer-architecture`.

The user's one hard requirement: **every example should come with a picture** whenever the code can be drawn.
Text-only explanation is acceptable only when a drawing genuinely adds nothing (e.g. a shell command).

## Files

- You write exactly one file: `src/NN-name.html` (given in your task). It is an HTML *fragment*: a sequence of
  `<section class="ch" ...>` elements, nothing else. Do not touch other files in `src/`.
- `src/00-head.html` holds all CSS + the shared SVG `<defs>` (gates `#g-and #g-or #g-nor #g-xor #g-not`,
  arrowheads `#ah` (ink) and `#ahc` (control blue)). **Read it first.** Do not add `<style>` blocks or inline
  colours; use the classes below so light/dark themes both work. `style="stroke-dasharray:none"` style tweaks on a
  single element are fine.
- Read `../verilog-course/src/30-seq.html` and `../verilog-course/src/50-design.html` as the **style reference**
  for prose tone, chapter structure, figure density and SVG technique. Match that quality.

## Chapter skeleton

```html
<!-- ============================================================ ch7 -->
<section class="ch" id="ch7" data-part="一條指令的旅程" data-nav="短的目錄標題">
<p class="eyebrow">第 7 章 · 一條指令的旅程</p>
<h2>章標題</h2>
<p>…</p>

<div class="ex">
<div class="src">riscvstall/riscvstall-CoreCtrl.v · 第 557–575 行</div>      <!-- real code: file + line numbers -->
<!-- or: <div class="src mine">示意範例</div> for code you wrote for illustration -->
<pre><code class="language-verilog">…escaped code…</code></pre>
<figure>
<div class="fig-scroll">
<svg viewBox="0 0 720 240" role="img" aria-label="一句完整描述這張圖在畫什麼的中文">
  …
</svg>
</div>
<figcaption><b>一句話重點。</b>補充說明。</figcaption>
</figure>
</div>
</section>
```

- `id` must be `chN` with the numbers given in your task; `data-part` exactly as given (it groups the TOC).
- Cross-reference other chapters with `<a href="#ch12">第 12 章</a>`; the basic course with
  `<a href="../verilog-course/index.html#ch15">基礎篇第 15 章</a>` (basic course ids: ch4 mux, ch5 concat,
  ch7 DFF, ch9 regfile, ch11 casez/`define, ch13 FSM, ch14 iterative multiplier + val/rdy, ch15 pipeline regs & stall).
- Other blocks available: `<div class="note"><b>標題</b><p>…</p></div>`, `<div class="trap"><b>常見錯誤</b><p>…</p></div>`,
  tables as `<div class="tbl"><table>…</table></div>` (`td.num` for mono numbers, `tr.hi` to highlight a row),
  and self-check questions:
  `<div class="quiz"><b>想一想</b><p>問題</p><details><summary>看答案</summary><p>…</p></details></div>`.
- Assembly snippets: `<pre><code class="language-x86asm">` is NOT loaded; use `<pre><code>` (no language class) for
  assembly / shell, `language-verilog` for Verilog. Escape `<` `>` `&` inside code (`&lt;=`).
- Code excerpts must be **copied from the real file** with correct line numbers (trim with `...` if long).
  Never invent line numbers. Verify with `sed -n 'A,Bp' file`.

## SVG conventions (must follow)

- `viewBox="0 0 W H"` with W between 560 and 780 (the build caps display width at 1.15×W). Keep 12px mono text
  legible: do not cram. Always `role="img"` + a full-sentence `aria-label`.
- Text: default is 12px mono (signal names). Add `class="zh"` for Chinese/prose labels, `s` small, `mut` muted,
  `cb` control-blue, `sq` register-copper, `ac` accent-teal, `wr` warning-red, `hd` bold heading.
- Shapes: `.w` data wire, `.wm` muted dashed wire, `.c` control wire (blue dashed), `.k` combinational block,
  `.r` register box (copper), `.rl` register clock triangle / copper line, `.re` copper dashed guide,
  `.d` junction dot (r=3), `.dc` control dot, `.x` red cross-out / error stroke, `.a` **accent highlighted path**
  (use for "the path this figure is about"), `.af` accent-filled box, `.gh` ghost box, `.grp` dashed grouping outline.
- Mux = trapezoid `<path class="k" d="M110 50L136 60V130L110 140Z"/>` with small input labels; select line is
  `.c` entering from the bottom/top. Register = `.r` rect plus clock triangle `.rl`. Arrowheads:
  `marker-end="url(#ah)"` on `.w`, `url(#ahc)` on `.c`.
- Instruction bit-field rectangles: classes `f-op f-rd f-rs1 f-rs2 f-fn f-imm` (opcode / rd / rs1 / rs2 /
  funct3+funct7 / immediate). Use these colours consistently across the whole course.
- Pipeline (time–space) diagrams: one row per instruction, one column per cycle, cells are
  `<rect class="pc" …>` with the stage letter centred; `pc-hold` = stage stalled this cycle (letter repeats),
  `pc-bub` = bubble, `pc-kill` = squashed, `pc-fwd` = cell that sends/receives a forwarded value. Cell size 34×26,
  2px gap. Put cycle numbers on top, instruction text (mono) on the left.
- Stage order left→right everywhere: P/F, D, X, M, W. Pipeline registers are tall thin `.r` rects between stages.
- Wires are orthogonal (H/V segments only), no wire crosses a label, junction dots where wires branch.
  Draw what the code says: every mux input, register and signal name in a figure must exist in the quoted source
  (or be clearly marked 示意 when it is something the student will add, e.g. bypass muxes).

## Verify your drawings (mandatory)

You draw blind, so you must look at the result:

```sh
cd <repo>/helper-web/lab1/riscv-cpu-course
tools/figshot.sh src/NN-name.html          # renders each <figure> to .figshot/NN-name/fig-K.png
```

Then **Read every PNG** and fix: overlapping text, text outside boxes or clipped by the viewBox, wires through
labels, misaligned arrows, unreadable crowding, wrong mux input order. Iterate until clean. Also spot-check a few
with `tools/figshot.sh src/NN-name.html dark`. Budget your effort: a correct, clean, medium-complexity figure beats
an ambitious broken one.

## Teaching rules

- One idea per figure; introduce a term in Chinese with the English in parentheses the first time:
  「冒險 (hazard)」「旁路／前饋 (bypass / forwarding)」.
- Always tie concept → this CPU's actual signal names → the lab Objective it helps with.
- The lab is graded homework. Teach **how to derive** answers (worked example + reasoning + hints + 想一想),
  do not print the complete finished control table or a complete drop-in bypass implementation. Worked examples
  that the handout itself gives (e.g. `lh`) or one representative per category are fine, as are 示意範例 snippets
  that show the *shape* of a solution.
- Be precise. If you state a fact about the code, you must have read it in the source. No invented signals.
- No emoji. No filler intros ("在本章中我們將…" once is fine, do not pad).

## Shared facts (already verified — rely on these)

- Stages: P (pc mux, `_Phl`), F, D, X, M, W. Instruction fetch request is sent in P, response consumed in F→D.
  Reset vector `0x00080000`. Regfile reads in D (combinational), writes in W (posedge), x0 hard-wired to 0.
- Control is NOT an FSM: `casez (ir_Dhl)` fills a 39-bit bundle `cs` (fields in `riscvstall-InstMsg.v` 167–187),
  each field is pipelined to the stage that uses it (`alu_fn_Dhl → alu_fn_Xhl`, `rf_wen_Dhl→Xhl→Mhl→Whl`…).
- Branches resolve in **X** (`brj_taken_Xhl`, target `branch_targ_Xhl`, squashes F and D → 2 wasted slots);
  `jal`/`jalr` redirect in **D** (`brj_taken_Dhl` via `J_EN`, squashes F → 1 wasted slot).
  `pc_mux_sel_Phl` priority: X branch > D jump > pc+4.
- Branch conditions come from the ALU result: `eq/ne` from `alu_out == 0`, `lt/ge/ltu/geu` from sign bits +
  `alu_out[31]` (CoreDpath 262–268). Existing rows: `bne` uses `alu_xor`, `blt` uses `alu_sub`. Only
  `bne_taken_Xhl`/`blt_taken_Xhl` exist so far (CoreCtrl 659–664) — new branches need new `*_taken_Xhl` wires.
- ALU shifter quirk: in `riscv_CoreDpathAlu`, the shifter is wired `.alu_a(in1)`, `.alu_b(in0)` — so `in0`(op0) is
  the value being shifted and `in1`(op1) is the shift amount; op1 mux has a `bm_shamt` input.
- Data hazard today (riscvstall): `stall_hazard_Dhl` compares rs1/rs2 (gated by `rs1_en/rs2_en`) with
  `rf_waddr` of X, M, W (gated by `inst_val_*`, `rf_wen_*`, `!= 0`) → stall D until the writer has left W.
- Bubble bit per stage; `inst_val_S = !bubble_S && !squash_S`; stall chain
  `stall_Whl(0) → stall_Mhl → stall_Xhl → stall_Dhl → stall_Fhl`; a stalled stage inserts a bubble into the next.
- Memory ports are val/rdy; `-rand-` simulators add random delay. dmem request in X, response in M.
- Mul/div: iterative unit `imuldiv_IntMulDivIterative` lives in X, val/rdy; D stalls while `!muldivreq_rdy`,
  X stalls while `!muldivresp_val`. 64-bit result, `muldiv_mux_sel_Xhl` picks low (mul/div) or high (rem) half.
  `mulh/mulhsu/mulhu` defines are commented out in InstMsg.v (Objective 2).
- `src/20-datapath.html` figures 0 and 4–8 (ch4 overview, ch6 walkthroughs) are GENERATED by `tools/gen-walk.py` — edit the generator, not the SVG.
- The simulators are built from `Testbench.v` + `Pattern.v` (stats counters live in Pattern.v); `riscvstall-sim.v` is stale and not compiled.
- Tests: `tests/riscv/*.S` use `riscv-macros.h`; pass/fail reported by `csrw 21, x29` (1 = pass, else failing line
  number) → `csr_status`. `+stats=1` prints num_cycles / num_inst / ipc (riscv-add on riscvstall: 468 cycles,
  232 inst, ipc 0.4957).
