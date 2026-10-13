#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_label_casing.py
===================
Tự sửa các nhãn batch_*.py bị lệch hoa/thường so với văn bản CV
(ví dụ nhãn 'ASP.NET Core MVC' nhưng CV ghi 'ASP.NET CORE MVC').

Nguyên tắc: tìm trong văn bản chuỗi khớp không phân biệt hoa/thường,
thay nhãn bằng đúng hình thức trong văn bản. Không bịa thêm gì.
Chỉ chạm vào các batch thủ công (batch_0*.py, batch_1*.py), không chạm
batch_90_synthetic.py (đã đúng vì sinh từ cùng một profile).

Cách chạy:
    venv/bin/python fix_label_casing.py            # xem trước
    venv/bin/python fix_label_casing.py --apply    # ghi file
"""
from __future__ import annotations

import argparse
import importlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
TXT_DIR = ROOT / "cv-analysis-service" / "cv_texts"
PARTS_DIR = HERE / "silver_parts"


def find_exact(txt: str, want: str) -> str | None:
    """Tìm trong txt chuỗi khớp want (không phân biệt hoa/thường),
    trả về đúng hình thức trong văn bản. Ưu tiên khớp dài nhất."""
    if want in txt:
        return want
    pat = re.compile(re.escape(want), re.IGNORECASE)
    cands = sorted(set(pat.findall(txt)), key=len, reverse=True)
    return cands[0] if cands else None


def walk_batches():
    sys.path.insert(0, str(PARTS_DIR))
    for p in sorted(PARTS_DIR.glob("batch_*.py")):
        if p.name == "batch_90_synthetic.py":
            continue
        mod = importlib.import_module(p.stem)
        importlib.reload(mod)
        yield p, getattr(mod, "BATCH", [])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    total_fix = 0
    leftovers: list[str] = []

    for path, rows in walk_batches():
        src = path.read_text(encoding="utf-8")
        n_fix = 0
        for rec in rows:
            fpath = TXT_DIR / rec["file"]
            if not fpath.exists():
                continue
            txt = fpath.read_text(encoding="utf-8")
            o = rec["profile"]

            targets: list[tuple[str, str]] = []  # (loại, giá trị nhãn)
            for pr in o.get("personal_projects", []):
                for t in pr.get("tech_stack", []) or []:
                    if t and t not in txt:
                        targets.append(("tech", t))
                for k in ("start_date", "end_date"):
                    if pr.get(k) and str(pr[k]) not in txt:
                        targets.append((f"proj.{k}", str(pr[k])))
            for e in o.get("experience", []):
                if e.get("company") and e["company"] not in txt:
                    targets.append(("company", e["company"]))
                for k in ("start_date", "end_date"):
                    if e.get(k) and str(e[k]) not in txt:
                        targets.append((f"exp.{k}", str(e[k])))

            for kind, want in targets:
                exact = find_exact(txt, want)
                if exact and exact != want:
                    # thay đúng 1 chuỗi literal trong file batch (dạng "want" hoặc 'want')
                    for q in ('"', "'"):
                        needle = f"{q}{want}{q}"
                        if needle in src:
                            src = src.replace(needle, f"{q}{exact}{q}", 1)
                            n_fix += 1
                            break
                    else:
                        leftovers.append(f"{rec['file']} [{kind}] {want!r} (không thay được literal)")
                elif not exact:
                    leftovers.append(f"{rec['file']} [{kind}] {want!r}")

        if n_fix and args.apply:
            path.write_text(src, encoding="utf-8")
        print(f"{path.name}: sửa {n_fix} chỗ" + ("" if args.apply else " (xem trước)"))
        total_fix += n_fix

    print(f"\nTổng: {total_fix} chỗ" + (" đã ghi." if args.apply else "."))
    if leftovers:
        print(f"Còn lại {len(leftovers)} chỗ cần sửa tay:")
        for s in leftovers:
            print("  -", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
