#!/bin/bash
# EKB SHIELD — стартовый скрипт сервера (Purpur 26.1.2, Java 25+)
#
# Java держится на переднем плане намеренно — скрипт рассчитан на запуск
# внутри screen или под systemd, а не напрямую в SSH-сессии:
#     screen -dmS minecraft ./start.sh
# Имя сессии "minecraft" обязательно: purge.sh и backup.sh шлют в неё команды
# через screen -S minecraft -X stuff.
#
# ФЛАГИ: набор Aikar (mcflags.emc.gs) в варианте для heap >= 12 ГБ.
# Xms = Xmx намеренно: heap фиксирован, чтобы JVM не тратила паузы на его
# расширение. Не раздувай 12G «про запас» — чем больше heap, тем длиннее
# паузы G1 на сборку; 12 ГБ с запасом хватает на max-players=30.
# G1NewSizePercent=40 / G1MaxNewSizePercent=50 / G1HeapRegionSize=16M —
# это значения именно для больших heap; для 4-8 ГБ они были бы другими
# (30/40/8M), так что при изменении -Xmx правь и их.

java -Xms12G -Xmx12G \
-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 \
-XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch \
-XX:G1NewSizePercent=40 -XX:G1MaxNewSizePercent=50 -XX:G1HeapRegionSize=16M \
-XX:G1ReservePercent=15 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 \
-XX:InitiatingHeapOccupancyPercent=20 -XX:G1MixedGCLiveThresholdPercent=90 \
-XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 \
-XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 \
-Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true \
-jar purpur-26.1.2.jar nogui
