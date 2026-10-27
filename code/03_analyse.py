"""Step 3: analysis. Reads ../data/churches.csv.gz and the geography in ../data/geo,
writes ../data/results.json (every number used anywhere), the reusable data
files in ../data, and page/collage inputs in ../work.

Everything is framed as SHARES WITHIN a country or region, because Wikidata's
coverage of church buildings differs hugely between countries.

  - countries: churches, churches per 1,000 km2, share with an identified
    dedication, share from P825 vs label, top dedications (shares of the
    churches with an identified dedication);
  - hexagons (20 km and 13 km, in ETRS89-LAEA): leading dedication and
    leading saint (Mary, Christ, the Trinity, the Holy Cross, the Holy Spirit,
    the Holy Family and All Saints set aside);
  - NUTS 2016 level 2 regions: shares, rarefied richness (expected number of
    different dedications among 100 churches drawn at random), and a
    'signature saint' (largest share relative to the rest of the same country);
  - selected saints and the group of early Insular Celtic saints;
  - St Michael and height (Britain and Ireland only, where the terrain model
    is available): ground height and height above the surrounding 1 km;
  - St James and distance from the cathedral of Santiago de Compostela;
  - holy wells (Wikidata holy wells in the study countries).
Run: python3 03_analyse.py
"""
import os, sys, json, csv, gzip, math, re, collections
import numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from pyproj import Transformer
from scipy.stats import mannwhitneyu
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import saints as S

WD = os.environ.get("WD_DIR", "/home/claude/hist/_data2/wikidata")
CC = ["GB", "IE", "FR", "BE", "NL", "LU", "DE", "CH", "AT", "IT", "ES", "PT"]
CNAME = {"GB": "United Kingdom", "IE": "Ireland", "FR": "France", "BE": "Belgium", "NL": "Netherlands", "LU": "Luxembourg", "DE": "Germany",
         "CH": "Switzerland", "AT": "Austria", "IT": "Italy", "ES": "Spain", "PT": "Portugal"}
AREA = json.load(open(os.path.join(ROOT, "data", "geo", "areas.json")))
NONSAINT = {"Mary", "Christ", "Holy Trinity", "Holy Cross", "Holy Spirit", "Holy Family", "All Saints"}
CELTIC = ["Patrick", "Brigid", "Columba", "Kevin", "Ciaran", "Brendan", "Finbarr", "Declan", "Aidan", "Ninian",
          "David", "Teilo", "Cadoc", "Illtud", "Dyfrig", "Padarn", "Beuno", "Deiniol", "Cybi", "Tysilio", "Asaph", "Non",
          "Piran", "Petroc", "Samson", "Brioc", "Ronan", "Malo", "Winwaloe", "Corentin", "Tugdual", "Gildas", "Méen", "Hervé", "Efflam", "Melaine"]
CELTIC = CELTIC + [k for k in S.CELTIC_EXTRA if k not in CELTIC]
SELECTED = ["Mary", "Martin", "Michael", "Peter", "James", "Nicholas", "John", "Celtic saints", "Boniface", "Kilian", "Ambrose", "Andrew", "Anthony", "Lambert"]
SANTIAGO = (-8.54444, 42.88056)   # Catedral de Santiago de Compostela, Wikidata Q205136 (this dataset)
_F = json.load(open(os.path.join(ROOT, "work", "forms.json")))
S.FORM.update(_F["form"]); S.FORM.update(_F["alias"])   # the same name table and learned aliases as step 2
laea = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
inv = Transformer.from_crs("EPSG:3035", "EPSG:4326", always_xy=True)
R = {}

# ---------------- load churches (only the columns needed) ----------------
rows = []
with gzip.open(os.path.join(ROOT, "data", "churches.csv.gz"), "rt", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append((r["qid"], r["country"], float(r["lon"]), float(r["lat"]), r["dedication"], r["source"], r["all_dedications"].count("|") + 1 if r["all_dedications"] else 0))
qid = np.array([r[0] for r in rows]); cc = np.array([r[1] for r in rows]); lon = np.array([r[2] for r in rows]); lat = np.array([r[3] for r in rows])
ded = np.array([r[4] for r in rows], dtype=object); src = np.array([r[5] for r in rows]); nded = np.array([r[6] for r in rows])
del rows
N = len(qid); idm = ded != ""
print("churches", N, "identified", idm.sum())
ktype = {k: S.key_type(k) for k in set(ded[idm])}
celtic = np.array([d in CELTIC for d in ded])

def share(mask_num, mask_den):
    d = mask_den.sum(); return float(mask_num[mask_den].sum() / d) if d else None

# ---------------- countries ----------------
R["n_churches"] = int(N); R["n_identified"] = int(idm.sum()); R["n_countries"] = len(CC)
R["n_p825"] = int((src == "P825").sum()); R["n_label"] = int((src == "label").sum()); R["n_none"] = int((src == "none").sum())
R["share_identified"] = R["n_identified"] / N
R["n_distinct_keys"] = len(set(ded[idm]))
R["share_multi_dedication"] = float((nded[idm] > 1).mean())
R["validation"] = json.load(open(os.path.join(ROOT, "work", "validation.json")))
del R["validation"]["aliases_sample"]
R["validation"]["top_disagreements"] = R["validation"]["top_disagreements"][:12]
R["counts_raw"] = json.load(open(os.path.join(ROOT, "work", "counts.json")))
countries = []; country_key_rows = []
for c in CC:
    m = cc == c; mi = m & idm; n = int(m.sum()); ni = int(mi.sum())
    cnt = collections.Counter(ded[mi])
    top = [{"key": k, "n": v, "share": v / ni, "type": ktype[k]} for k, v in cnt.most_common(12)]
    sa = [(k, v) for k, v in cnt.most_common() if k not in NONSAINT]
    for k, v in cnt.items(): country_key_rows.append([c, k, ktype[k], v, round(v / ni, 5)])
    countries.append({"cc": c, "name": CNAME[c], "n": n, "area_km2": AREA[c], "per_1000km2": n / AREA[c] * 1000, "n_identified": ni,
                      "share_identified": ni / n, "share_p825": float((src[m] == "P825").mean()), "share_label": float((src[m] == "label").mean()),
                      "share_mary": cnt["Mary"] / ni, "share_dominical": sum(v for k, v in cnt.items() if ktype[k] == "dominical") / ni,
                      "share_all_saints": cnt["All Saints"] / ni, "top": top, "lead_saint": sa[0][0], "lead_saint_share": sa[0][1] / ni,
                      "second_saint": sa[1][0], "second_saint_share": sa[1][1] / ni, "n_keys": len(cnt),
                      "share_celtic": float(celtic[mi].mean())})
R["countries"] = countries
cby = {x["cc"]: x for x in countries}
R["by_country"] = cby
R["max_density"] = max(countries, key=lambda x: x["per_1000km2"])["cc"]; R["min_density"] = min(countries, key=lambda x: x["per_1000km2"])["cc"]
R["max_identified"] = max(countries, key=lambda x: x["share_identified"])["cc"]; R["min_identified"] = min(countries, key=lambda x: x["share_identified"])["cc"]
with open(os.path.join(ROOT, "data", "country_dedications.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["country", "dedication", "type", "churches", "share_of_identified"])
    for r in sorted(country_key_rows, key=lambda r: (r[0], -r[3])): w.writerow(r)

# ---------------- selected saints by country ----------------
def is_key(k):
    return celtic if k == "Celtic saints" else (ded == k)
sel = {}
for k in SELECTED:
    mk = is_key(k)
    sel[k] = {"by_country": {c: share(mk, (cc == c) & idm) for c in CC}, "n": int((mk & idm).sum())}
    best = max(CC, key=lambda c: sel[k]["by_country"][c]); sel[k]["top_country"] = best
R["selected"] = sel
R["celtic_members"] = CELTIC
cel_cnt = collections.Counter(ded[celtic]); R["celtic_top"] = [{"key": k, "n": v} for k, v in cel_cnt.most_common(10)]

# ---------------- NUTS2 regions ----------------
NU = json.load(open(os.path.join(ROOT, "data", "geo", "nuts2.geojson")))["features"]
geoms = [shape(f["geometry"]) for f in NU]; tree = STRtree(geoms)
pts = [Point(x, y) for x, y in zip(lon, lat)]
reg = np.full(N, -1)
a, b = tree.query(pts, predicate="intersects")
reg[a] = b
miss = np.where(reg < 0)[0]
if len(miss):
    near = tree.query_nearest([pts[i] for i in miss], max_distance=0.15)
    reg[miss[near[0]]] = near[1]
# a point must stay in its own country's regions
rcc = np.array([f["properties"]["cc"] for f in NU])
bad = (reg >= 0) & (rcc[np.maximum(reg, 0)] != cc); reg[bad] = -1
del pts
R["share_in_region"] = float((reg >= 0).mean())

def rarefy(counts, m=100):
    n = sum(counts)
    if n < m: return None
    lg = lambda a, b: math.lgamma(a + 1) - math.lgamma(b + 1) - math.lgamma(a - b + 1)
    tot = lg(n, m)
    return sum(1 - (math.exp(lg(n - c, m) - tot) if n - c >= m else 0) for c in counts)

regions = []
for i, f in enumerate(NU):
    p = f["properties"]; m = reg == i; mi = m & idm; n = int(m.sum()); ni = int(mi.sum())
    rec = {"id": p["id"], "name": p["name"], "cc": p["cc"], "km2": p["km2"], "n": n, "n_identified": ni}
    if ni >= 30:
        cnt = collections.Counter(ded[mi])
        sa = [(k, v) for k, v in cnt.most_common() if k not in NONSAINT]
        rest = (cc == p["cc"]) & idm & ~m; nr = int(rest.sum()); crest = collections.Counter(ded[rest])
        sig = None
        if nr >= 100:
            best = None
            for k, v in sa:
                if v < 8: continue
                lift = (v / ni) / ((crest[k] + 0.5) / nr)
                if best is None or lift > best[1]: best = (k, lift, v)
            if best: sig = {"key": best[0], "lift": best[1], "n": best[2], "share": best[2] / ni, "share_rest": crest[best[0]] / nr,
                            "n_country": best[2] + crest[best[0]], "conc": best[2] / (best[2] + crest[best[0]])}
        rec.update({"top": cnt.most_common(1)[0][0], "top_share": cnt.most_common(1)[0][1] / ni, "lead_saint": sa[0][0] if sa else None,
                    "lead_saint_share": sa[0][1] / ni if sa else None, "share_mary": cnt["Mary"] / ni, "richness100": rarefy(list(cnt.values())),
                    "signature": sig, "n_keys": len(cnt), "share_celtic": float(celtic[mi].mean()),
                    "shares": {k: (float(is_key(k)[mi].mean())) for k in SELECTED}})
    regions.append(rec)
R["regions"] = regions
ok = [r for r in regions if r.get("richness100") is not None]
R["n_regions"] = len(regions); R["n_regions_rich"] = len(ok)
rich = sorted(ok, key=lambda r: -r["richness100"])
R["richest"] = [{k: r[k] for k in ("id", "name", "cc", "richness100", "n_identified", "share_mary")} for r in rich[:10]]
R["poorest"] = [{k: r[k] for k in ("id", "name", "cc", "richness100", "n_identified", "share_mary")} for r in rich[-10:]]
R["richness_by_country"] = {c: float(np.median([r["richness100"] for r in ok if r["cc"] == c])) for c in CC if any(r["cc"] == c for r in ok)}
R["richness_corr_mary"] = float(np.corrcoef([r["richness100"] for r in ok], [r["share_mary"] for r in ok])[0, 1])
for k in SELECTED:
    rr = sorted([r for r in regions if r.get("shares") and r["n_identified"] >= 100], key=lambda r: -r["shares"][k])
    R["selected"][k]["top_regions"] = [{"id": r["id"], "name": r["name"], "cc": r["cc"], "share": r["shares"][k], "n_identified": r["n_identified"]} for r in rr[:6]]
sigs = [r for r in regions if r.get("signature") and r["signature"]["lift"] >= 2]
R["signature_regions"] = sorted([{"id": r["id"], "name": r["name"], "cc": r["cc"], **r["signature"]} for r in sigs], key=lambda x: -x["lift"])
with open(os.path.join(ROOT, "data", "regions.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["nuts2", "name", "country", "km2", "churches", "identified", "top_dedication", "top_share", "leading_saint", "leading_saint_share", "share_mary",
                "richness_per_100", "signature_saint", "signature_lift", "signature_share", "signature_share_rest_of_country"] + [f"share_{k.lower().replace(' ', '_')}" for k in SELECTED])
    for r in regions:
        s = r.get("signature") or {}
        w.writerow([r["id"], r["name"], r["cc"], r["km2"], r["n"], r["n_identified"], r.get("top", ""), round(r.get("top_share") or 0, 4), r.get("lead_saint") or "",
                    round(r.get("lead_saint_share") or 0, 4), round(r.get("share_mary") or 0, 4), round(r["richness100"], 2) if r.get("richness100") else "",
                    s.get("key", ""), round(s["lift"], 2) if s else "", round(s["share"], 4) if s else "", round(s["share_rest"], 4) if s else ""] +
                   [round(r["shares"][k], 4) if r.get("shares") else "" for k in SELECTED])

# ---------------- hexagons ----------------
X, Y = laea.transform(lon, lat)
X = np.asarray(X); Y = np.asarray(Y)
def hexbin(s):
    q = (math.sqrt(3) / 3 * X - Y / 3) / s; r = (2 / 3 * Y) / s
    x, z = q, r; y = -x - z
    rx, ry, rz = np.round(x), np.round(y), np.round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    c1 = (dx > dy) & (dx > dz); rx[c1] = -ry[c1] - rz[c1]
    c2 = ~c1 & (dy > dz); ry[c2] = -rx[c2] - rz[c2]
    c3 = ~c1 & ~c2; rz[c3] = -rx[c3] - ry[c3]
    return rx.astype(int), rz.astype(int)
def hex_vertices(q, r, s):
    cx = s * math.sqrt(3) * (q + r / 2); cy = s * 1.5 * r
    vx = [cx + s * math.cos(math.radians(60 * i + 30)) for i in range(6)]; vy = [cy + s * math.sin(math.radians(60 * i + 30)) for i in range(6)]
    return cx, cy, vx, vy
tot_key = collections.Counter(ded[idm])
HEX = {}
for s_km in (20, 13):
    s = s_km * 1000; hq, hr = hexbin(s)
    cells = collections.defaultdict(lambda: {"n": 0, "ni": 0, "k": collections.Counter(), "cc": collections.Counter()})
    for i in range(N):
        c = cells[(hq[i], hr[i])]; c["n"] += 1; c["cc"][cc[i]] += 1
        if idm[i]: c["ni"] += 1; c["k"][ded[i]] += 1
    out = []
    for (q, r), c in cells.items():
        cx, cy, vx, vy = hex_vertices(q, r, s)
        sa = sorted([(v, tot_key[k], k) for k, v in c["k"].items() if k not in NONSAINT], reverse=True)
        al = sorted([(v, tot_key[k], k) for k, v in c["k"].items()], reverse=True)
        out.append({"q": int(q), "r": int(r), "x": cx, "y": cy, "vx": vx, "vy": vy, "n": c["n"], "ni": c["ni"], "cc": c["cc"].most_common(1)[0][0],
                    "lead": al[0][2] if al else None, "lead_n": al[0][0] if al else 0, "lead_tie": len(al) > 1 and al[1][0] == al[0][0],
                    "saint": sa[0][2] if sa else None, "saint_n": sa[0][0] if sa else 0, "saint_tie": len(sa) > 1 and sa[1][0] == sa[0][0],
                    "k": dict(c["k"]), "celtic": int(sum(v for k, v in c["k"].items() if k in CELTIC))})
    HEX[s_km] = out
    shown = [h for h in out if h["ni"] >= 10]
    lc = collections.Counter(h["saint"] for h in shown)
    R[f"hex{s_km}"] = {"size_km": s_km, "cells": len(out), "cells_shown": len(shown), "min_identified": 10,
                       "lead_saint_cells": [{"key": k, "cells": v, "share": v / len(shown)} for k, v in lc.most_common(20)],
                       "lead_any_cells": [{"key": k, "cells": v, "share": v / len(shown)} for k, v in collections.Counter(h["lead"] for h in shown).most_common(10)],
                       "ties": sum(h["saint_tie"] for h in shown)}
    print(s_km, len(out), len(shown), lc.most_common(16))
json.dump({k: v for k, v in HEX.items()}, open(os.path.join(ROOT, "work", "hex.json"), "w"), default=lambda o: o if not isinstance(o, np.integer) else int(o))
# a reusable hex layer: leading dedication and leading saint per 20 km hexagon
feats = []
for h in HEX[20]:
    lo, la = inv.transform(h["vx"] + [h["vx"][0]], h["vy"] + [h["vy"][0]])
    feats.append({"type": "Feature", "properties": {"q": h["q"], "r": h["r"], "churches": h["n"], "identified": h["ni"], "country": h["cc"],
                  "leading_dedication": h["lead"], "leading_dedication_n": h["lead_n"], "leading_saint": h["saint"], "leading_saint_n": h["saint_n"],
                  "saint_tie": h["saint_tie"]}, "geometry": {"type": "Polygon", "coordinates": [[[round(a, 4), round(b, 4)] for a, b in zip(lo, la)]]}})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(ROOT, "data", "hex20_leading.geojson"), "w"), separators=(",", ":"), ensure_ascii=False)

# ---------------- Michael and height (Britain and Ireland) ----------------
from dem import DEM
dem = DEM()
bi = np.where(((cc == "GB") | (cc == "IE")) & idm)[0]
la_, lo_ = lat[bi], lon[bi]
z0 = dem.elev(la_, lo_)
ring = []
for rad in (500, 1000):
    for ang in range(0, 360, 30):
        dx = rad * math.cos(math.radians(ang)); dy = rad * math.sin(math.radians(ang))
        dlat = dy / 111320.0; dlon = dx / (111320.0 * np.cos(np.radians(la_)))
        ring.append(dem.elev(la_ + dlat, lo_ + dlon))
ring = np.vstack(ring)
rel = z0 - ring.mean(axis=0)
rank = (ring < z0).mean(axis=0)
del ring
land = z0 > 0
dd = ded[bi]
mich = (dd == "Michael") & land; oth = (dd != "Michael") & land
u = mannwhitneyu(rel[mich], rel[oth], alternative="greater")
u2 = mannwhitneyu(z0[mich], z0[oth], alternative="greater")
R["michael"] = {"n_michael": int(mich.sum()), "n_other": int(oth.sum()), "median_rel_michael": float(np.median(rel[mich])), "median_rel_other": float(np.median(rel[oth])),
                "mean_rel_michael": float(rel[mich].mean()), "mean_rel_other": float(rel[oth].mean()),
                "median_elev_michael": float(np.median(z0[mich])), "median_elev_other": float(np.median(z0[oth])),
                "share_top_michael": float((rank[mich] >= 0.9).mean()), "share_top_other": float((rank[oth] >= 0.9).mean()),
                "share_rel20_michael": float((rel[mich] >= 20).mean()), "share_rel20_other": float((rel[oth] >= 20).mean()),
                "p_rel": float(u.pvalue), "p_elev": float(u2.pvalue)}
R["michael"]["ratio_top"] = R["michael"]["share_top_michael"] / R["michael"]["share_top_other"]
rk = []
for k, v in collections.Counter(dd[land]).most_common():
    if v < 150: break
    mk = (dd == k) & land
    rk.append({"key": k, "n": int(v), "median_rel": float(np.median(rel[mk])), "share_top": float((rank[mk] >= 0.9).mean()), "median_elev": float(np.median(z0[mk]))})
R["height_rank"] = sorted(rk, key=lambda x: -x["share_top"])
R["michael"]["rank_of_michael"] = [x["key"] for x in R["height_rank"]].index("Michael") + 1; R["michael"]["n_ranked"] = len(rk)
print("michael", R["michael"])

# ---------------- James and Santiago ----------------
sx, sy = laea.transform(*SANTIAGO)
dist = np.hypot(X - sx, Y - sy) / 1000
bands = [(0, 150), (150, 300), (300, 500), (500, 750), (750, 1000), (1000, 1500), (1500, 3000)]
jam = ded == "James"
R["james"] = {"santiago": {"lon": SANTIAGO[0], "lat": SANTIAGO[1], "source": "Wikidata Q205136 (Catedral de Santiago de Compostela), coordinates as in this dataset"}, "bands": {}}
for c in ("ES", "PT", "FR", "IT", "DE", "GB"):
    out = []
    for lo_b, hi_b in bands:
        m = (cc == c) & idm & (dist >= lo_b) & (dist < hi_b)
        if m.sum() >= 150: out.append({"lo": lo_b, "hi": hi_b, "n": int(m.sum()), "share": float(jam[m].mean())})
    R["james"]["bands"][c] = out
gal = [r for r in regions if r["id"] == "ES11"][0]
R["james"]["galicia_share"] = gal["shares"]["James"]; R["james"]["spain_share"] = sel["James"]["by_country"]["ES"]
R["james"]["n_iberia_within150"] = int((((cc == "ES") | (cc == "PT")) & idm & (dist < 150)).sum())

# ---------------- holy wells ----------------
HW = json.load(open(os.path.join(WD, "holywells.json")))
WC = {"Q27": "IE", "Q145": "GB", "Q26": "GB", "Q38": "IT", "Q142": "FR", "Q55": "NL", "Q29": "ES", "Q45": "PT", "Q183": "DE", "Q31": "BE", "Q39": "CH", "Q40": "AT"}
IRISH = [("Mary", r"t(?:obar|ober|ubber|ubbrid)\s*(?:na\s*)?(?:mhuire|muire|murry|vurry|mhure|mary)"), ("Brigid", r"t(?:obar|ober|ubber)\s*(?:bh|b)r[ií]de|toberbride|tobar\s*bhr[ií]d|tubberbride|toberbreeda"),
         ("Patrick", r"t(?:obar|ober|ubber)\s*(?:ph|p)h?[aá]draig|toberpatrick|tobar\s*ph[aá]draig")]
wells = []
for x in HW:
    c = WC.get(x["country"]); m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", x["c"])
    if not c or not m: continue
    lo_w, la_w = float(m.group(1)), float(m.group(2))
    if not (-11 <= lo_w <= 19 and 35.6 <= la_w <= 61): continue
    lab = x.get("wLabel") or ""
    k = None; how = "none"
    if x.get("ded"):
        k = S.key_for_ded(x["ded"], {"en": x.get("dedLabel") or ""}); how = "P825"
    if not k:
        ks = S.parse(lab)
        if not ks:
            mm = re.match(r"^\s*(?:the\s+)?([A-Z][\w']+?)(?:'s|s'|’s)?\s+(?:holy\s+)?well\b", lab)
            if mm:
                kk, _ = S.lookup([mm.group(1)])
                if mm.group(1).lower() == "lady": kk = "Mary"
                if kk: ks = [kk]
        if not ks:
            for kk, pat in IRISH:
                if re.search(pat, lab, re.I): ks = [kk]; break
        if ks: k = ks[0]; how = "label"
    wells.append({"qid": x["w"], "country": c, "lon": lo_w, "lat": la_w, "label": lab if not re.match(r"^Q\d+$", lab) else "", "dedication": k or "", "source": how})
with open(os.path.join(ROOT, "data", "holy_wells.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["qid", "country", "lon", "lat", "label", "dedication", "source"]); w.writeheader(); w.writerows(wells)
wc = collections.Counter(x["country"] for x in wells)
ie = [x for x in wells if x["country"] == "IE"]; ie_id = [x for x in ie if x["dedication"]]
iek = collections.Counter(x["dedication"] for x in ie_id)
mi = (cc == "IE") & idm; cie = collections.Counter(ded[mi])
gbw = [x for x in wells if x["country"] == "GB" and x["dedication"]]
R["wells"] = {"n": len(wells), "by_country": dict(wc.most_common()), "n_identified": sum(1 for x in wells if x["dedication"]),
              "ie_n": len(ie), "ie_identified": len(ie_id), "ie_top": [{"key": k, "n": v, "share": v / len(ie_id), "church_share": cie[k] / int(mi.sum())} for k, v in iek.most_common(10)],
              "gb_identified": len(gbw), "gb_top": [{"key": k, "n": v} for k, v in collections.Counter(x["dedication"] for x in gbw).most_common(6)],
              "ie_celtic_share": sum(1 for x in ie_id if x["dedication"] in CELTIC) / len(ie_id), "ie_church_celtic_share": cby["IE"]["share_celtic"],
              "excluded_outside_study": len(HW) - len(wells)}
print("wells", R["wells"]["n"], R["wells"]["by_country"], R["wells"]["ie_top"][:5])

# ---------------- dedication list for the page ----------------
keys_all = collections.Counter(ded[idm])
R["top_overall_note"] = "pooled counts are not compared across countries; used only to choose which saints the page lists"
R["n_keys_100plus"] = sum(1 for v in keys_all.values() if v >= 100)
with open(os.path.join(ROOT, "data", "dedications.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["dedication", "type", "churches_total"] + CC)
    byc = collections.defaultdict(collections.Counter)
    for c, d in zip(cc[idm], ded[idm]): byc[d][c] += 1
    for k, v in keys_all.most_common(): w.writerow([k, ktype[k], v] + [byc[k][c] for c in CC])
_v = [x["share"] for c, x in R["validation"]["rules_plus_heldout_aliases"].items() if c != "ALL" and x["both"] >= 100]
R["val_min"], R["val_max"] = min(_v), max(_v)
R["celtic_n"] = len(CELTIC)
R["celtic_bretagne"] = [r for r in regions if r["id"] == "FRH0"][0]["share_celtic"]
R["celtic_cornwall"] = [r for r in regions if r["id"] == "UKK3"][0]["share_celtic"]
R["n_ded_items"] = len(json.load(open(os.path.join(WD, "ded_labels.json"))))
json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False, default=lambda o: int(o) if isinstance(o, np.integer) else float(o))
print("results.json written")
