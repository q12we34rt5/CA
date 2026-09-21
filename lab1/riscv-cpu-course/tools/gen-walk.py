#!/usr/bin/env python3
"""Regenerate the generated SVGs of src/20-datapath.html in place:

  figure 0      block-level overview of the six stages (ch4)
  figures 4-8   the same simplified D/X/M/W datapath, one per instruction, with the
                active path highlighted (ch6: addi, lw, sw, bne, jal)

Only the <svg>…</svg> of those figures is replaced (aria-label and figcaption stay).
Run from anywhere:  tools/gen-walk.py   then ./build.sh
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'src', '20-datapath.html')


def T(x, y, s, cls='', anchor=None):
    a = ' text-anchor="%s"' % anchor if anchor else ''
    c = ' class="%s"' % cls if cls else ''
    s = s.replace('&', '&amp;').replace('<', '&lt;')
    return '<text%s x="%s" y="%s"%s>%s</text>' % (c, x, y, a, s)


def P(d, cls, extra=''):
    return '<path class="%s" d="%s"%s/>' % (cls, d, extra)


def mux(x, y0, y1, cls='k'):
    return P('M%d %dL%d %dV%dL%d %dZ' % (x, y0, x + 26, y0 + 10, y1 - 10, x, y1), cls)


def bar(x, y0, y1, label):
    return ('<rect class="r" x="%d" y="%d" width="16" height="%d"/>' % (x, y0, y1 - y0)
            + P('M%d %dl8 6l-8 6' % (x, y1 - 22), 'rl')
            + T(x + 8, y0 - 6, label, 's sq', 'middle'))


# ---------------------------------------------------------------------------
# ch6 walkthrough
# ---------------------------------------------------------------------------
# net name -> (path, [(x, y, text, anchor)])
NETS = {
    'rd0':    ('M86 70H200',            [(92, 64, 'rf_rdata0 (rs1)', None)]),
    'pc':     ('M178 92H200',           [(174, 96, 'pc_Dhl', 'end')]),
    'pc4':    ('M178 114H200',          [(174, 118, 'pc_plus4_Dhl', 'end')]),
    'c0a':    ('M178 136H200',          [(174, 140, 'const0', 'end')]),
    'rd1':    ('M55 140V200H200',       [(62, 194, 'rf_rdata1 (rs2)', None)]),
    'shamt':  ('M178 222H200',          [(174, 226, 'shamt', 'end')]),
    'imm':    ('M188 244H200',          []),
    'c0b':    ('M178 266H200',          [(174, 270, 'const0', 'end')]),
    'wdD':    ('M126 200V358H262',      [(132, 372, 'wdata_Dhl', None)]),
    'op0':    ('M226 103H262M278 103H384', [(283, 97, 'op0_mux_out_Xhl', None)]),
    'op1':    ('M226 233H262M278 233H384', [(283, 227, 'op1_mux_out_Xhl', None)]),
    'alu':    ('M440 168H522',          [(444, 162, 'alu_out_Xhl', None)]),
    'alu_ex': ('M522 168H532',          []),
    'alu_br': ('M522 168V92',           []),
    'alu_ad': ('M522 168V330H636',      [(528, 324, 'dmemreq_msg_addr', None)]),
    'md':     ('M440 286H508V204H532',  []),
    'ex':     ('M558 184H596M612 184H748', [(617, 178, 'execute_mux_out_Mhl', None)]),
    'wdX':    ('M278 358H636',          [(283, 352, 'wdata_Xhl → dmemreq_msg_data', None)]),
    'resp':   ('M683 322V270',          [(677, 308, 'dmemresp_msg_data', 'end')]),
    'mresp':  ('M730 256H748',          []),
    'wb':     ('M774 220H784M800 220H812V22H55V55', [(300, 16, 'wb_mux_out_Whl → regfile 寫入埠（W 級寫回）', None)]),
    'jt':     ('M140 319H106',          [(140, 346, 'jump_targ_Dhl', None)]),
    'btD':    ('M222 319H262',          []),
    'btX':    ('M278 319H296V394H65V385', [(302, 389, 'branch_targ_Xhl', None)]),
}
DOTS = {'wdD': (126, 200), 'alu_br': (522, 168), 'alu_ad': (522, 168)}
ARROWS = {'wb', 'jt', 'btX', 'alu_ad', 'wdX'}

# block name -> drawing function(cls, textcls)
def blocks(active, imm_name):
    def st(name):
        on = name in active
        return ('k' if on else 'kd'), ('' if on else ' mut')
    o = []
    k, t = st('regfile')
    o.append('<rect class="%s" x="24" y="55" width="62" height="85"/>' % k + T(55, 94, 'reg', t.strip(), 'middle') + T(55, 108, 'file', t.strip(), 'middle'))
    k, t = st('op0mux'); o.append(mux(200, 55, 151, k))
    k, t = st('op1mux'); o.append(mux(200, 185, 281, k))
    k, t = st('immgen')
    o.append('<rect class="%s" x="134" y="234" width="54" height="20"/>' % k + T(161, 248, imm_name, ('s' + t), 'middle'))
    k, t = st('pcadd')
    o.append('<rect class="%s" x="140" y="306" width="82" height="26"/>' % k + T(181, 323, 'pc_Dhl + imm', ('s' + t), 'middle'))
    k, t = st('pcmux')
    o.append('<rect class="%s" x="24" y="300" width="82" height="85"/>' % k + T(65, 324, 'PC mux', t.strip(), 'middle') + T(65, 340, '（P 級）', ('zh s' + t), 'middle'))
    k, t = st('alu')
    o.append('<rect class="%s" x="384" y="80" width="56" height="176"/>' % k + T(412, 172, 'ALU', t.strip(), 'middle')
             + T(389, 107, 'in0', 's mut') + T(389, 237, 'in1', 's mut'))
    k, t = st('muldiv')
    o.append('<rect class="%s" x="384" y="272" width="56" height="28"/>' % k + T(412, 290, 'muldiv', ('s' + t), 'middle'))
    k, t = st('brcond')
    o.append('<rect class="%s" x="506" y="56" width="74" height="36"/>' % k + T(543, 78, 'branch cond', ('s' + t), 'middle'))
    k, t = st('exmux'); o.append(mux(532, 150, 218, k))
    k, t = st('dmem')
    o.append('<rect class="%s" x="636" y="322" width="94" height="54"/>' % k + T(683, 345, 'data memory', ('s' + t), 'middle')
             + T(683, 361, 'X 請求 · M 回應', ('zh s' + t), 'middle'))
    k, t = st('respmux')
    o.append('<rect class="%s" x="636" y="242" width="94" height="28"/>' % k + T(683, 260, 'dmemresp mux', ('s' + t), 'middle'))
    k, t = st('wbmux'); o.append(mux(748, 160, 280, k))
    return ''.join(o)


WALK = {
    'addi': dict(nets='rd0 imm op0 op1 alu alu_ex ex wb', blk='regfile op0mux op1mux immgen alu exmux wbmux pcmux',
                 imm='imm_i', op0='am_rdat', op1='bm_imm_i', alu='alu_add', ex='em_alu', mem='nr（不發請求）', dmm='dmm_x',
                 wb='wm_alu', rf='rf_wen=y  waddr=rd', pc='pm_p'),
    'lw':   dict(nets='rd0 imm op0 op1 alu alu_ad resp mresp wb', blk='regfile op0mux op1mux immgen alu dmem respmux wbmux pcmux',
                 imm='imm_i', op0='am_rdat', op1='bm_imm_i', alu='alu_add', ex='em_x', mem='ld · ml_w', dmm='dmm_w',
                 wb='wm_mem', rf='rf_wen=y  waddr=rd', pc='pm_p'),
    'sw':   dict(nets='rd0 rd1 imm op0 op1 alu alu_ad wdD wdX', blk='regfile op0mux op1mux immgen alu dmem pcmux',
                 imm='imm_s', op0='am_rdat', op1='bm_imm_s', alu='alu_add', ex='em_x', mem='st · ml_w', dmm='dmm_w',
                 wb='wm_mem', rf='rf_wen=n', pc='pm_p'),
    'bne':  dict(nets='rd0 rd1 op0 op1 alu alu_br btD btX', blk='regfile op0mux op1mux alu brcond pcadd pcmux',
                 imm='imm_sb', op0='am_rdat', op1='bm_rdat', alu='alu_xor', ex='em_x', mem='nr', dmm='dmm_x',
                 wb='wm_x', rf='rf_wen=n', pc='pm_b（成立時）', brctl=True),
    'jal':  dict(nets='pc4 c0b op0 op1 alu alu_ex ex wb jt', blk='regfile op0mux op1mux alu exmux wbmux pcadd pcmux',
                 imm='imm_uj', op0='am_pc4', op1='bm_0', alu='alu_add', ex='em_alu', mem='nr', dmm='dmm_x',
                 wb='wm_alu', rf='rf_wen=y  waddr=rd', pc='pm_j（D 級就轉向）'),
}


def walk_svg(name, aria):
    w = WALK[name]
    act = set(w['nets'].split())
    o = ['<svg viewBox="0 0 820 416" role="img" aria-label="%s">' % aria]
    # dim nets first so the active ones paint on top
    for pass_on in (False, True):
        for n, (d, labels) in NETS.items():
            on = n in act
            if on != pass_on:
                continue
            extra = ''
            if n in ARROWS:
                extra = ' marker-end="url(#%s)"' % ('aha' if on else 'ahd')
            o.append(P(d, 'a' if on else 'wd', extra))
            for (x, y, s, anc) in labels:
                o.append(T(x, y, s, 's ac' if on else 's mut', anc))
            if n in DOTS and on:
                o.append('<circle class="da" cx="%d" cy="%d" r="3"/>' % DOTS[n])
    o.append(bar(262, 48, 372, 'X←D'))
    o.append(bar(596, 48, 290, 'M←X'))
    o.append(bar(784, 48, 290, 'W←M'))
    o.append(blocks(set(w['blk'].split()), w['imm']))
    # branch condition -> control
    if w.get('brctl'):
        o.append(P('M543 56V42', 'c', ' marker-end="url(#ahc)"'))
        o.append(T(586, 38, 'branch_cond_ne_Xhl → ctrl', 's cb', 'end'))
    # control values (blue): the row of the control table, placed next to what it drives
    o.append(P('M213 146V158', 'c')); o.append(T(176, 170, 'op0: ' + w['op0'], 's cb'))
    o.append(P('M213 276V288', 'c')); o.append(T(176, 299, 'op1: ' + w['op1'], 's cb'))
    o.append(T(412, 72, w['alu'], 's cb', 'middle'))
    o.append(T(526, 142, 'ex: ' + w['ex'], 's cb'))
    o.append(T(636, 236, 'memresp: ' + w['dmm'], 's cb'))
    o.append(T(683, 392, 'mem: ' + w['mem'], 'zh s cb', 'middle'))
    o.append(T(776, 150, 'wb: ' + w['wb'], 's cb', 'end'))
    o.append(T(766, 36, w['rf'], 's cb', 'end'))
    o.append(T(65, 362, 'pc: ' + w['pc'].split('（')[0], 's cb', 'middle'))
    if '（' in w['pc']:
        o.append(T(65, 377, '（' + w['pc'].split('（')[1], 'zh s cb', 'middle'))
    o.append(T(181, 410, 'D', 'hd', 'middle')); o.append(T(412, 410, 'X', 'hd', 'middle')); o.append(T(683, 410, 'M', 'hd', 'middle'))
    o.append('</svg>')
    return '\n'.join(o)


# ---------------------------------------------------------------------------
# ch4 overview
# ---------------------------------------------------------------------------
def overview_svg(aria):
    o = ['<svg viewBox="0 0 800 336" role="img" aria-label="%s">' % aria]
    A = ' marker-end="url(#ah)"'
    # P: pc mux + early imem request
    o.append(mux(60, 90, 190))
    for y, s in ((105, '0'), (128, '1'), (151, '2'), (174, '3')):
        o.append(T(64, y + 4, s, 's mut'))
    o.append(P('M86 140H130', 'w')); o.append('<circle class="d" cx="104" cy="140" r="3"/>')
    o.append(P('M104 140V56H207V84', 'w', A)); o.append(T(110, 50, 'imemreq_msg_addr（P 級就先送出）', 'zh s'))
    o.append(P('M73 95V76', 'c')); o.append(T(98, 70, 'pc_mux_sel_Phl', 's cb', 'end'))
    # F
    o.append('<rect class="k" x="165" y="84" width="85" height="36"/>' + T(207, 106, 'imem', '', 'middle'))
    o.append(P('M144 140H270', 'w')); o.append(T(150, 134, 'pc_Fhl', 's'))
    o.append('<circle class="d" cx="158" cy="140" r="3"/>')
    o.append(P('M158 140V175H175', 'w'))
    o.append('<rect class="k" x="175" y="160" width="40" height="30"/>' + T(195, 179, '+4', '', 'middle'))
    o.append(P('M215 175H270', 'w')); o.append('<circle class="d" cx="240" cy="175" r="3"/>')
    o.append(P('M250 102H270', 'w'))
    # D block
    o.append(P('M284 102H300M284 140H300M284 175H300', 'w'))
    o.append('<rect class="k" x="300" y="84" width="110" height="112"/>')
    for i, s in enumerate(('regfile', 'imm gen', 'op0 / op1 mux', '位址加法器')):
        o.append(T(355, 108 + i * 22, s, 'zh s' if i == 3 else 's', 'middle'))
    o.append(P('M410 102H430M410 130H430M410 158H430M410 186H430', 'w'))
    # X block
    o.append(P('M444 102H464M444 130H464M444 158H464', 'w'))
    o.append('<rect class="k" x="464" y="84" width="86" height="112"/>')
    for i, s in enumerate(('ALU', 'muldiv', 'branch cond', 'execute mux')):
        o.append(T(507, 108 + i * 22, s, 's', 'middle'))
    o.append(P('M550 130H570', 'w'))
    o.append(P('M507 84V64', 'c', ' marker-end="url(#ahc)"')); o.append(T(450, 58, 'branch_cond_*_Xhl → ctrl', 's cb'))
    # M block
    o.append(P('M584 130H600', 'w'))
    o.append('<rect class="k" x="600" y="84" width="90" height="112"/>')
    for i, s in enumerate(('data memory', 'dmemresp mux', 'wb mux')):
        o.append(T(645, 116 + i * 24, s, 's', 'middle'))
    o.append(P('M520 196V230H640V196', 'w', A)); o.append(T(528, 243, 'dmemreq：X 級送出位址與資料', 'zh s'))
    o.append(P('M690 140H710', 'w'))
    # W: back to the regfile
    o.append(P('M724 140H760V30H355V84', 'w', A))
    o.append(T(365, 24, 'wb_mux_out_Whl · rf_wen_out_Whl · rf_waddr_Whl → regfile', 's'))
    # feedback to the pc mux
    o.append(P('M320 196V246H52V174H60', 'w', A)); o.append(T(252, 242, 'jumpreg_targ_Dhl', 's'))
    o.append(P('M340 196V260H42V151H60', 'w', A)); o.append(T(252, 256, 'jump_targ_Dhl', 's'))
    o.append(P('M444 186H456V274H30V128H60', 'w', A)); o.append(T(346, 270, 'branch_targ_Xhl', 's'))
    o.append(P('M240 175V288H18V105H60', 'w', A)); o.append(T(62, 284, 'pc_plus4_Fhl', 's'))
    # pipeline registers on top of the wires
    for x, s in ((130, 'F←P'), (270, 'D←F'), (430, 'X←D'), (570, 'M←X'), (710, 'W←M')):
        o.append('<rect class="r" x="%d" y="70" width="14" height="140"/>' % x + P('M%d 190l7 5l-7 5' % x, 'rl')
                 + T(x + 7, 224, s, 's sq', 'middle'))
    for x, a, b in ((70, 'P', '選下一個 PC'), (207, 'F', '取指令'), (355, 'D', '解碼、讀暫存器'), (507, 'X', '執行'), (645, 'M', '記憶體'), (750, 'W', '寫回')):
        o.append(T(x, 312, a, 'hd', 'middle')); o.append(T(x, 328, b, 'zh s mut', 'middle'))
    o.append('</svg>')
    return '\n'.join(o)


def main():
    s = open(SRC, encoding='utf-8').read()
    figs = list(re.finditer(r'<figure>.*?</figure>', s, re.S))
    targets = {0: None, 4: 'addi', 5: 'lw', 6: 'sw', 7: 'bne', 8: 'jal'}
    out, last = [], 0
    for i, m in enumerate(figs):
        if i not in targets:
            continue
        f = m.group(0)
        sm = re.search(r'<svg\b.*?</svg>', f, re.S)
        aria = re.search(r'aria-label="([^"]*)"', sm.group(0)).group(1)
        new = overview_svg(aria) if targets[i] is None else walk_svg(targets[i], aria)
        out.append(s[last:m.start() + sm.start()]); out.append(new); last = m.start() + sm.end()
    out.append(s[last:])
    open(SRC, 'w', encoding='utf-8').write(''.join(out))
    print('regenerated %d figures' % len(targets))


if __name__ == '__main__':
    main()
