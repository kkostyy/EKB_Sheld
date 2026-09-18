#!/bin/bash
# EKB SHIELD — "Судная Ночь": временное окно без логирования и правил,
# с обязательным бэкапом мира и автоматическим откатом по истечении времени.
#
# Запускать ТОЛЬКО когда сервер уже работает в screen-сессии "minecraft":
#     screen -dmS minecraft ./start.sh
# Сам скрипт лучше запускать так, чтобы он пережил обрыв SSH:
#     nohup ./purge.sh > purge.log 2>&1 &

set -u

SERVER_DIR="/home/minecraft/server"
BACKUP_DIR="/home/minecraft/backups"
SCREEN_NAME="minecraft"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M)
BACKUP_PATH="$BACKUP_DIR/world_BEFORE_PURGE_$TIMESTAMP"
EVENT_SECONDS=10800   # 3 часа

mc() { screen -S "$SCREEN_NAME" -X stuff "$1^M"; }

die() { echo "ОШИБКА: $1" >&2; exit 1; }

# [0/5] Проверки перед стартом — лучше не начать, чем потерять мир
echo "[0/5] Проверка окружения..."
command -v screen >/dev/null || die "screen не установлен."
screen -list | grep -q "\.$SCREEN_NAME[[:space:]]" \
    || die "screen-сессия '$SCREEN_NAME' не найдена. Запусти сервер: screen -dmS $SCREEN_NAME ./start.sh"
[ -d "$SERVER_DIR/world" ] || die "Мир не найден: $SERVER_DIR/world"
mkdir -p "$BACKUP_DIR" || die "Не удалось создать $BACKUP_DIR"

AVAIL=$(df -Pk "$BACKUP_DIR" | awk 'NR==2 {print $4}')
NEEDED=$(du -sk "$SERVER_DIR/world" | awk '{print $1}')
[ "$AVAIL" -gt "$((NEEDED + NEEDED / 10))" ] \
    || die "Недостаточно места под бэкап: нужно ~${NEEDED}K, свободно ${AVAIL}K"

# [1/5] Бэкап мира с остановленной автозаписью — иначе копия может быть битой
echo "[1/5] Создание резервной копии мира..."
mc "save-off"
mc "save-all flush"
sleep 15
cp -r "$SERVER_DIR/world" "$BACKUP_PATH"
CP_STATUS=$?
mc "save-on"

[ $CP_STATUS -eq 0 ] || die "Копирование мира завершилось с ошибкой — ивент отменён."
[ -f "$BACKUP_PATH/level.dat" ] || die "В бэкапе нет level.dat — копия неполная, ивент отменён."
echo "      Бэкап проверен: $BACKUP_PATH"

# [2/5] Отключение CoreProtect (требует плагин PlugMan на сервере)
echo "[2/5] Отключение CoreProtect..."
mc "plugman disable CoreProtect"

# [3/5] Оповещение о старте Ивента
echo "[3/5] Оповещение о старте Ивента..."
mc "title @a title {\"text\":\"СУДНАЯ НОЧЬ НАЧАЛАСЬ\",\"color\":\"dark_red\"}"
mc "broadcast &4&l[PROJECT SHIELD] ПРАВИЛА И ЛОГИРОВАНИЕ ОТКЛЮЧЕНЫ НА 3 ЧАСА!"

# [4/5] Обратный отсчёт с предупреждениями
echo "[4/5] Запуск обратного отсчета ($EVENT_SECONDS секунд)..."
REMAINING=$EVENT_SECONDS
for WARN in 3600 1800 600 300 60; do
    if [ "$REMAINING" -gt "$WARN" ]; then
        sleep $((REMAINING - WARN))
        REMAINING=$WARN
        mc "broadcast &4&l[PROJECT SHIELD] &cДо конца Судной Ночи: $((WARN / 60)) мин. Откат мира неизбежен!"
    fi
done
sleep "$REMAINING"

# [5/5] Остановка, ожидание полного выхода JVM, откат
echo "[ВОССТАНОВЛЕНИЕ] Время вышло! Остановка сервера и откат мира..."
mc "title @a title {\"text\":\"СУДНАЯ НОЧЬ ОКОНЧЕНА\",\"color\":\"green\"}"
sleep 3
mc "stop"

# Ждём, пока screen-сессия реально умрёт (до 3 минут), а не фиксированные 10 секунд
for _ in $(seq 1 90); do
    screen -list | grep -q "\.$SCREEN_NAME[[:space:]]" || break
    sleep 2
done
if screen -list | grep -q "\.$SCREEN_NAME[[:space:]]"; then
    die "Сервер не остановился за 3 минуты. Мир НЕ откачен, бэкап цел: $BACKUP_PATH"
fi

# Старый мир не удаляем, а отодвигаем — на случай, если в ивенте построили что-то ценное
mv "$SERVER_DIR/world" "$SERVER_DIR/world_PURGE_RESULT_$TIMESTAMP" || die "Не удалось отодвинуть мир ивента."
cp -r "$BACKUP_PATH" "$SERVER_DIR/world" || die "Откат не удался! Мир ивента: $SERVER_DIR/world_PURGE_RESULT_$TIMESTAMP, бэкап: $BACKUP_PATH"

echo "[ГОТОВО] Мир откачен. Итог ивента сохранён в world_PURGE_RESULT_$TIMESTAMP (удали вручную, когда убедишься)."
cd "$SERVER_DIR" && screen -dmS "$SCREEN_NAME" ./start.sh
echo "Сервер перезапущен в screen-сессии '$SCREEN_NAME'."
