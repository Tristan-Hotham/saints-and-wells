"""Step 1: base geography.

Reads Natural Earth 1:10m admin 0 countries (public domain) and Eurostat GISCO
NUTS 2016 level 2 regions (via github.com/eurostat/Nuts2json, 1:20 million)
and writes small, simplified files to ../data/geo/:
  countries.geojson   the twelve study countries, European part only
  context.geojson     neighbouring land for the map background
  nuts2.geojson       NUTS 2016 level 2 regions of the twelve countries
  areas.json          land area (km2) of each study country inside the study frame

Source folders are given by environment variables NE_DIR and NUTS_DIR
(defaults: a scratch folder). Get them with:
  git clone --filter=blob:none --no-checkout --depth 1 https://github.com/nvkelso/natural-earth-vector ne
  (cd ne && git sparse-checkout set --no-cone geojson/ne_10m_admin_0_countries.geojson && git checkout)
  git clone --filter=blob:none --no-checkout --depth 1 https://github.com/eurostat/Nuts2json nuts
  (cd nuts && git sparse-checkout set --no-cone pub/v2/2016/4326/20M/nutsrg_2.json && git checkout)
Run: python3 01_geo.py
"""
import os, json
from shapely.geometry import shape, mapping, box
from shapely.ops import transform, unary_union
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
SCR = "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/sw"
NE = os.environ.get("NE_DIR", os.path.join(SCR, "ne"))
NUTS = os.environ.get("NUTS_DIR", os.path.join(SCR, "nuts"))
OUT = os.path.join(ROOT, "data", "geo"); os.makedirs(OUT, exist_ok=True)

CC = ["GB", "IE", "FR", "ES", "PT", "IT", "DE", "BE", "NL", "LU", "CH", "AT"]
A3 = {"GBR": "GB", "IRL": "IE", "FRA": "FR", "ESP": "ES", "PRT": "PT", "ITA": "IT", "DEU": "DE", "BEL": "BE", "NLD": "NL", "LUX": "LU", "CHE": "CH", "AUT": "AT"}
FRAME = box(-11.0, 35.6, 19.0, 61.0)          # study frame: Europe only (no Canaries, Azores, Madeira, overseas France)
VIEW = box(-14.0, 34.0, 24.0, 62.0)           # background land
laea = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True).transform


def rnd(g, nd=3):
    return json.loads(json.dumps(mapping(g)), parse_float=lambda s: round(float(s), nd))


ne = json.load(open(os.path.join(NE, "geojson", "ne_10m_admin_0_countries.geojson")))
feats, ctx, areas = [], [], {}
for f in ne["features"]:
    p = f["properties"]; g = shape(f["geometry"])
    if not g.intersects(VIEW):
        continue
    a3 = p["ADM0_A3"]
    if a3 in A3:
        c = A3[a3]; gi = g.intersection(FRAME)
        areas[c] = round(transform(laea, gi).area / 1e6)
        feats.append({"type": "Feature", "properties": {"cc": c, "name": p["NAME_EN"]}, "geometry": rnd(gi.simplify(0.01, preserve_topology=True))})
    else:
        gi = g.intersection(VIEW)
        if not gi.is_empty:
            ctx.append(gi.simplify(0.02, preserve_topology=True))
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "countries.geojson"), "w"), separators=(",", ":"))
json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": rnd(unary_union(ctx))}]},
          open(os.path.join(OUT, "context.geojson"), "w"), separators=(",", ":"))
json.dump(areas, open(os.path.join(OUT, "areas.json"), "w"), indent=1)
print("countries", len(feats), "areas", areas)

nu = json.load(open(os.path.join(NUTS, "pub", "v2", "2016", "4326", "20M", "nutsrg_2.json")))
nf = []
for f in nu["features"]:
    i = f["properties"]["id"]; c = {"UK": "GB", "EL": "GR"}.get(i[:2], i[:2])
    if c not in CC:
        continue
    g = shape(f["geometry"]).intersection(FRAME)
    if g.is_empty:
        continue
    nf.append({"type": "Feature", "properties": {"id": i, "name": f["properties"]["na"], "cc": c, "km2": round(transform(laea, g).area / 1e6)},
               "geometry": rnd(g.simplify(0.01, preserve_topology=True))})
json.dump({"type": "FeatureCollection", "features": nf}, open(os.path.join(OUT, "nuts2.geojson"), "w"), separators=(",", ":"))
print("nuts2", len(nf))
