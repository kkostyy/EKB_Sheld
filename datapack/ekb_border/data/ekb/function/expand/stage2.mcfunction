# Стадия 2: Врата Ада открыты — граница до 8000 блоков (Ад: 1000).

scoreboard players set #stage ekb 2

title @a times 20 80 20
title @a subtitle {"text":"Первый житель EKB SHIELD шагнул в Нижний мир.","color":"yellow"}
title @a title {"text":"Врата Ада открыты","color":"gold","bold":true}
execute at @a run playsound minecraft:ui.toast.challenge_complete master @a

tellraw @a [{"text":"[PROJECT SHIELD] ","color":"dark_red","bold":true},{"text":"Стадия 2 из 5: ","color":"gold"},{"text":"Врата Ада открыты","color":"yellow","bold":true}]
tellraw @a [{"text":"Первый житель EKB SHIELD шагнул в Нижний мир.","color":"gray","italic":true}]

# Если автоматический режим выключен — только объявляем и зовём администрацию.
# Админам выдать тег один раз: /tag <ник> add ekb_admin
execute if score #auto ekb matches 0 run tellraw @a[tag=ekb_admin] [{"text":"[АДМИН] ","color":"red","bold":true},{"text":"Стадия 2 разблокирована. Прогенерируй чанки (Chunky, радиус 4000), затем выполни ","color":"gray"},{"text":"./expand_border.sh 2","color":"white","underlined":true}]

# Автоматический режим — двигаем границу сразу.
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder center -1750 4000
execute if score #auto ekb matches 1 in minecraft:the_nether run worldborder center -218.75 500
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder set 8000 86400
execute if score #auto ekb matches 1 in minecraft:the_nether run worldborder set 1000 86400
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder warning distance 10
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder warning time 20
execute if score #auto ekb matches 1 run tellraw @a [{"text":"Границы мира расширяются до ","color":"gold"},{"text":"8000","color":"white","bold":true},{"text":" блоков в течение 24 ч.","color":"gold"}]
