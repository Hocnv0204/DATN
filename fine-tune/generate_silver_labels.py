#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_silver_labels.py
=========================
Bước sinh nhãn "Silver" bằng Gemini cho tập 520 file CV.

Hàm gọi API và JSON Schema giữ nguyên theo notebook
module1_finetune_qwen3_lora.ipynb (chỉ bổ sung retry + xác thực kết quả).

Cách chạy:
    export GEMINI_API_KEY=...
    venv/bin/python generate_silver_labels.py

    # chạy lại từ đúng chỗ đã dừng (không mất dữ liệu)
    venv/bin/python generate_silver_labels.py --resume

Tuỳ chọn:
    --model       tên model Gemini (mặc định lấy từ biến môi trường GEMINI_MODEL)
    --limit N     chỉ xử lý N file đầu (để thử trước)
    --start N     bắt đầu từ file thứ N
    --out PATH    đường dẫn file .jsonl đầu ra
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import pathlib
import random
import sys
import time
from typing import List, Optional

from pydantic import BaseModel

# ============================================================ JSON Schema (giữ nguyên notebook)
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

# ============================================================ Đường dẫn
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
INPUT_DIR = ROOT / "cv-analysis-service" / "cv_texts"
DEFAULT_OUT = ROOT / "cv-analysis-service" / "finetune_output" / "silver_dataset.jsonl"

# Model mặc định. Notebook dùng 'gemini-3.1-flash-lite' - đổi tên model là việc
# của người dùng; biến môi trường GEMINI_MODEL cho phép ghi đè mà không sửa code.
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Thời gian nghỉ giữa các lần gọi (tránh rate limit) và số lần thử lại
SLEEP_BETWEEN = float(os.environ.get("GEMINI_SLEEP", "1.0"))
MAX_RETRY = 4


# ============================================================ Gọi API
_client = None


def get_client():
    global _client
    if _client is None:
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("[LỖI] Thiếu GEMINI_API_KEY. Đặt biến môi trường trước khi chạy:")
            print("       export GEMINI_API_KEY='...'")
            sys.exit(1)
        _client = genai.Client(api_key=api_key)
    return _client


def extract_with_gemini(cv_text: str, model: str = DEFAULT_MODEL) -> Optional[dict]:
    """Gọi Gemini, trả về dict JSON hoặc None nếu lỗi (không ném exception).

    Có retry cho lỗi tạm thời (429/5xx). Lỗi schema hoặc lỗi không phải tạm
    thời thì trả None ngay để không mất thời gian vô ích.
    """
    client = get_client()
    last_err = None

    for attempt in range(MAX_RETRY):
        try:
            response = client.models.generate_content(
                model=model,
                contents=f"{SYSTEM_PROMPT}\n\nNội dung CV:\n{cv_text}",
                config={
                    "response_mime_type": "application/json",
                    "response_schema": CandidateProfile,
                    "temperature": 0.0,
                },
            )
            return json.loads(response.text)

        except Exception as e:
            last_err = e
            msg = str(e).lower()
            transient = any(k in msg for k in (
                "429", "500", "502", "503", "504",
                "rate limit", "quota", "resource_exhausted",
                "overloaded", "unavailable", "timeout", "deadline",
            ))
            if not transient or attempt == MAX_RETRY - 1:
                print(f"  -> Lỗi khi gọi API hoặc parse JSON: {e}")
                return None
            backoff = 2 ** attempt + random.uniform(0, 1)
            print(f"  -> Lỗi tạm thời, thử lại sau {backoff:.1f}s "
                  f"(lần {attempt + 1}/{MAX_RETRY})")
            time.sleep(backoff)

    print(f"  -> Lỗi khi gọi API hoặc parse JSON: {last_err}")
    return None


def validate_profile(data: dict) -> tuple[bool, str]:
    """Kiểm tra tối thiểu để tránh lưu rác vào tập train."""
    if not isinstance(data, dict):
        return False, "output không phải dict"
    pi = data.get("personal_info")
    if not isinstance(pi, dict) or not pi.get("full_name"):
        return False, "thiếu personal_info.full_name"
    name = str(pi["full_name"]).strip()
    if len(name) < 2:
        return False, f"full_name quá ngắn: {name!r}"
    # phải có ít nhất một trường nội dung nào khác ngoài họ tên
    rich = any(
        len(data.get(k) or []) > 0
        for k in ("education", "experience", "personal_projects", "skills")
    )
    if not rich:
        return False, "không có education/experience/projects/skills nào"
    return True, ""


# ============================================================ MAIN
def main() -> int:
    ap = argparse.ArgumentParser(description="Sinh nhãn silver bằng Gemini API")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="tên model Gemini")
    ap.add_argument("--input-dir", default=str(INPUT_DIR))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--limit", type=int, default=0, help="chỉ xử lý N file đầu")
    ap.add_argument("--start", type=int, default=1, help="bắt đầu từ file thứ N")
    ap.add_argument("--resume", action="store_true",
                    help="bỏ qua các file đã có trong file .jsonl đầu ra")
    args = ap.parse_args()

    input_dir = pathlib.Path(args.input_dir)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    file_paths = sorted(
        glob.glob(str(input_dir / "*.txt")),
        key=lambda p: int(pathlib.Path(p).stem) if pathlib.Path(p).stem.isdigit() else 0,
    )
    print(f"Tìm thấy {len(file_paths)} file .txt trong {input_dir}")
    print(f"Model: {args.model}")

    # ---- resume: đọc các file đã xử lý ----
    done: set[str] = set()
    if args.resume and out_path.exists():
        with out_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    done.add(json.loads(line)["file"])
                except Exception:
                    continue
        print(f"Resume: đã có {len(done)} bản ghi trong {out_path.name}")

    todo = [p for p in file_paths if pathlib.Path(p).name not in done]
    if args.start > 1:
        todo = todo[args.start - 1:]
    if args.limit:
        todo = todo[: args.limit]

    print(f"Sẽ xử lý {len(todo)} file.\n")

    # mở file ở chế độ append nếu resume, ngược lại ghi mới
    mode = "a" if (args.resume and out_path.exists()) else "w"
    n_ok = 0
    n_err = 0
    error_files: list[str] = []
    t0 = time.time()

    with out_path.open(mode, encoding="utf-8") as fout:
        for idx, file_path in enumerate(todo, start=1):
            filename = pathlib.Path(file_path).name
            print(f"[{idx}/{len(todo)}] Đang xử lý: {filename}")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cv_text = f.read()

                if not cv_text.strip():
                    print("  -> Bỏ qua: File rỗng.")
                    error_files.append(filename)
                    n_err += 1
                    continue

                result_json = extract_with_gemini(cv_text, args.model)

                if result_json:
                    ok, why = validate_profile(result_json)
                    if not ok:
                        print(f"  -> Bỏ qua: kết quả không hợp lệ ({why})")
                        error_files.append(filename)
                        n_err += 1
                        continue

                    fout.write(json.dumps({
                        "file": filename,
                        "instruction": SYSTEM_PROMPT,
                        "input": cv_text,
                        "output": json.dumps(result_json, ensure_ascii=False),
                    }, ensure_ascii=False) + "\n")
                    fout.flush()      # ghi ngay để --resume an toàn khi bị ngắt
                    n_ok += 1
                else:
                    error_files.append(filename)
                    n_err += 1

            except Exception as e:
                print(f"  -> Lỗi khi đọc file {filename}: {e}")
                error_files.append(filename)
                n_err += 1

            time.sleep(SLEEP_BETWEEN)

    elapsed = time.time() - t0
    print(f"\nHoàn thành! Đã lưu {n_ok} mẫu vào {out_path}")
    print(f"Thời gian: {elapsed / 60:.1f} phút ({elapsed / max(1, n_ok):.2f}s/file)")
    if error_files:
        print(f"Số file bị lỗi/bỏ qua: {len(error_files)}")
        err_path = out_path.parent / "silver_errors.txt"
        err_path.write_text("\n".join(error_files), encoding="utf-8")
        print(f"Danh sách lỗi: {err_path}")
        print(f"Gọi lại để xử lý tiếp: python3 {pathlib.Path(__file__).name} --resume")
    return 0


if __name__ == "__main__":
    sys.exit(main())
