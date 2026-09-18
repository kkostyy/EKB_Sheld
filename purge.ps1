# EKB SHIELD — «Кровавый Сон» / Судная Ночь (Windows-версия).
#
# Ивент: на несколько часов отключаются логирование и правила, а по окончании
# мир откатывается к бэкапу — «как будто ничего не было». Отсюда и название:
# сервер просыпается, и ночи не было.
#
# Запуск:
#     .\purge.ps1                 3 часа (по умолчанию)
#     .\purge.ps1 -Hours 1        час
#     .\purge.ps1 -WhatIfOnly     показать план и выйти, ничего не трогая
#
# Это двойник purge.sh. Отличий два, и оба вынужденные:
#   1. Команды идут по RCON, а не через screen — на Windows screen-сессии нет
#      (то же решение, что в backup.ps1 и expand_border.ps1).
#   2. Сервер поднимается обратно через start.bat, а не `screen -dmS`.
#
# ⚠️ Скрипт НЕ УДАЛЯЕТ мир ивента, а отодвигает его в world_PURGE_RESULT_<дата>.
# Если в Судную Ночь кто-то построил что-то ценное, это можно вытащить.
# Удалять папку — руками и потом.
#
# ⚠️ Запускать только на РАБОТАЮЩЕМ сервере: скрипт сам его остановит,
# откатит мир и запустит заново.

param(
    [double]$Hours = 3,
    [switch]$WhatIfOnly
)

$ErrorActionPreference = "Stop"

$ServerDir = "D:\EKB_Shield\server"
$BackupDir = "C:\Minecraft\backups"
$Rcon      = Join-Path $PSScriptRoot "rcon.py"
$Stamp     = Get-Date -Format "yyyy-MM-dd_HH-mm"
$BackupPath = Join-Path $BackupDir "world_BEFORE_PURGE_$Stamp"
$EventSeconds = [int]($Hours * 3600)

function Say($msg, $color = "Gray") { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor $color }

function Invoke-Mc {
    param([string[]]$Commands)
    # Команды передаём файлом: PowerShell 5.1 калечит аргументы с пробелами и
    # кавычками при вызове внешней программы, а в title/tellraw идёт JSON.
    $tmp = Join-Path $env:TEMP ("ekb_purge_" + [guid]::NewGuid().ToString("N") + ".txt")
    [System.IO.File]::WriteAllLines($tmp, $Commands, (New-Object System.Text.UTF8Encoding($false)))
    try { & py -3 $Rcon "--file" $tmp | Out-Null; return ($LASTEXITCODE -eq 0) }
    finally { Remove-Item $tmp -Force -EA SilentlyContinue }
}

Write-Host "==================================================" -ForegroundColor DarkRed
Write-Host " КРОВАВЫЙ СОН — $Hours ч., затем полный откат мира" -ForegroundColor Red
Write-Host "==================================================" -ForegroundColor DarkRed

# --- [0/5] Проверки. Лучше не начать, чем потерять мир ---
Say "[0/5] Проверка окружения..."
if (-not (Test-Path (Join-Path $ServerDir "world"))) { Say "ОШИБКА: нет $ServerDir\world" "Red"; exit 1 }
if (-not (Test-Path (Join-Path $ServerDir "start.bat"))) { Say "ОШИБКА: нет start.bat — сервер будет нечем поднять обратно" "Red"; exit 1 }
if (-not (Get-Process java -EA SilentlyContinue)) { Say "ОШИБКА: сервер не запущен. Запусти start.bat и повтори." "Red"; exit 1 }
if (-not (Invoke-Mc @("list"))) { Say "ОШИБКА: сервер не отвечает по RCON. Проверь enable-rcon в server.properties." "Red"; exit 1 }

# Места нужно столько же, сколько занимает мир, плюс запас: копия делается
# рядом, а не поверх.
$worldSize = (Get-ChildItem (Join-Path $ServerDir "world") -Recurse -Force -EA SilentlyContinue | Measure-Object Length -Sum).Sum
$drive = (Get-Item $ServerDir).PSDrive
$free = (Get-PSDrive $drive.Name).Free
if ($free -lt ($worldSize * 2.2)) {
    Say ("ОШИБКА: мало места. Мир " + [math]::Round($worldSize/1MB,1) + " МБ, свободно " + [math]::Round($free/1MB,1) + " МБ.") "Red"
    exit 1
}
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Say ("      мир " + [math]::Round($worldSize/1MB,1) + " МБ, свободно " + [math]::Round($free/1GB,1) + " ГБ — хватает") "Green"

if ($WhatIfOnly) {
    Say "Режим -WhatIfOnly: план показан, ничего не изменено." "Yellow"
    Write-Host "  1. бэкап       -> $BackupPath"
    Write-Host "  2. plugman disable CoreProtect"
    Write-Host "  3. ивент $Hours ч. с предупреждениями за 60/30/10/5/1 мин"
    Write-Host "  4. stop, мир ивента -> world_PURGE_RESULT_$Stamp"
    Write-Host "  5. бэкап -> world, запуск start.bat"
    exit 0
}

# --- [1/5] Бэкап с остановленной автозаписью ---
Say "[1/5] Резервная копия мира (автозапись на паузе)..."
Invoke-Mc @("save-off", "save-all flush") | Out-Null
Start-Sleep -Seconds 15
robocopy (Join-Path $ServerDir "world") $BackupPath /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
# robocopy возвращает 0-7 как успех, 8+ как ошибку — обычный -ne 0 здесь врёт.
$rc = $LASTEXITCODE
Invoke-Mc @("save-on") | Out-Null
if ($rc -ge 8) { Say "ОШИБКА: robocopy завершился с кодом $rc. Ивент отменён." "Red"; exit 1 }
if (-not (Test-Path (Join-Path $BackupPath "level.dat"))) {
    Say "ОШИБКА: в бэкапе нет level.dat — копия неполная. Ивент отменён." "Red"; exit 1
}
Say "      бэкап проверен: $BackupPath" "Green"

# --- [2/5] Гасим CoreProtect ---
# Судная Ночь не должна попасть в логи: иначе Суд получит тысячи «краж»,
# которых по правилам ивента не было.
Say "[2/5] Отключение CoreProtect..."
Invoke-Mc @("plugman disable CoreProtect") | Out-Null

# --- [3/5] Объявление ---
Say "[3/5] Объявление ивента..."
Invoke-Mc @(
    "title @a times 10 70 20",
    "title @a title {`"text`":`"КРОВАВЫЙ СОН`",`"color`":`"dark_red`",`"bold`":true}",
    "title @a subtitle {`"text`":`"Правила и логирование отключены`",`"color`":`"red`"}",
    "tellraw @a {`"text`":`"[EKB SHIELD] Судная Ночь началась. Всё, что случится, будет отменено откатом мира.`",`"color`":`"dark_red`"}",
    "tellraw @a {`"text`":`"Бэкап сделан до начала. Постройки этой ночи не сохранятся.`",`"color`":`"gray`"}"
) | Out-Null

# --- [4/5] Обратный отсчёт ---
Say "[4/5] Ивент идёт: $Hours ч."
$remaining = $EventSeconds
foreach ($warn in @(3600, 1800, 600, 300, 60)) {
    if ($remaining -gt $warn) {
        Start-Sleep -Seconds ($remaining - $warn)
        $remaining = $warn
        $min = [int]($warn / 60)
        Invoke-Mc @("tellraw @a {`"text`":`"[КРОВАВЫЙ СОН] До пробуждения: $min мин. Откат мира неизбежен.`",`"color`":`"red`"}") | Out-Null
        Say "      осталось $min мин."
    }
}
Start-Sleep -Seconds $remaining

# --- [5/5] Остановка и откат ---
Say "[5/5] Время вышло. Остановка сервера..." "Yellow"
Invoke-Mc @(
    "title @a title {`"text`":`"ПРОБУЖДЕНИЕ`",`"color`":`"green`",`"bold`":true}",
    "tellraw @a {`"text`":`"[EKB SHIELD] Сон окончен. Мир откатывается.`",`"color`":`"green`"}"
) | Out-Null
Start-Sleep -Seconds 3
Invoke-Mc @("stop") | Out-Null

# Ждём, пока JVM реально выйдет: копировать мир из-под работающего сервера —
# верный способ получить битый level.dat.
$waited = 0
while ((Get-Process java -EA SilentlyContinue) -and $waited -lt 180) {
    Start-Sleep -Seconds 2
    $waited += 2
}
if (Get-Process java -EA SilentlyContinue) {
    Say "ОШИБКА: сервер не остановился за 3 минуты. Мир НЕ откачен, бэкап цел: $BackupPath" "Red"
    exit 1
}
Start-Sleep -Seconds 3

$result = Join-Path $ServerDir "world_PURGE_RESULT_$Stamp"
Move-Item (Join-Path $ServerDir "world") $result
robocopy $BackupPath (Join-Path $ServerDir "world") /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) {
    Say "ОТКАТ НЕ УДАЛСЯ. Мир ивента: $result, бэкап: $BackupPath — восстанови руками." "Red"
    exit 1
}

Say "Мир откачен. Итог ивента лежит в $result — удали, когда убедишься." "Green"
Start-Process -FilePath (Join-Path $ServerDir "start.bat") -WorkingDirectory $ServerDir
Say "Сервер перезапущен." "Green"
