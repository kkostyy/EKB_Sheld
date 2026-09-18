"""EKB SHIELD — сборка .mrpack из client_modpack/.

.mrpack — это обычный zip: modrinth.index.json в корне + папка overrides/.
Служебные файлы (README, сами скрипты) в архив не попадают — лаунчер
скопирует overrides/ поверх .minecraft игрока, лишнее там не нужно.

Запуск:  py -3 pack.py [путь_к_выходному_файлу]
"""
import json, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "ekb_shield_client.mrpack"
# Второй аргумент — альтернативный индекс (например, собранный под другую версию игры).
INDEX = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "modrinth.index.json"
SKIP_NAMES = {"README.md", "build_index.py", "pack.py", ".DS_Store", "Thumbs.db"}
# Индексы других версий не должны попадать внутрь архива как лишние файлы

index = json.loads(INDEX.read_text(encoding="utf-8"))
for f in index["files"]:
    for h in ("sha1", "sha512"):
        if not f["hashes"].get(h) or "ЗАПОЛНИТЬ" in f["hashes"][h]:
            sys.exit("ОШИБКА: незаполненный %s у %s — сначала build_index.py" % (h, f["path"]))
    if not f.get("fileSize"):
        sys.exit("ОШИБКА: fileSize=0 у %s" % f["path"])

members = [p for p in sorted(HERE.rglob("*"))
           if p.is_file() and p.name not in SKIP_NAMES and not p.name.endswith(".pyc")
           and not p.name.startswith("index_")
           and p.name != "modrinth.index.json"]

# ⚠️ Свободно лежащий .jar в корне client_modpack/ в архив НЕ идёт.
# Лаунчер ставит моды двумя способами: по ссылкам из modrinth.index.json либо
# из overrides/mods/. Jar, попавший в корень .mrpack, не делает ничего — он
# только раздувает архив (на fc.jar, то есть FreeCam 1.4.1, пак вырос с 2 КБ
# до 1.3 МБ, при том что FreeCam и так есть в индексе). Если мод нужно возить
# файлом, а не ссылкой, его место — overrides/mods/.
stray = [p for p in members if p.suffix == ".jar" and p.parent == HERE]
if stray:
    for p in stray:
        print("ПРОПУЩЕН: %s — jar в корне модпака лаунчер игнорирует." % p.name)
        print("           нужен файлом — положи в overrides/mods/, нужен ссылкой — в build_index.py")
    members = [p for p in members if p not in stray]

OUT.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.writestr("modrinth.index.json", INDEX.read_text(encoding="utf-8"))
    for p in members:
        z.write(p, p.relative_to(HERE).as_posix())

print("Собран: %s (%.1f КБ)" % (OUT, OUT.stat().st_size / 1024))
print("Индекс: %s" % INDEX.name)
print("Модов в индексе: %d | Minecraft %s | Fabric Loader %s" % (
    len(index["files"]), index["dependencies"]["minecraft"], index["dependencies"]["fabric-loader"]))
for p in members:
    print("  ", p.relative_to(HERE).as_posix())
