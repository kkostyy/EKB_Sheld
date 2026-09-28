# -*- coding: utf-8 -*-
"""EKB SHIELD — глубокая проверка кнопок меню: сработает ли клик на деле.

check_menus.py отвечает «существует ли команда». Этого мало: кнопка может
вызывать существующую команду и всё равно «ничего не делать». Здесь каждая
кнопка (ЛКМ и ПКМ) проверяется на пять причин молчаливого провала:

  1. подкоманда, которой скрипт не знает (`/contract xyz`) — Skript уходит
     в ветку «неизвестное действие» или просто ничего не печатает;
  2. не хватает обязательного аргумента — Skript молча показывает usage;
  3. кнопку видит тот, у кого нет права на саму команду;
  4. действие мастера `ekbdo` не зарегистрировано в реестре menu_wizard.sk;
  5. `[player] <команда открытия меню>` — DeluxeMenus ловит их только из
     чата, performCommand мимо проходит.

Права берутся из ЖИВОГО LuckPerms: сначала `lp export ekbaudit` по RCON,
потом файл читается сам. Кто видит кнопку, решается по её view_requirement и
open_requirement меню: право из требования -> группы, где оно есть.

Запуск: py -3 audit_menus.py [путь к lp-экспорту .json]
"""
import glob
import gzip
import io
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from collections import defaultdict

import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(ROOT, 'server')
MENUS = os.path.join(SERVER, 'plugins', 'DeluxeMenus', 'gui_menus')
SCRIPTS = os.path.join(SERVER, 'plugins', 'Skript', 'scripts')

sys.path.insert(0, ROOT)
from check_menus import CODE_REGISTERED, VANILLA  # noqa: E402


# ---------------------------------------------------------------------------
# LuckPerms
# ---------------------------------------------------------------------------

def lp_export():
    if len(sys.argv) > 1:
        return json.load(io.open(sys.argv[1], encoding='utf-8'))
    tmp = os.path.join(os.environ.get('TEMP', '.'), 'ekb_audit_cmd.txt')
    io.open(tmp, 'w', encoding='utf-8').write('lp export ekbaudit\n')
    subprocess.run([sys.executable, os.path.join(ROOT, 'rcon.py'), '--file', tmp],
                   capture_output=True)
    f = os.path.join(SERVER, 'plugins', 'LuckPerms', 'ekbaudit.json.gz')
    for _ in range(30):
        if os.path.exists(f):
            break
        time.sleep(1)
    time.sleep(1)
    data = json.load(gzip.open(f, 'rt', encoding='utf-8'))
    os.remove(f)
    return data


def group_nodes(lp):
    """группа -> {нода: bool}, с наследованием (родитель слабее)."""
    raw = {}
    parents = {}
    for g, body in lp['groups'].items():
        nodes = {}
        par = []
        for n in body['nodes']:
            k = n['key']
            if n.get('context'):
                continue
            if k.startswith('group.'):
                par.append(k[6:])
            neg = k.startswith('-')
            nodes[k.lstrip('-').lower()] = (not neg) and n.get('value', True)
        raw[g] = nodes
        parents[g] = par
    weight = {g: int(next((k.split('.')[1] for k in raw[g] if k.startswith('weight.')), 0))
              for g in raw}

    def full(g, seen=()):
        out = {}
        for p in sorted(parents[g], key=lambda x: weight.get(x, 0)):
            if p in raw and p not in seen:
                out.update(full(p, seen + (g,)))
        out.update(raw[g])
        return out
    return {g: full(g) for g in raw}, weight


def viewer_perms(groups, weight, view_perms):
    """Права «типичного зрителя» кнопки: default + nomad + группы с правом.

    Группы накладываются по весу (тяжелее — поверх), как решает LuckPerms
    для унаследованных нод.
    """
    use = ['default', 'nomad']
    for vp in view_perms:
        for g, nodes in groups.items():
            if nodes.get(vp.lower()) is True or nodes.get('*') is True:
                if g not in use:
                    use.append(g)
    out = {}
    for g in sorted(use, key=lambda x: weight.get(x, 0)):
        out.update(groups.get(g, {}))
    for vp in view_perms:          # раз видит кнопку — право у него точно есть
        out.setdefault(vp.lower(), True)
    return out, use


def has(perms, node, plugin_default=None):
    node = node.lower()
    if node in perms:
        return perms[node]
    parts = node.split('.')
    for i in range(len(parts) - 1, 0, -1):
        wc = '.'.join(parts[:i]) + '.*'
        if wc in perms:
            return perms[wc]
    if '*' in perms:
        return perms['*']
    if plugin_default is True or plugin_default == 'true':
        return True
    return False


# ---------------------------------------------------------------------------
# Команды
# ---------------------------------------------------------------------------

def plugin_manifest():
    """команда -> (право или None, default этого права)."""
    cmds = {}
    perm_default = {}
    plug = os.path.join(SERVER, 'plugins')
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
            for p, body in (data.get('permissions') or {}).items():
                if isinstance(body, dict):
                    perm_default[str(p).lower()] = body.get('default', 'op')
            for c, body in (data.get('commands') or {}).items():
                body = body if isinstance(body, dict) else {}
                entry = (body.get('permission'), name)
                cmds[str(c).lower()] = entry
                for a in body.get('aliases') or []:
                    cmds[str(a).lower()] = entry
    return cmds, perm_default


def skript_manifest():
    """команда -> dict(perm, mandatory, subs, file, players_only)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(SCRIPTS, '*.sk'))):
        text = io.open(path, encoding='utf-8').read()
        om = re.search(r'(?ms)^options:\n(.*?)(?=^\S)', text)
        opts = dict(re.findall(r'(?m)^\s+(\w+):\s*(.*?)\s*(?:#.*)?$', om.group(1))) if om else {}
        blocks = re.split(r'(?m)^(?=\S)', text)
        for b in blocks:
            m = re.match(r'command\s+/(\S+?)((?:\s+[^:\n]*)?):', b)
            if not m:
                continue
            name = m.group(1).lower()
            sig = m.group(2) or ''
            # обязательные аргументы — <...> вне [...]
            depth, mand = 0, 0
            for tok in re.findall(r'\[|\]|<[^>]+>', sig):
                if tok == '[':
                    depth += 1
                elif tok == ']':
                    depth -= 1
                elif depth == 0:
                    mand += 1
            perm = re.search(r'(?m)^\s+permission:\s*(.+?)\s*$', b)
            perm = perm.group(1) if perm else None
            if perm:
                perm = re.sub(r'\{@(\w+)\}', lambda x: opts.get(x.group(1), x.group(0)), perm)
            # подкоманды: сравнения первого аргумента со строкой
            first_vars = set(re.findall(r'set (\{_\w+\}) to arg(?:ument)?[- ]1\b', b))
            subs = set(re.findall(r'arg(?:ument)?[- ]1 is "([^"]+)"', b))
            for v in first_vars:
                subs |= set(re.findall(re.escape(v) + r' is "([^"]+)"', b))
            info = dict(perm=perm, mandatory=mand, subs={s.lower() for s in subs},
                        file=os.path.basename(path), sig=sig.strip())
            out[name] = info
            al = re.search(r'(?m)^\s+aliases:\s*(.+)$', b)
            if al:
                for a in al.group(1).split(','):
                    out[a.strip().lstrip('/').lower()] = info
    return out


# Команды, у которых первый аргумент — ДАННЫЕ, а не подкоманда: сравнение
# со строкой в них есть (`/call take`), но остальные значения тоже законны
# (`/call medic` — тип вызова, проверяется функцией call_perm), а
# `/voicezone` без add/del по любому слову печатает список.
FREE_FIRST_ARG = {'call', 'voicezone'}


def wizard_registry():
    text = io.open(os.path.join(SCRIPTS, 'menu_wizard.sk'), encoding='utf-8').read()
    reg = {}
    for m in re.finditer(r'wz_new\("([^"]+)",\s*"[^"]*",\s*[^,]+,\s*"([^"]*)"', text):
        reg[m.group(1).lower()] = m.group(2) or None
    return reg


def dm_open_commands():
    opens = {}
    for f in glob.glob(os.path.join(MENUS, '*.yml')):
        d = yaml.safe_load(io.open(f, encoding='utf-8')) or {}
        oc = d.get('open_command')
        for c in (oc if isinstance(oc, list) else [oc] if oc else []):
            opens[str(c).lower()] = os.path.basename(f)
    return opens


def req_perms(req):
    """(права, нужно_все): DeluxeMenus складывает требования по И, если не
    задан minimum_requirements (тогда — «хотя бы N»)."""
    out = []
    if not isinstance(req, dict):
        return out, True
    for r in (req.get('requirements') or {}).values():
        if isinstance(r, dict) and 'permission' in str(r.get('type', '')).lower():
            out.append(str(r.get('permission')))
    return out, not req.get('minimum_requirements')


def sees(nodes, need):
    """Проходит ли группа все наборы требований (меню и кнопки)."""
    for perms, all_ in need:
        if not perms:
            continue
        ok = [nodes.get(p.lower()) is True for p in perms]
        if (all_ and not all(ok)) or (not all_ and not any(ok)):
            return False
    return True


# ---------------------------------------------------------------------------

def main():
    lp = lp_export()
    groups, weight = group_nodes(lp)
    pcmds, pdefaults = plugin_manifest()
    scmds = skript_manifest()
    wiz = wizard_registry()
    opens = dm_open_commands()
    known = set(pcmds) | set(scmds) | VANILLA | CODE_REGISTERED

    found = defaultdict(list)
    buttons = 0
    for f in sorted(glob.glob(os.path.join(MENUS, '*.yml'))):
        menu = os.path.basename(f)[:-4]
        d = yaml.safe_load(io.open(f, encoding='utf-8')) or {}
        menu_req = req_perms(d.get('open_requirement'))
        for key, it in (d.get('items') or {}).items():
            if key.startswith('frame_') or key in ('header', 'back', 'close'):
                continue
            need = [menu_req, req_perms(it.get('view_requirement'))]
            view = need[0][0] + need[1][0]
            # Каждая роль, которая видит кнопку, проверяется ОТДЕЛЬНО: общий
            # набор прятал бы судью за правами админа (у admin `*`).
            viewers = []
            if not view:
                viewers.append(viewer_perms(groups, weight, []))
            else:
                for g, nodes in groups.items():
                    if g in ('admin',) or nodes.get('*') is True:
                        continue
                    eff0 = {}
                    for gg in sorted(['default', 'nomad', g], key=lambda x: weight.get(x, 0)):
                        eff0.update(groups.get(gg, {}))
                    if sees(eff0, need):
                        eff = {}
                        for gg in sorted(['default', 'nomad', g], key=lambda x: weight.get(x, 0)):
                            eff.update(groups.get(gg, {}))
                        viewers.append((eff, [g]))
                if not viewers:          # видит только админ — у него `*`
                    continue
            for perms, who in viewers:
             for side, label in (('left_click_commands', 'ЛКМ'), ('right_click_commands', 'ПКМ')):
                for act in it.get(side) or []:
                    act = re.sub(r'\s*<delay=\d+>', '', str(act))
                    m = re.match(r'\[player\]\s+(.+)', act)
                    if not m:
                        continue
                    buttons += 1
                    where = '%s.%s %s' % (menu, key, label)
                    line = m.group(1).strip()
                    parts = line.split()
                    cmd, args = parts[0].lower(), parts[1:]
                    viewer = '/'.join(w for w in who if w not in ('default', 'nomad')) or 'обычный игрок'

                    if cmd in opens and not args:
                        found['5. команда открытия меню через [player]'].append(
                            '%s: /%s — нужно [openguimenu]' % (where, cmd))
                        continue
                    if cmd not in known:
                        found['0. команды нет вовсе'].append('%s: /%s' % (where, line))
                        continue

                    if cmd == 'ekbdo':
                        act_id = (args[0].lower() if args else '')
                        if act_id not in wiz:
                            found['4. действия нет в реестре ekbdo'].append('%s: ekbdo %s' % (where, act_id))
                        elif wiz[act_id] and not has(perms, wiz[act_id], pdefaults.get(wiz[act_id].lower())):
                            found['3. видит без права'].append(
                                '%s: ekbdo %s требует %s, видит %s' % (where, act_id, wiz[act_id], viewer))
                        continue

                    if cmd in scmds:
                        s = scmds[cmd]
                        if len(args) < s['mandatory']:
                            found['2. не хватает аргументов'].append(
                                '%s: /%s — нужно %s' % (where, line, s['sig']))
                        if s['subs'] and cmd not in FREE_FIRST_ARG and args and args[0].lower() not in s['subs'] \
                                and not args[0].startswith('%'):
                            found['1. неизвестная подкоманда'].append(
                                '%s: /%s — %s знает: %s' % (where, line, s['file'],
                                                          ', '.join(sorted(s['subs']))[:120]))
                        if s['perm'] and not has(perms, s['perm'], pdefaults.get(s['perm'].lower())):
                            found['3. видит без права'].append(
                                '%s: /%s требует %s, видит %s' % (where, cmd, s['perm'], viewer))
                        continue

                    if cmd in pcmds and pcmds[cmd][0]:
                        p = str(pcmds[cmd][0])
                        if not has(perms, p, pdefaults.get(p.lower())):
                            found['3. видит без права'].append(
                                '%s: /%s (%s) требует %s, видит %s'
                                % (where, cmd, pcmds[cmd][1], p, viewer))

    print('проверено действий [player]: %d' % buttons)
    total = 0
    for cat in sorted(found):
        print('\n--- %s: %d ---' % (cat, len(found[cat])))
        for row in found[cat]:
            print('   ' + row)
        total += len(found[cat])
    if not total:
        print('ok  проблем не найдено')
    print('\nвсего находок: %d' % total)


if __name__ == '__main__':
    main()
