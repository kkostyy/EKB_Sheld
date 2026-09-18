import json, urllib.request, urllib.parse, sys

UA = {"User-Agent": "ekb-shield-modpack/1.0 (server setup)"}
GAME = sys.argv[2] if len(sys.argv) > 2 else "26.1.2"   # версия игры: py -3 build_index.py <файл> [версия]

MODS = [
    ("mods/sodium.jar", "sodium"),
    ("mods/iris.jar", "iris"),
    ("mods/custom-player-models.jar", "custom-player-models"),
    ("mods/litematica.jar", "litematica"),
    ("mods/malilib.jar", "malilib"),
    ("mods/freecam.jar", "freecam"),
    ("mods/plasmo-voice.jar", "plasmo-voice"),

    # --- Клиентские половинки серверных плагинов (добавлено 18.09.2026) ---
    # Каждый из трёх — не «ещё один мод для красоты», а вторая половина уже
    # стоящего на сервере плагина. Без мода плагин работает вхолостую:
    # сервер шлёт пакеты, разбирать их некому.
    ("mods/armor-poser.jar", "armor-poser"),           # <- ArmorPoser-Plugin
    ("mods/imageframe-client.jar", "imageframeclient"), # <- ImageFrame
    ("mods/female-gender.jar", "female-gender"),        # <- Female-Gender-Mod-Plugin
]

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

files, report = [], []
for path, slug in MODS:
    q = urllib.parse.urlencode({
        "loaders": json.dumps(["fabric"]),
        "game_versions": json.dumps([GAME]),
    })
    versions = get(f"https://api.modrinth.com/v2/project/{slug}/version?{q}")
    if not versions:
        report.append((slug, "НЕТ ВЕРСИИ ПОД %s/fabric" % GAME, "", ""))
        continue
    # ⚠️ Берём последний RELEASE, а не просто versions[0].
    # Modrinth отдаёт версии от новой к старой, не разделяя каналы, и «самая
    # новая» регулярно оказывается alpha или beta. На этом уже обожглись:
    # пересборка индекса 18.09.2026 молча подменила FreeCam 1.4.1 (release)
    # на 1.5.0-alpha.1 — и этот alpha уехал бы игрокам в .mrpack как
    # «разрешённый на сервере мод». Beta/alpha берём только если релиза под
    # эту версию игры нет вообще; в отчёте канал видно в третьей колонке.
    v = next((x for x in versions if x["version_type"] == "release"), None) \
        or next((x for x in versions if x["version_type"] == "beta"), None) \
        or versions[0]
    primary = next((f for f in v["files"] if f.get("primary")), v["files"][0])
    proj = get(f"https://api.modrinth.com/v2/project/{slug}")
    files.append({
        "path": path,
        "hashes": {"sha1": primary["hashes"]["sha1"], "sha512": primary["hashes"]["sha512"]},
        "env": {
            "client": "required" if proj["client_side"] != "unsupported" else "unsupported",
            "server": "required" if proj["server_side"] == "required" else (
                "optional" if proj["server_side"] == "optional" else "unsupported"),
        },
        "downloads": [primary["url"]],
        "fileSize": primary["size"],
    })
    report.append((slug, v["version_number"], v["version_type"], primary["filename"]))

loaders = get("https://meta.fabricmc.net/v2/versions/loader")
fabric = next(l["version"] for l in loaders if l["stable"])

index = {
    "formatVersion": 1,
    "game": "minecraft",
    "versionId": "1.0.0",
    "name": f"EKB SHIELD Client Pack ({GAME})",
    "summary": "Клиентский набор разрешённых модов для сервера EKB SHIELD (Fabric)",
    "files": files,
    "dependencies": {"minecraft": GAME, "fabric-loader": fabric},
}

out = sys.argv[1]
with open(out, "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("fabric-loader (stable):", fabric)
for r in report:
    print("  %-24s %-14s %-8s %s" % r)
