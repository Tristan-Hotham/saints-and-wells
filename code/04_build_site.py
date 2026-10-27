"""Step 4: build ../index.html from page_template.html and ../work/site.json.

Every number in the page text is a placeholder like {{by_country.FR.share_mary|pct1}}
filled from ../data/results.json; the compact map and chart data are embedded
as `const D = ...`. Formats: int, pct0, pct1, f0, f1, f2, raw, words.
Also renders ../README.md from README_template.md the same way.
Run: python3 04_build_site.py
"""
import os, re, json, collections
from pyproj import Transformer
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
H = json.load(open(os.path.join(ROOT, "work", "hex.json")))["20"]
inv = Transformer.from_crs("EPSG:3035", "EPSG:4326", always_xy=True)
CC = [c["cc"] for c in R["countries"]]
import sys; sys.path.insert(0, HERE)
import saints as S

# saints offered in the picker: the featured ones, then every dedication with 150+ churches
FEATURED = ["Mary", "Martin", "Michael", "Peter", "James", "Nicholas", "John", "Celtic saints", "Patrick", "Brigid", "David", "Columba",
            "Boniface", "Kilian", "Ambrose", "Lambert", "Andrew", "Anthony", "Roch", "Joseph", "Christ", "All Saints"]
tot = collections.Counter()
for h in H:
    for k, v in h["k"].items(): tot[k] += v
others = sorted([k for k, v in tot.items() if v >= 150 and k not in FEATURED])
KEYS = FEATURED + others
KI = {k: i for i, k in enumerate(KEYS)}
CEL = set(R["celtic_members"])
cells = []
for h in H:
    lo, la = inv.transform(h["vx"], h["vy"])
    v = [round(a, 3) for p in zip(la, lo) for a in p]
    cnt = {}
    for k, n in h["k"].items():
        if k in KI: cnt[KI[k]] = n
    if h["celtic"]: cnt[KI["Celtic saints"]] = h["celtic"]
    lead = sorted(h["k"].items(), key=lambda kv: (-kv[1], -tot[kv[0]]))[:6]
    cells.append([v, h["n"], h["ni"], CC.index(h["cc"]), h["saint"] or "", h["saint_n"], int(h["saint_tie"]), h["lead"] or "", h["lead_n"],
                  [x for kv in cnt.items() for x in kv], [[k, n] for k, n in lead]])
wells = []
import csv
for r in csv.DictReader(open(os.path.join(ROOT, "data", "holy_wells.csv"))):
    wells.append([round(float(r["lat"]), 4), round(float(r["lon"]), 4), r["dedication"], r["label"], r["country"]])
slim = {k: R[k] for k in ["countries", "selected", "james", "height_rank", "michael", "richest", "poorest", "wells", "validation", "hex20",
                          "signature_regions", "richness_by_country", "celtic_members"]}
slim["signature_regions"] = [s for s in R["signature_regions"] if s["n"] >= 9 and s["key"] not in ("Peace", "Maranatha", "Martyrs", "Angels", "Innocents")][:24]
slim["regions"] = [{k: r.get(k) for k in ("id", "name", "cc", "n_identified", "richness100", "share_mary")} for r in R["regions"] if r.get("richness100")]
site = {"keys": KEYS, "featured": len(FEATURED), "cc": CC, "cells": cells, "wells": wells, "R": slim}
open(os.path.join(ROOT, "work", "site.json"), "w").write(json.dumps(site, separators=(",", ":"), ensure_ascii=False))


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f0": return f"{v:,.0f}"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "words":
        w = "zero one two three four five six seven eight nine ten eleven twelve".split()
        return w[int(v)] if int(v) < len(w) else f"{int(v):,}"
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


t = open(os.path.join(HERE, "page_template.html")).read()
t = re.sub(r"\{\{(.+?)\}\}", sub, t)
t = t.replace("/*DATA*/", "const D = " + json.dumps(site, separators=(",", ":"), ensure_ascii=False) + ";")
open(os.path.join(ROOT, "index.html"), "w").write(t)
print("index.html", len(t.encode()) // 1024, "KB")
if os.path.exists(os.path.join(HERE, "README_template.md")):
    md = re.sub(r"\{\{(.+?)\}\}", sub, open(os.path.join(HERE, "README_template.md")).read())
    open(os.path.join(ROOT, "README.md"), "w").write(md); print("README.md written")
