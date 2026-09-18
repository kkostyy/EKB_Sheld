# Разблокировка стадии 2 — выдаётся достижением ekb:stage2.
# Срабатывает один раз: если стадия уже 2 или выше, ничего не происходит.

execute if score #stage ekb matches ..1 run function ekb:expand/stage2
