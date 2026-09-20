#!/usr/bin/env python3
"""Regenerate riscvstall-datapath.html from its template.

The page embeds the actual Verilog sources so that clicking a block or wire
shows the code describing it. Re-run this after editing the .v files:

    python3 gen-riscvstall-datapath.py            # writes riscvstall-datapath.html
    python3 gen-riscvstall-datapath.py --fragment out.html   # body-only variant
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]  # helper-web/lab1/<this folder> -> repo root
LAB = ROOT / "lab1" / "lab1"

# key -> path relative to lab1/lab1 (keys are referenced by REFS in the template)
SOURCES = {
    "D": "riscvstall/riscvstall-CoreDpath.v",
    "C": "riscvstall/riscvstall-CoreCtrl.v",
    "K": "riscvstall/riscvstall-Core.v",
    "R": "riscvstall/riscvstall-CoreDpathRegfile.v",
    "A": "riscvstall/riscvstall-CoreDpathAlu.v",
    "M": "imuldiv/imuldiv-IntMulDivIterative.v",
    "I": "riscvstall/riscvstall-InstMsg.v",
    "S": "riscvstall/riscvstall-randdelay-sim.v",
}

WRAP_HEAD = (
    '<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    '</head>\n<body style="margin:0">\n'
)
WRAP_TAIL = "\n</body>\n</html>\n"


def main():
    src = {}
    for key, rel in SOURCES.items():
        p = LAB / rel
        text = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        src[key] = {"name": p.name, "path": "lab1/" + rel, "text": text.rstrip("\n")}
    blob = json.dumps(src, ensure_ascii=False).replace("<", "\\u003c")

    template = (HERE / "riscvstall-datapath.template.html").read_text(encoding="utf-8")
    assert template.count("__SRC_JSON__") == 1
    page = template.replace("__SRC_JSON__", blob)

    if len(sys.argv) == 3 and sys.argv[1] == "--fragment":
        Path(sys.argv[2]).write_text(page, encoding="utf-8")
        print("wrote", sys.argv[2])
    else:
        out = HERE / "riscvstall-datapath.html"
        out.write_text(WRAP_HEAD + page + WRAP_TAIL, encoding="utf-8")
        print("wrote", out)


if __name__ == "__main__":
    main()
