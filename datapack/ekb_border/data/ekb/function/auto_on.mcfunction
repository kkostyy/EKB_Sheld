# /function ekb:auto_on — разрешить автоматическое расширение при ачивке.
# Включать только если территория следующей стадии уже прогенерирована Chunky.
scoreboard players set #auto ekb 1
tellraw @s [{"text":"[EKB SHIELD] ","color":"gold","bold":true},{"text":"автоматическое расширение ВКЛЮЧЕНО. Убедись, что чанки прогенерированы.","color":"yellow"}]
