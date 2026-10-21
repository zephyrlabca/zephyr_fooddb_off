# zephyr_fooddb_off

The pipeline that turns the Open Food Facts product database into
`barcode_v1.db`: packaged foods sold in the United States and Canada, trimmed
to the shape of [ZephyrFit](https://zephyrfit.ca)'s food catalog, one row per
barcode, with stable ids. ZephyrFit's food backend serves this database to
the app's barcode scanner.

Published because the output is a derivative database of Open Food Facts
under the ODbL: this repository is the method that reproduces it. See
`DATA_LICENSE.md`.

> Contains information from [Open Food Facts](https://world.openfoodfacts.org),
> which is made available here under the Open Database License (ODbL).

## What is in here

| Path | What |
|---|---|
| `scripts/build_barcode_db.py` | the whole pipeline: DuckDB over the Parquet export, gates, ids, SQLite out |
| `data/barcode_id_map.csv` | barcode → `food_id`, the persistent id assignment; read and appended by every build |
| `data/catalog_reference.db` | the 41 nutrient types and 28 categories the output is keyed to |
| `docs/source-profile.md` | what the source looks like: counts, coverage, dirt, code shapes |
| `docs/output-shape.md` | the output tables, the gates, the nutrient map, the id rule |
| `docs/build-report-v1.md` | the v1 build: rows in, drops by reason, coverage, sample rows |
| `tools/decode_barcode.swift` | reads barcodes off photos with Apple Vision, for checking a build against real packs |

The output file and the source export are not committed (`build/`, `source/`).

## Source pin, v1

| | |
|---|---|
| Dataset | Hugging Face [`openfoodfacts/product-database`](https://huggingface.co/datasets/openfoodfacts/product-database), file `food.parquet` |
| Revision | `dbdc38c796c2a3588eefbab33fb4f4f4e1fafafd` (2026-10-19 18:03 UTC) |
| SHA-256 | `14369cd87be0baef808e5d9097c7eaf49c7480fc37e85a5f94d3fa93c44487ef` |
| Size | 7,963,759,220 bytes, 4,821,386 rows, 111 columns |
| Downloaded | 2026-10-21 05:25 UTC |

```bash
curl -L -o source/food.parquet \
  https://huggingface.co/datasets/openfoodfacts/product-database/resolve/dbdc38c796c2a3588eefbab33fb4f4f4e1fafafd/food.parquet
```

## Build

Python 3.12 or newer and about 10 GB of free disk. The build reads the
whole Parquet file once through DuckDB and writes SQLite; v1 took a few
minutes on a laptop.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/build_barcode_db.py \
    --source source/food.parquet \
    --bundled data/catalog_reference.db \
    --output build/barcode_v1.db \
    --id-map data/barcode_id_map.csv \
    --report build/report.md
```

`--id-map` is read before the build and rewritten after it with any new
codes appended. A build from the pinned source with the committed map
reproduces v1: 876,784 foods, `catalog_metadata.version = barcodev1`,
content hash as in `docs/build-report-v1.md`.

## Refreshing

1. Download a newer `food.parquet`; record its revision, SHA-256 and size
   here as the new pin.
2. Run the build with the committed `data/barcode_id_map.csv`. Existing
   barcodes keep their ids; new ones are appended.
3. Commit the updated map and the new build report. The map is the one file
   that must never be lost or rebuilt from scratch: ids are referenced by
   users' logged meals.

## Licences

Code: MIT, copyright Changkun (CK) Jiang o/a Zephyr Lab (`LICENSE`). Data: ODbL for the derived database and the id map,
public domain for the reference tables (`DATA_LICENSE.md`). Open Food Facts
does not endorse this project.
