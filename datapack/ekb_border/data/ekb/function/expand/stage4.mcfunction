# Стадия 4: Край достигнут — граница до 16000 блоков (Ад: 2000).

scoreboard players set #stage ekb 4

title @a times 20 80 20
title @a subtitle {"text":"Портал в Край пройден. Мир раздвигает свои пределы.","color":"yellow"}
title @a title {"text":"Край достигнут","color":"gold","bold":true}
execute at @a run playsound minecraft:ui.toast.challenge_complete master @a

tellraw @a [{"text":"[PROJECT SHIELD] ","color":"dark_red","bold":true},{"text":"Стадия 4 из 5: ","color":"gold"},{"text":"Край достигнут","color":"yellow","bold":true}]
tellraw @a [{"text":"Портал в Край пройден. Мир раздвигает свои пределы.","color":"gray","italic":true}]

# Если автоматический режим выключен — только объявляем и зовём администрацию.
# Админам выдать тег один раз: /tag <ник> add ekb_admin
execute if score #auto ekb matches 0 run tellraw @a[tag=ekb_admin] [{"text":"[АДМИН] ","color":"red","bold":true},{"text":"Стадия 4 разблокирована. Прогенерируй чанки (Chunky, радиус 8000), затем выполни ","color":"gray"},{"text":"./expand_border.sh 4","color":"white","underlined":true}]

# Автоматический режим — двигаем границу сразу.
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder center -1750 4000
execute if score #auto ekb matches 1 in minecraft:the_nether run worldborder center -218.75 500
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder set 16000 172800
execute if score #auto ekb matches 1 in minecraft:the_nether run worldborder set 2000 172800
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder warning distance 10
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder warning time 20
execute if score #auto ekb matches 1 run tellraw @a [{"text":"Границы мира расширяются до ","color":"gold"},{"text":"16000","color":"white","bold":true},{"text":" блоков в течение 48 ч.","color":"gold"}]
