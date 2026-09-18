# -*- coding: utf-8 -*-
"""EKB SHIELD — единый стиль диалоговых сообщений.

Сообщений в проекте больше двух тысяч: 25 Skript-файлов и 46 меню
DeluxeMenus. Разнобой в них не «некрасиво», а дорого: игрок опознаёт
источник сообщения по префиксу раньше, чем читает текст, и если Суд
пишет то с рамкой, то без, а Рынок — то с префиксом, то нет, чат
превращается в ленту без адресатов.

Правила, которые проверяются (они же — договор для новых скриптов):

  1. У каждого скрипта, который пишет игроку, в options есть `prefix`
     вида `&<цвет>&l[РАЗДЕЛ] &r`. Тематические добавки (`mark`, `vault`)
     — той же формы.
  2. Разделитель один на весь проект: `&8&m` и сорок дефисов
     (option `line` в admin_help.sk). Полосы из пробелов под `&m`
     в разных файлах получались разной длины и рвали рамку.
  3. Первая строка ответа несёт префикс. Продолжения (строки списка,
     подсказки, образцы команд) — без него и с отступом.
  4. Команда в тексте подсвечивается `&b`, пояснение — `&7`, тихая
     сноска — `&8`.

Запуск:
    py -3 check_messages.py          # отчёт
    py -3 check_messages.py --quiet  # только счётчик (для сборки)
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, 'docs')
MENUS = os.path.join(ROOT, 'plugins', 'DeluxeMenus', 'gui_menus')

PREFIX_RE = re.compile(r'^&[0-9a-f]&l\[[^\]]+\] &r$')
SEND_RE = re.compile(r'^(\s*)(?:send|broadcast)\s+"(.*)"(?:\s+to\s+.+)?$')
BAD_BAR_RE = re.compile(r'&8&m\s{2,}')
LINE_OPT = '&8&m----------------------------------------'

# Строки, которые намеренно живут без префикса: это не ответ команды,
# а кусок многострочного блока внутри рамки {@line}.
CONT_START = ('&7 ', '&8 ', '&8•', '&8 -', '&8  ', '&7  ', '  ')


def options_of(text):
    """options-блок скрипта: имя -> значение."""
    out = {}
    block = re.search(r'(?m)^options:\n((?:[ \t]+.+\n|\n)+)', text)
    if not block:
        return out
    for line in block.group(1).splitlines():
        m = re.match(r'\s+([a-z_]+):\s*(.*)$', line)
        if m:
            out[m.group(1)] = m.group(2).split('  #')[0].rstrip()
    return out


def check_script(path, problems):
    name = os.path.basename(path)
    text = io.open(path, encoding='utf-8').read()
    opts = options_of(text)
    lines = text.splitlines()

    writes = [l for l in lines if SEND_RE.match(l)]
    if writes and 'prefix' not in opts:
        problems.append((name, 0, 'нет option prefix, а сообщения есть'))

    for key in ('prefix', 'hunt', 'blade', 'clock', 'vault', 'mark', 'mask',
                'market'):
        val = opts.get(key)
        if val and not PREFIX_RE.match(val):
            problems.append((name, 0,
                             'префикс %s не в форме «&c&l[РАЗДЕЛ] &r»: %s'
                             % (key, val)))

    if 'line' in opts and opts['line'] != LINE_OPT:
        problems.append((name, 0, 'разделитель не совпадает с общим'))

    prev_send = False
    for n, raw in enumerate(lines, 1):
        if raw.lstrip().startswith('#'):
            continue
        m = SEND_RE.match(raw)
        if not m:
            # пустая строка и закрывающий блок не рвут цепочку ответа
            if raw.strip() and not raw.lstrip().startswith(('if ', 'else',
                                                            'loop ', 'set ',
                                                            'delete ')):
                prev_send = False
            continue
        body = m.group(2)

        if BAD_BAR_RE.search(body):
            problems.append((name, n, 'разделитель из пробелов — нужен {@line}'))

        to_console = ' to console' in raw
        if not to_console and not body.startswith('{@'):
            if not body.startswith(CONT_START) and not prev_send:
                problems.append((name, n,
                                 'ответ начинается без префикса: %s'
                                 % body[:58]))
        prev_send = True


def check_menu(path, problems):
    name = os.path.basename(path)
    for n, raw in enumerate(io.open(path, encoding='utf-8'), 1):
        m = re.search(r"\[message\]\s*(.*)$", raw.rstrip())
        if not m:
            continue
        body = m.group(1).strip().strip("'\"")
        if not body:
            continue
        if BAD_BAR_RE.search(body):
            problems.append((name, n, 'разделитель из пробелов'))
        # у кнопки образец команды печатается как «&<c>&lЗаголовок: &7/cmd»
        if body.startswith('/'):
            problems.append((name, n, 'команда без заголовка: %s' % body[:48]))


def main():
    problems = []
    for f in sorted(os.listdir(DOCS)):
        if f.endswith('.sk'):
            check_script(os.path.join(DOCS, f), problems)
    if os.path.isdir(MENUS):
        for f in sorted(os.listdir(MENUS)):
            if f.endswith('.yml'):
                check_menu(os.path.join(MENUS, f), problems)

    if '--quiet' not in sys.argv:
        for name, n, what in problems:
            where = '%s:%d' % (name, n) if n else name
            print('%-28s %s' % (where, what))
    print('проблем со стилем: %d' % len(problems))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
