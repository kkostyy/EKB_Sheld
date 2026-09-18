"""EKB SHIELD — сборка ресурспака в zip + подсчёт sha1 для server.properties.

Перед упаковкой проверяет целостность пака: что каждая модель, на которую
ссылается предметный файл, существует, и что у каждой модели есть все текстуры.
Битый пак при require-resource-pack=true = никто не зайдёт на сервер.

Запуск:  py -3 pack_resourcepack.py [имя_выходного_файла]
"""
import hashlib, json, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "resourcepack"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "shield_resourcepack_26.1.2.zip"
SKIP = {".DS_Store", "Thumbs.db", "desktop.ini"}
SKIP_SUFFIX = (".zip", ".rar", ".7z")   # готовые архивы внутри папки пака — не контент
SKIP_DIRS = {"новые"}                   # исходники бутылок (jpg), из которых режутся текстуры

def rid_to_path(rid, kind):
    """shield:item/rum -> assets/shield/models|textures/item/rum.(json|png)"""
    ns, _, name = rid.partition(":")
    if not name:
        ns, name = "minecraft", ns
    ext = "json" if kind == "models" else "png"
    return SRC / "assets" / ns / kind / f"{name}.{ext}"

errors, warnings = [], []

meta = json.loads((SRC / "pack.mcmeta").read_text(encoding="utf-8-sig"))
fmt = meta["pack"].get("pack_format")
print(f"pack_format = {fmt}")
EXPECTED = 84   # 26.1.x = 84, 26.2 = 88
if fmt != EXPECTED:
    warnings.append(f"pack_format={fmt}, для Minecraft 26.1.2 ожидается {EXPECTED}")

# 1) предметные файлы -> модели
models_used = set()
for item in sorted((SRC / "assets" / "minecraft" / "items").glob("*.json")):
    data = json.loads(item.read_text(encoding="utf-8-sig"))
    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "minecraft:model" and "model" in node:
                models_used.add(node["model"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(data)
    print(f"  {item.name}: найдено ссылок на модели — {len(models_used)}")

# 2) модели -> текстуры
textures_used = set()
for rid in sorted(models_used):
    if rid.startswith("minecraft:"):
        continue                      # ванильные модели — в паке их нет, это нормально
    mp = rid_to_path(rid, "models")
    if not mp.exists():
        errors.append(f"модель не найдена: {rid} -> {mp.relative_to(SRC)}")
        continue
    model = json.loads(mp.read_text(encoding="utf-8-sig"))
    for key, tex in model.get("textures", {}).items():
        if tex.startswith("#"):
            continue
        textures_used.add(tex)

for rid in sorted(textures_used):
    tp = rid_to_path(rid, "textures")
    if not tp.exists():
        errors.append(f"текстура не найдена: {rid} -> {tp.relative_to(SRC)}")
    elif tp.stat().st_size == 0:
        errors.append(f"текстура пустая (0 байт): {tp.relative_to(SRC)}")
    else:
        with tp.open("rb") as fh:
            if fh.read(8) != b"\x89PNG\r\n\x1a\n":
                errors.append(f"это не PNG: {tp.relative_to(SRC)}")

print(f"Моделей: {len(models_used)} | текстур: {len(textures_used)}")
for w in warnings:
    print("  ВНИМАНИЕ:", w)
if errors:
    for e in errors:
        print("  ОШИБКА:", e)
    sys.exit("Пак не собран — сначала исправь ошибки выше.")

# 3) упаковка: файлы кладутся в КОРЕНЬ архива, без обёрточной папки
members = [p for p in sorted(SRC.rglob("*"))
           if p.is_file() and p.name not in SKIP and p.suffix.lower() not in SKIP_SUFFIX
           and not SKIP_DIRS & set(p.relative_to(SRC).parts)]
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in members:
        z.write(p, p.relative_to(SRC).as_posix())

data = OUT.read_bytes()
sha1 = hashlib.sha1(data).hexdigest()

print(f"\nСобран: {OUT}")
print(f"Размер: {len(data)} байт ({len(data)/1024:.1f} КБ), файлов: {len(members)}")
print(f"\nresource-pack-sha1={sha1}")
print("\nПосле заливки файла на хостинг впиши в server.properties:")
print(f"  resource-pack=<URL загруженного файла>")
print(f"  resource-pack-sha1={sha1}")
print("ВАЖНО: sha1 считается от ЭТОГО файла — заливай именно его, не пересобирая.")
