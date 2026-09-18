#!/bin/bash
# EKB SHIELD — Автоматизированная установка сервера Purpur 26.1.2
# Выполняет: проверку Java, скачивание Purpur, создание структуры папок,
# принятие EULA, первичный запуск для генерации конфигов.

set -e

SERVER_DIR="/home/minecraft/server"
PURPUR_VERSION="26.1.2"
JAVA_MIN_VERSION=25

echo "=================================================="
echo " EKB SHIELD — Установка сервера Purpur $PURPUR_VERSION"
echo "=================================================="

# [1/7] Проверка Java
echo "[1/7] Проверка версии Java..."
if ! command -v java &> /dev/null; then
    echo "ОШИБКА: Java не найдена. Установите Java $JAVA_MIN_VERSION+ перед продолжением."
    exit 1
fi
JAVA_VER=$(java -version 2>&1 | head -1 | grep -oP '"\K[0-9]+' || echo "0")
if [ "$JAVA_VER" -lt "$JAVA_MIN_VERSION" ]; then
    echo "ПРЕДУПРЕЖДЕНИЕ: обнаружена Java $JAVA_VER, рекомендуется $JAVA_MIN_VERSION+"
fi

# [2/7] Создание структуры директорий
echo "[2/7] Создание структуры директорий..."
mkdir -p "$SERVER_DIR"/{plugins,config,backups,logs,resourcepack}
cd "$SERVER_DIR"

# [3/7] Скачивание Purpur (последний билд указанной версии)
echo "[3/7] Скачивание Purpur $PURPUR_VERSION..."
BUILD=$(curl -s "https://api.purpurmc.org/v2/purpur/$PURPUR_VERSION" | grep -oP '"latest":"\K[0-9]+' || echo "latest")
curl -o purpur-$PURPUR_VERSION.jar \
    "https://api.purpurmc.org/v2/purpur/$PURPUR_VERSION/$BUILD/download"

# [4/7] Принятие EULA
echo "[4/7] Принятие EULA..."
echo "eula=true" > eula.txt

# [5/7] Копирование служебных скриптов (лежат рядом с этим файлом)
echo "[5/7] Установка служебных скриптов..."
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
for SCRIPT in start.sh backup.sh purge.sh expand_border.sh check_server.sh; do
    if [ -f "$PROJECT_DIR/$SCRIPT" ]; then
        cp "$PROJECT_DIR/$SCRIPT" "$SERVER_DIR/$SCRIPT"
        chmod +x "$SERVER_DIR/$SCRIPT"
        echo "      $SCRIPT -> $SERVER_DIR/"
    else
        echo "      ПРЕДУПРЕЖДЕНИЕ: $SCRIPT не найден рядом со скриптом."
    fi
done

# [6/7] Первичный запуск для генерации базовых файлов (server.properties и т.д.)
echo "[6/7] Первичный запуск для генерации конфигов (10 секунд, затем остановка)..."
timeout 30 java -jar purpur-$PURPUR_VERSION.jar nogui || true
sleep 2

# [7/7] Копирование готовых конфигов и контента проекта
echo "[7/7] Установка конфигов и контента EKB SHIELD..."
[ -f "$PROJECT_DIR/server.properties" ] && cp "$PROJECT_DIR/server.properties" "$SERVER_DIR/"
# ⚠️ В $SERVER_DIR/config/ лежат ТОЛЬКО paper-*.yml. purpur.yml и spigot.yml
# Purpur и Spigot читают из КОРНЯ сервера, и до 18.09.2026 они уезжали сюда же,
# в config/, — то есть настройки проекта не работали вообще. Теперь эти два
# файла в репозитории — патчи, и накатывает их apply_server_configs.py.
cp "$PROJECT_DIR/config/"paper-*.yml "$SERVER_DIR/config/" 2>/dev/null || true
[ -d "$PROJECT_DIR/plugins" ] && cp -r "$PROJECT_DIR/plugins/"* "$SERVER_DIR/plugins/"

# Патчи purpur.yml и spigot.yml — по месту, в корень сервера. Копировать их
# нельзя: на сервере сгенерированный конфиг на тысячи строк, в репозитории —
# патч на несколько ключей.
if command -v python3 >/dev/null 2>&1; then
    if ! python3 "$PROJECT_DIR/apply_server_configs.py" --write; then
        echo "      ВНИМАНИЕ: патчи purpur/spigot не применились — сверь пути ключей"
    fi
else
    echo "      python3 не найден — покати патчи руками: python3 apply_server_configs.py --write"
fi

# Skript-скрипты: тюрьма по онлайн-часам и голограммы рынка
if [ -d "$PROJECT_DIR/docs" ]; then
    mkdir -p "$SERVER_DIR/plugins/Skript/scripts"
    if cp "$PROJECT_DIR/docs/"*.sk "$SERVER_DIR/plugins/Skript/scripts/" 2>/dev/null; then
        echo "      Skript-скрипты -> plugins/Skript/scripts/"
    fi
fi

# Датапак расширения мира по достижениям
if [ -d "$PROJECT_DIR/datapack/ekb_border" ]; then
    if [ -d "$SERVER_DIR/world" ]; then
        mkdir -p "$SERVER_DIR/world/datapacks"
        cp -r "$PROJECT_DIR/datapack/ekb_border" "$SERVER_DIR/world/datapacks/"
        echo "      Датапак -> world/datapacks/ekb_border"
    else
        echo "      ПРОПУЩЕНО: мира ещё нет. После первого запуска выполни:"
        echo "        cp -r $PROJECT_DIR/datapack/ekb_border $SERVER_DIR/world/datapacks/"
    fi
fi

# Собранный CourtBridge, если уже собран через mvn
if [ -f "$PROJECT_DIR/CourtBridge/target/CourtBridge.jar" ]; then
    cp "$PROJECT_DIR/CourtBridge/target/CourtBridge.jar" "$SERVER_DIR/plugins/"
    echo "      CourtBridge.jar -> plugins/"
fi


echo "=================================================="
echo " Установка завершена!"
echo ""
echo " ОБЯЗАТЕЛЬНО скачай .jar в $SERVER_DIR/plugins/ :"
echo "   Ядро проекта : CoreProtect, LuckPerms, DiscordSRV, TAB, squaremap"
echo "   Механики     : Brewery, ExecutableItems, MyCommand, DecentHolograms,"
echo "                  GSit, PlasmoVoice, CustomizablePlayerModels, Jail"
echo "   Админ-набор  : SuperVanish (невидимость), OpenInv (инвентари, в т.ч."
echo "                  оффлайн — доказательства по кражам), Chunky (прогенерация)"
echo "                  spark КАЧАТЬ НЕ НАДО — он встроен в Paper/Purpur"
echo "   Требуются скриптами проекта:"
echo "     Skript    — docs/jail_online_time.sk, docs/market_holograms.sk, docs/nirvana.sk"
echo "                 (копировать в plugins/Skript/scripts/)"
echo "     PlugMan   — purge.sh отключает им CoreProtect на время ивента"
echo "     ChestShop — Статья 6 УК и голограммы Рыночной площади"
echo "     WorldGuard + WorldEdit + аддон-мост для squaremap"
echo "                 — границы государств на веб-карте"
echo "   Собрать отдельно: cd CourtBridge && mvn clean package"
echo ""
echo " Затем запусти сервер в screen (этого ждёт purge.sh):"
echo "   cd $SERVER_DIR && screen -dmS minecraft ./start.sh"
echo "=================================================="
