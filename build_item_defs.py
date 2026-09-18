# -*- coding: utf-8 -*-
"""EKB SHIELD — генерация assets/minecraft/items/*.json для ресурспака.

ПОЧЕМУ НЕ РУКАМИ. Файл `items/<предмет>.json` заменяет ВАНИЛЬНОЕ определение
предмета целиком, а оно у многих вещей непростое:
  * `potion` содержит `tints` с окраской жидкости — без них у всех зелий,
    включая обычные ванильные, пропадает иконка;
  * `chainmail_helmet` — это `select` по `minecraft:trim_material` из 11 веток,
    по одной на каждый материал отделки брони.
Поэтому ванильное определение читается из клиентского jar и кладётся целиком
в `fallback`, а наши CustomModelData добавляются вокруг него. Так ничего
ванильного не теряется.

⚠️ ТОЛЬКО `range_dispatch`, НЕ `select`. До 18.09.2026 этот скрипт писал
`minecraft:select` с числовым `when` — форму, которая гарантированно ломает
пак. У `select` свойство `custom_model_data` читает список `strings`
компонента, и `when` обязано быть строкой; плагины же (BreweryX, Skript,
ExecutableItems) ставят CMD старым числовым способом, а он ложится в
`floats[0]`. Числовой `when` клиент даже не разбирает:

    Couldn't parse item model ...: Not a json array: 1001;
    Not a string: 1001; Empty case list

и тогда пропадает отрисовка ВСЕГО базового предмета — всех зелий, всех палок,
всей бумаги, а не только кастомного. Числа читает `range_dispatch` с
`entries[].threshold`.

Живые файлы в паке кто-то починил руками, а генератор остался сломанным:
запуск `py -3 build_item_defs.py` затирал починку и ронял пак целиком.

Запуск:  py -3 build_item_defs.py [--client <путь к minecraft-<версия>-client.jar>]
"""
import argparse
import glob
import json
import os
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ITEMS = os.path.join(ROOT, "resourcepack", "assets", "minecraft", "items")

# CMD -> (базовый ванильный предмет, модель в нашем пространстве имён)
OVERRIDES = {
    # напитки BreweryX
    1001: ("potion", "jagermeister"),
    1002: ("potion", "beer_bottle"),
    1003: ("potion", "tequila"),
    1004: ("potion", "rum"),
    1005: ("potion", "samogon"),
    1006: ("potion", "vodka_absolut"),
    1007: ("potion", "vodka_plain"),
    1008: ("potion", "whiskey"),
    1009: ("potion", "jagermeister_orange"),
    1010: ("potion", "jagermeister_dark"),
    1011: ("potion", "vodka_passionfruit"),
    1012: ("potion", "vodka_mojito"),
    1013: ("potion", "samogon_green"),
    1014: ("potion", "rassol"),
    # конопля (docs/nirvana.sk)
    2001: ("wheat_seeds", "hemp_seeds"),
    2002: ("sugar_cane", "hemp"),
    2003: ("dried_kelp", "weed_bud"),
    2004: ("paper", "hemp_cloth"),
    2005: ("glass_bottle", "bong_empty"),
    2006: ("paper", "joint"),
    2007: ("stick", "pipe_empty"),
    2008: ("stick", "pipe_stuffed"),
    2009: ("glass_bottle", "bong_full"),
    2010: ("slime_ball", "herbal_salve"),
    2011: ("cookie", "weed_brownie"),
    2012: ("chainmail_helmet", "deerstalker"),
    2013: ("paper", "hemp_burlap"),
    2014: ("stick", "pipe_suspicious"),
    2015: ("stick", "pipe_smouldering"),
    2016: ("tnt_minecart", "thc_minecart"),
    # Тетрадь Смерти (docs/death_note.sk)
    6666: ("writable_book", "death_note"),
    # Артефакты ExecutableItems (plugins/ExecutableItems/items/*.yml).
    # Диапазон 3001-3006 выбран свободным: заняты 1001-1014 (BreweryX),
    # 2001-2016 (Nirvana), 6666 (Тетрадь), 7001-7003 и 7200 (тюрьма),
    # 7300-7399 (меню ролей), 33000-33790 (TablePlays).
    3001: ("compass", "bounty_compass"),
    3002: ("netherite_sword", "shadow_dagger"),
    3003: ("clock", "time_hourglass"),
    3004: ("book", "smuggler_journal"),
    3005: ("coal", "black_mark"),
    3006: ("carved_pumpkin", "faceless_mask"),
}

DEFAULT_CLIENT_GLOB = os.path.join(
    os.environ.get("APPDATA", ""), "ElyPrismLauncher", "libraries", "com", "mojang",
    "minecraft", "*", "minecraft-*-client.jar")


def find_client(explicit):
    if explicit:
        return explicit
    found = sorted(glob.glob(DEFAULT_CLIENT_GLOB))
    for f in found:
        if "26.1.2" in f:
            return f
    if found:
        return found[-1]
    return None


def vanilla_models(client_jar, bases):
    """ванильные определения предметов из клиентского jar"""
    out = {}
    with zipfile.ZipFile(client_jar) as z:
        names = set(z.namelist())
        for base in bases:
            p = "assets/minecraft/items/%s.json" % base
            if p not in names:
                raise SystemExit("в клиенте нет %s — проверь версию jar" % p)
            out[base] = json.loads(z.read(p).decode("utf-8"))["model"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", help="путь к minecraft-<версия>-client.jar")
    args = ap.parse_args()

    client = find_client(args.client)
    if not client or not os.path.exists(client):
        raise SystemExit(
            "не найден клиентский jar. Укажи его через --client — без него\n"
            "нельзя узнать ванильные определения, а угадывать их нельзя:\n"
            "у potion есть tints, у брони — select по отделке.")
    print("клиент:", client)

    by_base = {}
    for cmd, (base, model) in sorted(OVERRIDES.items()):
        by_base.setdefault(base, []).append((cmd, model))

    fallbacks = vanilla_models(client, by_base.keys())
    os.makedirs(ITEMS, exist_ok=True)

    for base, entries in sorted(by_base.items()):
        # threshold пишется как float: клиент так его и хранит, а число
        # 1001 и 1001.0 для него одно и то же. Ванильное определение
        # целиком уходит в fallback — у compass и clock оно само по себе
        # range_dispatch (по стрелке и по времени суток), и вложение
        # работает штатно.
        doc = {
            "model": {
                "type": "minecraft:range_dispatch",
                "property": "minecraft:custom_model_data",
                "fallback": fallbacks[base],
                "entries": [
                    {"threshold": float(cmd),
                     "model": {"type": "minecraft:model", "model": "shield:item/" + model}}
                    for cmd, model in entries
                ],
            }
        }
        with open(os.path.join(ITEMS, base + ".json"), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
            f.write("\n")
        kind = fallbacks[base].get("type", "?").replace("minecraft:", "")
        print("%-18s порогов: %-3d ванильный fallback: %s" % (base, len(entries), kind))


if __name__ == "__main__":
    main()
