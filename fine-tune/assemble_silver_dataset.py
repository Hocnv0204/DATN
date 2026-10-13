#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assemble_silver_dataset.py
==========================
Ghép các profile đã trích xuất (thủ công bởi AI, lưu trong
fine-tune/silver_parts/part_*.jsonl) với nội dung CV gốc trong
cv-analysis-service/cv_texts/ để tạo ra silver_dataset.jsonl.

Vì sao tách 2 bước:
  - Bước trích xuất cần đọc TOÀN BỘ nội dung mỗi CV (do AI đọc và hiểu).
  - Bước ghép chỉ cần đọc file từ đĩa -> nhanh, chính xác, không làm sai lệch
    văn bản gốc (input luôn khớp 100% với file .txt).

Mỗi dòng trong part_*.jsonl có dạng:
    {"file": "1.txt", "profile": { ...CandidateProfile... }}

Cách chạy:
    venv/bin/python assemble_silver_dataset.py
    venv/bin/python assemble_silver_dataset.py --validate-only
"""

from __future__ import annotations

import argparse
import importlib
import json
import pathlib
import sys
from collections import Counter, defaultdict
from typing import List, Optional

from pydantic import BaseModel, ValidationError

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
INPUT_DIR = ROOT / "cv-analysis-service" / "cv_texts"
PARTS_DIR = HERE / "silver_parts"
OUT_DIR = ROOT / "cv-analysis-service" / "finetune_output"
OUT_PATH = OUT_DIR / "silver_dataset.jsonl"

# ------------------------------------------------------------- Schema (khớp notebook)
class PersonalInfo(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    github_url: Optional[str] = None


class Education(BaseModel):
    school: str
    major: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    gpa: Optional[str] = None


class Experience(BaseModel):
    company: str
    job_title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: List[str] = []


class Project(BaseModel):
    name: str
    role: Optional[str] = None
    team_size: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    github_url: Optional[str] = None
    description: Optional[str] = None
    tech_stack: List[str] = []


class LanguageSkill(BaseModel):
    language: str
    note: Optional[str] = None


class CandidateProfile(BaseModel):
    personal_info: PersonalInfo
    objective: Optional[str] = None
    education: List[Education] = []
    experience: List[Experience] = []
    personal_projects: List[Project] = []
    skills: List[str] = []
    certificates: List[str] = []
    honours: List[str] = []
    languages: List[LanguageSkill] = []


SYSTEM_PROMPT = """
Bạn là hệ thống trích xuất thông tin từ CV.

Nhiệm vụ:
Đọc DUY NHẤT nội dung CV được cung cấp và trả về JSON theo đúng schema.
Đây là bài toán INFORMATION EXTRACTION, không phải bài toán viết lại, tóm tắt
hay suy luận thông tin.

QUY TẮC BẮT BUỘC:

1. NGUỒN DỮ LIỆU
- Chỉ sử dụng thông tin xuất hiện trực tiếp trong CV được cung cấp.
- Không sử dụng kiến thức bên ngoài.
- Không sử dụng thông tin từ các CV khác, ví dụ khác hoặc câu trả lời trước đó.
- Không tự bịa, suy luận hoặc dự đoán thông tin còn thiếu.

2. THÔNG TIN KHÔNG CÓ
- Nếu một trường dạng scalar không xuất hiện trong CV → null.
- Nếu một trường dạng array không có dữ liệu → [].
- Không dùng 0, "", "N/A", "Unknown" để biểu diễn thông tin không có.

3. GIỮ NGUYÊN THÔNG TIN
- Giữ nguyên ngôn ngữ gốc của CV.
- Không dịch.
- Không tự ý sửa tên người, tên công ty, tên trường, tên project.
- Không tự ý chuẩn hóa hoặc thay đổi số điện thoại, URL, ngày tháng hoặc số liệu.
- Không thêm ngày/tháng/ngày cụ thể nếu CV không cung cấp.

4. URL
- Chỉ lấy URL xuất hiện trực tiếp trong CV.
- Giữ URL dưới dạng raw URL.
- Không chuyển URL thành Markdown.
- Không thêm text, dấu ngoặc hoặc formatting vào URL.
- Không tự tạo hoặc suy đoán URL.

5. NGÀY THÁNG
- Giữ nguyên mức độ chi tiết được cung cấp trong CV.
- Nếu CV chỉ có năm → chỉ ghi năm.
- Nếu CV có tháng và năm → giữ tháng và năm.
- Không tự thêm tháng hoặc ngày.
- Không suy ra ngày kết thúc từ ngày bắt đầu hoặc ngược lại.

6. ENTITY ATTRIBUTION
- Chỉ gán thông tin cho một entity khi CV thể hiện rõ thông tin đó thuộc entity tương ứng.
- Không suy diễn quan hệ giữa các thông tin chỉ vì chúng xuất hiện gần nhau.
- Không lấy thông tin của project này để điền vào project khác.
- Không lấy thông tin của experience này để điền vào experience khác.
- Không lấy thông tin ở header, objective hoặc profile để suy ra role/job_title của project hoặc experience.

7. SKILLS VÀ PROJECT TECH STACK
- "skills" là các kỹ năng/công nghệ được liệt kê trong phần Skills/Technical Skills chung của CV.
- "tech_stack" của project chỉ chứa công nghệ được CV gắn trực tiếp với project đó.
- Không copy toàn bộ skills chung vào tech_stack của project.
- Không copy tech_stack của project này sang project khác.
- Nếu một công nghệ chỉ xuất hiện trong Skills chung nhưng không được gắn với project → không đưa công nghệ đó vào project.
- Nếu một công nghệ xuất hiện trực tiếp trong project → có thể đưa vào tech_stack của project.

8. ROLE VÀ JOB TITLE
- Chỉ điền role/job_title nếu CV ghi rõ role/job title tương ứng.
- Không suy ra role từ objective, ngành học, skills hoặc tên công nghệ.
- Không suy ra role từ tên project.

9. TEAM SIZE
- Chỉ điền team_size khi CV ghi rõ số lượng thành viên của project/team.
- Không suy ra team size.
- Nếu không có → null.

10. DESCRIPTION
- Với experience.description: tách từng bullet/câu thành từng phần tử riêng biệt.
- Không gộp nhiều bullet thành một câu.
- Không bỏ mất thông tin định lượng hoặc tên công nghệ.
- Không tự tóm tắt hoặc paraphrase nội dung.
- Với project.description: giữ nội dung mô tả trung thực theo CV.

11. FRAMEWORK / TECHNOLOGY GROUP
- Nếu CV viết dạng nhóm như:
  "Spring Cloud - Gateway, Eureka, Config, Feign"
  thì khai triển thành:
  "Spring Cloud Gateway",
  "Spring Cloud Eureka",
  "Spring Cloud Config",
  "Spring Cloud Feign".
- Chỉ khai triển những module thực sự được CV liệt kê.
- Không tự thêm module không xuất hiện trong CV.

12. TÍNH ĐẦY ĐỦ
- Không bỏ qua thông tin có trong CV chỉ vì thông tin đó xuất hiện ở cuối CV.
- Đặc biệt phải kiểm tra đầy đủ các section:
  personal information,
  objective,
  education,
  experience,
  projects,
  skills,
  certificates,
  honours,
  languages.

13. OUTPUT
- Chỉ trả về JSON hợp lệ.
- Không trả về Markdown.
- Không trả về code fence.
- Không giải thích.
- Không thêm field ngoài schema.
- Không đổi tên key trong schema.

"""

LEVELS = ["intern", "junior", "middle", "senior", "lead"]

# CV không thể thoả schema CandidateProfile vì thiếu dữ liệu bắt buộc
# (ví dụ full_name không xuất hiện trong văn bản, hoặc mục kinh nghiệm không
# nêu tên công ty). Không bịa dữ liệu -> loại khỏi tập train.
# Lý do chung cho nhóm CV bị ẩn danh (ảnh scan từ nguồn chia sẻ, phần lớn đã
# bị che thông tin cá nhân).
_ANON = ("CV bị ẩn danh: không có họ tên ở bất kỳ đâu trong văn bản. "
         "full_name là trường bắt buộc trong CandidateProfile nên không thể điền "
         "mà không bịa thông tin.")

EXCLUSIONS: dict[str, str] = {
    "10.txt": "OCR không đọc được họ tên (nội dung bắt đầu bằng mục Dự Án); "
              "full_name là trường bắt buộc nên không thể điền mà không bịa.",
    "28.txt": "Mục 'Contact' bị bỏ trống hoàn toàn: không có họ tên, email hay số điện "
              "thoại trong văn bản. full_name là trường bắt buộc nên không thể điền.",
    "46.txt": "Văn bản chỉ có email/sĐT/username (soul703), không nêu họ tên ở bất kỳ "
              "đâu. full_name là trường bắt buộc nên không thể điền mà không bịa.",
    "56.txt": "Email đã được che (chỉ còn \"'@gmail.com\"), không có họ tên trong văn bản. "
              "full_name là trường bắt buộc nên không thể điền mà không bịa.",
    "57.txt": "CV không có mục thông tin cá nhân: không họ tên, không email. "
              "full_name là trường bắt buộc nên không thể điền mà không bịa.",
    "59.txt": _ANON,
    "60.txt": _ANON,
    "61.txt": _ANON,
    "62.txt": _ANON,
    "63.txt": _ANON,
    "66.txt": _ANON,
    "67.txt": _ANON,
    "69.txt": _ANON,
    "71.txt": _ANON,
    "72.txt": _ANON,
    "73.txt": _ANON,
    "74.txt": _ANON,
    "75.txt": _ANON,
    "76.txt": _ANON,
    "77.txt": _ANON,
    "78.txt": _ANON,
    "79.txt": _ANON,
    "80.txt": _ANON,
    "83.txt": _ANON,
    "84.txt": _ANON,
    "85.txt": _ANON,
}


# ------------------------------------------------------------- helpers
def load_parts() -> dict[str, dict]:
    """Đọc các batch_*.py, gộp profile theo tên file (batch sau ghi đè nếu trùng).

    Dùng file .py thay vì .jsonl vì dễ viết/kiểm tra cú pháp hơn khi trích xuất
    thủ công (không phải escape dấu nháy trong nội dung tiếng Việt).
    """
    out: dict[str, dict] = {}
    if not PARTS_DIR.exists():
        return out
    sys.path.insert(0, str(PARTS_DIR))
    for p in sorted(PARTS_DIR.glob("batch_*.py")):
        mod_name = p.stem
        try:
            mod = importlib.import_module(mod_name)
            importlib.reload(mod)
        except Exception as e:
            print(f"  [LỖI IMPORT] {p.name}: {type(e).__name__}: {e}")
            continue
        rows = getattr(mod, "BATCH", [])
        n_ok = 0
        for rec in rows:
            fname = rec.get("file")
            profile = rec.get("profile")
            if not fname or not isinstance(profile, dict):
                print(f"  [LỖI CẤU TRÚC] {p.name}: thiếu 'file' hoặc 'profile'")
                continue
            out[fname] = profile
            n_ok += 1
        print(f"  {p.name}: {n_ok} bản ghi")
    return out


def semantic_check(profile: dict) -> tuple[bool, str]:
    """Kiểm tra chất lượng ngoài schema (schema đã validate bằng Pydantic)."""
    pi = profile.get("personal_info") or {}
    name = str(pi.get("full_name") or "").strip()
    if len(name) < 2:
        return False, f"full_name không hợp lệ: {name!r}"
    if name.lower() in {"null", "none", "n/a", "unknown", "n/a"}:
        return False, f"full_name là giá trị vô nghĩa: {name!r}"
    rich = any(profile.get(k) for k in ("education", "experience", "personal_projects", "skills"))
    if not rich:
        return False, "không có education/experience/personal_projects/skills"
    # full_name phải có vẻ là tên người (không phải cụm từ dài)
    if len(name) > 80:
        return False, "full_name quá dài, có thể là đoạn văn"
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Ghép silver_dataset.jsonl từ các part đã trích xuất")
    ap.add_argument("--validate-only", action="store_true", help="chỉ kiểm tra, không ghi file")
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()

    print("Đọc các phần đã trích xuất:")
    profiles = load_parts()
    if not profiles:
        print("\nChưa có part nào trong", PARTS_DIR)
        return 1

    # danh sách file .txt đích
    files = sorted(
        INPUT_DIR.glob("*.txt"),
        key=lambda p: int(p.stem) if p.stem.isdigit() else 10**9,
    )
    print(f"\nFile .txt trong dataset: {len(files)}")
    print(f"Profile đã trích xuết  : {len(profiles)}")

    missing = [f.name for f in files if f.name not in profiles and f.name not in EXCLUSIONS]
    extra = [k for k in profiles if not (INPUT_DIR / k).exists()]

    records: list[dict] = []
    rejected: dict[str, str] = {}

    for f in files:
        if f.name in EXCLUSIONS:
            rejected[f.name] = f"loại có chủ đích: {EXCLUSIONS[f.name]}"
            continue
        if f.name not in profiles:
            continue
        raw_profile = profiles[f.name]

        # 1) validate bằng Pydantic (đúng schema notebook dùng)
        try:
            CandidateProfile.model_validate(raw_profile)
        except ValidationError as e:
            first = e.errors()[0]
            loc = ".".join(str(x) for x in first.get("loc", ()))
            rejected[f.name] = f"schema: {loc} {first.get('msg', '')}"
            continue

        # 2) validate ngữ nghĩa
        ok, why = semantic_check(raw_profile)
        if not ok:
            rejected[f.name] = why
            continue

        cv_text = f.read_text(encoding="utf-8")
        if not cv_text.strip():
            rejected[f.name] = "file rỗng"
            continue

        records.append({
            "file": f.name,
            "instruction": SYSTEM_PROMPT,
            "input": cv_text,
            "output": json.dumps(raw_profile, ensure_ascii=False),
        })

    # ---------------- báo cáo ----------------
    print(f"\n{'=' * 62}")
    print(f"  Hợp lệ      : {len(records)}")
    print(f"  Bị loại     : {len(rejected)}")
    print(f"  Chưa trích xuất: {len(missing)}")
    if extra:
        print(f"  Profile không khớp file nào: {len(extra)} -> {extra[:5]}")

    # thống kê theo role/level (dùng bảng nhãn gốc trước khi đổi tên)
    map_path = HERE / "_stage" / "filename_map.json"
    role_level: dict[str, tuple[str, str]] = {}
    if map_path.exists():
        old_to_new = {e["new"]: e["old"] for e in json.loads(map_path.read_text(encoding="utf-8"))}
        lab_path = HERE / "_stage" / "real_labels.json"
        labels = json.loads(lab_path.read_text(encoding="utf-8")) if lab_path.exists() else {}
        syn_path = HERE / "_stage" / "synthetic_manifest.json"
        syn = json.loads(syn_path.read_text(encoding="utf-8")) if syn_path.exists() else {}

        def role_level_of(new_name: str) -> tuple[str, str]:
            old = old_to_new.get(new_name, "")
            if old in labels:
                return labels[old]["role"], labels[old]["level"]
            for m in syn.get("manifest", []):
                if m["file"] == old:
                    return m["role"], m["level"]
            return "?", "?"

        for r in records:
            rl = role_level_of(r["file"])
            role_level[r["file"]] = rl

    if role_level:
        print(f"\nPhân bố theo Level (trong {len(records)} bản ghi hợp lệ):")
        cnt = Counter(lv for _, lv in role_level.values())
        for lv in LEVELS:
            print(f"  {lv:<8}: {cnt.get(lv, 0)}")
        print(f"\nPhân bố theo Role:")
        cnt_r = Counter(ro for ro, _ in role_level.values())
        for ro, c in sorted(cnt_r.items(), key=lambda x: -x[1]):
            print(f"  {ro:<10}: {c}")

    if missing:
        print(f"\nChưa trích xuất ({len(missing)}): {missing[:20]}"
              + ("..." if len(missing) > 20 else ""))
    if rejected:
        print(f"\nBị loại ({len(rejected)}):")
        for k, v in list(rejected.items())[:15]:
            print(f"  {k}: {v}")

    print("=" * 62)

    if args.validate_only:
        return 0

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\nĐã ghi {len(records)} bản ghi vào {out_path} ({size_mb:.2f} MB)")

    # ghi danh sách file còn thiếu để lần sau làm tiếp
    if missing:
        todo = out_path.parent / "silver_todo.txt"
        todo.write_text("\n".join(missing), encoding="utf-8")
        print(f"Danh sách còn lại: {todo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
