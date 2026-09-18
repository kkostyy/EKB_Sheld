#!/bin/bash
# EKB SHIELD — ежедневный бэкап мира без остановки сервера.
# Ставить в cron, например каждый день в 05:00:
#     0 5 * * * /home/minecraft/server/backup.sh >> /home/minecraft/backup.log 2>&1

set -u

SERVER_DIR="/home/minecraft/server"
BACKUP_DIR="/home/minecraft/backups"
SCREEN_NAME="minecraft"
KEEP_DAYS=7
TIMESTAMP=$(date +%Y-%m-%d_%H-%M)
ARCHIVE="$BACKUP_DIR/world_$TIMESTAMP.tar.gz"

mc() { screen -S "$SCREEN_NAME" -X stuff "$1^M"; }

echo "[$(date)] Старт бэкапа..."
mkdir -p "$BACKUP_DIR" || { echo "ОШИБКА: нет доступа к $BACKUP_DIR"; exit 1; }

# Если сервер поднят — приостанавливаем автозапись, иначе архив может быть битым
SERVER_UP=0
if screen -list | grep -q "\.$SCREEN_NAME[[:space:]]"; then
    SERVER_UP=1
    mc "save-off"
    mc "save-all flush"
    sleep 15
fi

tar -czf "$ARCHIVE" -C "$SERVER_DIR" world world_nether world_the_end 2>/dev/null
TAR_STATUS=$?

[ "$SERVER_UP" -eq 1 ] && mc "save-on"

if [ $TAR_STATUS -ne 0 ] || [ ! -s "$ARCHIVE" ]; then
    echo "ОШИБКА: архив не создан, старые бэкапы НЕ удаляются."
    rm -f "$ARCHIVE"
    exit 1
fi

echo "[$(date)] Готово: $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"

# Ротация — только после успешного архива
find "$BACKUP_DIR" -name "world_*.tar.gz" -type f -mtime +$KEEP_DAYS -delete
echo "Бэкапы старше $KEEP_DAYS дней удалены."
