#!/usr/bin/env python3
"""Build the barcode food database from the Open Food Facts Parquet export.

Output: a SQLite file in ZephyrFit's catalog shape (the catalog_* tables plus
food_name for label languages), one row per US/Canada product the shape can
hold, ids from a persistent map. See README.md for the source pin, the gates
and the licence.

  .venv/bin/python scripts/build_barcode_db.py \
      --source source/food.parquet --bundled data/catalog_reference.db \
      --output build/barcode_v1.db --id-map data/barcode_id_map.csv \
      --report build/report.md
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import random
import sqlite3
from pathlib import Path

import duckdb

ID_BLOCK_START = 100_000_000  # block 1 = this Open Food Facts import; ids start at +1
VERSION = "barcodev1"
SNAPSHOT = "2026-10-21"

# OFF nutriment name -> (app nutrient_id, factor from the normalised gram value)
NUTRIENTS = {
    "starch": (1009, 1),
    "fiber": (1079, 1),
    "calcium": (1087, 1e3),
    "iron": (1089, 1e3),
    "magnesium": (1090, 1e3),
    "phosphorus": (1091, 1e3),
    "potassium": (1092, 1e3),
    "sodium": (1093, 1e3),
    "zinc": (1095, 1e3),
    "copper": (1098, 1e3),
    "iodine": (1100, 1e6),
    "manganese": (1101, 1e3),
    "selenium": (1103, 1e6),
    "vitamin-a": (1106, 1e6),
    "vitamin-e": (1109, 1e3),
    "vitamin-d": (1114, 1e6),
    "vitamin-c": (1162, 1e3),
    "vitamin-b1": (1165, 1e3),
    "vitamin-b2": (1166, 1e3),
    "vitamin-pp": (1167, 1e3),
    "pantothenic-acid": (1170, 1e3),
    "vitamin-b6": (1175, 1e3),
    "biotin": (1176, 1e6),
    "vitamin-b12": (1178, 1e6),
    "choline": (1180, 1e3),
    "vitamin-k": (1185, 1e6),
    "vitamin-b9": (1190, 1e6),  # plain folate, not DFE
    "cholesterol": (1253, 1e3),
    "trans-fat": (1257, 1),
    "saturated-fat": (1258, 1),
    "monounsaturated-fat": (1292, 1),
    "polyunsaturated-fat": (1293, 1),
    "sugars": (2000, 1),
    "omega-3-fat": (9901, 1),
    "omega-6-fat": (9903, 1),
}
# 9902 omega-3 marine = EPA + DPA + DHA when any is present
MARINE = ("eicosapentaenoic-acid", "docosapentaenoic-acid", "docosahexaenoic-acid")
PERCENT_UNITS = ("%", "% DV", "%DV", "% dv")

DDL = """
CREATE TABLE catalog_food_category (food_category_id INTEGER PRIMARY KEY, description TEXT);
CREATE TABLE catalog_food (
    food_id INTEGER PRIMARY KEY,
    food_name TEXT NOT NULL,
    brand_name TEXT,
    food_category_id INTEGER REFERENCES catalog_food_category(food_category_id),
    base_amount REAL NOT NULL DEFAULT 100,
    base_unit TEXT NOT NULL DEFAULT 'g',
    calories_kcal REAL NOT NULL,
    carbs_g REAL NOT NULL,
    protein_g REAL NOT NULL,
    fat_g REAL NOT NULL,
    barcode TEXT
);
CREATE TABLE catalog_nutrient_type (nutrient_id INTEGER PRIMARY KEY, default_unit TEXT, display_name TEXT);
CREATE TABLE catalog_food_nutrient (
    food_id INTEGER NOT NULL REFERENCES catalog_food(food_id) ON DELETE CASCADE,
    nutrient_id INTEGER NOT NULL REFERENCES catalog_nutrient_type(nutrient_id) ON DELETE CASCADE,
    amount REAL,
    PRIMARY KEY (food_id, nutrient_id)
) WITHOUT ROWID;
CREATE TABLE catalog_food_portion_unit (portion_unit_id INTEGER PRIMARY KEY, unit_name TEXT);
CREATE TABLE catalog_food_portion (
    portion_id INTEGER PRIMARY KEY,
    food_id INTEGER NOT NULL REFERENCES catalog_food(food_id) ON DELETE CASCADE,
    sequence_number INTEGER,
    amount REAL,
    portion_unit_id INTEGER REFERENCES catalog_food_portion_unit(portion_unit_id),
    modifier TEXT,
    gram_weight REAL NOT NULL,
    is_fallback INTEGER NOT NULL DEFAULT 0 CHECK (is_fallback IN (0, 1))
);
CREATE TABLE catalog_metadata (version TEXT PRIMARY KEY, created_at TEXT, content_hash TEXT, food_count INTEGER);
CREATE TABLE food_name (
    food_id INTEGER NOT NULL REFERENCES catalog_food(food_id) ON DELETE CASCADE,
    lang TEXT NOT NULL,
    name TEXT NOT NULL,
    qualifier TEXT,
    PRIMARY KEY (food_id, lang)
) WITHOUT ROWID;
"""
INDEXES = """
CREATE UNIQUE INDEX idx_catalog_food_barcode ON catalog_food(barcode);
CREATE INDEX idx_catalog_food_name ON catalog_food(food_name);
CREATE INDEX idx_catalog_food_portion_food ON catalog_food_portion(food_id);
CREATE INDEX idx_food_name_name ON food_name(name);
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--bundled", type=Path, required=True, help="SQLite with catalog_nutrient_type and catalog_food_category (data/catalog_reference.db)")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--id-map", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    con = duckdb.connect()
    con.sql("SET preserve_insertion_order = false")
    src = str(args.source.resolve())

    # ---- 1. scope and shape gates -------------------------------------------------
    con.sql(f"""
    CREATE TABLE scoped AS
    SELECT code, try_cast(code AS BIGINT) AS canonical, lang, product_name, brands,
           nutrition_data_per, serving_size, try_cast(serving_quantity AS DOUBLE) AS serving_qty,
           last_modified_t, nutriments, countries_tags,
           list_filter(nutriments, x -> x.name = 'energy-kcal')[1]."100g" AS kcal,
           list_filter(nutriments, x -> x.name = 'carbohydrates')[1]."100g" AS carbs,
           list_filter(nutriments, x -> x.name = 'proteins')[1]."100g" AS protein,
           list_filter(nutriments, x -> x.name = 'fat')[1]."100g" AS fat
    FROM '{src}'
    WHERE list_contains(countries_tags, 'en:united-states') OR list_contains(countries_tags, 'en:canada')
    """)
    counts = {"scoped": con.sql("SELECT count(*) FROM scoped").fetchone()[0]}

    con.sql("""
    CREATE TABLE gated AS
    SELECT *,
      CASE
        WHEN NOT regexp_matches(code, '^[0-9]{8,14}$') THEN 'code_not_gtin'
        WHEN canonical < 1000000 THEN 'code_below_1e6'
        WHEN kcal IS NULL OR carbs IS NULL OR protein IS NULL OR fat IS NULL THEN 'macro_missing'
        WHEN kcal < 0 OR kcal > 950 THEN 'kcal_impossible'
        WHEN carbs < 0 OR carbs > 100 OR protein < 0 OR protein > 100 OR fat < 0 OR fat > 100 THEN 'macro_over_100g'
        WHEN carbs + protein + fat > 105 THEN 'macro_sum_over_105'
        WHEN len(list_filter(product_name, x -> x.text IS NOT NULL AND trim(x.text) <> '')) = 0 THEN 'no_name'
        ELSE NULL
      END AS drop_reason
    FROM scoped
    """)
    for reason, n in con.sql("SELECT coalesce(drop_reason,'kept'), count(*) FROM gated GROUP BY 1 ORDER BY 2 DESC").fetchall():
        counts[reason] = n

    # ---- 2. dedupe: same digits, different leading zeros -> newest wins ------------
    con.sql("""
    CREATE TABLE kept AS
    SELECT * EXCLUDE (rn) FROM (
      SELECT *, row_number() OVER (PARTITION BY canonical ORDER BY last_modified_t DESC, length(code) DESC, code) AS rn
      FROM gated WHERE drop_reason IS NULL)
    WHERE rn = 1
    """)
    counts["dedupe_collapsed"] = counts["kept"] - con.sql("SELECT count(*) FROM kept").fetchone()[0]
    counts["kept"] = con.sql("SELECT count(*) FROM kept").fetchone()[0]

    # ---- 3. ids from the persistent map --------------------------------------------
    id_map: dict[str, int] = {}
    if args.id_map.exists():
        with args.id_map.open(newline="") as f:
            for row in csv.DictReader(f):
                id_map[row["code"]] = int(row["food_id"])
    next_id = max([ID_BLOCK_START] + list(id_map.values())) + 1
    new_codes = [r[0] for r in con.sql("SELECT code FROM kept ORDER BY canonical, code").fetchall() if r[0] not in id_map]
    for code in new_codes:
        id_map[code] = next_id
        next_id += 1
    args.id_map.parent.mkdir(parents=True, exist_ok=True)
    with args.id_map.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "food_id"])
        for code, fid in sorted(id_map.items(), key=lambda kv: kv[1]):
            w.writerow([code, fid])
    counts["ids_new"] = len(new_codes)
    counts["ids_total_in_map"] = len(id_map)
    con.sql("CREATE TABLE ids (code VARCHAR, food_id BIGINT)")
    con.executemany("INSERT INTO ids VALUES (?, ?)", [(c, i) for c, i in id_map.items()])

    # ---- 4. the catalog rows --------------------------------------------------------
    con.sql("""
    CREATE TABLE food AS
    SELECT i.food_id, k.code AS barcode,
      coalesce(
        nullif(trim(list_filter(k.product_name, x -> x.lang = 'en')[1].text), ''),
        nullif(trim(list_filter(k.product_name, x -> x.lang = k.lang)[1].text), ''),
        nullif(trim(list_filter(k.product_name, x -> x.lang = 'main')[1].text), ''),
        trim(list_filter(k.product_name, x -> x.text IS NOT NULL AND trim(x.text) <> '')[1].text)
      ) AS food_name,
      nullif(trim(k.brands), '') AS brand_name,
      CASE WHEN k.nutrition_data_per = '100ml' THEN 'ml' ELSE 'g' END AS base_unit,
      round(k.kcal, 3) AS calories_kcal, round(k.carbs, 3) AS carbs_g,
      round(k.protein, 3) AS protein_g, round(k.fat, 3) AS fat_g,
      k.lang, k.product_name, k.nutriments, k.serving_size, k.serving_qty
    FROM kept k JOIN ids i USING (code)
    """)
    con.sql("""
    CREATE TABLE nutrient AS
    SELECT food_id, nutrient_id, round(sum(amount), 4) AS amount FROM (
      SELECT f.food_id,
        CASE n.name
          WHEN 'starch' THEN 1009 WHEN 'fiber' THEN 1079 WHEN 'calcium' THEN 1087 WHEN 'iron' THEN 1089
          WHEN 'magnesium' THEN 1090 WHEN 'phosphorus' THEN 1091 WHEN 'potassium' THEN 1092 WHEN 'sodium' THEN 1093
          WHEN 'zinc' THEN 1095 WHEN 'copper' THEN 1098 WHEN 'iodine' THEN 1100 WHEN 'manganese' THEN 1101
          WHEN 'selenium' THEN 1103 WHEN 'vitamin-a' THEN 1106 WHEN 'vitamin-e' THEN 1109 WHEN 'vitamin-d' THEN 1114
          WHEN 'vitamin-c' THEN 1162 WHEN 'vitamin-b1' THEN 1165 WHEN 'vitamin-b2' THEN 1166 WHEN 'vitamin-pp' THEN 1167
          WHEN 'pantothenic-acid' THEN 1170 WHEN 'vitamin-b6' THEN 1175 WHEN 'biotin' THEN 1176 WHEN 'vitamin-b12' THEN 1178
          WHEN 'choline' THEN 1180 WHEN 'vitamin-k' THEN 1185 WHEN 'vitamin-b9' THEN 1190 WHEN 'cholesterol' THEN 1253
          WHEN 'trans-fat' THEN 1257 WHEN 'saturated-fat' THEN 1258 WHEN 'monounsaturated-fat' THEN 1292
          WHEN 'polyunsaturated-fat' THEN 1293 WHEN 'sugars' THEN 2000 WHEN 'omega-3-fat' THEN 9901 WHEN 'omega-6-fat' THEN 9903
          WHEN 'eicosapentaenoic-acid' THEN 9902 WHEN 'docosapentaenoic-acid' THEN 9902 WHEN 'docosahexaenoic-acid' THEN 9902
        END AS nutrient_id,
        n."100g" * CASE
          WHEN n.name IN ('calcium','iron','magnesium','phosphorus','potassium','sodium','zinc','copper','manganese',
                          'vitamin-e','vitamin-c','vitamin-b1','vitamin-b2','vitamin-pp','pantothenic-acid','vitamin-b6',
                          'choline','cholesterol') THEN 1e3
          WHEN n.name IN ('iodine','selenium','vitamin-a','vitamin-d','biotin','vitamin-b12','vitamin-k','vitamin-b9') THEN 1e6
          ELSE 1 END AS amount
      FROM food f, unnest(f.nutriments) AS t(n)
      WHERE n."100g" IS NOT NULL AND n."100g" >= 0 AND n."100g" <= 100
        AND (n.unit IS NULL OR n.unit NOT LIKE '%\\%%' ESCAPE '\\')
    ) WHERE nutrient_id IS NOT NULL
    GROUP BY food_id, nutrient_id
    """)
    con.sql("""
    CREATE TABLE portion AS
    SELECT food_id * 10 + 1 AS portion_id, food_id, 1 AS sequence_number,
      CASE WHEN serving_qty > 0 AND serving_qty <= 5000 THEN 1.0 ELSE 100.0 END AS amount,
      CASE WHEN serving_qty > 0 AND serving_qty <= 5000 THEN 1 ELSE 0 END AS portion_unit_id,
      CASE WHEN serving_qty > 0 AND serving_qty <= 5000
           THEN left(regexp_replace(coalesce(nullif(trim(serving_size), ''), '1 serving'), '\\s+', ' ', 'g'), 80)
           ELSE '100 g' END AS modifier,
      CASE WHEN serving_qty > 0 AND serving_qty <= 5000 THEN round(serving_qty, 3) ELSE 100.0 END AS gram_weight,
      CASE WHEN serving_qty > 0 AND serving_qty <= 5000 THEN 0 ELSE 1 END AS is_fallback
    FROM food
    """)
    con.sql("""
    CREATE TABLE name AS
    SELECT food_id, lang, name FROM (
      SELECT f.food_id,
        CASE WHEN pn.lang = 'main' THEN coalesce(f.lang, 'en') ELSE pn.lang END AS lang,
        left(regexp_replace(trim(pn.text), '\\s+', ' ', 'g'), 200) AS name,
        row_number() OVER (PARTITION BY f.food_id, CASE WHEN pn.lang = 'main' THEN coalesce(f.lang, 'en') ELSE pn.lang END
                           ORDER BY CASE WHEN pn.lang = 'main' THEN 1 ELSE 0 END) AS rn
      FROM food f, unnest(f.product_name) AS t(pn)
      WHERE pn.text IS NOT NULL AND trim(pn.text) <> '' AND pn.lang IS NOT NULL AND length(pn.lang) BETWEEN 2 AND 3
    ) WHERE rn = 1
    """)

    # ---- 5. write SQLite ------------------------------------------------------------
    out = args.output.resolve()
    if out.exists():
        out.unlink()
    out.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(out)
    db.executescript(DDL)
    bundled = sqlite3.connect(f"file:{args.bundled.resolve()}?mode=ro", uri=True)
    db.executemany("INSERT INTO catalog_food_category VALUES (?, ?)", bundled.execute("SELECT food_category_id, description FROM catalog_food_category"))
    db.executemany("INSERT INTO catalog_nutrient_type VALUES (?, ?, ?)", bundled.execute("SELECT nutrient_id, default_unit, display_name FROM catalog_nutrient_type"))
    bundled.close()
    db.executemany("INSERT INTO catalog_food_portion_unit VALUES (?, ?)", [(0, "g"), (1, "serving")])
    db.commit()
    db.close()

    con.sql("INSTALL sqlite; LOAD sqlite;")
    con.sql(f"ATTACH '{out}' AS out (TYPE sqlite)")
    con.sql("""INSERT INTO out.catalog_food (food_id, food_name, brand_name, food_category_id, base_amount, base_unit,
                 calories_kcal, carbs_g, protein_g, fat_g, barcode)
               SELECT food_id, left(regexp_replace(food_name, '\\s+', ' ', 'g'), 200), left(brand_name, 120), NULL, 100, base_unit,
                 calories_kcal, carbs_g, protein_g, fat_g, barcode FROM food ORDER BY food_id""")
    con.sql("INSERT INTO out.catalog_food_nutrient SELECT food_id, nutrient_id, amount FROM nutrient ORDER BY food_id, nutrient_id")
    con.sql("INSERT INTO out.catalog_food_portion SELECT * FROM portion ORDER BY portion_id")
    con.sql("INSERT INTO out.food_name SELECT food_id, lang, name, NULL FROM name ORDER BY food_id, lang")
    con.sql("DETACH out")

    db = sqlite3.connect(out)
    db.executescript(INDEXES)
    food_count = db.execute("SELECT count(*) FROM catalog_food").fetchone()[0]
    h = hashlib.sha256()
    for row in db.execute("SELECT food_id, barcode, food_name, calories_kcal, carbs_g, protein_g, fat_g FROM catalog_food ORDER BY food_id"):
        h.update(repr(row).encode())
    db.execute("INSERT INTO catalog_metadata VALUES (?, NULL, ?, ?)", (VERSION, h.hexdigest(), food_count))
    db.commit()
    db.execute("VACUUM")
    db.close()

    # ---- 6. report --------------------------------------------------------------------
    types = {r[0]: r[1] for r in sqlite3.connect(out).execute("SELECT nutrient_id, display_name FROM catalog_nutrient_type")}
    coverage = con.sql("SELECT nutrient_id, count(*) FROM nutrient GROUP BY 1 ORDER BY 2 DESC").fetchall()
    langs = con.sql("SELECT lang, count(*) FROM name GROUP BY 1 ORDER BY 2 DESC LIMIT 12").fetchall()
    portions = con.sql("SELECT is_fallback, count(*) FROM portion GROUP BY 1").fetchall()
    units = con.sql("SELECT base_unit, count(*) FROM food GROUP BY 1").fetchall()
    brands = con.sql("SELECT count(*) FROM food WHERE brand_name IS NOT NULL").fetchone()[0]
    sample = con.sql("SELECT food_id, barcode, food_name, brand_name, calories_kcal, carbs_g, protein_g, fat_g FROM food USING SAMPLE 20").fetchall()
    size_mb = out.stat().st_size / 1e6

    lines = [f"# Barcode v1 build report", "", f"Source snapshot {SNAPSHOT}; output `{out.name}` {size_mb:.0f} MB; version `{VERSION}`.", "", "## Rows", "", "| Step | Rows |", "|---|---|"]
    for k, v in counts.items():
        lines.append(f"| {k} | {v:,} |")
    lines += ["", f"Brands present on {brands:,} foods. Base unit: " + ", ".join(f"{u} {c:,}" for u, c in units) + ".", "",
              "Portions: " + ", ".join(("fallback 100 g" if f else "1 serving") + f" {c:,}" for f, c in portions) + ".", "",
              "## Nutrient coverage (foods with a value)", "", "| Nutrient | Foods |", "|---|---|"]
    lines += [f"| {types.get(nid, nid)} | {c:,} |" for nid, c in coverage]
    lines += ["", "## Name languages (rows in food_name)", "", "| Lang | Rows |", "|---|---|"] + [f"| {l} | {c:,} |" for l, c in langs]
    lines += ["", "## 20 random rows", "", "| food_id | barcode | name | brand | kcal | carbs | protein | fat |", "|---|---|---|---|---|---|---|---|"]
    lines += ["| " + " | ".join(str(x).replace("|", "/") for x in row) + " |" for row in sample]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:20]))
    print(f"... full report: {args.report}")


if __name__ == "__main__":
    main()
