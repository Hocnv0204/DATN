#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kiem tra: nhan silver co suy ra duoc tu van ban CV hay khong?"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
d = ROOT / "cv-analysis-service" / "cv_texts"
recs = [json.loads(l) for l in open(
    ROOT / "cv-analysis-service/finetune_output/silver_dataset.jsonl", encoding="utf-8")]
mm = {e["new"]: e["old"] for e in json.load(open(
    ROOT / "fine-tune/_stage/filename_map.json"))}

syn = [r for r in recs if mm[r["file"]].startswith("syn_")]
real = [r for r in recs if mm[r["file"]].startswith("real_")]
print(f"CV tong hop: {len(syn)}   CV that: {len(real)}\n")

for label, group in (("TONG HOP", syn), ("THAT", real)):
    ts = team = gh = comp = date = 0
    n_proj = 0
    for r in group:
        txt = r["input"]
        o = json.loads(r["output"])
        for p in o.get("personal_projects", []):
            n_proj += 1
            for t in (p.get("tech_stack") or []):
                if t and t not in txt:
                    ts += 1
            if p.get("team_size") and str(p["team_size"]) not in txt:
                team += 1
            if p.get("github_url") and p["github_url"].split("//")[-1] not in txt:
                gh += 1
            if p.get("start_date") and str(p["start_date"]) not in txt:
                date += 1
        for e in o.get("experience", []):
            if e.get("company") and e["company"] not in txt:
                comp += 1
    print(f"[{label}] so project = {n_proj}")
    print(f"  tech_stack khong xuat hien trong CV text  : {ts}")
    print(f"  team_size  khong xuat hien trong CV text  : {team}")
    print(f"  github_url khong xuat hien trong CV text  : {gh}")
    print(f"  project.start_date khong co trong CV text : {date}")
    print(f"  experience.company khong co trong CV text : {comp}\n")
