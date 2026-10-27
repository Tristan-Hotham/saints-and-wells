"""Render ../header.png (1200x630 social card) with Playwright Chromium.

A mosaic of 13 km hexagons coloured by leading saint (Mary and Christ set aside),
on vellum with gold and lapis. Fonts: pass a folder of TTFs as FONT_DIR (FrauncesVar.ttf,
SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf, IBMPlexMono-Medium.ttf);
otherwise the system serif is used.
Run: python3 05_header.py
"""
import os, json
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
H = [h for h in json.load(open(os.path.join(ROOT, "work", "hex.json")))["13"] if h["ni"] >= 5]
FD = os.environ.get("FONT_DIR", "")
PAL = {"Peter": "#3E6FC4", "John": "#1E9C8A", "Martin": "#C8372D", "Michael": "#D9A520", "Anthony": "#A0683A", "Nicholas": "#8657C2",
       "Joseph": "#97A12E", "Roch": "#D46A9A", "James": "#E57F2B", "Andrew": "#6FB3E3", "Patrick": "#3B9A48", "Sebastian": "#8A96A8"}
xs = [x for h in H for x in h["vx"]]; ys = [y for h in H for y in h["vy"]]
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
HH = 600; sc = HH / (y1 - y0); WW = (x1 - x0) * sc
polys = []
for h in H:
    pts = " ".join(f"{(x - x0) * sc:.1f},{(y1 - y) * sc:.1f}" for x, y in zip(h["vx"], h["vy"]))
    c = PAL.get(h["saint"], "#CDBF9F"); op = .45 if h["saint_tie"] else .95
    polys.append(f'<polygon points="{pts}" fill="{c}" fill-opacity="{op}"/>')
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:#F4EEDF;color:#24190F;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:64px;top:70px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#6E5F4A;display:flex;gap:12px;align-items:center}}
.k b{{background:#B3261E;color:#fff;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:60px;top:120px;margin:0;font:900 88px/.9 Fraunces,Georgia,serif;letter-spacing:-.02em}}
h1 em{{font-style:italic;font-weight:600;color:#A87A12;display:block}}
p{{position:absolute;left:64px;top:430px;width:500px;margin:0;font-size:25px;line-height:1.36;color:#24190F}}
.f{{position:absolute;left:64px;bottom:40px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#6E5F4A}}
.rule{{position:absolute;left:64px;top:405px;width:470px;border-top:5px double #B8902A}}
svg{{position:absolute;right:30px;top:15px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Faith × landscape</span></div>
<h1>Whose church<em>is it?</em></h1>
<div class="rule"></div>
<p>{R['n_churches']:,} churches in twelve countries, sorted by their patron saint.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{WW:.0f}" height="{HH}" viewBox="0 0 {WW:.0f} {HH}"><g stroke="#F4EEDF" stroke-width=".4">{''.join(polys)}</g></svg>
</body></html>"""
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
print("header.png written")
