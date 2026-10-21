# Barcode v1 build report

Source snapshot 2026-10-21; output `barcode_v1.db` 358 MB; version `barcodev1`.

## Rows

| Step | Rows |
|---|---|
| scoped | 1,114,892 |
| kept | 876,784 |
| macro_missing | 170,466 |
| code_not_gtin | 37,858 |
| kcal_impossible | 12,057 |
| code_below_1e6 | 9,718 |
| macro_over_100g | 4,365 |
| macro_sum_over_105 | 2,233 |
| no_name | 1,408 |
| dedupe_collapsed | 3 |
| ids_new | 876,784 |
| ids_total_in_map | 876,784 |

Brands present on 596,877 foods. Base unit: ml 54, g 876,730.

Portions: 1 serving 619,025, fallback 100 g 257,759.

## Nutrient coverage (foods with a value)

| Nutrient | Foods |
|---|---|
| Total Sugars | 817,792 |
| Sodium, Na | 804,394 |
| Fatty acids, total saturated | 779,551 |
| Fiber, total dietary | 682,583 |
| Cholesterol | 491,288 |
| Iron, Fe | 448,896 |
| Calcium, Ca | 442,156 |
| Fatty acids, total trans | 435,735 |
| Potassium, K | 303,482 |
| Vitamin C, total ascorbic acid | 236,062 |
| Vitamin A, RAE | 228,379 |
| Vitamin D (D2 + D3) | 149,402 |
| Magnesium, Mg | 64,833 |
| Phosphorus, P | 61,340 |
| Zinc, Zn | 59,594 |
| Fatty acids, total monounsaturated | 58,547 |
| Fatty acids, total polyunsaturated | 58,382 |
| Thiamin | 54,080 |
| Riboflavin | 53,403 |
| Manganese, Mn | 53,171 |
| Copper, Cu | 52,814 |
| Vitamin E (alpha-tocopherol) | 52,377 |
| Vitamin B-6 | 51,875 |
| Starch | 51,578 |
| Selenium, Se | 50,476 |
| Vitamin B-12 | 47,647 |
| Niacin | 45,766 |
| Folate, DFE | 44,635 |
| Pantothenic acid | 33,832 |
| Choline, total | 32,300 |
| Iodine, I | 29,045 |
| Vitamin K (phylloquinone) | 28,482 |
| Omega-3 fatty acids (ALA + EPA + DPA + DHA) | 4,597 |
| Omega-6 fatty acids (linoleic acid, PUFA 18:2 fallback) | 4,421 |
| Omega-3 marine fatty acids (EPA + DPA + DHA) | 4,013 |
| Biotin | 406 |

## Name languages (rows in food_name)

| Lang | Rows |
|---|---|
| en | 809,641 |
| fr | 76,017 |
| it | 5,981 |
| es | 5,787 |
| de | 3,538 |
| id | 2,267 |
| nl | 1,900 |
| ro | 1,459 |
| pl | 1,233 |
| zh | 1,226 |
| sv | 1,223 |
| da | 1,184 |

## 20 random rows

| food_id | barcode | name | brand | kcal | carbs | protein | fat |
|---|---|---|---|---|---|---|---|
| 100165828 | 0041271028713 | Creamy yogurt, southern butter pecan | None | 110.0 | 17.18000030517578 | 2.640000104904175 | 3.5199999809265137 |
| 100613447 | 0768395494544 | Galerie, star wars candy dispenser | Galerie,  Ross Acquisition Inc. | 389.0 | 88.88999938964844 | 0.0 | 0.0 |
| 100680036 | 0830271000184 | Sweet bread | None | 280.0 | 54.0 | 10.0 | 4.0 |
| 100636793 | 0808912039633 | Potato Chips | Farm Boy | 500.0 | 60.0 | 6.0 | 28.0 |
| 100662224 | 0814453021648 | Greek With Kalamata Vinaigrette | Cindy's Kitchen | 466.6669921875 | 0.0 | 0.0 | 50.0 |
| 100776173 | 0873976011574 | Poulet Thaï cari rouge | Bravodelli | 113.33300018310547 | 10.333000183105469 | 12.333000183105469 | 2.6670000553131104 |
| 100713714 | 0850044218752 | Chili Lime Beef Slices | Vacadillos | 266.6669921875 | 0.0 | 50.0 | 6.666999816894531 |
| 100747487 | 0856336001064 | Organic Full Crunch PB | CB's Nuts | 587.5 | 18.75 | 25.0 | 50.0 |
| 100764563 | 0860006314989 | French crepe mix | None | 390.0 | 67.5 | 12.5 | 8.0 |
| 100218970 | 0051000149190 | Creamy Chicken & Dumplings | Campbell's Chunky Bowls | 71.7040023803711 | 6.708000183105469 | 2.7760000228881836 | 3.7009999752044678 |
| 100322065 | 0072992070002 | Macadamia Milk Frozen Dessert - Chocolate | Mauna Loa | 188.78500366210938 | 28.03700065612793 | 0.9350000023841858 | 8.41100025177002 |
| 100335843 | 0074780334006 | Perrier et jus | Perrier | 12.121000289916992 | 2.7269999980926514 | 0.029999999329447746 | 0.0 |
| 100001733 | 02506201 | Apple and lemon juice concentrates, lemonade | None | 250.0 | 50.0 | 0.0 | 0.0 |
| 100610794 | 0764014266325 | Aidells, smoked chicken breast, garlic & basil | None | 107.0 | 3.569999933242798 | 21.43000030517578 | 1.7899999618530273 |
| 100631851 | 0799034170246 | Paleta con saladito sabor fresa agridulce | Productos Diana | 375.0 | 90.0 | 1.0 | 2.5 |
| 100399579 | 0089125507311 | Lentil & quinoa | None | 365.0 | 64.86000061035156 | 21.6200008392334 | 2.700000047683716 |
| 100241566 | 0058449600060 | Pain mighty Manna | None | 266.6669921875 | 53.33300018310547 | 12.0 | 2.6670000553131104 |
| 100856055 | 8005713350147 | Limonzero | Pallini | 77.77799987792969 | 20.0 | 0.0 | 0.0 |
| 100534574 | 0660251604404 | Kettle Sweet & Salty Popped Corn Chips | Popped Munchies | 429.0 | 82.0999984741211 | 7.139999866485596 | 7.139999866485596 |
| 100031285 | 0009787029591 | Apple Pie Twisters | H-E-B | 480.0 | 72.0 | 4.0 | 20.0 |
