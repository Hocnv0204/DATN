#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_dataset_ocr.py
======================
Giai đoạn 1 - Khai thác dataset có sẵn để sinh ra văn bản CV (text thô).

Nguồn dữ liệu:
  * dataset/pdf/  -> 56 file PDF (trích xuất text bằng PyMuPDF; trang scan -> OCR)
  * dataset/img/  -> 30 file ảnh (OCR bằng Tesseract)

Đầu ra:
  * cv-analysis-service/cv_texts/real_pdf_01.txt ... real_pdf_56.txt
  * cv-analysis-service/cv_texts/real_img_01.txt ... real_img_30.txt
  * fine-tune/_stage/extracted.json   (bản thô + metadata, dùng cho bước gán nhãn)

Nguyên tắc làm sạch (giữ nguyên bố cục thật của CV):
  - Giữ nguyên thứ tự dòng, không sắp xếp lại các section.
  - Chỉ: bỏ ký tự điều khiển, gộp khoảng trắng cuối dòng, chuẩn hoá
    khoảng trắng "3+ dòng trống" về tối đa 1 dòng trống, bỏ form feed.

Cách chạy:
  python3 process_dataset_ocr.py
  python3 process_dataset_ocr.py --force      # ghi đè kết quả đã có
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import random
import re
import shutil
import sys
import unicodedata

# ----------------------------------------------------------------------------- paths
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PDF_DIR = ROOT / "dataset" / "pdf"
IMG_DIR = ROOT / "dataset" / "img"
OUT_DIR = ROOT / "cv-analysis-service" / "cv_texts"
STAGE_DIR = HERE / "_stage"
STAGE_JSON = STAGE_DIR / "extracted.json"

# Ngưỡng: trang PDF coi như "scan" (không có text layer) nếu số ký tự < ngưỡng
MIN_CHARS_DIRECT = 100
MIN_CHARS_OCR = 80          # dưới ngưỡng này coi như OCR thất bại
MIN_CHARS_KEEP = 150        # dưới ngưỡng này bỏ file (không đủ nội dung để train)

OCR_LANGS = "vie+eng"
OCR_DPI_SCALE = 3.0         # zoom khi render trang PDF scan -> ảnh
OCR_MIN_WIDTH = 1400        # ảnh hẹp sẽ được upscale để OCR chính xác hơn

random.seed(20240517)


# ----------------------------------------------------------------------------- tesseract
def _setup_tesseract() -> str | None:
    """Trỏ pytesseract tới binary tesseract. Trả về đường dẫn hoặc None nếu không có."""
    try:
        import pytesseract
    except ImportError:
        print("[LỖI] Chưa cài pytesseract: pip install pytesseract")
        return None

    candidates = [
        os.environ.get("TESSERACT_CMD"),
        str(pathlib.Path.home() / ".local/bin/tesseract"),
        shutil.which("tesseract"),
    ]
    for cand in candidates:
        if not cand:
            continue
        exe = cand
        if cand == str(pathlib.Path.home() / ".local/bin/tesseract"):
            # bản cài user-local cần wrapper để set LD_LIBRARY_PATH/TESSDATA_PREFIX
            wrapper = pathlib.Path(cand).parent / "tesseract-wrap"
            exe = str(wrapper) if wrapper.exists() else cand
        if pathlib.Path(exe).exists():
            pytesseract.pytesseract.tesseract_cmd = exe
            try:
                langs = pytesseract.get_languages(config="")
            except Exception:
                langs = []
            if langs:
                print(f"[OCR] Tesseract sẵn sàng: {exe} (langs: {', '.join(sorted(langs))})")
            else:
                print(f"[OCR] Tesseract: {exe} (không đọc được danh sách ngôn ngữ)")
            return exe

    print("[CẢNH BÁO] Không tìm thấy tesseract - các trang scan/ảnh sẽ bị bỏ qua.")
    return None


_TESSERACT = None


def ocr_image(img) -> str:
    """OCR một ảnh PIL, có tiền xử lý nhẹ (grayscale + upscale + tăng tương phản)."""
    import pytesseract

    if img.mode != "L":
        img = img.convert("L")
    # ảnh CV chụp từ màn hình/mobile thường nhỏ -> upscale để Tesseract bám chữ tốt hơn
    if img.width < OCR_MIN_WIDTH:
        scale = min(3.0, max(1.5, OCR_MIN_WIDTH / max(1, img.width)))
        img = img.resize((int(img.width * scale), int(img.height * scale)), 3)  # 3 = LANCZOS

    text = pytesseract.image_to_string(img, lang=OCR_LANGS)
    # thử lần 2 với psm 6 (uniform block) nếu lần 1 quá ngắn
    if len(text.strip()) < MIN_CHARS_OCR:
        text2 = pytesseract.image_to_string(img, lang=OCR_LANGS, config="--psm 6")
        if len(text2.strip()) > len(text.strip()):
            text = text2
    return text


# ----------------------------------------------------------------------------- cleaning
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_TRAIL_WS_RE = re.compile(r"[ \t ]+$", re.MULTILINE)
_MULTI_BLANK_RE = re.compile(r"\n{3,}")
_MULTI_SPACE_RE = re.compile(r"[ \t]{3,}")


def clean_text(text: str) -> str:
    """Làm sạch nhẹ, giữ nguyên bố cục/multi-column của bản thật."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("", "•").replace("", "-").replace("", "+")
    text = text.replace("–—", "-")  # gộp 2 ký tự nối bị lệch
    text = _CTRL_RE.sub("", text)
    text = unicodedata.normalize("NFC", text)
    lines = [_TRAIL_WS_RE.sub("", ln).rstrip() for ln in text.split("\n")]
    text = "\n".join(lines)
    text = _MULTI_SPACE_RE.sub("  ", text)
    text = _MULTI_BLANK_RE.sub("\n\n", text)
    return text.strip()


# ----------------------------------------------------------------------------- PDF
def process_pdf(pdf_path: pathlib.Path) -> dict:
    """Trích text từ PDF; trang nào không có text layer sẽ render sang ảnh rồi OCR."""
    import pymupdf

    chunks: list[str] = []
    n_pages = 0
    n_ocr_pages = 0
    n_errors = 0

    with pymupdf.open(pdf_path) as doc:
        n_pages = len(doc)
        for page in doc:
            direct = page.get_text().strip()
            if len(direct) >= MIN_CHARS_DIRECT or not _TESSERACT:
                chunks.append(direct)
                continue

            # --- trang scan: render -> OCR
            n_ocr_pages += 1
            try:
                pix = page.get_pixmap(matrix=pymupdf.Matrix(OCR_DPI_SCALE, OCR_DPI_SCALE))
                img = None
                try:
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    chunks.append(ocr_image(img))
                finally:
                    if img is not None:
                        img.close()
                    pix = None
            except Exception as exc:  # pragma: no cover
                n_errors += 1
                print(f"    ! OCR trang lỗi: {exc}")

    raw = "\n".join(chunks)
    return {
        "raw": raw,
        "n_pages": n_pages,
        "n_ocr_pages": n_ocr_pages,
        "n_errors": n_errors,
        "method": "pdf_text+ocr" if n_ocr_pages else "pdf_text",
    }


# ----------------------------------------------------------------------------- IMG
def process_image(img_path: pathlib.Path) -> dict:
    from PIL import Image

    with Image.open(img_path) as im:
        im.load()
        if _TESSERACT:
            text = ocr_image(im)
        else:
            text = ""
    return {
        "raw": text,
        "n_pages": 1,
        "n_ocr_pages": 1 if _TESSERACT else 0,
        "n_errors": 0,
        "method": "img_ocr" if _TESSERACT else "img_skipped",
        "image_size": list(Image.open(img_path).size),
    }


# ----------------------------------------------------------------------------- main
def main() -> int:
    global _TESSERACT

    ap = argparse.ArgumentParser(description="Trích xuất text từ PDF/IMG dataset -> cv_texts")
    ap.add_argument("--force", action="store_true", help="ghi đè các file đã tồn tại")
    ap.add_argument("--skip-existing", action="store_true", help="bỏ qua file .txt đã có")
    args = ap.parse_args()

    if not PDF_DIR.exists() and not IMG_DIR.exists():
        print(f"[LỖI] Không tìm thấy dataset tại {PDF_DIR.parent}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    _TESSERACT = _setup_tesseract()

    records: list[dict] = []
    stats = {"pdf_direct": 0, "pdf_ocr": 0, "img": 0, "dropped": 0}

    # ---- PDF ----
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    print(f"\n=== PDF: {len(pdf_files)} file ===")
    for i, pdf in enumerate(pdf_files, 1):
        out_name = f"real_pdf_{i:02d}.txt"
        out_path = OUT_DIR / out_name

        if out_path.exists() and not args.force:
            print(f"[{i:2}/{len(pdf_files)}] skip (đã có) {out_name}")
            continue

        try:
            info = process_pdf(pdf)
        except Exception as exc:
            print(f"[{i:2}/{len(pdf_files)}] [LỖI] {pdf.name}: {exc}")
            stats["dropped"] += 1
            continue

        text = clean_text(info.pop("raw"))
        if len(text) < MIN_CHARS_KEEP:
            print(f"[{i:2}/{len(pdf_files)}] [BỎ] {pdf.name}: quá ngắn ({len(text)} ký tự)")
            stats["dropped"] += 1
            continue

        out_path.write_text(text, encoding="utf-8")
        tag = "OCR" if info["n_ocr_pages"] else "TEXT"
        if info["n_ocr_pages"]:
            stats["pdf_ocr"] += 1
        else:
            stats["pdf_direct"] += 1
        records.append(
            {
                "file": out_name,
                "source": str(pdf.relative_to(ROOT)),
                "kind": "pdf",
                "chars": len(text),
                **info,
            }
        )
        print(f"[{i:2}/{len(pdf_files)}] [{tag}] {pdf.name} -> {out_name} ({len(text)} ký tự, {info['n_pages']} trang)")

    # ---- IMG ----
    img_files = sorted(
        p for p in IMG_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
    )
    print(f"\n=== IMG: {len(img_files)} file ===")
    if not _TESSERACT:
        print("[CẢNH BÁO] Bỏ qua toàn bộ ảnh vì không có Tesseract.")

    for i, img in enumerate(img_files, 1):
        out_name = f"real_img_{i:02d}.txt"
        out_path = OUT_DIR / out_name

        if out_path.exists() and not args.force:
            print(f"[{i:2}/{len(img_files)}] skip (đã có) {out_name}")
            continue

        if not _TESSERACT:
            break

        try:
            info = process_image(img)
        except Exception as exc:
            print(f"[{i:2}/{len(img_files)}] [LỖI] {img.name}: {exc}")
            stats["dropped"] += 1
            continue

        text = clean_text(info.pop("raw"))
        if len(text) < MIN_CHARS_KEEP:
            print(f"[{i:2}/{len(img_files)}] [BỎ] {img.name}: quá ngắn ({len(text)} ký tự)")
            stats["dropped"] += 1
            continue

        out_path.write_text(text, encoding="utf-8")
        stats["img"] += 1
        records.append(
            {
                "file": out_name,
                "source": str(img.relative_to(ROOT)),
                "kind": "img",
                "chars": len(text),
                **info,
            }
        )
        print(f"[{i:2}/{len(img_files)}] [OCR] {img.name[:38]:38s} -> {out_name} ({len(text)} ký tự)")

    # ---- lưu stage ----
    STAGE_JSON.write_text(
        json.dumps({"records": records, "stats": stats}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n=== Tổng kết giai đoạn 1 ===")
    print(f"  PDF trích text trực tiếp : {stats['pdf_direct']}")
    print(f"  PDF cần OCR               : {stats['pdf_ocr']}")
    print(f"  Ảnh OCR                   : {stats['img']}")
    print(f"  Bị loại                   : {stats['dropped']}")
    print(f"  Tổng file .txt tạo ra     : {len(records)}")
    print(f"  Stage                     : {STAGE_JSON}")

    total_txt = len(list(OUT_DIR.glob("*.txt")))
    print(f"  Hiện có trong {OUT_DIR.name}/: {total_txt} file .txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
