# Стадия 5: Дракон повержен — граница до 20000 блоков (Ад: 2500).

scoreboard players set #stage ekb 5

title @a times 20 80 20
title @a subtitle {"text":"Дракон Края убит. Мир раскрыт полностью — 20000 блоков.","color":"yellow"}
title @a title {"text":"Дракон повержен","color":"gold","bold":true}
execute at @a run playsound minecraft:ui.toast.challenge_complete master @a

tellraw @a [{"text":"[PROJECT SHIELD] ","color":"dark_red","bold":true},{"text":"Стадия 5 из 5: ","color":"gold"},{"text":"Дракон повержен","color":"yellow","bold":true}]
tellraw @a [{"text":"Дракон Края убит. Мир раскрыт полностью — 20000 блоков.","color":"gray","italic":true}]

# Если автоматический режим выключен — только объявляем и зовём администрацию.
# Админам выдать тег один раз: /tag <ник> add ekb_admin
execute if score #auto ekb matches 0 run tellraw @a[tag=ekb_admin] [{"text":"[АДМИН] ","color":"red","bold":true},{"text":"Стадия 5 разблокирована. Прогенерируй чанки (Chunky, радиус 10000), затем выполни ","color":"gray"},{"text":"./expand_border.sh 5","color":"white","underlined":true}]

# Автоматический режим — двигаем границу сразу.
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder center -1750 4000
execute if score #auto ekb matches 1 in minecraft:the_nether run worldborder center -218.75 500
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder set 20000 172800
execute if score #auto ekb matches 1 in minecraft:the_nether run worldborder set 2500 172800
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder warning distance 10
execute if score #auto ekb matches 1 in minecraft:overworld run worldborder warning time 20
execute if score #auto ekb matches 1 run tellraw @a [{"text":"Границы мира расширяются до ","color":"gold"},{"text":"20000","color":"white","bold":true},{"text":" блоков в течение 48 ч.","color":"gold"}]
