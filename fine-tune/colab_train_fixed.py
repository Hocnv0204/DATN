# ============================================================
# CELL 8 (SỬA) - Load model Qwen3-1.7B qua Unsloth
# Thay đổi so với bản cũ:
#   - base Qwen2.5-1.5B / Qwen3-0.6B -> Qwen3-1.7B (đời mới, tiếng Việt tốt hơn,
#     vẫn train vừa T4 free-tier và serve được trên CPU)
#   - max_seq_length 2048 -> 4096 (đo bằng tokenizer thật: tổng prompt max 3964
#     token; để 2048 thì 67% mẫu bị cắt cụt khi train)
# ============================================================
from unsloth import FastLanguageModel
import torch

model_name = "unsloth/Qwen3-1.7B"
max_seq_length = 4096
dtype = None  # Tự động phát hiện
load_in_4bit = True

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_name,
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit,
)

# ============================================================
# CELL 9 (GIỮ NGUYÊN) - Gắn LoRA adapter
# ============================================================
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
    use_rslora=False,
    loftq_config=None,
)

# ============================================================
# CELL 11 (SỬA) - Cấu hình SFTTrainer và Train
# Thay đổi so với bản cũ:
#   - num_train_epochs 3 -> 5 (bản Qwen2.5 train 5 epochs cho eval_loss 0.37,
#     không overfit; 3 epochs là chưa đủ với ~400 mẫu)
#   - thêm save_strategy="epoch" (bản cũ không chỉ định -> mặc định save theo
#     steps=500, chạy 250 steps sẽ KHÔNG lưu checkpoint nào giữa chừng)
# ============================================================
from trl import SFTTrainer
from transformers import TrainingArguments

output_model_dir = os.path.join(OUTPUT_DIR, 'lora_adapter')

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        num_train_epochs=5,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        eval_strategy="steps",
        eval_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        output_dir=output_model_dir,
        report_to="none"
    ),
)

trainer_stats = trainer.train()

print("\n--- ĐÁNH GIÁ KẾT QUẢ HUẤN LUYỆN ---")
history = trainer.state.log_history
train_losses = [log['loss'] for log in history if 'loss' in log]
eval_losses = [log['eval_loss'] for log in history if 'eval_loss' in log]

if train_losses:
    print(f"Train Loss cuối cùng: {train_losses[-1]:.4f}")
if eval_losses:
    print(f"Eval Loss cuối cùng: {eval_losses[-1]:.4f}")
    min_eval_loss = min(eval_losses)
    if eval_losses[-1] > min_eval_loss * 1.1:
        print("CẢNH BÁO: Có dấu hiệu Overfitting (Eval loss tăng trở lại).")

# ============================================================
# CELL 12 (SỬA) - Lưu adapter + merge + GGUF (để serve nhanh)
# Bản cũ chỉ lưu adapter -> về local phải chạy transformers fp32 trên CPU
# (2.67 tok/s, 210s/CV). Thêm 2 dòng dưới để có file GGUF Q4 chạy bằng
# llama.cpp (~15-30 tok/s, ~1 phút/CV).
# ============================================================
# 1. Adapter (để train tiếp / kiểm tra)
model.save_pretrained(output_model_dir)
tokenizer.save_pretrained(output_model_dir)
print(f"Đã lưu adapter vào: {output_model_dir}")

# 2. Merge full precision (KHÔNG merge trên base 4bit - sẽ làm mất tác dụng LoRA)
# LƯU Ý: truyền đường dẫn dạng positional, KHÔNG dùng keyword (Unsloth đổi tên
# tham số giữa các bản: save_directory / save_path / save_pretrained_directory
# -> dùng keyword sẽ TypeError tùy bản đang cài).
MERGED_DIR = os.path.join(OUTPUT_DIR, "merged_model")
model.save_pretrained_merged(
    MERGED_DIR,
    tokenizer,
    save_method="merged_16bit",
)
print(f"Đã lưu merged model vào: {MERGED_DIR}")

# 3. GGUF Q4_K_M (file duy nhất cần tải về local để serve)
GGUF_DIR = os.path.join(OUTPUT_DIR, "gguf")
model.save_pretrained_gguf(
    GGUF_DIR,
    tokenizer,
    quantization_method="q4_k_m",
)
print(f"Đã lưu GGUF vào: {GGUF_DIR}")
print("Tải file .gguf về máy, đặt vào ai-service/merged_model/ rồi restart service.")

# ============================================================
# CELL 13 (SỬA) - Đánh giá trên 10 mẫu validation
# Thay đổi so với bản cũ:
#   - max_new_tokens 1024 -> 2048 (output dài nhất 1726 token; để 1024 thì
#     49.6% mẫu bị cụt giữa JSON -> JSON parse fail hàng loạt)
#   - đo trên 10 mẫu thay vì 1 mẫu (val_records[0] không có ý nghĩa thống kê)
# ============================================================
import json as _json

FastLanguageModel.for_inference(model)

N_EVAL = min(10, len(val_records))
n_json_ok = 0
n_exact = 0
for i in range(N_EVAL):
    sample = val_records[i]
    prompt = (f"<|im_start|>system\n{sample['instruction']}<|im_end|>\n"
              f"<|im_start|>user\n{sample['input']}<|im_end|>\n"
              f"<|im_start|>assistant\n")
    inputs = tokenizer([prompt], return_tensors="pt").to("cuda")
    out = model.generate(**inputs, max_new_tokens=2048,
                         do_sample=False, use_cache=True)
    gen = out[0][inputs.input_ids.shape[1]:]
    pred = tokenizer.decode(gen, skip_special_tokens=True).strip()
    try:
        CandidateProfile.model_validate(_json.loads(pred))
        ok = True
    except Exception:
        ok = False
    exact = (pred.strip() == sample['output'].strip())
    n_json_ok += int(ok)
    n_exact += int(exact)
    print(f"[{i}] {sample['file']}: json_ok={ok} exact_match={exact} len={len(pred)}")

print(f"\nJSON hợp lệ: {n_json_ok}/{N_EVAL} | Khớp toàn bộ silver: {n_exact}/{N_EVAL}")
