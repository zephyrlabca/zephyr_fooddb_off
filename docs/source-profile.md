# Open Food Facts source profile (snapshot 2026-10-21)

Source: `source/food.parquet` from Hugging Face `openfoodfacts/product-database`,
repo commit dbdc38c7, 7.96 GB, 4,821,386 rows, 111 columns. Licence ODbL.
Profiled with DuckDB 1.5.6. The full pin (revision, SHA-256, size) is in the README. Scope filter: `countries_tags` contains
`en:united-states` or `en:canada`.

## Counts

| Set | Rows |
|---|---|
| US or Canada tagged | 1,114,892 |
| … with kcal, carbs, protein, fat per 100 g | 940,801 |
| … of which Canada | 111,341 |
| obsolete flag set | 0 |
| with a product name | 1,095,610 (en 1,017,514; fr 86,560) |
| with a brand | 762,087 |
| with serving_size text | 709,835 (697,575 parse to g or ml) |
| labelled per serving with a serving quantity | 337,893 |
| labelled per 100 ml | 59 |

## Nutriments

`nutriments` is a list of structs `{name, value, 100g, serving, unit, …}`.
`100g` is normalised to **grams** whatever the label unit (checked by median:
calcium `g` rows 0.0386, `mg` rows 0.021; sodium `g` 0.26, `mg` 0.167), except
`energy-kcal` which is kcal. Rule: read `100g`, multiply by 1000 for mg and
1,000,000 for µg. `value`/`unit` are the label as typed and are dirty
(`% DV`, `%`, `IU`, `mcg (400 IU)`, free text); ignore them except to drop a
value whose unit is a percentage.

Field coverage in the US/CA set (rows with a `100g` value): energy-kcal
960k, proteins 952k, fat 951k, carbohydrates 950k, sugars 895k, sodium 877k,
saturated-fat 856k, fiber 748k, cholesterol 516k, iron 485k, calcium 466k,
trans-fat 457k, potassium 319k, vitamin-c 267k, vitamin-a 258k, vitamin-d
160k, magnesium 84k, phosphorus 81k, zinc 79k, vitamin-b1 72k, manganese
72k, copper 72k, vitamin-b2 71k, vitamin-e 71k, vitamin-b6 70k, selenium
69k, mono 68k, poly 67k, starch 66k, vitamin-b12 65k, vitamin-b9 62k,
vitamin-pp 53k, vitamin-k 46k, choline 46k, pantothenic-acid 40k, iodine
35k, omega-3-fat 9k. Everything under 35k from there.

## Dirt

- 20,678 products have a macro above 100 g per 100 g or energy above 950
  kcal per 100 g. OFF's own tags agree: `nutrition-value-total-over-105`
  24,684, `energy-value-in-kcal-does-not-match…` 24,856,
  `over-3800-energy` 14,888.
- 11,025 products carry only per-serving values with no serving quantity, so
  no `100g` value exists.
- Vitamin A: 159,530 rows typed in IU. `100g` is already converted by OFF.
- Mean values are useless (a handful of rows carry values in the trillions);
  use medians or bounds.

## Codes

All digits. Lengths: 8 → 42,877; 13 → 1,031,956; 14 → 2,182; longer than 14
→ ~40k (not GTINs, internal or garbage); 9–12 → 19.

- 9,718 codes are below 1,000,000 as an integer.
- Only 3 kept codes collapse onto another when leading zeros are dropped.
  (An earlier count of 23,611 was an artefact: codes longer than 18 digits
  overflow a 64-bit cast and were counted as duplicates of each other.)

## Freshness

`last_modified_t` by year: 2020 179k (USDA import era), 2022 108k, 2023 88k,
2024 88k, 2025 233k, 2026 385k.
