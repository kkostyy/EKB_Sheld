# /function ekb:auto_off — только объявлять разблокировку, границу двигать вручную.
scoreboard players set #auto ekb 0
tellraw @s [{"text":"[EKB SHIELD] ","color":"gold","bold":true},{"text":"автоматическое расширение выключено — стадии будут только объявляться.","color":"yellow"}]
