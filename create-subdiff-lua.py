"""
for m_select test_subdiff
"""

import gzip
import json
import glob
import re

table_list = []
for bmt_filepath in glob.glob('../../table/*.bmt'):
    with gzip.GzipFile(bmt_filepath) as f:
        d = json.load(f, strict=False)
        table_name = d['name']
        if  'おすすめ譜面表' in table_name or 'BMS Search' in table_name:
            continue
        if  table_name == '≒slst推定難易度表':
            continue
        if  table_name == '≒slst推定難易度表（slstなし）':
            continue
        table_list.append((bmt_filepath, table_name))

# ソート
priority_list = [
    'Stella',
    'Supernova',
    'Satellite',
    'Satellite Recommend',
    'Satellite (Voting)',
    'Satellite (Rejected)',
    'Solar',
    '第2発狂難易度',
    '第2通常難易度',
    '発狂BMS難易度表',
    '通常難易度表',
    '16分乱打難易度表(仮)',
    'ウーデオシ小学校難易度表',
    '腕ガチ難易度表',
    'Delay小学校難易度表',
    'ディレイjoy',
    'Luminous',
    'LN難易度',
    'Scramble難易度表',
    '皿難易度表(3rd)',
    '≒slst推定難易度表（詳細）',
    'Stella Uploader',
]
priority_dict = {val: idx for idx, val in enumerate(priority_list)}

table_name_list = [ x[1] for x in table_list ]
for priority_table_name in priority_list:
    if priority_table_name not in table_name_list:
        print(table_name_list)
        print(priority_table_name)
        raise Exception

table_list = sorted(
        table_list,
        key=lambda x: (priority_dict.get(x[1], float('inf')), x[1])
)

# 各難易度
subdiff_data = {}

key_map_md5 = {}
key_map_sha256 = {}
for bmt_filepath, _ in table_list:
    with gzip.GzipFile(bmt_filepath) as f:
        d = json.load(f, strict=False)

        table_name = d['name']

        for d2 in d['folder']:
            subdiff_name = d2['name'].strip()

            if table_name == 'Satellite Recommend':
                subdiff_name += "*"
            elif table_name == 'Satellite (Voting)':
                subdiff_name += "?"
            elif table_name == 'Satellite (Rejected)':
                subdiff_name += "'"
            else:
                m = re.match(r'(?P<level>[EFHN]★\d+\.\d+)\.\.\.\d+\.\d+', subdiff_name)
                if m != None:
                    subdiff_name = m.group('level') + '…'

                m = re.match(r'(?P<short>[EFHN]★)\.\.\.(?P<level>\d+\.\d+)', subdiff_name)
                if m != None:
                    subdiff_name = m.group('short') + '…' + m.group('level')

                m = re.match(r'(?P<level>[EFHN]★\d+\.\d+)\.\.\.$', subdiff_name)
                if m != None:
                    subdiff_name = m.group('level') + '…'

            # print(subdiff_name)
            for d3 in d2['songs']:
                key = (d3.get('md5'), d3.get('sha256'))
                if key == (None, None):
                    print(subdiff_name, d3)
                    raise Exception

                if (key[0], None) in subdiff_data:
                    key = (key[0], None)
                elif (None, key[1]) in subdiff_data:
                    key = (None, key[1])

                if key[1] == None and key not in subdiff_data:
                    matched_key = key_map_md5.get(key[0])
                    if matched_key != None:
                        subdiff_data[key] = subdiff_data.pop(matched_key)
                        if matched_key[1] != None:
                            key_map_sha256.pop(matched_key[1])
                    key_map_md5[key[0]] = key
                elif key[0] == None and key not in subdiff_data:
                    matched_key = key_map_sha256.get(key[1])
                    if matched_key != None:
                        subdiff_data[key] = subdiff_data.pop(matched_key)
                        key_map_sha256[matched_key[1]] = key
                        if matched_key[0] != None:
                            key_map_md5.pop(matched_key[0])
                    key_map_sha256[key[1]] = key
                elif key[0] != None and key[1] != None:
                    key_map_md5[key[0]] = key
                    key_map_sha256[key[1]] = key

                if key not in subdiff_data:
                    subdiff_data[key] = []

                subdiff_data[key].append(subdiff_name)

# 削除
"""
査定中, 保留, 削除,
"""
remove_set = set([
    '査定中',
    '保留',
    '削除',
])
for key in subdiff_data:
    subdiff_data[key] = [
        x for x in subdiff_data[key] if x not in remove_set
    ]

# filter
p1 = r'^sU(?P<year>\d{4})/(?P<month>\d{2})$'
p2 = r'^sl\d+$'
p3 = r'^sl\d+\*$'
p4 = r'^≒(sl|st).*'
for key, value in subdiff_data.items():
    if len(value) == 2:
        su_found = False
        estimate_found = False
        for i, subdiff_name in enumerate(value):
            m1 = re.match(p1, subdiff_name)
            m4 = re.match(p4, subdiff_name)
            if m1 != None:
                su_found = True

            if m4 != None:
                estimate_found = True

        if su_found:
            if estimate_found:
                pop_su = False
            else:
                # sU かつ 推定難易度ではないとき
                # sU かつ 正式な難易度に入っているとき
                pop_su = True
        else:
            pop_su = False

    elif len(value) > 2:
        # sU かつ 正式な難易度に入っているとき
        pop_su = True
    else:
        pop_su = False


    for i, subdiff_name in enumerate(value):
        m = re.match(p1, subdiff_name)
        if m != None:
            if pop_su:
                value.pop(i)
                break
            else:
                value[i] = 'sU'
                break

    has_sl_rec = False
    for i, subdiff_name in enumerate(value):
        m = re.match(p3, subdiff_name)
        if m != None:
            has_sl_rec = True
            break
    if has_sl_rec:
        for i, subdiff_name in enumerate(value):
            m = re.match(p2, subdiff_name)
            if m != None:
                value.pop(i)
                break

# ハッシュでソート


# 結果
md5_list = []
sha256_list = []

for key, value in subdiff_data.items():
    subdiff = '"' + ' / '.join(value) + '"'
    if key[0] != None:
        t = f'["{key[0]}"] = {subdiff},'
        md5_list.append(t)
    elif key[1] != None:
        t = f'["{key[1]}"] = {subdiff},'
        sha256_list.append(t)
    else:
        raise Exception

md5_list.sort()
sha256_list.sort()

lua_list = []
lua_list.append('return {')
lua_list.append('  md5 = {')
lua_list += [ f'    {s}' for s in md5_list ]
lua_list.append('  },')
lua_list.append('  sha256 = {')
lua_list += [ f'    {s}' for s in sha256_list ]
lua_list.append('  },')
lua_list.append('}')

with open('subdiff.lua', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lua_list))

