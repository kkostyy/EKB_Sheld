# Карта меню EKB SHIELD

⚠️ ФАЙЛ СОБИРАЕТСЯ ГЕНЕРАТОРОМ — `py -3 build_menu_map.py`.
Руками не править: карта правилась вручную и поэтому врала
(стояло 32 меню и 360 кнопок, когда в игре было 40 и 430).

- меню: **49**, кнопок: **512**
- правка меню: `menus_spec.py` → `py -3 build_menus.py --install` → `/dm reload`
- проверка: `py -3 check_menus.py`

В квадратных скобках — право, без которого раздел не виден.

## Дерево

```
EKB SHIELD   /menu /меню
├─ Профиль   /profile /профиль
│  ├─ Контракты   /contracts /контракты
│  ├─ Личина   /masks /маски
│  ├─ Теневой Рынок   /blackmarket   [ekb.shadow.member]
│  ├─ Гражданин государства   /citizen /гражданин   [ekb.menu.citizen]
│  ├─ Житель Спавна (город САП)   /capital /спавн   [ekb.menu.capital]
│  │  └─ Стойка бара   /barshop /стойка
│  └─ Кочевник   /nomad /кочевник
├─ Торговля   /trade /торговля /shops
│  ├─ Торговая Коллегия   /market /коллегия
│  ├─ Ламповая Почта   /pochta /почта
│  └─ Бар и кости   /casino /казино
├─ Мир   /world /мир
│  ├─ Город   /town /город
│  │  ├─ Настройки города
│  │  ├─ Уровни власти
│  │  └─ Наёмники САП   /mercs /наёмники
│  ├─ Газета   /press /пресса
│  └─ Кровавый Сон
├─ Законы   /laws /законы
│  ├─ Шериф   /sheriff /шериф   [ekb.duty.sheriff]
│  └─ Криминалистика   /forensics /улики
├─ Служба   /duty /служба
│  ├─ Администрация   /adminmenu /амену   [ekb.menu.admin]
│  │  ├─ Суд и логи   [ekb.menu.admin]
│  │  ├─ Тюрьма   [ekb.menu.admin]
│  │  ├─ Предметы и вещества   /items /предметы   [ekb.menu.admin]
│  │  │  ├─ Тёмная Тетрадь Смерти   /deathnotemenu   [ekb.deathnote.admin]
│  │  │  ├─ Каталог вещей   /allitems /вещи /newitems /новое   [ekb.menu.admin]
│  │  │  │  ├─ Конопля   /herbs /конопля   [ekb.menu.admin]
│  │  │  │  ├─ Напитки   /drinks /напитки /bar /бар   [ekb.menu.admin]
│  │  │  │  ├─ Стволы   /guns /стволы   [ekb.menu.admin]
│  │  │  │  └─ Настольные игры   /tables /настолки   [ekb.menu.admin]
│  │  │  └─ Особые артефакты   /artifacts /артефакты   [ekb.menu.admin]
│  │  ├─ Мир и границы   [ekb.menu.admin]
│  │  └─ Сервис сервера   [ekb.menu.admin]
│  ├─ Помощник администратора   /helpermenu /хмену   [ekb.menu.helper]
│  ├─ Судья   /judge /судья   [ekb.menu.judge]
│  ├─ Врач Клиники   /doctor /врач   [ekb.menu.doctor]
│  ├─ Строительная бригада   /brigade /бригада   [ekb.duty.builder]
│  ├─ Почта   /postman /почтальон   [ekb.duty.postman]
│  ├─ Приказчик Мэрии   /clerk /приказчик   [ekb.duty.clerk]
│  ├─ Бармен   /barman /бармен   [ekb.duty.barman]
│  ├─ Крупье   /dealer /крупье   [ekb.duty.dealer]
│  ├─ Следователь   /detective /следователь   [ekb.duty.detective]
│  └─ Тёмное ремесло   /assassin /ремесло
├─ С чего начать   /start /начать
└─ Вызвать службу   /call /вызов
```

## Что внутри каждого меню

### EKB SHIELD
*`main.yml` · 12 кнопок · `/menu`, `/меню`*

- **EKB SHIELD**
- **Профиль** — → ekb_profile
- **Торговля** — → ekb_trade
- **Мир** — → ekb_world
- **Законы** — → ekb_laws
- **Службы** — → ekb_duty
- **С чего начать** — → ekb_start
- **Кто в сети** — `/list`
- **Канал чата** — `/l`, ПКМ: `/g`
- **Табло сбоку** — `/hud`
- **Вызвать службу** — → ekb_calls, ПКМ: текст в чат
- **Закрыть**

### Администрация
*`admin.yml` · 16 кнопок · `/adminmenu`, `/амену` · право `ekb.menu.admin`*

- **Администрация (САП)**
- **Суд и логи** — → ekb_admin_court
- **Тюрьма** — → ekb_admin_jail
- **Предметы и вещества** — → ekb_admin_items
- **Мир и границы** — → ekb_admin_world
- **Сервис** — → ekb_admin_service
- **Казна: установка** — текст в чат, ПКМ: `/treasury`
- **Границы государств** — текст в чат, ПКМ: `/borders`
- **Теневой Рынок: точка** — текст в чат
- **Роли и права** — `/ekbroles`
- **Справочник** — `/ahelp`
- **Чужие инвентари** — `/ekbmenu inv`, ПКМ: `/ekbmenu ender`
- **Ваниш** — `/sv`
- **TPS** — `/spark tps`
- **Назад** — → ekb_duty
- **Закрыть**

### Бар и кости
*`casino.yml` · 6 кнопок · `/casino`, `/казино`*

- **Азартный уголок Бармена**
- **Игра в кости** — `/dice`
- **Что наливают** — `/barmenu`
- **Стойка бара** — → ekb_barshop
- **Назад** — → ekb_trade
- **Закрыть**

### Бармен
*`barman.yml` · 9 кнопок · `/barman`, `/бармен` · право `ekb.duty.barman`*

- **Бармен Спавна**
- **Вытрезвить гостя** — `/ekbmenu sober`
- **Состояние гостя** — `/ekbmenu info`
- **Стойка Спавна** — → ekb_barshop
- **Прайс в чат** — `/barmenu`
- **Как варить своё** — текст в чат
- **Мои лавки** — `/shopkeeper list`
- **Назад** — → ekb_duty
- **Закрыть**

### Врач Клиники
*`doctor.yml` · 10 кнопок · `/doctor`, `/врач` · право `ekb.menu.doctor`*

- **Осмотр пациента** — `/ekbmenu info`
- **Курс лечения** — `/ekbmenu heal`
- **Облегчить симптомы**
- **Вытрезвитель** — `/ekbmenu sober`
- **Как устроена зависимость**
- **Порядок приёма**
- **Выезд к пациенту**
- **Прайс Клиники** — → ekb_laws
- **Назад** — → ekb_duty
- **Закрыть**

### Вызвать службу
*`calls.yml` · 9 кнопок · `/call`, `/вызов`*

- **Вызов службы**
- **Вызвать медика** — `/call medic`
- **Вызвать Суд** — `/call court`
- **Вызвать шерифа** — `/call sheriff`
- **Строительная бригада** — `/call builder`
- **Почтальон** — `/call post`
- **Открытые заявки** — `/calls`
- **Назад** — → ekb_main
- **Закрыть**

### Газета
*`press.yml` · 8 кнопок · `/press`, `/пресса`*

- **EKB SHIELD Times**
- **Свежий выпуск** — `/news`
- **Купить копию** — `/newsbuy`
- **Сдать выпуск** — `/newsissue`  `[ekb.duty.journalist]`
- **Экстренная новость** — текст в чат  `[ekb.duty.journalist]`
- **Анонс эфира** — текст в чат  `[ekb.media.streamer]`  `[ekb.media.youtuber]`
- **Назад** — → ekb_world
- **Закрыть**

### Город
*`town.yml` · 14 кнопок · `/town`, `/город`*

- **Город**
- **Мой город** — `/clan info`
- **Основатель города** — текст в чат
- **Настройки города** — → ekb_town_settings
- **Жители** — текст в чат
- **Чат города** — `/cc toggle`, ПКМ: текст в чат
- **Уровни власти** — → ekb_town_gov
- **Форма правления** — `/regime`, ПКМ: `/regime list`
- **Очки города** — `/clan points`, ПКМ: `/clan playerpoints`
- **Города сервера** — `/clan list`, ПКМ: `/topclans`
- **Наёмники САП** — → ekb_mercenaries
- **Почему нет /clan home**
- **Назад** — → ekb_world
- **Закрыть**

### Гражданин государства
*`citizen.yml` · 10 кнопок · `/citizen`, `/гражданин` · право `ekb.menu.citizen`*

- **Твоё государство**
- **Земля и границы**
- **Война и нейтралитет**
- **Неактивность**
- **Защита в Суде** — → ekb_laws
- **Торговля**
- **Связь с другими** — текст в чат
- **Моё состояние** — `/addiction`
- **Назад** — → ekb_profile
- **Закрыть**

### Житель Спавна (город САП)
*`capital.yml` · 10 кнопок · `/capital`, `/спавн` · право `ekb.menu.capital`*

- **Спавн, база САП**
- **Рыночная Площадь** — → ekb_market
- **Мэрия** — `/arenda`, ПКМ: `/treasury`
- **Клиника** — `/addiction`
- **Бар** — → ekb_barshop
- **Ламповая Почта** — → ekb_pochta
- **Суд и тюрьма** — текст в чат
- **Законы** — → ekb_laws
- **Назад** — → ekb_main
- **Закрыть**

### Законы
*`laws.yml` · 10 кнопок · `/laws`, `/законы`*

- **Законы**
- **Конституция** — текст в чат
- **Уголовный кодекс** — текст в чат
- **Как судят** — текст в чат
- **Цены** — текст в чат
- **Шериф Спавна** — → ekb_sheriff
- **Криминалистика** — → ekb_forensics
- **Подать иск** — текст в чат
- **Назад** — → ekb_main
- **Закрыть**

### Каталог вещей
*`allitems.yml` · 9 кнопок · `/allitems`, `/вещи`, `/newitems`, `/новое` · право `ekb.menu.admin`*

- **Каталог вещей сервера**
- **Конопля** — → ekb_herbs
- **Напитки** — → ekb_drinks
- **Особые артефакты** — → ekb_artifacts
- **Тетрадь Смерти** — → ekb_deathnote
- **Стволы** — → ekb_guns
- **Настольные игры** — → ekb_tables
- **Назад** — → ekb_admin_items
- **Закрыть**

### Конопля
*`herbs.yml` · 20 кнопок · `/herbs`, `/конопля` · право `ekb.menu.admin`*

- **Конопля и снадобья**
- **Семена конопли** — `/giveherb seeds 1`, ПКМ: `/giveherb seeds 16`
- **Конопля** — `/giveherb hemp 1`, ПКМ: `/giveherb hemp 16`
- **Шишка** — `/giveherb weed 1`, ПКМ: `/giveherb weed 16`
- **Конопляная ткань** — `/giveherb cloth 1`, ПКМ: `/giveherb cloth 16`
- **Мешковина** — `/giveherb burlap 1`, ПКМ: `/giveherb burlap 16`
- **Самокрутка** — `/giveherb joint 1`, ПКМ: `/giveherb joint 16`
- **Старая трубка** — `/giveherb pipe 1`, ПКМ: `/giveherb pipe 16`
- **Набитая трубка** — `/giveherb stuffed_pipe 1`, ПКМ: `/giveherb stuffed_pipe 16`
- **Подозрительная трубка** — `/giveherb pipe_suspicious 1`, ПКМ: `/giveherb pipe_suspicious 16`
- **Тлеющая трубка** — `/giveherb pipe_smouldering 1`, ПКМ: `/giveherb pipe_smouldering 16`
- **Бонг (пустой)** — `/giveherb empty_bong 1`, ПКМ: `/giveherb empty_bong 16`
- **Бонг** — `/giveherb bong 1`, ПКМ: `/giveherb bong 16`
- **Травяная мазь** — `/giveherb salve 1`, ПКМ: `/giveherb salve 16`
- **Брауни** — `/giveherb brownie 1`, ПКМ: `/giveherb brownie 16`
- **Двухкозырка** — `/giveherb deerstalker 1`, ПКМ: `/giveherb deerstalker 16`
- **ТГК** — `/giveherb thc 1`, ПКМ: `/giveherb thc 16`
- **Прибраться в метках** — `/nirvana cleanup`
- **Назад** — → ekb_allitems
- **Закрыть**

### Контракты
*`contracts.yml` · 8 кнопок · `/contracts`, `/контракты`*

- **Контракты на устранение**
- **Доска контрактов** — `/ctmenu board`, ПКМ: `/contract board`
- **Заказать устранение** — `/ctmenu`
- **Мои дела** — `/contract mine`
- **Что говорит закон** — текст в чат
- **Если ты видел убийство** — текст в чат
- **Назад** — → ekb_profile
- **Закрыть**

### Кочевник
*`nomad.yml` · 10 кнопок · `/nomad`, `/кочевник`*

- **Кто такой кочевник**
- **Нейтральные земли**
- **Как стать гражданином**
- **Статус беженца**
- **Чего избегать**
- **Жизнь в дороге**
- **Торговля и заработок**
- **Моё состояние** — `/addiction`
- **Назад** — → ekb_profile
- **Закрыть**

### Криминалистика
*`forensics.yml` · 7 кнопок · `/forensics`, `/улики`*

- **Криминалистическая экспертиза**
- **Осмотреть место** — `/expertise`
- **Открытые происшествия** — `/crimescenes`  `[coreprotect.rollback]`
- **Подать обвинение** — текст в чат
- **Логи CoreProtect** — текст в чат  `[coreprotect.lookup]`
- **Назад** — → ekb_duty
- **Закрыть**

### Кровавый Сон
*`bloodnight.yml` · 6 кнопок*

- **Кровавый Сон**
- **Что это и когда** — `/bloodnight`
- **Как подготовиться**
- **Назначить Сон** — текст в чат  `[coreprotect.rollback]`
- **Назад** — → ekb_world
- **Закрыть**

### Крупье
*`dealer.yml` · 10 кнопок · `/dealer`, `/крупье` · право `ekb.duty.dealer`*

- **Крупье**
- **Колода** — `/givetable card`
- **Фишки** — `/givetable chip`
- **Кубики** — `/givetable dice`
- **Доска и фигуры** — `/givetable board`, ПКМ: `/givetable chess`
- **Домино и нарды** — `/givetable domino`, ПКМ: `/givetable nardy`
- **Кости заведения** — `/dice`
- **Почему всё бумажное**
- **Назад** — → ekb_duty
- **Закрыть**

### Ламповая Почта
*`pochta.yml` · 7 кнопок · `/pochta`, `/почта`*

- **Ламповая Почта**
- **Отправить письмо** — текст в чат
- **Отправить посылку** — текст в чат
- **Мой ящик** — `/mailbox`
- **Выбросить письма** — `/mailclear`
- **Назад** — → ekb_trade
- **Закрыть**

### Личина
*`masks.yml` · 7 кнопок · `/masks`, `/маски`*

- **Гардероб и Личина**
- **Надеть или снять Личину** — `/disguise`
- **Чего Личина НЕ даёт**
- **Обычные скины** — `/skins`, ПКМ: `/skin clear`
- **Теневой Рынок** — → ekb_blackmarket
- **Назад** — → ekb_profile
- **Закрыть**

### Мир
*`world.yml` · 13 кнопок · `/world`, `/мир`*

- **Мир**
- **Веб-карта**
- **Границы государств** — `/borders`
- **Граница мира** — текст в чат
- **Кто в сети** — `/list`
- **Города сервера** — `/clan list`, ПКМ: `/topclans`
- **Спавн** — → ekb_capital
- **Город** — → ekb_town
- **Газета** — → ekb_press
- **Кровавый Сон** — → ekb_bloodnight
- **Discord** — текст в чат
- **Назад** — → ekb_main
- **Закрыть**

### Мир и границы
*`admin_world.yml` · 8 кнопок · право `ekb.menu.admin`*

- **Стадия границы** — `/function ekb:status`
- **Расширять автоматически** — `/function ekb:auto_on`
- **Только объявлять** — `/function ekb:auto_off`
- **Прогенерация (Chunky)** — текст в чат
- **Ручное расширение**
- **Погода и время** — `/weather clear`
- **Назад** — → ekb_admin
- **Закрыть**

### Напитки
*`drinks.yml` · 17 кнопок · `/drinks`, `/напитки`, `/bar`, `/бар` · право `ekb.menu.admin`*

- **Напитки BreweryX**
- **Мохито** — `/givedrink mojito 10`, ПКМ: `/givedrink mojito 2`
- **Разливное Фирменное** — `/givedrink firm_beer 10`, ПКМ: `/givedrink firm_beer 2`
- **Маракуйевая водка** — `/givedrink passionfruit 10`, ПКМ: `/givedrink passionfruit 2`
- **Деревенский самогон** — `/givedrink village_samogon 10`, ПКМ: `/givedrink village_samogon 2`
- **Водка** — `/givedrink vodka_plain 10`, ПКМ: `/givedrink vodka_plain 2`
- **Мексиканская Текила** — `/givedrink tequila 10`, ПКМ: `/givedrink tequila 2`
- **Шведская водка** — `/givedrink vodka_absolut 10`, ПКМ: `/givedrink vodka_absolut 2`
- **Капитанский Ром** — `/givedrink rum 10`, ПКМ: `/givedrink rum 2`
- **Егермейстер Orange** — `/givedrink jager_orange 10`, ПКМ: `/givedrink jager_orange 2`
- **Теннессийский виски** — `/givedrink tennessee_whiskey 10`, ПКМ: `/givedrink tennessee_whiskey 2`
- **Ликёр Егермейстер** — `/givedrink jagermeister 10`, ПКМ: `/givedrink jagermeister 2`
- **Егермейстер Охотничий** — `/givedrink jager_dark 10`, ПКМ: `/givedrink jager_dark 2`
- **Админский самогон** — `/givedrink admin_samogon 10`, ПКМ: `/givedrink admin_samogon 2`
- **Рассол** — `/givedrink rassol 10`, ПКМ: `/givedrink rassol 2`
- **Назад** — → ekb_allitems
- **Закрыть**

### Настольные игры
*`tables.yml` · 12 кнопок · `/tables`, `/настолки` · право `ekb.menu.admin`*

- **Наборы TablePlays**
- **Кубик** — `/givetable dice`
- **Игральная карта** — `/givetable card`
- **Фишка** — `/givetable chip`
- **Домино** — `/givetable domino`
- **Шахматная фигура** — `/givetable chess`
- **Шашка** — `/givetable checker`
- **Доска** — `/givetable board`
- **Нарды** — `/givetable nardy`, ПКМ: `/givetable nardyboard`
- **Как это устроено**
- **Назад** — → ekb_allitems
- **Закрыть**

### Настройки города
*`town_settings.yml` · 13 кнопок*

- **Настройки города**
- **Граница государства** — текст в чат, ПКМ: `/borders`
- **Чат города** — `/clanchat`
- **Префикс города** — текст в чат
- **Союзники** — текст в чат
- **Враги** — текст в чат
- **PvP между своими** — `/clan pvp`
- **Передать город** — текст в чат
- **Распустить город** — текст в чат
- **Должности в городе** — → ekb_town_gov
- **Казна города** — `/treasury`
- **Назад** — → ekb_town
- **Закрыть**

### Наёмники САП
*`mercenaries.yml` · 8 кнопок · `/mercs`, `/наёмники`*

- **Как это работает**
- **Охрана каравана** — консоль: `say &c[НАЁМ] &f%player_name% &7бронирует: &fОхрана каравана &8(64–96💎)`, текст в чат
- **Участие в войне** — консоль: `say &c[НАЁМ] &f%player_name% &7бронирует: &fУчастие в войне &8(256–384💎)`, текст в чат
- **Строительные работы** — консоль: `say &c[НАЁМ] &f%player_name% &7бронирует: &fСтроительные работы`, текст в чат
- **Конвой заключённого**
- **Заказ на игрока**
- **Назад** — → ekb_town
- **Закрыть**

### Особые артефакты
*`artifacts.yml` · 12 кнопок · `/artifacts`, `/артефакты` · право `ekb.menu.admin`*

- **Особые артефакты**
- **Компас Охотника** — `/giveartifact compass`
- **Кинжал Теневого Шага** — `/giveartifact dagger`
- **Песочные Часы** — `/giveartifact hourglass`
- **Журнал Контрабандиста** — `/giveartifact journal`
- **Чёрная Метка** — `/giveartifact mark`
- **Маска Безликого** — `/giveartifact mask`
- **Кто чем владеет** — `/artifact list`
- **Найти экземпляры** — `/artifact find`
- **Списать пропавший** — текст в чат
- **Назад** — → ekb_admin_items
- **Закрыть**

### Помощник администратора
*`helper.yml` · 13 кнопок · `/helpermenu`, `/хмену` · право `ekb.menu.helper`*

- **Инспектор CoreProtect** — `/co i`
- **Поиск по логам** — текст в чат
- **Заглянуть в инвентарь** — `/ekbmenu inv`, ПКМ: `/ekbmenu ender`
- **Ваниш** — `/sv`
- **Служебные телепорты** — текст в чат
- **TPS сервера** — `/spark tps`
- **Бар** — текст в чат
- **Режим игры** — `/gmc`, ПКМ: `/gms`
- **Что тебе закрыто**
- **Наблюдатель** — `/gmsp`, ПКМ: `/gms`
- **Роли и права** — `/ekbroles`
- **Назад** — → ekb_duty
- **Закрыть**

### Почта
*`postman.yml` · 8 кнопок · `/postman`, `/почтальон` · право `ekb.duty.postman`*

- **Почтальон**
- **Заявки на доставку** — `/calls`
- **Отправить письмо** — текст в чат
- **Очистить свою почту** — `/mailclear`
- **Комплект Ламповой Почты**
- **Куда нести** — `/clan list`
- **Назад** — → ekb_duty
- **Закрыть**

### Предметы и вещества
*`admin_items.yml` · 9 кнопок · `/items`, `/предметы` · право `ekb.menu.admin`*

- **Предметы и вещества**
- **Тетрадь Смерти** — → ekb_deathnote
- **Зависимость** — `/ekbmenu heal`, ПКМ: `/ekbmenu info`
- **Каталог вещей** — → ekb_allitems
- **Особые артефакты** — → ekb_artifacts
- **Голограммы рынка** — `/markethologramlist`, ПКМ: текст в чат
- **Каталог голов** — `/headdb`
- **Назад** — → ekb_admin
- **Закрыть**

### Приказчик Мэрии
*`clerk.yml` · 9 кнопок · `/clerk`, `/приказчик` · право `ekb.duty.clerk`*

- **Приказчик Мэрии**
- **Казна Спавна** — `/treasury`, ПКМ: `/treasurylog`
- **Арендаторы** — `/arenda список`
- **Скупщик** — `/skupka`
- **Доска лотов** — `/lots`
- **Заявки в Мэрию** — `/calls`
- **Торговая Коллегия** — → ekb_market
- **Назад** — → ekb_duty
- **Закрыть**

### Профиль
*`profile.yml` · 20 кнопок · `/profile`, `/профиль`*

- **Профиль**
- **Скины** — `/skins`, ПКМ: `/skin clear`
- **Скин по нику** — текст в чат
- **Куда выйти из тюрьмы** — `/freedom`
- **Состояние** — `/addiction`
- **Почта** — текст в чат, ПКМ: `/mailclear`
- **Контракты** — → ekb_contracts
- **Личина** — → ekb_masks
- **Теневое Сообщество** — → ekb_blackmarket  `[ekb.shadow.member]`
- **Анонс эфира** — текст в чат  `[ekb.media.streamer]`  `[ekb.media.youtuber]`
- **Поза** — `/gsit`, ПКМ: `/glay`
- **Нести на руках** — текст в чат
- **Сообщить о баге** — текст в чат
- **Мои жалобы** — `/myreports`, ПКМ: текст в чат
- **Чёрный список** — текст в чат
- **Гражданство** — → ekb_citizen  `[ekb.menu.citizen]`
- **Житель Спавна** — → ekb_capital  `[ekb.menu.capital]`
- **Кочевник** — → ekb_nomad
- **Назад** — → ekb_main
- **Закрыть**

### С чего начать
*`start.yml` · 11 кнопок · `/start`, `/начать`*

- **Первые шаги**
- **1. Пережить первую ночь**
- **2. Поставить кровать**
- **3. Прочитать законы** — → ekb_laws
- **4. Заработать первые алмазы** — → ekb_trade
- **5. Найти город или основать свой** — → ekb_town
- **6. Открыть лавку** — → ekb_trade
- **Где мы вообще** — → ekb_world
- **7. Знать, куда идти за правдой** — текст в чат
- **Назад** — → ekb_main
- **Закрыть**

### Сервис сервера
*`admin_service.yml` · 8 кнопок · право `ekb.menu.admin`*

- **TPS и здоровье сервера** — `/spark tps`
- **Сохранить мир** — консоль: `save-all`
- **Права (LuckPerms)** — `/lp editor`
- **Скрипты (Skript)** — текст в чат
- **Меню (DeluxeMenus)** — `/dm reload`
- **С консоли хоста**
- **Назад** — → ekb_admin
- **Закрыть**

### Следователь
*`detective.yml` · 8 кнопок · `/detective`, `/следователь` · право `ekb.duty.detective`*

- **Следователь**
- **Открытые происшествия** — `/crimescenes`
- **Осмотреть место** — `/expertise`
- **Инспектор блоков** — `/co i`
- **Подать обвинение** — текст в чат
- **Раздел криминалистики** — → ekb_forensics
- **Назад** — → ekb_duty
- **Закрыть**

### Служба
*`duty.yml` · 17 кнопок · `/duty`, `/служба`*

- **Служба**
- **Администрация** — → ekb_admin  `[ekb.menu.admin]`
- **Помощник админа** — → ekb_helper  `[ekb.menu.helper]`
- **Судья** — → ekb_judge  `[ekb.menu.judge]`
- **Врач Клиники** — → ekb_doctor  `[ekb.menu.doctor]`
- **Шериф Спавна** — → ekb_sheriff  `[ekb.duty.sheriff]`
- **Бригадир строителей** — → ekb_builder  `[ekb.duty.builder]`
- **Почтальон** — → ekb_postman  `[ekb.duty.postman]`
- **Приказчик Мэрии** — → ekb_clerk  `[ekb.duty.clerk]`
- **Бармен** — → ekb_barman  `[ekb.duty.barman]`
- **Крупье** — → ekb_dealer  `[ekb.duty.dealer]`
- **Следователь** — → ekb_detective  `[ekb.duty.detective]`
- **Газета** — → ekb_press
- **Тёмное ремесло** — → ekb_assassin
- **Вызвать службу** — → ekb_calls
- **Назад** — → ekb_main
- **Закрыть**

### Стволы
*`guns.yml` · 11 кнопок · `/guns`, `/стволы` · право `ekb.menu.admin`*

- **Оружие QualityArmory**
- **AK47** — `/givegun ak47`
- **AWP** — `/givegun awp`
- **Deagle** — `/givegun deagle`
- **SPAS-12** — `/givegun spas12`
- **Патроны 762** — `/givegun 762 64`
- **Патроны 9mm** — `/givegun 9mm 64`
- **Патроны shell** — `/givegun shell 64`
- **Все 70 стволов** — текст в чат
- **Назад** — → ekb_allitems
- **Закрыть**

### Стойка бара
*`barshop.yml` · 17 кнопок · `/barshop`, `/стойка`*

- **Стойка Спавна**
- **Мохито** — `/barbuy mojito`
- **Разливное Фирменное** — `/barbuy firm_beer`
- **Рассол** — `/barbuy rassol`
- **Маракуйевая водка** — `/barbuy passionfruit`
- **Деревенский самогон** — `/barbuy village_samogon`
- **Водка** — `/barbuy vodka_plain`
- **Мексиканская Текила** — `/barbuy tequila`
- **Шведская водка** — `/barbuy vodka_absolut`
- **Капитанский Ром** — `/barbuy rum`
- **Егермейстер Orange** — `/barbuy jager_orange`
- **Теннессийский виски** — `/barbuy tennessee_whiskey`
- **Ликёр Егермейстер** — `/barbuy jagermeister`
- **Егермейстер Охотничий** — `/barbuy jager_dark`
- **О зависимости** — `/addiction`
- **Назад** — → ekb_casino
- **Закрыть**

### Строительная бригада
*`builder.yml` · 8 кнопок · `/brigade`, `/бригада` · право `ekb.duty.builder`*

- **Бригадир строителей**
- **Заказы** — `/calls`
- **Прайс биржи** — текст в чат
- **Схемы**
- **Крупный подряд** — → ekb_mercenaries
- **Границы работ**
- **Назад** — → ekb_duty
- **Закрыть**

### Суд и логи
*`admin_court.yml` · 7 кнопок · право `ekb.menu.admin`*

- **Инспектор CoreProtect** — `/co i`
- **Поиск по логам** — текст в чат
- **Выгрузка в Discord** — текст в чат
- **Откат** — текст в чат
- **Дела в Discord**
- **Назад** — → ekb_admin
- **Закрыть**

### Судья
*`judge.yml` · 11 кнопок · `/judge`, `/судья` · право `ekb.menu.judge`*

- **Дела**
- **Сбор доказательств** — `/co i`
- **Приобщить логи к делу** — текст в чат
- **Приговор** — `/ekbmenu jail`, ПКМ: `/jailinfo`
- **Имущество осуждённых** — `/jailprop`, ПКМ: `/ekbmenu items`
- **Освободить** — `/ekbmenu free`, ПКМ: `/jailinfo`
- **Откат по решению Суда** — текст в чат
- **Жалобы игроков** — `/reports`
- **Статьи УК** — → ekb_laws
- **Назад** — → ekb_duty
- **Закрыть**

### Теневой Рынок
*`blackmarket.yml` · 7 кнопок · `/blackmarket` · право `ekb.shadow.member`*

- **Теневой Рынок Сообщества**
- **Координаты сбора** — `/shadowmarket`
- **Личина** — `/disguise`
- **Чем это грозит**
- **Белая доска лотов** — `/lots`
- **Назад** — → ekb_profile
- **Закрыть**

### Торговая Коллегия
*`market.yml` · 7 кнопок · `/market`, `/коллегия`*

- **Торговая Коллегия Спавна**
- **Скупщик в Казну** — `/skupka`, ПКМ: `/skupka сдать`
- **Аренда палатки** — `/arenda`, ПКМ: `/arenda оплатить`
- **Доска лотов** — `/lots`, ПКМ: текст в чат
- **Казна Спавна** — `/treasury`
- **Назад** — → ekb_trade
- **Закрыть**

### Торговля
*`trade.yml` · 14 кнопок · `/trade`, `/торговля`, `/shops`*

- **Торговля**
- **Мои лавки** — `/shopkeeper list`
- **Купить яйцо торговца** — `/shopegg`
- **Открыть ларёк** — текст в чат
- **Валюта**
- **Каталог голов** — `/headdb`
- **Торговая Коллегия** — → ekb_market
- **Теневой Рынок** — → ekb_blackmarket  `[ekb.shadow.member]`
- **Ламповая Почта** — → ekb_pochta
- **Бар и кости** — → ekb_casino
- **Прайс-лист** — → ekb_laws
- **Запреты рынка**
- **Назад** — → ekb_main
- **Закрыть**

### Тюрьма
*`admin_jail.yml` · 8 кнопок · право `ekb.menu.admin`*

- **Кто сидит** — `/jailinfo`
- **Посадить** — `/ekbmenu jail`
- **Освободить досрочно** — `/ekbmenu free`
- **Судейский ящик** — `/jailprop`, ПКМ: `/ekbmenu items`
- **Точка тюрьмы** — `/setjailpoint`
- **Крыльцо Суда** — `/setcourtpoint`
- **Назад** — → ekb_admin
- **Закрыть**

### Тёмная Тетрадь Смерти
*`deathnote.yml` · 12 кнопок · `/deathnotemenu` · право `ekb.deathnote.admin`*

- **Тёмная Тетрадь Смерти**
- **Выдать себе** — `/givenote`
- **Выдать игроку** — `/ekbmenu deathnote`
- **Выдать случайному** — `/deathnote give random`
- **Где она сейчас** — `/deathnote find`
- **Полный обыск** — `/dnscan`
- **Состояние** — `/deathnote info`
- **Изъять** — `/ekbmenu reclaim`
- **Кулдаун** — текст в чат
- **Счётчик выданных** — текст в чат
- **Назад** — → ekb_admin_items
- **Закрыть**

### Тёмное ремесло
*`assassin.yml` · 7 кнопок · `/assassin`, `/ремесло`*

- **Тёмное ремесло**
- **Контракты** — → ekb_contracts
- **Чем это грозит** — текст в чат
- **Теневой Рынок** — → ekb_blackmarket
- **Как не попасться**
- **Назад** — → ekb_duty
- **Закрыть**

### Уровни власти
*`town_gov.yml` · 11 кнопок*

- **Уровни власти в городе**
- **Глава города** — текст в чат
- **Советник** — текст в чат
- **Казначей** — текст в чат
- **Страж** — текст в чат
- **Житель** — текст в чат
- **Как назначить** — текст в чат
- **Выдать должность** — `/ekbroles`  `[ekb.roles.manage]`
- **Чего должности НЕ дают**
- **Назад** — → ekb_town
- **Закрыть**

### Шериф
*`sheriff.yml` · 8 кнопок · `/sheriff`, `/шериф` · право `ekb.duty.sheriff`*

- **Шериф Спавна**
- **Заявки на патруль** — `/calls`
- **Осмотр места** — `/co i`
- **Кто сидит** — `/jailinfo`
- **Передать в Суд** — текст в чат
- **Что считается нарушением** — → ekb_laws
- **Назад** — → ekb_duty
- **Закрыть**
