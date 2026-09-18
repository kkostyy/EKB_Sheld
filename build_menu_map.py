# -*- coding: utf-8 -*-
"""EKB SHIELD — генератор docs/menu_map.md.

Карта меню правилась руками и поэтому врала: на 18.09.2026 в ней стояло
32 меню и 360 кнопок, когда в gui_menus/ уже лежало 40 и 430. Документ,
который надо обновлять отдельно от кода, устаревает после первой же правки,
поэтому он собирается из самих YAML — как и сами меню из menus_spec.py.

Запуск:
    py -3 build_menu_map.py            # переписать docs/menu_map.md
    py -3 build_menu_map.py --check    # только проверить, что файл свежий

Дерево строится по кнопкам [openguimenu]: родитель — тот, кто открывает.
Меню, в которое никто не ведёт, печатается отдельным корнем.
"""
import io
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
MENUS_DIR = os.path.join(ROOT, 'plugins', 'DeluxeMenus', 'gui_menus')
CONFIG = os.path.join(ROOT, 'plugins', 'DeluxeMenus', 'config.yml')
OUT = os.path.join(ROOT, 'docs', 'menu_map.md')

COLOR = re.compile(r'&[0-9a-fk-or]')


def plain(text):
    """Убирает цветовые коды: в документе они только мешают читать."""
    return COLOR.sub('', str(text)).strip()


def load():
    cfg = yaml.safe_load(io.open(CONFIG, encoding='utf-8'))
    by_id, by_file = {}, {}
    for menu_id, spec in (cfg.get('gui_menus') or {}).items():
        path = os.path.join(MENUS_DIR, spec['file'])
        if not os.path.exists(path):
            print('ВНИМАНИЕ: %s зарегистрирован, но файла нет' % spec['file'])
            continue
        data = yaml.safe_load(io.open(path, encoding='utf-8'))
        by_id[menu_id] = (spec['file'], data)
        by_file[spec['file']] = menu_id
    return by_id, by_file


def commands(data):
    cmd = data.get('open_command')
    if not cmd:
        return []
    if isinstance(cmd, str):
        return [cmd]
    return list(cmd)


def permission(data):
    req = (data.get('open_requirement') or {}).get('requirements') or {}
    for value in req.values():
        if value.get('permission'):
            return value['permission']
    return None


def buttons(data):
    """Кнопки в порядке слотов, без рамки и без служебных."""
    out = []
    for key, item in (data.get('items') or {}).items():
        if key.startswith('frame_'):
            continue
        slot = item.get('slot', 999)
        out.append((slot, key, item))
    out.sort()
    return out


def actions(item):
    """Что кнопка делает — человеческим языком."""
    acts = []
    for side, label in (('left_click_commands', ''), ('right_click_commands', 'ПКМ: ')):
        for line in item.get(side) or []:
            line = str(line).strip()
            if line.startswith('[openguimenu]'):
                acts.append(label + '→ ' + line.split(']', 1)[1].strip())
            elif line.startswith('[player]'):
                acts.append(label + '`/' + line.split(']', 1)[1].strip() + '`')
            elif line.startswith('[console]'):
                acts.append(label + 'консоль: `' + line.split(']', 1)[1].strip() + '`')
            elif line.startswith('[message]'):
                acts.append(label + 'текст в чат')
            elif line.startswith('[close]'):
                pass
    # «текст в чат» повторяется столько раз, сколько строк в сообщении
    seen, uniq = set(), []
    for a in acts:
        if a not in seen:
            seen.add(a)
            uniq.append(a)
    return uniq


def build():
    by_id, by_file = load()

    # кто кого открывает
    children = {}
    has_parent = set()
    for menu_id, (_, data) in by_id.items():
        for _, _, item in buttons(data):
            for side in ('left_click_commands', 'right_click_commands'):
                for line in item.get(side) or []:
                    line = str(line).strip()
                    if line.startswith('[openguimenu]'):
                        target = line.split(']', 1)[1].strip()
                        if target in by_id and target != menu_id:
                            children.setdefault(menu_id, [])
                            if target not in children[menu_id]:
                                children[menu_id].append(target)
                            has_parent.add(target)

    total_buttons = sum(len(buttons(d)) for _, d in by_id.values())

    lines = [
        '# Карта меню EKB SHIELD',
        '',
        '⚠️ ФАЙЛ СОБИРАЕТСЯ ГЕНЕРАТОРОМ — `py -3 build_menu_map.py`.',
        'Руками не править: карта правилась вручную и поэтому врала',
        '(стояло 32 меню и 360 кнопок, когда в игре было 40 и 430).',
        '',
        '- меню: **%d**, кнопок: **%d**' % (len(by_id), total_buttons),
        '- правка меню: `menus_spec.py` → `py -3 build_menus.py --install` → `/dm reload`',
        '- проверка: `py -3 check_menus.py`',
        '',
        'В квадратных скобках — право, без которого раздел не виден.',
        '',
        '## Дерево',
        '',
        '```',
    ]

    # ⚠️ Родитель выбирается обходом В ШИРИНУ от главного меню, а не первой
    # попавшейся ссылкой. При обходе в глубину «Служба» уезжала на шестой
    # уровень (Профиль → Личина → Теневой Рынок → Тёмное ремесло → Служба),
    # потому что туда первой дотянулась кнопка из Личины, — а следом обрезание
    # по глубине выбрасывало все админские подменю в «сюда никто не ведёт».
    # Ближайший путь от /menu — это и есть то, как игрок туда доходит.
    order = []
    parent = {}
    queue = ['ekb_main'] if 'ekb_main' in by_id else []
    seen_bfs = set(queue)
    while queue:
        cur = queue.pop(0)
        order.append(cur)
        for kid in children.get(cur, []):
            if kid not in seen_bfs:
                seen_bfs.add(kid)
                parent[kid] = cur
                queue.append(kid)
    tree = {}
    for kid, par in parent.items():
        tree.setdefault(par, []).append(kid)

    def title_of(menu_id):
        _, data = by_id[menu_id]
        name = plain(data.get('menu_title', menu_id))
        cmds = ' '.join('/' + c for c in commands(data))
        perm = permission(data)
        row = name
        if cmds:
            row += '   ' + cmds
        if perm:
            row += '   [%s]' % perm
        return row

    drawn = set()

    def draw(menu_id, prefix, last, depth):
        mark = '└─ ' if last else '├─ '
        lines.append(prefix + (mark if depth else '') + title_of(menu_id))
        drawn.add(menu_id)
        kids = tree.get(menu_id, [])
        step = ('   ' if last else '│  ') if depth else ''
        for i, kid in enumerate(kids):
            draw(kid, prefix + step, i == len(kids) - 1, depth + 1)

    if 'ekb_main' in by_id:
        draw('ekb_main', '', True, 0)

    orphans = [m for m in sorted(by_id) if m not in drawn]
    if orphans:
        lines.append('')
        lines.append('# от /menu сюда не дойти — только своей командой:')
        for m in orphans:
            lines.append('  ' + title_of(m))
    lines.append('```')
    lines.append('')
    lines.append('## Что внутри каждого меню')

    for menu_id in sorted(by_id, key=lambda m: plain(by_id[m][1].get('menu_title', m))):
        fname, data = by_id[menu_id]
        btns = buttons(data)
        perm = permission(data)
        cmds = ', '.join('`/%s`' % c for c in commands(data))
        lines.append('')
        lines.append('### %s' % plain(data.get('menu_title', menu_id)))
        meta = '*`%s` · %d кнопок' % (fname, len(btns))
        if cmds:
            meta += ' · ' + cmds
        if perm:
            meta += ' · право `%s`' % perm
        lines.append(meta + '*')
        lines.append('')
        for _, _, item in btns:
            name = plain(item.get('display_name', '?'))
            acts = actions(item)
            row = '- **%s**' % name
            if acts:
                row += ' — ' + ', '.join(acts)
            view = (item.get('view_requirement') or {}).get('requirements') or {}
            for v in view.values():
                if v.get('permission'):
                    row += '  `[%s]`' % v['permission']
            lines.append(row)

    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    text = build()
    if '--check' in sys.argv:
        current = io.open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        if current == text:
            print('docs/menu_map.md свежий')
            sys.exit(0)
        print('docs/menu_map.md устарел — пересобери: py -3 build_menu_map.py')
        sys.exit(1)
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(text)
    print('docs/menu_map.md пересобран: %d строк' % text.count('\n'))
