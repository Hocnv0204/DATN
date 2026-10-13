#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dataset_audit.py — Pass 1: kiểm định toàn bộ silver_dataset.jsonl.

Kiểm tra từng bản ghi:
  1. JSONL đọc được, output parse được.
  2. Schema CandidateProfile (Pydantic strict).
  3. Sentinel bị cấm ở scalar: "", "null", "N/A", "Unknown" (rule 2).
  4. Kiểu sai: objective phải str|null (bắt lỗi list-bị-stringify),
     team_size/start_year/end_year phải int|null, description(exp) phải list.
  5. Grounding từng trường so với input: literal / normalized / UNGROUNDED.
  6. Trùng lặp: item trùng trong mảng, bullet trùng trong entity,
     cùng mô tả xuất hiện ở nhiều entity khác nhau trong một bản ghi.
  7. input khớp file .txt nguồn (toàn vẹn dữ liệu).
  8. instruction đồng nhất toàn dataset.

Kiểm tra cấp dataset:
  9. input gần trùng (Jaccard shingles) — nghi trùng CV.
  10. cụm description lặp qua nhiều bản ghi — nghi template misuse.

Xuất: fine-tune/_stage/full_audit.json (chi tiết từng bản ghi + toàn cục).
KHÔNG sửa gì ở pass này — sửa ở pass 2 sau khi review tay.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
JSONL = ROOT / "cv-analysis-service" / "finetune_output" / "silver_dataset.jsonl"
TXT_DIR = ROOT / "cv-analysis-service" / "cv_texts"
OUT = ROOT / "fine-tune" / "_stage" / "full_audit.json"

sys.path.insert(0, str(ROOT / "fine-tune"))
from assemble_silver_dataset import CandidateProfile  # noqa: E402
from pydantic import ValidationError  # noqa: E402

MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "jun": "06", "jul": "07", "aug": "08", "sep": "09", "sept": "09",
    "oct": "10", "nov": "11", "dec": "12",
}
FORBIDDEN_SCALARS = {"null", "n/a", "unknown", "none", "nil", "-"}
FORBIDDEN_EXACT = {"", "null", "n/a", "unknown"}


BULLETS = r"\*\•\◦\‣\⁃\▪\▫\◾\◽\￮\❖\➢\➤\-\>~=`\|"


def norm_text(t: str) -> str:
    """Chuẩn hóa văn bản để so khớp grounding:
    - thường hóa, tháng chữ -> số, bỏ số 0 đầu
    - xóa marker đầu dòng (*, •, -, +, >, #, ~, =, số thứ tự '1.', ...)
    - xóa mọi dấu phân tách còn lại (kể cả khoảng trắng) để so chuỗi liền
    Áp dụng NHƯ NHAU cho input và label nên không che giấu lỗi thật.
    """
    t = str(t).lower()
    # chuẩn hóa dấu nháy unicode về ascii trước khi strip
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    # xóa marker đầu dòng: bullets và số thứ tự
    t = re.sub(rf"(?m)^\s*(?:[{BULLETS}]+|\d+[.)])\s*", "", t)
    for n, v in MONTHS.items():
        t = re.sub(rf"\b{n}\b", v, t)
    t = re.sub(r"\b0(\d)", r"\1", t)
    t = re.sub(r"[\s._\-/:;!?,\"'()\[\]]+", "", t)
    # LƯU Ý: giữ '+' và '#' vì có nghĩa trong tên công nghệ (C++, C#, F#).
    t = re.sub(rf"[{BULLETS}]+", "", t)
    return t


def norm(s: str) -> str:
    return norm_text(s)


def count_occurrences(txt_norm: str, val_norm: str) -> int:
    if not val_norm:
        return 0
    return txt_norm.count(val_norm)


def split_sentences(s: str) -> list[str]:
    parts = re.split(r"[.\n;]+", str(s))
    return [p.strip() for p in parts if p.strip()]


def repo_path(url: str) -> str:
    u = str(url).strip()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^(github|gitlab|bitbucket)\.(com|org)/", "", u)
    u = re.sub(r"\.git$", "", u)
    return u.strip("/")


def ground_level(txt_raw: str, txt_norm: str, val: str, is_url: bool = False) -> str:
    """literal | normalized | ungrounded. So literal trên raw, chuẩn hóa trên norm."""
    if val is None:
        return "null"
    v = str(val)
    if not v.strip():
        return "empty"
    probe = repo_path(v) if is_url else v
    if probe and probe in txt_raw:
        return "literal"
    np = norm_text(probe)
    if np and np in txt_norm:
        return "normalized"
    return "ungrounded"


def check_long_text(txt_norm: str, text: str) -> tuple[str, list[str]]:
    """Kiểm tra đoạn văn dài: thử khớp cả đoạn, nếu không thì tách câu.
    Trả về (level, [câu không có căn cứ])."""
    s = str(text).strip()
    if norm_text(s) in txt_norm:
        return "ok", []
    bad = [c for c in split_sentences(s) if len(c) > 15 and norm_text(c) not in txt_norm]
    return ("ok", []) if not bad else ("partial", bad)


def shingles(text: str, k: int = 5) -> set:
    toks = re.findall(r"\w+", text.lower())
    return {" ".join(toks[i:i + k]) for i in range(max(0, len(toks) - k + 1))}


def main() -> int:
    lines = JSONL.read_text(encoding="utf-8").splitlines()
    records = []
    line_errors = []
    for i, ln in enumerate(lines, 1):
        if not ln.strip():
            continue
        try:
            records.append((i, json.loads(ln)))
        except json.JSONDecodeError as e:
            line_errors.append({"line": i, "error": str(e)})

    print(f"Dòng JSONL: {len(lines)}, parse được: {len(records)}, lỗi dòng: {len(line_errors)}")

    findings = []          # per-record issues
    desc_index = defaultdict(list)   # normalized description -> [(file, entity)]
    input_index = {}       # file -> shingles
    instr_set = set()

    for lineno, r in records:
        fname = r.get("file", f"?line{lineno}")
        issues = []
        txt = r.get("input", "")
        txt_norm = norm_text(txt)
        uses = Counter()   # norm(description) -> số lần nhãn dùng trong bản ghi
        instr_set.add(r.get("instruction", ""))

        # --- input khớp file nguồn ---
        src = TXT_DIR / fname if isinstance(fname, str) else None
        if src is None or not src.exists():
            issues.append({"path": "file", "type": "missing_source_txt",
                           "detail": f"không tìm thấy {fname} trong cv_texts/"})
        elif src.read_text(encoding="utf-8") != txt:
            issues.append({"path": "input", "type": "input_mismatch_source",
                           "detail": "input khác nội dung file .txt nguồn"})

        # --- output parse ---
        try:
            o = json.loads(r.get("output", ""))
        except Exception as e:
            issues.append({"path": "output", "type": "output_not_json", "detail": str(e)[:200]})
            findings.append({"file": fname, "line": lineno, "issues": issues})
            continue

        # --- schema ---
        try:
            CandidateProfile.model_validate(o)
        except ValidationError as e:
            for err in e.errors():
                loc = ".".join(str(x) for x in err.get("loc", ()))
                issues.append({"path": f"output.{loc}", "type": "schema_violation",
                               "detail": err.get("msg", "")})

        # --- sentinel + kiểu ---
        def check_scalar(path, v, allow_empty=False):
            if v is None:
                return
            if not isinstance(v, str):
                issues.append({"path": path, "type": "wrong_type",
                               "detail": f"expect str|null, got {type(v).__name__}: {v!r}"[:200]})
                return
            s = v.strip()
            if s == "" and not allow_empty:
                issues.append({"path": path, "type": "empty_string_for_missing",
                               "detail": "scalar rỗng, rule 2 yêu cầu null"})
            elif s.lower() in FORBIDDEN_SCALARS - {""} or s in ("null", "N/A", "Unknown"):
                issues.append({"path": path, "type": "forbidden_sentinel",
                               "detail": f"giá trị sentinel: {v!r}"})

        pi = o.get("personal_info") or {}
        for k in ("full_name", "email", "phone", "github_url"):
            check_scalar(f"output.personal_info.{k}", pi.get(k))
        if not isinstance(o.get("objective"), (str, type(None))):
            issues.append({"path": "output.objective", "type": "wrong_type",
                           "detail": f"expect str|null, got {type(o.get('objective')).__name__}"})
        elif isinstance(o.get("objective"), str) and o["objective"].strip().startswith("["):
            issues.append({"path": "output.objective", "type": "stringified_list",
                           "detail": o["objective"][:150]})

        # --- grounding ---
        def g(path, v, is_url=False):
            lv = ground_level(txt, txt_norm, v, is_url)
            if lv == "ungrounded":
                issues.append({"path": path, "type": "ungrounded",
                               "detail": f"{str(v)[:160]!r} không có căn cứ trong input"})
            return lv

        g("output.personal_info.full_name", pi.get("full_name"))
        g("output.personal_info.email", pi.get("email"))
        g("output.personal_info.phone", pi.get("phone"))
        g("output.personal_info.github_url", pi.get("github_url"), is_url=True)
        if isinstance(o.get("objective"), str) and o["objective"].strip():
            # objective dài: kiểm tra từng câu có căn cứ không
            for sent in re.split(r"[.\n]", o["objective"]):
                s = sent.strip()
                if len(s) > 40 and ground_level(txt, txt_norm, s) == "ungrounded":
                    issues.append({"path": "output.objective", "type": "ungrounded_sentence",
                                   "detail": s[:160]})
                    break

        for ei, e in enumerate(o.get("education") or []):
            base = f"output.education[{ei}]"
            if not isinstance(e, dict):
                issues.append({"path": base, "type": "wrong_type", "detail": "expect object"})
                continue
            g(f"{base}.school", e.get("school"))
            g(f"{base}.major", e.get("major"))
            g(f"{base}.gpa", e.get("gpa"))
            for k in ("start_year", "end_year"):
                v = e.get(k)
                if v is not None and not isinstance(v, int):
                    issues.append({"path": f"{base}.{k}", "type": "wrong_type",
                                   "detail": f"expect int|null, got {v!r}"})
                elif isinstance(v, int) and str(v) not in txt and norm_text(str(v)) not in txt_norm:
                    issues.append({"path": f"{base}.{k}", "type": "ungrounded",
                                   "detail": str(v)})

        ent_of = {}  # norm(description) -> entity đầu tiên dùng (để báo cáo)
        for ei, e in enumerate(o.get("experience") or []):
            base = f"output.experience[{ei}]"
            if not isinstance(e, dict):
                issues.append({"path": base, "type": "wrong_type", "detail": "expect object"})
                continue
            g(f"{base}.company", e.get("company"))
            g(f"{base}.job_title", e.get("job_title"))
            g(f"{base}.start_date", e.get("start_date"))
            g(f"{base}.end_date", e.get("end_date"))
            desc = e.get("description")
            if desc is None:
                issues.append({"path": f"{base}.description", "type": "wrong_type",
                               "detail": "expect list, got null"})
            elif not isinstance(desc, list):
                issues.append({"path": f"{base}.description", "type": "wrong_type",
                               "detail": f"expect list, got {type(desc).__name__}"})
            else:
                seen_bul = set()
                for b in desc:
                    bs = str(b).strip()
                    if not bs:
                        issues.append({"path": f"{base}.description", "type": "empty_bullet",
                                       "detail": "bullet rỗng"})
                        continue
                    nb = norm_text(bs)
                    if nb in seen_bul:
                        issues.append({"path": f"{base}.description", "type": "duplicate_bullet",
                                       "detail": bs[:160]})
                    seen_bul.add(nb)
                    if len(bs) > 30:
                        if ground_level(txt, txt_norm, bs) == "ungrounded":
                            issues.append({"path": f"{base}.description", "type": "ungrounded_bullet",
                                           "detail": bs[:200]})
                        else:
                            uses[nb] += 1
                            ent = f"{fname}#exp[{ei}]"
                            ent_of.setdefault(nb, ent)
                            desc_index[nb].append(ent)

        for pi_, p in enumerate(o.get("personal_projects") or []):
            base = f"output.personal_projects[{pi_}]"
            if not isinstance(p, dict):
                issues.append({"path": base, "type": "wrong_type", "detail": "expect object"})
                continue
            g(f"{base}.name", p.get("name"))
            g(f"{base}.role", p.get("role"))
            g(f"{base}.start_date", p.get("start_date"))
            g(f"{base}.end_date", p.get("end_date"))
            g(f"{base}.github_url", p.get("github_url"), is_url=True)
            ts = p.get("team_size")
            if ts is not None and not isinstance(ts, int):
                issues.append({"path": f"{base}.team_size", "type": "wrong_type",
                               "detail": f"expect int|null, got {ts!r}"})
            elif isinstance(ts, int) and str(ts) not in txt:
                issues.append({"path": f"{base}.team_size", "type": "ungrounded",
                               "detail": str(ts)})
            for t in (p.get("tech_stack") or []):
                if t and ground_level(txt, txt_norm, str(t)) == "ungrounded":
                    issues.append({"path": f"{base}.tech_stack", "type": "ungrounded",
                                   "detail": str(t)[:160]})
            d = p.get("description")
            if d is not None and not isinstance(d, str):
                issues.append({"path": f"{base}.description", "type": "wrong_type",
                               "detail": f"expect str|null, got {type(d).__name__}"})
            elif isinstance(d, str) and len(d.strip()) > 30:
                # description project là đoạn nối nhiều câu: kiểm tra từng câu
                lv, bad = check_long_text(txt_norm, d.strip())
                if lv != "ok":
                    issues.append({"path": f"{base}.description", "type": "ungrounded_bullet",
                                   "detail": "; ".join(b[:120] for b in bad[:2])})
                else:
                    for sent in split_sentences(d.strip()):
                        ns = norm_text(sent)
                        if len(sent) > 15 and ns:
                            uses[ns] += 1
                            ent = f"{fname}#proj[{pi_}]"
                            ent_of.setdefault(ns, ent)
                            desc_index[ns].append(ent)

        for arr_key in ("skills", "certificates", "honours"):
            arr = o.get(arr_key) or []
            if not isinstance(arr, list):
                issues.append({"path": f"output.{arr_key}", "type": "wrong_type",
                               "detail": "expect list"})
                continue
            seen = set()
            for item in arr:
                s = str(item).strip() if item is not None else ""
                if not s:
                    issues.append({"path": f"output.{arr_key}", "type": "empty_item",
                                   "detail": f"mục rỗng: {item!r}"})
                    continue
                ns = norm_text(s)
                if ns in seen:
                    issues.append({"path": f"output.{arr_key}", "type": "duplicate_item",
                                   "detail": s[:160]})
                seen.add(ns)
                if len(s) > 25 and ground_level(txt, txt_norm, s) == "ungrounded":
                    issues.append({"path": f"output.{arr_key}", "type": "ungrounded",
                                   "detail": s[:160]})

        for li, lang in enumerate(o.get("languages") or []):
            base = f"output.languages[{li}]"
            if not isinstance(lang, dict):
                issues.append({"path": base, "type": "wrong_type", "detail": "expect object"})
                continue
            g(f"{base}.language", lang.get("language"))
            g(f"{base}.note", lang.get("note"))

        # --- số lần nhãn dùng mô tả vs số lần văn bản chứa nó ---
        # (cùng câu template xuất hiện ở 2 job là hợp lệ NẾU văn bản cũng có 2 lần)
        for nb, used in uses.items():
            occ = count_occurrences(txt_norm, nb)
            if used > occ:
                issues.append({"path": "output", "type": "overused_description",
                               "detail": f"dùng {used} lần nhưng văn bản chỉ có {occ} lần "
                                         f"(entity đầu: {ent_of.get(nb)}): {nb[:120]}"})

        input_index[fname] = shingles(txt)
        if issues:
            findings.append({"file": fname, "line": lineno, "issues": issues})

    # ---- cấp dataset: input gần trùng ----
    files = list(input_index)
    near_dups = []
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            a, b = input_index[files[i]], input_index[files[j]]
            if not a or not b:
                continue
            jac = len(a & b) / len(a | b)
            if jac >= 0.5:
                near_dups.append({"files": [files[i], files[j]],
                                  "jaccard": round(jac, 3)})

    # ---- cụm description lặp qua nhiều bản ghi ----
    repeat_groups = []
    for k, ents in desc_index.items():
        recs = sorted(set(e.split("#")[0] for e in ents))
        if len(recs) >= 3:
            repeat_groups.append({"records": recs, "count": len(ents),
                                  "sample": k[:200]})

    by_type = Counter()
    for f in findings:
        for it in f["issues"]:
            by_type[it["type"]] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "total_lines": len(lines),
        "parsed_records": len(records),
        "line_errors": line_errors,
        "records_with_issues": len(findings),
        "issues_by_type": dict(by_type),
        "distinct_instructions": len(instr_set),
        "near_duplicate_inputs": sorted(near_dups, key=lambda x: -x["jaccard"]),
        "repeated_description_groups": sorted(repeat_groups, key=lambda x: -x["count"])[:50],
        "records": findings,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"Bản ghi có vấn đề: {len(findings)}/{len(records)}")
    print("Lỗi theo loại:")
    for k, v in by_type.most_common():
        print(f"  {k:<38} {v}")
    print(f"input gần trùng (>=0.5): {len(near_dups)} cặp")
    print(f"nhóm description lặp (>=3 bản ghi): {len(repeat_groups)}")
    print(f"instruction khác nhau: {len(instr_set)}")
    print(f"Chi tiết: {OUT}")


if __name__ == "__main__":
    main()
