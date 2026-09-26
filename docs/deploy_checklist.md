# EKB SHIELD — Чек-лист развёртывания

Всё, что нельзя сделать из репозитория: требует доступа в интернет, к Discord,
к хосту сервера или игровых решений. Отмечай по мере выполнения.

## 0. Куда что класть

`SERVER_DIR = /home/minecraft/server` — путь задан в `setup.sh`, `backup.sh`,
`purge.sh` и `expand_border.sh`. Меняешь его — меняй во всех четырёх.

**Почти всё раскладывает `setup.sh` сам.** Ниже — что куда попадает, чтобы можно
было проверить или разложить руками.

| Из репозитория | Куда на сервере | Кто кладёт |
|---|---|---|
| `server.properties` | `$SERVER_DIR/` | setup.sh |
| `config/paper-*.yml` | `$SERVER_DIR/config/` | setup.sh |
| `config/purpur.yml`, `config/spigot.yml` | **не копируются** — это патчи, их накатывает `apply_server_configs.py` в `$SERVER_DIR/purpur.yml` и `$SERVER_DIR/spigot.yml` | setup.sh вызывает скрипт |
| `plugins/<Плагин>/` | `$SERVER_DIR/plugins/<Плагин>/` | setup.sh |
| `start.sh`, `backup.sh`, `purge.sh`, `expand_border.sh` | `$SERVER_DIR/` | setup.sh |
| `docs/*.sk` | `$SERVER_DIR/plugins/Skript/scripts/` | setup.sh |
| `datapack/ekb_border/` | `$SERVER_DIR/world/datapacks/` | setup.sh (после того, как мир создан) |
| `CourtBridge/target/CourtBridge.jar` | `$SERVER_DIR/plugins/` | setup.sh, если собран |
| Скачанные `.jar` плагинов | `$SERVER_DIR/plugins/` | **ты, вручную** |

### Что НЕ идёт на игровой сервер

| Файл | Куда на самом деле |
|---|---|
| `shield_resourcepack_26.1.2.zip` | на файловый хостинг (mc-packs.net или свой веб-сервер). На сервер кладётся только URL + sha1 в `server.properties` |
| `ekb_shield_client.mrpack` | игрокам — в Discord, на сайт. Открывается в Modrinth App / Prism Launcher |
| `discord_bot/` | любой хост с Node.js — можно тот же VPS, отдельной папкой (например `/home/minecraft/court-bot`). Серверу Minecraft он не нужен |
| `docs/*.md` | нигде не «ставится» — это законы для Discord и людей |

### Порядок первого развёртывания

```bash
# 1. Залить папку проекта на сервер, например в /home/minecraft/ekb_shield
scp -r ekb_shield user@сервер:/home/minecraft/

# 2. Развернуть
cd /home/minecraft/ekb_shield && ./setup.sh

# 3. Скачать .jar плагинов в /home/minecraft/server/plugins/ (список — §1)

# 4. Запустить
cd /home/minecraft/server && screen -dmS minecraft ./start.sh

# 5. Мир создан — доложить датапак и перезагрузить
cp -r /home/minecraft/ekb_shield/datapack/ekb_border /home/minecraft/server/world/datapacks/
screen -S minecraft -X stuff "reload^M"
```

Конфиги плагинов из репозитория перезаписывают дефолтные. Плагин, впервые
запустившись, дополнит свой файл недостающими ключами сам — в репозитории лежат
только те секции, которые важны проекту, а не полные конфиги на 400 строк.

## 0a. Windows: как это запускается

Сервер развёрнут локально в `D:\EKB_Shield\server` (Linux-хоста нет).
Bash-скрипты (`setup.sh`, `start.sh`, `backup.sh`, `purge.sh`, `expand_border.sh`,
`check_server.sh`) оставлены для будущего переезда на VPS — на Windows работают
их PowerShell-двойники:

| Задача | Windows | Linux |
|---|---|---|
| Установка | `.\setup.ps1` | `./setup.sh` |
| Запуск | `D:\EKB_Shield\server\start.bat` (двойной клик) | `screen -dmS minecraft ./start.sh` |
| Проверка | `.\check_server.ps1` | `./check_server.sh` |
| Бэкап | `.ackup.ps1` | `./backup.sh` |
| Граница мира | `.\expand_border.ps1 <1..5>` | `./expand_border.sh <1..5>` |

Команды на работающий сервер уходят через **RCON** (`rcon.py`), потому что окно
консоли на Windows не подцепить так, как screen-сессию. В `server.properties`
для этого включено `enable-rcon=true`, порт 25575 слушает только localhost —
наружу его открывать не надо.

⚠️ Minecraft переписывает `server.properties` при каждом запуске. Если правишь
файл при работающем сервере, изменения затрутся — правь на остановленном.

Ежедневный бэкап по расписанию (один раз, PowerShell от администратора):
```powershell
$a = New-ScheduledTaskAction -Execute "powershell.exe" `
     -Argument "-NoProfile -ExecutionPolicy Bypass -File D:\EKB_Shieldackup.ps1"
$t = New-ScheduledTaskTrigger -Daily -At 5am
Register-ScheduledTask -TaskName "EKB SHIELD backup" -Action $a -Trigger $t
```

## 1. Плагины — ссылки и версии под 26.1.2 (проверено по API 2026-09-15)

Все ссылки на Modrinth имеют вид `https://modrinth.com/plugin/<слаг>`.

### Ядро проекта

| Плагин | Ссылка | Версия под 26.1.2 |
|---|---|---|
| CoreProtect | modrinth.com/plugin/coreprotect | 24.0 |
| LuckPerms | modrinth.com/plugin/luckperms | 5.5.71 (Bukkit) |
| DiscordSRV | modrinth.com/plugin/discordsrv | 1.30.5 |
| TAB | modrinth.com/plugin/tab-was-taken | 6.1.3 |
| squaremap | modrinth.com/plugin/squaremap | 1.3.13.1 |

### Механики

| Плагин | Ссылка | Версия под 26.1.2 |
|---|---|---|
| BreweryX | modrinth.com/plugin/breweryx | 3.7.0 |
| ExecutableItems | modrinth.com/plugin/executableitems | 7.26.9.14 (тег `26.1`) |
| DecentHolograms | modrinth.com/plugin/decentholograms | 2.10.1 |
| GSit | modrinth.com/plugin/gsit | 3.5.1 |
| Plasmo Voice | modrinth.com/plugin/plasmo-voice | 2.1.17 (Paper) — поднят 18.09.2026 вместе с модпаком |
| CPM (серверная часть) | modrinth.com/plugin/custom-player-models | 0.6.27a (Paper) |
| ChestShop | modrinth.com/plugin/chestshop | 3.13-pre-1 |
| EssentialsX | essentialsx.net/downloads.html — вкладка **Stable Release** | 2.22.0 |

### Админ-набор и инфраструктура

| Плагин | Ссылка | Версия под 26.1.2 |
|---|---|---|
| SuperVanish | modrinth.com/plugin/supervanish | 3.3 |
| spark | **качать не нужно** — встроен в Paper 1.21+, значит и в Purpur 26.1.2 | 1.10.185 |
| OpenInv | modrinth.com/plugin/openinv | 5.3.3 |
| Skript | modrinth.com/plugin/skript | 2.16.2 |
| PlugManX | modrinth.com/plugin/plugmanx | 3.1.0 |
| WorldGuard | modrinth.com/plugin/worldguard | 7.0.18 |
| WorldEdit | modrinth.com/plugin/worldedit | 7.4.5 |

### Обновление 18.09.2026 — плагины из присланного списка

Проверено по Modrinth API 18.09.2026. Ссылки вида `modrinth.com/plugin/<слаг>`.

| Плагин | Слаг | Версия под 26.1.2 | Зачем |
|---|---|---|---|
| ImageFrame | `imageframe` | 2026.1.4.0 | картины на картах в рамках: вывески лавок, объявления Суда |
| QualityArmory | `qualityarmory` | 2.1.4 | огнестрел; крафт и магазин выключены, стволы выдаёт Администрация |
| TablePlays | `tableplays` | 3.14159-1 | настольные игры (есть русская локализация в jar) |
| Faster Minecarts | `speedier-minecarts` | 1.0 | рельсы — единственный быстрый транспорт там, где запрещены телепорты |
| Attack Through | `attack-through` | 1.0.2 | удар сквозь решётку и забор: тюрьма и загоны |
| Female Gender (плагин) | `female-gender-spigot` | 1.6.0 | серверная половина клиентского мода |
| pv-addon-nickname | `pv-addon-nickname` | 2.1.3 | ники в интерфейсе Plasmo Voice |
| ArmorPoser (плагин) | `armor-poser-plugin` | 2.0.1 | обновление с 2.0.0 |

Плюс три КЛИЕНТСКИХ мода в `client_modpack` — без них три плагина из таблицы
работают вхолостую: `armor-poser` 14.1.0, `imageframeclient` 1.2.0,
`female-gender` 5.0.0-Beta.5. Первый и третий существуют только в канале beta.

Plasmo Voice поднят **2.1.16 -> 2.1.17** на обеих сторонах разом: у Plasmo
клиент и сервер должны говорить на одном протоколе, а модпак при пересборке
всё равно взял бы свежий релиз.

### Границы государств на карте (18.09.2026)

| Плагин | Откуда | Версия | Зачем |
|---|---|---|---|
| squaremap-worldguard | CI-сборка jpenilla/squaremap-addons | 1.0.0-SNAPSHOT (04.09.2026) | рисует регионы WorldGuard на squaremap, в том числе полигональные |

⚠️ **У аддона нет релизов вообще** — ни на Modrinth, ни на Hangar, ни в
GitHub Releases: только ночные артефакты GitHub Actions. Скачан через
nightly.link (сборка ветки master, run 33909343384). Зависит от squaremap и
WorldGuard — оба у нас стоят, `api-version: 1.18`. Гарантий под 26.1.2 нет,
как и у ClansLite.

- [ ] После первого запуска поправить сгенерированный
      `plugins/squaremap-worldguard/config.yml`:
      `world-settings.default.control.label` → `Государства`,
      `update-interval` → `60` (по умолчанию 300 секунд, то есть новая
      граница появляется на карте через пять минут).
      В репозитории конфига нет намеренно: у Configurate свой
      `config-version` и цепочка миграций, и подсунутый руками файл
      с чужой версией плагин стал бы трансформировать.
- [ ] Проверить в игре: глава города `/border start <город>`, обход,
      `/border finish`; админ в том же мире `/borderapply <город>`.
      Полигон должен появиться в слое карты в ближайший цикл обновления.
- [ ] Аддон по умолчанию рисует ВСЕ регионы (`regions.list-mode: BLACKLIST`
      с пустым списком), то есть и приват Спавна. Решить, надо ли
      его показывать; если нет — внести `spawn` в `regions.list`.

### Из присланного списка НЕ ставится

| Просили | Почему нет |
|---|---|
| `styled-chat` | Fabric-мод, Purpur Fabric не грузит. Чат у нас CarbonChat |
| `fsit` | Fabric-мод; сидение уже даёт GSit 3.5.1 |
| `lmd` (Let Me Despawn) | под 26.1.2 только Fabric-сборка. И по сути противоречит §1b: плагин ускоряет деспавн предметов, а дроп на этом сервере — улики и чужое имущество |
| `tooltrims` | это ПЛАГИН под Paper/Purpur, и он застрял на 1.21.6 (перепроверено 19.09.2026). Замена под 26.1.2 есть — датапак `tool-trims` 3.0.7 (modrinth.com/datapack/tool-trims): один zip, внутри и `data/` (4 шаблона ковки, рецепты), и `assets/` с папкой `assets-26-1` под нашу версию. Датапак кладётся в `server/world/datapacks/`, ассеты мерджатся в `shield_resourcepack`, а дальше по обычному кругу: пересборка пака, заливка на mc-packs.net, новый `resource-pack-sha1`. Не поставлено — ждёт решения |
| `displaytags` | останавливается на 1.21.11 |
| `watut-plugin` | останавливается на 1.21.5 |
| `erebus-god-pickaxe` | останавливается на 1.21.11 |
| `attack-cooldown-remover` | останавливается на 1.20.1 |
| `fungun` | останавливается на 1.21.10 |
| `death-note-plugin` | останавливается на 1.21.5 — и не нужен: Тетрадь уже написана на Skript (`docs/death_note.sk`), два механизма на один предмет конфликтовали бы |
| Plasmo Voice Messages `[PVM]` | это ДРУГОЙ проект, не тот `pv-addon-voice-messages`, что уже стоит; под 26.1.2 сборок нет |

### 1d. Долги по ресурспаку после этого обновления

Два плагина рисуют свои предметы через CustomModelData, а моделей у нас нет:

- [x] ~~**QualityArmory**~~ 18.09.2026: модели вмерджены. Пак взят с
      `github.com/ZombieStriker/QualityArmory-Resourcepack` (`QualityArmory-21.zip`),
      213 файлов пространства `qualityarmory` плюс определения `crossbow`,
      `phantom_membrane`, `quartz`, `rabbit_hide`. Рассылка своего пака у плагина
      по-прежнему выключена (`useDefaultResourcepack`, `sendOnJoin`) — иначе он
      перебивал бы наш принудительный.
- [x] ~~**TablePlays**~~ 18.09.2026: модели вмерджены. Пак — `tableplays_1_21_4.zip`,
      дополнительный файл версии на Modrinth; в jar'е ассетов нет вообще.
      223 файла пространства `m3vtg`, всё на `warped_fungus_on_a_stick`.
- [x] ~~**ImageFrame** — язык.~~ 18.09.2026: `ru_ru` есть. Страница
      `loohpjames.com/imageframe/languages/` отдаёт список не в HTML, а
      скриптом с `api.loohpjames.com/spigot/plugins/imageframe/language` —
      именно поэтому раньше и не подтверждалось. 29 языков,
      есть и `uk_ua`. `Language: "ru_ru"` выставлен.

### 1f. Что настроить в игре после обновления 18.09.2026

Восемь новых разделов меню держатся на Skript, а он — на Казне Спавна.
Пока Казна не назначена, не работают скупщик, аренда, почта, казино, бар,
газета и экспертиза: все они платят и принимают через неё.

- [ ] **Точка появления и центр границы.** В консоли:
      `/setworldspawn -1750 75 4000`, потом `.\expand_border.ps1 1` — он ставит
      центр границы туда же (Ад — −1750/8 = −218.75, 500). Без этого
      граница останется вокруг 0,0, а Спавн окажется за ней: до него
      от нуля 4370 блоков, а первая стадия — ±2000.
      Проверить: `/rg load`, затем `/rg info spawn -w world`.
- [ ] **Казна Спавна.** Поставить сундук или бочку в Мэрии, встать перед ним
      и выполнить `/settreasury`. Проверить: `/treasury`. Сундук должен стоять
      внутри региона `spawn`, иначе это просто сундук у дороги.
      Мало места — поставить рядом ещё и добавить `/addtreasury` (убрать —
      `/deltreasury`). Двойной сундук считается одним контейнером на 54 слота,
      вторую половину добавлять не надо.
- [ ] **Наполнить Казну.** Пустая Казна = скупщик не покупает, казино не
      принимает ставки. Это задумано, но на старте её надо чем-то наполнить.
- [ ] **Точка Теневого Рынка:** встать на месте и `/setshadowpoint`.
      Скин Личины: `/setshadowskin <ник>` (по умолчанию Steve).
- [ ] **Роли новых должностей** через `/ekbroles`: Журналист (без него нет
      выпусков газеты), Стример/Ютубер, Теневое Сообщество.
- [ ] **Первый выпуск газеты:** журналист пишет книгу, ПОДПИСЫВАЕТ её и
      сдаёт `/newsissue`. Книга с пером не годится — у неё для Skript ноль
      страниц.
- [ ] **Кровавый Сон:** объявить `/bloodnight через <часов>`, а сам ивент
      запустить с хоста: `.\purge.ps1 -Hours 3` (сначала `-WhatIfOnly`).
- [ ] **Особые артефакты.** Ничего настраивать не надо, но и появиться сами
      они не могут: `/artifact give <ник> <id>` (id — `/artifact ids`).
      Каждого по два на мир, реестр ведёт скрипт. Раздал — посматривай
      `/artifact list`; экземпляр, утонувший в лаве, списывается вручную
      через `/artifact release <id> <номер>`, иначе третий не выдать.

Новые Skript-скрипты (ставятся вместе с остальными, `docs/*.sk`):
`treasury.sk` (фундамент, нужен всем), `spawn_market.sk`, `mail.sk`,
`bar_casino.sk`, `press.sk`, `shadow.sk`, `evidence.sk`, `bloodnight.sk`,
`artifacts.sk` (требует `contracts.sk` и `shadow.sk` — Маска зовёт их
функции `ct_alias` и `sh_skin`).

### 1e. Приват Спавна (WorldGuard)

Регион `spawn` собирается генератором, потому что `/rg define` требует
выделения WorldEdit, а у консоли и RCON выделения нет:

```bash
py -3 build_spawn_region.py --radius 192 --install    # 384x384 вокруг 0,0
# на работающем сервере:
py -3 rcon.py "rg load"
py -3 rcon.py "rg info spawn -w world"
```

- [x] `spawn-protection=0` в `server.properties` — иначе ванильная защита
      33x33 перебивает WorldGuard для всех, кроме операторов, и Строительная
      бригада не может строить в центре Спавна без видимой причины.
- [ ] Строителей добавить поимённо: `/rg addmember spawn <ник> -w world`
      (право `ekb.duty.builder` — не группа LuckPerms, через файл региона
      его не подставить).
- [ ] Радиус 192 взят с потолка: Конституция 6.2 объявляет базу САП
      нейтральной зоной, но её размер нигде не записан. Сверить с реальной
      застройкой и пересобрать с другим `--radius`.

⚠️ `chest-access` у региона намеренно НЕ выставлен. Закрыть сундуки выглядит
как очевидный приват, но кража на этом сервере — не то, что предотвращают,
а то, что судят (Глава 1 УК, логи CoreProtect, возврат вещей по приговору).
Флаг отобрал бы у Суда половину дел и заодно сломал лавки Shopkeepers,
которые торгуют из сундука владельца.

### Три ловушки при скачивании

1. **Brewery** — качать именно **BreweryX** (живой форк). Проект `modrinth.com/plugin/brewery` —
   это Fabric-мод, на сервер он не встанет.
2. **TAB** — слаг `tab-was-taken`; по запросу «TAB» поиск Modrinth выдаёт посторонние плагины.
3. **spark** — на Modrinth лежат только Fabric/Forge/NeoForge сборки. Серверный jar — на
   `spark.lucko.me/download`, раздел Bukkit.

### Чего качать НЕ надо

**MyCommand** и **Jail** — живых сборок под 26.x нет ни на Modrinth, ни на Hangar.
Оба заменяются Skript'ом, который и так нужен проекту: почта — несколько строк скрипта,
тюрьма — готовый `docs/jail_online_time.sk` (он и по УК правильнее, считает онлайн-часы).

Мост squaremap ↔ WorldGuard для отрисовки границ государств найти не удалось —
проверить в документации squaremap либо размечать границы в игре (Конституция 4.2).

## 1b. Оптимизация — что уже сделано и что ставить

**Главное: почти вся оптимизация Paper/Purpur — конфигурационная, а не плагинная.**
В `config/paper-world-defaults.yml` включено (ключи сверены с эталонными дефолтами
Paper 15.09.2026, несуществующие удалены):

| Настройка | Что даёт |
|---|---|
| `misc.redstone-implementation: ALTERNATE_CURRENT` | редстоун в разы дешевле ванильного |
| `misc.update-pathfinding-on-block-update: false` | мобы не пересчитывают маршрут на каждый блок |
| `environment.optimize-explosions: true` | критично при `max-tnt-per-tick: 200` в spigot.yml |
| `entities.armor-stands.tick: false` | стойки брони не тикают |
| `collisions.max-entity-collisions: 2` | дешевле толпы мобов и фермы |
| `entities.spawning.per-player-mob-spawns: true` | mob-cap на игрока, а не на сервер |
| `tick-rates.mob-spawner: 2` | спавнеры считаются вдвое реже |
| `unsupported-settings.disable-world-ticking-when-empty: true` | пустой сервер не жжёт CPU |

Намеренно НЕ включено: `hopper.disable-move-event` — ускоряет воронки, но ломает
`InventoryMoveItemEvent`, на котором CoreProtect ведёт лог контейнеров. Без этого
лога разваливаются дела о кражах (Глава 1 УК).

### Плагины оптимизации

- [x] **Chunky** 1.5.3 — прогенерация чанков. Единственный по-настоящему нужный:
      генерировать мир заранее дешевле, чем на ходу под игроками.
- [x] **spark** — уже встроен в Purpur, отдельный jar не нужен.
- [ ] **FastAsyncWorldEdit** 2.15.4 (modrinth.com/plugin/fastasyncworldedit) — опционально,
      вместо обычного WorldEdit: быстрее на больших операциях. **Ставить только вместо**
      `worldedit-bukkit`, не вместе с ним.

### Чего ставить НЕЛЬЗЯ

**ClearLag, LagFixer, LagAssist и подобные.** Они «оптимизируют» тем, что чистят
дропнутые предметы и мобов по таймеру. На этом сервере алмаз — валюта, а Статьи 1–4 УК
требуют возврата вещей по решению суда. Автоочистка = уничтожение улик и чужого
имущества, причём молча. Для контроля количества сущностей используй
`entity-activation-range` и `merge-radius` в `spigot.yml`, а не автоочистку.

## 1a. Почему 26.1.2, а не 26.2

Под 26.2 **нет стабильных сборок** трёх плагинов (проверено по Modrinth, Hangar и
GitHub Releases 15.09.2026): CoreProtect 24.0 (07.07.2026), BreweryX 3.7.0 (08.05.2026)
и CPM-Paper 0.6.27a — все останавливаются на 26.1.2.

EssentialsX из этого списка уже выбыл: его **dev-билды** (2.22.1-dev, build 1827)
поддерживают 26.2, о чём сказано прямо на essentialsx.net. Стабильный 2.22.0 покрывает
26.1.2, так что сейчас берём его. Без CoreProtect не работает судебный контур целиком
(Конституция 1.2 — единственный арбитр действий), без BreweryX мертвы 13 рецептов
алкоголя, без EssentialsX — служебные телепорты Администрации.

На 26.1.2 доступен весь стек: 18 серверных плагинов и все 7 клиентских модов.

**Когда CoreProtect обновится** (версии выходят примерно раз в два месяца, 24.0 — от
07.07.2026), переход на 26.2 — это правка версии в пяти местах:
`setup.sh`, `start.sh`, `CourtBridge/pom.xml` + `plugin.yml`, `resourcepack/pack.mcmeta`
(`pack_format: 88`), `client_modpack/build_index.py` (`GAME`), затем пересборка
ресурспака и модпака скриптами и новый sha1 в `server.properties`.

Единственная формальность: ExecutableItems помечен тегами `26.1` и `26.2`, без `26.1.2` —
это особенность тегирования, jar под 26.1 работает на 26.1.2.

## 1c. Зависимости, которых не хватает

- [ ] **SCore** — жёсткая зависимость ExecutableItems (`depend: [SCore]` в его plugin.yml).
      Без неё ExecutableItems не запустится, Тетрадь Смерти не заработает.
      Качать там же, где ExecutableItems (тот же автор, ssomar).
- [ ] **PlaceholderAPI** 2.12.3 (modrinth.com/plugin/placeholderapi) — мягкая зависимость
      TAB, DecentHolograms, GSit, PlasmoVoice, LoginTo. Без неё плейсхолдеры
      в таблице игроков и голограммах останутся сырым текстом.
- [ ] **Расширения PAPI `player` и `server`** — ставятся ОТДЕЛЬНО, в самой
      PlaceholderAPI их нет:
          /papi ecloud download Player
          /papi ecloud download Server
          /papi reload
      Без них `%player_name%`, `%server_online%`, `%server_max_players%` не
      раскрываются, а показываются в меню и в таблице как есть — сырым текстом,
      и никакой ошибки в лог при этом не пишется. Проверка:
          /papi parse <ник> Онлайн: %server_online%/%server_max_players%
      Должно ответить числами. Регистрация после `papi reload` асинхронная:
      `papi list` сразу после неё ещё покажет старый набор — это нормально.
- [ ] **Vault / VaultUnlocked** 2.20.2 (modrinth.com/plugin/vaultunlocked) — проверить,
      нужен ли ChestShop для экономики. У ChestShop он в softdepend.

## 2. Версии — ПРОВЕРЕНО 2026-09-15

⚠️ Проект работает на **Minecraft 26.1.2**, а не на новейшей 26.2 — см. §1a.
Префикс `1.` Mojang убрала начиная с 26.1, поэтому «1.26.x» в любом виде неверно.

- [x] Purpur `26.1.2`, последний билд 2592 (`setup.sh` качает `latest` автоматически)
- [x] `paper-api 26.1.2.build.74-stable` — схема версий теперь `<версия>.build.<N>-stable`,
      никаких `-R0.1-SNAPSHOT`
- [x] Minecraft 26.1.2 требует **Java 25** (по манифесту Mojang), paper-api собран под
      class file 69 — в `pom.xml` выставлен target 25, `start.sh` корректен
- [x] CoreProtect 24.0 — последняя, поддерживает 26.1.2
- [x] `api-version` в `plugin.yml` = `26.1.2` (из `apiVersioning.json` внутри paper-api)
- [x] `pack_format` ресурспака = **84** (26.1.x = 84, 26.2 = 88)
- [x] Сигнатура `CoreProtectAPI.performLookup(...)` выверена по jar, CourtBridge собирается

### Дополнено 18.09.2026

- [x] 8 новых плагинов и 3 клиентских мода — список и слаги в §1,
      версии сняты с Modrinth API в тот же день
- [x] Plasmo Voice `2.1.17` на сервере и в модпаке одновременно
- [x] `build_index.py` теперь берёт последний **release**, а не просто самую
      свежую версию. Раньше он молча притащил бы в модпак FreeCam
      `1.5.0-alpha.1` вместо `1.4.1` — alpha уехала бы игрокам как
      «разрешённый на сервере мод»
- [x] ⚠️ **Найдено и исправлено:** `config/purpur.yml` и `config/spigot.yml`
      копировались в `$SERVER_DIR/config/`, а Purpur и Spigot читают их из
      корня сервера. Настройки проекта (`max-tnt-per-tick: 200`, суженные
      `entity-activation-range`, `use-alternate-keepalive`) не работали.
      Вдобавок ключа `settings.lobotomize-enabled` у Purpur не существует —
      настоящий путь `world-settings.default.mobs.villager.lobotomize.enabled`.
      Теперь оба файла — патчи, накатывает `apply_server_configs.py`
- [x] Скип ночи при 25% спящих — геймрул `playersSleepingPercentage`,
      ставится датапаком `ekb_border` (функция `ekb:init`, одноразово под
      флагом `#rules ekb`, как `#auto`)

## 3. Секреты и ID

Пошаговая инструкция по ботам, каналам и ролям: **`docs/discord_setup.md`**


- [ ] `plugins/DiscordSRV/config.yml` — `BotToken` + ID каналов: global, admin-logs, суд, военный-трибунал, консоль
- [ ] `plugins/DiscordSRV/alerts.yml:37` — `ROLE_ID_ГЛАВНЫЙ_АДМИН` (пинг при сломанном спавнере)
- [ ] `CourtBridge/src/main/resources/config.yml` — Discord Webhook канала `#суд`
- [ ] `discord_bot/.env` — DISCORD_TOKEN, CLIENT_ID, GUILD_ID, COURT_CHANNEL_ID, ADMIN_ROLE_ID
- [ ] `plugins/squaremap/config.yml:3` — реальный адрес вместо `your-server-ip`

Заполненные значения держать только на сервере: `.gitignore` защищает `.env`,
но `config.yml` плагинов отслеживаются — не коммить в них боевые токены.

## 4. Игровые решения

- [ ] Координаты тюрьмы: встать на месте тюрьмы и выполнить `/setjailpoint`
      (переменная `{jail-location}` сохраняется сама). Проверить: `/jailinfo`.
      При загрузке скрипт сам напомнит, если точка не задана
- [x] Система тюрьмы выбрана: Skript (онлайн-часы, как требует УК). Плагин Jail
      не ставится, его конфиг удалён из репозитория.
- [ ] Разметить Рыночную площадь и зарегистрировать регионы государств (`docs/state_borders_setup.sh`)
- [ ] Границы мира: поставить стадию 1 (4000 блоков) сразу после первого запуска —
      `./expand_border.sh 1`. План стадий до 20000 — в `docs/world_border.md`,
      Конституция 4.4–4.5
- [ ] Установить датапак: `cp -r datapack/ekb_border <мир>/datapacks/`, затем `/reload`
      и `/datapack list` — он открывает стадии по достижениям игроков
- [ ] Выдать админам тег для подсказок: `/tag <ник> add ekb_admin`
- [x] Мод Nirvana (конопля) НЕ ставится — вместо него `docs/nirvana.sk`. Причины две:
      на Modrinth у мода `server_side: required` (это контент-мод, а Purpur — Bukkit,
      Fabric-моды не грузит), и билды есть только под 1.20.1/1.21.1, а игра 26.1.2.
      Не «чинить» это добавлением мода в клиентский модпак: на сервере его содержимого
      всё равно нет
- [ ] Решить режим: `/function ekb:auto_off` (по умолчанию — только объявлять)
      или `/function ekb:auto_on` (расширять сразу, только если чанки прогенерированы)
- [ ] Скачать **Chunky** (modrinth.com/plugin/chunky, 1.5.3) и прогенерировать
      территорию ПЕРЕД каждым расширением — иначе лаги на новых чанках
- [ ] На стадиях 4–5 пересмотреть `backup.sh`: суточный tar.gz мира в десятки ГБ
      нежизнеспособен, нужен инкрементальный бэкап или меньший `KEEP_DAYS`

## 4a. Лицензия или пиратка (register/login) — РЕШЕНИЕ ЗА ТОБОЙ

Сейчас `server.properties:6` стоит `online-mode=true` — сервер только для лицензионных
аккаунтов, плагин авторизации НЕ нужен и ставить его нельзя.

- [ ] **Оставить online-mode=true (рекомендуется).** Никаких `/register` и `/login`,
      ники уникальны, UUID выдаёт Mojang. Для проекта с судом это принципиально:
      CoreProtect, Jail, LuckPerms и дела в `cases.json` привязаны к UUID/нику, а на
      пиратке ник может занять кто угодно — вся доказательная база рассыпается.
- [ ] **Или перейти на пиратку:** `online-mode=false` + **AuthMeReloaded 6.0.1**
      (есть под 26.1.2, modrinth.com/plugin/authmereloaded). Тогда обязательно:
      - закрыть порт 25565 файрволом от прямых подключений в обход прокси, иначе
        любой может зайти под ником администрации (online-mode=false = нет проверки);
      - решить, что делать с уже накопленными UUID — при смене режима они меняются,
        история CoreProtect и права LuckPerms по старым UUID теряются;
      - привязка Discord↔Minecraft в DiscordSRV станет менее надёжной.

Вывод: пиратка даёт больше игроков, но ломает Статью 1.2 Конституции — CoreProtect
перестаёт быть надёжным арбитром, если ник не гарантирует личность.

## 5. Ресурспак

### Куда заливать

**https://mc-packs.net/** — бесплатный хостинг ресурспаков без регистрации.
Порядок:

1. Пересобрать: `py -3 pack_resourcepack.py`.
2. Открыть mc-packs.net, закинуть `shield_resourcepack_26.1.2.zip`.
   Автоматизировать нельзя — там CAPTCHA.
3. Сайт отдаст готовые строки `resource-pack` и `resource-pack-sha1` —
   скопировать ОБЕ в `server.properties`.

⚠️ **sha1 брать ИЗ ССЫЛКИ, а не из вывода `pack_resourcepack.py`.**
mc-packs перепаковывает zip (добавляет записи каталогов), содержимое файлов
при этом то же, а хеш другой. Имя файла в ссылке и есть нужный sha1:
`https://download.mc-packs.net/pack/<sha1>.zip`.

⚠️ При `require-resource-pack=true` расхождение хеша с файлом закрывает
вход ВСЕМ. Поэтому сначала заливка, потом правка `server.properties`,
а не наоборот.

Свой веб-сервер тоже годится — нужен прямой HTTP(S)-линк на .zip
без редиректов и страницы-прокладки. Тогда sha1 останется тот, что
печатает `pack_resourcepack.py`. Готовый веб-сервер у нас уже есть —
squaremap на порту 8080, но раздавать с него пак нельзя: он отдаёт
только свою папку с картой.

- [x] ~~Пак собран и залит 18.09.2026:~~
      https://download.mc-packs.net/pack/04f45a4edb2a4c8e887d642160e54b006de890c6.zip
      104 файла, 160 моделей, 37 текстур, включая шесть артефактов
      (CMD 3001-3006). URL и sha1 вписаны в `server.properties`.
      Залитый архив скачан обратно и сверен: содержимое всех 104
      файлов совпадает с локальной сборкой байт в байт.
      ⚠ sha1 у залитого другой, чем у собранного (`caec4048…`): mc-packs
      перепаковывает zip. В `server.properties` должен стоять хеш ИЗ ССЫЛКИ.
- [ ] Лицензия: текстуры 2001–2012 взяты из ассетов мода Nirvana, а они All Rights Reserved
      (MIT в `LICENSE_Nirvana.md` покрывает только код). Спросить разрешение у TeamGalena
      либо заменить эти 12 файлов своим артом
- [x] ~~Пак собран и залит: https://download.mc-packs.net/pack/59c020c34312eddb36493ecfdca06f648e8fd35e.zip~~
      (пак от 5 бутылок; sha1 залитого архива отличался от собранного скриптом — mc-packs
      перепаковывает zip, добавляя записи каталогов, содержимое файлов при этом идентично)
- [ ] Если пак будешь менять: пересобрать `py -3 pack_resourcepack.py`, залить заново
      и вписать НОВЫЙ sha1 — при `require-resource-pack=true` расхождение закрывает вход всем

## 6. Сборка компонентов

- [x] `CourtBridge` СОБРАН: `CourtBridge/target/CourtBridge.jar` (JDK 25, class file 69).
      Сигнатура `performLookup` выверена по CoreProtect 24.0 и исправлена в `fetchLogs()`;
      `ParseResult.getWorldName()` не существует — заменено на `worldName()`.
- [ ] Скопировать `CourtBridge/target/CourtBridge.jar` в `plugins/` на сервере
- [ ] Проверить `/courtlog` в игре — API-вызов компилируется, но в бою не проверялся
- [ ] `cd discord_bot && npm install && npm run deploy && npm start`
- [x] `client_modpack/modrinth.index.json` заполнен реальными данными из Modrinth API
      (7 модов под 26.1.2/Fabric + fabric-loader 0.19.5). Пересобрать при обновлении модов:
      `cd client_modpack && py -3 build_index.py modrinth.index.json`
- [x] Пак собран: `ekb_shield_client.mrpack` (1.8 КБ, Minecraft 26.1.2) — ссылки проверены,
      размеры сходятся с индексом. Пересборка: `cd client_modpack && py -3 pack.py`
- [x] Собран второй пак `ekb_shield_client_26.2.mrpack` для клиентов 26.2 (заходят
      через ViaVersion). Ссылки обоих паков проверены HEAD-запросом
- [ ] Раздать игрокам `ekb_shield_client.mrpack` (26.1.2) и проверить установку
- [ ] ПЕРЕД раздачей 26.2-пака проверить на тестовом клиенте: применяется ли ресурспак
      (у сервера pack_format 84, у клиента 26.2 ожидается 88) и работают ли Plasmo Voice
      и CPM через ViaVersion. Если нет — раздавать только 26.1.2

## 6a. Проверка перед первым запуском

- [ ] Прогнать на сервере `./check_server.sh` — он проверяет Java, ядро, EULA, наличие
      всех обязательных плагинов, конфиги, anti-xray, Skript-скрипты, датапак и
      незаполненные секреты. Ничего не меняет, только докладывает.
      Путь можно переопределить: `SERVER_DIR=/иной/путь ./check_server.sh`

## 7. Эксплуатация хоста

- [ ] Запускать сервер как `screen -dmS minecraft ./start.sh` (имя сессии ждут purge.sh и backup.sh)
- [ ] Поставить `backup.sh` в cron: `0 5 * * * /home/minecraft/server/backup.sh >> /home/minecraft/backup.log 2>&1`
- [ ] Проверить, что на диске хватает места под бэкап мира (purge.sh проверяет сам и откажется стартовать)
- [ ] Автоперезапуск при падении (systemd-юнит или цикл-обёртка) — сейчас его нет
- [x] JVM-флаги: набор Aikar для heap >= 12 ГБ (`start.sh`). При смене `-Xmx`
      правь и `G1NewSizePercent`/`G1MaxNewSizePercent`/`G1HeapRegionSize`
- [x] Anti-Xray настроен в `config/paper-world-defaults.yml` (engine-mode 2, Обычный мир).
      Отдельный плагин не нужен — это встроенная функция Paper
- [ ] Скопировать per-world конфиги anti-xray для Ада и Края — готовые блоки
      закомментированы в конце `config/paper-world-defaults.yml`

## 8. Проверить на тестовом сервере

- [ ] Все 13 рецептов Brewery → модели 1001–1013 отображаются
- [ ] Тетрадь Смерти (CMD 6666), механика в `docs/death_note.sk`:
      `/deathnote give random` выдаёт тетрадь со страницей правил; имя пишется со 2-й страницы
      и вступает в силу по кнопке **Подписать**; второе имя в тот же кулдаун отклоняется;
      стёртое имя возвращается на место при следующей подписи; `/deathnote find` находит тетрадь
      и в эндер-сундуке; `/deathnote reclaim <ник>` у оффлайн-игрока после суток простоя
      открывает `/oi` и `/oe`
- [x] Кулдаун настраивается на ходу: `/deathnote cooldown <часы>` (по умолчанию 5 ч),
      хранится в `{deathnote::cooldown}`. Проверено: 5 ч -> 2 ч, `/deathnote info` показывает новое
- [x] Тетрадей на сервере не больше двух: третья выдача отклоняется с подсказкой про `reclaim`.
      Счётчик `{deathnote::issued}` правится через `/deathnote setcount <n>`, если разошёлся
- [ ] Отрезвление: «Рассол» (1014) снимает опьянение, молоко снимает 25 %, мёд 15 %
- [ ] Конопля (`nirvana.sk`, CMD 2001–2012), полный цикл:
      семена из травы в джунглях → посадка на грядку → сбор даёт коноплю, а не пшеницу →
      ПКМ коноплёй по горящему костру даёт шишку → шишка + бумага во второй руке = самокрутка →
      ПКМ самокруткой поднимает «Умиротворение», мобы перестают брать игрока в цель,
      с 3-го уровня приходит тошнота, с 5-го — обкуренные крипера
- [ ] Ткацкий станок: 4 конопли → ткань; 6 тканей → 2 кожи; в присяде 5 тканей → двухкозырка;
      конопля + 2 верёвки во второй руке → поводок
- [ ] Запреты работают: конопля не ставится на землю как тростник, шишка не съедается
      как водоросли (иначе предмет теряет CMD)
- [ ] `/nirvana give <ник> <предмет>` выдаёт все 12 предметов, `/nirvana cleanup` не падает
- [x] Право на выдачу — отдельная нода `ekb.nirvana.admin` (не `coreprotect.rollback`):
      выдана `admin` и `restricted_admin`, у `default` стоит явный минус. Обычным игрокам
      выдача закрыта намеренно — цены прайс-листа держатся на дефиците семян
- [ ] Кожаные шлемы не обесцветились (проверить крашеный шлем: `items/leather_helmet.json`
      мы НЕ трогали, Двухкозырка сидит на кольчуге)
- [ ] `/nirvana` без аргументов открывает меню на 4 ряда: 12 предметов конопли и 13 напитков;
      клик выдаёт 1 шт., клик в присяде — 16 шт., клик по бутылке дёргает `/brew create`.
      В поиске творческого режима этих предметов нет и не будет — это не баг, меню его и заменяет
- [ ] SuperVanish: обычный игрок не видит админа в `/v`; `restricted_admin` не видит
      главного админа (нода `-sv.see`); мобы не агрятся на невидимого
- [ ] OpenInv: `restricted_admin` может ПОСМОТРЕТЬ инвентарь, но не изменить
      (`-OpenInv.editinv`) — изъятие краденого только по решению Суда
- [ ] `/mailsend`, `/courtlog <ник> 120 50 7`, `/иск` → `/дела` → `/закрыть_дело`
- [ ] `purge.sh` на тестовом мире — целиком, включая откат и перезапуск
