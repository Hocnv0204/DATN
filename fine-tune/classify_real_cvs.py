#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
classify_real_cvs.py
====================
Giai đoạn 2a - Tự động gán nhãn Role x Level cho các CV thật đã trích xuất.

Chiến lược phân loại (theo thứ tự ưu tiên, tránh nhiễu từ CV thật của sinh viên):

ROLE
  1. "fullstack"/"cross-functional" chỉ được chọn khi CV tự nêu rõ
     fullstack / full-stack / web developer / embedded / IoT / solution architect.
     Nếu không, fullstack bị loại khỏi cuộc đua (tránh việc mọi CV có cả React lẫn
     Java đều bị gán nhầm là fullstack).
  2. Ngoài ra: chấm điểm 8 nhóm ngành theo keyword, ưu tiên điểm ở phần đầu CV
     (tiêu đề + mục tiêu nghề nghiệp) vì đó là chỗ người ứng tuyển tự khai báo vị trí.

LEVEL
  1. Tiêu đề/summary có nhãn seniority rõ (Intern, Fresher, Junior, Mid, Senior,
     Lead, Manager, Architect) -> lấy nhãn đó.
  2. Có dấu hiệu sinh viên mạnh (sinh viên, thực tập, năm cuối, đồ án...) và
     không có nhãn seniority cao hơn -> intern.
  3. Nếu không -> suy ra từ số năm kinh nghiệm lớn nhất tìm được trong CV.

Output: fine-tune/_stage/real_labels.json
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import unicodedata
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
TXT_DIR = ROOT / "cv-analysis-service" / "cv_texts"
STAGE_DIR = HERE / "_stage"

HEAD_CHARS = 1200          # vùng "tiêu đề + mục tiêu" - tín hiệu mạnh nhất về vị trí
READ_CHARS = 6000          # vùng đọc đầy đủ - tín hiệu về stack + kinh nghiệm

# --------------------------------------------------------------------- role keywords
# w_head: điểm khi xuất hiện ở phần đầu CV; w_body: điểm ở thân CV
ROLE_KEYWORDS: dict[str, list[tuple[str, float, float]]] = {
    "backend": [
        ("spring boot", 3.5, 3.0), ("springboot", 3.5, 3.0), ("java", 2.0, 1.5),
        ("j2ee", 3.0, 2.5), ("python", 1.2, 1.0), ("django", 3.0, 2.5),
        ("fastapi", 3.2, 2.8), ("flask", 2.5, 2.0), ("node.js", 2.0, 1.5),
        ("nodejs", 2.0, 1.5), ("express", 2.0, 1.5), ("nestjs", 3.2, 2.8),
        ("golang", 3.5, 3.0), (".net", 3.0, 2.5), ("dotnet", 3.0, 2.5),
        ("c#", 2.0, 1.5), ("laravel", 3.0, 2.5), ("symfony", 3.0, 2.5),
        ("php", 1.5, 1.2), ("restful", 1.5, 1.2), ("rest api", 1.5, 1.2),
        ("microservice", 1.5, 1.2), ("graphql", 2.5, 2.2), ("jpa", 2.5, 2.0),
        ("hibernate", 2.5, 2.0), ("backend", 3.0, 1.2), ("back-end", 3.0, 1.2),
        ("entity framework", 2.5, 2.0),
    ],
    "frontend": [
        ("react", 2.5, 1.8), ("reactjs", 2.5, 1.8), ("react native", 3.5, 3.0),
        ("next.js", 3.0, 2.5), ("nextjs", 3.0, 2.5), ("vue", 2.2, 1.8),
        ("vuejs", 3.0, 2.5), ("angular", 3.0, 2.5), ("svelte", 2.5, 2.0),
        ("flutter", 3.5, 3.0), ("swift", 2.5, 2.0), ("android", 1.5, 1.2),
        ("css", 1.5, 1.2), ("sass", 2.0, 1.5), ("tailwind", 2.5, 2.0),
        ("redux", 2.0, 1.5), ("frontend", 3.5, 1.2), ("front-end", 3.5, 1.2),
        ("ui/ux", 1.5, 1.2), ("figma", 2.0, 1.5), ("webpack", 2.0, 1.5),
        ("ant design", 2.0, 1.5), ("material-ui", 2.5, 2.0),
    ],
    "devops": [
        ("devops", 4.0, 3.5), ("docker", 2.5, 2.0), ("kubernetes", 3.5, 3.0),
        ("k8s", 3.0, 2.5), ("terraform", 3.5, 3.0), ("ansible", 3.2, 2.8),
        ("jenkins", 3.0, 2.5), ("gitlab ci", 3.0, 2.5), ("github actions", 3.0, 2.5),
        ("ci/cd", 3.5, 3.0), ("cicd", 3.5, 3.0), ("aws", 2.5, 2.0),
        ("gcp", 2.5, 2.0), ("eks", 3.0, 2.5), ("ec2", 3.0, 2.5),
        ("helm", 2.5, 2.0), ("prometheus", 3.0, 2.5), ("grafana", 3.0, 2.5),
        ("site reliability", 4.0, 3.5), ("haproxy", 2.5, 2.0), ("argocd", 3.0, 2.5),
        ("istio", 3.0, 2.5), ("infrastructure as code", 3.0, 2.5),
        ("cloud", 1.2, 1.0), ("nginx", 2.0, 1.5),
    ],
    "data": [
        ("machine learning", 3.5, 3.0), ("deep learning", 3.5, 3.0),
        ("pytorch", 3.5, 3.0), ("tensorflow", 3.5, 3.0), ("scikit-learn", 3.2, 2.8),
        ("nlp", 3.2, 2.8), ("computer vision", 3.0, 2.8), ("opencv", 3.0, 2.5),
        ("mlops", 4.0, 3.5), ("data engineer", 4.0, 3.5),
        ("data scientist", 4.0, 3.5), ("data analyst", 4.0, 3.5),
        ("data analysis", 3.5, 3.0), ("spark", 3.5, 3.0), ("hadoop", 3.5, 3.0),
        ("airflow", 3.0, 2.5), ("dbt", 3.0, 2.5), ("power bi", 3.5, 3.0),
        ("powerbi", 3.5, 3.0), ("tableau", 3.5, 3.0), ("looker", 3.0, 2.5),
        ("pandas", 2.5, 2.0), ("llm", 2.5, 2.0), ("langchain", 3.5, 3.0),
        ("transformers", 3.0, 2.5), ("hugging face", 3.0, 2.5),
        ("xgboost", 3.0, 2.5), ("keras", 3.0, 2.5), ("etl", 2.5, 2.0),
        ("data warehouse", 3.5, 3.0),
    ],
    "ba": [
        ("business analyst", 4.5, 4.0), ("business analysis", 4.0, 3.5),
        ("product owner", 4.5, 4.0), ("scrum master", 4.5, 4.0),
        ("product manager", 4.0, 3.5), ("phân tích nghiệp vụ", 4.0, 3.5),
        ("nghiệp vụ", 2.5, 2.0), ("brd", 3.5, 3.0), ("srs", 3.5, 3.0),
        ("bpmn", 3.5, 3.0), ("use case", 3.0, 2.5), ("user stor", 3.2, 2.8),
        ("acceptance criteria", 3.2, 2.8), ("product roadmap", 3.5, 3.0),
        ("requirement", 2.0, 1.5), ("stakeholder", 3.0, 2.5), ("jira", 1.5, 1.2),
        ("confluence", 2.0, 1.5), ("agile", 1.5, 1.2), ("scrum", 1.5, 1.2),
    ],
    "qa": [
        ("quality assurance", 4.0, 3.5), ("tester", 3.5, 3.0),
        ("kiểm thử", 4.0, 3.5), ("test case", 3.2, 2.8), ("test plan", 3.2, 2.8),
        ("selenium", 3.5, 3.0), ("cypress", 3.5, 3.0), ("playwright", 3.5, 3.0),
        ("appium", 3.2, 2.8), ("jmeter", 3.0, 2.5), ("manual test", 3.5, 3.0),
        ("automation test", 3.2, 2.8), ("regression test", 3.0, 2.5),
        ("smoke test", 3.0, 2.5), ("integration test", 2.8, 2.4),
        ("unit test", 2.5, 2.0), ("robot framework", 3.2, 2.8),
        ("junit", 2.8, 2.4), ("nunit", 2.8, 2.4), ("defect", 1.5, 1.2),
    ],
    "security": [
        ("cybersecurity", 4.0, 3.5), ("an ninh mạng", 4.0, 3.5),
        ("pentest", 4.0, 3.5), ("penetration test", 4.0, 3.5),
        ("vulnerability", 3.0, 2.5), ("soc analyst", 4.0, 3.5),
        ("siem", 3.5, 3.0), ("splunk", 3.5, 3.0), ("wazuh", 3.5, 3.0),
        ("firewall", 3.0, 2.5), ("kali linux", 3.2, 2.8), ("burp suite", 3.2, 2.8),
        ("owasp", 3.5, 3.0), ("nmap", 3.0, 2.5), ("metasploit", 3.2, 2.8),
        ("incident response", 3.5, 3.0), ("sysadmin", 3.5, 3.0),
        ("system administrator", 4.0, 3.5), ("quản trị hệ thống", 4.0, 3.5),
        ("active directory", 3.0, 2.5), ("ccna", 3.5, 3.0), ("bảo mật", 2.5, 2.0),
        ("ldap", 2.5, 2.0), ("vpn", 2.0, 1.5),
    ],
}

# "fullstack" là nhãn thỏa hiệp: chỉ dùng khi có tín hiệu tường minh
FULLSTACK_EXPLICIT = [
    ("fullstack", 4.5), ("full-stack", 4.5), ("full stack", 4.5),
    ("web developer", 3.0), ("mern", 3.0), ("mean", 2.5),
    ("embedded", 3.5), ("iot", 3.5), ("arduino", 3.5), ("raspberry pi", 3.5),
    ("stm32", 3.5), ("esp32", 3.2), ("solution architect", 4.0),
]
# tín hiệu ngành khác trong nhóm Fullstack & Khác (C++, ngôn ngữ hệ thống...)
FULLSTACK_WEAK = [("c++", 1.5), ("c/c++", 2.0), ("objective-c", 2.0), ("qt", 2.0)]

# ---------------------------------------------------------------------------
# Nhận diện chức danh người ứng tuyển tự khai báo.
# Đây là tín hiệu mạnh nhất: đầu CV (tiêu đề + mục tiêu) là nơi người ứng tuyển
# ghi đúng vị trí mình ứng tuyển, đáng tin hơn việc suy đoán từ toàn bộ keyword.
TITLE_CHARS = 400        # vùng tiêu đề thật sự (tên + chức danh + mục tiêu ngắn)
ROLE_TITLE_PATTERNS: list[tuple[re.Pattern, str, float]] = [
    # ---- đặc biệt ----
    (re.compile(r"\bfull[- ]?stack\b"), "fullstack", 6.5),
    (re.compile(r"\bsolution architect\b|\bkien truc su\b"), "fullstack", 6.5),
    (re.compile(r"\b(embedded|iot)\b.*\b(engineer|developer)\b"), "fullstack", 6.0),
    (re.compile(r"\b(arduino|raspberry pi|stm32|esp32|freertos)\b"), "fullstack", 5.5),
    # ---- ngành chức danh rõ ràng ----
    (re.compile(r"\b(mobile|android|ios|flutter|react native)\b.*\b(developer|engineer)\b"), "frontend", 6.0),
    (re.compile(r"\bflutter developer\b|\breact native developer\b"), "frontend", 6.5),
    (re.compile(r"\b(front[- ]?end|frontend)\b.*\b(developer|engineer|intern|fresher)\b"), "frontend", 6.0),
    (re.compile(r"\b(ui|ux|web) designer\b"), "frontend", 5.5),
    (re.compile(r"\b(back[- ]?end|backend)\b.*\b(developer|engineer|intern|fresher)\b"), "backend", 6.0),
    (re.compile(r"\b(java|php|dotnet|net|python|golang|node) (backend )?developer\b"), "backend", 5.5),
    # ---- devops: PHẢI đi kèm chức danh, không nhận "DevOps" trong mục kỹ năng ----
    (re.compile(r"\bdevops (engineer|developer|architect)\b"), "devops", 6.5),
    (re.compile(r"\bsre\b.*\b(engineer|specialist)\b|\bsite reliability engineer\b"), "devops", 6.5),
    (re.compile(r"\bcloud (engineer|architect|devops)\b"), "devops", 6.0),
    (re.compile(r"\b(platform|infrastructure) (engineer|architect)\b"), "devops", 5.5),
    # ---- data / ai ----
    (re.compile(r"\b(machine learning|ml|ai|artificial intelligence)\b.*\b(engineer|developer|scientist)\b"), "data", 6.0),
    (re.compile(r"\bdata (scientist|analyst|engineer)\b"), "data", 6.0),
    # ---- BA / Product ----
    (re.compile(r"\b(business analyst|product owner|product manager|scrum master)\b"), "ba", 7.0),
    # ---- QA ----
    (re.compile(r"\b(qa|qc|quality assurance)\b.*\b(engineer|tester|analyst|specialist)\b"), "qa", 6.5),
    (re.compile(r"\b(test automation|automation) (engineer|tester)\b"), "qa", 6.5),
    # ---- Security / SysAdmin ----
    (re.compile(r"\b(security|cyber ?security|pentester|soc analyst)\b.*\b(engineer|analyst|specialist)\b"), "security", 6.5),
    (re.compile(r"\b(system|network|it|infrastructure) (admin|administrator)\b"), "security", 7.0),
    (re.compile(r"\bsysadmin\b"), "security", 6.5),
    (re.compile(r"\bhelpdesk\b.*\b(intern|student|support|technician)\b"), "security", 6.0),
]

# --------------------------------------------------------------------- level
SENIORITY_ORDER = ["intern", "junior", "middle", "senior", "lead"]

# (mẫu regex, level) - CHỈ kiểm tra trên phần tiêu đề CV.
# Lưu ý: không dùng \blead\b trần vì CV sinh viên hay viết "Team Leader" trong
# mục dự án -> sẽ bị nâng nhầm lên senior. Phải là cụm chức danh thật.
TITLE_LEVEL_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(engineering|technical|it|delivery|product|project) manager\b"), "lead"),
    (re.compile(r"\bscrum master\b"), "lead"),
    (re.compile(r"\bproduct owner\b"), "lead"),
    (re.compile(r"\b(head of|director of|cto|cio)\b"), "lead"),
    (re.compile(r"\bteam lead\b|\btech(nical)? lead\b|\blead developer\b|\blead engineer\b"), "senior"),
    (re.compile(r"\bsenior\b|\bsr\.\b|\bsnr\b|\bsenior architect\b"), "senior"),
    (re.compile(r"\bjunior\b|\bjr\.\b"), "junior"),
    (re.compile(r"\bmid[- ]?level\b|\bmiddle\b"), "middle"),
    (re.compile(r"\b(intern|internship)\b"), "intern"),
    (re.compile(r"\bfresher\b|\bfresh(er| graduate)\b"), "intern"),
    (re.compile(r"\bthuc tap\b|\bthuc tap sinh\b"), "intern"),
]
# mức tối thiểu để tin tín hiệu tiêu đề (tránh 1 từ trùng ngẫu nhiên)
TITLE_LEVEL_MIN_HITS = 1

# tín hiệu "đang là sinh viên"
STUDENT_PATTERNS = [
    r"sinh vien", r"thuc tap", r"do an chuyen nganh", r"do an tot nghiep",
    r"nam cuoi", r"nam 3", r"nam 4", r"năm cuối", r"năm 3", r"năm 4",
    r"final[- ]year", r"third[- ]year", r"fourth[- ]year", r"undergraduate",
    r"college student", r"university student", r"student at", r"pursuing",
    r"expected graduation", r"graduating", r"hoc sinh", r"học sinh",
]
STUDENT_RE = re.compile("|".join(STUDENT_PATTERNS))

# số năm kinh nghiệm: "3 năm", "5+ years", "over 4 years", "2 years of experience"
YEARS_RE = re.compile(
    r"(\d{1,2})\s*(?:\+|-\s*\d{1,2}\s*)?\s*(?:năm|year)", re.IGNORECASE
)


def strip_accents(text: str) -> str:
    t = text.lower()
    t = t.replace("–", "-").replace("—", "-").replace("’", "'")
    t = unicodedata.normalize("NFD", t)
    return "".join(ch for ch in t if unicodedata.category(ch) != "Mn")


def score_roles(head: str, body: str) -> dict[str, float]:
    """head/body đã strip dấu. Điểm = max(head_weight, body_weight) cho mỗi từ khoá."""
    scores: dict[str, float] = {}
    for role, kws in ROLE_KEYWORDS.items():
        total = 0.0
        for kw, w_head, w_body in kws:
            k = strip_accents(kw)
            if k in head:
                total += w_head
            elif k in body:
                total += w_body
        scores[role] = total
    return scores


def score_fullstack(head: str, body: str) -> float:
    score = 0.0
    for kw, w in FULLSTACK_EXPLICIT:
        if strip_accents(kw) in head:
            score += w
        elif strip_accents(kw) in body:
            score += w * 0.8
    for kw, w in FULLSTACK_WEAK:
        if strip_accents(kw) in head:
            score += w
        elif strip_accents(kw) in body:
            score += w * 0.6
    return score


def pick_role(head: str, body: str) -> tuple[str, dict]:
    """head/body đã strip dấu. Trả về (role, thông tin chẩn đoán)."""
    info: dict = {}

    # 1) chức danh người ứng tuyển tự khai ở tiêu đề - tín hiệu đáng tin nhất
    title_hits: list[tuple[str, float, str]] = []
    for pat, role, w in ROLE_TITLE_PATTERNS:
        m = pat.search(head)
        if m:
            title_hits.append((role, w, m.group(0)[:28]))
    # chỉ xét chức danh trong vùng tiêu đề thật sự
    title_zone = head[:TITLE_CHARS]
    title_hits: list[tuple[str, float, str]] = []
    for pat, role, w in ROLE_TITLE_PATTERNS:
        m = pat.search(title_zone)
        if m:
            title_hits.append((role, w, m.group(0)[:28]))
    if title_hits:
        title_hits.sort(key=lambda x: -x[1])
        info["title_hint"] = title_hits[0][2]

    scores = score_roles(head, body)
    fs = score_fullstack(head, body)
    top_special = max(scores.values())

    if title_hits:
        t_role, t_w, t_txt = title_hits[0]
        # chức danh tiêu đề rõ ràng -> tin ngay
        if t_w >= 6.0:
            info["role_signal"] = "title"
            return t_role, info
        # chức danh vừa đủ -> chỉ chấp nhận nếu bằng chứng thân CV không phản đối
        if t_role != "fullstack" and scores.get(t_role, 0) >= top_special * 0.5:
            info["role_signal"] = "title+kw"
            return t_role, info

    if fs >= 4.0 and fs >= top_special * 0.9:
        scores["fullstack"] = fs
        best = "fullstack"
    else:
        scores["fullstack"] = round(fs, 1)
        best = max(scores, key=lambda k: scores[k])
    info["role_signal"] = "keyword"
    info["role_scores"] = {k: round(v, 1) for k, v in sorted(scores.items(), key=lambda x: -x[1])}
    return best, info


def pick_level(head: str, body: str) -> tuple[str, dict]:
    """head/body đã strip dấu."""
    info: dict = {}

    # 1) nhãn seniority trong TIÊU ĐỀ CV (chỉ 600 ký tự đầu)
    title = head[:TITLE_CHARS]
    found = [lvl for pat, lvl in TITLE_LEVEL_PATTERNS if pat.search(title)]
    if found and len(found) >= TITLE_LEVEL_MIN_HITS:
        # nếu có cả intern và nhãn cao hơn -> ưu tiên nhãn cao hơn, trừ khi CV
        # ghi rõ "intern" ở tiêu đề (dấu hiệu mạnh nhất của sinh viên)
        order = SENIORITY_ORDER
        best = max(found, key=lambda x: order.index(x))
        if "intern" in found and best in ("senior", "lead"):
            # "Senior" chỉ xuất hiện trong tiêu đề mà CV không có dấu hiệu
            # kinh nghiệm thực tế -> coi như intern (hầu hết CV này là sinh viên)
            if not re.search(r"\d\s*(?:\+|-\s*\d\s*)?\s*(?:năm|year)", title):
                best = "intern"
        info["signal"] = "title:" + best
        return best, info

    # 2) tín hiệu sinh viên
    if STUDENT_RE.search(head) or STUDENT_RE.search(body[:2500]):
        info["signal"] = "student"
        return "intern", info

    # 3) suy từ số năm kinh nghiệm
    years = [int(m.group(1)) for m in YEARS_RE.finditer(body)]
    years = [y for y in years if 0 <= y <= 30]
    if years:
        top = max(years)
        info["signal"] = f"years={top}"
        if top <= 1:
            return "intern", info
        if top <= 3:
            return "junior", info
        if top <= 6:
            return "middle", info
        if top <= 9:
            return "senior", info
        return "lead", info

    info["signal"] = "default"
    return "junior", info


# ---------------------------------------------------------------------------
# OVERRIDES: nhãn role/level đã được kiểm tra thủ công cho từng file thật.
# Lý do: keyword scoring không đủ tin cậy ở một số CV (tiêu đề chung chung,
# OCR nhiễu, hoặc CV viết tắt nghề nghiệp). Bảng này là "đáp án đúng" có thể
# kiểm chứng, luôn thắng phần tự động.
#   key = tên file trong cv_texts/, value = (role, level, lý do)
OVERRIDES: dict[str, tuple[str, str, str]] = {
    # --- ảnh OCR: các CV không có chức danh rõ ở đầu file ---
    "real_img_27.txt": ("data", "intern", "Machine Learning Engineer Intern"),
    "real_img_28.txt": ("data", "intern", "AI/CV - OpenCV, YOLO"),
    "real_img_30.txt": ("data", "intern", "AI Engineer - LLM, retrieval, Text-to-SQL"),
    "real_img_03.txt": ("security", "junior", "Network & IT Infrastructure / pfSense / Active Directory"),
    "real_img_04.txt": ("backend", "intern", "Backend focus (Spring Boot)"),
    "real_img_09.txt": ("backend", "intern", "Backend Developer, Team Leader trong đồ án"),
    "real_img_12.txt": ("backend", "intern", "Java/Spring Boot; 'Full-stack' chỉ là định hướng"),
    "real_img_14.txt": ("backend", "junior", "Backend Java/Spring"),
    "real_img_16.txt": ("backend", "intern", "Backend - Node.js/NestJS"),
    "real_img_20.txt": ("backend", "intern", "Backend NestJS/PostgreSQL"),
    "real_img_21.txt": ("backend", "junior", "Backend + Docker/K8s (DevOps là phụ trợ)"),
    "real_img_02.txt": ("backend", "intern", "Backend Java/Spring Boot, tìm internship"),
    "real_img_25.txt": ("fullstack", "junior", "React + Node, Web Developer"),
    "real_img_29.txt": ("fullstack", "intern", "Full-stack Web (React + Spring Boot)"),
    # --- PDF ---
    "real_pdf_04.txt": ("backend", "intern", "Tiêu đề 'Backend Developer', học bổ sung bằng full-stack"),
    "real_pdf_05.txt": ("backend", "junior", "Mục tiêu: backend development"),
    "real_pdf_07.txt": ("backend", "junior", "Backend engineer Java/Spring Boot"),
    "real_pdf_08.txt": ("fullstack", "intern", "Software Engineer - full-stack web + REST"),
    "real_pdf_10.txt": ("fullstack", "intern", "Nhiều dự án .NET + React (full-stack thực tế)"),
    "real_pdf_12.txt": ("backend", "intern", "Skills: Backend PHP/Laravel/Node; Frontend Vue/React (full-stack nhưng nền backend)"),
    "real_pdf_13.txt": ("backend", "intern", "Fresher Java Developer - RESTful API, MySQL/Oracle"),
    "real_pdf_15.txt": ("backend", "intern", "Fresher Java Developer"),
    "real_pdf_16.txt": ("backend", "junior", "Backend Developer .NET, ASP.NET Core"),
    "real_pdf_17.txt": ("fullstack", "intern", "Java Spring Boot + ReactJS/Angular cùng lúc"),
    "real_pdf_19.txt": ("backend", "intern", "Fresher Java Backend (Spring Boot)"),
    "real_pdf_20.txt": ("frontend", "intern", "Kỹ năng Front-end HTML/CSS/JS/Bootstrap"),
    "real_pdf_22.txt": ("fullstack", "intern", "Java Spring + Node + React + Docker (full-stack)"),
    "real_pdf_23.txt": ("fullstack", "intern", "Tự học, đa nền tảng web"),
    "real_pdf_24.txt": ("fullstack", "intern", "Java Spring Boot + React"),
    "real_pdf_25.txt": ("backend", "intern", "Backend Developer - PHP/Laravel"),
    "real_pdf_26.txt": ("backend", "intern", "Java Backend - mục tiêu Java Back-end"),
    "real_pdf_27.txt": ("frontend", "intern", "Android - Kotlin, Android Studio"),
    "real_pdf_28.txt": ("frontend", "intern", "Android Intern App - Kotlin/Java"),
    "real_pdf_29.txt": ("backend", "intern", "Intern .NET Developer"),
    "real_pdf_30.txt": ("fullstack", "intern", "Web developer đa nền tảng"),
    "real_pdf_31.txt": ("fullstack", "intern", "Web Developer Intern (HTML/CSS/JS/PHP)"),
    "real_pdf_32.txt": ("backend", "intern", "Intern PHP/Laravel"),
    "real_pdf_33.txt": ("frontend", "junior", "Front-end / Web (React, JS)"),
    "real_pdf_34.txt": ("fullstack", "intern", "ReactJS + Node.js (Express) + MySQL"),
    "real_pdf_35.txt": ("fullstack", "junior", "Developer đa nền tảng web"),
    "real_pdf_37.txt": ("backend", "intern", "Backend Developer"),
    "real_pdf_38.txt": ("frontend", "intern", "Low-code Developer Intern"),
    "real_pdf_40.txt": ("fullstack", "intern", "Front-end + Back-end (C#/SQL Server)"),
    "real_pdf_41.txt": ("security", "intern", "IT Helpdesk"),
    "real_pdf_42.txt": ("fullstack", "intern", "Profile - React/Node"),
    "real_pdf_43.txt": ("fullstack", "junior", "FULL-STACK DEVELOPER"),
    "real_pdf_44.txt": ("backend", "intern", "Java Backend - PHP/Laravel song song"),
    "real_pdf_47.txt": ("backend", "intern", "Motivated Backend Developer (Java)"),
    "real_pdf_48.txt": ("backend", "intern", ".NET Backend Developer"),
    "real_pdf_49.txt": ("backend", "intern", "Intern Developer - Java"),
    "real_pdf_51.txt": ("backend", "junior", "Backend Developer - JS/SQL"),
    "real_pdf_52.txt": ("backend", "intern", "Backend - Java Spring"),
    "real_pdf_53.txt": ("backend", "intern", "Backend Developer"),
    "real_pdf_54.txt": ("backend", "intern", "Developer - backend trọng tâm"),
    "real_pdf_23.txt": ("backend", "intern", "BACKEND INTERN - Java/Spring Boot"),
    "real_pdf_36.txt": ("backend", "junior", "C#/ASP.NET Core backend"),
    "real_pdf_56.txt": ("fullstack", "junior", "Fullstack Web Developer - Java Spring + Angular"),
    # --- ngoại lệ: CV không thuộc ngành IT ---
    "real_pdf_46.txt": ("OTHER", "junior", "CV Nhật - 応募職種：マーケティングスタッフ/事務员 (không phải IT, loại khỏi dataset)"),
}


def main() -> int:
    files = sorted(TXT_DIR.glob("real_*.txt"))
    if not files:
        print(f"[LỖI] Không có file .txt nào trong {TXT_DIR}")
        return 1

    labels: dict[str, dict] = {}
    dist: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for f in files:
        raw = f.read_text(encoding="utf-8", errors="replace")
        head = strip_accents(raw[:HEAD_CHARS])
        body = strip_accents(raw[:READ_CHARS])

        role, role_info = pick_role(head, body)
        level, level_info = pick_level(head, body)
        signal_role = "keyword"
        signal_level = level_info.get("signal", "")

        if f.name in OVERRIDES:
            o_role, o_level, why = OVERRIDES[f.name]
            role, level = o_role, o_level
            signal_role = "manual"
            signal_level = why
            role_info.pop("title_hint", None)

        labels[f.name] = {
            "role": role,
            "level": level,
            "role_signal": signal_role,
            "level_signal": signal_level,
            "title_hint": role_info.get("title_hint", ""),
            "auto_role": role if signal_role != "manual" else None,
            "role_scores": role_info.get("role_scores", {}),
            "chars": len(raw),
        }
        dist[role][level] += 1

    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    out = STAGE_DIR / "real_labels.json"
    out.write_text(json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Đã gán nhãn {len(labels)} CV thật -> {out}\n")
    all_roles = list(ROLE_KEYWORDS.keys()) + ["fullstack", "OTHER"]
    print(f"{'role':<11}" + "".join(f"{l:>9}" for l in SENIORITY_ORDER) + f"{'Tổng':>8}")
    print("-" * 65)
    tot = defaultdict(int)
    for role in all_roles:
        row = [dist[role].get(l, 0) for l in SENIORITY_ORDER]
        for l, c in zip(SENIORITY_ORDER, row):
            tot[l] += c
        print(f"{role:<11}" + "".join(f"{c:>9}" for c in row) + f"{sum(row):>8}")
    print("-" * 65)
    row = [tot[l] for l in SENIORITY_ORDER]
    print(f"{'TỔNG':<11}" + "".join(f"{c:>9}" for c in row) + f"{sum(row):>8}")

    # đối chiếu nhãn thủ công với nhãn tự động
    mismatches = [
        (f, v["auto_role"], v["role"])
        for f, v in labels.items()
        if v["role_signal"] == "manual" and v["auto_role"] and v["auto_role"] != v["role"]
    ]
    if mismatches:
        print(f"\n[SỬA THỦ CÔNG] {len(mismatches)} file khác kết quả tự động:")
        for f, auto, manual in mismatches:
            print(f"  {f[-6:-4]}: auto={auto:<10} -> manual={manual}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
