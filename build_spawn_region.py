# -*- coding: utf-8 -*-
"""EKB SHIELD — генератор WorldGuard-региона привата Спавна.

Зачем генератор, а не «зайди и введи /rg define».

    /rg define требует выделения WorldEdit, а выделение есть только у игрока
    в мире. Из консоли и по RCON регион не создать вообще: у консоли нет
    ни позиции, ни мира. Поэтому регион пишется прямо в хранилище WorldGuard —
    plugins/WorldGuard/worlds/<мир>/regions.yml — а сервер подхватывает его
    командой /rg load.

Формат файла сверен по самому jar'у (worldguard-bukkit-7.0.18,
com/sk89q/worldguard/protection/managers/storage/file/YamlRegionFile):
ключи regions / type / min / max / priority / flags / owners / members,
вектор — вложенные x, y, z; StateFlag.unmarshal принимает 'allow' и 'deny'
без учёта регистра.

Запуск:
    py -3 build_spawn_region.py                    # собрать с параметрами по умолчанию
    py -3 build_spawn_region.py --radius 256       # другой радиус
    py -3 build_spawn_region.py --install          # и скопировать на сервер
    py -3 build_spawn_region.py --install --reload # и сказать серверу /rg load

После установки на работающем сервере:  /rg load  (или перезапуск).
Проверить:  /rg info spawn -w world

⚠️ Одновременно с этим в server.properties надо поставить spawn-protection=0.
Ванильная защита спавна закрывает 33x33 блока вокруг точки появления ВСЕМ,
кроме операторов, и она сильнее WorldGuard: Строительная бригада, добавленная
в members региона, всё равно не смогла бы там строить, а причину пришлось бы
искать в WorldGuard, где её нет.
"""
import argparse
import gzip
import io
import os
import shutil
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
WORLD = 'world'

# Центр мира EKB SHIELD — точка появления -1750 75 4000. Те же числа
# стоят в expand_border.ps1/.sh и в датапаке (там ещё и центр Ада = /8).
# Служат запасным вариантом: в свежем мире level.dat ещё держит 0,0, пока
# на сервере не выполнили /setworldspawn -1750 75 4000, и регион привата
# уехал бы в чистое поле за четыре с половиной тысячи блоков от Спавна.
CENTER = (-1750, 4000)
OUT = os.path.join(ROOT, 'plugins', 'WorldGuard', 'worlds', WORLD, 'regions.yml')
SERVER = os.path.join(ROOT, 'server', 'plugins', 'WorldGuard', 'worlds', WORLD, 'regions.yml')
LEVEL_DAT = os.path.join(ROOT, 'server', WORLD, 'level.dat')

# Высота региона. Приват Спавна идёт на всю высоту мира намеренно: иначе
# подкоп под базой САП и «крыша» над ней остаются вне защиты, а вся идея
# нейтральной зоны (Конституция 6.2) в том, что тронуть её нельзя ниоткуда.
MIN_Y, MAX_Y = -64, 319

# Флаги региона. Значение None означает «не трогать», такой флаг в файл
# не пишется и остаётся на усмотрение WorldGuard.
FLAGS = [
    # --- Конституция 6.2: полностью нейтральная безопасная зона ---
    #
    # ⚠️ pvp НАМЕРЕННО allow, а запрет ведёт docs/spawn_pvp.sk.
    #
    # Правило Главного города — «драться нельзя, КРОМЕ случая, когда на
    # жертву есть активный заказ». Флаг WorldGuard исключений не знает
    # вообще: `deny` отменяет урон безусловно и раньше любого скрипта, то
    # есть заказ в городе не сработал бы никогда. Поэтому зону держит
    # Skript — он единственный, кто видит доску контрактов.
    #
    # Вернёшь сюда 'deny' — PvP в городе закроется целиком, вместе с
    # исключением, и выглядеть это будет как сломавшийся скрипт.
    ('pvp', 'allow', 'запрет ведёт docs/spawn_pvp.sk — ему нужны исключения'),
    ('mob-damage', 'deny', 'мобы не бьют — зона безопасная и для беженцев (5.6)'),
    ('mob-spawning', 'deny', 'и не спавнятся: иначе «безопасная» держится на факелах'),

    # --- Застройка ---
    #
    # ⚠️ ЗДЕСЬ НАМЕРЕННО НЕТ ФЛАГА build (и block-break/block-place).
    #
    # Регион WorldGuard и так защищает себя: в границах региона строить
    # может только owner или member, всем остальным отказ приходит сам,
    # без единого флага. Это базовое поведение плагина, а не настройка.
    #
    # Флаг build поверх этого работает НЕ как «разрешить только своим», а
    # как «запретить всем»: явно выставленное значение перебивает проверку
    # членства, и отказ получает даже owner. Спасало только то, что у
    # оператора есть worldguard.region.bypass.<мир> — то есть главный админ
    # ходил сквозь запрет и ничего не замечал.
    #
    # Поймано 24.09.2026 по скриншоту: помощник администратора
    # (restricted_admin, он в members.groups) не мог сломать ни блока —
    # «Sorry, but you can't break that block here» шло пачкой. Проверено,
    # что дело не в чтении групп: Skript-условие `is the owner of the
    # region "spawn"` для админа отвечало true, то есть WEPIF группы
    # резолвит верно.
    #
    # Вернёшь сюда ('build', 'deny', ...) — вместе со стройкой отвалится
    # и весь /spawnbuild: добавление в members перестанет что-либо значить.

    # --- Взрывы и огонь. Гриф Спавна — отдельная статья УК, но чинить
    #     кратер после каждого криперa никто не должен.
    ('creeper-explosion', 'deny', None),
    ('other-explosion', 'deny', 'в т.ч. динамит и кристаллы Края'),
    ('tnt', 'deny', None),
    ('wither-damage', 'deny', None),
    ('fire-spread', 'deny', None),
    ('lava-fire', 'deny', None),
    ('lighter', 'deny', 'огниво'),

    # --- Декор Спавна. Вывески ImageFrame, карты городов и стойки брони
    #     висят именно здесь, а ломаются они не событием block-break,
    #     а своими собственными — build их не закрывает.
    # ⚠️ Флага armor-stand-destroy у WorldGuard нет — имя сверено с реестром
    #    Flags.class в worldguard-bukkit-7.0.18. Стойки брони закрыты общим
    #    build: WorldGuard проводит урон по ним через ту же проверку.
    #    Неизвестное имя флага плагин проглатывает молча, с одной строкой
    #    в лог, — то есть выглядело бы как работающая защита.
    ('entity-painting-destroy', 'deny', None),
    ('entity-item-frame-destroy', 'deny', 'картины ImageFrame на стенах Мэрии'),
    ('item-frame-rotation', 'deny', None),
    ('vehicle-destroy', 'deny', None),
    ('damage-animals', 'deny', 'скот и жители Мэрии — тоже имущество САП'),
    ('enderman-grief', 'deny', 'эндермены не растаскивают застройку Спавна'),

    # --- Что остаётся разрешённым ---
    ('use', 'allow', 'двери, кнопки, верстаки, лавки Shopkeepers'),
    ('ride', 'allow', 'вагонетки Незер-метро приходят на Спавн'),
    ('entry', 'allow', 'Спавн не запирается ни от кого'),
    ('exit', 'allow', None),

    # --- Сообщения на входе и выходе ---
    ('greeting', '&6&l[СПАВН] &rТерритория базы САП. Нейтральная зона, Конституция 6.2.', None),
    ('farewell', '&6&l[СПАВН] &rТы покинул нейтральную зону. Дальше — по общим законам.', None),
]

# ⚠️ chest-access НАМЕРЕННО не выставлен.
#
# Запретить доступ к чужим сундукам на Спавне выглядит как очевидный «приват»,
# но на этом сервере кража — не то, что предотвращают, а то, что судят:
# Глава 1 УК, логи CoreProtect и возврат вещей по решению Суда. Закрыв сундуки
# флагом, мы отберём у Суда половину дел и заодно сломаем лавки Shopkeepers,
# которые торгуют из сундука владельца.

OWNER_GROUPS = ['admin']
MEMBER_GROUPS = ['restricted_admin']


def spawn_from_level_dat(path):
    """Достаёт точку появления из level.dat. В 26.1 это compound 'spawn'
    с полем 'pos' (список из трёх int), а не старые SpawnX/SpawnY/SpawnZ."""
    f = io.BytesIO(gzip.open(path, 'rb').read())

    def rd(n):
        b = f.read(n)
        if len(b) != n:
            raise EOFError('level.dat обрывается на offset %d' % f.tell())
        return b

    def nm():
        return rd(struct.unpack('>H', rd(2))[0]).decode('utf-8', 'replace')

    def payload(t):
        if t == 1:  return struct.unpack('>b', rd(1))[0]
        if t == 2:  return struct.unpack('>h', rd(2))[0]
        if t == 3:  return struct.unpack('>i', rd(4))[0]
        if t == 4:  return struct.unpack('>q', rd(8))[0]
        if t == 5:  return struct.unpack('>f', rd(4))[0]
        if t == 6:  return struct.unpack('>d', rd(8))[0]
        if t == 7:  return list(rd(struct.unpack('>i', rd(4))[0]))
        if t == 8:  return nm()
        if t == 9:
            et = rd(1)[0]
            return [payload(et) for _ in range(struct.unpack('>i', rd(4))[0])]
        if t == 10:
            d = {}
            while True:
                tt = rd(1)[0]
                if tt == 0:
                    return d
                k = nm()
                d[k] = payload(tt)
        if t == 11: return [struct.unpack('>i', rd(4))[0] for _ in range(struct.unpack('>i', rd(4))[0])]
        if t == 12: return [struct.unpack('>q', rd(8))[0] for _ in range(struct.unpack('>i', rd(4))[0])]
        raise ValueError('неизвестный NBT-тег %d' % t)

    t = rd(1)[0]
    nm()
    root = payload(t)
    data = root.get('Data', root)
    pos = (data.get('spawn') or {}).get('pos')
    if not pos or len(pos) != 3:
        raise ValueError('в level.dat нет spawn.pos')
    return int(pos[0]), int(pos[2])


def keep_people(path):
    """Поимённые owners/members из УСТАНОВЛЕННОГО regions.yml.

    WorldGuard хранит регионы в своём формате (flow-стиль, `/rg save`
    переписывает файл целиком), поэтому читаем его YAML-ом, а не разбором
    нашего шаблона. Нет файла или нет региона — возвращаем пусто: это
    первая сборка.

    Возвращает {'owners': {'players': [...], 'unique-ids': [...]},
                'members': {...}} — ровно то, что дописывается в шаблон.
    """
    empty = {'owners': {'players': [], 'unique-ids': []},
             'members': {'players': [], 'unique-ids': []}}
    if not os.path.exists(path):
        return empty
    try:
        import yaml
    except ImportError:
        print('⚠ PyYAML не установлен — поимённые строители НЕ перенесены.')
        print('  Проверь /rg info spawn -w world после установки.')
        return empty
    try:
        data = yaml.safe_load(io.open(path, encoding='utf-8').read()) or {}
    except Exception as exc:
        print('⚠ %s прочитать не удалось (%s) — строители не перенесены.'
              % (os.path.basename(path), exc))
        return empty
    region = ((data.get('regions') or {}).get('spawn')) or {}
    out = {}
    for side in ('owners', 'members'):
        block = region.get(side) or {}
        out[side] = {
            'players': list(block.get('players') or []),
            'unique-ids': list(block.get('unique-ids') or []),
        }
    return out


def render(cx, cz, radius, source, keep=None):
    lines = [
        '# EKB SHIELD — WorldGuard, регион привата Спавна.',
        '#',
        '# ⚠️ ФАЙЛ СОБИРАЕТСЯ ГЕНЕРАТОРОМ. Руками не править:',
        '#       py -3 build_spawn_region.py --radius %d --install' % radius,
        '#   Иначе правка потеряется при первой же пересборке, а /rg save',
        '#   на сервере перезапишет её обратно без комментариев.',
        '#',
        '# Центр: %d, %d (%s).' % (cx, cz, source),
        '# Радиус %d блоков -> квадрат %dx%d, на всю высоту мира (%d..%d).' % (
            radius, radius * 2, radius * 2, MIN_Y, MAX_Y),
        '#',
        '# Кто может строить (флага build НЕТ — его ставить нельзя, см.',
        '# разбор в build_spawn_region.py; защищает само членство в регионе):',
        '#   owners  — группы %s' % ', '.join(OWNER_GROUPS),
        '#   members — группы %s' % ', '.join(MEMBER_GROUPS),
        '# Группа здесь — это право group.<имя> у LuckPerms, так WorldGuard',
        '# сопоставляет свои g:-записи с чужими группами.',
        '#',
        '# Поимённые строители (нанятые Мэрией рабочие) выдаются в игре:',
        '#       /spawnbuild   — окно с головами, docs/spawn_build.sk',
        '#       /rg addmember spawn <ник> -w world   — то же самое руками',
        '# Их UUID ложатся в members.unique-ids, и генератор ПЕРЕНОСИТ их',
        '# при пересборке: читает установленный на сервере regions.yml и',
        '# дописывает найденных людей обратно. Иначе первая же пересборка',
        '# молча лишала бы права всю строительную бригаду.',
        '',
        'regions:',
        '  __global__:',
        '    type: global',
        '    priority: 0',
        '    flags: {}',
        '    owners: {}',
        '    members: {}',
        '',
        '  spawn:',
        '    type: cuboid',
        '    # Приоритет 10: выше будущих регионов-маркеров государств',
        '    # (docs/state_borders_setup.sh, у них приоритет 1).',
        '    priority: 10',
        '    min:',
        '      x: %d' % (cx - radius),
        '      y: %d' % MIN_Y,
        '      z: %d' % (cz - radius),
        '    max:',
        '      x: %d' % (cx + radius),
        '      y: %d' % MAX_Y,
        '      z: %d' % (cz + radius),
        '    flags:',
    ]
    for name, value, note in FLAGS:
        if note:
            lines.append('      # %s' % note)
        if value in ('allow', 'deny'):
            lines.append('      %s: %s' % (name, value))
        else:
            lines.append("      %s: '%s'" % (name, value.replace("'", "''")))
    lines += [
        '    owners:',
        '      groups:',
    ]
    lines += ['      - %s' % g for g in OWNER_GROUPS]
    lines += domain_lines(keep, 'owners')
    lines += [
        '    members:',
        '      groups:',
    ]
    lines += ['      - %s' % g for g in MEMBER_GROUPS]
    lines += domain_lines(keep, 'members')
    lines += ['']
    return '\n'.join(lines)


def domain_lines(keep, side):
    """Строки players/unique-ids: пустые на первой сборке, перенесённые —
    на последующих."""
    block = (keep or {}).get(side) or {}
    out = []
    for key in ('players', 'unique-ids'):
        items = block.get(key) or []
        if not items:
            out.append('      %s: []' % key)
        else:
            out.append('      %s:' % key)
            out += ['      - %s' % v for v in items]
    return out


def main():
    ap = argparse.ArgumentParser(description='Регион привата Спавна для WorldGuard')
    ap.add_argument('--radius', type=int, default=192,
                    help='половина стороны квадрата в блоках (по умолчанию 192 -> 384x384)')
    ap.add_argument('--center', default=None, metavar='X,Z',
                    help='центр вручную; по умолчанию берётся из level.dat')
    ap.add_argument('--install', action='store_true', help='скопировать на сервер')
    ap.add_argument('--reload', action='store_true',
                    help='после установки послать серверу /rg load по RCON')
    args = ap.parse_args()

    if args.center:
        cx, cz = (int(v) for v in args.center.split(','))
        source = 'задан вручную ключом --center'
        print('центр задан вручную: %d, %d' % (cx, cz))
    else:
        cx, cz = CENTER
        source = 'центр проекта, CENTER в build_spawn_region.py'
        try:
            lx, lz = spawn_from_level_dat(LEVEL_DAT)
        except Exception as exc:
            print('level.dat прочитать не удалось (%s)' % exc)
            print('беру центр проекта: %d, %d' % (cx, cz))
        else:
            if (lx, lz) == (cx, cz):
                source = 'level.dat, spawn.pos — совпадает с центром проекта'
                print('центр из level.dat: %d, %d' % (cx, cz))
            else:
                # Не молча берём level.dat: если точку появления ещё не двигали,
                # там лежит 0,0 — и приват встал бы за 4,5 тысячи блоков от Спавна,
                # причём выглядело бы это как «регион создан, всё хорошо».
                print('⚠ level.dat говорит %d, %d, а центр проекта %d, %d' % (lx, lz, cx, cz))
                print('  беру центр проекта. Чтобы сошлось, на сервере:'
                      ' /setworldspawn -1750 75 4000')

    if args.radius < 16:
        sys.exit('радиус меньше 16 блоков бессмысленен')

    keep = keep_people(SERVER)
    carried = sum(len(keep[s][k]) for s in keep for k in keep[s])
    if carried:
        print('перенесено поимённых записей из регион-файла сервера: %d' % carried)
    text = render(cx, cz, args.radius, source, keep)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(text)
    print('%s — регион spawn, %dx%d блоков, %d флагов'
          % (os.path.relpath(OUT, ROOT), args.radius * 2, args.radius * 2, len(FLAGS)))

    if args.install:
        os.makedirs(os.path.dirname(SERVER), exist_ok=True)
        shutil.copy(OUT, SERVER)
        print('скопировано: %s' % os.path.relpath(SERVER, ROOT))

    if args.reload:
        if not args.install:
            sys.exit('--reload без --install бессмыслен: на сервере лежит старый файл')
        rc = subprocess.call([sys.executable, os.path.join(ROOT, 'rcon.py'), 'rg load'])
        if rc != 0:
            print('RCON не ответил — сервер выключен? Регион подхватится при следующем старте.')

    print('')
    print('Дальше руками:')
    print('  1. server.properties: spawn-protection=0 (иначе ванильная защита')
    print('     33x33 перебьёт WorldGuard для всех, кроме операторов)')
    print('  2. на сервере: /rg load  и  /rg info spawn -w world')
    print('  3. строителей выдавать в игре: /spawnbuild (окно с головами)')
    print('  4. PvP в городе ведёт docs/spawn_pvp.sk, а не флаг pvp —')
    print('     без этого скрипта Главный город останется без защиты')


if __name__ == '__main__':
    main()
