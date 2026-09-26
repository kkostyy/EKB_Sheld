# -*- coding: utf-8 -*-
"""EKB SHIELD — регистрация кастомных скинов из папки skins/.

Зачем скрипт, а не «положить PNG в плагин». SkinsRestorer хранит скин не
картинкой, а парой value+signature (`plugins/SkinsRestorer/skins/*.customskin`).
Подпись ставит Mojang, локально её не подделать — клиент такой скин отвергнет.
Обходной путь один, и им пользуется сам плагин в `/skin url`: залить PNG на
MineSkin, получить подписанную текстуру (value+signature) и записать её
в хранилище плагина тем же JSON, что пишет он сам (см. register()).

Запуск:
    py -3 add_skins.py            # показать план, ничего не делать
    py -3 add_skins.py --write    # залить и зарегистрировать
    py -3 add_skins.py --write --force   # перезалить даже уже загруженные
"""
import hashlib
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SKINS = os.path.join(ROOT, 'skins')
INDEX = os.path.join(SKINS, 'uploaded.json')
SR_CONFIG = os.path.join(ROOT, 'server', 'plugins', 'SkinsRestorer', 'config.yml')
SR_SKINS = os.path.join(ROOT, 'server', 'plugins', 'SkinsRestorer', 'skins')

MINESKIN = 'https://api.mineskin.org/generate/upload'
# MineSkin просит не частить: без ключа окно примерно такое.
DELAY = 12

# Имя скина уходит в команду `/skin <имя>` первым и единственным аргументом.
# Отсюда единственное жёсткое требование — без пробелов: `/skin Генерал
# Петухов` плагин прочитает как «Генерал», а «Петухов» выбросит.
#
# Кириллица при этом РАЗРЕШЕНА: имя набирают в чате Minecraft, который её
# принимает, а выбирают скин вообще из окна `/skins`. Запрещать её значило
# бы переименовывать половину присланной пачки в транслит без всякой нужды.
ALLOWED = set('abcdefghijklmnopqrstuvwxyz0123456789_-'
              'абвгдеёжзийклмнопрстуфхцчшщъыьэюя')


def norm(base):
    """Имя файла -> имя скина: нижний регистр, пробелы и точки в '_',
    всё непечатаемое выброшено, повторы подчёркиваний схлопнуты."""
    out = []
    for ch in base.lower():
        if ch in ALLOWED:
            out.append(ch)
        elif ch in ' .()[]+,':
            out.append('_')
        # остальное (эмодзи, кавычки, слэши) просто пропускаем
    name = ''.join(out)
    while '__' in name:
        name = name.replace('__', '_')
    return name.strip('_-')


KEYFILE = os.path.join(SKINS, 'mineskin.key')


def api_key():
    """Ключ MineSkin: сначала skins/mineskin.key, потом конфиг SkinsRestorer.

    Отдельный файл нужен потому, что конфиг плагина лежит в server/ — то
    есть в развёрнутой копии, которую перезатирает setup. Ключ в skins/
    переживает переустановку сервера.
    """
    if os.path.exists(KEYFILE):
        v = io.open(KEYFILE, encoding='utf-8').read().strip()
        if v:
            return v
    if not os.path.exists(SR_CONFIG):
        return None
    for line in io.open(SR_CONFIG, encoding='utf-8'):
        s = line.strip()
        if s.startswith('mineskinAPIKey:'):
            v = s.split(':', 1)[1].strip().strip('"\'')
            # 'key' — это заглушка из коробки, а не ключ
            if v and v != 'key':
                return v
    return None


def load_index():
    if os.path.exists(INDEX):
        try:
            return json.loads(io.open(INDEX, encoding='utf-8').read())
        except ValueError:
            print('uploaded.json повреждён — начинаю учёт заново')
    return {}


def save_index(data):
    io.open(INDEX, 'w', encoding='utf-8').write(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def collect():
    """PNG из папки -> (имя скина, модель, путь). Проверки тут же."""
    out, bad, seen = [], [], {}
    if not os.path.isdir(SKINS):
        return out, [('skins/', 'папки нет')]
    for f in sorted(os.listdir(SKINS)):
        if not f.lower().endswith('.png'):
            continue
        base = f[:-4]
        variant = 'classic'
        if base.endswith('_slim'):
            base, variant = base[:-5], 'slim'
        name = norm(base)
        if not name:
            bad.append((f, 'из имени ничего не осталось — переименуй файл'))
        elif name in seen:
            bad.append((f, 'имя «%s» уже занято файлом %s' % (name, seen[name])))
        else:
            seen[name] = f
            if name != base.lower():
                print('имя        %-28s -> %s' % (f, name))
            out.append((name, variant, os.path.join(SKINS, f)))
    return out, bad


def upload(path, name, variant, key):
    """PNG -> MineSkin -> URL подписанной текстуры."""
    boundary = '----ekbshield%d' % int(time.time() * 1000)
    data = io.open(path, 'rb').read()
    # Имя для MineSkin — только подпись в их галерее, на сервере скин
    # называется так, как его регистрирует `sr createcustom`. Кириллицу
    # MineSkin в этом поле отбивает через раз (`validation_error: Invalid
    # (name)`: «россия» нет, «беловолосая_в_платье» да), поэтому туда
    # уходит латинская метка, а русское имя остаётся в игре.
    label = 'ekb_' + hashlib.md5(name.encode('utf-8')).hexdigest()[:10]
    parts = []
    for field, value in (('name', label), ('variant', variant), ('visibility', '1')):
        parts.append(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
                      % (boundary, field, value)).encode('utf-8'))
    parts.append(('--%s\r\nContent-Disposition: form-data; name="file"; filename="%s.png"\r\n'
                  'Content-Type: image/png\r\n\r\n' % (boundary, label)).encode('utf-8'))
    parts.append(data)
    parts.append(('\r\n--%s--\r\n' % boundary).encode('utf-8'))
    body = b''.join(parts)

    req = urllib.request.Request(MINESKIN, data=body)
    req.add_header('Content-Type', 'multipart/form-data; boundary=%s' % boundary)
    req.add_header('User-Agent', 'EKB-SHIELD/1.0')
    if key:
        req.add_header('Authorization', 'Bearer %s' % key)
    # MineSkin без ключа отвечает 429, если спросить раньше срока. Ждём
    # столько, сколько просит сам сервис (поле `delay`), и повторяем.
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                res = json.loads(r.read().decode('utf-8'))
            break
        except urllib.error.HTTPError as exc:
            body = exc.read().decode('utf-8', 'replace')
            if exc.code != 429 or attempt == 3:
                raise RuntimeError('HTTP %d: %s' % (exc.code, body[:200]))
            try:
                wait = float(json.loads(body).get('delay') or DELAY)
            except ValueError:
                wait = DELAY
            time.sleep(wait + 1)
    # Формат ответа MineSkin v1: data.texture.{url, value, signature}.
    # value+signature — уже подписанная Mojang текстура, ровно то, что
    # SkinsRestorer кладёт в .customskin.
    tex = (res.get('data') or {}).get('texture') or {}
    if not (tex.get('url') and tex.get('value') and tex.get('signature')):
        raise RuntimeError('MineSkin не вернул текстуру: %s' % json.dumps(res)[:200])
    return tex['url'], tex['value'], tex['signature']


def skin_file(name):
    return os.path.join(SR_SKINS, '%s.customskin' % name)


def register(name, value, signature):
    """Записать скин прямо в хранилище SkinsRestorer.

    Раньше здесь была команда `sr createcustom <имя> <url>` по RCON, и она
    молча теряла скины: получив URL, плагин САМ идёт на MineSkin за
    подписью, а без ключа MineSkin делит лимит запросов на IP между ним и
    этим скриптом. Отказ плагин пишет только в чат отправителю, RCON
    получает пустой ответ, файла нет. Подпись у нас уже на руках, второй
    поход за ней не нужен — пишем тот же JSON, что пишет сам плагин
    (FILE-хранилище, `dataVersion: 1`)."""
    if not os.path.isdir(SR_SKINS):
        return False
    data = {'skinName': name, 'value': value, 'signature': signature,
            'dataVersion': 1}
    io.open(skin_file(name), 'w', encoding='utf-8').write(
        json.dumps(data, ensure_ascii=False))
    return True


def main():
    write = '--write' in sys.argv
    force = '--force' in sys.argv

    found, bad = collect()
    for f, why in bad:
        print('пропуск  %-28s %s' % (f, why))
    if not found:
        print('в skins/ нет подходящих PNG')
        return 0 if not bad else 1

    index = load_index()
    key = api_key()
    print('скинов найдено: %d, ключ MineSkin: %s'
          % (len(found), 'есть' if key else 'нет (будет медленнее)'))

    todo = []
    for name, variant, path in found:
        size = os.path.getsize(path)
        known = index.get(name)
        if known and not force and known.get('size') == size:
            if os.path.exists(skin_file(name)):
                print('уже загружен  %-20s %s' % (name, known.get('url', '')[:48]))
                continue
            # залит, но на сервере его нет (старый путь через RCON терял):
            # подпись сохранена — дописываем файл без похода на MineSkin
            if known.get('value') and write:
                register(name, known['value'], known['signature'])
                print('восстановлен  %-20s /skin %s' % (name, name))
                continue
        todo.append((name, variant, path, size))

    if not todo:
        print('новых скинов нет')
        return 0
    for name, variant, _p, _s in todo:
        print('к загрузке    %-20s модель %s' % (name, variant))

    if not write:
        print('')
        print('это план. Залить: py -3 add_skins.py --write')
        return 0

    ok = 0
    for i, (name, variant, path, size) in enumerate(todo):
        if i:
            # с ключом очередь быстрая; если частим — 429 и повтор в upload()
            time.sleep(DELAY if not key else 2)
        # Без ключа у MineSkin есть и ЧАСОВОЙ лимит («rate limit exceeded
        # (hour)»), а поле `delay` в таком ответе врёт — там всё те же 6 с.
        # Упёрлись — ждём по 10 минут и повторяем тот же скин: большая пачка
        # заливается несколько часов, и бросать её на середине незачем.
        while True:
            try:
                url, value, signature = upload(path, name, variant, key)
            except Exception as exc:
                if '(hour)' in str(exc):
                    print('лимит     MineSkin на час исчерпан, жду 10 минут (%s)'
                          % time.strftime('%H:%M'))
                    time.sleep(600)
                    continue
                print('ОШИБКА  %-20s %s' % (name, exc))
                url = None
            break
        if not url:
            continue
        # подпись храним в учёте: без неё потерянный файл пришлось бы
        # заново гонять через MineSkin
        index[name] = {'url': url, 'variant': variant, 'size': size,
                       'value': value, 'signature': signature}
        save_index(index)
        if register(name, value, signature):
            ok += 1
            print('готово  %-20s /skin %s' % (name, name))
        else:
            print('ОШИБКА  %-20s залит, но нет папки %s' % (name, SR_SKINS))

    print('')
    print('зарегистрировано: %d из %d' % (ok, len(todo)))
    return 0 if ok == len(todo) else 1


if __name__ == '__main__':
    sys.exit(main())
