#!/usr/bin/env python3
"""Sanity-check explanations/*.json: schema, naming fragments, `symbol` references."""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "data.js").read_text(encoding="utf-8")[len("window.SYMDATA = "):-2])
names = {e["name"] for e in data["entities"]}
bad = 0
refs_missing = {}
for p in sorted((HERE / "explanations").glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    for k, v in d["entities"].items():
        errs = []
        for fld in ("sum", "naming", "desc"):
            if not v.get(fld):
                errs.append(f"missing {fld}")
        nm = v.get("naming") or []
        if any(not isinstance(x, list) or len(x) != 3 for x in nm):
            errs.append("naming entries must be [frag, en, zh]")
        else:
            name = re.split(r"[|`]", k)[-1]
            joined = re.sub(r"[_\W]", "", "".join(x[0] for x in nm)).lower()
            if joined != re.sub(r"[_\W]", "", name).lower():
                errs.append(f"naming fragments {[x[0] for x in nm]} != name")
        if len(v.get("desc", "")) < 25:
            errs.append("desc too short")
        for r in re.findall(r"`([^`\n]+)`", v.get("desc", "")):
            if re.fullmatch(r"[A-Za-z_]\w*", r) and r not in names:
                refs_missing.setdefault(r, []).append(k)
        if errs:
            bad += 1
            print(f"{p.name}: {k}: {'; '.join(errs)}")
print(f"\n{bad} entries with problems")
if "-r" in sys.argv:
    print("backticked identifiers that are not symbols (not clickable):")
    for r, ks in sorted(refs_missing.items(), key=lambda x: -len(x[1]))[:80]:
        print(f"  {r}  x{len(ks)}")
