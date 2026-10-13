#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_synthetic_cvs.py
=========================
Giai đoạn 2b - Sinh CV tổng hợp (synthetic data) để lấp đầy ma trận Role x Level.

Ma trận mục tiêu (thiết kế ban đầu, tổng 500 ô):
    Role              intern junior middle senior lead   tổng
    Backend              15     18     18     15    9      75
    Frontend & Mobile    15     18     18     15    9      75
    DevOps & Cloud       12     15     15     12    6      60
    Data & AI/ML         12     15     15     12    6      60
    Business Analyst     12     15     15     12    6      60
    QA / QC              12     15     15     12    6      60
    Security & SysAdmin  10     12     12     10    6      50
    Fullstack & Khác     12     15     15     12    6      60

Cách hoạt động:
  1. Đọc nhãn Role x Level của các CV thật (fine-tune/_stage/real_labels.json).
  2. Với mỗi ô (role, level), tính số lượng thiếu = max(0, target - số CV thật).
  3. Sinh đúng số CV synthetic cho ô đó với ngôn ngữ, độ dài, văn phong, layout
     đa dạng nhẫn nhiều (dùng seed cố định => chạy lại cho kết quả giống nhau).

Tổng file cuối cùng = 500 ô ma trận + phần CV thật vượt quá target
(không cắt bỏ dữ liệu thật) => khoảng 520 file .txt.

Cách chạy:
  python3 generate_synthetic_cvs.py
  python3 generate_synthetic_cvs.py --seed 123 --force
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import re
import sys
import unicodedata
from collections import defaultdict

import cv_knowledge_base as KB

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
TXT_DIR = ROOT / "cv-analysis-service" / "cv_texts"
STAGE_DIR = HERE / "_stage"
LABELS_JSON = STAGE_DIR / "real_labels.json"
SYNTH_MANIFEST = STAGE_DIR / "synthetic_manifest.json"
SYNTH_PROFILES = STAGE_DIR / "synthetic_profiles.json"

LEVELS = ["intern", "junior", "middle", "senior", "lead"]

# ---------------------------------------------------------------------------
# Ma trận Role x Level mục tiêu (thiết kế của đề bài)
MATRIX: dict[str, list[int]] = {
    "backend":   [15, 18, 18, 15, 9],
    "frontend":  [15, 18, 18, 15, 9],
    "devops":    [12, 15, 15, 12, 6],
    "data":      [12, 15, 15, 12, 6],
    "ba":        [12, 15, 15, 12, 6],
    "qa":        [12, 15, 15, 12, 6],
    "security":  [10, 12, 12, 10, 6],
    "fullstack": [12, 15, 15, 12, 6],
}
TOTAL_CELLS = sum(sum(v) for v in MATRIX.values())   # 500

# Ngôn ngữ: ~70% tiếng Việt, ~30% tiếng Anh (mô phỏng thị trường tuyển dụng IT VN)
LANG_WEIGHTS = {"vi": 0.70, "en": 0.30}

# Kích thước file: chỉ tiêu 1.5 KB - 7 KB
MIN_BYTES, MAX_BYTES = 1500, 7000


# ============================================================ TIỆN ÍCH
def strip_accents(s: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn"
    )


def slug(s: str) -> str:
    """Chuyển chuỗi thành slug không dấu, dùng cho tên file."""
    s = strip_accents(s.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "cv"


def make_name(rng: random.Random, lang: str) -> str:
    if lang == "en" and rng.random() < 0.55:
        return f"{rng.choice(KB.EN_FIRST)} {rng.choice(KB.EN_LAST)}"
    return (
        f"{rng.choice(KB.VN_SURNAMES)} "
        f"{rng.choice(KB.VN_MIDDLE)} "
        f"{rng.choice(KB.VN_GIVEN)}"
    )


def make_contact(rng: random.Random, name: str, lang: str, idx: int) -> dict:
    base = slug(name).replace("-", "")
    email = f"{base}{idx}{rng.randint(10, 99)}@{rng.choice(KB.EMAIL_DOMAINS)}"
    phone = (
        f"0{rng.choice('35789')}{rng.randint(1000000, 9999999)}"
        if rng.random() < 0.5
        else f"+84 {rng.randint(30, 98)} {rng.randint(1000000, 9999999)}"
    )
    city = rng.choice(KB.CITIES_EN if lang == "en" else KB.CITIES_VN)
    user = f"{base}{rng.randint(1, 999)}"
    return {
        "email": email,
        "phone": phone,
        "city": city,
        "github": f"https://github.com/{user}",
        "gitlab": f"https://gitlab.com/{user}",
        "linkedin": f"https://linkedin.com/in/{user.replace('-', '-')}",
        "website": f"https://{user}.dev",
    }


def job_title_ladder(role: str, level: str, lang: str) -> list[str]:
    """Chức danh của các công việc CŨ, theo thứ tự từ mới -> cũ.

    Chức danh hiện tại đã có sẵn; các chức danh ở đây luôn thấp hơn nó, ví dụ
    một Senior Backend sẽ có lịch sử: Senior -> Mid-level -> Junior.
    """
    rank = {"intern": 0, "junior": 1, "middle": 2, "senior": 3, "lead": 4}
    cur = rank[level]
    # ánh xạ sang bậc thấp hơn, bỏ qua 'intern' trừ khi bản thân là intern
    candidates = [lv for lv in ("lead", "senior", "middle", "junior", "intern")
                  if rank[lv] < cur]
    if not candidates:
        return [translate_title(role, level) if lang == "en"
                else KB.ROLE_BANKS[role]["vi"]["titles"][level]]
    # sắp xếp từ cao xuống thấp, lấy tối đa 3 cấp
    candidates = [lv for lv in ("senior", "middle", "junior") if lv in candidates]
    if not candidates:
        candidates = ["junior"]
    return [
        translate_title(role, lv) if lang == "en"
        else KB.ROLE_BANKS[role]["vi"]["titles"][lv][0]
        for lv in candidates[:3]
    ]


def make_dates(rng: random.Random, level: str, today_year: int = 2026) -> list[tuple[int, int]]:
    """Trả về danh sách (năm bắt đầu, số năm) theo thứ tự gần nhất -> cũ nhất."""
    bank = KB.LEVEL_BANKS[level]
    lo, hi = bank["vi"]["exp_years"]
    total = rng.randint(lo, hi)
    if total == 0:
        return [(today_year - 1, 1)]
    # chia thành các giai đoạn liên tiếp, mỗi giai đoạn 1-3 năm
    spans: list[int] = []
    remaining = total
    while remaining > 0:
        take = min(remaining, rng.randint(1, 3))
        spans.append(take)
        remaining -= take
    out: list[tuple[int, int]] = []
    cursor = today_year
    for sp in spans:
        cursor -= sp
        out.append((cursor, sp))
    return out


def rand_range(rng: random.Random, spec) -> int:
    """Chọn số nguyên trong khoảng; chấp nhận int hoặc [a, b]."""
    if isinstance(spec, int):
        return spec
    if len(spec) == 1:
        return spec[0]
    return rng.randint(spec[0], spec[1])


def fmt_month_year(rng: random.Random, year: int, first: bool = False) -> str:
    month = rng.choice([1, 3, 5, 7, 9, 11]) if first else rng.choice([2, 4, 6, 8, 10, 12])
    return f"{month:02d}/{year}"


def fmt_range(rng: random.Random, start_year: int, months: int, today_year: int) -> str:
    """Khoảng thời gian dạng MM/YYYY - MM/YYYY (hoặc 'Hiện tại' nếu còn đang làm).

    `months` là số THÁNG kéo dài (không phải năm).
    """
    sm = rng.randint(1, 10)
    total = sm - 1 + max(1, months)
    ey = start_year + total // 12
    em = total % 12 + 1
    end = "Hiện tại" if ey >= today_year else f"{em:02d}/{ey}"
    return f"{sm:02d}/{start_year} - {end}"


def fmt_range_vi(rng: random.Random, start_year: int, months: int, today_year: int) -> str:
    return fmt_range(rng, start_year, months, today_year)


def fmt_range_en(rng: random.Random, start_year: int, months: int, today_year: int) -> str:
    """Bản tiếng Anh: 'Mar 2021 - Present'."""
    months_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    sm = rng.randint(1, 10)
    total = sm - 1 + max(1, months)
    ey = start_year + total // 12
    em = total % 12
    end = "Present" if ey >= today_year else f"{months_en[em]} {ey}"
    return f"{months_en[sm - 1]} {start_year} - {end}"


# ============================================================ DỰNG PROFILE
def build_profile(rng: random.Random, role: str, level: str, idx: int) -> dict:
    """Tạo một CandidateProfile hoàn chỉnh (dùng chung cho mọi layout)."""
    lang = "vi" if rng.random() < LANG_WEIGHTS["vi"] else "en"
    today_year = 2026

    name = make_name(rng, lang)
    contact = make_contact(rng, name, lang, idx)

    bank = KB.ROLE_BANKS[role]
    lbank = KB.LEVEL_BANKS[level]
    lang_bank = lbank["vi"] if lang == "vi" else lbank["en"]

    # Chức danh mục tiêu (ứng tuyển) và chức danh theo từng cấp bậc.
    # Vì `titles[level]` đã chứa sẵn cấp bậc ("Kỹ sư Phần mềm Cao cấp") nên
    # không được nối thêm `job_suffix` vào, tránh lặp ("Cao cấp Cao cấp").
    title = translate_title(role, level) if lang == "en" else rng.choice(bank["vi"]["titles"][level])
    # chức danh của các công việc CŨ hơn: luôn thấp hơn chức danh hiện tại
    title_ladder = job_title_ladder(role, level, lang)

    core = rng.sample(bank["vi"]["core"], k=min(len(bank["vi"]["core"]), rng.randint(5, 8)))
    extra = rng.sample(bank["vi"]["stack"], k=min(len(bank["vi"]["stack"]), rng.randint(4, 6)))
    skills = list(dict.fromkeys(core + extra))

    # ---- metrics ----
    # Mỗi CV có bộ chỉ số riêng (giữ nhất quán trong 1 CV để không bị vô lý),
    # nhưng giá trị được rút ngẫu nhiên lại cho từng job/project để CV không bị
    # lặp lại cùng một con số ở mọi nơi.
    metrics: dict[str, object] = {
        k: rng.choice(v) for k, v in KB.METRIC_POOL.items()
    }
    metrics["cov0"] = rng.randint(15, 40)
    metrics["years"] = rand_range(rng, lbank["vi"]["exp_years"])

    def local_metrics() -> dict:
        """Bộ chỉ số riêng cho một job/project (giữ các giá trị 'danh tính' ổn định)."""
        m = dict(metrics)
        for k, pool in KB.METRIC_POOL.items():
            if k in ("years", "cov0", "cov"):
                continue
            m[k] = rng.choice(pool)
        return m

    # ---- education ----
    is_course = level == "intern" and rng.random() < 0.3
    if is_course:
        school, major = rng.choice(KB.SCHOOLS_VN_COURSE)
    else:
        school, major = rng.choice(KB.SCHOOLS_VN)
    if lang == "en":
        school = translate_school(school)
        major = translate_major(major)
    grad_year = today_year - rng.randint(0, 1) if level == "intern" else today_year - rng.randint(1, 4)
    start_year = grad_year - rng.choice([3, 4])
    gpa = f"{rng.uniform(2.8, 3.95):.2f}/4.0" if rng.random() < 0.6 else f"{rng.uniform(7.0, 9.5):.1f}/10.0"
    degree = rng.choice(["Kỹ sư", "Cử nhân", "Thạc sĩ"] if lang == "vi" else ["Bachelor of Engineering", "Bachelor of Science", "Master of Science"])
    if lang == "en":
        degree = degree.replace("Kỹ sư", "Bachelor of Engineering")

    education = [{
        "school": school,
        "major": major,
        "degree": degree,
        "start_year": start_year,
        "end_year": grad_year,
        "gpa": gpa,
        "note": rng.choice([
            "Học bổng khuyến khích học giỏi" if lang == "vi" else "Dean's List scholarship",
            "Đồ án chuyên ngành đạt điểm 9/10" if lang == "vi" else "Capstone project scored 9/10",
            "Chủ nhiệm lớp kỹ thuật" if lang == "vi" else "Technical class lead",
        ]),
    }]

    # ---- experience ----
    spans = make_dates(rng, level, today_year)
    n_jobs = min(len(spans), rand_range(rng, lbank["vi"]["n_jobs"]))
    spans = spans[:n_jobs]

    domains = (bank["domains_en"] if lang == "en" else bank["vi"]["domains"])
    modules = bank["vi"]["modules"]
    companies = KB.COMPANIES_EN if (lang == "en" and rng.random() < 0.5) else KB.COMPANIES_VN
    companies = [c for c in companies if c not in ("Rất nhiều", "Tổng công ty")]

    used_companies: set[str] = set()
    experience = []
    for i, (sy, months) in enumerate(spans):
        # công ty: ưu tiên công ty chưa dùng để tránh trùng
        avail = [c for c in companies if c not in used_companies] or companies
        company = rng.choice(avail)
        used_companies.add(company)

        exp: dict = {
            "company": company,
            "job_title": title if i == 0 else title_ladder[min(i - 1, len(title_ladder) - 1)],
            "start_year": sy,
            "end_year": "Hiện tại" if sy + months >= today_year else f"{sy + months}",
            "period": (fmt_range_vi if lang == "vi" else fmt_range_en)(rng, sy, months * 12, today_year),
            "domain": rng.choice(domains),
            "module": rng.choice(modules),
            "tech": rng.choice(skills),
            "bullets": [],
        }
        # job cũ phải "nhẹ hơn" job hiện tại: bỏ các bullet chỉ dành cho senior/lead
        pool = [b for b in lbank[lang]["desc_bullets"]]
        if i > 0 and level in ("senior", "lead"):
            pool = [b for b in pool if not re.search(r"\{n_team\}|\{n_mentee\}|\{n_sprint\}|\{n_month\}", b)]
        if i == 0 and level == "intern":
            pool = [b for b in pool if not re.search(r"\{n_team\}|\{n_mentee\}|\{n_sprint\}", b)]

        m = local_metrics()
        n_bul = rng.randint(3, 4) if level in ("intern", "junior") else rng.randint(4, 5)
        for b in rng.sample(pool, k=min(n_bul, len(pool))):
            exp["bullets"].append(fill_template(b, exp, m, rng))
        experience.append(exp)

    # ---- projects ----
    n_proj = rand_range(rng, lbank["vi"]["n_projects"])
    projects = []
    used_pnames: set[str] = set()

    # Dự án phải nằm trong cửa sổ kinh nghiệm (không trước ngày bắt đầu đi làm,
    # không sau năm hiện tại) để CV không vô lý.
    career_start = min(sy for sy, _ in spans) if spans else today_year - 1
    career_lo = max(career_start - 1, start_year)      # có thể có đồ án từ năm học
    career_hi = today_year
    career_span = max(1, career_hi - career_lo)

    for i in range(n_proj):
        if career_span <= 1:
            sy, months = career_lo, rng.randint(2, 10)
        else:
            sy = career_lo + rng.randint(0, career_span - 1)
            months = rng.randint(2, max(2, min(11, career_hi - sy))) if sy < career_hi else rng.randint(2, 10)

        pool_names = [n for n in (KB.PROJECT_NAMES_VI if lang == "vi" else KB.PROJECT_NAMES_EN)
                      if n not in used_pnames]
        pname = rng.choice(pool_names) if pool_names else rng.choice(
            KB.PROJECT_NAMES_VI if lang == "vi" else KB.PROJECT_NAMES_EN)
        used_pnames.add(pname)

        # tech_stack RIÊNG của project: tập con 2-4 công nghệ, khác nhau giữa các
        # project, và BẮT BUỘC in ra văn bản (xem project_meta) để nhãn suy ra được.
        k_tech = min(len(skills), rng.randint(2, 4))
        ptech = rng.sample(skills, k=k_tech)

        # period chỉ tính 1 lần: nhãn (start_date) và văn bản in ra phải khớp nhau.
        per = (fmt_range_vi if lang == "vi" else fmt_range_en)(rng, sy, months, today_year)

        pr: dict = {
            "name": pname,
            "role": title,
            "start_year": sy,
            "start_date": per,
            "end_year": sy + max(0, months // 12),
            "period": per,
            "domain": rng.choice(domains),
            "module": rng.choice(modules),
            "tech": rng.choice(skills),
            "tech_stack": ptech,
            "github": rng.choice([contact["github"], contact["gitlab"], ""]),
            "team_size": rng.choice([1, 2, 3, 4, 5]),
            "bullets": [],
        }
        # Bullet "Dự án {project} - {domain}..." chỉ hữu ích ở bullet đầu tiên
        # (nơi người đọc chưa biết tên dự án). Các bullet sau bỏ {project} để
        # tránh lặp lại tên dự án nhiều lần trong cùng một mục.
        pool = []
        for b in lbank[lang]["project_bullets"]:
            if "{project}" in b and pr["bullets"]:
                continue
            pool.append(b)
        # bỏ bullet chỉ phù hợp cấp cao cho dự án cá nhân của intern/junior
        if level in ("intern", "junior"):
            pool = [b for b in pool if not re.search(r"\{n_team\}|\{n_mentee\}|\{n_sprint\}|\{n_month\}|\{n_year\}|\{n_product\}", b)]
        if not pool:
            pool = lbank[lang]["project_bullets"]

        m = local_metrics()
        n_bul = rng.randint(2, 4)
        for b in rng.sample(pool, k=min(n_bul, len(pool))):
            pr["bullets"].append(fill_template(b, pr, m, rng))
        projects.append(pr)

    # sắp xếp dự án mới -> cũ cho mỹ thuật
    projects.sort(key=lambda x: x["start_year"], reverse=True)

    # ---- certificates / honours / activities / languages ----
    cert_pool = KB.CERTS_VN if lang == "vi" else KB.CERTS_EN
    n_cert = rng.randint(1, 3) if level != "intern" else rng.randint(0, 2)
    certs = rng.sample(cert_pool, k=min(n_cert, len(cert_pool)))

    ach_pool = KB.ACHIEVEMENTS_VN if lang == "vi" else KB.ACHIEVEMENTS_EN
    honours = rng.sample(ach_pool, k=rng.randint(1, 2) if level == "intern" else rng.randint(1, 3))

    activities = (
        rng.sample(KB.ACTIVITIES_VN, k=rng.randint(1, 2)) if lang == "vi" and rng.random() < 0.5
        else []
    )

    langs = [KB.LANG_VN[0]] + rng.sample(KB.LANG_VN[1:], k=rng.randint(1, 2))
    if lang == "en":
        langs = [("Vietnamese", "Native"), ("English", rng.choice([
            "Fluent - IELTS 7.5", "Good - TOEFL 95", "Intermediate - IELTS 6.0",
        ]))]

    soft = rng.sample(KB.SOFT_SKILLS_VI if lang == "vi" else KB.SOFT_SKILLS_EN, k=3)

    objective_pool = lbank[lang]["objective"]
    objective = fill_template(
        rng.choice(objective_pool),
        {"domain": rng.choice(domains)},
        metrics,
        rng,
        extra={
            "title": title,
            "tech": ", ".join(core[:3]),
            "major": major,
            "years": metrics["years"],
            "domain": rng.choice(domains),
        },
    )

    return {
        "lang": lang,
        "name": name,
        "title": title,
        "contact": contact,
        "objective": objective,
        "education": education,
        "experience": experience,
        "projects": projects,
        "skills": skills,
        "certificates": certs,
        "honours": honours,
        "activities": activities,
        "languages": langs,
        "soft_skills": soft,
        "domain": experience[0]["domain"] if experience else rng.choice(domains),
    }


def fill_template(tpl: str, ctx: dict, metrics: dict, rng: random.Random,
                 extra: dict | None = None) -> str:
    """Điền mọi placeholder trong khuôn câu.

    Tự động bù bất kỳ placeholder nào chưa có giá trị từ KB.METRIC_POOL, nên
    thêm placeholder mới vào từ điển không cần sửa hàm này.
    """
    vals: dict[str, object] = {}
    for key, pool in KB.METRIC_POOL.items():
        vals[key] = metrics.get(key, rng.choice(pool))
    vals["project"] = ctx.get("name", "")
    vals["domain"] = ctx.get("domain", "")
    vals["module"] = ctx.get("module", "")
    vals["tech"] = ctx.get("tech", "")
    vals["course"] = rng.choice(KB.COURSE_NAMES)
    if extra:
        vals.update(extra)

    # placeholder lạ chưa biết -> lấy giá trị ngẫu nhiên hợp lý từ metric pool
    def _fallback(key: str, _fmt: str, _conv: int | None, spec: str, conv: object) -> str:
        if key not in vals:
            vals[key] = rng.choice(KB.METRIC_POOL.get(key, [1, 2, 3, 5, 8, 10]))
        return "{" + key + "}"

    try:
        rendered = tpl.format_map(_FormatMap(vals, _fallback))
    except (ValueError, IndexError, KeyError):
        return tpl
    return rendered


class _FormatMap(dict):
    """dict hỗ trợ __missing__ để tự điền placeholder lạ."""

    def __init__(self, data: dict, fallback) -> None:
        super().__init__(data)
        self._fallback = fallback

    def __missing__(self, key: str) -> str:
        return self._fallback(key, "", None, "", None)


# ============================================================ DỊCH TIÊU ĐỀ
def translate_title(role: str, level: str) -> str:
    table = {
        ("backend", "intern"): "Backend Developer Intern",
        ("backend", "junior"): "Backend Developer",
        ("backend", "middle"): "Mid-level Backend Engineer",
        ("backend", "senior"): "Senior Backend Engineer",
        ("backend", "lead"): "Backend Tech Lead / Architect",
        ("frontend", "intern"): "Frontend Developer Intern",
        ("frontend", "junior"): "Frontend Developer",
        ("frontend", "middle"): "Mid-level Frontend Engineer",
        ("frontend", "senior"): "Senior Frontend Engineer",
        ("frontend", "lead"): "Frontend Tech Lead / Architect",
        ("devops", "intern"): "DevOps Intern",
        ("devops", "junior"): "DevOps Engineer",
        ("devops", "middle"): "Site Reliability Engineer",
        ("devops", "senior"): "Senior DevOps / SRE",
        ("devops", "lead"): "DevOps Lead / Cloud Architect",
        ("data", "intern"): "Data Science / ML Intern",
        ("data", "junior"): "Data Analyst / ML Engineer",
        ("data", "middle"): "Data Engineer",
        ("data", "senior"): "Senior Data Scientist",
        ("data", "lead"): "Head of Data",
        ("ba", "intern"): "Business Analyst Intern",
        ("ba", "junior"): "Business Analyst",
        ("ba", "middle"): "Senior Business Analyst",
        ("ba", "senior"): "Lead Business Analyst",
        ("ba", "lead"): "Product Owner / Product Manager",
        ("qa", "intern"): "QA Intern",
        ("qa", "junior"): "QA Engineer",
        ("qa", "middle"): "Automation QA Engineer",
        ("qa", "senior"): "Senior SDET",
        ("qa", "lead"): "QA Lead / Test Architect",
        ("security", "intern"): "Cyber Security Intern",
        ("security", "junior"): "Security Analyst / SOC",
        ("security", "middle"): "Security Engineer",
        ("security", "senior"): "Senior Penetration Tester",
        ("security", "lead"): "Security Architect / Head of InfoSec",
        ("fullstack", "intern"): "Full-stack Developer Intern",
        ("fullstack", "junior"): "Full-stack Developer",
        ("fullstack", "middle"): "Full-stack Engineer",
        ("fullstack", "senior"): "Senior Full-stack Engineer",
        ("fullstack", "lead"): "Solution Architect",
    }
    return table[(role, level)]


def translate_school(s: str) -> str:
    return s.replace("Trường Đại học ", "").replace("Trường Cao đẳng ", "").replace("Học viện ", "")


def translate_major(m: str) -> str:
    table = {
        "Khoa học Máy tính": "Computer Science",
        "Kỹ thuật Phần mềm": "Software Engineering",
        "Lập trình phần mềm": "Software Programming",
    }
    return table.get(m, m)


# ============================================================ HEADINGS
HEADINGS = {
    "vi": {
        "objective": ["MỤC TIÊU NGHỀ NGHIỆP", "MỤC TIÊU", "TỐM TẮT"],
        "experience": ["KINH NGHIỆM LÀM VIỆC", "KINH NGHIỆM CHUYÊN MÔN", "CÔNG VIỆC ĐÃ LÀM"],
        "education": ["HỌC VẤN", "GIÁO DỤC", "TRÌNH ĐỘ"],
        "projects": ["DỰ ÁN CÁ NHÂN", "DỰ ÁN", "CÁC DỰ ÁN TIÊU BIỂU"],
        "skills": ["KỸ NĂNG", "KỸ NĂNG CHUYÊN MÔN", "NĂNG LỰC KỸ THUẬT"],
        "certificates": ["CHỨNG CHỈ", "CHỨNG CHỈ & CHỨNG NHẬN"],
        "honours": ["GIẢI THƯỞNG", "THÀNH TÍCH", "GIẢI THƯỞNG & THÀNH TÍCH"],
        "activities": ["HOẠT ĐỘNG", "HOẠT ĐỘNG XÃ HỘI"],
        "languages": ["NGÔN NGỮ", "NGOẠI NGỮ"],
        "soft": ["KỸ NĂNG MỀM"],
        "contact": ["THÔNG TIN LIÊN HỆ", "LIÊN HỆ"],
    },
    "en": {
        "objective": ["PROFESSIONAL SUMMARY", "OBJECTIVE", "SUMMARY"],
        "experience": ["WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE", "EMPLOYMENT"],
        "education": ["EDUCATION"],
        "projects": ["PERSONAL PROJECTS", "PROJECTS", "SELECTED PROJECTS"],
        "skills": ["TECHNICAL SKILLS", "SKILLS", "CORE COMPETENCIES"],
        "certificates": ["CERTIFICATIONS", "CERTIFICATES"],
        "honours": ["ACHIEVEMENTS", "AWARDS & HONOURS", "HONOURS"],
        "activities": ["ACTIVITIES", "EXTRACURRICULAR ACTIVITIES"],
        "languages": ["LANGUAGES"],
        "soft": ["SOFT SKILLS"],
        "contact": ["CONTACT INFORMATION", "CONTACT"],
    },
}


# ============================================================ CÁC LAYOUT
def render_markdown(p: dict) -> str:
    """Layout 1: Markdown có tiêu đề #, ## và bullet '- '."""
    h = HEADINGS[p["lang"]]
    L: list[str] = [f"# {p['name']}", f"**{p['title']}**", ""]
    c = p["contact"]
    L.append(f"- Email: {c['email']}  |  Phone: {c['phone']}  |  Location: {c['city']}")
    L.append(f"- GitHub: {c['github']}  |  LinkedIn: {c['linkedin']}")
    L.append("")

    if p["objective"]:
        L.append(f"## {h['objective'][0]}")
        L.append(p["objective"])
        L.append("")

    if p["experience"]:
        L.append(f"## {h['experience'][0]}")
        for e in p["experience"]:
            L.append(f"### {e['job_title']} | {e['company']}")
            L.append(f"`{e['period']}`")
            for b in e["bullets"]:
                L.append(f"- {b}")
            L.append("")

    if p["projects"]:
        L.append(f"## {h['projects'][0]}")
        for pr in p["projects"]:
            L.append(f"### {pr['name']}")
            L.append(f"- Role: {pr['role']} | {project_meta(pr, p['lang'])}")
            for b in pr["bullets"]:
                L.append(f"- {b}")
            L.append("")

    if p["education"]:
        L.append(f"## {h['education'][0]}")
        for ed in p["education"]:
            L.append(f"### {ed['school']}")
            L.append(f"- {ed['degree']}, Major: {ed['major']}")
            L.append(f"- {ed['start_year']} - {ed['end_year']} | GPA: {ed['gpa']}")
            L.append(f"- {ed['note']}")
        L.append("")

    L.append(f"## {h['skills'][0]}")
    L.append(f"- Technical: {', '.join(p['skills'])}")
    L.append(f"- Soft skills: {', '.join(p['soft_skills'])}")
    L.append("")

    if p["certificates"]:
        L.append(f"## {h['certificates'][0]}")
        for cert in p["certificates"]:
            L.append(f"- {cert}")
        L.append("")

    if p["honours"]:
        L.append(f"## {h['honours'][0]}")
        for a in p["honours"]:
            L.append(f"- {a}")
        L.append("")

    if p["activities"]:
        L.append(f"## {h['activities'][0]}")
        for a in p["activities"]:
            L.append(f"- {a}")
        L.append("")

    L.append(f"## {h['languages'][0]}")
    for lang, note in p["languages"]:
        L.append(f"- {lang}: {note}")

    return "\n".join(L)


def render_uppercase(p: dict) -> str:
    """Layout 2: chữ in hoa, block text dạng CV truyền thống, bullet '•'."""
    h = HEADINGS[p["lang"]]
    c = p["contact"]
    L: list[str] = []
    L.append(p["name"].upper())
    L.append(p["title"].upper())
    L.append(f"{c['phone']} | {c['email']} | {c['city']}")
    L.append(f"{c['github']} | {c['linkedin']}")
    L.append("=" * 60)
    L.append("")

    if p["objective"]:
        L.append(h["objective"][0])
        L.append(p["objective"])
        L.append("")

    for key, items in (
        ("experience", None), ("projects", None), ("education", None),
    ):
        if key == "experience" and p["experience"]:
            L.append(h["experience"][0])
            for e in p["experience"]:
                L.append(f"{e['job_title']} | {e['company']} | {e['period']}")
                for b in e["bullets"]:
                    L.append(f"• {b}")
                L.append("")
        if key == "projects" and p["projects"]:
            L.append(h["projects"][0])
            for pr in p["projects"]:
                L.append(f"{pr['name']} ({pr['role']}, {pr['period']})")
                L.append(f"• {project_meta(pr, p['lang'])}")
                for b in pr["bullets"]:
                    L.append(f"• {b}")
                L.append("")
        if key == "education" and p["education"]:
            L.append(h["education"][0])
            for ed in p["education"]:
                L.append(f"{ed['degree']} - {ed['major']}")
                L.append(f"{ed['school']}, {ed['start_year']} - {ed['end_year']}, GPA: {ed['gpa']}")
                L.append(f"{ed['note']}")
            L.append("")

    L.append(h["skills"][0])
    L.append(", ".join(p["skills"]))
    L.append(", ".join(p["soft_skills"]))
    L.append("")

    for key, pool in (("certificates", p["certificates"]), ("honours", p["honours"]),
                      ("activities", p["activities"])):
        if pool:
            L.append(h[key][0])
            for it in pool:
                L.append(f"• {it}")
            L.append("")

    L.append(h["languages"][0])
    for lang, note in p["languages"]:
        L.append(f"• {lang} - {note}")

    return "\n".join(L)


def render_bullets_star(p: dict) -> str:
    """Layout 3: tiêu đề dạng '**X**', bullet '*'."""
    h = HEADINGS[p["lang"]]
    c = p["contact"]
    L: list[str] = [
        p["name"],
        f"{p['title']} | {c['city']}",
        f"{c['phone']} • {c['email']} • {c['github']}",
        "",
    ]

    L.append(f"**{h['objective'][0]}**")
    L.append(p["objective"])
    L.append("")

    L.append(f"**{h['experience'][0]}**")
    for e in p["experience"]:
        L.append(f"*{e['job_title']}* - {e['company']} ({e['period']})")
        for b in e["bullets"]:
            L.append(f"  * {b}")
        L.append("")

    L.append(f"**{h['projects'][0]}**")
    for pr in p["projects"]:
        L.append(f"*{pr['name']}* ({pr['period']})")
        L.append(f"  * {project_meta(pr, p['lang'])}")
        for b in pr["bullets"]:
            L.append(f"  * {b}")
        L.append("")

    L.append(f"**{h['education'][0]}**")
    for ed in p["education"]:
        L.append(f"*{ed['school']}*")
        L.append(f"  {ed['degree']} - {ed['major']}, {ed['start_year']} - {ed['end_year']}, GPA: {ed['gpa']}")
        L.append(f"  {ed['note']}")
    L.append("")

    L.append(f"**{h['skills'][0]}**")
    L.append(f"* {', '.join(p['skills'])}")
    L.append(f"* {', '.join(p['soft_skills'])}")
    L.append("")

    for key, pool in (("certificates", p["certificates"]), ("honours", p["honours"])):
        if pool:
            L.append(f"**{h[key][0]}**")
            for it in pool:
                L.append(f"* {it}")
            L.append("")

    L.append(f"**{h['languages'][0]}**")
    for lang, note in p["languages"]:
        L.append(f"* {lang}: {note}")

    return "\n".join(L)


def render_compact(p: dict) -> str:
    """Layout 4: dạng bản gọn hai cột dùng dấu '|', giống CV TopCV / FlowCV."""
    h = HEADINGS[p["lang"]]
    c = p["contact"]
    L: list[str] = [
        p["name"].upper(),
        f"{p['title']}",
        f"{c['phone']}  {c['email']}  {c['city']}",
        f"{c['github']}  {c['linkedin']}",
        "",
    ]
    if p["objective"]:
        L += [h["objective"][1], p["objective"], ""]

    if p["skills"]:
        L += [h["skills"][-1], " | ".join(p["skills"]), ""]

    if p["experience"]:
        L.append(h["experience"][-1])
        for e in p["experience"]:
            L.append(f"{e['company']} | {e['job_title']} | {e['period']}")
            for b in e["bullets"]:
                L.append(f"  - {b}")
            L.append("")

    if p["projects"]:
        L.append(h["projects"][-1])
        for pr in p["projects"]:
            L.append(f"{pr['name']} | {pr['period']}")
            L.append(f"  - {project_meta(pr, p['lang'])}")
            for b in pr["bullets"]:
                L.append(f"  - {b}")
            L.append("")

    if p["education"]:
        L.append(h["education"][0])
        for ed in p["education"]:
            L.append(f"{ed['school']} | {ed['major']} | {ed['start_year']}-{ed['end_year']} | GPA {ed['gpa']}")
        L.append("")

    for key, pool in (("certificates", p["certificates"]), ("honours", p["honours"]),
                      ("activities", p["activities"])):
        if pool:
            L.append(h[key][0])
            L += [f"- {it}" for it in pool]
            L.append("")

    L.append(h["languages"][0])
    L += [f"- {lang}: {note}" for lang, note in p["languages"]]

    return "\n".join(L)


def render_plain(p: dict) -> str:
    """Layout 5: văn bản khối, ít bullet, gần với CV do người viết tay sắp xếp."""
    h = HEADINGS[p["lang"]]
    c = p["contact"]
    L: list[str] = [
        p["name"],
        p["title"],
        f"{c['phone']} | {c['email']} | {c['city']} | {c['github']}",
        "",
        f"{h['objective'][1]}",
        p["objective"],
        "",
    ]
    if p["experience"]:
        L.append(h["experience"][1])
        for e in p["experience"]:
            L.append(f"{e['job_title']}, {e['company']}, {e['period']}")
            L.append(" ".join(e["bullets"]))
            L.append("")

    if p["projects"]:
        L.append(h["projects"][0])
        for pr in p["projects"]:
            L.append(f"{pr['name']} ({pr['period']})")
            L.append(project_meta(pr, p["lang"]) + ".")
            L.append(" ".join(pr["bullets"]))
            L.append("")

    if p["education"]:
        L.append(h["education"][0])
        for ed in p["education"]:
            L.append(f"{ed['school']}, {ed['major']}, {ed['start_year']} - {ed['end_year']}, GPA: {ed['gpa']}. {ed['note']}.")
        L.append("")

    L.append(h["skills"][0])
    L.append(", ".join(p["skills"]) + ". " + ", ".join(p["soft_skills"]) + ".")
    L.append("")

    for key, pool in (("certificates", p["certificates"]), ("honours", p["honours"])):
        if pool:
            L.append(h[key][0])
            L.append("; ".join(pool) + ".")
            L.append("")

    L.append(h["languages"][0])
    L.append("; ".join(f"{lang}: {note}" for lang, note in p["languages"]) + ".")

    return "\n".join(L)


def render_outline(p: dict) -> str:
    """Layout 6: tiêu đề có gạch dưới, phân cấp rõ, pha trộn bullet các kiểu."""
    h = HEADINGS[p["lang"]]
    c = p["contact"]
    L: list[str] = [p["name"], f"{p['title']}", ""]
    L.append(f"Email: {c['email']}")
    L.append(f"Phone: {c['phone']}")
    L.append(f"Address: {c['city']}")
    L.append(f"GitHub: {c['github']}")
    L.append(f"LinkedIn: {c['linkedin']}")
    L.append("")
    L.append("_" * 50)
    L.append("")

    def head(t: str) -> None:
        L.append(t)
        L.append("~" * len(t))

    head(h["objective"][-1])
    L.append(p["objective"])
    L.append("")

    if p["experience"]:
        head(h["experience"][0])
        for e in p["experience"]:
            L.append(f"{e['job_title']} - {e['company']} ({e['period']})")
            for i, b in enumerate(e["bullets"]):
                L.append(f"  {i + 1}. {b}")
            L.append("")

    if p["projects"]:
        head(h["projects"][0])
        for pr in p["projects"]:
            L.append(f"{pr['name']} | {pr['role']} | {pr['period']}")
            L.append(f"  {project_meta(pr, p['lang'])}")
            for i, b in enumerate(pr["bullets"]):
                L.append(f"  {i + 1}. {b}")
            L.append("")

    if p["education"]:
        head(h["education"][0])
        for ed in p["education"]:
            L.append(f"{ed['school']}")
            L.append(f"  {ed['degree']}, {ed['major']}")
            L.append(f"  {ed['start_year']} - {ed['end_year']} | GPA {ed['gpa']}")
            L.append(f"  {ed['note']}")
        L.append("")

    head(h["skills"][0])
    for s in p["skills"]:
        L.append(f"  + {s}")
    L.append("")

    for key, pool in (("certificates", p["certificates"]), ("honours", p["honours"]),
                      ("activities", p["activities"])):
        if pool:
            head(h[key][0])
            for it in pool:
                L.append(f"  - {it}")
            L.append("")

    head(h["languages"][0])
    for lang, note in p["languages"]:
        L.append(f"  - {lang}: {note}")

    return "\n".join(L)


def project_meta(pr: dict, lang: str) -> str:
    """Dòng metadata của project: thời gian - nhóm - tech - repo.

    Bắt buộc mọi layout đều phải in dòng này, vì nhãn silver của project chứa
    đúng các trường ở đây. Thiếu nó -> nhãn không suy ra được từ văn bản ->
    model học đoán bừa thay vì trích xuất.
    """
    parts = [pr["period"]]
    if pr.get("team_size"):
        parts.append(f"Nhóm: {pr['team_size']}" if lang == "vi" else f"Team: {pr['team_size']}")
    if pr.get("tech_stack"):
        parts.append("Công nghệ: " + ", ".join(pr["tech_stack"]) if lang == "vi"
                     else "Tech: " + ", ".join(pr["tech_stack"]))
    if pr.get("github"):
        parts.append(pr["github"])
    return " | ".join(parts)


LAYOUTS = [
    render_markdown,
    render_uppercase,
    render_bullets_star,
    render_compact,
    render_plain,
    render_outline,
]
LAYOUT_NAMES = ["markdown", "uppercase", "bullets_star", "compact", "plain", "outline"]


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


# ============================================================ MAIN
def main() -> int:
    ap = argparse.ArgumentParser(description="Sinh CV tổng hợp theo ma trận Role x Level")
    ap.add_argument("--seed", type=int, default=20240517, help="seed ngẫu nhiên (mặc định cố định)")
    ap.add_argument("--force", action="store_true", help="ghi đè file synthetic đã tồn tại")
    ap.add_argument("--clean", action="store_true",
                    help="xóa toàn bộ file syn_*.txt cũ trước khi sinh (chống trùng tên)")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    TXT_DIR.mkdir(parents=True, exist_ok=True)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)

    # ---- dọn file synthetic cũ (tránh tích tụ từ các lần chạy trước) ----
    stale = sorted(TXT_DIR.glob("syn_*.txt"))
    if stale:
        for f in stale:
            f.unlink()
        print(f"Đã xóa {len(stale)} file syn_*.txt cũ.")
    if args.force:
        print("(áp dụng --force: sẽ ghi lại toàn bộ file synthetic)")

    # ---- đếm CV thật theo ô ----
    real_count: dict[tuple[str, str], int] = defaultdict(int)
    real_files: list[str] = []
    if LABELS_JSON.exists():
        labels = json.loads(LABELS_JSON.read_text(encoding="utf-8"))
        for fname, meta in labels.items():
            role, level = meta["role"], meta["level"]
            if role == "OTHER":
                continue   # CV không thuộc ngành IT -> không đưa vào ma trận
            if role not in MATRIX or level not in LEVELS:
                continue
            real_count[(role, level)] += 1
            real_files.append(fname)
    else:
        print(f"[CẢNH BÁO] Không thấy {LABELS_JSON}, coi như chưa có CV thật nào.")

    print(f"Ma trận mục tiêu: {TOTAL_CELLS} ô")
    print(f"CV thật dùng được: {len(real_files)}\n")

    # ---- tính nhu cầu synthetic ----
    need: dict[tuple[str, str], int] = {}
    total_synth = 0
    print(f"{'Role / Level':<26}{'Target':>8}{'Real':>7}{'Sinh ra':>9}")
    print("-" * 50)
    for role, counts in MATRIX.items():
        for level, target in zip(LEVELS, counts):
            have = real_count[(role, level)]
            short = max(0, target - have)
            need[(role, level)] = short
            total_synth += short
            print(f"{role + '/' + level:<26}{target:>8}{have:>7}{short:>9}")
    print("-" * 50)
    print(f"{'TỔNG SYNTHETIC':<26}{TOTAL_CELLS:>8}{len(real_files):>7}{total_synth:>9}\n")

    # ---- sinh ----
    manifest: list[dict] = []
    per_cell: dict[str, int] = defaultdict(int)
    synthetic_profiles: dict[str, dict] = {}
    idx_global = 0

    for role, counts in MATRIX.items():
        for level, target in zip(LEVELS, counts):
            for i in range(need[(role, level)]):
                idx_global += 1
                p = build_profile(rng, role, level, idx_global)

                # chọn layout ngẫu nhiên nhưng bảo đảm đa dạng
                li = (idx_global + role.__len__() + level.__len__()) % len(LAYOUTS)
                text = clean_text(LAYOUTS[li](p))

                # ---- điều chỉnh kích thước về khoảng 1.5KB - 7KB ----
                text = fit_size(text, p, li, rng)

                slug_name = slug(p["name"])
                fname = f"syn_{role}_{level}_{per_cell[f'{role}_{level}'] + 1:02d}_{slug_name}.txt"
                (TXT_DIR / fname).write_text(text, encoding="utf-8")

                per_cell[f"{role}_{level}"] += 1
                manifest.append({
                    "file": fname,
                    "role": role,
                    "level": level,
                    "lang": p["lang"],
                    "layout": LAYOUT_NAMES[li],
                    "bytes": len(text.encode("utf-8")),
                })
                # Lưu luôn profile gốc -> nhãn silver cho CV tổng hợp là chính xác
                # tuyệt đối, không cần trích xuất lại từ văn bản.
                synthetic_profiles[fname] = p

    # ---- tổng kết ----
    SYNTH_MANIFEST.write_text(
        json.dumps({"manifest": manifest, "seed": args.seed}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    SYNTH_PROFILES.write_text(
        json.dumps(synthetic_profiles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lang_count = defaultdict(int)
    layout_count = defaultdict(int)
    for m in manifest:
        lang_count[m["lang"]] += 1
        layout_count[m["layout"]] += 1
    sizes = sorted(m["bytes"] for m in manifest)

    print(f"Đã sinh {len(manifest)} file synthetic.")
    print(f"  Ngôn ngữ      : VI={lang_count['vi']} ({lang_count['vi']/max(1,len(manifest)):.0%}), EN={lang_count['en']} ({lang_count['en']/max(1,len(manifest)):.0%})")
    print("  Layout        : " + ", ".join(f"{k}={v}" for k, v in sorted(layout_count.items())))
    print(f"  Kích thước    : min={sizes[0]}B, median={sizes[len(sizes)//2]}B, max={sizes[-1]}B")

    total_txt = len(list(TXT_DIR.glob("*.txt")))
    print(f"\n  TỔNG file .txt trong {TXT_DIR.name}/: {total_txt}")
    print(f"  Manifest      : {SYNTH_MANIFEST}")
    return 0


def fit_size(text: str, p: dict, layout_idx: int, rng: random.Random) -> str:
    """Đảm bảo kích thước nằm trong khoảng hợp lý; bổ sung chi tiết nếu quá ngắn."""
    # quá dài -> rút bớt bullet (giữ phần cốt lõi của CV)
    guard = 0
    while len(text.encode("utf-8")) > MAX_BYTES and guard < 12:
        if p["projects"] and any(len(x["bullets"]) > 2 for x in p["projects"]):
            for x in p["projects"]:
                if len(x["bullets"]) > 2:
                    x["bullets"].pop()
                    break
        elif p["experience"] and any(len(x["bullets"]) > 3 for x in p["experience"]):
            for x in p["experience"]:
                if len(x["bullets"]) > 3:
                    x["bullets"].pop()
                    break
        else:
            break
        text = clean_text(LAYOUTS[layout_idx](p))
        guard += 1

    # quá ngắn -> bổ sung dự án / chứng chỉ / thành tích hợp lệ
    guard = 0
    vi = p["lang"] == "vi"
    while len(text.encode("utf-8")) < MIN_BYTES and guard < 8:
        if not p["projects"]:
            p["projects"].append({
                "name": rng.choice(KB.PROJECT_NAMES_VI if vi else KB.PROJECT_NAMES_EN),
                "role": p["title"],
                "start_year": 2024, "end_year": 2025,
                "period": "01/2024 - 06/2025",
                "domain": p["domain"],
                "module": rng.choice(KB.ROLE_BANKS["backend"]["vi"]["modules"]),
                "tech": p["skills"][0],
                "github": p["contact"]["github"],
                "team_size": rng.randint(1, 5),
                "bullets": [],
            })
        else:
            p["projects"].append({
                **p["projects"][-1],
                "name": rng.choice(KB.PROJECT_NAMES_VI if vi else KB.PROJECT_NAMES_EN),
                "start_year": 2023,
                "end_year": 2024,
                "period": "03/2023 - 11/2024",
                "bullets": [],
            })
        newp = p["projects"][-1]
        newp["bullets"] = [
            (f"Phát triển tính năng {newp['module']} trên nền tảng {newp['tech']} cho {newp['domain']}."
             if vi else
             f"Built {newp['module']} features on {newp['tech']} for the {newp['domain']}."),
            (f"Áp dụng kiểm thử tự động và code review để bảo đảm chất lượng mã nguồn."
             if vi else
             "Added automated tests and code review to maintain source quality."),
        ]
        if len(p["certificates"]) < 4:
            p["certificates"].append(rng.choice(KB.CERTS_VN if vi else KB.CERTS_EN))
        if len(p["honours"]) < 4:
            p["honours"].append(rng.choice(KB.ACHIEVEMENTS_VN if vi else KB.ACHIEVEMENTS_EN))
        if not p["activities"] and vi:
            p["activities"] = rng.sample(KB.ACTIVITIES_VN, k=1)
        text = clean_text(LAYOUTS[layout_idx](p))
        guard += 1

    return text


if __name__ == "__main__":
    sys.exit(main())
