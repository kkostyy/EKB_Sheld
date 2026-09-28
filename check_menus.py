# -*- coding: utf-8 -*-
"""EKB SHIELD — проверка меню DeluxeMenus.

Смотрит на каждое меню и отвечает на шесть вопросов:
  1. существуют ли команды, которые вызывают кнопки;
  2. не ведёт ли кнопка в несуществующее меню;
  3. не конфликтуют ли слоты и не потерялся ли заголовок;
  4. делает ли кнопка хоть что-нибудь;
  5. не повторяет ли одно и то же действие в трёх и более меню;
  6. есть ли в ресурспаке модель под `model_data` кнопки.

Команды собираются из plugin.yml всех плагинов сервера, из Skript-скриптов
и из списка ванильных — то есть проверка идёт по факту, а не по памяти.

Запуск: py -3 check_menus.py
"""
import io
import json
import os
import re
import zipfile
from collections import defaultdict

import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(ROOT, 'server')
MENUS = os.path.join(ROOT, 'plugins', 'DeluxeMenus', 'gui_menus')
CONFIG = os.path.join(ROOT, 'plugins', 'DeluxeMenus', 'config.yml')
SCRIPTS = os.path.join(SERVER, 'plugins', 'Skript', 'scripts')
PACK_ITEMS = os.path.join(ROOT, 'resourcepack', 'assets', 'minecraft', 'items')

VANILLA = {
    'list', 'help', 'me', 'msg', 'tell', 'w', 'say', 'seed', 'weather', 'time',
    'save-all', 'function', 'tp', 'teleport', 'gamemode', 'kill', 'give',
    'spawnpoint', 'trigger', 'execute',
}

# Команды, которые плагин регистрирует кодом, а не в манифесте: в jar их
# не найти, поэтому перечислены явно. Каждая проверена на живом сервере.
CODE_REGISTERED = {
    'spark',                      # spark
    'skins', 'skin', 'sr',        # SkinsRestorer
    'headdb', 'hdb',              # HeadDB
    'g', 'l', 'local', 'global',  # каналы CarbonChat
    'staff', 'sap', 'carbon',
    'shopkeeper', 'shopkeepers',  # Shopkeepers
    'report', 'reports', 'myreports', 'bugreport',  # AdvancedReports
    'clan', 'clans', 'cl', 'cc', 'clanchat', 'topclans',  # ClansLite
    'co', 'coreprotect', 'core',  # CoreProtect
    'lp', 'luckperms', 'perm',    # LuckPerms
    'dm', 'deluxemenus',          # DeluxeMenus
    'sv', 'vanish',               # SuperVanish
    # ⚠ Аддоны Plasmo Voice регистрируют команды через API самого PV,
    # а не через plugin.yml — в jar'е их не найти, отсюда ручной список.
    'groups', 'vbroadcast',       # pv-addon-groups, pv-addon-broadcast
    'vm', 'vm-actions',           # pv-addon-voice-messages (голосовые в чат)
    'oi', 'openinv', 'oe', 'openender',
    'brew', 'breweryx',           # BreweryX
    'tab',                        # TAB
    'chunky', 'sk', 'skript', 'papi', 'placeholderapi',
    'ignore', 'unignore', 'mail',  # EssentialsX
    'qa', 'qualityarmory',        # QualityArmory
    'imageframe', 'iframe', 'frame',  # ImageFrame
    'gimme', 'treload',           # TablePlays
}


def plugin_commands():
    """Команды всех плагинов: и bukkit-, и paper-манифесты."""
    found = set()
    plug = os.path.join(SERVER, 'plugins')
    if not os.path.isdir(plug):
        return found
    for name in os.listdir(plug):
        if not name.endswith('.jar'):
            continue
        try:
            z = zipfile.ZipFile(os.path.join(plug, name))
        except Exception:
            continue
        for manifest in ('plugin.yml', 'paper-plugin.yml'):
            try:
                data = yaml.safe_load(z.read(manifest).decode('utf-8', 'replace'))
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            for cmd, body in (data.get('commands') or {}).items():
                found.add(str(cmd).lower())
                if isinstance(body, dict):
                    for alias in (body.get('aliases') or []):
                        found.add(str(alias).lower())
    return found


def skript_commands():
    """Команды из .sk: и сама команда, и её aliases."""
    found = set()
    if not os.path.isdir(SCRIPTS):
        return found
    for name in sorted(os.listdir(SCRIPTS)):
        if not name.endswith('.sk'):
            continue
        text = io.open(os.path.join(SCRIPTS, name), encoding='utf-8').read()
        # ⚠️ Двоеточие обязательно отрезать. У команды без аргументов строка
        # выглядит как `command /treasury:`, и `\S+` утаскивает двоеточие
        # в имя — команда считалась несуществующей, хотя она есть.
        # У команды с аргументом (`command /skupka [<text>]:`) этого не видно,
        # поэтому ошибка всплывает только на части команд.
        for cmd in re.findall(r'(?m)^command\s+/(\S+)', text):
            found.add(cmd.rstrip(':').lower())
        for line in re.findall(r'(?m)^\s+aliases:\s*(.+)$', text):
            for alias in line.split(','):
                found.add(alias.strip().lstrip('/').lower())
    return found


def _cmd_thresholds(node, out):
    """Пороги всех `range_dispatch` по custom_model_data внутри определения.

    Только по `custom_model_data`: у компаса и часов в ванильном fallback свой
    `range_dispatch` (`minecraft:compass`, `minecraft:time`) с порогами 0…63 —
    та же грабля, что уже ловил `build_3d_models.py`.
    """
    if isinstance(node, dict):
        if str(node.get('type', '')).endswith('range_dispatch')                 and str(node.get('property', '')).endswith('custom_model_data'):
            for e in node.get('entries') or []:
                if 'threshold' in e:
                    out.add(int(e['threshold']))
        for v in node.values():
            _cmd_thresholds(v, out)
    elif isinstance(node, list):
        for v in node:
            _cmd_thresholds(v, out)


def pack_models():
    """Материал -> множество CMD, под которые в ресурспаке есть модель."""
    found = {}
    if not os.path.isdir(PACK_ITEMS):
        return found
    for name in os.listdir(PACK_ITEMS):
        if not name.endswith('.json'):
            continue
        try:
            data = json.load(io.open(os.path.join(PACK_ITEMS, name), encoding='utf-8'))
        except ValueError:
            continue
        out = set()
        _cmd_thresholds(data, out)
        found[name[:-5]] = out
    return found


def cmd_issues(buttons, models):
    """Кнопка с `model_data`, под который в паке нет модели.

    DeluxeMenus ставит номер молча, клиент так же молча рисует ванильный
    предмет — опечатка в номере выглядит как «иконка просто обычная», и
    никто её не ищет. Сверяется ТОЧНОЕ совпадение с порогом: `range_dispatch`
    выбрал бы ближайший порог снизу, то есть чужую модель, а это та же
    ошибка, только хуже заметная. Головы (`basehead-`, `head-`, `hdb-`)
    пропускаются — модель у них не из пака.
    """
    issues = []
    for key, body in buttons.items():
        cmd = body.get('model_data')
        if cmd is None:
            continue
        mat = str(body.get('material', '')).lower()
        if '-' in mat:
            continue
        mat = mat.split(':', 1)[-1]
        have = models.get(mat)
        if have is None:
            issues.append('%s: model_data %s, но у %s в паке нет определения '
                          'с custom_model_data' % (key, cmd, mat))
        elif int(cmd) not in have:
            issues.append('%s: model_data %s — у %s в паке такой модели нет'
                          % (key, cmd, mat))
    return issues


def main():
    known_cmds = plugin_commands() | skript_commands() | VANILLA | CODE_REGISTERED
    cfg = yaml.safe_load(io.open(CONFIG, encoding='utf-8'))
    models = pack_models()
    known_menus = set(cfg['gui_menus'])
    registered = {v['file'] for v in cfg['gui_menus'].values()}

    problems = 0
    total_buttons = 0
    print('меню в реестре: %d' % len(known_menus))

    for name in sorted(os.listdir(MENUS)):
        if not name.endswith('.yml'):
            continue
        path = os.path.join(MENUS, name)
        text = io.open(path, encoding='utf-8').read()
        data = yaml.safe_load(text)
        items = data.get('items') or {}
        buttons = {k: v for k, v in items.items() if not k.startswith('frame_')}
        total_buttons += len(buttons)
        issues = []

        if name not in registered:
            issues.append('файл не подключён в config.yml')

        slots = {}
        for key, body in items.items():
            slot = body.get('slot')
            if slot is None:
                issues.append('%s: нет слота' % key)
            elif slot in slots:
                issues.append('%s и %s делят слот %s' % (key, slots[slot], slot))
            else:
                slots[slot] = key
            if slot is not None and not (0 <= slot < data.get('size', 54)):
                issues.append('%s: слот %s вне окна' % (key, slot))

        for target in re.findall(r"\[openguimenu\] ([^'\s]+)", text):
            if target not in known_menus:
                issues.append('ведёт в несуществующее меню: %s' % target)

        for cmd in re.findall(r"\[player\] (\S+)", text):
            # Тег задержки DeluxeMenus идёт вплотную к команде (`roulette<delay=2>`).
            base = re.sub(r'<delay=\d+>', '', cmd.strip("'")).lower()
            if base not in known_cmds:
                issues.append('команда не найдена: /%s' % base)

        # Кнопка обязана что-то делать. Правило проекта: «кнопка либо
        # что-то делает, либо её нет». В ручных меню так набралось десять
        # кнопок-картинок (три в capital.yml, семь в town_gov.yml) —
        # раздел выглядел рабочим, а был лором. Найдено 18.09.2026.
        for key, body in buttons.items():
            # header, back и close — служебные: заголовок по определению
            # не кликается, а «Назад» и «Закрыть» ставит сам генератор.
            if key in ('header', 'back', 'close'):
                continue
            acts = (body.get('left_click_commands') or []) \
                + (body.get('right_click_commands') or [])
            meaningful = [a for a in acts if str(a).strip() != '[close]']
            if not meaningful and not body.get('lore'):
                issues.append('%s: кнопка ничего не делает и ничего не поясняет' % key)

        issues += cmd_issues(buttons, models)

        mark = 'ok ' if not issues else 'ПРОБЛЕМЫ'
        print('%-8s %-18s кнопок %2d' % (mark, name, len(buttons)))
        for i in issues:
            print('          → %s' % i)
            problems += 1

    problems += reachability(cfg)
    problems += cross_checks(cfg)
    duplicate_checks()
    print('\nвсего кнопок: %d, проблем: %d' % (total_buttons, problems))


def reachability(cfg):
    """До каждого меню можно дойти кликами от /menu.

    28.09.2026 пять новых разделов собрались, но кнопка-вход в них
    потерялась (вставка шла в старый список) — меню было, а попасть в него
    было нельзя. Со стороны это выглядит как «раздела нет», и искать его
    не станет никто.
    """
    links = {}
    for key, body in cfg['gui_menus'].items():
        text = io.open(os.path.join(MENUS, body['file']), encoding='utf-8').read()
        links[key] = set(re.findall(r"\[openguimenu\] ([^'\s]+)", text))
    seen, queue = {'ekb_main'}, ['ekb_main']
    while queue:
        for n in links.get(queue.pop(), ()):
            if n not in seen:
                seen.add(n)
                queue.append(n)
    lost = sorted(set(links) - seen)
    print('\n--- достижимость от /menu ---')
    for m in lost:
        print('ПРОБЛЕМА %s: ни одна кнопка сюда не ведёт' % m)
    if not lost:
        print('ok  все %d меню достижимы' % len(links))
    return len(lost)


def duplicate_checks():
    """Одно и то же действие в разных меню.

    Не ошибка сама по себе: законы и «Вызвать службу» намеренно доступны из
    нескольких ролевых меню — это точки входа, а не мусор. Ошибка — когда
    целое меню повторяет другое. Так в проекте жили bar.yml и herbs.yml:
    18 и 16 кнопок из 31, дословно совпадавших с allitems.yml, плюс
    contracts.yml, повторённый в assassin.yml. Убрано 18.09.2026.

    Порог в три меню подобран так, чтобы законы и заявки не шумели,
    а новый полноценный дубль — бросался в глаза.
    """
    by_action = defaultdict(list)
    for name in sorted(os.listdir(MENUS)):
        if not name.endswith('.yml'):
            continue
        d = yaml.safe_load(io.open(os.path.join(MENUS, name), encoding='utf-8'))
        for key, body in (d.get('items') or {}).items():
            if key.startswith('frame_') or key in ('back', 'close', 'header'):
                continue
            acts = tuple(str(a)
                         for side in ('left_click_commands', 'right_click_commands')
                         for a in (body.get(side) or []))
            if acts:
                by_action[acts].append(name)

    print('\n--- одно действие в трёх и более меню ---')
    noisy = 0
    for acts, files in sorted(by_action.items(), key=lambda x: -len(set(x[1]))):
        uniq = sorted(set(files))
        if len(uniq) >= 3:
            noisy += 1
            print('    %-46s %s' % (' | '.join(acts)[:46], ', '.join(uniq)))
    if not noisy:
        print('ok  ни одно действие не повторяется в трёх и более меню')


def cross_checks(cfg):
    """Две ловушки, которых не видно внутри одного файла меню.

    1. Команды открытия меню DeluxeMenus НЕ попадают в карту команд Bukkit:
       плагин ловит их в PlayerCommandPreprocessEvent, то есть только когда
       игрок печатает их в чате. Skript-эффект `make player execute command`
       идёт через Bukkit.dispatchCommand, чата не касается — и такой переход
       в меню молча не срабатывает. Открывать меню из Skript надо через
       `make player say "/menu"`: это настоящий ввод в чат.
    2. Голая команда открытия перехватывает одноимённую настоящую команду.
       DeluxeMenus сверяет строку целиком, поэтому `/call medic` проходит
       дальше к Skript, а голый `/call` — уже нет.
    """
    bad = 0
    opens = {}
    for key, body in cfg['gui_menus'].items():
        d = yaml.safe_load(io.open(os.path.join(MENUS, body['file']), encoding='utf-8'))
        oc = d.get('open_command')
        for c in (oc if isinstance(oc, list) else [oc] if oc else []):
            opens[str(c).lower()] = body['file']

    print('\n--- переходы в меню из Skript ---')
    names = sorted(os.listdir(SCRIPTS)) if os.path.isdir(SCRIPTS) else []
    for name in names:
        if not name.endswith('.sk'):
            continue
        text = io.open(os.path.join(SCRIPTS, name), encoding='utf-8').read()
        for line in re.findall(r'execute command "([^"]+)"', text):
            first = line.split()[0].lower()
            if first in opens:
                print('ПРОБЛЕМА %s: dispatch "/%s" не откроет %s — нужно '
                      'make player say "/%s"' % (name, first, opens[first], first))
                bad += 1
    if not bad:
        print('ok  ни один скрипт не открывает меню через dispatchCommand')

    print('\n--- команда открытия поверх настоящей команды ---')
    shadow = sorted(set(opens) & (plugin_commands() | skript_commands()))
    for c in shadow:
        print('    /%-12s голый вызов откроет %s, а не исходную команду'
              % (c, opens[c]))
    if not shadow:
        print('ok  пересечений нет')
    return bad


if __name__ == '__main__':
    main()
