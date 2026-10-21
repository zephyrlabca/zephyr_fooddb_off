# Data licence

The code in this repository is MIT (see `LICENSE`). The data is not.

## The derived database

`barcode_v1.db`, the file this pipeline produces, is a **derivative database**
of Open Food Facts and is made available under the
[Open Database License (ODbL) v1.0](https://opendatacommons.org/licenses/odbl/1-0/).
Its individual contents are under the
[Database Contents License (DbCL) v1.0](https://opendatacommons.org/licenses/dbcl/1-0/),
as Open Food Facts' own contents are.

> Contains information from [Open Food Facts](https://world.openfoodfacts.org),
> which is made available here under the Open Database License (ODbL).

This repository is the share-alike offer the ODbL asks for (section 4.6 b):
the method that produces the derivative database from the pinned Open Food
Facts snapshot, together with the additional data the method needs
(`data/barcode_id_map.csv`, which fixes the ids; `data/catalog_reference.db`,
the nutrient types and categories the output is keyed to). Anyone can rebuild
the same database with `scripts/build_barcode_db.py`.

## The inputs this repository adds

- `data/barcode_id_map.csv` is published under the ODbL as part of the
  derivative database's method.
- `data/catalog_reference.db` holds nutrient type ids and names that follow
  USDA FoodData Central, a United States government work in the public
  domain, and ZephyrFit's own food category list. Public domain (CC0).

## What this does not cover

Open Food Facts does not endorse ZephyrFit. The ZephyrFit apps and servers
that consume the derived database are separate works and are not licensed
here; the ODbL's share-alike applies to the database, which this repository
provides, not to the software around it.
