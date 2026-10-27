"""r/dataisbeautiful collage: 'Whose church is it?' Gold leaf on lapis, a mosaic of 13 km hexagons.
Reads ../data/results.json, ../work/hex.json (code/03_analyse.py) and ../data/geo.
Fonts: FONT_DIR with FrauncesVar.ttf, SourceSerif4-*.ttf, IBMPlexMono-*.ttf.
Run: python3 collage.py
"""
import os, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle, RegularPolygon
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts") + "/"
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, GOLD, GOLD2, LAND = "#F4EEDF", "#24190F", "#6E5F4A", "#B8902A", "#A87A12", "#E8DEC6"
RED, LAPIS = "#B3261E", "#1F3A8A"
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
HX = json.load(open(os.path.join(ROOT, "work", "hex.json")))
PAL = {"Peter": "#3E6FC4", "John": "#1E9C8A", "Martin": "#C8372D", "Michael": "#D9A520", "Anthony": "#A0683A", "Nicholas": "#8657C2",
       "Joseph": "#97A12E", "Roch": "#D46A9A", "James": "#E57F2B", "Andrew": "#6FB3E3", "Patrick": "#3B9A48", "Sebastian": "#8A96A8"}
OTHER = "#CDBF9F"
laea = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True).transform
CTRY = [transform(laea, shape(f["geometry"])) for f in json.load(open(os.path.join(ROOT, "data", "geo", "countries.geojson")))["features"]]
CTX = [transform(laea, shape(f["geometry"])) for f in json.load(open(os.path.join(ROOT, "data", "geo", "context.geojson")))["features"]]
polys = lambda g: [g] if g.geom_type == "Polygon" else list(g.geoms)


def land(ax, ctx=True):
    if ctx:
        for g in CTX:
            for p in polys(g): ax.fill(*p.exterior.xy, color="#ECE4D0", lw=0, zorder=0)
    for g in CTRY:
        for p in polys(g): ax.fill(*p.exterior.xy, color=LAND, lw=0, zorder=0)


def frame(ax, x0=2.62e6, x1=5.05e6, y0=1.55e6, y1=4.15e6):
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")


fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
# illuminated border: double gold rule with corner hexagons
bd = fig.add_axes([0, 0, 1, 1]); bd.axis("off"); bd.set_xlim(0, 1); bd.set_ylim(0, 1)
for m, lw in [(.014, 2.2), (.020, .8)]:
    bd.add_patch(Rectangle((m, m * .8), 1 - 2 * m, 1 - 1.6 * m, fill=False, ec=GOLD2, lw=lw))
for x, y in [(.014, .0112), (.986, .0112), (.014, .9888), (.986, .9888)]:
    bd.add_patch(RegularPolygon((x, y), 6, radius=.011, orientation=0, fc=BG, ec=GOLD, lw=1.6, transform=bd.transAxes))
    bd.add_patch(RegularPolygon((x, y), 6, radius=.005, orientation=0, fc=GOLD, ec="none", transform=bd.transAxes))

# title block
fig.text(.05, .962, "Whose church is it?", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(.05, .903, f"The patron saint of {R['n_identified']:,} churches in twelve countries of Western Europe. Each hexagon (13 km) is coloured\n"
                    "by its most common saint, with Mary, Christ, the Trinity, the Cross and All Saints set aside.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.4)

# hero mosaic
ax = fig.add_axes([.01, .255, .63, .63], facecolor=BG); land(ax)
H = [h for h in HX["13"] if h["ni"] >= 5]
cols = [PAL.get(h["saint"], OTHER) for h in H]
pc = PolyCollection([list(zip(h["vx"], h["vy"])) for h in H], facecolors=cols, edgecolors=BG, linewidths=.25, zorder=2)
pc.set_alpha(None); ax.add_collection(pc)
fc = pc.get_facecolors(); fc[:, 3] = [.5 if h["saint_tie"] else 1 for h in H]; pc.set_facecolors(fc)
for g in CTRY:
    for p in polys(g): ax.plot(*p.exterior.xy, color=GOLD2, lw=.6, alpha=.8, zorder=3)
frame(ax)
# annotations on the hero map
A = [("Martin's France", (3.70e6, 2.95e6), (3.02e6, 3.16e6)), ("Patrick's Ireland", (3.25e6, 3.50e6), (2.68e6, 3.92e6)),
     ("Anthony's Portugal", (2.80e6, 2.05e6), (2.68e6, 1.70e6)), ("Roch in the Alps", (4.15e6, 2.48e6), (4.30e6, 2.30e6))]
for t, xy, xt in A:
    ax.annotate(t, xy=xy, xytext=xt, family=MONO, fontsize=11, color=FG, arrowprops=dict(arrowstyle="-", color=GOLD, lw=.9), zorder=5,
                bbox=dict(boxstyle="round,pad=.25", fc=BG, ec=GOLD, lw=.6, alpha=.92))

# legend
lg = fig.add_axes([.655, .66, .33, .18]); lg.axis("off"); lg.set_xlim(0, 1); lg.set_ylim(0, 1)
lg.text(0, 1.0, "LEADING SAINT", family=MONO, fontsize=11, color=MUT, va="top")
cnt = {d["key"]: d["share"] for d in R["hex13"]["lead_saint_cells"]}
items = list(PAL.items()) + [("Other saints", OTHER)]
for i, (k, c) in enumerate(items):
    x = 0 if i < 7 else .52; y = .82 - (i % 7) * .125
    lg.add_patch(RegularPolygon((x + .035, y), 6, radius=.035, orientation=0, fc=c, ec=GOLD, lw=.6, transform=lg.transAxes))
    s = f"{cnt[k] * 100:.0f}%" if k in cnt and cnt[k] >= .01 else ""
    lg.text(x + .09, y, k, family=MONO, fontsize=11.5, color=FG, va="center")
    if s: lg.text(x + .44, y, s, family=MONO, fontsize=10, color=MUT, va="center", ha="right")
lg.text(0, -.07, "% = share of hexagons it leads. Paler = tie.", family=MONO, fontsize=9.5, color=MUT, va="top")

# headline numbers
tx = fig.add_axes([.655, .285, .32, .345]); tx.axis("off")
c = R["by_country"]
notes = [(f"{R['hex13']['lead_any_cells'][0]['share'] * 100:.0f}%", f"of hexagons are led by Mary when she is\ncounted: {c['PT']['share_mary'] * 100:.0f}% of churches in Portugal,\n{c['GB']['share_mary'] * 100:.0f}% in the UK."),
         (f"{R['selected']['Martin']['top_regions'][0]['share'] * 100:.0f}%", f"of churches in Picardie are Saint Martin's,\nagainst {R['selected']['Martin']['by_country']['GB'] * 100:.1f}% across the Channel in the UK."),
         (f"{R['richest'][0]['richness100']:.0f} vs {R['poorest'][9]['richness100']:.0f}", "different saints per 100 churches in\nCornwall, Europe's most varied region,\nagainst the Algarve, its least."),
         (f"{R['wells']['ie_top'][0]['share'] * 100:.0f}%", f"of Ireland's named holy wells are\nBrigid's. She has {R['wells']['ie_top'][0]['church_share'] * 100:.1f}% of its churches.")]
for (big, small), y, col in zip(notes, [1.0, .73, .47, .21], [LAPIS, RED, "#2F7D4F", GOLD2]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=30, color=col, va="top", transform=tx.transAxes)
    tx.text(0, y - .095, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# small multiples: share of churches per 20 km hexagon
H20 = [h for h in HX["20"] if h["ni"] >= 10]
cel = set(R["celtic_members"])
cmap = matplotlib.colors.LinearSegmentedColormap.from_list("g", ["#EBDFC2", "#D9A02D", "#B3261E", "#5A0F0A"])
SM = [("Martin", "Martin"), ("Michael", "Michael"), ("Nicholas", "Nicholas"), ("James", "James"), ("Celtic saints", "Celtic saints"), ("Lambert", "Lambert")]
fig.text(.05, .248, "WHERE EACH SAINT'S SHARE IS HIGHEST  (share of churches per 20 km hexagon; darkest = top 3%)", family=MONO, fontsize=10.5, color=MUT)
for i, (k, lab) in enumerate(SM):
    a = fig.add_axes([.03 + i * .158, .08, .155, .135], facecolor=BG); land(a, ctx=False)
    v = np.array([(sum(n for kk, n in h["k"].items() if kk in cel) if k == "Celtic saints" else h["k"].get(k, 0)) / h["ni"] for h in H20])
    top = max(np.quantile(v, .97), .01)
    fcs = [cmap(min(x / top, 1)) if x > 0 else LAND for x in v]
    a.add_collection(PolyCollection([list(zip(h["vx"], h["vy"])) for h in H20], facecolors=fcs, edgecolors="none", zorder=2))
    frame(a, 2.62e6, 5.05e6, 1.55e6, 4.15e6)
    s = R["selected"][k]
    SHORT = {"Herefordshire, Worcestershire and Warwickshire": "Herefordshire", "Northern and Western": "NW Ireland"}
    nm = s['top_regions'][0]['name']; nm = SHORT.get(nm, nm)
    fig.text(.03 + i * .158 + .0775, .236, f"{lab}\ntop: {nm}", family=MONO, fontsize=10, color=FG, ha="center", va="top", linespacing=1.3)

fig.text(.05, .066, f"Data: Wikidata church buildings and holy wells (CC0); {R['n_churches']:,} churches, {R['n_identified']:,} with a dedication, from Wikidata's 'dedicated to'\n"
                    f"or read from the name (agrees with 'dedicated to' {R['validation']['rules_plus_heldout_aliases']['ALL']['share'] * 100:.0f}% of the time). Coverage varies by country, so all figures are shares\n"
                    "within a country or region. Regions: Eurostat NUTS 2016. Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=9.2, color=MUT, va="top", linespacing=1.45)
fig.savefig(os.path.join(HERE, "whose_church.png"), facecolor=BG, dpi=200)
print("ok")
