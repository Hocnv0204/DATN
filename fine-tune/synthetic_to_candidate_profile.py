#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
synthetic_to_candidate_profile.py
================================
Chuyển profile gốc của CV tổng hợp (fine-tune/_stage/synthetic_profiles.json, do
generate_synthetic_cvs.py sinh ra) sang đúng schema CandidateProfile mà notebook
dùng.

Lý do: 435 CV tổng hợp được sinh TỪ một profile có cấu trúc. Vì vậy nhãn silver
của chúng đã biết chính xác 100% - không cần gọi LLM đọc lại văn bản. Cách này
nhanh hơn, miễn phí và không có lỗi OCR/parse.

Việc còn lại là ánh xạ tên field:
    profile['education']   -> [{school, major, start_year, end_year, gpa}]
    profile['experience']  -> [{company, job_title, start_date, end_date, description[]}]
    profile['projects']    -> [{name, role, team_size, start_date, end_date,
                                github_url, description, tech_stack[]}]
    profile['skills']      -> [str]
    profile['certificates']-> [str]
    profile['honours']     -> [str]
    profile['languages']   -> [{language, note}]

Cách chạy:
    venv/bin/python synthetic_to_candidate_profile.py
"""

from __future__ import annotations

import json
import re
import pathlib
import sys
from typing import Optional

HERE = pathlib.Path(__file__).resolve().parent
STAGE_DIR = HERE / "_stage"
SRC = STAGE_DIR / "synthetic_profiles.json"
OUT = HERE / "silver_parts" / "batch_90_synthetic.py"

FILENAME_MAP = STAGE_DIR / "filename_map.json"


def split_period(period: str | None) -> tuple[str | None, str | None]:
    """Tách 'MM/YYYY - MM/YYYY' hoặc 'MM/YYYY - Hiện tại' thành (start, end).

    'Hiện tại'/'Present' -> end_date None (đang làm). Nhãn và văn bản dùng chung
    một chuỗi period nên tách ra vẫn khớp 100% với CV.
    """
    if not period:
        return None, None
    parts = [s.strip() for s in str(period).split(" - ")]
    start = parts[0] or None
    end = parts[1] if len(parts) > 1 else None
    if end and end.lower() in ("hiện tại", "hien tai", "present", "now", "hien tai"):
        end = None
    return start, end


def to_candidate(p: dict) -> dict:
    c = p["contact"]
    return {
        "personal_info": {
            "full_name": p["name"],
            "email": c["email"],
            "phone": c["phone"],
            "github_url": c["github"],
        },
        "objective": p.get("objective") or None,
        "education": [
            {
                "school": e["school"],
                "major": e.get("major"),
                "start_year": e.get("start_year"),
                "end_year": e.get("end_year"),
                "gpa": e.get("gpa"),
            }
            for e in p.get("education", [])
        ],
        "experience": [
            {
                "company": e["company"],
                "job_title": e.get("job_title"),
                "start_date": split_period(e.get("period"))[0],
                "end_date": split_period(e.get("period"))[1],
                "description": list(e.get("bullets", [])),
            }
            for e in p.get("experience", [])
        ],
        "personal_projects": [
            {
                "name": pr["name"],
                "role": pr.get("role"),
                "team_size": pr.get("team_size"),
                "start_date": split_period(pr.get("period"))[0],
                "end_date": split_period(pr.get("period"))[1],
                "github_url": pr.get("github") or None,
                "description": " ".join(pr.get("bullets", [])) or None,
                "tech_stack": list(pr.get("tech_stack", [])) or [pr.get("tech", "")],
            }
            for pr in p.get("projects", [])
        ],
        "skills": list(p.get("skills", [])),
        "certificates": list(p.get("certificates", [])),
        "honours": list(p.get("honours", [])),
        "languages": [
            {"language": l[0], "note": l[1]} for l in p.get("languages", [])
        ],
    }


def main() -> int:
    if not SRC.exists():
        print(f"[LỖI] Không thấy {SRC}\nHãy chạy lại generate_synthetic_cvs.py trước.")
        return 1

    raw = json.loads(SRC.read_text(encoding="utf-8"))

    # tên file đã đổi thành số -> ánh xạ ngược lại tên gốc
    number_map: dict[str, str] = {}
    if FILENAME_MAP.exists():
        entries = json.loads(FILENAME_MAP.read_text(encoding="utf-8"))
        number_map = {e["new"]: e["old"] for e in entries}

    batch = []
    for old_name, profile in raw.items():
        new_name = None
        for num, orig in number_map.items():
            if orig == old_name:
                new_name = num
                break
        if new_name is None:
            continue
        batch.append({"file": new_name, "profile": to_candidate(profile)})

    batch.sort(key=lambda r: int(r["file"][:-4]))

    # ghi ra file batch dưới dạng module python
    lines = [
        "# -*- coding: utf-8 -*-",
        '"""Batch tự động: nhãn silver cho 435 CV tổng hợp.',
        "",
        "Nguồn: _stage/synthetic_profiles.json (profile gốc lúc sinh CV), ánh xạ",
        "sang schema CandidateProfile. Không dùng LLM vì nhãn đã biết chính xác.",
        '"""',
        "",
        "BATCH = [",
    ]
    for rec in batch:
        # json.dumps xuất null (JSON) -> phải đổi thành None (Python)
        body = json.dumps(rec["profile"], ensure_ascii=False)
        body = re.sub(r"\bnull\b", "None", body)
        lines.append("    {")
        lines.append(f"        \"file\": {rec['file']!r},")
        lines.append(f"        \"profile\": {body},")
        lines.append("    },")
    lines.append("]")
    lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Đã ghi {len(batch)} profile tổng hợp vào {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
