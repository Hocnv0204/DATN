#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rename_cv_texts.py
==================
Đổi tên toàn bộ file trong cv-analysis-service/cv_texts/ thành số thứ tự
1.txt, 2.txt, ... N.txt.

Thứ tự đánh số cố định (để chạy lại cho cùng kết quả):
    1. real_pdf_01..56   (PDF trích text / OCR)
    2. real_img_01..30   (ảnh OCR)
    3. syn_<role>_<level> theo thứ tự ma trận Role x Level, rồi theo số thứ tự

Mỗi lần đổi tên đều lưu lại bảng ánh xạ cũ -> mới tại
fine-tune/_stage/filename_map.json (và bản CSV để đọc) để không mất liên kết
với nhãn Role/Level đã gán ở classify_real_cvs.py / synthetic_manifest.json.

Cách chạy:
    python3 rename_cv_texts.py            # xem trước kế hoạch đổi tên
    python3 rename_cv_texts.py --apply    # thực hiện đổi tên
    python3 rename_cv_texts.py --restore  # khôi phục tên gốc
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
TXT_DIR = ROOT / "cv-analysis-service" / "cv_texts"
STAGE_DIR = HERE / "_stage"
MAP_JSON = STAGE_DIR / "filename_map.json"
MAP_CSV = STAGE_DIR / "filename_map.csv"

# thứ tự role trong ma trận (khớp generate_synthetic_cvs.MATRIX)
ROLE_ORDER = ["backend", "frontend", "devops", "data", "ba", "qa", "security", "fullstack"]
LEVEL_ORDER = ["intern", "junior", "middle", "senior", "lead"]

REAL_PREFIX_ORDER = ["real_pdf_", "real_img_"]


def sort_key(path: pathlib.Path) -> tuple:
    """Sắp xếp có thứ tự, ổn định."""
    name = path.stem

    # 1) CV thật từ PDF
    if name.startswith("real_pdf_"):
        return (0, name)
    # 2) CV thật từ ảnh
    if name.startswith("real_img_"):
        return (1, name)

    # 3) CV tổng hợp: theo vị trí trong ma trận role x level
    if name.startswith("syn_"):
        parts = name.split("_")
        role = parts[1] if len(parts) > 1 else ""
        level = parts[2] if len(parts) > 2 else ""
        try:
            r = ROLE_ORDER.index(role)
        except ValueError:
            r = len(ROLE_ORDER)
        try:
            lv = LEVEL_ORDER.index(level)
        except ValueError:
            lv = len(LEVEL_ORDER)
        return (2, r, lv, name)

    # 4) file lạ -> đưa xuống cuối
    return (3, name)


def build_plan() -> list[tuple[pathlib.Path, pathlib.Path]]:
    files = sorted(TXT_DIR.glob("*.txt"), key=sort_key)
    plan: list[tuple[pathlib.Path, pathlib.Path]] = []
    for i, old in enumerate(files, start=1):
        new = TXT_DIR / f"{i}.txt"
        plan.append((old, new))
    return plan


def main() -> int:
    ap = argparse.ArgumentParser(description="Đổi tên file .txt thành số thứ tự 1.txt, 2.txt, ...")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="thực hiện đổi tên")
    group.add_argument("--restore", action="store_true", help="khôi phục tên gốc từ bảng ánh xạ")
    args = ap.parse_args()

    if not TXT_DIR.exists():
        print(f"[LỖI] Không thấy thư mục {TXT_DIR}")
        return 1

    # ---------------- khôi phục ----------------
    if args.restore:
        if not MAP_JSON.exists():
            print(f"[LỖI] Không có bảng ánh xạ {MAP_JSON}")
            return 1
        mapping = json.loads(MAP_JSON.read_text(encoding="utf-8"))
        count = 0
        for entry in mapping:
            src = TXT_DIR / entry["new"]
            dst = TXT_DIR / entry["old"]
            if src.exists() and not dst.exists():
                src.rename(dst)
                count += 1
        print(f"Đã khôi phục {count}/{len(mapping)} tên file gốc.")
        return 0

    # ---------------- lập kế hoạch ----------------
    plan = build_plan()
    if not plan:
        print("[LỖI] Không có file .txt nào.")
        return 1

    changes = [(o, n) for o, n in plan if o.name != n.name]
    unchanged = len(plan) - len(changes)

    print(f"Tổng file .txt: {len(plan)}")
    print(f"  Cần đổi tên : {len(changes)}")
    print(f"  Giữ nguyên  : {unchanged}\n")

    print(f"{'#':>4}  {'Tên cũ':<52} -> {'Tên mới'}")
    print("-" * 72)
    for i, (old, new) in enumerate(changes[:15], start=1):
        print(f"{i:>4}  {old.name:<52} -> {new.name}")
    if len(changes) > 15:
        print(f"     ... và {len(changes) - 15} file nữa")
    print("-" * 72)
    print(f"  {changes[-1][0].name if changes else '-'} -> {changes[-1][1].name if changes else '-'}")

    if not args.apply:
        print("\n(Chạy lại với --apply để thực hiện)")
        return 0

    # ---------------- thực hiện ----------------
    # đổi qua tên tạm trước để tránh va chạm (1.txt -> 1.txt không cần,
    # nhưng 1.txt -> 2.txt thì phải tránh ghi đè)
    tmp_map: list[tuple[pathlib.Path, pathlib.Path]] = []
    for i, (old, new) in enumerate(plan):
        if old.name == new.name:
            continue
        tmp = TXT_DIR / f".__renaming_{i}__.tmp"
        old.rename(tmp)
        tmp_map.append((tmp, new))

    applied = 0
    for tmp, new in tmp_map:
        if new.exists():
            new.unlink()
        tmp.rename(new)
        applied += 1

    # lưu bảng ánh xạ
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    mapping = [{"old": o.name, "new": n.name} for o, n in plan]
    MAP_JSON.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    with MAP_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["old", "new"])
        w.writerows([[m["old"], m["new"]] for m in mapping])

    print(f"\nĐã đổi tên {applied} file.")
    print(f"  Bảng ánh xạ : {MAP_JSON}")
    print(f"  Bảng CSV    : {MAP_CSV}")
    print(f"  Có thể khôi phục bằng: python3 rename_cv_texts.py --restore")
    return 0


if __name__ == "__main__":
    sys.exit(main())
