#!/usr/bin/env python3
"""Build the symbol index for the lab1 symbol lookup page.

Scans every .v file under <repo>/lab1/lab1 (skipping generated build dirs), finds every
identifier / macro occurrence, works out which module it belongs to and how it
is used there (declared, driven, read, connected to an instance port, ...),
merges in the hand-written explanations from explanations/*.json, and writes
data.js which index.html loads.

    python3 build.py              # writes data.js
    python3 build.py --worklist   # also writes worklist/<file>.json (the
                                  # entities each explanation file must cover)
    python3 build.py --check      # report entities that lack an explanation

Re-run after editing the .v files: line numbers and usages are regenerated,
explanations are keyed by module + name so they survive edits.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2] / "lab1" / "lab1"   # computer-architecture/lab1/lab1
EXPL_DIR = HERE / "explanations"
SKIP_DIRS = {"build", "tests", "ubmark", ".git"}

KEYWORDS = set("""
always and assign automatic begin buf bufif0 bufif1 case casex casez cell cmos
config deassign default defparam design disable edge else end endcase endconfig
endfunction endgenerate endmodule endprimitive endspecify endtable endtask event
for force forever fork function generate genvar highz0 highz1 if ifnone incdir
include initial inout input instance integer join large liblist library
localparam macromodule medium module nand negedge nmos nor noshowcancelled not
notif0 notif1 or output parameter pmos posedge primitive pull0 pull1 pulldown
pullup pulsestyle_onevent pulsestyle_ondetect rcmos real realtime reg release
repeat rnmos rpmos rtran rtranif0 rtranif1 scalared showcancelled signed small
specify specparam strong0 strong1 supply0 supply1 table task time tran tranif0
tranif1 tri tri0 tri1 triand trior trireg unsigned use vectored wait wand weak0
weak1 while wire wor xnor xor
""".split())
KEYWORDS.discard("type")  # used as a port name in vc-MemReqMsg.v

DECL_KW = {"input", "output", "inout", "wire", "reg", "integer", "genvar",
           "parameter", "localparam", "real", "time", "event"}
DECL_MOD = {"wire", "reg", "signed", "unsigned", "integer"}
DIRECTIVES = {"define", "ifdef", "ifndef", "elsif", "else", "endif", "include",
              "timescale", "undef", "default_nettype", "resetall", "line"}

TOKEN_RE = re.compile(r"""
    (?P<lc>//[^\n]*)
  | (?P<bc>/\*.*?\*/)
  | (?P<str>"(?:\\.|[^"\\\n])*")
  | (?P<num>(?:\d[\d_]*)?\s*'[sS]?[bBoOdDhH]\s*[0-9a-fA-FxXzZ_?]+|\d[\d_]*(?:\.\d+)?)
  | (?P<mac>`[A-Za-z_]\w*)
  | (?P<sys>\$\w+)
  | (?P<id>[A-Za-z_][\w$]*)
  | (?P<cont>\\\n)
  | (?P<nl>\n)
  | (?P<op><=|===|!==|==|!=|&&|\|\||<<<|>>>|<<|>>|>=|[-+*/%&|^~!<>=?:;,.()\[\]{}#@])
  | (?P<ws>[ \t\r]+)
  | (?P<other>.)
""", re.X | re.S)


class Tok:
    __slots__ = ("t", "s", "line", "col")

    def __init__(self, t, s, line, col):
        self.t, self.s, self.line, self.col = t, s, line, col

    def __repr__(self):
        return f"{self.t}:{self.s}@{self.line}"


def tokenize(text):
    toks = []
    line, line_start = 1, 0
    for m in TOKEN_RE.finditer(text):
        kind = m.lastgroup
        s = m.group()
        if kind in ("id", "mac", "op", "num", "sys", "nl", "cont", "str"):
            if kind == "num":
                lead = len(s) - len(s.lstrip())
                toks.append(Tok(kind, s.strip(), line, m.start() + lead - line_start))
            else:
                toks.append(Tok(kind, s, line, m.start() - line_start))
        nls = s.count("\n")
        if nls:
            line += nls
            line_start = m.start() + s.rfind("\n") + 1
    return toks


# ---------------------------------------------------------------------------
# Per-file scan
# ---------------------------------------------------------------------------
# Occurrence kinds:
#   def      macro `define / module header
#   decl     declaration inside a module
#   write    driven here (assign / always LHS / decl with initialiser)
#   read     plain use
#   conn     used inside an instance port/param connection  (.p(<here>))
#   port     the ".p" name in an instance connection (belongs to child module)
#   inst     module name used to instantiate
#   guard    macro tested by `ifdef/`ifndef/`elsif
#   hier     reached via hierarchical path (a.b.<here>)


class FileScan:
    def __init__(self, rel, text):
        self.rel = rel
        self.text = text
        self.lines = text.split("\n")
        self.modules = []   # {name, start, end}
        self.occs = []      # dicts
        self.includes = []
        self.scan(tokenize(text))

    def add(self, tok, name, kind, scope, **extra):
        o = {"name": name, "kind": kind, "scope": scope, "line": tok.line,
             "col": tok.col, "len": len(tok.s)}
        o.update(extra)
        self.occs.append(o)
        return o

    def scan(self, all_toks):
        # ---- pass A: directives (line oriented), produce the code token list
        toks = []
        i, n = 0, len(all_toks)
        while i < n:
            t = all_toks[i]
            if t.t == "mac" and t.s[1:] in DIRECTIVES:
                d = t.s[1:]
                if d == "define":
                    i = self.scan_define(all_toks, i)
                    continue
                if d in ("ifdef", "ifndef", "elsif", "undef"):
                    j = i + 1
                    if j < n and all_toks[j].t == "id":
                        self.add(all_toks[j], all_toks[j].s, "guard", None,
                                 macro=True, directive=d)
                        i = j + 1
                        continue
                if d == "include":
                    j = i + 1
                    if j < n and all_toks[j].t == "str":
                        self.includes.append(all_toks[j].s.strip('"'))
                    i = j + 1
                    continue
                if d == "timescale":
                    while i < n and all_toks[i].t != "nl":
                        i += 1
                    continue
                i += 1
                continue
            if t.t not in ("nl", "cont"):
                toks.append(t)
            i += 1
        self.scan_code(toks)

    def scan_define(self, all_toks, i):
        n = len(all_toks)
        name_tok = all_toks[i + 1]
        name = name_tok.s
        self.add(name_tok, name, "def", None, macro=True)
        j = i + 2
        formals = set()
        # function-like macro: '(' immediately after the name
        if (j < n and all_toks[j].s == "(" and all_toks[j].line == name_tok.line
                and all_toks[j].col == name_tok.col + len(name)):
            j += 1
            while j < n and all_toks[j].s != ")":
                if all_toks[j].t == "id":
                    formals.add(all_toks[j].s)
                j += 1
            j += 1
        while j < n and all_toks[j].t != "nl":
            t = all_toks[j]
            if t.t == "mac" and t.s[1:] not in DIRECTIVES:
                self.add(t, t.s[1:], "read", None, macro=True, inmacro=name)
            j += 1
        return j

    def scan_code(self, toks):
        n = len(toks)
        i = 0
        module = None
        depth = 0
        decl = None            # {kind, depth, state}  state: 'name' | 'expr'
        conn_stack = []        # [{depth, inst, module, port, isparam}]
        inst_ctx = None        # {module, inst, depth, phase}
        prev_sig = None        # previous significant token string
        skip_idx = -1          # task/function name already recorded

        def scope():
            return module["name"] if module else None

        while i < n:
            t = toks[i]
            s = t.s
            nxt = toks[i + 1] if i + 1 < n else None

            if t.t == "mac":
                extra = {}
                if conn_stack:
                    extra["conn"] = dict(conn_stack[-1]["info"])
                self.add(t, s[1:], "read", scope(), macro=True, **extra)
                prev_sig = s
                i += 1
                continue

            if t.t == "op":
                if s in "([{":
                    depth += 1
                elif s in ")]}":
                    depth -= 1
                    if conn_stack and depth < conn_stack[-1]["depth"]:
                        conn_stack.pop()
                    if decl and depth < decl["depth"]:
                        decl = None
                    if inst_ctx and depth < inst_ctx["depth"]:
                        pass
                elif s == ";":
                    decl = None
                    if depth == 0:
                        inst_ctx = None
                elif s == "," and decl and depth == decl["depth"]:
                    decl["state"] = "name"
                elif s == "=" and decl and depth == decl["depth"] and decl["state"] == "after":
                    decl["state"] = "expr"
                    if decl.get("last"):
                        decl["last"]["init"] = True
                prev_sig = s
                i += 1
                continue

            if t.t != "id":
                prev_sig = s
                i += 1
                continue

            # ---- identifiers / keywords
            if s in KEYWORDS:
                if s in ("module", "macromodule") and nxt and nxt.t == "id":
                    module = {"name": nxt.s, "start": t.line, "end": t.line}
                    self.modules.append(module)
                    self.add(nxt, nxt.s, "def", None, ismodule=True)
                    depth = 0
                    i += 2
                    prev_sig = nxt.s
                    continue
                if s == "endmodule":
                    if module:
                        module["end"] = t.line
                    module = None
                    decl = None
                    depth = 0
                elif s in ("task", "function"):
                    k = i + 1
                    while k < n and (toks[k].t != "id" or toks[k].s in KEYWORDS):
                        if toks[k].s == ";":
                            break
                        k += 1
                    if k < n and toks[k].t == "id":
                        self.add(toks[k], toks[k].s, "decl", scope(), dkind=s, stmt=s)
                        skip_idx = k
                elif s in DECL_KW:
                    if decl and depth == decl["depth"] and s in DECL_MOD:
                        # "output reg x" / "input wire x": keep port kind
                        if decl["kind"] in ("input", "output", "inout"):
                            decl["sub"] = s
                        else:
                            decl["kind"] = s
                    else:
                        decl = {"kind": s, "depth": depth, "state": "name", "start": i}
                elif s in ("signed", "unsigned"):
                    pass
                prev_sig = s
                i += 1
                continue

            if i == skip_idx:
                prev_sig = s
                i += 1
                continue

            # hierarchical tail:  a.b.c  (prev is '.', and not a port connection)
            if prev_sig == "." and i >= 2 and toks[i - 2].t == "id" and toks[i - 2].s not in KEYWORDS:
                # collect the path back to the head
                path = []
                k = i - 2
                while k >= 0 and toks[k].t == "id":
                    path.insert(0, toks[k].s)
                    if k >= 2 and toks[k - 1].s == "." and toks[k - 2].t == "id":
                        k -= 2
                    elif k >= 4 and toks[k - 1].s == "." and toks[k - 2].s == "]":
                        break
                    else:
                        break
                self.add(t, s, "hier", scope(), path=path)
                prev_sig = s
                i += 1
                continue

            # named block:  begin : label
            if prev_sig == ":" and i >= 2 and toks[i - 2].s in ("begin", "fork"):
                self.add(t, s, "decl", scope(), dkind="block", stmt="begin : " + s)
                prev_sig = s
                i += 1
                continue

            # port / parameter connection name:  .name (
            if prev_sig == "." and nxt and nxt.s == "(" and inst_ctx:
                isparam = inst_ctx["phase"] == "params"
                info = {"inst": inst_ctx["inst"], "module": inst_ctx["module"],
                        "port": s, "isparam": isparam}
                self.add(t, s, "port", scope(), target=inst_ctx["module"],
                         inst=inst_ctx["inst"], isparam=isparam)
                conn_stack.append({"depth": depth + 1, "info": info})
                prev_sig = s
                i += 1
                continue

            # declaration name
            if decl and depth == decl["depth"] and decl["state"] == "name":
                kind = decl["kind"]
                o = self.add(t, s, "decl", scope(), dkind=kind, sub=decl.get("sub"),
                             stmt=self.decl_text(toks, decl["start"], i))
                decl["state"] = "after"
                decl["last"] = o
                prev_sig = s
                i += 1
                continue

            # instantiation:  ModName [#(...)] inst_name (
            if module and not decl and not conn_stack and depth == 0 and nxt is not None:
                is_inst = False
                if nxt.s == "#":
                    is_inst = True
                elif nxt.t == "id" and nxt.s not in KEYWORDS and i + 2 < n and toks[i + 2].s == "(":
                    is_inst = True
                if is_inst:
                    # find the instance name
                    k = i + 1
                    if toks[k].s == "#":
                        k += 1
                        if k < n and toks[k].s == "(":
                            d = 0
                            while k < n:
                                if toks[k].s == "(":
                                    d += 1
                                elif toks[k].s == ")":
                                    d -= 1
                                    if d == 0:
                                        break
                                k += 1
                            k += 1
                    inst_name = toks[k].s if k < n and toks[k].t == "id" else "?"
                    self.add(t, s, "inst", scope(), inst=inst_name, ismodule=True)
                    inst_ctx = {"module": s, "inst": inst_name, "depth": 0,
                                "phase": "params" if nxt.s == "#" else "ports",
                                "name_idx": k}
                    prev_sig = s
                    i += 1
                    continue

            if inst_ctx and depth == 0 and i == inst_ctx.get("name_idx"):
                self.add(t, s, "decl", scope(), dkind="instance", of=inst_ctx["module"],
                         stmt=f"{inst_ctx['module']} {s} ( ... );")
                inst_ctx["phase"] = "ports"
                prev_sig = s
                i += 1
                continue

            # plain use: read or write?
            kind = "read"
            k = i + 1
            while k < n and toks[k].s == "[":
                d = 0
                while k < n:
                    if toks[k].s == "[":
                        d += 1
                    elif toks[k].s == "]":
                        d -= 1
                        if d == 0:
                            break
                    k += 1
                k += 1
            if k < n and toks[k].s in ("=", "<=") and not conn_stack:
                if prev_sig in (";", "begin", "end", "else", ")", "assign", ":", None) or \
                        (toks[k].s == "=" and prev_sig in ("(", ",") and self.in_for(toks, i)):
                    if not (toks[k].s == "<=" and prev_sig in ("(",)):
                        kind = "write"
            extra = {}
            if conn_stack:
                extra["conn"] = dict(conn_stack[-1]["info"])
                kind = "conn"
            if decl and decl["state"] == "expr" and decl.get("last"):
                extra["indecl"] = decl["last"]["name"]
            self.add(t, s, kind, scope(), **extra)
            prev_sig = s
            i += 1

    @staticmethod
    def in_for(toks, i):
        k = i - 1
        while k >= 0 and toks[k].s not in (";", "begin", "end"):
            if toks[k].s == "for":
                return True
            k -= 1
        return k >= 0 and toks[k].s == ";" and any(
            toks[j].s == "for" for j in range(max(0, k - 12), k))

    @staticmethod
    def decl_text(toks, start, i):
        """'input [31:0]' style summary of the declaration head."""
        parts = []
        k = start
        depth = 0
        while k < i:
            s = toks[k].s
            if s == ",":
                if depth == 0:
                    # keep only the head (kind + range) for later names in a list
                    head = []
                    d = 0
                    for p in toks[start:k]:
                        if p.t == "id" and p.s not in KEYWORDS and d == 0:
                            break
                        if p.s == "[":
                            d += 1
                        if p.s == "]":
                            d -= 1
                        head.append(p.s)
                    return FileScan.join(head)
            if s in "([{":
                depth += 1
            elif s in ")]}":
                depth -= 1
            parts.append(s)
            k += 1
        return FileScan.join(parts)

    @staticmethod
    def join(parts):
        out = ""
        for p in parts:
            if out and (out[-1].isalnum() or out[-1] in "_]") and (p[0].isalnum() or p[0] in "_[`"):
                out += " "
            out += p
        return out


# ---------------------------------------------------------------------------
# Linking
# ---------------------------------------------------------------------------

def main():
    files = []
    for p in sorted(LAB.rglob("*.v")):
        rel = p.relative_to(LAB).as_posix()
        if rel.split("/")[0] in SKIP_DIRS:
            continue
        text = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        files.append(FileScan(rel, text.rstrip("\n")))

    by_base = {Path(f.rel).name: f for f in files}

    # include closure per file (what is visible from this file)
    def closure(f, seen=None):
        seen = seen if seen is not None else []
        for inc in f.includes:
            g = by_base.get(inc)
            if g and g.rel not in seen:
                seen.append(g.rel)
                closure(g, seen)
        return seen

    # module name -> [(file, module)]
    mod_defs = defaultdict(list)
    for f in files:
        for m in f.modules:
            mod_defs[m["name"]].append(f.rel)

    def resolve_module(name, from_file):
        cands = mod_defs.get(name)
        if not cands:
            return None
        if len(cands) == 1:
            return cands[0]
        if from_file in cands:
            return from_file
        vis = closure(by_base[Path(from_file).name])
        for c in vis:
            if c in cands:
                return c
        return cands[0]

    entities = {}

    def ent(key, **init):
        e = entities.get(key)
        if e is None:
            e = {"key": key, "occ": [], **init}
            entities[key] = e
        return e

    fidx = {f.rel: i for i, f in enumerate(files)}

    # --- first: declarations, to know what exists in each (file, module)
    declared = defaultdict(dict)   # (file, module) -> name -> entity
    instances = defaultdict(dict)  # (file, module) -> inst name -> (module name)
    for f in files:
        for o in f.occs:
            if o["kind"] == "decl" and o["scope"]:
                key = f"{f.rel}|{o['scope']}|{o['name']}"
                e = ent(key, name=o["name"], file=f.rel, module=o["scope"], cat="signal",
                        dkind=o["dkind"], decls=[])
                # port declared as "output x; reg x;" -> keep the port kind first
                if o["dkind"] in ("input", "output", "inout") and e["dkind"] not in ("input", "output", "inout"):
                    e["dkind"] = o["dkind"]
                if o["dkind"] == "reg" and e["dkind"] in ("input", "output", "inout"):
                    e["sub"] = "reg"
                if o.get("sub"):
                    e["sub"] = o["sub"]
                if o["dkind"] == "instance":
                    e["of"] = o["of"]
                    e["ofFile"] = resolve_module(o["of"], f.rel)
                    instances[(f.rel, o["scope"])][o["name"]] = o["of"]
                e["decls"].append(o["stmt"])
                declared[(f.rel, o["scope"])][o["name"]] = e

    def occ_row(f, o, kind=None, **extra):
        r = {"f": fidx[f.rel], "l": o["line"], "c": o["col"], "n": o["len"],
             "k": kind or o["kind"]}
        if o["scope"]:
            r["m"] = o["scope"]
        r.update(extra)
        return r

    def conn_extra(f, o):
        c = o.get("conn")
        if not c:
            return {}
        tfile = resolve_module(c["module"], f.rel)
        x = {"inst": c["inst"], "tm": c["module"], "tp": c["port"]}
        if tfile:
            x["tf"] = tfile
            te = declared.get((tfile, c["module"]), {}).get(c["port"])
            if te:
                x["dir"] = te["dkind"]
        return x

    for f in files:
        for o in f.occs:
            name = o["name"]
            if o.get("macro"):
                e = ent("`" + name, name=name, cat="macro", defs=[])
                if o["kind"] == "def":
                    e["defs"].append(f.rel)
                    e.setdefault("file", f.rel)
                extra = conn_extra(f, o)
                if o.get("inmacro"):
                    extra["inmacro"] = o["inmacro"]
                if o.get("directive"):
                    extra["dv"] = o["directive"]
                e["occ"].append(occ_row(f, o, **extra))
                continue
            if o.get("ismodule"):
                tfile = f.rel if o["kind"] == "def" else resolve_module(name, f.rel)
                key = f"{tfile or '?'}||{name}"
                e = ent(key, name=name, cat="module", file=tfile)
                extra = {"inst": o["inst"]} if o.get("inst") else {}
                e["occ"].append(occ_row(f, o, **extra))
                continue
            if o["kind"] == "port":
                tfile = resolve_module(o["target"], f.rel)
                te = declared.get((tfile, o["target"]), {}).get(name) if tfile else None
                if te is None:
                    key = f"{tfile or '?'}|{o['target']}|{name}"
                    te = ent(key, name=name, file=tfile, module=o["target"], cat="signal",
                             dkind="unknown", decls=[])
                te["occ"].append(occ_row(f, o, inst=o["inst"]))
                continue
            if o["kind"] == "hier":
                # walk the instance path
                cur = (f.rel, o["scope"])
                ok = True
                for comp in o["path"]:
                    mname = instances.get(cur, {}).get(comp)
                    if not mname:
                        ok = False
                        break
                    mfile = resolve_module(mname, cur[0])
                    if not mfile:
                        ok = False
                        break
                    cur = (mfile, mname)
                path = ".".join(o["path"])
                if ok:
                    te = declared.get(cur, {}).get(name)
                    if te is None:
                        te = ent(f"{cur[0]}|{cur[1]}|{name}", name=name, file=cur[0],
                                 module=cur[1], cat="signal", dkind="implicit", decls=[])
                        declared[cur][name] = te
                    te["occ"].append(occ_row(f, o, path=path))
                else:
                    e = ent(f"{f.rel}|{o['scope']}|{path}.{name}", name=name, file=f.rel,
                            module=o["scope"], cat="signal", dkind="hier-unresolved", decls=[])
                    e["occ"].append(occ_row(f, o, path=path))
                continue
            # decl / read / write / conn inside a module (or file scope)
            sc = o["scope"]
            if sc is None:
                continue  # stray identifier outside any module (macro bodies etc.)
            e = declared.get((f.rel, sc), {}).get(name)
            if e is None and name in mod_defs:
                tfile = resolve_module(name, f.rel)
                e = ent(f"{tfile}||{name}", name=name, cat="module", file=tfile)
                e["occ"].append(occ_row(f, o))
                continue
            if e is None:
                e = ent(f"{f.rel}|{sc}|{name}", name=name, file=f.rel, module=sc,
                        cat="signal", dkind="implicit", decls=[])
                declared[(f.rel, sc)][name] = e
            extra = conn_extra(f, o)
            if o.get("init"):
                extra["init"] = 1
            if o.get("indecl"):
                extra["for"] = o["indecl"]
            e["occ"].append(occ_row(f, o, **extra))

    # --- explanations
    expl = {}
    if EXPL_DIR.exists():
        for p in sorted(EXPL_DIR.glob("*.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception as ex:  # noqa
                print(f"!! {p.name}: invalid JSON: {ex}")
                continue
            for k, v in d.get("entities", {}).items():
                expl[k] = v
    glossary = {}
    gp = HERE / "glossary.json"
    if gp.exists():
        glossary = json.loads(gp.read_text(encoding="utf-8"))

    def expl_key(e):
        if e["cat"] == "macro":
            return "`" + e["name"]
        if e["cat"] == "module":
            return f"{e.get('file')}||{e['name']}"
        return e["key"]

    missing = defaultdict(list)
    for e in entities.values():
        x = expl.get(expl_key(e))
        if x:
            e["x"] = x
        else:
            home = e.get("file") or "(undefined)"
            missing[home].append(expl_key(e))

    if "--worklist" in sys.argv:
        wl = HERE / "worklist"
        wl.mkdir(exist_ok=True)
        for old in wl.glob("*.json"):
            old.unlink()
        per = defaultdict(list)
        for e in entities.values():
            home = e.get("file") or "_undefined"
            item = {"key": expl_key(e), "name": e["name"], "cat": e["cat"]}
            if e["cat"] == "signal":
                item["module"] = e["module"]
                item["kind"] = e["dkind"]
                if e.get("decls"):
                    item["decl"] = e["decls"][0]
                if e.get("of"):
                    item["instance_of"] = e["of"]
            item["lines"] = sorted({f"{files[o['f']].rel}:{o['l']}" for o in e["occ"]})[:12]
            item["n_occ"] = len(e["occ"])
            per[home].append(item)
        for home, items in per.items():
            out = wl / (home.replace("/", "__") + ".json")
            out.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
        print("worklist:", {k: len(v) for k, v in per.items()})

    if "--check" in sys.argv:
        tot = sum(len(v) for v in missing.values())
        print(f"missing explanations: {tot} / {len(entities)}")
        for home, keys in sorted(missing.items()):
            print(f"  {home}: {len(keys)}")
            if "-v" in sys.argv:
                for k in keys:
                    print("     ", k)
        stale = set(expl) - {expl_key(e) for e in entities.values()}
        if stale:
            print(f"stale explanation keys (no such symbol any more): {len(stale)}")
            for k in sorted(stale):
                print("     ", k)

    if "--check" in sys.argv:
        return

    data = {
        "files": [{"path": f.rel, "lines": f.lines,
                   "modules": f.modules, "includes": f.includes} for f in files],
        "entities": [
            {k: v for k, v in e.items() if k != "key"} | {"id": e["key"]}
            for e in entities.values()
        ],
        "glossary": glossary,
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (HERE / "data.js").write_text("window.SYMDATA = " + blob + ";\n", encoding="utf-8")
    print(f"files={len(files)} entities={len(entities)} "
          f"occurrences={sum(len(e['occ']) for e in entities.values())} "
          f"explained={len(entities) - sum(len(v) for v in missing.values())} "
          f"data.js={len(blob) // 1024}KB")


if __name__ == "__main__":
    main()
