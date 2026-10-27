## Title

[OC] Whose church is it? The patron saint of 208,005 churches across 12 Western European countries, mapped in 13 km hexagons: Martin rules northern France, Patrick Ireland, and Cornwall has the most varied saints in Europe

## Body (optional)

I took every church building with coordinates in Wikidata for twelve countries and worked out who each one is dedicated to, from Wikidata's 'dedicated to' field where it exists and otherwise by reading the name in eight languages (it agrees with the structured field 96% of the time where both exist).

Mary leads almost everywhere, so the map sets her aside. Then Peter leads 31% of hexagons, John 20% and Martin 13%. Saint Martin has 15% of churches in Picardie but 1.1% in the UK. Cornwall has 66 different saints per 100 churches; the Algarve has 23. In Ireland, Brigid has 23% of named holy wells but 3.3% of churches.

Caveat: Wikidata's coverage differs a lot by country, so everything is a share within a country or region.

Interactive version: https://tristan-hotham.github.io/saints-and-wells/

## Source comment

Source: Wikidata church buildings (Q16970) with coordinates and the property 'dedicated to' (P825), and Wikidata holy wells, CC0; NUTS 2016 level 2 regions from Eurostat GISCO (via github.com/eurostat/Nuts2json, © EuroGeographics for the administrative boundaries); country outlines from Natural Earth (public domain).

Tools: Python (a multilingual regular-expression name parser with a saint-name table built from Wikidata labels, shapely and pyproj for the equal-area hexagons and regions, NumPy, matplotlib).

Interactive: https://tristan-hotham.github.io/saints-and-wells/
Blog post: https://blog.tristanhotham.com/2026/10/27/saints-and-wells/
Paper: https://doi.org/10.5281/zenodo.23677171
