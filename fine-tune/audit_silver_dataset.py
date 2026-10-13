#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_silver_dataset.py
=======================
Kiểm tra chất lượng tập nhãn silver trước khi train. Bắt được 3 lỗi đã gây ra
việc model học thuộc thay vì đọc CV:

  1. Output vượt max_seq_length / max_new_tokens -> bị cắt giữa JSON.
  2. Nhãn có trường KHÔNG suy ra được từ văn bản (mất thông tin khi render).
  3. Quan hệ "ngắn hỏng" giữa các trường (vd tech_stack luôn là bản sao của
     skills) -> model học đường tắt thay vì trích xuất.

Cách chạy:
    venv/bin/python audit_silver_dataset.py
    venv/bin/python audit_silver_dataset.py --max-seq 4096 --max-new 2048
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
JSONL = ROOT / "cv-analysis-service" / "finetune_output" / "silver_dataset.jsonl"
MAP = ROOT / "fine-tune" / "_stage" / "filename_map.json"
MODEL = "Qwen/Qwen3-0.6B"

# token dành cho phần template chat (<|im_start|>, <|im_end|>, system prompt wrapper...)
TEMPLATE_OVERHEAD = 256


def load():
    recs = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    src = {}
    if MAP.exists():
        src = {e["new"]: e["old"] for e in json.loads(MAP.read_text(encoding="utf-8"))}
    return recs, src


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-seq", type=int, default=2048)
    ap.add_argument("--max-new", type=int, default=1024)
    ap.add_argument("--skip-tokenizer", action="store_true",
                    help="bỏ qua đo token, dùng ước lượng theo ký tự")
    args = ap.parse_args()

    recs, src = load()
    n = len(recs)
    print(f"Tập nhãn: {n} mẫu\n")
    if n == 0:
        print("Chưa có silver_dataset.jsonl")
        return 1

    problems = 0

    # ---------------------------------------------------------------- 1. độ dài
    tk = None
    if not args.skip_tokenizer:
        try:
            from tokenizers import Tokenizer
            tk = Tokenizer.from_pretrained(MODEL)
        except Exception as e:
            print(f"[!] Không tải được tokenizer ({e}); dùng ước lượng theo ký tự.\n")

    if tk is not None:
        enc = tk.encode
        out_tok = [(len(enc(r["output"]).ids), r["file"]) for r in recs]
        tot_tok = [
            len(enc(r["instruction"]).ids) + len(enc(r["input"]).ids)
            + len(enc(r["output"]).ids) + TEMPLATE_OVERHEAD
            for r in recs
        ]
        label = f"({MODEL})"
    else:
        out_tok = [(len(r["output"]) // 2.2, r["file"]) for r in recs]
        tot_tok = [(len(r["instruction"]) + len(r["input"]) + len(r["output"])) // 2.2 + TEMPLATE_OVERHEAD
                   for r in recs]
        label = "(ước lượng 2.2 ký tự/token)"

    out_over = [x for x in out_tok if x[0] > args.max_new]
    seq_over = sum(1 for x in tot_tok if x > args.max_seq)
    mx = max(t for t, _ in out_tok)
    print("[1] ĐỘ DÀI " + label)
    print(f"    output  max = {mx} token")
    print(f"    > max_new_tokens({args.max_new}) : {len(out_over)}/{n} ({100*len(out_over)/n:.1f}%)")
    print(f"    > max_seq_length({args.max_seq})  : {seq_over}/{n} ({100*seq_over/n:.1f}%)")
    if out_over or seq_over:
        problems += 1
        need_new = max(args.max_new, mx + 64)
        need_seq = max(args.max_seq, max(tot_tok) + 64)
        print(f"    -> SỬA: max_new_tokens = {need_new}, max_seq_length = {need_seq}")
        if out_over:
            print(f"       ví dụ bị cắt: {[f for _, f in out_over[:5]]}")
    else:
        print("    OK")
    print()

    # ------------------------------------------------- 2. nhãn không suy ra được
    # So sánh sau CHUẨN HÓA (không phân biệt hoa/thường, tên tháng, số 0 đứng
    # đầu, dấu câu): model học được các chuẩn hóa này từ hàng trăm ví dụ.
    # Chỉ gắn cờ khi nội dung thật sự không có căn cứ trong văn bản.
    MONTHS = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "jun": "06", "jul": "07", "aug": "08", "sep": "09", "sept": "09",
        "oct": "10", "nov": "11", "dec": "12",
    }

    def _norm(s: str) -> str:
        s = str(s).lower()
        for name, num in MONTHS.items():
            s = re.sub(rf"\b{name}\b", num, s)
        s = re.sub(r"\b0(\d)", r"\1", s)          # 09/2023 -> 9/2023
        s = re.sub(r"[\s._\-/]+", "", s)          # node.js -> nodejs
        return s

    def _repo_path(url: str) -> str:
        """Chuẩn hóa URL repo để so sánh: bỏ scheme/domain và '.git' ở cuối."""
        u = str(url).strip()
        u = re.sub(r"^https?://", "", u)
        u = re.sub(r"^(github|gitlab|bitbucket)\.(com|org)/", "", u)
        u = re.sub(r"\.git$", "", u)
        return u.strip("/")

    def _grounded(txt: str, val: str) -> bool:
        if not val:
            return True
        if val in txt:
            return True
        nv = _norm(val)
        if not nv:
            return True
        ntxt = _norm(txt)
        return nv in ntxt

    missing = Counter()
    for r in recs:
        txt, o = r["input"], json.loads(r["output"])
        for p in o.get("personal_projects", []):
            if p.get("team_size") and not _grounded(txt, str(p["team_size"])):
                missing["project.team_size"] += 1
            if p.get("github_url") and not _grounded(txt, _repo_path(p["github_url"])):
                missing["project.github_url"] += 1
            for t in (p.get("tech_stack") or []):
                if t and not _grounded(txt, t):
                    missing["project.tech_stack[]"] += 1
        for e in o.get("experience", []):
            if e.get("company") and not _grounded(txt, e["company"]):
                missing["experience.company"] += 1
            if e.get("start_date") and not _grounded(txt, str(e["start_date"])):
                missing["experience.start_date"] += 1
            if e.get("end_date") and not _grounded(txt, str(e["end_date"])):
                missing["experience.end_date"] += 1

    print("[2] TRƯỜNG KHÔNG SUY RA ĐƯỢC TỪ VĂN BẢN")
    if not missing:
        print("    OK - mọi trường đều có bằng chứng trong CV")
    else:
        problems += 1
        syn_missing = sum(1 for r in recs
                          if src.get(r["file"], "").startswith("syn_")
                          and any(v and str(v) not in r["input"]
                                  for v in [json.loads(r["output"])["personal_projects"][0].get("team_size")]
                                  if v))
        for k, v in missing.most_common():
            print(f"    {k:<26} {v}")
        print("    -> SỬA: renderer phải in ra mọi trường có trong nhãn "
              "(team_size, github, tech theo project) ở TẤT CẢ layout")
    print()

    # --------------------------------------- 3. nhãn suy biến (không cần đọc cũng đoán được)
    # Sau khi sửa generator, tech_stack là tập con THẬT SỰ của skills (2-4 mục,
    # khác nhau giữa các project, in ra trong văn bản) -> subset là bình thường.
    # Cái cần bắt giờ là:
    #   (a) tech_stack == toàn bộ skills (không có tín hiệu phân biệt project);
    #   (b) mọi project trong 1 CV dùng tech y hệt nhau;
    #   (c) end_date luôn null ở CV tổng hợp (không học được gì về trường này).
    total_proj = 0
    full_copy = 0
    same_tech = 0
    n_syn_end_null = 0
    n_syn_end_total = 0
    for r in recs:
        o = json.loads(r["output"])
        sk = set(o.get("skills") or [])
        ts_all = [set(p.get("tech_stack") or []) for p in (o.get("personal_projects") or [])]
        ts_all = [t for t in ts_all if t]
        total_proj += len(ts_all)
        full_copy += sum(1 for t in ts_all if sk and t == sk)
        if len(ts_all) > 1 and all(t == ts_all[0] for t in ts_all):
            same_tech += 1
        if src.get(r["file"], "").startswith("syn_"):
            for e in (o.get("experience") or []) + (o.get("personal_projects") or []):
                n_syn_end_total += 1
                if not e.get("end_date"):
                    n_syn_end_null += 1

    print("[3] NHÃN SUY BIẾN (đoán được mà không cần đọc CV)")
    if not total_proj:
        print("    OK")
    else:
        n_cv = len(recs)
        print(f"    tech_stack == toàn bộ skills        : {full_copy}/{total_proj}")
        print(f"    mọi project trong 1 CV cùng tech    : {same_tech}/{n_cv} CV")
        print(f"    end_date null ở CV tổng hợp         : {n_syn_end_null}/{n_syn_end_total}")
        bad = (full_copy > total_proj * 0.2) or (same_tech > n_cv * 0.2) or (
            n_syn_end_total and n_syn_end_null / n_syn_end_total > 0.95)
        if bad:
            problems += 1
            print("    -> SỬA: tech mỗi project phải khác nhau và in ra văn bản; "
                  "end_date phải tách từ period.")
        else:
            print("    OK")
    print()

    print("=" * 58)
    if problems == 0:
        print("KHÔNG CÓ VẤN ĐỀ NGHIÊM TRỌNG - có thể train.")
    else:
        print(f"PHÁT HIỆN {problems} NHÓM VẤN ĐỀ - nên sửa trước khi train lại.")
    print("=" * 58)
    return 0




if __name__ == "__main__":
    sys.exit(main())
