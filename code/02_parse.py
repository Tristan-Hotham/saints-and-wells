"""Step 2: assign a dedication to every church building, one country at a time.

Input: Wikidata church-building extracts (CC0) in WD_DIR (default
/home/claude/hist/_data2/wikidata): ch_<CC>.json with fields ch (QID),
c ('Point(lon lat)'), lab (local-language label), en (English label),
ded (P825 'dedicated to' QID, may be missing; one row per value),
plus ded_labels.json (labels of every dedication QID).

Method (see saints.py for the parser rules):
  - dedupe rows by church QID; keep churches whose point falls in the
    study frame (lon -11 to 19, lat 35.6 to 61: the European parts of the
    twelve countries; no Canaries, Azores, Madeira or overseas France);
  - if the church has P825, its dedication keys come from P825
    (primary = the P825 key the label names first, else the most used);
  - otherwise the local label is parsed, then the English label;
  - learned aliases: a name the rule set does not know (e.g. Dutch
    'Kwintens') is mapped to a known saint when, among churches that have
    both P825 and that label name, at least 2 do and at least 75% of them
    point to the same saint;
  - validation: among churches with BOTH P825 and a label parse, the share
    whose parsed primary matches one of the P825 keys; reported for the
    core rules alone and for the rules plus aliases learned on the other
    half of the churches (two-fold split on the QID number), so the alias
    step is not checked on the data it was learned from.

Two streaming passes over the countries (memory-light).
Output:
  ../data/churches.csv.gz  one row per church (qid, country, lon, lat, label,
                           dedication, all_dedications, source P825/label/none, p825 QIDs)
  ../work/validation.json  agreement by country, aliases, top disagreements
  ../work/counts.json      per-country totals
Run: python3 02_parse.py
"""
import os, sys, json, csv, re, gzip, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import saints as S

WD = os.environ.get("WD_DIR", "/home/claude/hist/_data2/wikidata")
CC = ["GB", "IE", "FR", "ES", "PT", "IT", "DE", "BE", "NL", "LU", "CH", "AT"]
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
FRAME = (-11.0, 35.6, 19.0, 61.0)

DL = json.load(open(os.path.join(WD, "ded_labels.json")))
freq = collections.Counter()
for c in CC:
    for r in json.load(open(os.path.join(WD, f"ch_{c}.json"))):
        if r.get("ded"): freq[r["ded"]] += 1
DKEY = S.build_forms(DL, freq)
KNOWN = set(S.FORM.values()) | set(DKEY.values())


def churches(c):
    """Yield (qid, lon, lat, label, parsed keys, p825 keys, p825 qids) for one country, deduped and in frame."""
    rows = json.load(open(os.path.join(WD, f"ch_{c}.json")))
    ch = {}
    for r in rows:
        q = r["ch"]
        if q not in ch: ch[q] = {"c": r.get("c"), "lab": r.get("lab"), "en": r.get("en"), "ded": []}
        if r.get("ded") and r["ded"] not in ch[q]["ded"]: ch[q]["ded"].append(r["ded"])
    del rows
    for q, d in ch.items():
        m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", d["c"] or "")
        if not m: yield q, None, None, None, None, None, None; continue
        lon, lat = float(m.group(1)), float(m.group(2))
        if not (FRAME[0] <= lon <= FRAME[2] and FRAME[1] <= lat <= FRAME[3]): yield q, None, None, None, None, None, None; continue
        parsed = S.parse(d["lab"]) or S.parse(d["en"])
        pk = list(dict.fromkeys(DKEY[x] for x in d["ded"] if x in DKEY))
        yield q, lon, lat, d["lab"] or d["en"] or "", parsed, pk, d["ded"]


def apply(parsed, alias):
    return list(dict.fromkeys(alias.get(S.norm(k), k) if k not in KNOWN else k for k in parsed))


def learn(records):
    cnt = collections.defaultdict(collections.Counter)
    for fold, cc, parsed, pk in records:
        k = parsed[0]
        if k not in KNOWN and len(pk) == 1: cnt[S.norm(k)][pk[0]] += 1
    out = {}
    for f, c in cnt.items():
        k, n = c.most_common(1)[0]
        if n >= 2 and n / sum(c.values()) >= 0.75: out[f] = k
    return out


# ---- pass 1: churches with both P825 and a label parse -----------------------
records = []; seen = set()
for c in CC:
    for q, lon, lat, label, parsed, pk, _ in churches(c):
        if lon is None or q in seen: continue
        seen.add(q)
        if pk and parsed: records.append((int(q[1:]) % 2, c, parsed, pk))
    print("pass 1", c, len(records))
alias_fold = {f: learn([r for r in records if r[0] != f]) for f in (0, 1)}
ALIAS = learn(records)


def agreement(use_alias):
    by = collections.defaultdict(collections.Counter)
    for fold, c, parsed, pk in records:
        p = apply(parsed, alias_fold[fold]) if use_alias else parsed
        for g in (c, "ALL"):
            by[g]["both"] += 1; by[g]["agree"] += p[0] in pk
    return {g: {"both": v["both"], "agree": v["agree"], "share": round(v["agree"] / v["both"], 4)} for g, v in by.items()}


val = {"core_rules": agreement(False), "rules_plus_heldout_aliases": agreement(True), "n_aliases": len(ALIAS),
       "aliases_sample": dict(sorted(ALIAS.items())[:80])}
dis = collections.Counter()
for fold, c, parsed, pk in records:
    p = apply(parsed, alias_fold[fold])
    if p[0] not in pk: dis[(c, p[0], pk[0])] += 1
val["top_disagreements"] = [{"country": a, "label_parse": b, "p825": k, "n": n} for (a, b, k), n in dis.most_common(40)]
json.dump(val, open(os.path.join(ROOT, "work", "validation.json"), "w"), indent=1, ensure_ascii=False)
json.dump({"form": S.FORM, "alias": ALIAS, "dkey": DKEY}, open(os.path.join(ROOT, "work", "forms.json"), "w"), ensure_ascii=False)
print("agreement core", val["core_rules"]["ALL"], "held-out aliases", val["rules_plus_heldout_aliases"]["ALL"], "aliases", len(ALIAS))
del records

# ---- pass 2: write every church ---------------------------------------------
out = gzip.open(os.path.join(ROOT, "data", "churches.csv.gz"), "wt", newline="", encoding="utf-8")
w = csv.writer(out); w.writerow(["qid", "country", "lon", "lat", "label", "dedication", "all_dedications", "source", "p825"])
counts = {}; seen = set()
for c in CC:
    n = collections.Counter()
    for q, lon, lat, label, parsed, pk, ded in churches(c):
        n["raw_unique"] += 1
        if lon is None: n["outside_frame_or_no_point"] += 1; continue
        if q in seen: n["duplicate_other_country"] += 1; continue
        seen.add(q)
        parsed = apply(parsed, ALIAS)
        if pk:
            order = [k for k in parsed if k in pk] + [k for k in sorted(pk, key=lambda k: -sum(freq[x] for x in ded if DKEY.get(x) == k)) if k not in parsed]
            keys, src = order, "P825"
        elif parsed: keys, src = parsed, "label"
        else: keys, src = [], "none"
        n["src_" + src] += 1; n["kept"] += 1
        w.writerow([q, c, f"{lon:.5f}", f"{lat:.5f}", label.replace("\n", " "), keys[0] if keys else "", "|".join(keys), src, "|".join(ded)])
    counts[c] = dict(n); print("pass 2", c, dict(n))
out.close()
json.dump(counts, open(os.path.join(ROOT, "work", "counts.json"), "w"), indent=1)
