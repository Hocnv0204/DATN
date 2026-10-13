#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
synth_phase3.py — Phase 2+3: chốt dataset synthetic đã kiểm định.

Kết quả Phase 1 (synth_phase1.json + kiểm tra tay):
  - 0 lỗi JSON / schema / kiểu dữ liệu / grounding / omission (trừ nhóm
    không có trường schema) / trùng input / trùng identity.
  - 27 F-TIMELINE: trung thực với input (việc làm trước đại học ở CV lead/
    senior), không có căn cứ sửa — GIỮ NGUYÊN, đưa vào manual_review.
  - 2 C-SAME-TECH: input ghi cùng tech cho 2 projects — GIỮ NGUYÊN.
  - LinkedIn/soft-skills/activities/address/demo-URL: schema không có trường
    chứa — GIỮ NGUYÊN (không đổi schema), ghi nhận giới hạn.
  - Lặp template: đặc tính thiết kế của generator — ghi nhận, không sửa.

Do đó cleaned = sao chép nguyên 435 bản synthetic (giữ thứ tự), + verify lại
100% theo tiêu chí nghiệm thu, + 2 báo cáo JSON.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
JSONL = ROOT / "cv-analysis-service" / "finetune_output" / "silver_dataset.jsonl"
OUTDIR = ROOT / "cv-analysis-service" / "finetune_output" / "dataset"

sys.path.insert(0, str(ROOT / "fine-tune"))
from assemble_silver_dataset import CandidateProfile  # noqa: E402
from pydantic import ValidationError  # noqa: E402


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    mm = {e["new"]: e["old"] for e in json.loads(
        (ROOT / "fine-tune/_stage/filename_map.json").read_text(encoding="utf-8"))}
    recs = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    syn = [r for r in recs if mm.get(r["file"], "").startswith("syn_")]
    real_n = len(recs) - len(syn)
    phase1 = json.loads((ROOT / "fine-tune/_stage/synth_phase1.json").read_text(encoding="utf-8"))

    # ---- 1. cleaned (giữ nguyên nội dung + thứ tự) ----
    cleaned_path = OUTDIR / "silver_dataset_cleaned.jsonl"
    cleaned_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in syn) + "\n", encoding="utf-8")

    # ---- 2. verify nghiệm thu trên file cleaned ----
    lines = cleaned_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(syn), (len(lines), len(syn))
    n_schema_ok = 0
    for ln in lines:
        r = json.loads(ln)  # 100% dòng đọc được + output parse được (raise nếu lỗi)
        assert set(r.keys()) == {"file", "input", "instruction", "output"}
        CandidateProfile.model_validate(json.loads(r["output"]))
        n_schema_ok += 1

    # ---- 3. audit report ----
    ftimeline = [i for i in phase1["issues"] if i["code"] == "F-TIMELINE"]
    sametech = [i for i in phase1["issues"] if i["code"] == "C-SAME-TECH"]
    report = {
        "scope": "435 bản ghi synthetic (file 86.txt-520.txt). 59 bản real ngoài phạm vi task này.",
        "overview": {
            "total_before": len(syn),
            "total_after": len(lines),
            "removed": 0,
            "modified_records": 0,
            "unchanged_records": len(syn),
            "schema_valid": n_schema_ok,
        },
        "automated_checks": {
            "json_lines_readable": f"{len(lines)}/{len(lines)}",
            "output_json_valid": f"{n_schema_ok}/{len(syn)}",
            "schema_compliant": f"{n_schema_ok}/{len(syn)}",
            "grounding_errors_output_to_input": 0,
            "omission_errors_input_to_output": 0,
            "exact_duplicate_inputs": phase1["exact_duplicate_inputs"],
            "near_duplicate_pairs_jaccard_ge_05": len(phase1["near_duplicate_pairs"]),
            "duplicate_identities": len(phase1["duplicate_personal_info"]),
            "type_errors": 0,
            "sentinel_errors": 0,
        },
        "fixed_by_rule": [],
        "fixed_note": ("Không có nội dung nào đủ căn cứ để sửa: mọi trường output đều khớp input; "
                       "27 F-TIMELINE và 2 C-SAME-TECH trung thực với input nên giữ nguyên. "
                       "Chi tiết xem manual_review.json."),
        "reviewed_ok_no_change": {
            "C-SAME-TECH": sametech,
            "note": ("input ghi cùng tech cho 2 projects (vd 200.txt, 391.txt) — nhãn sao chép "
                     "đúng, không gán nhầm."),
        },
        "internal_inconsistencies": {
            "F-TIMELINE_pre_school_employment": ftimeline,
            "note": ("27 jobs ở CV lead/senior bắt đầu trước năm nhập học. Không tự kết luận sai "
                     "(làm trước học là khả thi) và không có căn cứ sửa ngày — giữ nguyên, "
                     "đưa vào manual_review để quyết định có loại khi cần dataset khắt khe."),
        },
        "duplicate_groups": phase1["near_duplicate_pairs"],
        "repeated_sentence_groups": phase1["repeated_sentence_groups"],
        "project_name_reuse_note": ("Tên dự án lấy từ pool ~15 tên nên lặp qua 56-78 CV (vd 'Hệ thống "
                                    "quản lý nội dung': 78 CVs); chi tiết mỗi CV khác nhau (số liệu/tech). "
                                    "Đây là đặc tính thiết kế, không phải sao chép lỗi."),
        "unresolved_schema_gaps": [
            {"field_missing": "LinkedIn", "affected": 288,
             "note": "Schema không có trường LinkedIn; 288 URL LinkedIn trong input không có nơi chứa. "
                     "GitHub/GitLab: 809/809 đầy đủ."},
            {"field_missing": "soft_skills (riêng)", "note": "CV in dòng soft skills nhưng schema chỉ có skills chung."},
            {"field_missing": "activities", "note": "CV in HOẠT ĐỘNG nhưng schema không có trường."},
            {"field_missing": "address/city", "note": "Địa chỉ trong header không có trường chứa."},
            {"field_missing": "demo/deploy URLs", "note": "URL demo/deploy trong project text không có trường chứa."},
        ],
        "limitations": [
            "Không có ground truth độc lập: nhãn đúng theo nghĩa 'khớp input', không xác minh với CV thật.",
            "Câu template lặp qua nhiều CV (tối đa 170x/câu) là đặc tính của generator; đa dạng paraphrase hạn chế.",
            "27 CV lead/senior có việc làm trước đại học — giữ nguyên theo nguyên tắc không suy đoán.",
            "Kiểm tra omission ở cấp item cho skills/certs/honours/languages: 0 thiếu (trừ nhóm schema gaps).",
            "59 bản real + 26 file loại không thuộc phạm vi task này.",
        ],
    }
    (OUTDIR / "dataset_audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- 4. manual review ----
    manual = []
    for it in ftimeline:
        manual.append({
            "file": it["file"],
            "issue_type": "F-TIMELINE_pre_school_employment",
            "json_path": it["json_path"],
            "evidence": it["evidence"],
            "reason": ("Kinh nghiệm bắt đầu trước năm nhập học. Input-output nhất quán; "
                       "không thể xác minh ngoài đời; người tự học đi làm trước đại học là khả thi."),
            "suggested_action": "GIỮ NGUYÊN (mặc định). Chỉ loại khi cần dataset khắt khe về tính điển hình.",
            "confidence": "low",
        })
    manual.append({
        "file": "DATASET",
        "issue_type": "schema_gap_linkedin",
        "json_path": "output.personal_info",
        "evidence": "288 URL LinkedIn trong input của 288/435 CV không có trường schema nào chứa; GitHub/GitLab 809/809 đầy đủ.",
        "reason": "Schema CandidateProfile không định nghĩa trường LinkedIn. Không được đổi schema khi chưa có yêu cầu.",
        "suggested_action": "Quyết định: (a) chấp nhận mất LinkedIn, hoặc (b) mở rộng schema thêm linkedin_url rồi sinh nhãn bổ sung.",
        "confidence": "high",
    })
    manual.append({
        "file": "DATASET",
        "issue_type": "template_repetition",
        "json_path": "output.experience[*].description / output.personal_projects[*].description",
        "evidence": (f"60 nhóm câu lặp ở >=5 CV (tối đa {phase1['repeated_sentence_groups'][0]['count']}x "
                     "cho câu system-design ở bản lead). Tên dự án tái dùng qua 56-78 CV."),
        "reason": ("Đặc tính của generator dùng template banks. Mỗi bản ghi vẫn nhất quán nội bộ; "
                   "rủi ro là model học thuộc mẫu câu thay vì trích xuất tổng quát."),
        "suggested_action": "Quyết định: (a) chấp nhận cho bản hiện tại, hoặc (b) yêu cầu mở rộng template/paraphrase rồi sinh lại.",
        "confidence": "high",
    })
    (OUTDIR / "dataset_manual_review.json").write_text(
        json.dumps(manual, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"cleaned: {len(lines)} bản ghi -> {cleaned_path}")
    print(f"schema OK: {n_schema_ok}/{len(syn)}")
    print(f"manual_review entries: {len(manual)} (27 timeline + 2 dataset-level)")
    print(f"report + manual: {OUTDIR}")


if __name__ == "__main__":
    main()
