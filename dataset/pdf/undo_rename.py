#!/usr/bin/env python3
"""
Script khôi phục lại tên file gốc từ mapping.csv
Chạy lệnh: python3 undo_rename.py
"""

import csv
import pathlib

def restore():
    dir_path = pathlib.Path(__file__).parent.resolve()
    csv_path = dir_path / "mapping.csv"

    if not csv_path.exists():
        print("Lỗi: Không tìm thấy file mapping.csv!")
        return

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        mapping = list(reader)

    # Đổi sang tên tạm trước để tránh xung đột
    for item in mapping:
        curr_path = dir_path / item["new_name"]
        tmp_path = dir_path / f"__tmp_restore_{item['stt']}__.pdf"
        if curr_path.exists():
            curr_path.rename(tmp_path)
        else:
            print(f"Cảnh báo: Không tìm thấy {item['new_name']}")

    # Đổi về tên cũ ban đầu
    restored_count = 0
    for item in mapping:
        tmp_path = dir_path / f"__tmp_restore_{item['stt']}__.pdf"
        old_path = dir_path / item["old_name"]
        if tmp_path.exists():
            tmp_path.rename(old_path)
            restored_count += 1

    print(f"Đã khôi phục thành công {restored_count}/{len(mapping)} files về tên cũ!")

if __name__ == "__main__":
    restore()
