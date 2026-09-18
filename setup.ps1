# EKB SHIELD — установка сервера на Windows (Purpur 26.1.2, Java 25).
# Запуск из PowerShell:  .\setup.ps1
# Аналог setup.sh для Linux. Ничего не удаляет: существующие world/ и конфиги
# плагинов не трогаются, перезаписываются только файлы проекта.

$ErrorActionPreference = "Stop"

$ProjectDir = $PSScriptRoot
$ServerDir  = "D:\EKB_Shield\server"
$PurpurVer  = "26.1.2"

Write-Host "==================================================" -ForegroundColor DarkGray
Write-Host " EKB SHIELD - установка сервера Purpur $PurpurVer" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor DarkGray

# [1/6] Java 25
Write-Host "`n[1/6] Поиск Java 25..."
$JavaExe = $null
$candidates = @(
    "C:\Program Files\Eclipse Adoptium\jdk-25*\bin\java.exe",
    "C:\Program Files\Java\jdk-25*\bin\java.exe",
    "C:\Program Files\Microsoft\jdk-25*\bin\java.exe"
)
foreach ($c in $candidates) {
    $found = Get-ChildItem $c -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $JavaExe = $found.FullName; break }
}
if (-not $JavaExe) {
    throw "Java 25 не найдена. Minecraft 26.1.2 требует именно её. Скачай: https://adoptium.net/temurin/releases/?version=25"
}
Write-Host "      $JavaExe" -ForegroundColor Green

# [2/6] Структура папок
Write-Host "`n[2/6] Создание папок в $ServerDir..."
foreach ($d in @("", "\plugins", "\config", "\backups", "\logs")) {
    $path = "$ServerDir$d"
    if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path -Force | Out-Null }
}

# [3/6] Purpur
$JarPath = "$ServerDir\purpur-$PurpurVer.jar"
if (Test-Path $JarPath) {
    Write-Host "`n[3/6] Purpur уже скачан, пропускаю."
} else {
    Write-Host "`n[3/6] Скачивание Purpur $PurpurVer..."
    $meta  = Invoke-RestMethod "https://api.purpurmc.org/v2/purpur/$PurpurVer" -TimeoutSec 60
    $build = $meta.builds.latest
    Write-Host "      билд $build"
    Invoke-WebRequest "https://api.purpurmc.org/v2/purpur/$PurpurVer/$build/download" -OutFile $JarPath -TimeoutSec 600
    Write-Host ("      скачано: " + [math]::Round((Get-Item $JarPath).Length/1MB,1) + " МБ") -ForegroundColor Green
}

# [4/6] EULA
Write-Host "`n[4/6] Принятие EULA (eula.txt)..."
"eula=true" | Out-File "$ServerDir\eula.txt" -Encoding ascii

# [5/6] Конфиги, плагины, контент проекта
Write-Host "`n[5/6] Копирование конфигов и плагинов..."
Copy-Item "$ProjectDir\server.properties" $ServerDir -Force
# ⚠️ В $ServerDir\config\ лежат ТОЛЬКО paper-*.yml. purpur.yml и spigot.yml
# Purpur и Spigot читают из КОРНЯ сервера, и до 18.09.2026 они уезжали сюда же,
# в config\, — то есть настройки проекта не работали вообще. Теперь эти два
# файла в репозитории — патчи, и накатывает их apply_server_configs.py.
Copy-Item "$ProjectDir\config\paper-*.yml" "$ServerDir\config\" -Force
Copy-Item "$ProjectDir\plugins\*" "$ServerDir\plugins\" -Recurse -Force
Write-Host ("      плагинов: " + (Get-ChildItem "$ServerDir\plugins\*.jar").Count + " jar") -ForegroundColor Green

$CourtJar = "$ProjectDir\CourtBridge\target\CourtBridge.jar"
if (Test-Path $CourtJar) { Copy-Item $CourtJar "$ServerDir\plugins\" -Force; Write-Host "      CourtBridge.jar скопирован" }

$SkriptDir = "$ServerDir\plugins\Skript\scripts"
if (-not (Test-Path $SkriptDir)) { New-Item -ItemType Directory -Path $SkriptDir -Force | Out-Null }
Copy-Item "$ProjectDir\docs\*.sk" $SkriptDir -Force
Write-Host "      Skript-скрипты скопированы"

# [5c/6] Патчи purpur.yml и spigot.yml — по месту, в корень сервера.
# Эти два файла нельзя копировать: на сервере лежит сгенерированный конфиг
# на тысячи строк, а в репозитории — патч на несколько ключей.
Write-Host "      применение патчей purpur.yml и spigot.yml..."
& py -3 (Join-Path $ProjectDir "apply_server_configs.py") "--write"
if (-not $?) { Write-Host "      ВНИМАНИЕ: патчи не применились — сверь пути ключей" -ForegroundColor Yellow }

# [5b/6] Скрипты управления рядом с сервером
Copy-Item (Join-Path $ProjectDir "rcon.py") $ServerDir -Force -ErrorAction SilentlyContinue
foreach ($ps in @("check_server.ps1","expand_border.ps1","backup.ps1")) {
    if (Test-Path (Join-Path $ProjectDir $ps)) { Copy-Item (Join-Path $ProjectDir $ps) $ServerDir -Force }
}
Write-Host "      rcon.py и управляющие скрипты скопированы"

# [6/6] Стартовый скрипт с найденной Java.
# Heap 4-6 ГБ, а не 8: сервер и игровой клиент делят одну машину.
# На max-players=30 и границе 4000 этого с запасом, а лишние гигабайты
# отнимались у клиента и уводили систему в подкачку.
Write-Host "`n[6/6] Создание start.bat..."
$startBat = @"
@echo off
title EKB SHIELD - Purpur $PurpurVer
cd /d "$ServerDir"
"$JavaExe" -Xms4G -Xmx6G ^
 -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 ^
 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch ^
 -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M ^
 -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 ^
 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 ^
 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 ^
 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 ^
 -jar "$JarPath" nogui
echo.
echo Сервер остановлен. Нажми любую клавишу.
pause >nul
"@
$startBat | Out-File "$ServerDir\start.bat" -Encoding oem

Write-Host "`n==================================================" -ForegroundColor DarkGray
Write-Host " Готово. Запуск сервера:" -ForegroundColor Yellow
Write-Host "   $ServerDir\start.bat" -ForegroundColor White
Write-Host ""
Write-Host " Команды сервера вводятся прямо в открывшемся окне." -ForegroundColor Gray
Write-Host " Остановка: команда stop (не крестиком!)." -ForegroundColor Gray
Write-Host "==================================================" -ForegroundColor DarkGray
