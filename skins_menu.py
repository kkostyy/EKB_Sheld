# -*- coding: utf-8 -*-
"""EKB SHIELD — раздел меню «Скины по цвету» для build_menus.py.

Кнопки не пишутся руками, а собираются из того, что реально залито:
`skins/uploaded.json` (имя и URL подписанной текстуры) плюс PNG в `skins/`
(по нему считается цвет). Скин, которого нет на сервере, в меню не попадает —
кнопка «надеть» с ответом «скин не найден» хуже отсутствующей.

Голова на кнопке — `texture-<id>`: DeluxeMenus рисует её по id текстуры
Mojang, а id — последний кусок URL из учёта. Плагин голов не нужен.

Цвет берётся по ОДЕЖДЕ — корпус, руки, ноги, без головы: лицо у двух третей
скинов телесное, и по нему всё уезжало бы в «Бежевые».
"""
import colorsys
import io
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SKINS = os.path.join(ROOT, 'skins')
SR_SKINS = os.path.join(ROOT, 'server', 'plugins', 'SkinsRestorer', 'skins')

# ключ, подпись, материал иконки раздела
COLORS = [
    ('red', 'Красные', 'RED_WOOL', '&c'),
    ('orange', 'Оранжевые', 'ORANGE_WOOL', '&6'),
    ('yellow', 'Жёлтые', 'YELLOW_WOOL', '&e'),
    ('green', 'Зелёные', 'LIME_WOOL', '&a'),
    ('cyan', 'Голубые', 'LIGHT_BLUE_WOOL', '&b'),
    ('blue', 'Синие', 'BLUE_WOOL', '&9'),
    ('purple', 'Фиолетовые', 'PURPLE_WOOL', '&5'),
    ('pink', 'Розовые', 'PINK_WOOL', '&d'),
    ('brown', 'Коричневые', 'BROWN_WOOL', '&6'),
    ('beige', 'Бежевые и телесные', 'SAND', '&e'),
    ('white', 'Белые', 'WHITE_WOOL', '&f'),
    ('gray', 'Серые', 'GRAY_WOOL', '&7'),
    ('black', 'Чёрные', 'BLACK_WOOL', '&8'),
]

# одежда в развёртке 64x64: корпус, руки, ноги — основной слой и верхний
CLOTHES = [(16, 16, 40, 32), (40, 16, 56, 32), (0, 16, 16, 32),
           (32, 48, 48, 64), (16, 48, 32, 64),
           (16, 32, 40, 48), (40, 32, 56, 48), (0, 32, 16, 48),
           (48, 48, 64, 64), (0, 48, 16, 64)]


def pixel_color(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    h *= 360
    if v < 0.2:
        return 'black'
    if s < 0.18:
        return 'white' if v > 0.8 else 'gray'
    if h < 15 or h >= 345:
        return 'red'
    if h < 45:
        if v < 0.55:
            return 'brown'
        return 'beige' if s < 0.5 else 'orange'
    if h < 70:
        return 'yellow'
    if h < 165:
        return 'green'
    if h < 200:
        return 'cyan'
    if h < 255:
        return 'blue'
    if h < 290:
        return 'purple'
    return 'pink'


def classify(path):
    """PNG -> (цвет, светлота). Цвет — самый частый среди пикселей одежды."""
    from PIL import Image
    im = Image.open(path).convert('RGBA')
    boxes = CLOTHES if im.size[1] == 64 else CLOTHES[:3]
    count, light = {}, []
    for box in boxes:
        for x in range(box[0], box[2]):
            for y in range(box[1], box[3]):
                r, g, b, a = im.getpixel((x, y))
                if a < 128:
                    continue
                c = pixel_color(r, g, b)
                count[c] = count.get(c, 0) + 1
                light.append(r + g + b)
    if not count:
        return 'gray', 0
    return max(count, key=count.get), sum(light) / len(light)


def png_for(name):
    for f in (name + '.png', name + '_slim.png'):
        p = os.path.join(SKINS, f)
        if os.path.exists(p):
            return p, f.endswith('_slim.png')
    # имена вроде «Генерал Петухов.png»: сверяем по той же нормализации
    import add_skins
    for f in os.listdir(SKINS):
        if f.lower().endswith('.png'):
            base = f[:-4]
            slim = base.endswith('_slim')
            if slim:
                base = base[:-5]
            if add_skins.norm(base) == name:
                return os.path.join(SKINS, f), slim
    return None, False


def skin_menus():
    index_path = os.path.join(SKINS, 'uploaded.json')
    if not os.path.exists(index_path):
        return {}
    index = json.loads(io.open(index_path, encoding='utf-8').read())
    check_server = os.path.isdir(SR_SKINS)

    groups = {key: [] for key, _l, _m, _c in COLORS}
    for name, entry in sorted(index.items()):
        if check_server and not os.path.exists(
                os.path.join(SR_SKINS, name + '.customskin')):
            continue
        path, slim = png_for(name)
        url = entry.get('url', '')
        if not path or '/texture/' not in url:
            continue
        color, light = classify(path)
        groups[color].append((light, name, url.rsplit('/', 1)[1], slim))

    menus = {}
    hub = []
    for key, label, icon, code in COLORS:
        items = sorted(groups[key])
        if not items:
            continue
        buttons = []
        for i, (_l, name, tex, slim) in enumerate(items):
            buttons.append({
                'id': 's%03d' % i,
                'material': 'texture-' + tex,
                'name': code + '&l' + name.replace('_', ' '),
                'lore': ['&8/skin ' + name] + (['&7Тонкие руки'] if slim else []),
                'run': 'skin ' + name, 'tip': 'надеть',
            })
        menus['skins_' + key] = {
            'title': '&8Скины: ' + label.lower(),
            'header': code + '&l' + label,
            'icon': icon,
            'hint': ['&7Клик по голове — надеть скин.',
                     '&7Снять — «Скины» в Профиле, ПКМ.'],
            'back': 'ekb_skinscolor',
            'buttons': buttons,
        }
        hub.append({'id': key, 'material': icon, 'name': code + '&l' + label,
                    'lore': ['&7Скинов: &f%d' % len(items)],
                    'open': 'ekb_skins_' + key, 'tip': 'открыть'})

    if hub:
        menus['skinscolor'] = {
            'title': '&8Скины по цвету',
            'command': ['skincolor', 'скиныцвет'],
            'header': '&f&lСкины по цвету',
            'icon': 'WHITE_WOOL',
            'hint': ['&7Цвет считается по одежде, не по лицу.',
                     '&7Внутри раздела — от тёмных к светлым.'],
            'back': 'ekb_profile',
            'buttons': hub,
        }
    return menus
