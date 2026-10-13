#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_system_prompt.py
=====================
Đồng bộ SYSTEM_PROMPT.txt (bản chuẩn) vào mọi nơi sử dụng prompt:
  - fine-tune/assemble_silver_dataset.py  (SYSTEM_PROMPT = \"\"\"...\"\"\")
  - fine-tune/generate_silver_labels.py   (SYSTEM_PROMPT = \"\"\"...\"\"\")
  - ai-service/main.py                    (instruction = (...) + bỏ dòng phụ)
  - fine-tune/module1_finetune_qwen3_lora.ipynb (cell SYSTEM_PROMPT)

Lý do: train - serve - sinh nhãn phải dùng ĐÚNG MỘT prompt. Lệch nhau là lệch
phân phối, model suy giảm không rõ nguyên nhân.

Cách chạy:
    venv/bin/python sync_system_prompt.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = HERE / "SYSTEM_PROMPT.txt"


def replace_triple_quoted_block(src: str, var: str, new_body: str) -> str:
    """Thay nội dung trong VAR = \"\"\"...\"\"\" bằng new_body."""
    pat = re.compile(
        rf"({re.escape(var)}\s*=\s*\"\"\")[\s\S]*?(\"\"\")",
    )
    new_src, n = pat.subn(lambda m: m.group(1) + "\n" + new_body + "\n" + m.group(2), src, count=1)
    if n == 0:
        raise ValueError(f"Không tìm thấy khối {var} = \"\"\"...\"\"\"")
    return new_src


def main() -> int:
    new_prompt = SRC.read_text(encoding="utf-8").strip() + "\n"
    changed = []

    # ---- 1 & 2. hai script fine-tune ----
    for name in ("assemble_silver_dataset.py", "generate_silver_labels.py"):
        p = HERE / name
        src = p.read_text(encoding="utf-8")
        p.write_text(replace_triple_quoted_block(src, "SYSTEM_PROMPT", new_prompt), encoding="utf-8")
        changed.append(name)

    # ---- 3. ai-service/main.py (nhúng literal để service standalone) ----
    mp = ROOT / "ai-service" / "main.py"
    msrc = mp.read_text(encoding="utf-8")
    pat = re.compile(r"    instruction = \(\n(?:.*\n)*?    \)\n", re.MULTILINE)
    literal = '"""' + "\n" + new_prompt + '"""'
    new_block = "    instruction = " + literal + "\n"
    msrc2, n = pat.subn(new_block, msrc, count=1)
    if n == 0:
        raise ValueError("Không tìm thấy khối instruction = (...) trong main.py")
    # bỏ dòng phụ đã thêm trước đây (giờ trùng với rule 13 của prompt mới)
    msrc2 = msrc2.replace(
        '    system_prompt = instruction + (f"\\n{JSON_SCHEMA_FORMAT}" if INCLUDE_SCHEMA_IN_PROMPT else "")',
        '    system_prompt = instruction.rstrip() + ("\\n" + JSON_SCHEMA_FORMAT if INCLUDE_SCHEMA_IN_PROMPT else "")',
    )
    mp.write_text(msrc2, encoding="utf-8")
    changed.append("ai-service/main.py")

    # ---- 4. notebook ----
    nbp = HERE / "module1_finetune_qwen3_lora.ipynb"
    nb = json.loads(nbp.read_text(encoding="utf-8"))
    n_cells = 0
    for cell in nb["cells"]:
        src_joined = "".join(cell.get("source", []))
        if "SYSTEM_PROMPT" in src_joined and "Bạn là hệ thống trích xuất" in src_joined:
            cell["source"] = ['SYSTEM_PROMPT = """\n'] + [
                line + "\n" for line in new_prompt.rstrip("\n").split("\n")
            ] + ['"""\n']
            n_cells += 1
    if n_cells == 0:
        raise ValueError("Không tìm thấy cell SYSTEM_PROMPT trong notebook")
    nbp.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    changed.append(f"notebook ({n_cells} cell)")

    print("Đã đồng bộ prompt mới vào:")
    for c in changed:
        print("  -", c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
