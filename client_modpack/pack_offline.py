"""EKB SHIELD — «офлайн»-модпак: все моды ВНУТРИ файла, без Modrinth.

Обычный ekb_shield_client.mrpack хранит моды ссылками на cdn.modrinth.com, и
лаунчер качает их при установке. У части игроков Modrinth заблокирован
провайдером (api.modrinth.com и meta.prismlauncher.org не открываются —
28.09.2026, друг владельца) — такой .mrpack у них не ставится вовсе.
Здесь каждый мод из индекса скачивается ЗДЕСЬ, сверяется по sha1 и кладётся
в overrides/mods/, а список files в индексе остаётся пустым: лаунчеру нечего
качать с Modrinth.

⚠ Сам Minecraft и Fabric Loader лаунчер всё равно тянет у Mojang и со своего
сервера метаданных — это обходится кэшем метаданных (ely_meta_*.zip), а не
этим скриптом.

Запуск:  py -3 pack_offline.py [--publish]
  --publish  положить результат в веб-корень squaremap: тогда игроки из
             Radmin скачают его по http://<Radmin-IP>:8080/<имя файла>
"""
import hashlib, json, shutil, sys, urllib.request, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "ekb_shield_client_offline.mrpack"
CACHE = HERE / "__jarcache__"
WEB = ROOT / "server" / "plugins" / "squaremap" / "web"
SKIP = {"README.md", "build_index.py", "pack.py", "pack_offline.py", ".DS_Store", "Thumbs.db"}

index = json.loads((HERE / "modrinth.index.json").read_text(encoding="utf-8"))
CACHE.mkdir(exist_ok=True)

jars = []
for f in index["files"]:
    if f.get("env", {}).get("client") == "unsupported":
        continue
    name = Path(f["path"]).name
    dst = CACHE / name
    want = f["hashes"]["sha1"]
    if not dst.exists() or hashlib.sha1(dst.read_bytes()).hexdigest() != want:
        url = f["downloads"][0]
        print("  качаю", name)
        req = urllib.request.Request(url, headers={"User-Agent": "ekb-shield-pack/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            dst.write_bytes(r.read())
    got = hashlib.sha1(dst.read_bytes()).hexdigest()
    if got != want:
        sys.exit("ОШИБКА: sha1 %s не совпал (%s != %s)" % (name, got, want))
    jars.append((f["path"], dst))

offline = dict(index)
offline["files"] = []
offline["name"] = index["name"] + " — офлайн"
offline["versionId"] = index["versionId"] + "-offline"

overrides = [p for p in sorted((HERE / "overrides").rglob("*")) if p.is_file() and p.name not in SKIP]
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.writestr("modrinth.index.json", json.dumps(offline, ensure_ascii=False, indent=2))
    for p in overrides:
        z.write(p, p.relative_to(HERE).as_posix())
    # mods/<имя>.jar из индекса -> overrides/mods/<имя>.jar
    for path, src in jars:
        z.write(src, "overrides/" + path)

print("Собран: %s (%.1f МБ), модов внутри: %d" % (OUT, OUT.stat().st_size / 1048576, len(jars)))
if "--publish" in sys.argv:
    shutil.copy2(OUT, WEB / OUT.name)
    print("Выложен: %s" % (WEB / OUT.name))
