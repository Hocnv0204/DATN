# AI Service - CV Information Extraction

Dịch vụ trích xuất thông tin CV (CV Parsing) ứng dụng Mô hình Ngôn ngữ Lớn (**Qwen3-1.7B**) đã được tinh chỉnh (Fine-tuned) với kỹ thuật LoRA và tối ưu lượng tử hóa **GGUF Q4_K_M**.

---

## 📌 Tài liệu Kỹ thuật Chi tiết
Vui lòng tham khảo tài liệu kỹ thuật đầy đủ tại:  
👉 **[AI_SERVICE_GUIDE.md](../AI_SERVICE_GUIDE.md)**

Nội dung tài liệu bao gồm:
1. **Tổng quan Kiến trúc:** Tương tác giữa Spring Boot Backend và FastAPI AI Service.
2. **Mô hình Ngôn ngữ Lớn:** Đặc tả kiến trúc Qwen3-1.7B (1.74B params, 28 layers, Context 4096 tokens).
3. **Luồng chạy chi tiết:** Quy trình từ tiếp nhận request, tiền xử lý (`clean_cv_text`), Prompt Chat Template Qwen3 với "No-thinking mode", cơ chế suy luận kép (`llama.cpp` / `transformers`) đến hậu xử lý làm sạch JSON (`extract_json` + `json_repair`).
4. **Quy trình Fine-tuning:** 
   - Xây dựng Silver Dataset gồm 494 mẫu qua Gemini API (`gemini-3.1-flash-lite`).
   - Huấn luyện LoRA (r=16, alpha=16, 17.43M params) với Unsloth trên GPU Tesla T4 (5 epochs, 250 steps, Loss hội tụ 0.000121, không overfitting).
   - Đóng gói Merged 16-bit và GGUF Q4_K_M (1.11 GB).
5. **Hướng dẫn Cài đặt & Vận hành:** Cấu hình biến môi trường, cài đặt thư viện và kiểm thử API.

---

## 🚀 Khởi Chạy Nhanh

```bash
# 1. Tạo môi trường ảo
python3 -m venv .venv
source .venv/bin/activate

# 2. Cài đặt thư viện
pip install -r requirements.txt

# 3. Chạy service
python3 main.py
# Hoặc: uvicorn main:app --host 0.0.0.0 --port 8000
```
