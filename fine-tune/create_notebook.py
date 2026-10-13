import json
import os

nb = {
    "cells": [],
    "metadata": {},
    "nbformat": 4,
    "nbformat_minor": 5
}

def add_markdown(source):
    nb["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\\n" for line in source.split("\\n")]
    })

def add_code(source):
    nb["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\\n" for line in source.split("\\n")]
    })

# Cell 1
add_markdown("""# Module 1: Fine-tune Qwen3-1.7B bằng LoRA & Xuất GGUF

## Tổng quan:
1. **Sinh Silver Dataset**: Sử dụng Gemini API để trích xuất thông tin từ CV (raw text) thành định dạng JSON có cấu trúc (hoặc load silver_dataset.jsonl đã chuẩn bị).
2. **Fine-tune LoRA**: Sử dụng Unsloth tải mô hình `Qwen3-1.7B` (4-bit, max_seq_length=4096), huấn luyện (SFT) 5 epochs trên bộ dữ liệu silver dataset.
3. **Merge & Xuất GGUF**: Lưu LoRA adapter, merge 16-bit và export định dạng GGUF `q4_k_m` để phục vụ suy luận tốc độ cao trên CPU / llama.cpp.
4. **Đánh giá**: Kiểm tra validation trên 10 mẫu với max_new_tokens=2048, đối chiếu tính hợp lệ của schema Pydantic và nhãn silver.
""")

# Cell 2
add_code("""# Cài đặt các thư viện cần thiết
!pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install --no-deps xformers trl peft accelerate bitsandbytes
!pip install google-genai pydantic scikit-learn
""")

# Cell 3
add_code("""import os
from google.colab import drive
import time
import json
from google import genai
from pydantic import BaseModel
from typing import Optional, List

# Mount Google Drive
drive.mount('/content/drive')

# Khai báo đường dẫn
INPUT_DIR = '/content/drive/MyDrive/cv-analysis-service/cv_texts/'
OUTPUT_DIR = '/content/drive/MyDrive/cv-analysis-service/finetune_output/'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Kiểm tra thư mục input
if not os.path.exists(INPUT_DIR) or len(os.listdir(INPUT_DIR)) == 0:
    raise FileNotFoundError(f"Thư mục {INPUT_DIR} không tồn tại hoặc trống. Vui lòng kiểm tra lại Google Drive.")

# Nhập API Key (Không hardcode)
import getpass
GEMINI_API_KEY = getpass.getpass('Nhập GEMINI_API_KEY: ')

# Khởi tạo client Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
""")

# Cell 4
add_code("""# Định nghĩa JSON Schema (Pydantic)
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
""")

# Cell 5
add_code("""# Định nghĩa SYSTEM_PROMPT
SYSTEM_PROMPT = \"\"\"Bạn là hệ thống trích xuất thông tin CV. Đọc văn bản CV được cung cấp và trả
về JSON đúng theo schema. Quy tắc:
- Nếu một trường không có trong CV, để null hoặc mảng rỗng, KHÔNG tự bịa thông tin.
- Giữ nguyên ngôn ngữ gốc của nội dung (không dịch).
- "description" trong experience: tách thành từng câu/bullet riêng biệt trong mảng.
- Khi CV viết tắt kiểu "Framework - A, B, C" (nhóm nhiều module dưới một framework),
  khai triển đầy đủ thành "Framework A", "Framework B", "Framework C" trong tech_stack/skills,
  KHÔNG tách rời "A", "B", "C" thành các mục đứng riêng không rõ nghĩa.\"\"\"
""")

# Cell 6
add_code("""# Hàm gọi Gemini API để lấy JSON
def extract_with_gemini(cv_text):
    try:
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=f"{SYSTEM_PROMPT}\\n\\nNội dung CV:\\n{cv_text}",
            config={
                "response_mime_type": "application/json",
                "response_schema": CandidateProfile,
                "temperature": 0.0
            },
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Lỗi khi gọi API hoặc parse JSON: {e}")
        return None
""")

# Cell 7
add_code("""# Sinh silver_dataset.jsonl
import glob

file_paths = glob.glob(os.path.join(INPUT_DIR, "*.txt"))
print(f"Tìm thấy {len(file_paths)} file .txt trong {INPUT_DIR}")

dataset_records = []
error_files = []

for idx, file_path in enumerate(file_paths):
    filename = os.path.basename(file_path)
    print(f"[{idx+1}/{len(file_paths)}] Đang xử lý: {filename}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            cv_text = f.read()
            
        if not cv_text.strip():
            print(f"  -> Bỏ qua: File rỗng.")
            error_files.append(filename)
            continue
            
        result_json = extract_with_gemini(cv_text)
        
        if result_json:
            dataset_records.append({
                "file": filename,
                "instruction": SYSTEM_PROMPT,
                "input": cv_text,
                "output": json.dumps(result_json, ensure_ascii=False)
            })
        else:
            error_files.append(filename)
            
    except Exception as e:
        print(f"  -> Lỗi khi đọc file {filename}: {e}")
        error_files.append(filename)
        
    time.sleep(1) # Tránh rate limit

silver_dataset_path = os.path.join(OUTPUT_DIR, 'silver_dataset.jsonl')
with open(silver_dataset_path, 'w', encoding='utf-8') as f:
    for record in dataset_records:
        f.write(json.dumps(record, ensure_ascii=False) + '\\n')

print(f"\\nHoàn thành! Đã lưu {len(dataset_records)} mẫu vào {silver_dataset_path}")
if error_files:
    print(f"Số file bị lỗi/bỏ qua: {len(error_files)}")
""")

# Cell 8
add_code("""# Chia tập train/val
from sklearn.model_selection import train_test_split

with open(silver_dataset_path, 'r', encoding='utf-8') as f:
    records = [json.loads(line) for line in f]

train_records, val_records = train_test_split(records, test_size=0.2, random_state=42)

train_path = os.path.join(OUTPUT_DIR, 'train.jsonl')
val_path = os.path.join(OUTPUT_DIR, 'val.jsonl')

with open(train_path, 'w', encoding='utf-8') as f:
    for record in train_records:
        f.write(json.dumps(record, ensure_ascii=False) + '\\n')

with open(val_path, 'w', encoding='utf-8') as f:
    for record in val_records:
        f.write(json.dumps(record, ensure_ascii=False) + '\\n')
        
print(f"Đã chia {len(train_records)} mẫu train và {len(val_records)} mẫu val.")
""")

# Cell 8
add_code("""# Load model Qwen3-1.7B qua Unsloth
from unsloth import FastLanguageModel
import torch

model_name = "unsloth/Qwen3-1.7B"
max_seq_length = 4096
dtype = None # Tự động phát hiện
load_in_4bit = True

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)
""")

# Cell 10
add_code("""# Gắn LoRA adapter
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 42,
    use_rslora = False,
    loftq_config = None,
)
""")

# Cell 11
add_code("""# Format dataset theo chat template
from datasets import Dataset

chat_template = \"\"\"<|im_start|>system
{instruction}<|im_end|>
<|im_start|>user
{input}<|im_end|>
<|im_start|>assistant
{output}<|im_end|>
\"\"\"

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input_text, output in zip(instructions, inputs, outputs):
        text = chat_template.format(instruction=instruction, input=input_text, output=output)
        texts.append(text)
    return { "text" : texts, }

train_dataset = Dataset.from_json(train_path)
val_dataset = Dataset.from_json(val_path)

train_dataset = train_dataset.map(formatting_prompts_func, batched = True)
val_dataset = val_dataset.map(formatting_prompts_func, batched = True)
""")

# Cell 11
add_code("""# Cấu hình SFTTrainer và Train
from trl import SFTTrainer
from transformers import TrainingArguments

output_model_dir = os.path.join(OUTPUT_DIR, 'lora_adapter')

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = train_dataset,
    eval_dataset = val_dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        num_train_epochs = 5,
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        eval_strategy = "steps",
        eval_steps = 10,
        save_strategy = "epoch",
        save_total_limit = 2,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 42,
        output_dir = output_model_dir,
        report_to = "none"
    ),
)

trainer_stats = trainer.train()

# In kết quả train loss, eval loss và đánh giá overfitting
print("\\n--- ĐÁNH GIÁ KẾT QUẢ HUẤN LUYỆN ---")
history = trainer.state.log_history
train_losses = [log['loss'] for log in history if 'loss' in log]
eval_losses = [log['eval_loss'] for log in history if 'eval_loss' in log]

if train_losses:
    print(f"Train Loss cuối cùng: {train_losses[-1]:.4f}")
if eval_losses:
    print(f"Eval Loss cuối cùng: {eval_losses[-1]:.4f}")
    
    # Check simple overfitting criteria: if last eval loss is higher than min eval loss significantly
    min_eval_loss = min(eval_losses)
    if eval_losses[-1] > min_eval_loss * 1.1:
        print("CẢNH BÁO: Có dấu hiệu Overfitting (Eval loss tăng trở lại).")
""")

# Cell 12
add_code("""# Lưu adapter + merge + GGUF (để serve nhanh)
# 1. Adapter (để train tiếp / kiểm tra)
model.save_pretrained(output_model_dir)
tokenizer.save_pretrained(output_model_dir)
print(f"Đã lưu adapter vào: {output_model_dir}")

# 2. Merge full precision (KHÔNG merge trên base 4bit - sẽ làm mất tác dụng LoRA)
MERGED_DIR = os.path.join(OUTPUT_DIR, "merged_model")
model.save_pretrained_merged(
    save_pretrained_directory = MERGED_DIR,
    tokenizer = tokenizer,
    save_method = "merged_16bit",
)
print(f"Đã lưu merged model vào: {MERGED_DIR}")

# 3. GGUF Q4_K_M (file duy nhất cần tải về local để serve)
GGUF_DIR = os.path.join(OUTPUT_DIR, "gguf")
model.save_pretrained_gguf(
    save_directory = GGUF_DIR,
    tokenizer = tokenizer,
    quantization_method = "q4_k_m",
)
print(f"Đã lưu GGUF vào: {GGUF_DIR}")
print("Tải file .gguf về máy, đặt vào ai-service/merged_model/ rồi restart service.")
""")

# Cell 13
add_code("""# Đánh giá trên 10 mẫu validation
import json as _json

FastLanguageModel.for_inference(model)

N_EVAL = min(10, len(val_records))
n_json_ok = 0
n_exact = 0
for i in range(N_EVAL):
    sample = val_records[i]
    prompt = f\"\"\"<|im_start|>system
{sample['instruction']}<|im_end|>
<|im_start|>user
{sample['input']}<|im_end|>
<|im_start|>assistant
\"\"\"
    inputs = tokenizer([prompt], return_tensors = "pt").to("cuda")
    out = model.generate(
        **inputs,
        max_new_tokens = 2048,
        do_sample = False,
        use_cache = True,
    )
    gen = out[0][inputs.input_ids.shape[1]:]
    pred = tokenizer.decode(gen, skip_special_tokens = True).strip()
    try:
        CandidateProfile.model_validate(_json.loads(pred))
        ok = True
    except Exception:
        ok = False
    exact = (pred.strip() == sample['output'].strip())
    n_json_ok += int(ok)
    n_exact += int(exact)
    print(f"[{i}] {sample['file']}: json_ok={ok} exact_match={exact} len={len(pred)}")

print(f"\\nJSON hợp lệ: {n_json_ok}/{N_EVAL} | Khớp toàn bộ silver: {n_exact}/{N_EVAL}")
""")

output_nb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'module1_finetune_qwen3_lora.ipynb')
with open(output_nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)
print(f"Created {output_nb_path}")

