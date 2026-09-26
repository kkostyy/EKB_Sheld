# EKB SHIELD — инициализация системы расширения мира.
# Выполняется автоматически при каждой загрузке мира (тег minecraft:load).

scoreboard objectives add ekb dummy {"text":"EKB SHIELD","color":"gold"}

# #stage — текущая стадия границы (1..5). Ставим 1 только при самой первой загрузке.
execute unless score #stage ekb matches -2147483648..2147483647 run scoreboard players set #stage ekb 1

# #auto — расширять границу автоматически при разблокировке стадии?
#   0 = только объявить (по умолчанию: сначала прогенерировать чанки через Chunky)
#   1 = расширять сразу, без подтверждения админа
execute unless score #auto ekb matches -2147483648..2147483647 run scoreboard players set #auto ekb 0

# --- Правила мира EKB SHIELD ---
# #rules — версия применённого набора правил. Одноразовая установка, как у
# #auto: иначе датапак затирал бы ручную правку админа при каждой загрузке
# мира. Меняешь правила ниже — подними номер, и они применятся заново.
#
# players_sleeping_percentage: чтобы пропустить ночь, хватает 25% онлайна.
# Ваниль требует 100%, а на сервере без телепортов (Конституция 1.1) игроки
# разбросаны по своим городам и физически не могут лечь одновременно: ночь
# не скипалась никогда. В purpur.yml ключ
#   world-settings.default.gameplay-mechanics.player.can-skip-night
# обязан быть true, иначе скип не сработает ни при каком проценте.
#
# ⚠️ ИМЯ ГЕЙМРУЛА — snake_case. В 26.1 Mojang переименовала их все:
# players_sleeping_percentage, keep_inventory и так далее. Старое
# camelCase-имя парсер команд НЕ понимает, и функция с ним не грузится
# целиком: в лог падает «Incorrect argument for command ... gamerule»,
# а следом «Couldn't load tag minecraft:load ... missing ekb:init» —
# то есть вместе с геймрулом отваливается и вся инициализация границы.
# Проверено на живом сервере 18.09.2026: gamerule doDaylightCycle
# не разбирается, gamerule do_daylight_cycle тоже (это правило
# переименовано иначе), а players_sleeping_percentage отвечает.
execute unless score #rules ekb matches 1.. run gamerule players_sleeping_percentage 25
execute unless score #rules ekb matches 1.. run scoreboard players set #rules ekb 1

# locator_bar: полоса локатора над хотбаром, появилась в 1.21.9 и включена
# по умолчанию. Она показывает НАПРАВЛЕНИЕ на каждого игрока рядом цветной
# точкой — то есть выдаёт чужое расположение сквозь стены и рельеф, бесплатно
# и всем. На сервере без телепортов и миникарт (Конституция 1.1) это ломает
# и разведку, и засады, и всю анонимность контрактов: по точке видно, кто
# идёт следом. Выключено.
#
# ⚠ Клиентский мод No Locator Bar для этого не нужен: правило серверное,
# и выключенная полоса гаснет у всех сразу, включая тех, кто без модпака.
execute unless score #rules ekb matches 2.. run gamerule locator_bar false
execute unless score #rules ekb matches 2.. run scoreboard players set #rules ekb 2
