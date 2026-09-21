#!/usr/bin/env python3
"""Generate src/70-appendix.html — 附錄 A：控制表速查.

Everything value-related is read from the real sources, so the appendix follows the code:
  * localparam section of <lab>/riscvstall/riscvstall-CoreCtrl.v  -> the value listing
  * RISCV_INST_MSG_* control-bundle defines of riscvstall-InstMsg.v -> bit ranges
  * the uncommented rows of the casez table                        -> "rows you already have"
New localparams you add (e.g. md_mulh) show up after rerunning this script; give them a
Chinese note in NOTE below, otherwise the comment from the source file is used.

Usage: tools/gen-appendix.py [riscvstall|riscvbyp|riscvlong]   then ./build.sh
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'lab1', 'lab1'))
VARIANT = sys.argv[1] if len(sys.argv) > 1 else 'riscvstall'
CTRL = os.path.join(LAB, VARIANT, VARIANT + '-CoreCtrl.v')
MSG = os.path.join(LAB, VARIANT, VARIANT + '-InstMsg.v')
OUT = os.path.join(HERE, '..', 'src', '70-appendix.html')

# casez header, macro, signal it becomes (stage), one-liner, listing group id, ch5 detail anchor
FIELDS = [
    ('val',            'INST_VAL',   '只給結尾的 assertion 讀',                       'D', '這一列是合法指令。每一列都填 <code>y</code>',                          'yn',  'fld1'),
    ('j taken',        'J_EN',       '<code>brj_taken_Dhl</code>',                     'D', 'D 級就確定要跳的無條件跳躍（<code>jal</code>／<code>jalr</code>）',       'yn',  'fld1'),
    ('br type',        'BR_SEL',     '<code>br_sel_Xhl</code>',                        'X', '條件分支的種類；X 級用它挑 <code>branch_cond_*_Xhl</code>',              'br',  'fld1'),
    ('pc muxsel',      'PC_SEL',     '<code>pc_mux_sel_Dhl</code> → <code>pc_mux_sel_Phl</code>', 'P', 'PC mux 選誰——只有 <code>j taken = y</code> 時才被採用',      'pm',  'fld1'),
    ('op0 muxsel',     'OP0_SEL',    '<code>op0_mux_sel_Dhl</code>',                   'D', 'ALU <code>in0</code>（乘除法器 <code>a</code>）的來源',                    'am',  'fld2'),
    ('rs1 en',         'RS1_EN',     '<code>rs1_en_Dhl</code>',                        'D', '指令真的會讀 rs1 嗎（冒險偵測／bypass 用，不碰 mux）',                    'yn',  'fld2'),
    ('op1 muxsel',     'OP1_SEL',    '<code>op1_mux_sel_Dhl</code>',                   'D', 'ALU <code>in1</code>（乘除法器 <code>b</code>）的來源',                    'bm',  'fld2'),
    ('rs2 en',         'RS2_EN',     '<code>rs2_en_Dhl</code>',                        'D', '指令真的會讀 rs2 嗎（store 也算）',                                       'yn',  'fld2'),
    ('alu fn',         'ALU_FN',     '<code>alu_fn_Xhl</code>',                        'X', 'ALU 做哪一種運算',                                                         'alu', 'fld3'),
    ('md fn',          'MULDIV_FN',  '<code>muldivreq_msg_fn_Xhl</code>',              'X', '乘除法器做哪一種運算',                                                     'md',  'fld3'),
    ('md en',          'MULDIV_EN',  '<code>muldivreq_val</code>',                     'X', '要不要啟動乘除法器（啟動後管線會等它）',                                   'yn',  'fld3'),
    ('md muxsel',      'MULDIV_SEL', '<code>muldiv_mux_sel_Xhl</code>',                'X', '64 位元結果取低半還是高半',                                                'mdm', 'fld3'),
    ('ex muxsel',      'EX_SEL',     '<code>execute_mux_sel_Xhl</code>',               'X', 'X 級的結果取 ALU 還是乘除法器',                                            'em',  'fld3'),
    ('mem rq',         'MEM_REQ',    '<code>dmemreq_val</code>、<code>dmemreq_msg_rw</code>', 'X', '要不要存取資料記憶體、讀還是寫',                                  'mrq', 'fld4'),
    ('mem len',        'MEM_LEN',    '<code>dmemreq_msg_len</code>',                   'X', '存取幾個 byte',                                                            'ml',  'fld4'),
    ('memresp muxsel', 'MEM_SEL',    '<code>dmemresp_mux_sel_Mhl</code>',              'M', 'load 讀回來的資料怎麼延伸成 32 位元',                                      'dmm', 'fld4'),
    ('wb muxsel',      'WB_SEL',     '<code>wb_mux_sel_Mhl</code>',                    'M', '寫回的值取 X 級結果還是記憶體回應',                                        'wm',  'fld5'),
    ('rf wen',         'RF_WEN',     '<code>rf_wen_out_Whl</code>（中途的 <code>rf_wen_Xhl/_Mhl/_Whl</code> 給冒險比對）', 'W', '要不要寫 regfile',                     'yn',  'fld5'),
    ('wa',             'RF_WADDR',   '<code>rf_waddr_Whl</code>（中途的值同樣給冒險比對）', 'W', '寫到哪個暫存器',                                                    'reg', 'fld5'),
    ('csr wen',        'CSR_WEN',    '<code>csr_wen_Whl</code>',                       'W', '要不要寫 CSR（只有 <code>csrw</code>）',                                   'yn',  'fld5'),
]

# source comment header -> (group id, which column(s) may use these values)
GROUPS = {
    'Generic Parameters':         ('yn',  'val · j taken · rs1 en · rs2 en · md en · rf wen · csr wen（是／否；不可填 x）'),
    'Register specifiers':        ('reg', 'wa（RF_WADDR）'),
    'Branch Type':                ('br',  'br type（BR_SEL）'),
    'PC Mux Select':              ('pm',  'pc muxsel（PC_SEL）'),
    'Operand 0 Mux Select':       ('am',  'op0 muxsel（OP0_SEL）'),
    'Operand 1 Mux Select':       ('bm',  'op1 muxsel（OP1_SEL）'),
    'ALU Function':               ('alu', 'alu fn（ALU_FN）'),
    'Muldiv Function':            ('md',  'md fn（MULDIV_FN）'),
    'MulDiv Mux Select':          ('mdm', 'md muxsel（MULDIV_SEL）'),
    'Execute Mux Select':         ('em',  'ex muxsel（EX_SEL）'),
    'Memory Request Type':        ('mrq', 'mem rq（MEM_REQ）'),
    'Subword Memop Length':       ('ml',  'mem len（MEM_LEN）'),
    'Memory Response Mux Select': ('dmm', 'memresp muxsel（MEM_SEL）'),
    'Writeback Mux 1':            ('wm',  'wb muxsel（WB_SEL）'),
}

SHIPPED = {'LUI', 'AUIPC', 'ADDI', 'ORI', 'ADD', 'LW', 'SW', 'JAL', 'BNE', 'BLT', 'CSRW'}

NOTE = {
    'n': '否', 'y': '是',
    'rx': "don't care：rf wen = n 的列填它", 'r0': '寫到 x0（會被 regfile 忽略；用不到）',
    'br_x': '不要用：x 會流進 brj_taken_Xhl', 'br_none': '不是分支（所有非分支指令）',
    'br_beq': 'beq　看 branch_cond_eq_Xhl', 'br_bne': 'bne　看 branch_cond_ne_Xhl（已接好）',
    'br_blt': 'blt　看 branch_cond_lt_Xhl（已接好）', 'br_bltu': 'bltu　看 branch_cond_ltu_Xhl',
    'br_bge': 'bge　看 branch_cond_ge_Xhl', 'br_bgeu': 'bgeu　看 branch_cond_geu_Xhl',
    'pm_x': "don't care", 'pm_p': 'pc + 4（所有不轉向的指令）', 'pm_b': 'branch_targ_Xhl（分支；實際由 X 級硬選）',
    'pm_j': 'jump_targ_Dhl = pc + imm_uj（jal）', 'pm_r': 'jumpreg_targ_Dhl = (rs1 + imm_i) & ~1（jalr）',
    'am_x': "don't care（這個 lab 用不到）", 'am_rdat': 'rs1 的值（幾乎所有指令）', 'am_pc': 'pc_Dhl（auipc）',
    'am_pc4': 'pc + 4，返回位址（jal／jalr）', 'am_0': '常數 0（lui）',
    'bm_x': "don't care（這個 lab 用不到）", 'bm_rdat': 'rs2 的值（R-type、分支、M 指令）', 'bm_shamt': 'inst[24:20] 補 0（slli／srli／srai）',
    'bm_imm_u': '{inst[31:12], 12\'b0}（lui、auipc）', 'bm_imm_sb': '分支位移——目前沒有任何一列用它',
    'bm_imm_i': 'I 型立即數（addi 一族、所有 load）', 'bm_imm_s': 'S 型立即數（所有 store）', 'bm_0': '常數 0（jal、csrw：讓 ALU 原樣通過 op0）',
    'alu_x': "don't care：只有 M 指令能填", 'alu_add': 'in0 + in1（加法、所有位址計算、借 ALU 搬值）',
    'alu_sub': 'in0 − in1（sub；要比大小的分支）', 'alu_sll': 'in0 << in1[4:0]', 'alu_or': 'in0 | in1',
    'alu_lt': '有號 in0 < in1 ? 1 : 0（slt／slti）', 'alu_ltu': '無號 in0 < in1 ? 1 : 0（sltu／sltiu）', 'alu_and': 'in0 & in1',
    'alu_xor': 'in0 ^ in1（xor；只比「相不相等」的分支）', 'alu_nor': '~(in0 | in1)（MIPS 留下來的，用不到）',
    'alu_srl': 'in0 >> in1[4:0]，補 0', 'alu_sra': 'in0 >>> in1[4:0]，補符號位元',
    'md_x': "don't care：md en = n 的列", 'md_mul': '有號乘法，64 位元乘積', 'md_div': '有號除法 → {餘數, 商}',
    'md_divu': '無號除法 → {餘數, 商}', 'md_rem': '同 md_div（差別在 md muxsel 取高半）', 'md_remu': '同 md_divu',
    'mdm_x': "don't care：md en = n 的列", 'mdm_l': '[31:0]：乘積低半／商（mul、div、divu）', 'mdm_u': '[63:32]：乘積高半／餘數（rem、remu、mulh 家族）',
    'em_x': "don't care：X 級結果沒人要（load、store、分支）", 'em_alu': 'ALU 輸出', 'em_md': '乘除法器輸出（M 指令）',
    'nr': '不存取記憶體', 'ld': 'load：dmemreq_val = 1, rw = 0', 'st': 'store：dmemreq_val = 1, rw = 1',
    'ml_x': "don't care：mem rq = nr 的列", 'ml_w': '4 bytes（lw、sw）——注意編碼是 0', 'ml_b': '1 byte（lb、lbu、sb）', 'ml_h': '2 bytes（lh、lhu、sh）',
    'dmm_x': "don't care：不是 load 的列", 'dmm_w': '原樣（lw）', 'dmm_b': '[7:0] 符號延伸（lb）', 'dmm_bu': '[7:0] 補 0（lbu）',
    'dmm_h': '[15:0] 符號延伸（lh）', 'dmm_hu': '[15:0] 補 0（lhu）',
    'wm_x': "don't care：不寫回的列（分支、store）", 'wm_alu': 'X 級的結果（ALU 或乘除法器）', 'wm_mem': '記憶體回應（所有 load）',
}


def esc(s):
    return html.escape(s, quote=False)


def main():
    ctrl = open(CTRL, encoding='utf-8', errors='replace').read().split('\n')
    msg = open(MSG, encoding='utf-8', errors='replace').read()
    rel = VARIANT + '/' + os.path.basename(CTRL)

    # ---- bit ranges of the control bundle
    bits = dict(re.findall(r'`define RISCV_INST_MSG_(\w+)\s+(\d+:\d+)\s*$', msg, re.M))
    cs_sz = re.search(r'`define RISCV_INST_MSG_CS_SZ\s+(\d+)', msg).group(1)

    # ---- localparam listing, grouped by the source's own comment headers
    start = next(i for i, l in enumerate(ctrl) if 'Decode Stage: Constants' in l)
    end = next(i for i, l in enumerate(ctrl) if 'Decode Stage: Logic' in l)
    groups, cur = [], None
    for i in range(start, end):
        l = ctrl[i]
        m = re.match(r'\s*//\s*(.+?)\s*$', l)
        if m and m.group(1) in GROUPS:
            cur = dict(title=m.group(1), first=i + 1, last=i + 1, vals=[]); groups.append(cur); continue
        m = re.match(r"\s*localparam\s+(\w+)\s*=\s*([^;]+);\s*(?://\s*(.*))?$", l)
        if m and cur is not None:
            cur['vals'].append((m.group(1), m.group(2).strip(), (m.group(3) or '').strip())); cur['last'] = i + 1
    lo, hi = groups[0]['first'], groups[-1]['last']

    L = []
    for g in groups:
        gid, cols = GROUPS[g['title']]
        L.append('<span class="hljs-comment" id="ref-%s">// ── %s ── 第 %d–%d 行</span>' % (gid, esc(cols), g['first'], g['last']))
        w = max(len(n) for n, _, _ in g['vals'])
        vw = max(len(v) for _, v, _ in g['vals'])
        for n, v, cmt in g['vals']:
            note = NOTE.get(n) or cmt or ''
            L.append('<span class="hljs-keyword">localparam</span> %s = <span class="hljs-number">%s</span>;%s<span class="hljs-comment">// %s</span>'
                     % (esc(n.ljust(w)), esc(v), ' ' * (vw - len(v) + 2), esc(note)))
        if gid == 'reg':
            L.append('<span class="hljs-keyword">wire</span> [4:0] %s = inst_rd_Dhl;%s<span class="hljs-comment">// 不是常數：指令的 rd 欄位 inst[11:7]。rf wen = y 的列都填它</span>' % ('rd', ' '))
        L.append('')
    listing = '\n'.join(L).rstrip('\n')

    # ---- rows that already exist in the casez table
    cz = next(i for i, l in enumerate(ctrl) if re.search(r'casez\s*\(\s*ir_Dhl', l))
    ce = next(i for i in range(cz, len(ctrl)) if 'endcase' in ctrl[i])
    # only the rows that shipped with the lab: rows you add yourself are homework and must not end up in the page
    rows = [re.sub(r'^\s+', '', l.rstrip()) for l in ctrl[cz:ce]
            if (lambda m: m and m.group(1) in SHIPPED)(re.match(r'\s*`RISCV_INST_MSG_(\w+)\s*:cs=', l))]
    raw_hdr = [l for l in ctrl[cz:ce] if re.match(r'\s*//\s+(j |val )', l)]
    base = min(len(l) - len(l.lstrip()) for l in ctrl[cz:ce] if l.strip().startswith('`RISCV'))
    rows_txt = '\n'.join([l[base:].rstrip() for l in raw_hdr] + rows)
    n_rows = len(rows)

    # ---- field table
    T = []
    for i, (hd, macro, sig, stage, what, gid, anchor) in enumerate(FIELDS):
        b = bits.get(macro, '?')
        hi_, lo_ = b.split(':')
        rng = 'cs[%s]' % hi_ if hi_ == lo_ else 'cs[%s]' % b
        T.append('<tr><td class="num">%d</td><td><code>%s</code></td><td class="mac"><code>%s</code> <span class="bitr">%s</span></td><td>%s</td><td>%s</td><td class="stg">%s</td>'
                 '<td><a href="#ref-%s">值</a> · <a href="#%s">詳解</a></td></tr>' % (i + 1, hd, macro, rng, what, sig, stage, gid, anchor))

    out = '''<!-- GENERATED by tools/gen-appendix.py from %s — do not edit by hand -->
<!-- ============================================================ chA -->
<section class="ch" id="chA" data-part="附錄" data-nav="控制表速查">
<p class="eyebrow">附錄 A · 速查</p>
<h2>控制表速查：20 個欄位、所有可填的值</h2>
<p>填控制表時只需要這一頁。上半是<b>欄位表</b>（每一欄是什麼、接到哪條訊號、在哪一級被用到）；下半是<b>值的清單</b>，照 <code>%s</code> 的 <code>localparam</code> 原樣條列，每一段開頭的註解標明「這些值是給哪一欄用的」。想知道為什麼，點「詳解」回到<a href="#ch5">第 5 章</a>對應的那一組。</p>
<p class="refhint">在任何章節都可以按右下角的 <b>控制表速查</b> 按鈕（或鍵盤 <kbd>?</kbd>）把這一頁叫出來，不用離開正在讀的地方。</p>

<h3 id="ref-fields">欄位表（由左到右 = 大括號裡的順序 = cs[%d] → cs[0]）</h3>
<div class="tbl"><table class="reftbl">
<thead><tr><th>#</th><th>表頭</th><th>巨集 · 位元</th><th>這一欄在決定什麼</th><th>變成哪條訊號</th><th>級</th><th>查</th></tr></thead>
<tbody>
%s
</tbody></table></div>
<p class="refhint">「級」是這個欄位<b>真正被用掉</b>的那一級：所有欄位都在 D 級由 <code>casez</code> 產生，再跟著指令經過管線暫存器走到那裡（<code>alu_fn_Dhl → alu_fn_Xhl</code>）。</p>

<h3 id="ref-values">可填的值（%s 第 %d–%d 行）</h3>
<p>編碼就是 mux 的第幾個輸入，也是你在波形上會看到的數字。註解是中文說明；<code>*_x</code> 一律是 don't care。</p>
<pre class="ref"><code>%s</code></pre>

<h3 id="ref-rows">lab 一開始就寫好的 %d 列（可以直接拿來對照）</h3>
<p>其餘的列在原始檔裡是 <code>// `RISCV_INST_MSG_XXX :cs={};</code> 的空殼，等你填。你自己加的列不會出現在這裡。</p>
<pre><code class="language-verilog">%s</code></pre>
</section>
''' % (rel, rel, int(cs_sz) - 1, '\n'.join(T), rel, lo, hi, listing, n_rows, esc(rows_txt))
    open(OUT, 'w', encoding='utf-8').write(out)
    print('wrote %s: %d fields, %d value groups, %d shipped rows' % (os.path.relpath(OUT), len(FIELDS), len(groups), n_rows))


if __name__ == '__main__':
    main()
