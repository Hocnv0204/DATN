import os
import glob
import fitz  # PyMuPDF

# Thư mục chứa PDF và thư mục đích chứa TXT
PDF_DIR = "../dataset/pdf"
TXT_DIR = "../cv-analysis-service/cv_texts"

os.makedirs(TXT_DIR, exist_ok=True)

pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
print(f"Tìm thấy {len(pdf_files)} file PDF.")

success_count = 0
for pdf_path in pdf_files:
    filename = os.path.basename(pdf_path)
    txt_filename = os.path.splitext(filename)[0] + ".txt"
    txt_path = os.path.join(TXT_DIR, txt_filename)
    
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text() + "\\n"
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text.strip())
            
        success_count += 1
        print(f"[OK] Đã trích xuất: {filename} -> {txt_filename}")
    except Exception as e:
        print(f"[LỖI] Không thể trích xuất {filename}: {e}")

print(f"\\nHoàn thành! Đã trích xuất {success_count}/{len(pdf_files)} file.")
print(f"Vui lòng upload thư mục {os.path.abspath(TXT_DIR)} lên Google Drive theo đường dẫn:")
print("/content/drive/MyDrive/cv-analysis-service/cv_texts/")
