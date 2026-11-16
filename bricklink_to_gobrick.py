# -*- coding: utf-8 -*-

import csv

# Bricklink wanted list columns (bom.csv)
COL_ITEMID = 1
COL_COLOR = 2
COL_QTY = 4  # MINQTY

# https://swooshable.com/parts/colors
# https://customizeminifiguresintelligence.wordpress.com/2020/07/27/gobricks-the-foxconn-of-china-clone-bricks/
colors = {}
with open('color_table.csv', mode='r', encoding="utf-8-sig") as infile:
    reader = csv.reader(infile)
    next(reader, None)  # skip the headers
    for row in reader:
        colors[row[1]] = row[2]

# gobrick_conversion_table.csv has no header row
parts = {}
with open('gobrick_conversion_table.csv', mode='r', encoding="utf-8-sig") as infile:
    reader = csv.reader(infile)
    for row in reader:
        parts[row[0]] = row[1]

#%%
unknown_parts = []
unknown_colors = []
no_color = []

with open('bom.csv', mode='r', encoding="utf-8-sig") as infile, open('bom_gobricks.csv', mode='w', newline='', encoding='utf8') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    # writer.writerow(['零件编号', '颜色编号', '数量'])
    next(reader, None)  # skip the headers
    for row in reader:
        part = row[COL_ITEMID]
        color = row[COL_COLOR]
        quantity = row[COL_QTY]

        # parts without a color (e.g. sticker sheets) cannot be ordered at gobricks
        if len(color) == 0:
            no_color.append(part)
            continue

        if part in parts:
            part = parts[part]
        else:
            unknown_parts.append(part)  # keep the LEGO/Bricklink part number

        if color in colors:
            color = colors[color]
        else:
            unknown_colors.append(color)  # keep the Bricklink color id

        writer.writerow([part + '\t' + color.zfill(3) + '\t' + quantity])

if unknown_parts:
    print(f'{len(unknown_parts)} rows with no gobricks part number (LEGO number kept):')
    print('  ' + ', '.join(sorted(set(unknown_parts))))
if unknown_colors:
    print(f'{len(unknown_colors)} rows with no gobricks color (Bricklink color id kept):')
    print('  ' + ', '.join(sorted(set(unknown_colors))))
if no_color:
    print(f'{len(no_color)} rows skipped because they have no color:')
    print('  ' + ', '.join(no_color))
