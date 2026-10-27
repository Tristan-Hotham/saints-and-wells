"""Render index.html with Playwright Chromium at 1280px and 390px, light and dark, for checking.
Screenshots go to ../_shots/ (not part of the published site).

Usage: python3 shots.py [--fonts DIR] [--leaflet DIR]
Where Google Fonts and cdnjs are unreachable, pass folders holding the font files
(FrauncesVar.ttf, SourceSerif4-*.ttf, IBMPlexMono-*.ttf) and leaflet/dist. Map tiles are blocked.
"""
import asyncio, os, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
FD, LD = arg("--fonts"), arg("--leaflet")
OUT = os.path.join(ROOT, "_shots"); os.makedirs(OUT, exist_ok=True)
FONTCSS = (f"@font-face{{font-family:'Fraunces';font-weight:100 900;src:url(file://{FD}/FrauncesVar.ttf)}}"
           f"@font-face{{font-family:'Source Serif 4';font-weight:400;src:url(file://{FD}/SourceSerif4-Regular.ttf)}}"
           f"@font-face{{font-family:'Source Serif 4';font-weight:600;src:url(file://{FD}/SourceSerif4-Semibold.ttf)}}"
           f"@font-face{{font-family:'Source Serif 4';font-style:italic;src:url(file://{FD}/SourceSerif4-It.ttf)}}"
           f"@font-face{{font-family:'IBM Plex Mono';font-weight:400;src:url(file://{FD}/IBMPlexMono-Regular.ttf)}}"
           f"@font-face{{font-family:'IBM Plex Mono';font-weight:500;src:url(file://{FD}/IBMPlexMono-Medium.ttf)}}")


async def route(r):
    u = r.request.url
    if FD and "fonts.googleapis.com" in u: return await r.fulfill(body=FONTCSS, content_type="text/css")
    if LD and "leaflet.min.js" in u: return await r.fulfill(path=os.path.join(LD, "leaflet.js"), content_type="application/javascript")
    if LD and "leaflet.min.css" in u: return await r.fulfill(path=os.path.join(LD, "leaflet.css"), content_type="text/css")
    if u.startswith("file://"): return await r.continue_()
    return await r.abort()


async def shoot(b, width, theme):
    ctx = await b.new_context(viewport={"width": width, "height": 900}, color_scheme=theme, device_scale_factor=1)
    pg = await ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.route("**/*", route)
    await pg.goto("file://" + os.path.abspath(os.path.join(ROOT, "index.html")))
    await pg.wait_for_timeout(2500)
    sw = await pg.evaluate("document.documentElement.scrollWidth")
    tag = f"{width}_{theme}"
    await pg.screenshot(path=os.path.join(OUT, f"full_{tag}.png"), full_page=True)
    fig = await pg.query_selector(".figure.bleed")
    await fig.scroll_into_view_if_needed()
    for m in ["saint", "any", "one", "wells"]:
        await pg.evaluate(f"window.__mode('{m}')"); await pg.wait_for_timeout(900)
        await fig.screenshot(path=os.path.join(OUT, f"map_{m}_{tag}.png"))
    for sel in ["#maryc", "#matrix", "#sig", "#jamesc", "#heightc", "#richc", "#wellc", "#ctab", "#valc"]:
        e = await pg.query_selector(sel); await e.scroll_into_view_if_needed()
        par = await e.evaluate_handle("n => n.closest('.figure') || n")
        await par.as_element().screenshot(path=os.path.join(OUT, f"fig_{sel[1:]}_{tag}.png"))
    print(tag, "scrollWidth", sw, "errors", errs[:5])
    await ctx.close()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w in (1280, 390):
            for t in ("light", "dark"): await shoot(b, w, t)
        await b.close()

asyncio.run(main())
