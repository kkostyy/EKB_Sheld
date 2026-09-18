# -*- coding: utf-8 -*-
"""Разложить текстуры Nirvana (CMD 2001-2012) в ресурспак EKB SHIELD."""
import json
import os
import shutil

from PIL import Image

MOD = r"D:\EKB_Shield\nirvana-fabric-2.0.11\assets\nirvana\textures\item"
PACK = r"D:\EKB_Shield\resourcepack"
TEX = os.path.join(PACK, "assets", "shield", "textures", "item")
MODELS = os.path.join(PACK, "assets", "shield", "models", "item")
ITEMS = os.path.join(PACK, "assets", "minecraft", "items")

# CMD -> (имя в паке, исходник в моде, базовый ванильный предмет)
ITEMS_MAP = [
    (2001, "hemp_seeds",    "hemp_seeds.png",    "wheat_seeds"),
    (2002, "hemp",          "hemp.png",          "sugar_cane"),
    (2003, "weed_bud",      "weed.png",          "dried_kelp"),
    (2004, "hemp_cloth",    "hemp_cloth.png",    "paper"),
    (2005, "bong_empty",    "bong.png",          "glass_bottle"),
    (2006, "joint",         "joint.png",         "paper"),
    (2007, "pipe_empty",    "old_pipe.png",      "stick"),
    (2008, "pipe_stuffed",  "stuffed_pipe.png",  "stick"),
    (2009, "bong_full",     None,                "glass_bottle"),   # собирается ниже
    (2010, "herbal_salve",  "herbal_salve.png",  "slime_ball"),
    (2011, "weed_brownie",  "weed_brownie.png",  "cookie"),
    (2012, "deerstalker",   "deerstalker.png",   "chainmail_helmet"),
]


def build_bong_full():
    """заряженный бонг = основа бутылки + слой «жидкости», подкрашенный в зелёный"""
    base = Image.open(os.path.join(MOD, "bong_potion.png")).convert("RGBA")
    overlay = Image.open(os.path.join(MOD, "bong_potion_overlay.png")).convert("RGBA")
    px = overlay.load()
    tint = (122, 170, 60)
    for y in range(overlay.height):
        for x in range(overlay.width):
            r, g, b, a = px[x, y]
            if a:
                lum = (r + g + b) / 3.0 / 255.0
                px[x, y] = (int(tint[0] * lum), int(tint[1] * lum), int(tint[2] * lum), a)
    base.alpha_composite(overlay)
    return base


def main():
    for d in (TEX, MODELS, ITEMS):
        os.makedirs(d, exist_ok=True)

    # 1) текстуры
    for cmd, name, src, base in ITEMS_MAP:
        dst = os.path.join(TEX, name + ".png")
        if src is None:
            build_bong_full().save(dst)
        else:
            shutil.copyfile(os.path.join(MOD, src), dst)
        print("текстура %-14s <- %s" % (name, src or "bong_potion + overlay"))

    # 2) модели — плоские спрайты, как у бутылок
    for cmd, name, src, base in ITEMS_MAP:
        model = {
            "credit": "Nirvana by TeamGalena, assets used on EKB SHIELD",
            "parent": "minecraft:item/generated",
            "textures": {"layer0": "shield:item/" + name},
        }
        with open(os.path.join(MODELS, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(model, f, ensure_ascii=False, indent=2)
            f.write("\n")

    # 3) определения предметов: один файл на базовый ванильный предмет
    by_base = {}
    for cmd, name, src, base in ITEMS_MAP:
        by_base.setdefault(base, []).append((cmd, name))

    for base, entries in sorted(by_base.items()):
        path = os.path.join(ITEMS, base + ".json")
        doc = {
            "model": {
                "type": "minecraft:select",
                "property": "minecraft:custom_model_data",
                "fallback": {"type": "minecraft:model", "model": "minecraft:item/" + base},
                "cases": [
                    {"when": cmd, "model": {"type": "minecraft:model", "model": "shield:item/" + name}}
                    for cmd, name in sorted(entries)
                ],
            }
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("предмет  %-18s %s" % (base, [c for c, _ in sorted(entries)]))


if __name__ == "__main__":
    main()
