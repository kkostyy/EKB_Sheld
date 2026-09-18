#!/bin/bash
# EKB SHIELD — поэтапное расширение границы мира до 20000 блоков.
#
# Запуск:  ./expand_border.sh <стадия>      (стадии 1..5)
#          ./expand_border.sh status        — показать текущую границу
#
# Требует работающий сервер в screen-сессии "minecraft".
# Нижний мир всегда выставляется как 1/8 от Обычного — иначе игрок, ушедший
# в Аду дальше предела, при выходе из портала окажется ЗА границей Обычного мира.

set -u
SCREEN_NAME="minecraft"

# ЦЕНТР МИРА. Не 0,0: Спавн стоит на -1750 75 4000, и граница растёт
# вокруг него. Центр в нуле отрезал бы Спавн уже на первой стадии:
# 4000 в диаметре — это ±2000 от центра, а до Спавна оттуда 4370.
#
# ⚠ Нижний мир — РОВНО центр/8, как и диаметр. Записано числом,
# а не считается через $(( )): целочисленное деление bash дало бы -218
# вместо -218.75, и центры двух миров разъехались бы на шесть блоков.
# Меняешь одну пару — меняй вторую (совпадение стережёт check_server).
CENTER_X=-1750
CENTER_Z=4000
NETHER_X=-218.75
NETHER_Z=500

# стадия:  диаметр_обычного  секунд_на_расширение  повод
# Стадии разблокируются ДОСТИЖЕНИЯМИ (датапак datapack/ekb_border), а не датами.
# Этот скрипт — ручной способ применить стадию после прогенерации чанков.
# стадия:  диаметр  секунд   достижение-триггер
STAGES=(
    "1 4000  600    Открытие сервера"
    "2 8000  86400  Вход-в-Ад (story/enter_the_nether)"
    "3 12000 86400  Найдена-крепость (nether/find_fortress)"
    "4 16000 172800 Вход-в-Край (story/enter_the_end)"
    "5 20000 172800 Убит-дракон (end/kill_dragon)"
)

mc() { screen -S "$SCREEN_NAME" -X stuff "$1^M"; }
die() { echo "ОШИБКА: $1" >&2; exit 1; }

command -v screen >/dev/null || die "screen не установлен."
screen -list | grep -q "\.$SCREEN_NAME[[:space:]]" \
    || die "сервер не запущен в screen-сессии '$SCREEN_NAME'."

if [ "${1:-}" = "status" ]; then
    mc "worldborder get"
    echo "Результат смотри в консоли сервера: screen -r $SCREEN_NAME"
    exit 0
fi

STAGE="${1:-}"
[ -n "$STAGE" ] || die "укажи стадию: ./expand_border.sh <1..5>"

LINE=""
for s in "${STAGES[@]}"; do
    [ "${s%% *}" = "$STAGE" ] && LINE="$s"
done
[ -n "$LINE" ] || die "стадия '$STAGE' не найдена (доступны 1..5)."

read -r _ SIZE SECONDS_ REASON <<< "$LINE"
NETHER=$((SIZE / 8))
HOURS=$((SECONDS_ / 3600))

echo "=== Стадия $STAGE: $REASON ==="
echo "Обычный мир: $SIZE блоков (±$((SIZE / 2))), Нижний: $NETHER (±$((NETHER / 2)))"
echo "Расширение растянуто на $SECONDS_ сек (~$HOURS ч)."
echo
# Синхронизируем счётчик стадии в датапаке, иначе достижение может сработать повторно
mc "scoreboard players set #stage ekb $STAGE"

echo "ВНИМАНИЕ: перед расширением новая территория должна быть прогенерирована"
echo "плагином Chunky, иначе игроки будут генерировать чанки на ходу и ловить лаги."
echo "См. docs/world_border.md, раздел «Прогенерация»."
read -r -p "Продолжить? [y/N] " ANSWER
[ "$ANSWER" = "y" ] || { echo "Отменено."; exit 0; }

# Центр фиксируем явно — если мир уже двигали, границы разъедутся
mc "execute in minecraft:overworld run worldborder center $CENTER_X $CENTER_Z"
mc "execute in minecraft:the_nether run worldborder center $NETHER_X $NETHER_Z"

mc "execute in minecraft:overworld run worldborder set $SIZE $SECONDS_"
mc "execute in minecraft:the_nether run worldborder set $NETHER $SECONDS_"

# Предупреждение о приближении к границе: 10 блоков и 20 секунд пути
mc "execute in minecraft:overworld run worldborder warning distance 10"
mc "execute in minecraft:overworld run worldborder warning time 20"

mc "title @a title {\"text\":\"ГРАНИЦЫ МИРА РАСШИРЯЮТСЯ\",\"color\":\"gold\"}"
mc "title @a subtitle {\"text\":\"$REASON\",\"color\":\"yellow\"}"
mc "broadcast &6&l[PROJECT SHIELD] &eМир расширяется до &f$SIZE &eблоков в течение &f$HOURS ч&e. Нижний мир: &f$NETHER&e."

echo "Команды отправлены. Проверить: ./expand_border.sh status"
