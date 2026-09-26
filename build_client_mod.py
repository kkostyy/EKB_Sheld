# -*- coding: utf-8 -*-
"""EKB SHIELD — сборка клиентского мода (вкладка креатива).

    py -3 build_client_mod.py            # собрать jar в client_mod/build/
    py -3 build_client_mod.py --install  # и положить в client_modpack/overrides/mods/

⚠ Gradle и Fabric Loom здесь НЕ используются, и это не лень, а единственный
работающий путь. Loom 1.18.2 (последний релиз на 19.09.2026) падает на
`Failed to find official mojang mappings for 26.1.2`: в версионном json
Mojang у 26.1.2 остались только `client` и `server`, файлов маппингов
больше нет. Их нет потому, что клиент 26.x поставляется УЖЕ
РАЗОБФУСЦИРОВАННЫМ — в jar'е лежат настоящие `net/minecraft/...`. По той же
причине под 26.x не публикуются ни yarn, ни intermediary (на maven Fabric
последние — 1.21.11).

Раз обфускации нет, ремаппинг не нужен вообще: мод компилируется обычным
javac прямо по клиентскому jar'у, а на выходе — обычный zip с
`fabric.mod.json`. Fabric Loader такой мод грузит как свой.

⚠ Имена классов в 26.x официальные и местами НОВЫЕ: `ResourceLocation`
переименован в `Identifier`, модуль Fabric API называется
`fabric-creative-tab-api-v1` (а не `item-group-api-v1`), и точка входа —
`FabricCreativeModeTab.builder()`. Сверять по jar'у, а не по памяти и не по
докам старых версий.
"""
import glob
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(ROOT, 'client_mod')
SRC = os.path.join(MOD, 'src', 'main', 'java')
RES = os.path.join(MOD, 'src', 'main', 'resources')
BUILD = os.path.join(MOD, 'build')
LIBS = os.path.join(MOD, 'libs')
OVERRIDES = os.path.join(ROOT, 'client_modpack', 'overrides', 'mods')

MC_VERSION = '26.1.2'
LOADER_VERSION = '0.19.5'
FABRIC_API_PROJECT = 'P7dR8mSH'          # Fabric API на Modrinth
MOD_VERSION = '1.0.0'
JAR_NAME = 'ekbshield-creative-%s.jar' % MOD_VERSION

APPDATA = os.environ.get('APPDATA', '')
MINECRAFT = os.path.join(APPDATA, '.minecraft')


def jdk():
    """JDK 21+: клиент 26.1.2 просит рантайм 25, компилируем под 21."""
    for base in [r'C:\Program Files\Eclipse Adoptium', r'C:\Program Files\Java']:
        for d in sorted(glob.glob(os.path.join(base, 'jdk-*')), reverse=True):
            javac = os.path.join(d, 'bin', 'javac.exe')
            if os.path.exists(javac):
                return d
    sys.exit('не найден JDK — нужен 21 или новее')


def client_jar():
    path = os.path.join(MINECRAFT, 'versions', MC_VERSION, '%s.jar' % MC_VERSION)
    if not os.path.exists(path):
        sys.exit('не найден клиент %s: %s\n'
                 'Запусти игру этой версии хотя бы раз — лаунчер её скачает.'
                 % (MC_VERSION, path))
    return path


def client_libraries():
    """Все библиотеки клиента.

    ⚠ Их нужен ВЕСЬ набор, а не gson со slf4j: сигнатуры Minecraft тянут за
    собой brigadier (`Message` в `Component`), DataFixerUpper (`DataResult`
    у `TextColor.parseColor`, `Keyable` у реестров) и jspecify (`@Nullable`
    на `ItemStack.get`). Без них javac падает на «cannot access», даже если
    сам код этих классов не упоминает.
    """
    jars = glob.glob(os.path.join(MINECRAFT, 'libraries', '**', '*.jar'), recursive=True)
    if not jars:
        sys.exit('не найдены библиотеки клиента в %s' % os.path.join(MINECRAFT, 'libraries'))
    # natives-* — это .dll в jar'ах, компилятору они не нужны
    return [j for j in jars if 'natives' not in os.path.basename(j)]


def fetch(url, path):
    if os.path.exists(path):
        return path
    print('качаю %s' % os.path.basename(path))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as r, io.open(path, 'wb') as f:
        shutil.copyfileobj(r, f)
    return path


def fabric_libs():
    """Loader (точка входа) и модуль вкладок из Fabric API (builder)."""
    loader = fetch(
        'https://maven.fabricmc.net/net/fabricmc/fabric-loader/%s/fabric-loader-%s.jar'
        % (LOADER_VERSION, LOADER_VERSION),
        os.path.join(LIBS, 'fabric-loader-%s.jar' % LOADER_VERSION))

    api = os.path.join(LIBS, 'fabric-api.jar')
    if not os.path.exists(api):
        url = ('https://api.modrinth.com/v2/project/%s/version'
               '?game_versions=%%5B%%22%s%%22%%5D&loaders=%%5B%%22fabric%%22%%5D'
               % (FABRIC_API_PROJECT, MC_VERSION))
        with urllib.request.urlopen(url, timeout=60) as r:
            versions = json.loads(r.read().decode('utf-8'))
        if not versions:
            sys.exit('на Modrinth нет Fabric API под %s' % MC_VERSION)
        print('Fabric API %s' % versions[0]['version_number'])
        fetch(versions[0]['files'][0]['url'], api)

    # ⚠ Fabric API — это контейнер: сами модули лежат ВЛОЖЕННЫМИ jar'ами в
    # META-INF/jars. Распаковываются все: вкладку даёт
    # fabric-creative-tab-api-v1 (с 26.x переименован из item-group-api-v1),
    # но он тянет fabric-api-base с классом `Event`, и без него javac
    # спотыкается на «cannot access Event».
    modules = os.path.join(LIBS, 'api')
    if not os.path.isdir(modules):
        os.makedirs(modules)
        with zipfile.ZipFile(api) as z:
            inner = [n for n in z.namelist()
                     if n.startswith('META-INF/jars/') and n.endswith('.jar')]
            if not any('creative-tab-api' in n for n in inner):
                sys.exit('в Fabric API нет модуля creative-tab-api')
            for name in inner:
                io.open(os.path.join(modules, os.path.basename(name)), 'wb').write(z.read(name))
        print('модулей Fabric API: %d' % len(inner))
    return [loader] + sorted(glob.glob(os.path.join(modules, '*.jar')))


def main():
    java_home = jdk()
    print('JDK:    %s' % java_home)
    print('клиент: %s' % client_jar())

    cp = [client_jar()] + client_libraries() + fabric_libs()
    print('classpath: %d jar(ов)' % len(cp))

    classes = os.path.join(BUILD, 'classes')
    shutil.rmtree(classes, ignore_errors=True)
    os.makedirs(classes)

    sources = glob.glob(os.path.join(SRC, '**', '*.java'), recursive=True)
    # Аргументы уходят файлом: classpath из сотен jar'ов в командную
    # строку Windows не влезает (лимит 32 КБ).
    argfile = os.path.join(BUILD, 'javac.args')
    with io.open(argfile, 'w', encoding='utf-8') as f:
        f.write('-encoding UTF-8\n--release 21\n')
        f.write('-classpath "%s"\n' % os.pathsep.join(cp).replace('\\', '/'))
        f.write('-d "%s"\n' % classes.replace('\\', '/'))
        for src in sources:
            f.write('"%s"\n' % src.replace('\\', '/'))
    cmd = [os.path.join(java_home, 'bin', 'javac.exe'), '@' + argfile]
    print('javac: %d файл(ов)' % len(sources))
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if res.returncode:
        print(res.stdout)
        print(res.stderr)
        sys.exit('компиляция не прошла')
    if res.stderr.strip():
        print(res.stderr.strip())

    jar_path = os.path.join(BUILD, JAR_NAME)
    with zipfile.ZipFile(jar_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for base in (classes, RES):
            for root, _, files in os.walk(base):
                for name in files:
                    full = os.path.join(root, name)
                    rel = os.path.relpath(full, base).replace('\\', '/')
                    data = io.open(full, 'rb').read()
                    if rel == 'fabric.mod.json':
                        # версия подставляется здесь, как это делал бы Gradle
                        data = data.decode('utf-8').replace('${version}', MOD_VERSION)
                        data = data.encode('utf-8')
                    z.writestr(rel, data)
    print('готово: %s (%d КБ)' % (jar_path, os.path.getsize(jar_path) // 1024))

    if '--install' in sys.argv:
        os.makedirs(OVERRIDES, exist_ok=True)
        for old in glob.glob(os.path.join(OVERRIDES, 'ekbshield-creative-*.jar')):
            os.remove(old)
        shutil.copy2(jar_path, os.path.join(OVERRIDES, JAR_NAME))
        print('положено в модпак: client_modpack/overrides/mods/%s' % JAR_NAME)
        print('дальше: py -3 client_modpack/pack.py')


if __name__ == '__main__':
    main()
