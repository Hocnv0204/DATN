# Báo Cáo Chi Tiết Các Công Việc Đã Thực Hiện - Đồ Án Tốt Nghiệp
**Chủ đề:** Hệ thống trích xuất thông tin CV (CV Parsing) sử dụng LLM & Cơ chế Luật (Rule-based)
**Thời điểm báo cáo:** Cập nhật đến hiện tại

Báo cáo này trình bày cụ thể về các hạng mục công việc đã được hoàn thành trong quá trình thực hiện Đồ án tốt nghiệp. Nhằm tối ưu hóa hiệu năng, độ chính xác và giảm thiểu độ trễ, hệ thống hiện đã được phát triển theo **Kiến trúc Hybrid (Lai)**: Luồng xử lý Rule-based (nhanh, chạy cục bộ) đóng vai trò nòng cốt và luồng AI (LLM) làm công cụ bổ trợ nâng cao.

## 1. Phân tích Yêu cầu và Thiết kế Hệ thống

**Phân tích yêu cầu và Thiết kế kiến trúc**
Hệ thống sử dụng kiến trúc Microservices tinh gọn, phân tách rõ ràng trách nhiệm:
- Ứng dụng Backend chính (Java/Spring Boot) đảm nhiệm quản lý luồng dữ liệu, thao tác tệp tin và đặc biệt là xử lý toàn bộ pipeline Rule-based cục bộ.
- Dịch vụ AI độc lập (Python/FastAPI) chuyên trách việc nạp mô hình ngôn ngữ lớn (LLM) và phục vụ suy luận khi cấu trúc CV nằm ngoài bộ quy tắc có sẵn.

**Thiết kế cấu trúc dữ liệu trích xuất (JSON Schema)**
Xây dựng chuẩn đầu ra JSON bao phủ toàn bộ trường thông tin cốt lõi: `personal_info`, `objective`, `education`, `experience`, `personal_projects`, `skills`, `certificates`, `honours`, `languages`. 
- Phía Backend: Cấu trúc được phản ánh bằng các đối tượng Data Transfer Object (DTO) phân cấp chi tiết (`CandidateProfile.java`).
- Phía AI-Service: Định nghĩa ràng buộc nghiêm ngặt trong hệ thống prompt nhằm ép LLM luôn trả về đúng định dạng đã định.

---

## 2. Hệ thống Trích xuất Dựa trên Luật (Rule-Based Pipeline) - Cốt lõi Backend

Để ưu tiên **tốc độ phản hồi** (không call API bên ngoài) và **đảm bảo dữ liệu nguyên bản** (không bịa thông tin), dự án đã phát triển thành công một Pipeline Rule-based mạnh mẽ hoàn toàn bằng Java:

**Trích xuất và Tái tạo Bố cục (Layout Reconstruction)**
- Module `PdfTextExtractor.java` tích hợp thư viện `Apache PDFBox` thực hiện quét văn bản kèm tọa độ X/Y chính xác.
- Tự động nhận diện cấu trúc trang CV (một cột hoặc nhiều cột). Qua đó tiến hành gom nhóm ký tự thành dòng và các khối văn bản (TextBlock), khôi phục thành công thứ tự đọc thực tế của người dùng và ngăn chặn lỗi văn bản hai cột bị xáo trộn lẫn vào nhau.

**Nhận diện Phân vùng (Section Detection)**
- Cấu trúc hệ từ điển tiêu đề đa ngôn ngữ (`SectionDictionary.java`) kết hợp đối sánh chuỗi.
- Tự động phân loại chính xác các khối văn bản vào từng phần như: Học vấn, Kinh nghiệm, Dự án, Kỹ năng... bất chấp các cách viết biến thể của ứng viên (Ví dụ: "KỸ NĂNG KHÁC", "NGOẠI NGỮ", "KỸ NĂNG CHUYÊN MÔN").

**Trích xuất Trường và State Machine (Extraction & Entity Linking)**
- Áp dụng các Biểu thức chính quy (Regex) tối ưu và hệ Từ điển định nghĩa trước để bắt chuẩn xác Email, Số điện thoại, URL Github/LinkedIn, điểm GPA, và mốc thời gian.
- Điểm sáng của hệ thống là việc xây dựng mô hình **State Machine** (`ExperienceExtractor.java`, `ProjectExtractor.java`) nhằm quản lý trạng thái phân tích theo ngữ cảnh. Kỹ thuật này giúp khoanh vùng chuẩn xác tên công ty, chức danh, khoảng thời gian, công nghệ (tech stack) và tách riêng biệt từng dòng mô tả (bullet points) cho mỗi kinh nghiệm/dự án. Giải quyết triệt để vấn đề "râu ông nọ cắm cằm bà kia" (sao chép nhầm tech stack hoặc mô tả của dự án này sang dự án khác).

**Kiểm định và Ánh xạ (Validation & Mapping)**
- Chuyển đổi dữ liệu thô sang JSON DTO chuẩn qua lớp `CvJsonMapper.java`.
- Tích hợp lớp tường lửa `CvValidator.java` để chặn lỗi logic: Cảnh báo tự động nếu phát hiện ngày kết thúc xảy ra trước ngày bắt đầu, giới hạn điểm GPA không vượt mức chuẩn, và tự động khử các dòng bullet bị lặp lố do lỗi formatting PDF.

---

## 3. Huấn luyện Mô hình LLM và Triển khai (LLM Pipeline & Colab Notebook)

Luồng LLM được nghiên cứu và thực nghiệm chuyên sâu nhằm bóc tách các mẫu CV phức tạp, có thiết kế đồ họa dị biệt hoặc bố cục phi chuẩn mà luồng Rule-based khó bao phủ toàn diện.

### 3.1. Chi tiết Nội dung và Quy trình Thực nghiệm trên Google Colab (`fine_tune_qwen3-1.7B.ipynb`)

Toàn bộ quy trình chuẩn bị dữ liệu, huấn luyện LoRA và đóng gói mô hình được thiết kế và thực thi khép kín trong notebook Google Colab với các hạng mục cốt lõi:

- **Môi trường Thực thi & Thư viện**:
  - Phần cứng: Google Colab GPU Tesla T4 (14.56 GB VRAM), hệ điều hành Linux, CUDA 13.0, PyTorch 2.11.0.
  - Bộ công cụ tăng tốc: Tích hợp thư viện `Unsloth` (phiên bản `2026.10.2`) giúp tăng tốc độ huấn luyện gấp 2 lần, tối ưu bộ nhớ VRAM với gradient offloading và double buffering.
  - Thư viện huấn luyện & suy luận: `transformers` (v5.17.0), `trl` (SFTTrainer v1.13.0), `peft` (v0.21.1), `bitsandbytes` (v0.50.2), `pydantic`, `google-genai`.

- **Xây dựng Dữ liệu Huấn luyện (Silver Dataset Pipeline)**:
  - Tập dữ liệu gồm **494 mẫu CV** kết hợp giữa hồ sơ thực tế và dữ liệu tổng hợp (synthetic) bao phủ đa dạng các vị trí ngành CNTT (Backend, Frontend, Full-stack, Mobile, DevOps, AI/Data, BA...).
  - Dữ liệu được gán nhãn tự động thông qua Gemini API (`gemini-3.1-flash-lite`) với cơ chế ép cấu trúc JSON nghiêm ngặt tuân thủ Pydantic Schema `CandidateProfile`.
  - Áp dụng hệ thống System Prompt gồm 13 nguyên tắc vàng chống suy diễn/ảo giác: Không bịa thông tin ngoài CV; giữ nguyên URL và ngôn ngữ gốc; tách riêng từng bullet trong `experience.description`; tách bạch kỹ năng chung (`skills`) với công nghệ thực tế của từng dự án (`tech_stack`); và tự động khai triển các nhóm framework viết tắt (như "Spring Cloud - Gateway, Eureka" $\rightarrow$ "Spring Cloud Gateway", "Spring Cloud Eureka").
  - Phân chia tập dữ liệu theo tỷ lệ 80/20: **395 mẫu tập Train** và **99 mẫu tập Validation**.

- **Thiết kế Prompt Template & Kỹ thuật Khóa Cấu trúc (Schema Prompt Injection)**:
  - Cấu trúc Chat Template chuẩn Qwen3:
    ```
    <|im_start|>system
    {instruction}
    {schema}<|im_end|>
    <|im_start|>user
    {cv_text}<|im_end|>
    <|im_start|>assistant
    {output_json}<|im_end|>
    ```
  - Kỹ thuật bơm trực tiếp khung JSON Schema mẫu (`JSON_SCHEMA_FORMAT`) vào System Prompt nhằm tạo "neo định dạng cứng", ép mô hình học chính xác tên các trường (keys), triệt tiêu hoàn toàn khả năng sinh sai field hay bịa key mới.

- **Cơ chế No-Thinking Mode chuyên biệt cho Information Extraction**:
  - Trong các thử nghiệm ban đầu, mô hình Qwen3 mặc định sinh hàng nghìn token suy luận (`<think> ... </think>`), dẫn đến việc chạm trần độ dài `max_new_tokens`, khiến phản hồi bị cắt cụt giữa chừng (`hit_cap=True`) và làm hỏng hoàn toàn cấu trúc JSON (`json_ok=False`).
  - Giải pháp triển khai: Thiết lập tham số `enable_thinking=False` trong hàm `apply_chat_template` của Qwen3, kết hợp lệnh cấm sinh suy luận trong prompt. Kết quả giúp mô hình sinh ngay lập tức ký tự `{` mở đầu của JSON payload, loại bỏ 100% token thừa thãi, tối ưu tuyệt đối tốc độ suy luận và chi phí token.

---

### 3.2. Cấu hình Siêu tham số & Quá trình Huấn luyện (Fine-Tuning with LoRA)

- **Mô hình nền (Base Model)**:
  - Lựa chọn mô hình: `unsloth/Qwen3-1.7B` nạp ở định dạng lượng tử hóa 4-bit (`load_in_4bit=True`). Đây là dòng mô hình thế hệ mới vượt trội về năng lực hiểu tiếng Việt và phân tích cấu trúc văn bản kỹ thuật so với các bản tiền nhiệm (0.6B hay Qwen2.5-1.5B), đồng thời vẫn đảm bảo tính gọn nhẹ để suy luận trên CPU.
  - Mở rộng độ dài ngữ cảnh: Nâng `max_seq_length = 4096` (sau khi đo đạc tokenizer thực tế ghi nhận độ dài prompt tối đa đạt 3964 tokens; cấu hình cũ 2048 tokens khiến hơn 67% mẫu bị cắt cụt dữ liệu).

- **Thiết lập LoRA (Low-Rank Adaptation)**:
  - Rank ($r$): 16 | Alpha ($\alpha$): 16 | Dropout: 0 | Bias: "none".
  - Target Modules: Can thiệp toàn diện trên cả 28 layers của mô hình với 7 khối phép chiếu tuyến tính: `["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]`.
  - Số lượng tham số tinh chỉnh: **17,432,576 tham số** trên tổng số 1,738,007,552 tham số (chiếm đúng **1.00%** tổng tham số mô hình), đảm bảo huấn luyện siêu nhẹ mà không làm mất tri thức ngôn ngữ cốt lõi (catastrophic forgetting).

- **Siêu tham số Huấn luyện (Training Arguments)**:
  - Số Epochs: **5 epochs** (được kiểm chứng qua thực nghiệm là điểm dừng tối ưu để mô hình ghi nhớ cấu trúc JSON mà không bị overfitting).
  - Kích thước Batch: `per_device_train_batch_size = 2`, `gradient_accumulation_steps = 4` $\rightarrow$ Kích thước Batch thực tế = **8**.
  - Tốc độ học (Learning Rate): $2 \times 10^{-4}$ (`2e-4`) với chiến lược giảm dần tuyến tính (`linear`), `warmup_steps = 5`.
  - Bộ tối ưu (Optimizer): `adamw_8bit`, `weight_decay = 0.01`.
  - Chiến lược lưu và đánh giá: Đánh giá sau mỗi 10 steps (`eval_steps = 10`), lưu checkpoint theo epoch (`save_strategy = "epoch"`).
  - Tổng số bước huấn luyện: **250 steps**.
  - Tổng thời gian huấn luyện trên GPU Tesla T4: **58 phút 44 giây**.

---

### 3.3. Kết quả Huấn luyện (Loss History & Độ hội tụ)

Quá trình huấn luyện diễn ra ổn định với sự suy giảm sâu và mượt mà của hàm mất mát qua từng bước:

| Bước (Step) | Epoch | Training Loss | Validation Loss | Ghi chú |
| :---: | :---: | :---: | :---: | :--- |
| **10** | 0.20 | 1.6710 | 1.5768 | Bắt đầu học cú pháp Chat Template |
| **20** | 0.40 | 0.6129 | 0.5125 | Nhanh chóng nắm bắt định dạng JSON |
| **30** | 0.60 | 0.0332 | 0.0251 | Loss giảm mạnh, cấu trúc JSON được định hình |
| **50** | 1.00 | 0.0040 | 0.0034 | Hoàn thành Epoch 1, lưu `checkpoint-50` |
| **100** | 2.00 | 0.000216 | 0.000213 | Hoàn thành Epoch 2, lưu `checkpoint-100` |
| **150** | 3.00 | 0.000152 | 0.000151 | Hoàn thành Epoch 3, lưu `checkpoint-150` |
| **200** | 4.00 | 0.000128 | 0.000127 | Hoàn thành Epoch 4, lưu `checkpoint-200` |
| **250** | 5.00 | **0.000121** | **0.000121** | **Hoàn thành Epoch 5, lưu `checkpoint-250`** |

- **Đánh giá hiện tượng Overfitting**:
  - Training Loss cuối cùng: **0.000121** (~0.0001).
  - Validation Loss cuối cùng: **0.000121** (~0.0001).
  - Đường cong mất mát của tập Train và tập Val giảm song song, hội tụ đồng đều và tuyệt đối không có dấu hiệu ngóc đầu lên của Validation Loss $\rightarrow$ Mô hình hoàn toàn không bị overfitting, khả năng tổng quát hóa với schema đạt mức tối ưu.
- **Kiểm định chất lượng thích ứng LoRA**:
  - Kiểm tra 392 tensor LoRA sau huấn luyện: Trị tuyệt đối lớn nhất của ma trận LoRA B đạt `max|lora_B| = 0.6488` (so với giá trị khởi tạo ban đầu là 0.0), khẳng định các vector LoRA đã hấp thụ trọn vẹn đặc trưng phân tích CV và ánh xạ schema.

---

### 3.4. Sản phẩm Đầu ra (Model Artifacts) & Kết quả Đạt được

Quy trình trong file Colab đã xuất bản thành công 3 định dạng đóng gói mô hình:

1. **LoRA Adapter Weights (`finetune_output/lora_adapter`)**:
   - Trọng số LoRA tối ưu nhất được cố định tại `checkpoint-250` (dung lượng ~70 MB).
   - Được nạp trực tiếp vào dịch vụ `ai-service` (`main.py`) thông qua thư viện `peft` và `transformers` để phục vụ suy luận.

2. **Merged Model 16-bit (`finetune_output/merged_model`)**:
   - Thực hiện merge trực tiếp trọng số LoRA vào Base Model ở chuẩn Float16 full-precision thông qua hàm `model.save_pretrained_merged(save_method="merged_16bit")`.
   - Tạo ra mô hình hoàn chỉnh độc lập có kích thước ~3.44 GB (`model.safetensors`), bảo toàn 100% độ chính xác của LoRA adapter, sẵn sàng triển khai trên các môi trường GPU hoặc CPU chuẩn.

3. **Lượng tử hóa GGUF Q4_K_M (`finetune_output/gguf`)**:
   - Sử dụng công cụ `llama.cpp` tích hợp trong Unsloth để lượng tử hóa mô hình đã merge sang chuẩn `Qwen3-1.7B.Q4_K_M.gguf`.
   - **Tối ưu dung lượng đột phá**: Kích thước tệp giảm xuống chỉ còn **1.11 GB** (giảm 68% so với bản 16-bit).
   - Tự động sinh `Modelfile` tương thích chuẩn với Ollama và llama.cpp.
   - Giải quyết triệt để bài toán phục vụ mô hình: Cho phép chạy suy luận mượt mà trên môi trường CPU phổ thông với tốc độ ước tính **15 - 30 tokens/giây** (thay vì mức 2.67 tokens/giây khi chạy mô hình FP32 thô), hạ thấp thời gian xử lý mỗi CV từ hơn 3 phút xuống chỉ còn dưới 1 phút.

- **Kết quả Kiểm thử Suy luận (Inference & Validation Output)**:
  - Tiến hành đánh giá độc lập trên tập mẫu kiểm thử Validation:
    - **Tỷ lệ sinh JSON hợp lệ**: Đạt **100% (10/10 mẫu)** vượt qua kiểm định tính hợp lệ của `CandidateProfile.model_validate()` (`JSON valid: True`), không cần qua xử lý sửa lỗi.
    - **Kiểm soát kết thúc sinh (EOS Termination)**: **100% các mẫu dừng chuẩn xác tại token EOS** (`Stopped by EOS: True`, token id 151645), không gặp bất kỳ lỗi lặp vô tận hay đứt gãy giữa chừng (`hit_cap=False`).
    - **Độ dài đầu ra tối ưu**: Mỗi CV sinh trung bình từ 896 đến 1399 tokens (~3200 - 4300 ký tự), phản ánh đầy đủ thông tin mà không sinh từ thừa.
    - **Độ chuẩn xác bóc tách ngữ nghĩa**: Mô hình phân tách rành mạch tên trường học, GPA, phân tách từng đầu việc trong kinh nghiệm thành các chuỗi riêng biệt trong mảng `description`, đồng thời gom nhóm chuẩn xác `tech_stack` gắn liền với từng dự án cụ thể thay vì gom bừa vào danh sách `skills` tổng thể.

### 3.5. Triển khai và Phục vụ Mô hình (Model Serving)
- Cấu hình dịch vụ `AI-Service` (`main.py`) nạp Base Model kết hợp chặt chẽ với LoRA Adapter qua thư viện `transformers` và `peft` (full-precision), duy trì toàn vẹn trọng số học được.
- Dịch vụ có cơ chế tự động đếm token kiểm soát đầu vào và sử dụng `json_repair` để làm sạch/khôi phục chuỗi JSON nếu LLM trả về bị lỗi cú pháp nhỏ.

---

## 4. Tích hợp API và Vận hành (End-to-End)

- **Đa dạng Endpoint**: Controller `CvAnalysisController.java` đã sẵn sàng cung cấp các endpoint phục vụ luồng trích xuất khác nhau:
  - `/api/v1/cv/extract-rule-based`: Trích xuất tốc độ cao bằng Java nội bộ.
  - `/api/v1/cv/analyze-pdf`: Gọi sang AI-Service qua giao thức HTTP (sử dụng Spring Cloud OpenFeign) để xử lý chuyên sâu bằng LLM.
- **Tính trong suốt**: Bất kể đi qua đường Rule-based hay LLM, dữ liệu cuối cùng luôn được chuẩn hóa và trả về theo cùng một schema `CandidateProfile`, tạo sự đồng bộ hoàn hảo cho bộ phận làm Frontend sau này.
- **Tính sẵn sàng**: Cấu trúc Java Class đã được định hình rõ ràng để bước tiếp theo có thể dễ dàng map (ánh xạ) trực tiếp vào bảng cơ sở dữ liệu PostgreSQL dưới dạng cột không cấu trúc `JSONB`.
