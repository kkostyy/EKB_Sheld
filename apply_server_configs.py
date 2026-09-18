# -*- coding: utf-8 -*-
"""EKB SHIELD — накат патчей config/purpur.yml и config/spigot.yml на сервер.

Зачем отдельный скрипт, а не обычное копирование.

    purpur.yml и spigot.yml лежат в КОРНЕ сервера, а не в config/ — там
    только paper-global.yml и paper-world-defaults.yml. setup.sh и setup.ps1
    копировали весь config/* в $SERVER_DIR/config/, поэтому два из четырёх
    файлов уезжали в папку, куда Purpur и Spigot вообще не смотрят. Внешне
    всё выглядело установленным: файл на месте, значения правильные, —
    а на сервере три года стояли дефолты. Найдено 18.09.2026.

    Просто скопировать их в корень тоже нельзя: в репозитории лежит патч на
    несколько ключей, а на сервере — сгенерированный файл на две тысячи строк
    с комментариями и всеми остальными настройками. Копия затёрла бы их.

    Поэтому скрипт правит значения ПО МЕСТУ: находит ключ по пути и
    переписывает одну строку, не трогая ни комментарии, ни порядок, ни
    соседние ключи.

Запуск:
    py -3 apply_server_configs.py            # показать, что изменится
    py -3 apply_server_configs.py --write    # применить

Ключа, которого нет в файле сервера, скрипт НЕ добавляет, а ругается: почти
всегда это опечатка в пути или ключ, выброшенный из новой версии ядра, и
дописать его молча — значит завести ещё одну «включённую и не работающую»
настройку. Именно так в проекте жил settings.lobotomize-enabled, которого
у Purpur никогда не было.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(ROOT, 'server')

# репозиторный патч -> файл на сервере
PATCHES = [
    (os.path.join(ROOT, 'config', 'purpur.yml'), os.path.join(SERVER, 'purpur.yml')),
    (os.path.join(ROOT, 'config', 'spigot.yml'), os.path.join(SERVER, 'spigot.yml')),
]

# Эти двое, наоборот, лежат ИМЕННО в server/config/ и копируются как есть:
# Paper дочитывает недостающие ключи из своих дефолтов сам.
PAPER_FILES = ['paper-world-defaults.yml', 'paper-global.yml']


def flatten(node, prefix=''):
    """{'a': {'b': 1}} -> [('a.b', 1)]"""
    out = []
    for key, value in node.items():
        path = '%s.%s' % (prefix, key) if prefix else key
        if isinstance(value, dict):
            out += flatten(value, path)
        else:
            out.append((path, value))
    return out


def dump_scalar(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if value is None:
        return 'null'
    if isinstance(value, str):
        # Значения вроде ALTERNATE_CURRENT кавычек не требуют; строку с
        # пробелом или спецсимволом — закавычиваем.
        if re.fullmatch(r'[A-Za-z0-9_.:/-]+', value):
            return value
        return "'%s'" % value.replace("'", "''")
    return str(value)


def find_line(lines, path):
    """Номер строки с ключом по пути a.b.c, либо None.

    Идём сверху вниз: ищем каждое звено пути как ключ на СЛЕДУЮЩЕМ уровне
    отступа внутри блока, найденного на предыдущем шаге. Списки и многострочные
    значения не поддерживаются намеренно — в патчах проекта их нет, а
    угадывать их границы построчно значит рано или поздно испортить файл.
    """
    parts = path.split('.')
    start, end = 0, len(lines)
    parent_indent = -1

    for depth, part in enumerate(parts):
        last = depth == len(parts) - 1
        found = None
        indent = None
        for i in range(start, end):
            raw = lines[i]
            stripped = raw.strip()
            if not stripped or stripped.startswith('#'):
                continue
            cur = len(raw) - len(raw.lstrip())
            if cur <= parent_indent:
                break                      # блок родителя кончился
            if indent is None:
                indent = cur               # отступ этого уровня
            if cur != indent:
                continue                   # это глубже — не наш уровень
            m = re.match(r'([A-Za-z0-9_.\-]+)\s*:', stripped)
            if m and m.group(1) == part:
                found = i
                break
        if found is None:
            return None
        if last:
            return found
        # сужаем окно до тела найденного блока
        parent_indent = len(lines[found]) - len(lines[found].lstrip())
        start = found + 1
        new_end = end
        for i in range(start, end):
            raw = lines[i]
            if not raw.strip() or raw.strip().startswith('#'):
                continue
            if len(raw) - len(raw.lstrip()) <= parent_indent:
                new_end = i
                break
        end = new_end
    return None


def apply(patch_path, target_path, write):
    try:
        import yaml
    except ImportError:
        sys.exit('нужен PyYAML:  py -3 -m pip install pyyaml')

    if not os.path.exists(target_path):
        print('  ПРОПУСК: %s не существует — сервер ещё не запускался?'
              % os.path.relpath(target_path, ROOT))
        return 0, 0

    patch = yaml.safe_load(io.open(patch_path, encoding='utf-8')) or {}
    lines = io.open(target_path, encoding='utf-8').read().split('\n')

    changed = missing = 0
    for path, value in flatten(patch):
        i = find_line(lines, path)
        if i is None:
            print('  ! ключа нет в файле сервера: %s' % path)
            print('    сверь путь с живым %s — Purpur и Spigot неизвестные'
                  % os.path.basename(target_path))
            print('    ключи не создают и об этом не сообщают')
            missing += 1
            continue
        indent = ' ' * (len(lines[i]) - len(lines[i].lstrip()))
        key = lines[i].strip().split(':', 1)[0]
        old = lines[i].split(':', 1)[1].strip()
        new = dump_scalar(value)
        if old == new:
            continue
        lines[i] = '%s%s: %s' % (indent, key, new)
        print('  %-62s %s -> %s' % (path, old or '(пусто)', new))
        changed += 1

    if changed and write:
        io.open(target_path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    return changed, missing


def main():
    write = '--write' in sys.argv
    total_changed = total_missing = 0
    for patch_path, target_path in PATCHES:
        print('%s  ->  %s' % (os.path.relpath(patch_path, ROOT),
                              os.path.relpath(target_path, ROOT)))
        c, m = apply(patch_path, target_path, write)
        if not c and not m:
            print('  всё уже применено')
        total_changed += c
        total_missing += m
        print('')

    if total_missing:
        print('НЕ НАЙДЕНО КЛЮЧЕЙ: %d — это ошибка в патче, а не в сервере.'
              % total_missing)
    if total_changed and not write:
        print('Изменений: %d. Применить:  py -3 apply_server_configs.py --write'
              % total_changed)
    elif total_changed:
        print('Применено изменений: %d. Нужен перезапуск сервера.' % total_changed)
    return 1 if total_missing else 0


if __name__ == '__main__':
    sys.exit(main())
