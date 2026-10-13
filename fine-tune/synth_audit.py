#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
synth_audit.py — Phase 1: quét toàn bộ 435 bản ghi SYNTHETIC.

Không sửa gì. Chỉ thống kê + gắn cờ theo nhóm lỗi A–G của nhiệm vụ.
Xuất: fine-tune/_stage/synth_phase1.json
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
JSONL = ROOT / "cv-analysis-service" / "finetune_output" / "silver_dataset.jsonl"
OUT = ROOT / "fine-tune" / "_stage" / "synth_phase1.json"

sys.path.insert(0, str(ROOT / "fine-tune"))
from dataset_audit import norm_text, repo_path, shingles  # noqa: E402
from assemble_silver_dataset import CandidateProfile  # noqa: E402
from pydantic import ValidationError  # noqa: E402

SCHEMA_KEYS = {"personal_info", "objective", "education", "experience",
               "personal_projects", "skills", "certificates", "honours", "languages"}

DATE_RE = re.compile(r"(\d{1,2})[/-](\d{4})")
YEAR_RE = re.compile(r"(19\d{2}|20\d{2})")


def one_date(s: str | None):
    """Parse một mốc ngày đơn (MM/YYYY, YYYY, hoặc Hiện tại/Present)."""
    if not s:
        return None
    s = str(s).strip()
    if re.search(r"hiện tại|hien tai|present|now|current", s, re.I):
        return "present"
    m = DATE_RE.search(s)
    if m:
        return int(m.group(2)) * 12 + int(m.group(1))
    y = YEAR_RE.search(s)
    return int(y.group(1)) * 12 + 1 if y else None


def main() -> int:
    mm = {e["new"]: e["old"] for e in json.loads(
        (ROOT / "fine-tune/_stage/filename_map.json").read_text(encoding="utf-8"))}
    recs = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    syn = [r for r in recs if mm.get(r["file"], "").startswith("syn_")]
    print(f"Tổng bản ghi: {len(recs)} | synthetic: {len(syn)}")

    issues = []   # {code, file, json_path, evidence, severity, action}
    def flag(code, f, path, ev, sev, act):
        issues.append({"code": code, "file": f, "json_path": path,
                       "evidence": str(ev)[:300], "severity": sev,
                       "suggested_action": act})

    stats = {"lang": Counter(), "layout": Counter(), "role": Counter(),
             "level": Counter(), "n_projects": Counter(), "n_exp": Counter(),
             "input_chars": [], "missing_fields": Counter()}
    man = json.loads((ROOT / "fine-tune/_stage/synthetic_manifest.json").read_text(encoding="utf-8"))
    man_by_old = {m["file"]: m for m in man["manifest"]}
    repeat_counter = Counter()   # norm sentence -> số CV chứa
    repeat_files = defaultdict(set)  # norm sentence -> set files
    metric_counter = Counter()   # số liệu định lượng (pct, users...) -> tần suất
    input_hashes = Counter()
    input_shingles = {}
    pi_seen = defaultdict(list)  # norm(name|email) -> files

    for r in syn:
        f = r["file"]
        old = mm.get(f, "")
        m = man_by_old.get(old, {})
        stats["lang"][m.get("lang", "?")] += 1
        stats["layout"][m.get("layout", "?")] += 1
        stats["role"][m.get("role", "?")] += 1
        stats["level"][m.get("level", "?")] += 1
        txt = r.get("input", "")
        tnorm = norm_text(txt)
        stats["input_chars"].append(len(txt))
        input_hashes[txt] += 1
        input_shingles[f] = shingles(txt)

        # ---- A1: output JSON hợp lệ ----
        try:
            o = json.loads(r.get("output", ""))
        except Exception as e:
            flag("A-JSON", f, "output", str(e)[:200], "critical", "sửa JSON thủ công")
            continue
        # ---- A2: keys khớp schema ----
        extra = set(o.keys()) - SCHEMA_KEYS
        missing_k = SCHEMA_KEYS - set(o.keys())
        if extra:
            flag("A-KEYS-EXTRA", f, "output", sorted(extra), "high", "xóa key thừa")
        if missing_k:
            flag("A-KEYS-MISSING", f, "output", sorted(missing_k), "critical", "bổ sung key")
        # ---- A3: schema validate ----
        try:
            CandidateProfile.model_validate(o)
        except ValidationError as e:
            for err in e.errors():
                flag("A-SCHEMA", f, "output." + ".".join(map(str, err.get("loc", ()))),
                     err.get("msg", ""), "high", "sửa kiểu/cấu trúc")
        # ---- A4: trường bắt buộc ----
        pi = o.get("personal_info") or {}
        if not (pi.get("full_name") or "").strip():
            flag("A-REQ-NAME", f, "output.personal_info.full_name", pi.get("full_name"),
                 "critical", "xem xét thủ công")
        for i, e in enumerate(o.get("education") or []):
            if isinstance(e, dict) and not (e.get("school") or "").strip():
                flag("A-REQ-SCHOOL", f, f"output.education[{i}].school", e.get("school"),
                     "high", "xem xét thủ công")
        for i, e in enumerate(o.get("experience") or []):
            if isinstance(e, dict) and not (e.get("company") or "").strip():
                flag("A-REQ-COMPANY", f, f"output.experience[{i}].company", e.get("company"),
                     "high", "xem xét thủ công")
        for i, p in enumerate(o.get("personal_projects") or []):
            if isinstance(p, dict) and not (p.get("name") or "").strip():
                flag("A-REQ-PNAME", f, f"output.personal_projects[{i}].name", p.get("name"),
                     "high", "xem xét thủ công")
        # ---- A5: kiểu dữ liệu ----
        for i, p in enumerate(o.get("personal_projects") or []):
            if not isinstance(p, dict):
                continue
            ts = p.get("team_size")
            if ts is not None and not isinstance(ts, int):
                flag("A-TYPE", f, f"output.personal_projects[{i}].team_size",
                     repr(ts), "high", "ép int hoặc null")
            d = p.get("description")
            if d is not None and not isinstance(d, str):
                flag("A-TYPE", f, f"output.personal_projects[{i}].description",
                     type(d).__name__, "high", "nối thành chuỗi")
        for i, e in enumerate(o.get("education") or []):
            if not isinstance(e, dict):
                continue
            for k in ("start_year", "end_year"):
                if e.get(k) is not None and not isinstance(e.get(k), int):
                    flag("A-TYPE", f, f"output.education[{i}].{k}",
                         repr(e.get(k)), "high", "ép int hoặc null")
        for i, e in enumerate(o.get("experience") or []):
            if isinstance(e, dict) and not isinstance(e.get("description"), list):
                flag("A-TYPE", f, f"output.experience[{i}].description",
                     type(e.get("description")).__name__, "high", "chuyển thành list")
        if not isinstance(o.get("objective"), (str, type(None))):
            flag("A-TYPE", f, "output.objective", type(o.get("objective")).__name__,
                 "high", "chuyển thành chuỗi hoặc null")
        # ---- A6: sentinel cho thiếu ----
        for path, v in [("output.objective", o.get("objective"))]:
            if isinstance(v, str) and v.strip().lower() in ("null", "n/a", "unknown", ""):
                flag("A-SENTINEL", f, path, repr(v), "medium", "đổi thành null")
        # ---- B: nhất quán input-output ----
        for k in ("full_name", "email", "phone"):
            v = (pi.get(k) or "").strip()
            if v and v not in txt and norm_text(v) not in tnorm:
                flag("B-CONTACT", f, f"output.personal_info.{k}", v, "high",
                     "đối chiếu input, sửa hoặc null")
        gh = (pi.get("github_url") or "").strip()
        if gh and repo_path(gh) not in txt and norm_text(repo_path(gh)) not in tnorm:
            flag("B-CONTACT", f, "output.personal_info.github_url", gh, "high",
                 "đối chiếu input, sửa hoặc null")
        for i, e in enumerate(o.get("experience") or []):
            if not isinstance(e, dict):
                continue
            for k in ("company", "job_title", "start_date", "end_date"):
                v = e.get(k)
                if v and str(v).strip() and str(v) not in txt and norm_text(str(v)) not in tnorm:
                    flag("B-EXP", f, f"output.experience[{i}].{k}", str(v)[:150], "high",
                         "đối chiếu input, sửa hoặc null")
            for b in (e.get("description") or []):
                bs = str(b).strip()
                if len(bs) > 30 and bs not in txt and norm_text(bs) not in tnorm:
                    # thử theo câu
                    bad = [s for s in re.split(r"[.\n;]+", bs)
                           if len(s.strip()) > 20 and s.strip() not in txt
                           and norm_text(s.strip()) not in tnorm]
                    if bad:
                        flag("B-EXP-BULLET", f, f"output.experience[{i}].description",
                             bad[0][:200], "high", "sửa theo input")
        for i, p in enumerate(o.get("personal_projects") or []):
            if not isinstance(p, dict):
                continue
            for k in ("name", "role", "start_date", "end_date"):
                v = p.get(k)
                if v and str(v).strip() and str(v) not in txt and norm_text(str(v)) not in tnorm:
                    flag("B-PROJ", f, f"output.personal_projects[{i}].{k}", str(v)[:150],
                         "high", "đối chiếu input, sửa hoặc null")
            if p.get("github_url") and norm_text(repo_path(p["github_url"])) not in tnorm:
                flag("B-PROJ-URL", f, f"output.personal_projects[{i}].github_url",
                     p["github_url"], "high", "đối chiếu input")
            ts = p.get("team_size")
            if isinstance(ts, int) and str(ts) not in txt:
                flag("B-PROJ-TEAM", f, f"output.personal_projects[{i}].team_size",
                     ts, "medium", "đối chiếu input")
            for t in (p.get("tech_stack") or []):
                if t and str(t) not in txt and norm_text(str(t)) not in tnorm:
                    flag("B-PROJ-TECH", f, f"output.personal_projects[{i}].tech_stack",
                         str(t)[:120], "high", "đối chiếu input")
            d = p.get("description") or ""
            if isinstance(d, str) and len(d.strip()) > 30:
                bad = [s for s in re.split(r"[.\n;]+", d)
                       if len(s.strip()) > 20 and s.strip() not in txt
                       and norm_text(s.strip()) not in tnorm]
                if bad:
                    flag("B-PROJ-DESC", f, f"output.personal_projects[{i}].description",
                         bad[0][:200], "high", "sửa theo input")
        for i, e in enumerate(o.get("education") or []):
            if not isinstance(e, dict):
                continue
            for k in ("school", "major", "gpa"):
                v = e.get(k)
                if v and str(v).strip() and str(v) not in txt and norm_text(str(v)) not in tnorm:
                    flag("B-EDU", f, f"output.education[{i}].{k}", str(v)[:150],
                         "high", "đối chiếu input")
        for arr, key in (("skills", None), ("certificates", None), ("honours", None)):
            for item in (o.get(arr) or []):
                s = str(item).strip() if item else ""
                if len(s) > 25 and s not in txt and norm_text(s) not in tnorm:
                    flag("B-LIST", f, f"output.{arr}", s[:150], "medium",
                         "đối chiếu input")
        # ---- C: gán nhầm thực thể ----
        # C1: cùng câu mô tả ở 2 entity khác nhau (vượt số lần xuất hiện)
        seen = Counter()
        ent_of = {}
        for i, e in enumerate(o.get("experience") or []):
            if not isinstance(e, dict):
                continue
            for b in (e.get("description") or []):
                n = norm_text(str(b))
                if len(str(b).strip()) > 30 and n:
                    seen[n] += 1
                    ent_of.setdefault(n, f"exp[{i}]")
        for i, p in enumerate(o.get("personal_projects") or []):
            if not isinstance(p, dict):
                continue
            d = p.get("description") or ""
            if isinstance(d, str):
                for s in re.split(r"[.\n;]+", d):
                    n = norm_text(s)
                    if len(s.strip()) > 30 and n:
                        seen[n] += 1
                        ent_of.setdefault(n, f"proj[{i}]")
        for n, c in seen.items():
            occ = tnorm.count(n) if n else 0
            if c > occ and occ >= 0 and c > 1:
                flag("C-REUSE", f, "output",
                     f"câu dùng {c} lần, input có {occ} lần (entity đầu {ent_of[n]}): {n[:150]}",
                     "medium", "kiểm tra gán nhầm")
        # C2: tech_stack giống hệt nhau ở mọi project trong CV
        tss = [tuple(sorted(map(str, (p.get("tech_stack") or [])))) for p in (o.get("personal_projects") or []) if isinstance(p, dict)]
        if len(tss) > 1 and all(t == tss[0] for t in tss) and tss[0]:
            flag("C-SAME-TECH", f, "output.personal_projects",
                 f"{len(tss)} projects cùng tech: {list(tss[0])[:6]}", "low",
                 "chấp nhận nếu input đúng vậy (đa số do template)")
        # C3: cùng câu mô tả cho 2 dự án khác nhau nhưng input mỗi project khác nhau
        # (đã bao bởi C1 qua multiplicity)
        # ---- E: lặp trong entity ----
        for i, e in enumerate(o.get("experience") or []):
            if not isinstance(e, dict):
                continue
            bl = [norm_text(str(b)) for b in (e.get("description") or []) if str(b).strip()]
            if len(bl) != len(set(bl)):
                flag("E-DUP-BULLET", f, f"output.experience[{i}].description",
                     "bullet lặp trong cùng công ty", "medium", "xóa bản trùng")
        # ---- E: thống kê lặp toàn cục (mẫu câu + số liệu) ----
        for i, e in enumerate(o.get("experience") or []):
            if not isinstance(e, dict):
                continue
            for b in (e.get("description") or []):
                n = norm_text(str(b))
                if len(str(b).strip()) > 30 and n:
                    repeat_counter[n] += 1
                    repeat_files[n].add(f)
        for i, p in enumerate(o.get("personal_projects") or []):
            if not isinstance(p, dict):
                continue
            d = p.get("description") or ""
            if isinstance(d, str):
                for s in re.split(r"[.\n;]+", d):
                    n = norm_text(s)
                    if len(s.strip()) > 30 and n:
                        repeat_counter[n] += 1
        for m in re.findall(r"\d[\d.,]*\s*(?:%|request|users?|pull request|service|ms|s\b|phút|triệu|nghìn)", txt):
            metric_counter[norm_text(m)] += 1
        periods = []
        for i, e in enumerate(o.get("experience") or []):
            if not isinstance(e, dict):
                continue
            s2, e2 = one_date(e.get("start_date")), one_date(e.get("end_date"))
            # so sánh end vs start khi cùng parse được
            if isinstance(e2, int) and isinstance(s2, int) and e2 < s2:
                flag("F-DATE", f, f"output.experience[{i}]",
                     f"end < start: {e.get('start_date')} / {e.get('end_date')}", "high", "sửa theo input")
            periods.append(("exp", i, (s2, e2)))
        for i, p in enumerate(o.get("personal_projects") or []):
            if not isinstance(p, dict):
                continue
            s2, e2 = one_date(p.get("start_date")), one_date(p.get("end_date"))
            if isinstance(e2, int) and isinstance(s2, int) and e2 < s2:
                flag("F-DATE", f, f"output.personal_projects[{i}]",
                     f"end < start: {p.get('start_date')} / {p.get('end_date')}", "high", "sửa theo input")
            periods.append(("proj", i, (s2, e2)))
        edus = [e for e in (o.get("education") or []) if isinstance(e, dict)]
        for i, e in enumerate(edus):
            sy, ey = e.get("start_year"), e.get("end_year")
            if isinstance(sy, int) and isinstance(ey, int) and ey < sy:
                flag("F-EDU-YEARS", f, f"output.education[{i}]",
                     f"{sy}-{ey}", "high", "sửa theo input")
            if isinstance(sy, int) and not (1950 <= sy <= 2030):
                flag("F-EDU-YEARS", f, f"output.education[{i}].start_year", sy,
                     "medium", "kiểm tra")
            if isinstance(ey, int) and not (1950 <= ey <= 2035):
                flag("F-EDU-YEARS", f, f"output.education[{i}].end_year", ey,
                     "medium", "kiểm tra")
        # project/experience nằm ngoài cửa sổ học + làm? (dung sai 1 năm)
        for kind, i, per in periods:
            if not per or per[0] is None:
                continue
            y0 = per[0] // 12
            for e in edus:
                sy = e.get("start_year")
                if isinstance(sy, int) and y0 < sy - 1:
                    flag("F-TIMELINE", f, f"output.{'personal_projects' if kind=='proj' else 'experience'}[{i}]",
                         f"năm {y0} trước khi nhập học {sy}", "low",
                         "chấp nhận nếu là đồ án/sở thích (ghi chú), ngược lại sửa")
        # ---- G: đa dạng + thiếu trường ----
        stats["n_projects"][len(o.get("personal_projects") or [])] += 1
        stats["n_exp"][len(o.get("experience") or [])] += 1
        for k in ("objective", "education", "experience", "personal_projects",
                  "skills", "certificates", "honours", "languages"):
            if not o.get(k):
                stats["missing_fields"][k] += 1
        # ---- D: personal_info trùng ----
        key = norm_text(f"{pi.get('full_name','')}|{pi.get('email','')}")
        pi_seen[key].append(f)

    # ---- D: input trùng / gần trùng ----
    exact_dups = [h for h, c in input_hashes.items() if c > 1]
    files = list(input_shingles)
    near = []
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            a, b = input_shingles[files[i]], input_shingles[files[j]]
            if not a or not b:
                continue
            jac = len(a & b) / len(a | b)
            if jac >= 0.5:
                near.append({"files": [files[i], files[j]], "jaccard": round(jac, 3)})
    near.sort(key=lambda x: -x["jaccard"])
    dup_pi = {k: v for k, v in pi_seen.items() if len(v) > 1}

    # ---- E: cụm lặp (câu dài >=60 ký tự, xuất hiện ở >=5 CV) ----
    rep_groups = [{"sample": k[:200], "records": sorted(repeat_files[k]), "count": c}
                  for k, c in repeat_counter.most_common()
                  if len(repeat_files[k]) >= 5 and len(k) >= 60][:60]
    top_repeat = repeat_counter.most_common(40)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "total_synthetic": len(syn),
        "issues": issues,
        "issues_by_code": dict(Counter(i["code"] for i in issues)),
        "stats": {k: (dict(v) if isinstance(v, Counter) else v) for k, v in stats.items()},
        "input_chars": {"min": min(stats["input_chars"]), "median": sorted(stats["input_chars"])[len(stats["input_chars"]) // 2], "max": max(stats["input_chars"])},
        "exact_duplicate_inputs": len(exact_dups),
        "near_duplicate_pairs": near,
        "duplicate_personal_info": dup_pi,
        "top_repeated_sentences": [{"sample": k[:200], "count": c} for k, c in top_repeat],
        "top_repeated_metrics": [{"sample": k[:120], "count": c} for k, c in metric_counter.most_common(20)],
        "repeated_sentence_groups": rep_groups,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"Issues: {len(issues)}")
    for k, v in Counter(i["code"] for i in issues).most_common():
        print(f"  {k:<18} {v}")
    print(f"exact dup inputs: {len(exact_dups)} | near>=0.5: {len(near)} | dup personal_info: {len(dup_pi)}")
    print(f"Gesc/how: {OUT}")


if __name__ == "__main__":
    main()
