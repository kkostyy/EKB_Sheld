# EKB SHIELD — поэтапное расширение границы мира (Windows-версия).
# Запуск:  .\expand_border.ps1 2        — применить стадию
#          .\expand_border.ps1 status   — текущий размер
# Команды уходят на работающий сервер через RCON (см. rcon.py).

param([Parameter(Position=0)][string]$Stage = "status")

$ErrorActionPreference = "Stop"
$Rcon = Join-Path $PSScriptRoot "rcon.py"

# ЦЕНТР МИРА. Не 0,0: Спавн стоит на -1750 75 4000, и граница растёт вокруг
# него. Центр в нуле отрезал бы Спавн уже на первой стадии — 4000 блоков
# в диаметре это ±2000 от центра, а до Спавна оттуда 4370.
#
# ⚠️ Нижний мир — РОВНО центр/8, как и диаметр. Иначе игрок, ушедший далеко
# по Аду, выходит из портала за границей Обычного мира: ванильный портал
# делит координаты на 8, и если центры не сходятся, расхождение растёт
# вместе с расстоянием.
#
# ⚠️ Дробное число в строку кладём через InvariantCulture: в русской локали
# PowerShell печатает «-218,75», и сервер такую команду не разберёт.
$CenterX = -1750
$CenterZ = 4000
$Inv     = [System.Globalization.CultureInfo]::InvariantCulture
$NetherX = ([double]$CenterX / 8).ToString($Inv)
$NetherZ = ([double]$CenterZ / 8).ToString($Inv)

# стадия = @(диаметр Обычного, секунд на расширение, повод)
$Stages = @{
  "1" = @(4000,  600,    "Открытие сервера")
  "2" = @(8000,  86400,  "Достижение: вход в Нижний мир")
  "3" = @(12000, 86400,  "Достижение: найдена крепость Ада")
  "4" = @(16000, 172800, "Достижение: вход в Край")
  "5" = @(20000, 172800, "Достижение: убит дракон Края")
}

function Invoke-Mc {
    param([string[]]$Commands)
    # Команды передаём файлом: PowerShell 5.1 калечит аргументы с пробелами и
    # кавычками при вызове внешней программы, а в tellraw/title идёт JSON.
    $tmp = Join-Path $env:TEMP ("ekb_rcon_" + [guid]::NewGuid().ToString("N") + ".txt")
    [System.IO.File]::WriteAllLines($tmp, $Commands, (New-Object System.Text.UTF8Encoding($false)))
    try { & py -3 $Rcon "--file" $tmp } finally { Remove-Item $tmp -Force -EA SilentlyContinue }
}

if ($Stage -eq "status") {
    Invoke-Mc @("worldborder get", "function ekb:status")
    exit 0
}

if (-not $Stages.ContainsKey($Stage)) {
    Write-Host "Неизвестная стадия '$Stage'. Доступны: 1..5 или status" -ForegroundColor Red
    exit 1
}

$size, $secs, $reason = $Stages[$Stage]
$nether = [int]($size / 8)
$hours  = [math]::Round($secs / 3600, 1)

Write-Host "=== Стадия $Stage : $reason ===" -ForegroundColor Yellow
Write-Host "Обычный мир: $size (±$($size/2)), Нижний: $nether (±$($nether/2))"
Write-Host "Расширение растянуто на $secs сек (~$hours ч)"
Write-Host ""
Write-Host "ВНИМАНИЕ: территория должна быть прогенерирована Chunky, иначе игроки" -ForegroundColor DarkYellow
Write-Host "будут генерировать чанки на ходу и ловить просадки TPS:" -ForegroundColor DarkYellow
Write-Host "  /chunky world world; /chunky center $CenterX $CenterZ; /chunky radius $($size/2); /chunky start" -ForegroundColor Gray
Write-Host ""
$answer = Read-Host "Продолжить? (y/N)"
if ($answer -ne "y") { Write-Host "Отменено."; exit 0 }

Invoke-Mc @(
  "scoreboard players set #stage ekb $Stage",
  "execute in minecraft:overworld run worldborder center $CenterX $CenterZ",
  "execute in minecraft:the_nether run worldborder center $NetherX $NetherZ",
  "execute in minecraft:overworld run worldborder set $size $secs",
  "execute in minecraft:the_nether run worldborder set $nether $secs",
  "execute in minecraft:overworld run worldborder warning distance 10",
  "execute in minecraft:overworld run worldborder warning time 20",
  "title @a title {`"text`":`"ГРАНИЦЫ МИРА РАСШИРЯЮТСЯ`",`"color`":`"gold`"}",
  "title @a subtitle {`"text`":`"$reason`",`"color`":`"yellow`"}",
  "tellraw @a {`"text`":`"[PROJECT SHIELD] Мир расширяется до $size блоков в течение $hours ч.`",`"color`":`"gold`"}"
)

Write-Host "`nГотово. Проверить: .\expand_border.ps1 status" -ForegroundColor Green
