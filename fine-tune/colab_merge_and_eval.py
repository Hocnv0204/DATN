# ============================================================
# CELL A - Merge LoRA vào base model (bắt buộc)
# ============================================================
# Notebook hiện tại chỉ lưu adapter (~70 MB). Muốn chạy ở ai-service thì cần
# base model đã được merge. Cell này tạo thư mục merged_model/ trên Drive.
#
# Kết quả: /content/drive/MyDrive/cv-analysis-service/finetune_output/merged_model/

import os, shutil, torch
from unsloth import FastLanguageModel
from transformers import AutoTokenizer

BASE_MODEL_NAME = "Qwen/Qwen3-0.6B"
MERGED_DIR = os.path.join(OUTPUT_DIR, "merged_model")

print("1/4 Nạp base model + adapter...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL_NAME,
    max_seq_length=4096,          # >= 4028 như audit đã tính
    dtype=None,                   # tự chọn theo GPU (bf16 trên T4/A100)
    load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

print("2/4 Merge adapter vào base (full precision)...")
# Quan trọng: merge ở float16/float32, KHÔNG merge ở 4bit.
# Merge trên base 4bit làm LoRA adapter mất tác dụng.
model.save_pretrained_merged(
    save_pretrained_directory=MERGED_DIR,
    tokenizer=tokenizer,
    save_method="merged_16bit",   # 0.6B -> ~1.2 GB
)
print(f"    -> {MERGED_DIR}")
!ls -lh {MERGED_DIR}

# ============================================================
# CELL B - Kiểm tra nhanh model vừa merge (CPU/GPU đều chạy)
# ============================================================
import json

from unsloth import FastLanguageModel
from transformers import AutoTokenizer
from pydantic import BaseModel
from typing import List, Optional

# --- nạp lại đúng schema như notebook để so sánh công bằng ---
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

SYSTEM_PROMPT = """Bạn là hệ thống trích xuất thông tin CV. Đọc văn bản CV được cung cấp và trả
về JSON đúng theo schema. Quy tắc:
- Nếu một trường không có trong CV, để null hoặc mảng rỗng, KHÔNG tự bịa thông tin.
- Giữ nguyên ngôn ngữ gốc của nội dung (không dịch).
- "description" trong experience: tách thành từng câu/bullet riêng biệt trong mảng.
- Khi CV viết tắt kiểu "Framework - A, B, C" (nhóm nhiều module dưới một framework),
  khai triển đầy đủ thành "Framework A", "Framework B", "Framework C" trong tech_stack/skills,
  KHÔNG tách rời "A", "B", "C" thành các mục đứng riêng không rõ nghĩa."""

# ĐỔI max_new_tokens: 1024 -> 2048 (49.6% nhãn dài hơn 1024 token)
MAX_NEW_TOKENS = 2048

tok = AutoTokenizer.from_pretrained(MERGED_DIR)
m, _ = FastLanguageModel.from_pretrained(
    model_name=MERGED_DIR, max_seq_length=4096, dtype=None, load_in_4bit=True
)

def run(cv_text):
    prompt = (f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
              f"<|im_start|>user\n{cv_text}<|im_end|>\n"
              f"<|im_start|>assistant\n")
    inputs = tok([prompt], return_tensors="pt").to("cuda")
    out = m.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS,
                     do_sample=False, use_cache=True)
    gen = out[0][inputs.input_ids.shape[1]:]
    text = tok.decode(gen, skip_special_tokens=True).strip()
    return text

# --- đo trên N mẫu validation, không phải 1 mẫu ---
import json as _json

with open(os.path.join(OUTPUT_DIR, "val.jsonl"), encoding="utf-8") as f:
    val_records = [_json.loads(l) for l in f if l.strip()]

n_ok = 0
for i, r in enumerate(val_records[:10]):
    pred = run(r["input"])
    try:
        CandidateProfile.model_validate(_json.loads(pred))
        ok_json = True
    except Exception as e:
        ok_json = False
    # khớp chính xác toàn bộ nội dung hay không
    exact = pred.strip() == r["output"].strip()
    n_ok += int(ok_json)
    print(f"[{i}] json_ok={ok_json}  exact_match={exact}  len={len(pred)}")

print(f"\nJSON hợp lệ: {n_ok}/10")
