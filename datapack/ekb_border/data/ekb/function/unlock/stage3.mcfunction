# Разблокировка стадии 3 — выдаётся достижением ekb:stage3.
# Срабатывает один раз: если стадия уже 3 или выше, ничего не происходит.

execute if score #stage ekb matches ..2 run function ekb:expand/stage3
