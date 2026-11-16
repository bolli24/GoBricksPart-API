# /// script
# requires-python = ">=3.9"
# dependencies = ["requests"]
# ///
# -*- coding: utf-8 -*-
# run with: uv run gobricker.py
import csv
import gzip
import io
import json
import time

import requests

# Part numbers and categories from https://rebrickable.com/downloads
# -> skip categories gobricks does not produce (e.g. Duplo, electronics, gear)
PARTS_URL = 'https://cdn.rebrickable.com/media/downloads/parts.csv.gz'
CATEGORIES_URL = 'https://cdn.rebrickable.com/media/downloads/part_categories.csv.gz'

# Rebrickable category names to skip (matched exactly against part_categories.csv).
# All other categories are queried. These had no gobricks equivalents in a full run (2026-11-16).
CATEGORY_EXCLUDE = [
    'Belville, Scala and Fabuland',
    'Clikits',
    'Duplo, Quatro and Primo',
    'Electronics',
    'Gear Parts',
    'HO Scale',
    'Minidoll Heads',
    'Minidoll Lower Body',
    'Minidoll Upper Body',
    'Modulex',
    'Non-Buildable Figures (Duplo, Fabuland, etc)',
    'Non-System Parts',
    'Other',
    'Pen & Watch',
    'Znap',
]

API_URL = 'https://gobricks.cn/frontend/v1/community/lego2ItemList'
BATCH_SIZE = 1000      # parts per API request
BATCH_DELAY = 1.0      # seconds between requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json;charset=utf-8',
    'Origin': 'https://gobricks.cn',
    'Referer': 'https://gobricks.cn/',
}

# lists in the API response:
# "itemList"            available
# "inventoryDeficiency" not in stock
# "colorDeficiency"     does not exist in the requested color
# "missList"            no gobricks equivalent
# "noSellList", "buyLimitList", "quantityErrorList"  not sold / limited
RESPONSE_LISTS = ['itemList', 'missList', 'colorDeficiency', 'inventoryDeficiency',
                  'noSellList', 'buyLimitList', 'quantityErrorList']
# parts that gobricks produces (in any color / stock state)
HIT_LISTS = ['colorDeficiency', 'inventoryDeficiency', 'itemList']


def download_csv(url, save_as):
    """Download a gzipped Rebrickable CSV, save an uncompressed copy, return its rows."""
    print(f'downloading {url}')
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    text = gzip.decompress(resp.content).decode('utf-8-sig')
    with open(save_as, 'w', newline='', encoding='utf8') as outfile:
        outfile.write(text)
    reader = csv.reader(io.StringIO(text))
    next(reader, None)  # skip the headers
    return list(reader)


#%% DOWNLOAD PARTS AND CATEGORIES, EXCLUDE CATEGORIES BY NAME
categories = {row[0]: row[1] for row in download_csv(CATEGORIES_URL, 'part_categories.csv')}

unknown = [name for name in CATEGORY_EXCLUDE if name not in categories.values()]
if unknown:
    raise SystemExit(f'category names not found at Rebrickable (renamed?): {unknown}')

parts = download_csv(PARTS_URL, 'parts.csv')
# [0] = part number / [2] = category id
mylist = [row[0] for row in parts if categories.get(row[2]) not in CATEGORY_EXCLUDE]
print(f'{len(parts)} parts total, {len(mylist)} after excluding categories')


#%% QUERY THE GOBRICKS API IN BATCHES
result = {name: [] for name in RESPONSE_LISTS}
session = requests.Session()
for start in range(0, len(mylist), BATCH_SIZE):
    batch = mylist[start:start + BATCH_SIZE]
    payload = {'testList': [
        {'color_type': 'ldr', 'colorid': '0', 'designid': number, 'quantity': 1}  # color 0 = black
        for number in batch
    ]}
    response = session.post(API_URL, headers=HEADERS, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    for name in RESPONSE_LISTS:
        result[name].extend(data.get(name) or [])
    hits = sum(len(data.get(name) or []) for name in HIT_LISTS)
    print(f'parts {start + 1}-{start + len(batch)} of {len(mylist)}: {hits} hits')
    time.sleep(BATCH_DELAY)


#%% FIND THE LEGO ID AND GOBRICKS ID
conversion = {}
for name in HIT_LISTS:
    for item in result[name]:
        ldd = item['designid']
        gob = '-'.join(item['info']['id'].split('-')[0:2])  # GDS-612-080-DE01 ==> GDS-612
        conversion.setdefault(ldd, gob)
print(f'{len(conversion)} parts with a gobricks equivalent')


#%% OUTPUT THE FULL CONVERSION TABLE (no header row)
with open('gobrick_conversion_table.csv', newline='', mode='w', encoding='utf8') as outfile:
    writer = csv.writer(outfile, delimiter=',')
    for ldd, gob in conversion.items():
        writer.writerow([ldd, gob])

#%% OUTPUT THE RAW JSON FILE
with open('api_request_raw.json', 'w', encoding='utf8') as outfile:
    json.dump(result, outfile, sort_keys=True, indent=4, ensure_ascii=False)
