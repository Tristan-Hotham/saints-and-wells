# Whose Church Is It?

Which saint is each church in Western Europe dedicated to? 279,212 church buildings from Wikidata in the United Kingdom, Ireland, France, Belgium, the Netherlands, Luxembourg, Germany, Switzerland, Austria, Italy, Spain and Portugal, sorted by their patron, with a hexagon map of leading saints, regional patrons, a test of St Michael and high ground, St James and Santiago, and Ireland's holy wells.

**Interactive version:** https://tristan-hotham.github.io/saints-and-wells/
**Blog post:** https://blog.tristanhotham.com/2026/10/27/saints-and-wells/
**Paper and archived data:** https://doi.org/10.5281/zenodo.23677171

By Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

All shares are within a country or region, because Wikidata's coverage of churches differs a lot between countries.

- 208,005 of 279,212 churches (74%) have an identifiable dedication: 47,902 from Wikidata's 'dedicated to' field (P825) and 160,103 read from the church's name. Where both exist, the name reading agrees with P825 for 96.3% of 41,574 churches (aliases learned on the other half).
- Mary is the leading dedication in every country and in 85% of 20 km hexagons, from 9% of churches in Luxembourg and 15% in the United Kingdom to 38% in Portugal.
- With Mary, Christ, the Trinity, the Cross, the Holy Spirit, the Holy Family and All Saints set aside, Peter leads in 30% of hexagons, John in 22% and Martin in 13%. Martin has 7.9% of French churches and 14.9% in Picardie.
- Early saints of Ireland, Scotland, Wales, Cornwall and Brittany (117 names) hold 21.6% of Irish churches, 4.7% of British ones and 10.0% in Brittany.
- Variety: Cornwall and Isles of Scilly has 66.2 different dedications per 100 churches, the most of 176 regions; Algarve has 22.6.
- James: 6.6% of Spanish churches within 150 km of Santiago de Compostela, 2.1% at 500 to 750 km.
- Michael in Britain and Ireland: higher ground overall (median 70 m against 57 m) but not more often on local high points (6.7% against 6.2%).
- Ireland's holy wells: Brigid holds 23.1% of named wells but 3.3% of churches.

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

Wikidata church buildings with coordinates, extracted per country, deduplicated and clipped to the European parts of the twelve countries. Dedication from P825 where present; otherwise from the local-language name (then the English name) with a multilingual rule set: saint prefixes (St, Saint, Sankt, Hl., Sint, San, Santa, Santo, Santi, Sant', São ...), French hyphenated forms, German and Dutch compounds (Martinskirche, Nikolaikirche), and Marian and Christological titles. A name table maps language variants to one saint at the level of the name (John covers the Baptist and the Evangelist; every Marian title is Mary). It combines a hand-written core, the labels of the 2,129 dedication items in the data, and 91 aliases learned from churches that have both P825 and a name. Hexagons in ETRS89-LAEA; regions NUTS 2016 level 2.

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
