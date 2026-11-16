# GoBricksPart-API
API and conversion table of Gobricks vs. LEGO® part ID numbers using gobricks backend API

[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/cc-0.svg)](https://forthebadge.com)

---

`gobricker.py` downloads the current part list from [rebrickable.com](https://rebrickable.com/downloads/) (ca. 65'000 LEGO® part numbers).
Categories that Gobricks does not produce (Duplo®, electronics, minidolls, gear etc.) are skipped.
The remaining parts (ca. 47'000) are sent to the [gobricks.cn](https://gobricks.cn) backend API to find out **if** Gobricks offers a compatible clone part and what its Gobricks item number is.

Last refresh: 2026-11-16, 1'992 parts with a Gobricks equivalent.

**Note**

There is no need to convert your lists as long as they are in .csv format.
The Gobricks toolkit accepts part lists with LEGO® part numbers in the Rebrickable .csv format.
LEGO® part numbers in a .xlsx file will not work.

---

### Files

| File | Content |
|---|---|
| [gobrick_conversion_table.csv](./gobrick_conversion_table.csv) | LEGO® part number → Gobricks item number (no header row), e.g. `3001,GDS-542` |
| [color_table.csv](./color_table.csv) | LEGO®, Bricklink and Gobricks color ids, based on the [Brickwith Gobricks color guide](https://www.brickwith.com/en/about/help/article/gobricks-color-guide) |
| [parts.csv](./parts.csv), [part_categories.csv](./part_categories.csv) | Rebrickable data used for the last refresh |
| [example_hogwarts](./example_hogwarts) | Example Bricklink list and its converted output |
| [raw](./raw) | Example raw JSON responses from the API |

---

### Refresh the conversion table

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv run gobricker.py
```

The script

- downloads `parts.csv.gz` and `part_categories.csv.gz` from Rebrickable and saves them as `parts.csv` / `part_categories.csv`
- skips all parts whose category is listed in `CATEGORY_EXCLUDE` (matched by name; the script stops if a name no longer exists at Rebrickable)
- queries the Gobricks API in batches of 1000 parts
- writes `gobrick_conversion_table.csv` and the full API response to `api_request_raw.json` (ignored by git)

---

### Convert Bricklink to BOM

- pick a set
- export set inventory to new Wanted List
    + click "part out"
    + create new Wanted List
- download the Wanted List as `.xml` file
- open the `.xml` file with Microsoft Excel
- save the table as `bom.csv`
- put `bom.csv`, `color_table.csv` and `gobrick_conversion_table.csv` in the same folder and run `python bricklink_to_gobrick.py` there
- check the report printed by the script:
    + parts without a Gobricks equivalent keep their LEGO® part number
    + colors without a Gobricks equivalent keep their Bricklink color id
    + parts without a color (e.g. sticker sheets) are skipped
- open the `bom_gobricks.csv` with a text editor
- select all + copy
- open the template `gds-list.xlsx` from gobricks in Microsoft Excel
- paste the values in the table (they are tab separated, so each lands in its own column), save
- upload to gobricks.cn toolkit

Each output line is `gobricks part<TAB>gobricks color<TAB>quantity`, e.g. `GDS-563	031	2`.

---

### Gobricks API Documentation

(unofficial / reverse engineered)

`POST https://gobricks.cn/frontend/v1/community/lego2ItemList` with a JSON body:

```python
import requests

parts = ['3001', '10884']

payload = {'testList': [
    {'color_type': 'ldr', 'colorid': '0', 'designid': number, 'quantity': 1}  # color 0 = black
    for number in parts
]}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json;charset=utf-8',
    'Origin': 'https://gobricks.cn',
    'Referer': 'https://gobricks.cn/',
}

url = 'https://gobricks.cn/frontend/v1/community/lego2ItemList'
response = requests.post(url, headers=headers, json=payload, timeout=120)
response.raise_for_status()
result = response.json()
```

| Request field | Meaning |
|---|---|
| `designid` | LEGO® part number (string) |
| `colorid` | color id (string) in the numbering given by `color_type` |
| `color_type` | `ldr` = LDraw color numbers |
| `quantity` | number of pieces (affects price and stock check) |

Every requested part ends up in one of these lists of the response:

| Response list | Meaning |
|---|---|
| `itemList` | available in the requested color and in stock |
| `colorDeficiency` | Gobricks makes the part, but not in the requested color |
| `inventoryDeficiency` | Gobricks makes the part, but it is out of stock |
| `missList` | no Gobricks equivalent |
| `noSellList`, `buyLimitList`, `quantityErrorList` | not sold / purchase limits |

An entry looks like this (shortened):

```json
{
  "designid": "3001", "colorid": "0", "color_type": "ldr", "quantity": 1,
  "item_id": "GDS-542-080",
  "info": {
    "id": "GDS-542-080",
    "caption_en": "Brick 2 x 4",
    "product_id": "542",
    "color_id": "080",
    "inventory": 74609,
    "price": "0.52",
    "picture": "https://image.gobricks.cn/newproducts/080/542.png"
  }
}
```

`info.id` is `GDS-<product>-<color>`, sometimes with an extra suffix (e.g. `GDS-612-080-DE01`).
The conversion table uses the first two parts (`GDS-542`).
See the [raw](./raw) directory for full responses.
