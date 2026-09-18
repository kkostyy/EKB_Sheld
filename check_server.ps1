# EKB SHIELD — проверка готовности сервера (Windows-версия).
# Запуск:  .\check_server.ps1
# Ничего не меняет, только смотрит и докладывает.

param([string]$ServerDir = "D:\EKB_Shield\server")

$Plugins = Join-Path $ServerDir "plugins"
$script:ok = 0; $script:warn = 0; $script:err = 0

function Ok   ($m) { Write-Host "  [ OK ] $m" -ForegroundColor Green;      $script:ok++ }
function Warn ($m) { Write-Host "  [ !  ] $m" -ForegroundColor Yellow;     $script:warn++ }
function Err  ($m) { Write-Host "  [ XX ] $m" -ForegroundColor Red;        $script:err++ }
# ⚠ Имя ищется ОТ НАЧАЛА файла, а не подстрокой где угодно: старый
# -match без якоря рапортовал «WorldGuard - squaremap-worldguard…jar».
# Та же грабля, что с TAB внутри Execu-TAB-leItems.
#
# ⚠ И вторая половина той же грабли: имя аддона начинается с имени
# чужого плагина, и squaremap-worldguard один, без самой карты,
# закрывал бы собой проверку squaremap. Аддоны перечислены явно.
$AddonJars = @("squaremap-worldguard")
function JarList ($n) {
    Get-ChildItem "$Plugins\*.jar" -EA SilentlyContinue | Where-Object {
        $file = $_.Name
        if ($file -notlike "$n*") { return $false }
        foreach ($a in $AddonJars) {
            if ($n -ne $a -and $file -like "$a*") { return $false }
        }
        return $true
    }
}
function HasJar ($n) { [bool](JarList $n) }
function JarName ($n) { (JarList $n | Select-Object -First 1).Name }

Write-Host "==================================================" -ForegroundColor DarkGray
Write-Host " EKB SHIELD - проверка $ServerDir" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor DarkGray

Write-Host "`n[1] Окружение"
if (Test-Path $ServerDir) { Ok "каталог сервера на месте" } else { Err "нет каталога $ServerDir"; }
$java25 = Get-ChildItem "C:\Program Files\Eclipse Adoptium\jdk-25*\bin\java.exe","C:\Program Files\Java\jdk-25*\bin\java.exe" -EA SilentlyContinue | Select-Object -First 1
if ($java25) { Ok "Java 25: $($java25.FullName)" } else { Err "Java 25 не найдена (26.1.2 требует именно её)" }
if (Test-Path "$ServerDir\purpur-26.1.2.jar") { Ok "ядро purpur-26.1.2.jar" } else { Err "нет purpur-26.1.2.jar" }
if ((Get-Content "$ServerDir\eula.txt" -EA SilentlyContinue) -match "eula=true") { Ok "EULA принята" } else { Err "eula.txt не принята" }
if (Test-Path "$ServerDir\start.bat") { Ok "start.bat на месте" } else { Warn "нет start.bat — пересоздаст setup.ps1" }
$free = [math]::Round((Get-PSDrive C).Free / 1GB, 1)
if ($free -ge 20) { Ok "свободно $free ГБ" } else { Warn "свободно $free ГБ — мало под мир и бэкапы" }

Write-Host "`n[2] Обязательные плагины"
# "TAB" ищем отдельно: подстрока "tab" сидит внутри "ExecutableItems"
# (Execu-TAB-leItems), а -match в PowerShell регистронезависим — проверка
# рапортовала о найденном TAB, даже когда его jar отсутствовал.
if (Get-ChildItem "$Plugins\TAB*.jar" -EA SilentlyContinue) {
    Ok "TAB - $((Get-ChildItem "$Plugins\TAB*.jar" | Select-Object -First 1).Name)"
} else { Err "TAB не найден" }
foreach ($p in @("CoreProtect","LuckPerms","DiscordSRV","squaremap","BreweryX","ExecutableItems",
                 "DecentHolograms","GSit","PlasmoVoice","Skript","ChestShop","WorldGuard","worldedit","Chunky")) {
    if (HasJar $p) { Ok "$p - $(JarName $p)" } else { Err "$p не найден" }
}
if (HasJar "CustomPlayerModels") { Ok "CPM - $(JarName 'CustomPlayerModels')" } else { Err "CustomPlayerModels не найден" }
if (HasJar "Essentials") { Ok "EssentialsX - $(JarName 'Essentials')" } else { Warn "EssentialsX не найден" }

Write-Host "`n[3] Зависимости"
if (HasJar "SCore") { Ok "SCore" } else { Err "SCore ОТСУТСТВУЕТ - ExecutableItems не загрузится, Тетради Смерти не будет" }
if (HasJar "Vault") { Ok "Vault - $(JarName 'Vault')" } else { Err "Vault отсутствует - ChestShop не запустится (No Economy adapter)" }
if (HasJar "PlaceholderAPI") { Ok "PlaceholderAPI" } else { Warn "PlaceholderAPI нет - плейсхолдеры в TAB и голограммах не раскроются" }

Write-Host "`n[4] Админ-набор"
foreach ($p in @("SuperVanish","OpenInv","PlugMan")) {
    if (HasJar $p) { Ok "$p - $(JarName $p)" } else { Warn "$p не найден" }
}
if (HasJar "spark") { Warn "spark лежит в plugins/ - он уже встроен в Purpur, лишний jar лучше убрать" }
else { Ok "spark - встроен в ядро, отдельный jar не нужен" }
if (HasJar "CourtBridge") { Ok "CourtBridge - плагин суда" } else { Warn "CourtBridge.jar не залит - /courtlog работать не будет" }

Write-Host "`n[5] Конфликты"
foreach ($p in @("MyCommand","Jail")) {
    if (HasJar $p) { Warn "$p установлен - проект от него отказался (заменён Skript)" } else { Ok "$p отсутствует, как и задумано" }
}
foreach ($p in @("ClearLag","LagFixer","LagAssist")) {
    if (HasJar $p) { Err "$p чистит дроп по таймеру - на этом сервере это уничтожение улик и имущества" }
}
if ((HasJar "FastAsyncWorldEdit") -and (HasJar "worldedit-bukkit")) { Err "FAWE и WorldEdit вместе - оставь что-то одно" }

Write-Host "`n[6] Конфиги и контент"
# ⚠️ purpur.yml и spigot.yml Purpur и Spigot читают из КОРНЯ сервера,
# а не из config\. Копии в config\ — мёртвые: до 18.09.2026 setup клал их
# именно туда, и настройки проекта не работали ни дня.
foreach ($f in @("config\paper-world-defaults.yml","purpur.yml","spigot.yml","server.properties")) {
    if (Test-Path (Join-Path $ServerDir $f)) { Ok $f } else { Err "нет $f" }
}
foreach ($f in @("config\purpur.yml","config\spigot.yml")) {
    if (Test-Path (Join-Path $ServerDir $f)) {
        Err "$f - мёртвая копия, сервер её не читает. Удали и накати патчи: py -3 apply_server_configs.py --write"
    }
}
# Патчи из репозитория реально доехали?
$pur = Get-Content "$ServerDir\purpur.yml" -Raw -Encoding UTF8 -EA SilentlyContinue
$spi = Get-Content "$ServerDir\spigot.yml" -Raw -Encoding UTF8 -EA SilentlyContinue
if ($pur -match "use-alternate-keepalive:\s*true") { Ok "purpur.yml: патч проекта применён" }
else { Err "purpur.yml: патч НЕ применён - py -3 apply_server_configs.py --write" }
if ($spi -match "max-tnt-per-tick:\s*200") { Ok "spigot.yml: патч проекта применён" }
else { Err "spigot.yml: патч НЕ применён - py -3 apply_server_configs.py --write" }
if ((Get-Content "$ServerDir\config\paper-world-defaults.yml" -Raw -Encoding UTF8 -EA SilentlyContinue) -match "anti-xray") { Ok "anti-xray настроен" } else { Err "нет секции anti-xray" }
if (Test-Path "$Plugins\BreweryX\recipes.yml") {
    # BreweryX при загрузке переписывает значение в кавычки: customModelData: '1001'
    if ((Get-Content "$Plugins\BreweryX\recipes.yml" -Raw -Encoding UTF8) -match "customModelData: .?1001") { Ok "рецепты EKB в BreweryX/recipes.yml" }
    else { Err "в BreweryX/recipes.yml нет наших рецептов" }
} else { Err "нет plugins\BreweryX\recipes.yml" }
$sk = Get-ChildItem "$Plugins\Skript\scripts\*.sk" -EA SilentlyContinue
if ($sk) { Ok "Skript-скрипты: $($sk.Count) шт." } else { Warn "нет .sk в plugins\Skript\scripts" }
if (Test-Path "$ServerDir\world\datapacks\ekb_border") { Ok "датапак границы установлен" } else { Warn "датапак не установлен (ставится после создания мира)" }

$props = Get-Content "$ServerDir\server.properties" -Raw -Encoding UTF8
Write-Host "`n[6b] Обновление 18.09.2026"
foreach ($p in @("ImageFrame","QualityArmory","TablePlays","FasterMinecarts","AttackThrough","squaremap-worldguard",
                 "Female-Gender","pv-addon-nickname","ArmorPoser")) {
    if (HasJar $p) { Ok "$p - $(JarName $p)" } else { Warn "$p не установлен" }
}
# QualityArmory по умолчанию сам рассылает свой пак с Dropbox поверх нашего
# принудительного - клиент ловит ошибку загрузки на каждом входе.
$qa = Get-Content "$Plugins\QualityArmory\config.yml" -Raw -Encoding UTF8 -EA SilentlyContinue
if ($qa) {
    if ($qa -match "useDefaultResourcepack:\s*false" -and $qa -match "sendOnJoin:\s*false") {
        Ok "QualityArmory не перебивает наш ресурспак"
    } else { Err "QualityArmory рассылает свой пак поверх принудительного - useDefaultResourcepack и sendOnJoin в false" }
    if ($qa -match "enable_permssionsToShoot:\s*true") { Ok "QualityArmory проверяет право на выстрел" }
    else { Err "QualityArmory: enable_permssionsToShoot=false - стреляет кто угодно, право qualityarmory.usegun не проверяется" }
    if ($qa -match "enableCrafting:\s*false" -and $qa -match "enableShop:\s*false") { Ok "QualityArmory: стволы не крафтятся и не покупаются" }
    else { Warn "QualityArmory: включён крафт или магазин - оружие появляется в обход Администрации" }
}
$ifr = Get-Content "$Plugins\ImageFrame\config.yml" -Raw -Encoding UTF8 -EA SilentlyContinue
if ($ifr -match "your-server-ip") { Warn "ImageFrame: DisplayURL - заглушка, аплоад картинок игроку не открыть" }
elseif ($ifr) { Ok "ImageFrame: DisplayURL задан" }

# Приват Спавна
$rg = "$Plugins\WorldGuard\worlds\world\regions.yml"
if (Test-Path $rg) {
    $rgt = Get-Content $rg -Raw -Encoding UTF8
    if ($rgt -match "(?m)^\s+spawn:") { Ok "WorldGuard: регион spawn определён" } else { Err "WorldGuard: в regions.yml нет региона spawn" }
} else { Err "WorldGuard: нет regions.yml - приват Спавна не создан (py -3 build_spawn_region.py --install)" }
if ($props -match "spawn-protection=0") { Ok "ванильная spawn-protection выключена - защиту держит WorldGuard" }
else { Warn "spawn-protection не 0 - ванильная защита 33x33 перебьёт WorldGuard для всех, кроме операторов" }

# Центр мира совпадает во всех четырёх местах?
# Он прописан в датапаке, в двух expand_border и в регионе привата.
# Разъехались — граница встанет не вокруг Спавна, а заметится это
# только когда игроков начнёт выталкивать с уже обжитой территории.
$stageF = "$ServerDir\world\datapacks\ekb_border\data\ekbunction\expand\stage2.mcfunction"
$stage  = Get-Content $stageF -Raw -Encoding UTF8 -EA SilentlyContinue
$badCenter = @()
if ($stage -notmatch "overworld run worldborder center -1750 4000") { $badCenter += "датапак (Обычный)" }
if ($stage -notmatch "the_nether run worldborder center -218\.75 500")  { $badCenter += "датапак (Ад)" }
$eb = Get-Content "$PSScriptRoot\expand_border.ps1" -Raw -Encoding UTF8 -EA SilentlyContinue
if ($eb -notmatch '\$CenterX = -1750') { $badCenter += "expand_border.ps1" }
$ebs = Get-Content "$PSScriptRoot\expand_border.sh" -Raw -Encoding UTF8 -EA SilentlyContinue
if ($ebs -notmatch "CENTER_X=-1750") { $badCenter += "expand_border.sh" }
if ($rgt -and $rgt -notmatch "x: -1942") { $badCenter += "регион spawn" }
if ($badCenter.Count -eq 0) { Ok "центр мира -1750/4000 совпадает везде (Ад -218.75/500)" }
else { Err ("центр мира разошёлся: " + ($badCenter -join ", ")) }

# Скип ночи при 25%
$init = Get-Content "$ServerDir\world\datapacks\ekb_border\data\ekb\function\init.mcfunction" -Raw -Encoding UTF8 -EA SilentlyContinue
# Имя геймрула в 26.1 — snake_case. Проверка искала старое camelCase-имя
# и ругалась на правильный датапак — то есть гнала чинить то, что работает.
if ($init -match "players_sleeping_percentage 25") { Ok "датапак ставит скип ночи при 25% спящих" }
elseif ($init -match "playersSleepingPercentage") { Err "в датапаке camelCase-имя геймрула - функция не загрузится целиком" }
else { Warn "в датапаке нет players_sleeping_percentage - ночь скипается только при 100% онлайна" }

Write-Host "`n[7] Незаполненные секреты"
# Комментарии отрезаются: в шапке config.yml лежит ПРИМЕР строки с
# ID_КАНАЛА_*, и проверка ругалась на заполненный конфиг: каналы стоят,
# а сервер выводил ошибку и требовал чинить то, что работает.
$dsrv  = (Get-Content "$Plugins\DiscordSRV\config.yml" -Encoding UTF8 -EA SilentlyContinue | Where-Object { $_ -notmatch '^\s*#' }) -join "`n"
if ($dsrv -match "ВСТАВЬ_ТОКЕН_БОТА_СЮДА") { Err "DiscordSRV: не вписан BotToken" } else { Ok "DiscordSRV: токен задан" }
if ($dsrv -match "ID_КАНАЛА")               { Err "DiscordSRV: не заполнены ID каналов" } else { Ok "DiscordSRV: каналы заданы" }
if ($props -match "ВСТАВЬ_URL")             { Err "server.properties: не вписан URL ресурспака" } else { Ok "URL ресурспака задан" }
if ($props -match "enable-rcon=true")       { Ok "RCON включён (нужен backup.ps1 и expand_border.ps1)" } else { Warn "RCON выключен - скрипты не смогут слать команды" }

Write-Host "`n[8] Сторонние плагины (не из плана проекта)"
$known = @("CoreProtect","LuckPerms","DiscordSRV","TAB","squaremap","BreweryX","ExecutableItems","SCore",
           "DecentHolograms","GSit","PlasmoVoice","Skript","ChestShop","WorldGuard","worldedit","Chunky",
           "SuperVanish","OpenInv","PlugMan","CustomPlayerModels","Essentials","CourtBridge","PlaceholderAPI","Vault",
           "ImageFrame","QualityArmory","TablePlays","FasterMinecarts","AttackThrough",
           "Female-Gender","pv-addon-nickname","ArmorPoser")
Get-ChildItem "$Plugins\*.jar" -EA SilentlyContinue | ForEach-Object {
    $n = $_.Name
    if (-not ($known | Where-Object { $n -match [regex]::Escape($_) })) { Write-Host "  [ .. ] $n" -ForegroundColor DarkGray }
}

Write-Host "`n==================================================" -ForegroundColor DarkGray
Write-Host " Итог: OK=$script:ok, предупреждений=$script:warn, ошибок=$script:err"
if ($script:err -gt 0) { Write-Host " Есть блокирующие проблемы." -ForegroundColor Red }
else { Write-Host " Блокеров нет. Запуск: $ServerDir\start.bat" -ForegroundColor Green }
Write-Host "==================================================" -ForegroundColor DarkGray
