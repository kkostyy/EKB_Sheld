# -*- coding: utf-8 -*-
"""EKB SHIELD — 3D-модели и иконки для всех кастомных предметов.

Каждому предмету с CustomModelData полагается своя текстура-развёртка 64×64
и объёмная модель: плоские спрайты в паке не остаются нигде.

⚠ Имена моделей берутся ИЗ `assets/minecraft/items/*.json`, а не из головы.
На этом уже обожглись: генератор писал `tequila_bottle.json`, а пак ссылался
на `tequila.json` — пять напитков молча оставались плоскими, хотя скрипт
рапортовал об успехе. Теперь список читается из пака, а в конце сверяется:
для каждого CMD должна существовать модель с `elements`.

Запуск:
    py -3 build_3d_models.py          # собрать всё
    py -3 build_3d_models.py --check  # показать план и пропуски

Развёртка (64×64, 4 пикселя текстуры = 1 пиксель модели):
    (0,0)–(31,31)   бока/лицо с этикеткой
    (32,0)–(47,15)  верх        (32,16)–(47,31) низ
    (48,0)–(63,15)  горло/бок   (48,16)–(63,31) пробка/деталь
"""
import glob
import io
import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(ROOT, 'resourcepack', 'assets', 'shield', 'models', 'item')
TEX = os.path.join(ROOT, 'resourcepack', 'assets', 'shield', 'textures', 'item')
ITEMS = os.path.join(ROOT, 'resourcepack', 'assets', 'minecraft', 'items')

# ---------------------------------------------------------------------------
# Что из чего сделано: имя модели -> (форма, эмблема, цвета)
# Цвета: основной, вторичный (жидкость/подкладка), акцент (этикетка), деталь
# ---------------------------------------------------------------------------

SPEC = {
    # --- напитки BreweryX -------------------------------------------------
    'jagermeister':        ('flask',  'deer',     (58, 82, 48),    (24, 40, 18),    (232, 214, 150), (90, 66, 40)),
    'jagermeister_orange': ('flask',  'deer',     (70, 92, 44),    (196, 104, 24),  (240, 226, 170), (90, 66, 40)),
    'jagermeister_dark':   ('flask',  'deer',     (40, 58, 36),    (16, 26, 14),    (196, 176, 120), (70, 52, 32)),
    'beer_bottle':         ('classic', 'hop',     (120, 88, 40),   (214, 152, 44),  (236, 226, 196), (140, 120, 90)),
    'tequila':             ('cone',   'cactus',   (196, 206, 188), (232, 214, 128), (228, 196, 96),  (120, 92, 56)),
    'rum':                 ('round',  'palm',     (110, 76, 44),   (150, 78, 30),   (226, 206, 160), (96, 70, 44)),
    'samogon':             ('round',  'star',     (150, 178, 140), (208, 226, 176), (226, 226, 214), (128, 104, 64)),
    'samogon_green':       ('jar',    'wheat',    (188, 200, 190), (226, 232, 208), (220, 214, 190), (150, 150, 150)),
    'vodka_absolut':       ('tall',   'star',     (206, 214, 216), (232, 240, 244), (208, 226, 236), (150, 156, 160)),
    'vodka_plain':         ('tall',   'wheat',    (200, 208, 212), (236, 240, 244), (226, 232, 236), (140, 146, 150)),
    'vodka_passionfruit':  ('tall',   'flower',   (206, 200, 214), (214, 132, 196), (238, 214, 232), (150, 120, 150)),
    'vodka_mojito':        ('tall',   'lime',     (198, 214, 198), (168, 216, 140), (226, 240, 216), (120, 150, 110)),
    'whiskey':             ('square', 'barrel',   (116, 82, 46),   (176, 108, 36),  (226, 210, 170), (96, 72, 44)),
    'rassol':              ('jar',    'cucumber', (196, 206, 198), (206, 196, 120), (226, 224, 200), (168, 172, 168)),

    # --- конопля Nirvana --------------------------------------------------
    'hemp_seeds':      ('seeds',   None, (146, 128, 84),  (110, 94, 58),   (0, 0, 0), (0, 0, 0)),
    'hemp':            ('plant',   None, (96, 142, 62),   (70, 112, 46),   (0, 0, 0), (0, 0, 0)),
    'weed_bud':        ('lump',    None, (96, 134, 62),   (64, 96, 44),    (0, 0, 0), (0, 0, 0)),
    'hemp_cloth':      ('cloth',   None, (196, 178, 126), (160, 142, 96),  (0, 0, 0), (0, 0, 0)),
    'hemp_burlap':     ('sack',    None, (164, 136, 88),  (126, 102, 62),  (0, 0, 0), (0, 0, 0)),
    'bong_empty':      ('tube',    None, (188, 210, 214), (150, 176, 182), (0, 0, 0), (0, 0, 0)),
    'bong_full':       ('tube',    None, (188, 210, 214), (110, 158, 86),  (0, 0, 0), (0, 0, 0)),
    'joint':           ('stick',   None, (238, 234, 220), (60, 56, 52),    (0, 0, 0), (0, 0, 0)),
    'pipe_empty':      ('stick',   None, (110, 78, 48),   (70, 52, 34),    (0, 0, 0), (0, 0, 0)),
    'pipe_stuffed':    ('stick',   None, (110, 78, 48),   (86, 122, 60),   (0, 0, 0), (0, 0, 0)),
    'pipe_suspicious': ('stick',   None, (110, 78, 48),   (138, 92, 160),  (0, 0, 0), (0, 0, 0)),
    'pipe_smouldering': ('stick',  None, (110, 78, 48),   (198, 96, 40),   (0, 0, 0), (0, 0, 0)),
    'herbal_salve':    ('salve',   None, (198, 196, 176), (120, 158, 86),  (0, 0, 0), (0, 0, 0)),
    'weed_brownie':    ('lump',    None, (92, 62, 40),    (64, 42, 28),    (0, 0, 0), (0, 0, 0)),
    'deerstalker':     ('hat',     None, (122, 104, 72),  (92, 76, 52),    (0, 0, 0), (0, 0, 0)),
    'thc_minecart':    ('crystal', None, (150, 226, 170), (96, 186, 120),  (0, 0, 0), (0, 0, 0)),

    # --- прочее -----------------------------------------------------------
    'death_note':      ('book',    None, (26, 24, 30),    (226, 220, 198), (150, 30, 38), (0, 0, 0)),

    # --- артефакты ExecutableItems (CMD 3001-3006) ------------------------
    # Силуэты разведены так же, как у бутылок: вещь должна узнаваться
    # раньше, чем игрок прочтёт её название. Диск, клинок, песочные часы,
    # книга, печать и маска не спутаешь ни в хотбаре, ни на земле.
    'bounty_compass':    ('dial',      None, (168, 142, 96),  (196, 64, 52),   (0, 0, 0), (0, 0, 0)),
    'shadow_dagger':     ('blade',     None, (48, 44, 56),    (90, 74, 110),   (0, 0, 0), (0, 0, 0)),
    'time_hourglass':    ('hourglass', None, (150, 118, 68),  (226, 200, 130), (0, 0, 0), (0, 0, 0)),
    'smuggler_journal':  ('book',      None, (58, 34, 30),    (208, 190, 150), (120, 96, 40), (0, 0, 0)),
    'black_mark':        ('seal',      None, (26, 24, 26),    (150, 30, 38),   (0, 0, 0), (0, 0, 0)),
    'faceless_mask':     ('mask',      None, (232, 228, 220), (60, 56, 60),    (0, 0, 0), (0, 0, 0)),
}

GLOW = {'pipe_smouldering', 'joint'}     # у кого тлеет кончик
GLOWING = {'bounty_compass', 'shadow_dagger', 'time_hourglass',
           'smuggler_journal', 'black_mark', 'faceless_mask'}
# ⚠️ GLOWING — это НЕ свечение текстуры, а пометка для отчёта: у всех
# шести артефактов в ExecutableItems стоит glow: true, то есть зачарованный
# блеск даёт сам предмет, а не модель. В паке для этого делать нечего.

# ---------------------------------------------------------------------------
# Эмблемы на этикетках: пиксельные значки 12×12
# ---------------------------------------------------------------------------


def emblem(d, ox, oy, kind, ink):
    def px(x, y, c=None):
        d.point((ox + x, oy + y), fill=c or ink)

    def box(x1, y1, x2, y2, c=None):
        d.rectangle([ox + x1, oy + y1, ox + x2, oy + y2], fill=c or ink)

    if kind == 'deer':
        box(5, 5, 6, 9); box(4, 4, 7, 5)
        for x, y in ((3, 3), (2, 2), (1, 1), (2, 0), (8, 3), (9, 2), (10, 1), (9, 0)):
            px(x, y)
    elif kind == 'wheat':
        box(5, 2, 6, 11)
        for y in range(3, 9, 2):
            px(3, y); px(4, y - 1); px(8, y); px(7, y - 1)
    elif kind == 'star':
        box(5, 1, 6, 10); box(1, 5, 10, 6)
        for i in range(3):
            px(3 + i, 3 + i); px(8 - i, 3 + i); px(3 + i, 8 - i); px(8 - i, 8 - i)
    elif kind == 'palm':
        box(5, 5, 6, 11)
        for x, y in ((2, 3), (3, 2), (4, 2), (7, 2), (8, 2), (9, 3), (1, 4), (10, 4)):
            px(x, y)
        box(4, 3, 7, 4)
    elif kind == 'cactus':
        box(5, 2, 6, 11); box(2, 5, 3, 9); box(3, 5, 4, 6)
        box(8, 4, 9, 8); box(7, 4, 8, 5)
    elif kind == 'barrel':
        box(2, 2, 9, 10)
        box(2, 4, 9, 4, (0, 0, 0)); box(2, 8, 9, 8, (0, 0, 0))
        px(1, 4); px(10, 4); px(1, 8); px(10, 8)
    elif kind == 'lime':
        box(3, 1, 8, 10); box(1, 3, 10, 8)
        px(2, 2); px(9, 2); px(2, 9); px(9, 9)
        d.line([(ox + 5, oy + 2), (ox + 5, oy + 9)], fill=(0, 0, 0))
        d.line([(ox + 2, oy + 5), (ox + 9, oy + 5)], fill=(0, 0, 0))
        d.line([(ox + 3, oy + 3), (ox + 8, oy + 8)], fill=(0, 0, 0))
        d.line([(ox + 8, oy + 3), (ox + 3, oy + 8)], fill=(0, 0, 0))
    elif kind == 'flower':
        box(5, 5, 6, 6); box(5, 2, 6, 3); box(5, 8, 6, 9)
        box(2, 5, 3, 6); box(8, 5, 9, 6)
        px(3, 3); px(8, 3); px(3, 8); px(8, 8)
    elif kind == 'cucumber':
        for i in range(7):
            box(2 + i, 8 - i, 4 + i, 10 - i)
        px(1, 9); px(9, 1)
        for x, y in ((3, 7), (5, 5), (7, 3), (4, 6), (6, 4)):
            px(x, y, (0, 0, 0))
    elif kind == 'hop':
        box(4, 3, 7, 9); px(3, 4); px(8, 4); px(3, 7); px(8, 7); box(5, 1, 6, 2)
        for y in range(4, 9, 2):
            px(5, y, (0, 0, 0)); px(6, y, (0, 0, 0))


# ---------------------------------------------------------------------------
# Текстуры
# ---------------------------------------------------------------------------

def shade(c, k):
    return tuple(max(0, min(255, int(v + k))) for v in c)


def tex_bottle(main, liquid, label, detail, mark, fill_top):
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 31, 31], fill=main)
    d.rectangle([0, fill_top, 31, 31], fill=liquid)
    d.rectangle([0, 0, 31, 1], fill=shade(main, 30))
    d.line([(2, 2), (2, 30)], fill=shade(main, 30))
    d.line([(29, 2), (29, 30)], fill=shade(main, -28))
    d.rectangle([0, 13, 31, 29], fill=label)
    d.rectangle([1, 14, 30, 28], outline=shade(label, -50))
    if mark:
        emblem(d, 10, 15, mark, shade(label, -95))
    d.line([(4, 27), (27, 27)], fill=shade(label, -95))
    d.rectangle([32, 0, 47, 15], fill=shade(main, 30))
    d.rectangle([32, 16, 47, 31], fill=shade(main, -28))
    d.rectangle([48, 0, 63, 15], fill=main)
    d.rectangle([48, 16, 63, 31], fill=detail)
    return img


def tex_simple(main, second, style):
    """Развёртки для предметов без этикетки: лицо, верх, низ, деталь."""
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 31, 31], fill=main)
    d.rectangle([32, 0, 47, 15], fill=shade(main, 28))
    d.rectangle([32, 16, 47, 31], fill=shade(main, -30))
    d.rectangle([48, 0, 63, 31], fill=second)

    if style == 'seeds':                       # зёрна на ткани
        for x in range(2, 30, 6):
            for y in range(2, 30, 6):
                d.ellipse([x, y, x + 3, y + 4], fill=second)
                d.point((x + 1, y + 1), fill=shade(second, 40))
    elif style == 'plant':                     # прожилки листа
        d.line([(16, 1), (16, 30)], fill=shade(main, -45))
        for y in range(4, 30, 5):
            d.line([(16, y), (6, y + 4)], fill=shade(main, -45))
            d.line([(16, y), (26, y + 4)], fill=shade(main, -45))
    elif style == 'cloth':                     # переплетение нитей
        for i in range(0, 32, 2):
            d.line([(i, 0), (i, 31)], fill=shade(main, -18))
        for i in range(1, 32, 4):
            d.line([(0, i), (31, i)], fill=shade(main, 16))
    elif style == 'sack':                      # мешковина крупнее и с завязкой
        for i in range(0, 32, 3):
            d.line([(i, 0), (i, 31)], fill=shade(main, -22))
            d.line([(0, i), (31, i)], fill=shade(main, -10))
        d.rectangle([0, 0, 31, 5], fill=second)
    elif style == 'lump':                      # неровный ком
        for x in range(0, 32, 5):
            for y in range((x // 5) % 3, 32, 7):
                d.rectangle([x, y, x + 2, y + 2], fill=second)
    elif style == 'tube':                      # стекло с водой
        d.rectangle([0, 18, 31, 31], fill=second)
        d.line([(3, 1), (3, 30)], fill=(236, 244, 246))
    elif style == 'stick':                     # черенок и чаша
        d.line([(0, 0), (31, 0)], fill=shade(main, 25))
        d.line([(0, 31), (31, 31)], fill=shade(main, -30))
        d.rectangle([48, 0, 63, 31], fill=second)
    elif style == 'salve':                     # баночка с мазью
        d.rectangle([0, 0, 31, 9], fill=second)
        d.rectangle([0, 10, 31, 31], fill=main)
        for y in range(13, 30, 4):
            d.line([(2, y), (29, y)], fill=shade(main, -20))
    elif style == 'hat':                       # твид в клетку
        for i in range(0, 32, 4):
            d.line([(i, 0), (i, 31)], fill=shade(main, -20))
            d.line([(0, i), (31, i)], fill=shade(main, -20))
        for i in range(2, 32, 8):
            d.line([(i, 0), (i, 31)], fill=shade(main, 22))
    elif style == 'crystal':                   # грани кристалла
        d.polygon([(16, 1), (30, 16), (16, 30), (2, 16)], fill=second)
        d.polygon([(16, 5), (26, 16), (16, 26), (6, 16)], fill=shade(second, 35))
        d.line([(16, 1), (16, 30)], fill=shade(second, 60))
    elif style == 'dial':                      # циферблат компаса
        d.ellipse([2, 2, 29, 29], fill=shade(main, -25), outline=shade(main, 40))
        d.ellipse([5, 5, 26, 26], fill=shade(main, 18))
        d.polygon([(16, 7), (19, 16), (16, 24), (13, 16)], fill=second)
        d.polygon([(16, 16), (19, 16), (16, 24), (13, 16)], fill=(236, 236, 240))
        d.point((16, 16), fill=(0, 0, 0))
        for x, y in ((16, 3), (16, 28), (3, 16), (28, 16)):
            d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=shade(main, 55))
    elif style == 'blade':                     # клинок с долом
        d.rectangle([12, 0, 19, 31], fill=main)
        d.rectangle([14, 2, 17, 29], fill=shade(main, 45))
        d.line([(16, 2), (16, 29)], fill=second)
        d.rectangle([48, 0, 63, 15], fill=second)          # рукоять
        d.rectangle([48, 16, 63, 31], fill=shade(second, -35))
        for y in range(18, 31, 3):
            d.line([(48, y), (63, y)], fill=shade(second, -55))
    elif style == 'hourglass':                 # песок в двух воронках
        d.rectangle([0, 0, 31, 31], fill=shade(main, -40))
        d.polygon([(3, 2), (28, 2), (17, 15), (14, 15)], fill=second)
        d.polygon([(14, 16), (17, 16), (28, 29), (3, 29)], fill=shade(second, -25))
        d.line([(15, 12), (15, 19)], fill=shade(second, 45))
        d.rectangle([32, 0, 47, 15], fill=main)            # рама
        d.rectangle([32, 16, 47, 31], fill=shade(main, -30))
    elif style == 'seal':                      # сургучная печать
        d.rectangle([0, 0, 31, 31], fill=main)
        d.ellipse([4, 4, 27, 27], fill=second)
        d.ellipse([8, 8, 23, 23], fill=shade(second, -40))
        # череп: две глазницы и зубы
        d.rectangle([11, 12, 13, 15], fill=main)
        d.rectangle([18, 12, 20, 15], fill=main)
        d.rectangle([13, 18, 18, 20], fill=main)
        for x in range(14, 19, 2):
            d.line([(x, 18), (x, 20)], fill=second)
    elif style == 'mask':                      # гладкая личина
        d.rectangle([0, 0, 31, 31], fill=main)
        d.ellipse([3, 1, 28, 30], fill=shade(main, 22))
        d.ellipse([8, 11, 13, 15], fill=second)            # глазницы
        d.ellipse([18, 11, 23, 15], fill=second)
        d.arc([11, 19, 20, 25], 200, 340, fill=second)     # рот
        d.line([(16, 15), (16, 18)], fill=shade(main, -30))
        d.rectangle([48, 0, 63, 31], fill=shade(main, -35))  # изнанка
    elif style == 'book':
        d.rectangle([2, 2, 29, 29], outline=shade(main, -30))
        d.line([(8, 10), (23, 10)], fill=(150, 30, 38))
        d.line([(8, 14), (23, 14)], fill=(150, 30, 38))
        d.rectangle([32, 0, 63, 31], fill=second)
        for y in range(2, 30, 3):
            d.line([(32, y), (63, y)], fill=shade(second, -25))
    return img


def tex_glow(img, tip):
    """Подсвеченный кончик для тлеющих вещей."""
    d = ImageDraw.Draw(img)
    d.rectangle([52, 4, 59, 11], fill=(255, 196, 96))
    d.rectangle([54, 6, 57, 9], fill=(255, 240, 180))
    return img

# ---------------------------------------------------------------------------
# Формы
# ---------------------------------------------------------------------------

def face(uv, tex='#0'):
    return {'uv': uv, 'texture': tex}


def sides(uv):
    return {k: face(uv) for k in ('north', 'south', 'east', 'west')}


def cube(x1, y1, z1, x2, y2, z2, uv, up=None, down=None, rot=None):
    el = {'from': [x1, y1, z1], 'to': [x2, y2, z2], 'faces': sides(uv)}
    if up:
        el['faces']['up'] = face(up)
    if down:
        el['faces']['down'] = face(down)
    if rot:
        el['rotation'] = rot
    return el


FRONT, CAP, BOTTOM, SIDE = [0, 0, 8, 8], [8, 0, 12, 4], [8, 4, 12, 8], [12, 0, 16, 8]


def shape(kind):
    """Кубы предмета и уровень жидкости для текстуры бутылки."""
    if kind == 'classic':
        return [cube(5, 0, 5, 11, 8, 11, FRONT, None, BOTTOM),
                cube(5.5, 8, 5.5, 10.5, 10, 10.5, [0, 2, 8, 6]),
                cube(6.5, 10, 6.5, 9.5, 12, 9.5, [0, 4, 8, 7], CAP),
                cube(7, 12, 7, 9, 15, 9, SIDE),
                cube(6.8, 15, 6.8, 9.2, 16, 9.2, [12, 4, 16, 8], [12, 4, 16, 8])], 10
    if kind == 'flask':
        return [cube(4.5, 0, 6, 11.5, 10, 10, FRONT, CAP, BOTTOM),
                cube(5.5, 10, 6.5, 10.5, 11.5, 9.5, [0, 0, 8, 3], CAP),
                cube(7, 11.5, 7, 9, 14, 9, SIDE),
                cube(6.6, 14, 6.6, 9.4, 15.5, 9.4, [12, 4, 16, 8], [12, 4, 16, 8])], 9
    if kind == 'tall':
        return [cube(6, 0, 6, 10, 11, 10, FRONT, CAP, BOTTOM),
                cube(6.5, 11, 6.5, 9.5, 12.5, 9.5, [0, 0, 8, 3], CAP),
                cube(7, 12.5, 7, 9, 15, 9, SIDE),
                cube(6.7, 15, 6.7, 9.3, 16, 9.3, [12, 4, 16, 8], [12, 4, 16, 8])], 7
    if kind == 'square':
        return [cube(4, 0, 4.5, 12, 8, 11.5, FRONT, CAP, BOTTOM),
                cube(5, 8, 5.5, 11, 10, 10.5, [0, 0, 8, 3], CAP),
                cube(7, 10, 7, 9, 13, 9, SIDE),
                cube(6.5, 13, 6.5, 9.5, 14.5, 9.5, [12, 4, 16, 8], [12, 4, 16, 8])], 11
    if kind == 'round':
        return [cube(4.5, 0, 4.5, 11.5, 7, 11.5, FRONT, CAP, BOTTOM),
                cube(5.5, 7, 5.5, 10.5, 9.5, 10.5, [0, 0, 8, 4], CAP),
                cube(6.8, 9.5, 6.8, 9.2, 13.5, 9.2, SIDE),
                cube(6.4, 13.5, 6.4, 9.6, 15, 9.6, [12, 4, 16, 8], [12, 4, 16, 8])], 12
    if kind == 'cone':
        return [cube(5, 0, 5, 11, 4, 11, [0, 0, 8, 4], None, BOTTOM),
                cube(5.5, 4, 5.5, 10.5, 8, 10.5, [0, 2, 8, 6]),
                cube(6, 8, 6, 10, 11, 10, [0, 4, 8, 8], CAP),
                cube(7, 11, 7, 9, 14.5, 9, SIDE),
                cube(6.6, 14.5, 6.6, 9.4, 16, 9.4, [12, 4, 16, 8], [12, 4, 16, 8])], 8
    if kind == 'jar':
        return [cube(4, 0, 4, 12, 10, 12, FRONT, None, BOTTOM),
                cube(4.5, 10, 4.5, 11.5, 12, 11.5, [12, 4, 16, 8], [12, 4, 16, 8])], 6
    if kind == 'seeds':                       # горсть зёрен на ладони
        els = [cube(4, 0, 4, 12, 1, 12, FRONT, FRONT, BOTTOM)]
        for x, z in ((5, 6), (7, 5), (9, 7), (6, 9), (8, 9)):
            els.append(cube(x, 1, z, x + 1.5, 2, z + 1.5, SIDE, SIDE))
        return els, 0
    if kind == 'plant':                       # стебель с листьями
        return [cube(7.5, 0, 7.5, 8.5, 14, 8.5, SIDE),
                cube(3, 6, 7.8, 7.5, 11, 8.2, FRONT, FRONT),
                cube(8.5, 8, 7.8, 13, 13, 8.2, FRONT, FRONT),
                cube(5, 10, 7.8, 8, 15, 8.2, FRONT, FRONT)], 0
    if kind == 'cloth':                       # сложенное полотно
        return [cube(3, 0, 4, 13, 2, 12, FRONT, FRONT, BOTTOM),
                cube(4, 2, 5, 12, 3.5, 11, FRONT, FRONT),
                cube(5, 3.5, 6, 11, 4.5, 10, FRONT, FRONT)], 0
    if kind == 'sack':                        # мешок с перевязью
        return [cube(4, 0, 4, 12, 9, 12, FRONT, None, BOTTOM),
                cube(5, 9, 5, 11, 11, 11, FRONT),
                cube(6, 11, 6, 10, 13, 10, SIDE, SIDE)], 0
    if kind == 'lump':
        return [cube(5, 3, 5, 11, 10, 11, FRONT, FRONT, FRONT),
                cube(6, 9.5, 6, 10, 12, 10, FRONT, FRONT)], 0
    if kind == 'tube':
        return [cube(5, 0, 5, 11, 4, 11, FRONT, None, BOTTOM),
                cube(6.5, 4, 6.5, 9.5, 14, 9.5, FRONT),
                cube(6, 14, 6, 10, 15.5, 10, SIDE, SIDE)], 0
    if kind == 'stick':
        rot = {'angle': 22.5, 'axis': 'x', 'origin': [8, 8, 8]}
        return [cube(7, 2, 7, 9, 13, 9, FRONT, None, None, rot),
                cube(6.2, 12.5, 6.2, 9.8, 15, 9.8, SIDE, SIDE, None, rot)], 0
    if kind == 'salve':                       # низкая баночка с крышкой
        return [cube(5, 0, 5, 11, 4, 11, FRONT, None, BOTTOM),
                cube(4.5, 4, 4.5, 11.5, 5.5, 11.5, SIDE, SIDE)], 0
    if kind == 'hat':                         # двухкозырка: тулья и козырьки
        return [cube(4, 2, 4, 12, 7, 12, FRONT, CAP),
                cube(2.5, 1, 2.5, 13.5, 2, 13.5, FRONT, FRONT, BOTTOM),
                cube(2.5, 1, 0.5, 13.5, 2, 2.5, SIDE, SIDE),
                cube(2.5, 1, 13.5, 13.5, 2, 15.5, SIDE, SIDE)], 0
    if kind == 'crystal':                     # кристалл ТГК
        rot = {'angle': 45, 'axis': 'y', 'origin': [8, 8, 8]}
        return [cube(6, 2, 6, 10, 9, 10, FRONT, FRONT, FRONT, rot),
                cube(7, 9, 7, 9, 12, 9, FRONT, FRONT, None, rot),
                cube(7, 0, 7, 9, 2, 9, FRONT, None, FRONT, rot)], 0
    if kind == 'dial':                        # компас: плоский диск
        return [cube(3, 0, 3, 13, 1, 13, FRONT, FRONT, BOTTOM),
                cube(2.5, 1, 2.5, 13.5, 1.6, 13.5, SIDE, FRONT, SIDE)], 0
    if kind == 'blade':                       # кинжал под наклоном
        rot = {'angle': 45, 'axis': 'z', 'origin': [8, 8, 8]}
        return [cube(7.4, 4, 7.4, 8.6, 15, 8.6, FRONT, FRONT, None, rot),
                cube(6, 3, 7.5, 10, 4, 8.5, SIDE, SIDE, SIDE, rot),
                cube(7.2, 0, 7.2, 8.8, 3, 8.8, SIDE, SIDE, SIDE, rot)], 0
    if kind == 'hourglass':                   # две воронки в раме
        return [cube(4, 0, 4, 12, 1.5, 12, SIDE, SIDE, BOTTOM),
                cube(5, 1.5, 5, 11, 6, 11, FRONT),
                cube(7, 6, 7, 9, 9, 9, FRONT),
                cube(5, 9, 5, 11, 13.5, 11, FRONT),
                cube(4, 13.5, 4, 12, 15, 12, SIDE, SIDE)], 0
    if kind == 'seal':                        # плоская печать на шнурке
        return [cube(4, 0, 4, 12, 1.5, 12, FRONT, FRONT, BOTTOM),
                cube(5, 1.5, 5, 11, 2.2, 11, FRONT, FRONT),
                cube(7.5, 2.2, 7.5, 8.5, 6, 8.5, SIDE, SIDE)], 0
    if kind == 'mask':                        # выгнутая личина
        return [cube(3.5, 2, 6.5, 12.5, 14, 8, FRONT, SIDE, SIDE),
                cube(4.5, 3, 5.8, 11.5, 13, 6.5, FRONT, FRONT, FRONT),
                cube(3, 5, 7.5, 3.8, 11, 8.2, SIDE, SIDE, SIDE),
                cube(12.2, 5, 7.5, 13, 11, 8.2, SIDE, SIDE, SIDE)], 0
    # book
    return [cube(3.5, 0, 4, 12.5, 1, 12, [0, 0, 8, 1], FRONT, FRONT),
            cube(4, 1, 4.5, 12, 2.2, 11.5, [8, 0, 16, 2], [8, 0, 16, 8]),
            cube(3.5, 2.2, 4, 12.5, 3.2, 12, [0, 8, 8, 12], FRONT)], 0


DISPLAY = {
    # Компас, печать и маска лежат плашмя: их надо читать в слоте, а не
    # рассматривать сбоку. Кинжал наоборот — его узнают по силуэту клинка.
    'dial': {'gui': [90, 0, 0, 1.15], 'hand': [0, 0, 0, 0.7]},
    'blade': {'gui': [20, -30, 0, 1.05], 'hand': [0, -90, 25, 0.9]},
    'hourglass': {'gui': [25, -25, 0, 1.0], 'hand': [0, 0, 0, 0.7]},
    'seal': {'gui': [75, 0, 0, 1.1], 'hand': [0, 0, 0, 0.7]},
    'mask': {'gui': [5, -25, 0, 1.15], 'hand': [0, 0, 0, 0.8]},
    'book': {'gui': [30, 135, 0, 1.1], 'hand': [0, -90, 55, 0.85]},
    'hat':  {'gui': [25, -35, 0, 0.95], 'hand': [0, 0, 0, 0.7]},
    'cloth': {'gui': [30, -35, 0, 1.1], 'hand': [0, 0, 0, 0.6]},
    'seeds': {'gui': [35, -35, 0, 1.15], 'hand': [0, 0, 0, 0.6]},
}


def model(texture, kind):
    els, _ = shape(kind)
    conf = DISPLAY.get(kind, {'gui': [25, -35, 0, 1.0], 'hand': [0, 0, 0, 0.65]})
    gx, gy, gz, gs = conf['gui']
    hx, hy, hz, hs = conf['hand']
    return {
        'credit': 'EKB SHIELD — сгенерировано build_3d_models.py',
        'texture_size': [64, 64],
        'textures': {'0': 'shield:item/%s' % texture, 'particle': 'shield:item/%s' % texture},
        'elements': els,
        'display': {
            'thirdperson_righthand': {'rotation': [hx, hy, hz], 'translation': [0, 3, 1], 'scale': [hs, hs, hs]},
            'firstperson_righthand': {'rotation': [0, -90, 25], 'translation': [0, 4, 2], 'scale': [hs + 0.05, hs + 0.05, hs + 0.05]},
            'gui': {'rotation': [gx, gy, gz], 'translation': [0, 0, 0], 'scale': [gs, gs, gs]},
            'ground': {'scale': [0.5, 0.5, 0.5]},
            'fixed': {'rotation': [0, 180, 0], 'scale': [1, 1, 1]},
            'head': {'scale': [1, 1, 1]},
        },
    }


def write(path, data):
    io.open(path, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def pack_models():
    """CMD -> имя модели, прямо из assets/minecraft/items/*.json."""
    found = {}
    for f in glob.glob(os.path.join(ITEMS, '*.json')):
        data = json.load(io.open(f, encoding='utf-8'))

        def walk(node):
            if isinstance(node, dict):
                # ⚠ только range_dispatch по custom_model_data: у компаса и
                # часов в ванильном fallback лежит СВОЙ range_dispatch
                # (minecraft:compass, minecraft:time) с порогами 0…31 и 0…63,
                # и без этой проверки генератор считал их за наши CMD и
                # рапортовал о 64 предметах «без 3D-модели».
                if node.get('property') == 'minecraft:custom_model_data':
                    for e in node.get('entries', []):
                        t, m = e.get('threshold'), e.get('model', {})
                        if t is not None:
                            found[int(t)] = m.get('model', '').split('/')[-1]
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
        walk(data)
    return found


BOTTLES = {'classic', 'flask', 'tall', 'square', 'round', 'cone', 'jar'}

if __name__ == '__main__':
    check = '--check' in sys.argv
    used = pack_models()
    print('предметов в паке: %d' % len(used))

    missing = [n for n in used.values() if n not in SPEC]
    if missing:
        print('НЕТ В СПЕЦИФИКАЦИИ: %s' % ', '.join(sorted(missing)))

    made = 0
    for cmd, name in sorted(used.items()):
        if name not in SPEC:
            continue
        kind, mark, main, second, label, detail = SPEC[name]
        print('%5d  %-20s %-8s' % (cmd, name, kind))
        if check:
            continue
        tex_name = name + '_3d'
        if kind in BOTTLES:
            _, fill = shape(kind)
            img = tex_bottle(main, second, label, detail, mark, fill)
        else:
            img = tex_simple(main, second, kind)
            if name in GLOW:
                img = tex_glow(img, second)
        img.save(os.path.join(TEX, tex_name + '.png'))
        write(os.path.join(MODELS, name + '.json'), model(tex_name, kind))
        made += 1

    if not check:
        # проверка: у каждого CMD своя объёмная модель и своя текстура
        flat, notex = [], []
        for cmd, name in sorted(used.items()):
            mp = os.path.join(MODELS, name + '.json')
            if not os.path.exists(mp) or 'elements' not in io.open(mp, encoding='utf-8').read():
                flat.append('%s (%s)' % (name, cmd))
            if not os.path.exists(os.path.join(TEX, name + '_3d.png')):
                notex.append(name)
        print('\nсобрано: %d' % made)
        print('без 3D-модели: %s' % (', '.join(flat) if flat else 'нет'))
        print('без текстуры:  %s' % (', '.join(notex) if notex else 'нет'))
        print('\nдальше: py -3 pack_resourcepack.py')
