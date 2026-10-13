#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diff_label.py — so câu nhãn với vùng input gần nhất để sửa tay nhanh.
Usage: venv/bin/python fine-tune/diff_label.py <file.txt> [N]
In ra từng issue kèm vùng input giống nhất (difflib).
"""
from __future__ import annotations

import difflib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def windows(txt: str, nwords: int = 40):
    w = txt.split()
    for i in range(0, max(1, len(w)), 10):
        yield " ".join(w[i:i + nwords])


def main() -> int:
    fname = sys.argv[1]
    recs = [json.loads(l) for l in open(
        ROOT / "cv-analysis-service/finetune_output/silver_dataset.jsonl", encoding="utf-8")]
    r = next(x for x in recs if x["file"] == fname)
    audit = json.load(open(ROOT / "fine-tune/_stage/full_audit.json"))
    rec = next(x for x in audit["records"] if x["file"] == fname)
    txt = r["input"]
    print(f"===== {fname} ({len(rec['issues'])} issues) =====")
    for it in rec["issues"]:
        print(f"\n[{it['type']}] {it['path']}\n  LABEL: {it['detail'][:220]}")
        if it["type"] in ("ungrounded", "ungrounded_sentence", "ungrounded_bullet",
                          "overused_description"):
            probe = it["detail"].split("không có căn cứ")[0].strip(" '") if "không có căn cứ" in it["detail"] else it["detail"]
            probe = probe.split(": ", 1)[-1] if ": " in probe[:60] else probe
            best = max(((difflib.SequenceMatcher(None, probe, w).ratio(), w)
                        for w in windows(txt)), default=(0, ""))
            print(f"  INPUT GẦN NHẤT ({best[0]:.2f}): ...{best[1][:260]}...")


if __name__ == "__main__":
    main()
