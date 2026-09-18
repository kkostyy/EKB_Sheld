#!/bin/bash
# EKB SHIELD — проверка готовности сервера перед первым запуском.
# Запускать НА СЕРВЕРЕ: ./check_server.sh
# Ничего не меняет, только смотрит и докладывает.

set -u
SERVER_DIR="${SERVER_DIR:-/home/minecraft/server}"
PLUGINS="$SERVER_DIR/plugins"
OK=0; WARN=0; ERR=0

ok()   { echo "  [ OK ] $1"; OK=$((OK+1)); }
warn() { echo "  [ !  ] $1"; WARN=$((WARN+1)); }
err()  { echo "  [ XX ] $1"; ERR=$((ERR+1)); }

# Ищем jar по подстроке в имени, без учёта регистра
# ⚠ Имя ищется ОТ НАЧАЛА файла, а не подстрокой где угодно
# (грабля TAB внутри Execu-TAB-leItems), и аддон, чьё имя начинается
# с имени чужого плагина, не закрывает собой его отсутствие:
# один squaremap-worldguard без самого squaremap считался бы картой.
ADDON_JARS="squaremap-worldguard"
jar_list() {
    n=$(printf '%s' "$1" | tr 'A-Z' 'a-z')
    for f in "$PLUGINS"/*.jar; do
        [ -e "$f" ] || continue
        b=$(basename "$f")
        lb=$(printf '%s' "$b" | tr 'A-Z' 'a-z')
        case "$lb" in "$n"*) ;; *) continue ;; esac
        skip=""
        for a in $ADDON_JARS; do
            [ "$n" = "$a" ] && continue
            case "$lb" in "$a"*) skip=1 ;; esac
        done
        [ -z "$skip" ] && printf '%s\n' "$b"
    done
}
has_jar() { [ -n "$(jar_list "$1")" ]; }
jar_name() { jar_list "$1" | head -1; }

echo "=================================================="
echo " EKB SHIELD — проверка сервера в $SERVER_DIR"
echo "=================================================="

echo
echo "[1] Окружение"
if [ -d "$SERVER_DIR" ]; then ok "каталог сервера на месте"; else err "нет каталога $SERVER_DIR"; fi
if command -v java >/dev/null; then
    JV=$(java -version 2>&1 | head -1 | grep -oE '"[0-9]+' | tr -d '"')
    if [ "${JV:-0}" -ge 25 ]; then ok "Java $JV"
    else err "Java $JV — для 26.1.2 нужна Java 25+"; fi
else err "Java не найдена"; fi
command -v screen >/dev/null && ok "screen установлен" || warn "screen не установлен (нужен для start/backup/purge)"
if [ -f "$SERVER_DIR/purpur-26.1.2.jar" ]; then ok "ядро purpur-26.1.2.jar"
else err "нет purpur-26.1.2.jar (имя должно совпадать со start.sh)"; fi
if grep -q "^eula=true" "$SERVER_DIR/eula.txt" 2>/dev/null; then ok "EULA принята"; else err "eula.txt не принята"; fi
FREE=$(df -Pk "$SERVER_DIR" 2>/dev/null | awk 'NR==2{print int($4/1048576)}')
[ "${FREE:-0}" -ge 20 ] && ok "свободно ${FREE} ГБ" || warn "свободно ${FREE:-?} ГБ — мало под мир и бэкапы"

echo
echo "[2] Обязательные плагины"
# TAB проверяем отдельно и по НАЧАЛУ имени файла: подстрока "tab" сидит
# внутри "ExecutableItems" (Execu-TAB-leItems), а has_jar ищет без учёта
# регистра — проверка рапортовала о найденном TAB, даже когда его не было.
if ls "$PLUGINS"/TAB*.jar >/dev/null 2>&1; then
    ok "TAB — $(ls "$PLUGINS"/TAB*.jar | head -1 | sed 's|.*/||')"
else err "TAB не найден в plugins/"; fi
for P in CoreProtect LuckPerms DiscordSRV squaremap BreweryX ExecutableItems \
         DecentHolograms GSit PlasmoVoice Skript ChestShop WorldGuard WorldEdit; do
    if has_jar "$P"; then ok "$P — $(jar_name "$P")"; else err "$P не найден в plugins/"; fi
done
if has_jar "CustomPlayerModels" || has_jar "cpm"; then ok "CPM — $(jar_name 'CustomPlayerModels')"
else err "CustomPlayerModels (серверная часть) не найден"; fi
if has_jar "Essentials"; then ok "EssentialsX — $(jar_name 'Essentials')"
else warn "EssentialsX не найден — служебные телепорты Администрации не заработают"; fi

echo
echo "[3] Админ-набор и вспомогательные"
for P in SuperVanish OpenInv PlugMan Chunky; do
    has_jar "$P" && ok "$P — $(jar_name "$P")" || warn "$P не найден (см. §1 чек-листа)"
done
# spark встроен в Paper 1.21+ — отдельный jar не нужен и даже вреден (двойная загрузка)
if has_jar "spark"; then
    warn "spark лежит в plugins/ — он уже встроен в Purpur, лишний jar лучше убрать"
else
    ok "spark — встроен в ядро, отдельный jar не нужен"
fi
has_jar "CourtBridge" && ok "CourtBridge — собственный плагин суда" \
    || warn "CourtBridge.jar не залит — /courtlog работать не будет"

echo
echo "[4] Зависимости плагинов"
if has_jar "SCore"; then ok "SCore — обязательная зависимость ExecutableItems"
else err "SCore НЕ НАЙДЕН — ExecutableItems не запустится, Тетрадь Смерти работать не будет"; fi
has_jar "PlaceholderAPI" && ok "PlaceholderAPI"     || warn "PlaceholderAPI не найден — плейсхолдеры в TAB, DecentHolograms, GSit не раскроются"
if has_jar "Vault"; then ok "Vault — $(jar_name 'Vault')"
else warn "Vault не найден — проверь, заработает ли экономика ChestShop без него"; fi

echo
echo "[5] Конфликты и лишнее"
if has_jar "FastAsyncWorldEdit" && has_jar "worldedit-bukkit"; then
    err "FAWE и обычный WorldEdit одновременно — оставь что-то одно"
fi
for P in ClearLag LagFixer LagAssist; do
    has_jar "$P" && err "$P установлен: такие плагины чистят дропнутые предметы. На сервере, где алмазы — валюта, а суд возвращает вещи, это потеря улик и имущества"
done
for P in MyCommand Jail; do
    has_jar "$P" && warn "$P установлен — проект от него отказался (заменён Skript)" \
        || ok "$P отсутствует, как и задумано"
done

echo
echo "[5] Конфиги проекта"
# purpur.yml и spigot.yml Purpur и Spigot читают из КОРНЯ сервера, а не из
# config/. До 18.09.2026 setup клал их именно в config/ — настройки проекта
# не работали ни дня, и по файлам это было не видно: они лежали на месте.
for F in config/paper-world-defaults.yml purpur.yml spigot.yml server.properties; do
    [ -f "$SERVER_DIR/$F" ] && ok "$F" || err "нет $F"
done
for F in config/purpur.yml config/spigot.yml; do
    [ -f "$SERVER_DIR/$F" ] && err "$F — мёртвая копия, сервер её не читает. Удали и накати патчи: python3 apply_server_configs.py --write"
done
grep -qE "use-alternate-keepalive:[[:space:]]*true" "$SERVER_DIR/purpur.yml" 2>/dev/null \
    && ok "purpur.yml: патч проекта применён" \
    || err "purpur.yml: патч НЕ применён — python3 apply_server_configs.py --write"
grep -qE "max-tnt-per-tick:[[:space:]]*200" "$SERVER_DIR/spigot.yml" 2>/dev/null \
    && ok "spigot.yml: патч проекта применён" \
    || err "spigot.yml: патч НЕ применён — python3 apply_server_configs.py --write"
grep -q "anti-xray" "$SERVER_DIR/config/paper-world-defaults.yml" 2>/dev/null \
    && ok "anti-xray настроен" || err "в paper-world-defaults.yml нет секции anti-xray"
[ -d "$PLUGINS/BreweryX" ] && ok "конфиг BreweryX (папка BreweryX, не Brewery)"     || err "нет plugins/BreweryX/ — рецепты алкоголя не загрузятся"
[ -d "$PLUGINS/Skript/scripts" ] && ls "$PLUGINS/Skript/scripts/"*.sk >/dev/null 2>&1 \
    && ok "Skript-скрипты: $(ls "$PLUGINS/Skript/scripts/"*.sk | wc -l) шт." \
    || warn "нет .sk в plugins/Skript/scripts/ (тюрьма и голограммы рынка)"
[ -d "$SERVER_DIR/world/datapacks/ekb_border" ] && ok "датапак границы установлен" \
    || warn "датапака нет — ставится после первого запуска (мир должен существовать)"

echo
echo "[5b] Обновление 18.09.2026"
for P in ImageFrame QualityArmory TablePlays FasterMinecarts AttackThrough \
         Female-Gender pv-addon-nickname ArmorPoser; do
    if has_jar "$P"; then ok "$P — $(jar_name "$P")"; else warn "$P не установлен"; fi
done

# QualityArmory по умолчанию сам рассылает свой пак с Dropbox поверх нашего
# принудительного — клиент ловит ошибку загрузки на каждом входе.
QA="$PLUGINS/QualityArmory/config.yml"
if [ -f "$QA" ]; then
    if grep -qE "useDefaultResourcepack:[[:space:]]*false" "$QA" && grep -qE "sendOnJoin:[[:space:]]*false" "$QA"; then
        ok "QualityArmory не перебивает наш ресурспак"
    else err "QualityArmory рассылает свой пак поверх принудительного — useDefaultResourcepack и sendOnJoin в false"; fi
    grep -qE "enable_permssionsToShoot:[[:space:]]*true" "$QA" \
        && ok "QualityArmory проверяет право на выстрел" \
        || err "QualityArmory: enable_permssionsToShoot=false — стреляет кто угодно, qualityarmory.usegun не проверяется"
    if grep -qE "enableCrafting:[[:space:]]*false" "$QA" && grep -qE "enableShop:[[:space:]]*false" "$QA"; then
        ok "QualityArmory: стволы не крафтятся и не покупаются"
    else warn "QualityArmory: включён крафт или магазин — оружие появляется в обход Администрации"; fi
fi

IFR="$PLUGINS/ImageFrame/config.yml"
if [ -f "$IFR" ]; then
    grep -q "your-server-ip" "$IFR" \
        && warn "ImageFrame: DisplayURL — заглушка, аплоад картинок игроку не открыть" \
        || ok "ImageFrame: DisplayURL задан"
fi

# Приват Спавна
RG="$PLUGINS/WorldGuard/worlds/world/regions.yml"
if [ -f "$RG" ]; then
    grep -qE "^[[:space:]]+spawn:" "$RG" \
        && ok "WorldGuard: регион spawn определён" \
        || err "WorldGuard: в regions.yml нет региона spawn"
else err "WorldGuard: нет regions.yml — приват Спавна не создан (python3 build_spawn_region.py --install)"; fi
grep -qE "^spawn-protection=0" "$SERVER_DIR/server.properties" 2>/dev/null \
    && ok "ванильная spawn-protection выключена — защиту держит WorldGuard" \
    || warn "spawn-protection не 0 — ванильная защита 33x33 перебьёт WorldGuard для всех, кроме операторов"

# Центр мира совпадает во всех четырёх местах?
# Он прописан в датапаке, в двух expand_border и в регионе привата.
# Разъехались — граница встанет не вокруг Спавна.
STAGE2="$SERVER_DIR/world/datapacks/ekb_border/data/ekb/function/expand/stage2.mcfunction"
BAD_CENTER=""
grep -q "overworld run worldborder center -1750 4000" "$STAGE2" 2>/dev/null     || BAD_CENTER="$BAD_CENTER датапак(Обычный)"
grep -q "the_nether run worldborder center -218.75 500" "$STAGE2" 2>/dev/null     || BAD_CENTER="$BAD_CENTER датапак(Ад)"
grep -q "CENTER_X=-1750" "$(dirname "$0")/expand_border.sh" 2>/dev/null     || BAD_CENTER="$BAD_CENTER expand_border.sh"
grep -q "CenterX = -1750" "$(dirname "$0")/expand_border.ps1" 2>/dev/null     || BAD_CENTER="$BAD_CENTER expand_border.ps1"
grep -q "x: -1942" "$PLUGINS/WorldGuard/worlds/world/regions.yml" 2>/dev/null     || BAD_CENTER="$BAD_CENTER регион-spawn"
if [ -z "$BAD_CENTER" ]; then
    ok "центр мира -1750/4000 совпадает везде (Ад -218.75/500)"
else
    err "центр мира разошёлся:$BAD_CENTER"
fi


# Скип ночи при 25%
INIT="$SERVER_DIR/world/datapacks/ekb_border/data/ekb/function/init.mcfunction"
# Имя геймрула в 26.1 — snake_case. Проверка искала старое camelCase-имя
# и ругалась на правильный датапак — то есть гнала чинить то, что работает.
if grep -q "players_sleeping_percentage 25" "$INIT" 2>/dev/null; then
    ok "датапак ставит скип ночи при 25% спящих"
elif grep -q "playersSleepingPercentage" "$INIT" 2>/dev/null; then
    err "в датапаке camelCase-имя геймрула — функция не загрузится целиком"
else
    warn "в датапаке нет players_sleeping_percentage — ночь скипается только при 100% онлайна"
fi

echo
echo "[6] Незаполненные секреты"
grep -q "ВСТАВЬ_ТОКЕН_БОТА_СЮДА" "$PLUGINS/DiscordSRV/config.yml" 2>/dev/null \
    && err "DiscordSRV: не вписан BotToken" || ok "DiscordSRV: токен задан"
# Комментарии отрезаются: в шапке config.yml лежит пример строки с ID_КАНАЛА_*.
grep -v "^[[:space:]]*#" "$PLUGINS/DiscordSRV/config.yml" 2>/dev/null | grep -q "ID_КАНАЛА" 2>/dev/null \
    && err "DiscordSRV: не заполнены ID каналов" || ok "DiscordSRV: каналы заданы"
grep -q "ВСТАВЬ_ID" "$PLUGINS/CourtBridge/config.yml" 2>/dev/null \
    && warn "CourtBridge: не вписан Discord Webhook" || ok "CourtBridge: webhook задан"
grep -q "ВСТАВЬ_URL_ЗАГРУЖЕННОГО_ПАКА" "$SERVER_DIR/server.properties" 2>/dev/null \
    && err "server.properties: не вписан URL ресурспака, а require-resource-pack=true — НИКТО не зайдёт" \
    || ok "URL ресурспака задан"
grep -q "your-server-ip" "$PLUGINS/squaremap/config.yml" 2>/dev/null \
    && warn "squaremap: не вписан адрес веб-карты" || ok "squaremap: адрес задан"

echo
echo "=================================================="
echo " Итог: OK=$OK, предупреждений=$WARN, ошибок=$ERR"
if [ "$ERR" -gt 0 ]; then
    echo " Есть блокирующие проблемы — стартовать рано."
else
    echo " Блокеров нет. Запуск: cd $SERVER_DIR && screen -dmS minecraft ./start.sh"
fi
echo "=================================================="
