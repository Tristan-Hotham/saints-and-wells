# Whose Church Is It?

Which saint is each church in Western Europe dedicated to? {{n_churches|int}} church buildings from Wikidata in the United Kingdom, Ireland, France, Belgium, the Netherlands, Luxembourg, Germany, Switzerland, Austria, Italy, Spain and Portugal, sorted by their patron, with a hexagon map of leading saints, regional patrons, a test of St Michael and high ground, St James and Santiago, and Ireland's holy wells.

**Interactive version:** https://tristan-hotham.github.io/saints-and-wells/
**Blog post:** https://blog.tristanhotham.com/2026/10/27/saints-and-wells/
**Paper and archived data:** https://doi.org/10.5281/zenodo.23677171

By Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

All shares are within a country or region, because Wikidata's coverage of churches differs a lot between countries.

- {{n_identified|int}} of {{n_churches|int}} churches ({{share_identified|pct0}}) have an identifiable dedication: {{n_p825|int}} from Wikidata's 'dedicated to' field (P825) and {{n_label|int}} read from the church's name. Where both exist, the name reading agrees with P825 for {{validation.rules_plus_heldout_aliases.ALL.share|pct1}} of {{validation.rules_plus_heldout_aliases.ALL.both|int}} churches (aliases learned on the other half).
- Mary is the leading dedication in every country and in {{hex20.lead_any_cells.0.share|pct0}} of 20 km hexagons, from {{by_country.LU.share_mary|pct0}} of churches in Luxembourg and {{by_country.GB.share_mary|pct0}} in the United Kingdom to {{by_country.PT.share_mary|pct0}} in Portugal.
- With Mary, Christ, the Trinity, the Cross, the Holy Spirit, the Holy Family and All Saints set aside, Peter leads in {{hex20.lead_saint_cells.0.share|pct0}} of hexagons, John in {{hex20.lead_saint_cells.1.share|pct0}} and Martin in {{hex20.lead_saint_cells.2.share|pct0}}. Martin has {{selected.Martin.by_country.FR|pct1}} of French churches and {{selected.Martin.top_regions.0.share|pct1}} in {{selected.Martin.top_regions.0.name}}.
- Early saints of Ireland, Scotland, Wales, Cornwall and Brittany ({{celtic_n|raw}} names) hold {{by_country.IE.share_celtic|pct1}} of Irish churches, {{by_country.GB.share_celtic|pct1}} of British ones and {{celtic_bretagne|pct1}} in Brittany.
- Variety: {{richest.0.name}} has {{richest.0.richness100|f1}} different dedications per 100 churches, the most of {{n_regions_rich|raw}} regions; {{poorest.9.name}} has {{poorest.9.richness100|f1}}.
- James: {{james.bands.ES.0.share|pct1}} of Spanish churches within 150 km of Santiago de Compostela, {{james.bands.ES.3.share|pct1}} at 500 to 750 km.
- Michael in Britain and Ireland: higher ground overall (median {{michael.median_elev_michael|f0}} m against {{michael.median_elev_other|f0}} m) but not more often on local high points ({{michael.share_top_michael|pct1}} against {{michael.share_top_other|pct1}}).
- Ireland's holy wells: Brigid holds {{wells.ie_top.0.share|pct1}} of named wells but {{wells.ie_top.0.church_share|pct1}} of churches.

## Files

- `index.html`: the interactive page (Leaflet map, charts); `header.png`: social card.
- `data/churches.csv.gz`: one row per church: Wikidata QID, country, lon, lat, label, dedication (primary), all dedications, source (P825, label or none), P825 QIDs. Gzipped CSV (about 6 MB, 23 MB unpacked).
- `data/country_dedications.csv`: churches and share of identified churches by country and dedication.
- `data/dedications.csv`: every dedication name with its type and counts by country.
- `data/regions.csv`: NUTS 2016 level 2 regions: churches, identified, top dedication, leading saint, Mary's share, variety (rarefied richness at 100), signature saint, shares of selected saints.
- `data/hex20_leading.geojson`: 20 km hexagons with the leading dedication and leading saint.
- `data/holy_wells.csv`: Wikidata holy wells in the study countries with the dedication read.
- `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `data/geo/`: country outlines, background land and NUTS 2 regions used by the analysis.
- `code/`: Python scripts, run in order: `01_geo.py`, `02_parse.py`, `03_analyse.py`, `04_build_site.py`, `05_header.py`. `saints.py` holds the name parser and normalisation table; `dem.py` the terrain lookup; `shots.py` renders check screenshots. `release/` holds the paper, blog figures and Zenodo files; `reddit/` the collage.

## Method in brief

Wikidata church buildings with coordinates, extracted per country, deduplicated and clipped to the European parts of the twelve countries. Dedication from P825 where present; otherwise from the local-language name (then the English name) with a multilingual rule set: saint prefixes (St, Saint, Sankt, Hl., Sint, San, Santa, Santo, Santi, Sant', São ...), French hyphenated forms, German and Dutch compounds (Martinskirche, Nikolaikirche), and Marian and Christological titles. A name table maps language variants to one saint at the level of the name (John covers the Baptist and the Evangelist; every Marian title is Mary). It combines a hand-written core, the labels of the {{n_ded_items|int}} dedication items in the data, and {{validation.n_aliases|raw}} aliases learned from churches that have both P825 and a name. Hexagons in ETRS89-LAEA; regions NUTS 2016 level 2.

Caveats: this is a map of Wikidata, whose coverage and use of P825 vary by country; the name reader is checked only where P825 exists; dedications can change over time; small hexagons often tie.

## Sources and licences

- Churches and holy wells: Wikidata (https://www.wikidata.org), CC0.
- Regions: Eurostat GISCO NUTS 2016 (via https://github.com/eurostat/Nuts2json), © EuroGeographics for the administrative boundaries.
- Country outlines: Natural Earth (public domain).
- Terrain for the Michael test: AWS Terrain Tiles by Mapzen/Tilezen (zoom 10), sources including SRTM, GMTED2010, ETOPO1 and national datasets; attribution https://github.com/tilezen/joerd/blob/master/docs/attribution.md. Not included here.
- Base map tiles on the page: Esri. Map library: Leaflet.

Derived data, text and figures: CC BY 4.0. Code: MIT (see `LICENSE`).

## Rerun

Python 3 with numpy, scipy, shapely, pyproj, matplotlib and playwright. Set `WD_DIR` to the folder of Wikidata extracts (`ch_<CC>.json`, `ded_labels.json`, `holywells.json`; SPARQL extracts of church buildings with P625 and P825 per country), and `DEM_BIN`/`DEM_IDX` for the terrain tiles, then run the scripts in order.

## Citation

Hotham, T. (2026) *Whose Church Is It? Church dedications and holy wells across Western Europe*. Zenodo. https://doi.org/10.5281/zenodo.23677171

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
