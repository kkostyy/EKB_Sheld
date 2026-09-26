# -*- coding: utf-8 -*-
"""EKB SHIELD — список предметов для вкладки креатива.

Вкладку рисует клиентский мод (`client_mod/`), но СПИСОК предметов берётся
отсюда, из `docs/nirvana.sk`: функция `nirvana_item()` — единственное место,
где предмет описан целиком (база, CustomModelData, имя, лор). Если список
переписывать в моде руками, он разойдётся с игрой на первой же правке
скрипта, а разойдётся молча: клиент соберёт предмет с чужим CMD, ресурспак
нарисует что придётся, а скрипт его не опознает.

    py -3 build_creative_items.py          # показать, что получилось
    py -3 build_creative_items.py --write  # записать json в мод
    py -3 build_creative_items.py --check  # не устарел ли json

⚠ В мод уходит только конопля (2001-2016). Напитки BreweryX, стволы
QualityArmory, настолки TablePlays, артефакты и Тетрадь в креатив не
попадают НАМЕРЕННО: у них внутри данные плагина (закодированный рецепт,
NBT-метка ствола) или номер экземпляра в реестре скрипта. Клиент такой
предмет собрать не может — вышла бы копия, которая правильно выглядит и не
работает, а артефакты с Тетрадью ещё и обошли бы лимит «два на мир».
Их выдают каталоги `/allitems` и `/newitems`.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'docs', 'nirvana.sk')
OUT = os.path.join(ROOT, 'client_mod', 'src', 'main', 'resources',
                   'assets', 'ekbshield', 'creative_items.json')

# Цвета Minecraft: & -> имя цвета для клиента.
COLORS = {
    '0': 'black', '1': 'dark_blue', '2': 'dark_green', '3': 'dark_aqua',
    '4': 'dark_red', '5': 'dark_purple', '6': 'gold', '7': 'gray',
    '8': 'dark_gray', '9': 'blue', 'a': 'green', 'b': 'aqua',
    'c': 'red', 'd': 'light_purple', 'e': 'yellow', 'f': 'white',
}

# Алиас Skript -> предмет Minecraft. Названия у Skript человеческие
# («minecart with tnt»), у клиента — из реестра («minecraft:tnt_minecart»).
ITEMS = {
    'wheat seeds': 'minecraft:wheat_seeds',
    'sugar cane': 'minecraft:sugar_cane',
    'dried kelp': 'minecraft:dried_kelp',
    'paper': 'minecraft:paper',
    'glass bottle': 'minecraft:glass_bottle',
    'stick': 'minecraft:stick',
    'slime ball': 'minecraft:slime_ball',
    'cookie': 'minecraft:cookie',
    'chainmail helmet': 'minecraft:chainmail_helmet',
    'minecart with tnt': 'minecraft:tnt_minecart',
}


def parts(text):
    """Строка с цветовыми кодами -> [{'text':..., 'color':...}]."""
    out = []
    color = 'white'
    for chunk in re.split(r'(&[0-9a-fk-or])', text):
        if not chunk:
            continue
        if re.fullmatch(r'&[0-9a-f]', chunk):
            color = COLORS[chunk[1]]
        elif re.fullmatch(r'&[k-or]', chunk):
            continue          # жирный/курсив в креативе не нужны
        else:
            out.append({'text': chunk, 'color': color})
    return out


def parse():
    text = io.open(SRC, encoding='utf-8').read()
    body = text.split('function nirvana_item(id: text) :: item:', 1)[1]
    body = body.split('\nfunction ', 1)[0]

    items, cur = [], None
    for line in body.split('\n'):
        s = line.strip()
        m = re.match(r'(?:else )?if \{_id\} is "([a-z_]+)":', s)
        if m:
            cur = {'id': m.group(1)}
            items.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r'set \{_i\} to 1 of ([a-z ]+)$', s)
        if m:
            alias = m.group(1).strip()
            if alias not in ITEMS:
                sys.exit('неизвестный предмет Skript: %s' % alias)
            cur['item'] = ITEMS[alias]
        m = re.match(r'set custom model data of \{_i\} to (\d+)', s)
        if m:
            cur['cmd'] = int(m.group(1))
        m = re.match(r'set name of \{_i\} to "(.*)"$', s)
        if m:
            cur['name'] = parts(m.group(1))
        m = re.match(r'set lore of \{_i\} to (.*)$', s)
        if m:
            rows = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
            cur['lore'] = [parts(r) for r in rows]

    items = [i for i in items if i.get('cmd')]
    items.sort(key=lambda i: i['cmd'])
    return items


def main():
    items = parse()
    data = json.dumps({'items': items}, ensure_ascii=False, indent=2) + '\n'

    if '--check' in sys.argv:
        old = io.open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        if old != data:
            print('creative_items.json устарел — запусти с --write')
            sys.exit(1)
        print('creative_items.json свежий')
        return

    if '--write' in sys.argv:
        io.open(OUT, 'w', encoding='utf-8', newline='\n').write(data)
        print('записано: %s (%d предметов)' % (OUT, len(items)))
        return

    for i in items:
        name = ''.join(p['text'] for p in i.get('name', []))
        print('%5d  %-28s %s' % (i['cmd'], i['item'].split(':')[1], name))
    print('всего: %d' % len(items))


if __name__ == '__main__':
    main()
