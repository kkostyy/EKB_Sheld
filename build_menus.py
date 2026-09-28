# -*- coding: utf-8 -*-
"""EKB SHIELD — генератор меню DeluxeMenus.

Меню собираются отсюда, а не правятся руками: 19 файлов на одной сетке
руками не удержать, раскладка разъезжается после первой же вставки кнопки.
Здесь описываются только разделы и кнопки, всё остальное — сетка, рамка,
навигация, права — добавляется автоматически.

Запуск:
    py -3 build_menus.py            # собрать в plugins/DeluxeMenus/gui_menus
    py -3 build_menus.py --install  # и скопировать на сервер

После сборки на сервере: /dm reload

Правила раскладки (одинаковы во всех меню):
    ряд 0        рамка, в центре — заголовок раздела
    10-16        первый ряд кнопок
    19-25, 28-34, 37-43   следующие ряды
    45           «Назад», 49 «Закрыть», прочее в нижнем ряду — рамка
Каждый ряд центрируется, если кнопок меньше семи.

Действия кнопок:
    run:    команда от имени игрока      ([player])
    open:   открыть другое меню          ([openguimenu])
    say:    сообщение игроку             ([message])
    right:  то же самое для правой кнопки (словарь такого же вида)
"""
import io
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'plugins', 'DeluxeMenus', 'gui_menus')
SERVER = os.path.join(ROOT, 'server', 'plugins', 'DeluxeMenus', 'gui_menus')
HEADS = json.load(io.open(os.path.join(ROOT, 'plugins', 'DeluxeMenus', 'heads.json'),
                          encoding='utf-8'))

ROWS = [[10, 11, 12, 13, 14, 15, 16],
        [19, 20, 21, 22, 23, 24, 25],
        [28, 29, 30, 31, 32, 33, 34],
        [37, 38, 39, 40, 41, 42, 43]]
FRAME = [0, 1, 2, 3, 5, 6, 7, 8, 9, 17, 18, 26, 27, 35, 36, 44, 46, 47, 48, 50, 51, 52, 53]
BACK, CLOSE, TITLE = 45, 49, 4


def head(key):
    return 'basehead-' + HEADS[key]


def esc(text):
    return text.replace("'", "''")


# Сколько кнопок влезает на одну страницу: четыре чистых ряда.
# Раньше при переполнении раскрывался нижний ряд (EXTRA), и «Все вещи»
# упирались в 34 кнопки, прижатые к «Назад» и «Закрыть». Теперь лишнее
# уезжает на следующую страницу, а нижний ряд отдан навигации.
PER_PAGE = sum(len(r) for r in ROWS)
PREV, NEXT = 48, 50


# Раскладка «ёлочкой»: сверху узко, книзу шире — так меню читается сверху
# вниз, а не сплошной стеной. Центры рядов сходятся к слоту 4, где стоит
# заголовок раздела, поэтому картинка симметрична.
TREE = [[13],
        [20, 22, 24],
        [28, 29, 30, 31, 32, 33, 34],
        [37, 38, 39, 40, 41, 42, 43]]


def place(buttons):
    """Ёлочка, пока помещается; дальше — плотная сетка."""
    n = len(buttons)
    rows = TREE if n <= sum(len(r) for r in TREE) else ROWS
    slots, left = [], n
    for row in rows:
        if left <= 0:
            break
        take = min(left, len(row))
        start = (len(row) - take) // 2
        slots.extend(row[start:start + take])
        left -= take
    return slots


def page_id(name, page):
    return name if page == 1 else '%s_%d' % (name, page)


def render(name, spec, page=1, pages=1):
    title = spec['title']
    if pages > 1:
        title = '%s &8(%d/%d)' % (title, page, pages)
    lines = ["menu_title: '%s'" % esc(title)]
    # Команда открытия — только у первой страницы: /allitems ведёт на начало,
    # дальше листают стрелками.
    if spec.get('command') and page == 1:
        lines.append('open_command:')
        for c in spec['command']:
            lines.append('  - %s' % c)
    lines.append('size: 54')
    if spec.get('permission'):
        lines += [
            'open_requirement:',
            '  requirements:',
            '    perm:',
            '      type: has permission',
            '      permission: %s' % spec['permission'],
            '      deny_commands:',
            "        - '[message] %s'" % esc(spec.get('deny', '&cНет доступа.')),
        ]
    lines.append('')
    lines.append('items:')

    buttons = spec['buttons'][(page - 1) * PER_PAGE: page * PER_PAGE]
    slots = place(buttons)
    for btn, slot in zip(buttons, slots):
        lines += button(btn, slot)

    # заголовок раздела в центре верхней рамки
    lines += ['', "  'header':",
              '    material: %s' % material(spec.get('icon', 'NETHER_STAR')),
              '    slot: %d' % TITLE,
              "    display_name: '%s'" % esc(spec['header'])]
    if spec.get('hint'):
        lines.append('    lore:')
        for row in spec['hint']:
            lines.append("      - '%s'" % esc(row))

    # «Назад» ведёт НА ОДНУ СТРАНИЦУ назад, а не сразу к родителю: на 2-й
    # странице каталога она возвращает на 1-ю, и только с 1-й — в родительский
    # раздел. Так «Назад» всегда шаг назад, а не прыжок наружу.
    if page > 1:
        lines += ['', "  'back':", '    material: ARROW', '    slot: %d' % BACK,
                  "    display_name: '&7Назад'",
                  '    lore:', "      - '&7На страницу %d'" % (page - 1),
                  '    left_click_commands:',
                  "      - '[openguimenu] ekb_%s'" % page_id(name, page - 1)]
    elif spec.get('back'):
        lines += ['', "  'back':", '    material: ARROW', '    slot: %d' % BACK,
                  "    display_name: '&7Назад'", '    left_click_commands:',
                  "      - '[openguimenu] %s'" % spec['back']]
    if page > 1:
        lines += ['', "  'prev_page':", '    material: SPECTRAL_ARROW',
                  '    slot: %d' % PREV,
                  "    display_name: '&e&lПредыдущая страница'",
                  '    lore:', "      - '&7Страница %d из %d'" % (page - 1, pages),
                  '    left_click_commands:',
                  "      - '[openguimenu] ekb_%s'" % page_id(name, page - 1)]
    if page < pages:
        lines += ['', "  'next_page':", '    material: SPECTRAL_ARROW',
                  '    slot: %d' % NEXT,
                  "    display_name: '&e&lСледующая страница'",
                  '    lore:', "      - '&7Страница %d из %d'" % (page + 1, pages),
                  '    left_click_commands:',
                  "      - '[openguimenu] ekb_%s'" % page_id(name, page + 1)]

    lines += ['', "  'close':", '    material: BARRIER', '    slot: %d' % CLOSE,
              "    display_name: '&cЗакрыть'", '    left_click_commands:',
              "      - '[close]'"]

    # Рамка по периметру: обводит содержимое и отделяет от инвентаря.
    # Слоты, занятые кнопками и навигацией, пропускаются.
    lines.append('')
    lines.append('  # рамка ставится генератором, руками её не правят')
    # ⚠ Стрелки листания стоят В НИЖНЕМ РЯДУ, то есть внутри рамки:
    # без этой пометки генератор ставил на их слоты ещё и стекло,
    # а два предмета в одном слоте DeluxeMenus разбирает как повезёт.
    busy = set(slots) | {BACK, CLOSE, TITLE}
    if page > 1:
        busy.add(PREV)
    if page < pages:
        busy.add(NEXT)
    for f in [x for x in FRAME if x not in busy]:
        lines += ["  'frame_%d':" % f, '    material: GRAY_STAINED_GLASS_PANE',
                  '    slot: %d' % f, "    display_name: ' '"]
    return '\n'.join(lines) + '\n'


def material(value):
    """HEAD:ключ -> кастомная голова из heads.json, остальное как есть."""
    if value.startswith('HEAD:'):
        return head(value.split(':', 1)[1])
    return value


def button(btn, slot):
    out = ["", "  '%s':" % btn['id'],
           '    material: %s' % material(btn['material']),
           '    slot: %d' % slot,
           "    display_name: '%s'" % esc(btn['name'])]
    lore = list(btn.get('lore', []))
    tips = []
    if btn.get('run') or btn.get('open') or btn.get('say') or btn.get('close'):
        tips.append('&aЛКМ &8— %s' % btn.get('tip', 'выполнить'))
    if btn.get('right'):
        tips.append('&aПКМ &8— %s' % btn['right'].get('tip', 'выполнить'))
    if lore and tips:
        lore.append('')
    lore += tips
    if lore:
        out.append('    lore:')
        for row in lore:
            out.append("      - '%s'" % esc(row))
    if btn.get('cmd'):
        # ⚠ Без model_data кнопка показывает ВАНИЛЬНЫЙ предмет: трубка —
        # палкой, семена конопли — семенами, все 14 напитков — одинаковым
        # зельем. Модели в паке есть, но клиент выбирает их по
        # CustomModelData, а DeluxeMenus по умолчанию его не ставит.
        # У плагина это `model_data` (старый числовой способ) — ровно тот,
        # что читает наш range_dispatch.
        out.append('    model_data: %d' % btn['cmd'])
    if btn.get('view'):
        # Список прав = «любое из них». У DeluxeMenus требования по умолчанию
        # складываются по И, а minimum_requirements: 1 превращает это в ИЛИ.
        # Без него кнопку с двумя правами не видел никто: ни у кого нет обоих.
        perms = btn['view'] if isinstance(btn['view'], list) else [btn['view']]
        out.append('    view_requirement:')
        if len(perms) > 1:
            out.append('      minimum_requirements: 1')
        out.append('      requirements:')
        for i, perm in enumerate(perms, 1):
            out += ['        perm%d:' % i,
                    '          type: has permission',
                    '          permission: %s' % perm]
    left = actions(btn)
    if left:
        out.append('    left_click_commands:')
        out += ['      - %s' % a for a in left]
    right = actions(btn.get('right') or {})
    if right:
        out.append('    right_click_commands:')
        out += ['      - %s' % a for a in right]
    return out


def actions(btn):
    out = []
    if btn.get('close'):
        # ⚠ Порядок важен: [close] идёт ПЕРЕД командой. Иначе игрок
        # останется с открытым меню поверх того, что команда ему показала —
        # именно так сделаны ручные меню, оттуда и взято.
        out.append("'[close]'")
    if btn.get('open'):
        out.append("'[openguimenu] %s'" % btn['open'])
    if btn.get('run'):
        # ⚠ После [close] команда идёт с задержкой в 2 тика. DeluxeMenus
        # закрывает меню не сразу, а своим отложенным закрытием — и оно
        # захлопывало окно, которое команда только что открыла (мастер
        # `ekbdo`, рулетка, наём…): кнопка «ничего не делала». Так ломались
        # 53 кнопки из 104 с [close] (28.09.2026). Две тика — меню уже
        # закрыто, окно Skript открывается поверх пустого экрана.
        # ⚠ Без пробела: DeluxeMenus вырезает сам тег, а пробел перед ним
        # оставляет — и команда без аргументов (`/roulette `) падала с
        # «Неверный аргумент для команды» (28.09.2026, скриншот владельца).
        tail = '<delay=2>' if btn.get('close') else ''
        out.append("'[player] %s%s'" % (btn['run'], tail))
    if btn.get('say'):
        for row in btn['say']:
            out.append("'[message] %s'" % esc(row))
    return out


from menus_spec import MENUS  # спецификация лежит отдельно, чтобы не мешать коду

CONFIG = os.path.join(ROOT, 'plugins', 'DeluxeMenus', 'config.yml')
SERVER_CONFIG = os.path.join(ROOT, 'server', 'plugins', 'DeluxeMenus', 'config.yml')


MARK = '# рамка ставится генератором'


def sweep(made):
    """Удалить меню, которые генератор когда-то собрал, а теперь нет.

    Без этого старый файл остаётся жить и держать свою `open_command`:
    после разборки каталога на разделы `/newitems` остался и у
    старого newitems.yml, и у нового allitems.yml — два меню на одну
    команду. Ручные меню не трогаем: у них нет метки генератора.
    """
    keep = set(made)
    gone = []
    for f in sorted(os.listdir(OUT)):
        if not f.endswith('.yml') or f[:-4] in keep:
            continue
        path = os.path.join(OUT, f)
        if MARK not in io.open(path, encoding='utf-8').read():
            continue          # ручное меню, не наше дело
        os.remove(path)
        sp = os.path.join(SERVER, f)
        if os.path.exists(sp):
            os.remove(sp)
        gone.append(f[:-4])
    return gone


def unregister(ids):
    """Выкинуть из config.yml две строки на каждое удалённое меню."""
    for path in (CONFIG, SERVER_CONFIG):
        if not os.path.exists(path):
            continue
        lines = io.open(path, encoding='utf-8').read().split('\n')
        out, skip = [], False
        for line in lines:
            if line.strip().rstrip(':') in ids and line.startswith('  ekb_'):
                skip = True
                continue
            if skip:
                skip = False
                if line.strip().startswith('file:'):
                    continue
            out.append(line)
        io.open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))


def register(ids):
    """Дописать в config.yml меню, которых там ещё нет.

    ⚠ Файл, которого нет в `gui_menus:` config.yml, DeluxeMenus просто не
    видит: кнопка «открыть» молча не срабатывает. Раньше регистрация была
    ручной, и каждое новое меню приходилось вспоминать отдельно — теперь
    за этим следит генератор. Правим построчно, а не через yaml.dump:
    в файле полсотни строк комментариев про права, их терять нельзя.
    """
    added = []
    for path in (CONFIG, SERVER_CONFIG):
        if not os.path.exists(path):
            continue
        lines = io.open(path, encoding='utf-8').read().split('\n')
        have = set()
        for line in lines:
            if line.startswith('  ekb_') and line.rstrip().endswith(':'):
                have.add(line.strip().rstrip(':'))
        new = [i for i in ids if i not in have]
        if not new:
            continue
        # дописываем в конец секции gui_menus: она идёт до конца файла
        while lines and not lines[-1].strip():
            lines.pop()
        for i in new:
            lines += ['  %s:' % i, '    file: %s.yml' % i[4:]]
        lines.append('')
        io.open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
        added = new
    return added


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    made = []
    for name, spec in MENUS.items():
        total = len(spec['buttons'])
        pages = max(1, -(-total // PER_PAGE))
        for page in range(1, pages + 1):
            pid = page_id(name, page)
            text = render(name, spec, page, pages)
            io.open(os.path.join(OUT, pid + '.yml'), 'w',
                    encoding='utf-8', newline='\n').write(text)
            made.append(pid)
        note = '' if pages == 1 else '  -> %d страницы' % pages
        print('%-18s %d кнопок%s' % (name + '.yml', total, note))

    gone = sweep(made)
    if gone:
        unregister(set('ekb_' + g for g in gone))
        print('\nудалены выпавшие из спецификации: %s' % ', '.join(gone))

    new = register(['ekb_' + m for m in made])
    if new:
        print('зарегистрировано в config.yml: %s' % ', '.join(new))

    if '--install' in sys.argv:
        for name in made:
            shutil.copy(os.path.join(OUT, name + '.yml'),
                        os.path.join(SERVER, name + '.yml'))
        print('скопировано на сервер:', len(made))
    print('\nготово. На сервере: /dm reload')
