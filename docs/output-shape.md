# Output shape

`barcode_v1.db` is SQLite in the shape ZephyrFit's bundled food catalog uses,
so the app reads either file with the same statements. The DDL is in
`scripts/build_barcode_db.py` (`DDL`, `INDEXES`).

| Table | One row per | Notes |
|---|---|---|
| `catalog_food` | product | `food_id`, `food_name` (display name), `brand_name`, `base_amount` 100, `base_unit` `g` or `ml`, the four macros per base, `barcode` as the digit string Open Food Facts stores, leading zeros kept |
| `catalog_food_nutrient` | product × nutrient | `nutrient_id` from `catalog_nutrient_type`; `amount` per base in the type's `default_unit` (G, MG, UG) |
| `catalog_food_portion` | product | exactly one: `1 serving` (unit 1) with the label's serving text as `modifier` and its gram weight, or the fallback `100 g` (unit 0, `is_fallback` 1); `portion_id = food_id × 10 + 1` |
| `catalog_food_portion_unit` | unit | 0 = `g`, 1 = `serving` |
| `food_name` | product × language | every language the label carries; `main` is mapped to the product's language |
| `catalog_nutrient_type`, `catalog_food_category` | reference | copied from `data/catalog_reference.db`; `food_category_id` is never set |
| `catalog_metadata` | file | `version`, a SHA-256 over the food rows, `food_count` |

## Ids

`food_id` is a serial in a block per source. Block 1, this import, starts at
100,000,001. An id is assigned to a barcode the first time the barcode is
kept and is recorded in `data/barcode_id_map.csv` (`code,food_id`); a rebuild
reads the map first and only appends, so an id never changes meaning and a
product that leaves the source keeps its id reserved. A new source (another
market, another database) takes the next 100,000,000 block.

## Gates

A product is kept when all of these hold; the build report counts each drop
reason.

- tagged `en:united-states` or `en:canada` in `countries_tags`
- the code is 8 to 14 digits and at least 1,000,000 as an integer
- energy (kcal), carbohydrates, protein and fat per 100 g are all present
- energy 0 to 950 kcal per 100 g; each macro 0 to 100 g; the three macros
  sum to at most 105 g
- a product name in some language

Codes that are the same digits apart from leading zeros collapse to one row;
the most recently modified wins.

## Nutrients

Open Food Facts normalises `nutriments[*]."100g"` to grams whatever the
label's unit (energy excepted, which is kcal). The pipeline reads that value
and multiplies by 1,000 for types whose default unit is mg and 1,000,000 for
µg. Entries typed as a percentage are dropped; a value above 100 g per 100 g
is dropped. Omega-3 marine (9902) is EPA + DPA + DHA. The map is `NUTRIENTS`
in the script; 36 of the catalog's 41 types have a source in Open Food Facts.

## Names and base

`food_name` is the English name, else the product's own language, else the
`main` entry, else the first non-empty name. `base_unit` is `ml` only when
the label says `nutrition_data_per = 100ml`.
