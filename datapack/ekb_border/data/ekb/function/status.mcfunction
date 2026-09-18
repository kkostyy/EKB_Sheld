# /function ekb:status — показать текущее состояние системы
tellraw @s [{"text":"[EKB SHIELD] ","color":"gold","bold":true},{"text":"стадия границы: ","color":"gray"},{"score":{"name":"#stage","objective":"ekb"},"color":"white"},{"text":" из 5","color":"gray"}]
tellraw @s [{"text":"Автоматическое расширение: ","color":"gray"},{"score":{"name":"#auto","objective":"ekb"},"color":"white"},{"text":"  (0 = только объявлять, 1 = расширять сразу)","color":"dark_gray"}]
tellraw @s [{"text":"Правила мира: ","color":"gray"},{"text":"набор №","color":"gray"},{"score":{"name":"#rules","objective":"ekb"},"color":"white"},{"text":"  (ночь скипается при 25% спящих)","color":"dark_gray"}]
execute in minecraft:overworld run worldborder get
