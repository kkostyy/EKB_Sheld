# Разблокировка стадии 4 — выдаётся достижением ekb:stage4.
# Срабатывает один раз: если стадия уже 4 или выше, ничего не происходит.

execute if score #stage ekb matches ..3 run function ekb:expand/stage4
