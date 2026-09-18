# Стадия 3: Найдена крепость Ада — граница до 12000 блоков (Ад: 1500).

scoreboard players set #stage ekb 3

title @a times 20 80 20
title @a subtitle {"text":"Крепость обнаружена — путь к незеритовому веку открыт.","color":"yellow"}
title @a title {"text":"Найдена крепость Ада","color":"gold","bold":true}
execute at @a run playsound minecraft:ui.toast.challenge_complete master @a

tellraw @a [{"text":"[PROJECT SHIELD] ","color":"dark_red","bold":true},{"text":"Стадия 3 из 5: ","color":"gold"},{"text":"Найдена крепость Ада","color":"yellow","bold":true}]
tellraw @a [{"text":"Крепость обнаружена — путь к незеритовому веку открыт.","color":"gray","italic":true}]

# Если автоматический режим выключен — только объявляем и зовём администрацию.
# Админам выдать тег один раз: /tag <ник> add ekb_admin
execute if score #auto ekb matches 0 run tellraw @a[tag=ekb_admin] [{"text":"[АДМИН] ","color":"red","bold":true},{"text":"Стадия 3 разблокирована. Прогенерируй чанки (Chunky, радиус 6000), затем выполни ","color":"gray"},{"text":"./expand_border.sh 3","color":"white","underlined":true}]

# Автоматический режим — двигаем границу сразу.
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder center -1750 4000
execute if score #auto ekb matches 1 in minecraft:the_nether run worldborder center -218.75 500
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder set 12000 86400
execute if score #auto ekb matches 1 in minecraft:the_nether run worldborder set 1500 86400
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder warning distance 10
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder warning time 20
execute if score #auto ekb matches 1 run tellraw @a [{"text":"Границы мира расширяются до ","color":"gold"},{"text":"12000","color":"white","bold":true},{"text":" блоков в течение 24 ч.","color":"gold"}]
