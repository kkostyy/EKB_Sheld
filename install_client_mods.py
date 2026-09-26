# -*- coding: utf-8 -*-
"""EKB SHIELD — разложить клиентский модпак в .minecraft.

    py -3 install_client_mods.py           # показать, что будет поставлено
    py -3 install_client_mods.py --write   # скачать и разложить

Что делает: читает `client_modpack/modrinth.index.json`, качает каждый мод по
ссылке из индекса, сверяет sha1 (в индексе он есть — иначе проверять было бы
нечего) и кладёт в `%APPDATA%\\.minecraft\\mods`. Следом копирует
`client_modpack/overrides/` поверх `.minecraft` — там лежат `options.txt` и
собственный мод проекта.

Зачем скрипт, а не лаунчер: `.mrpack` понимают Modrinth App и Prism, а на
машине владельца стоит TLauncher — он такой файл не открывает вовсе. Ставить
десять модов руками, сверяя версии с индексом, надёжнее один раз
автоматизировать.

⚠ Fabric Loader ставится ОТДЕЛЬНО, официальным installer'ом, и без него моды
не загрузятся вообще: `.minecraft/mods` читает не ваниль, а загрузчик.
Профиль называется `fabric-loader-<версия>-<игра>`, и в лаунчере надо выбрать
именно его, а не `26.1.2`.

⚠ Версии модов НЕ трогать руками: индекс собирается `client_modpack/
build_index.py` с Modrinth, и он же следит, чтобы не уехала alpha. Отдельно
помни про Plasmo Voice: клиент и сервер обязаны быть одной версии, иначе
голос не поднимется (2.1.17 — и в `server/plugins/`, и здесь).
"""
import hashlib
import io
import json
import os
import shutil
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, 'client_modpack', 'modrinth.index.json')
OVERRIDES = os.path.join(ROOT, 'client_modpack', 'overrides')
MINECRAFT = os.path.join(os.environ.get('APPDATA', ''), '.minecraft')


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    write = '--write' in sys.argv
    index = json.load(io.open(INDEX, encoding='utf-8'))
    deps = index.get('dependencies', {})
    print('модпак: %s' % index.get('name', '—'))
    print('Minecraft %s, Fabric Loader %s'
          % (deps.get('minecraft', '?'), deps.get('fabric-loader', '?')))

    if not os.path.isdir(MINECRAFT):
        sys.exit('не найден %s' % MINECRAFT)

    profile = 'fabric-loader-%s-%s' % (deps.get('fabric-loader'), deps.get('minecraft'))
    if not os.path.isdir(os.path.join(MINECRAFT, 'versions', profile)):
        print('⚠ профиля %s нет — сначала поставь Fabric Loader' % profile)

    mods = os.path.join(MINECRAFT, 'mods')
    if write:
        os.makedirs(mods, exist_ok=True)

    for f in index['files']:
        name = os.path.basename(f['path'])
        dest = os.path.join(mods, name)
        want = (f.get('hashes') or {}).get('sha1')

        if os.path.exists(dest) and want and sha1(dest) == want:
            print('  = %-26s уже стоит' % name)
            continue
        if not write:
            print('  + %-26s %s' % (name, f['downloads'][0].split('/')[-1]))
            continue

        print('  + %-26s качаю...' % name, end=' ')
        tmp = dest + '.part'
        with urllib.request.urlopen(f['downloads'][0], timeout=180) as r, io.open(tmp, 'wb') as out:
            shutil.copyfileobj(r, out)
        got = sha1(tmp)
        if want and got != want:
            os.remove(tmp)
            sys.exit('sha1 не сошёлся у %s: ждали %s, получили %s' % (name, want, got))
        os.replace(tmp, dest)
        print('%d КБ, sha1 сошёлся' % (os.path.getsize(dest) // 1024))

    # overrides поверх .minecraft — как это делает лаунчер при установке .mrpack
    if os.path.isdir(OVERRIDES):
        for root, _, files in os.walk(OVERRIDES):
            for name in files:
                src = os.path.join(root, name)
                rel = os.path.relpath(src, OVERRIDES)
                dst = os.path.join(MINECRAFT, rel)
                if not write:
                    print('  o %s' % rel.replace('\\', '/'))
                    continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                print('  o %s' % rel.replace('\\', '/'))

    if not write:
        print('\nэто был показ. Ставить: py -3 install_client_mods.py --write')
    else:
        print('\nготово. В лаунчере выбери версию %s' % profile)


if __name__ == '__main__':
    main()
