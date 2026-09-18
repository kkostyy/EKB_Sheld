# Разблокировка стадии 5 — выдаётся достижением ekb:stage5.
# Срабатывает один раз: если стадия уже 5 или выше, ничего не происходит.

execute if score #stage ekb matches ..4 run function ekb:expand/stage5
