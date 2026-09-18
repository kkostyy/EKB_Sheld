# EKB SHIELD — резервное копирование миров (Windows-версия).
# Запуск вручную:  .\backup.ps1
# По расписанию (ежедневно в 05:00), выполнить ОДИН раз в PowerShell от админа:
#   $a = New-ScheduledTaskAction -Execute "powershell.exe" `
#        -Argument "-NoProfile -ExecutionPolicy Bypass -File D:\EKB_Shield\backup.ps1"
#   $t = New-ScheduledTaskTrigger -Daily -At 5am
#   Register-ScheduledTask -TaskName "EKB SHIELD backup" -Action $a -Trigger $t
#
# Если сервер запущен, автозапись приостанавливается через RCON — иначе архив
# может получиться битым. Старые копии удаляются ТОЛЬКО после успешного архива.

$ErrorActionPreference = "Stop"

$ServerDir = "D:\EKB_Shield\server"
$BackupDir = "C:\Minecraft\backups"
$KeepDays  = 7
$Rcon      = Join-Path $PSScriptRoot "rcon.py"
$Stamp     = Get-Date -Format "yyyy-MM-dd_HH-mm"
$Archive   = Join-Path $BackupDir "world_$Stamp.zip"
$Staging   = Join-Path $env:TEMP "ekb_backup_$Stamp"

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Старт бэкапа..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

# Сервер поднят? Тогда просим его дописать мир на диск и не трогать файлы.
$ServerUp = $false
try {
    $tmp = Join-Path $env:TEMP "ekb_rcon_saveoff.txt"
    [System.IO.File]::WriteAllLines($tmp, @("save-off","save-all flush"), (New-Object System.Text.UTF8Encoding($false)))
    & py -3 $Rcon "--file" $tmp | Out-Null
    if ($LASTEXITCODE -eq 0) { $ServerUp = $true; Write-Host "      сервер работает: автозапись приостановлена" }
} catch {
    Write-Host "      сервер не отвечает по RCON — копирую как есть" -ForegroundColor DarkGray
}
if ($ServerUp) { Start-Sleep -Seconds 10 }

try {
    # Копируем во временную папку: Compress-Archive спотыкается о файлы, занятые сервером
    New-Item -ItemType Directory -Path $Staging -Force | Out-Null
    foreach ($w in @("world", "world_nether", "world_the_end")) {
        $src = Join-Path $ServerDir $w
        if (Test-Path $src) {
            robocopy $src (Join-Path $Staging $w) /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
        }
    }
    Compress-Archive -Path (Join-Path $Staging "*") -DestinationPath $Archive -CompressionLevel Optimal
}
finally {
    if ($ServerUp) { [System.IO.File]::WriteAllLines($tmp, @("save-on"), (New-Object System.Text.UTF8Encoding($false))); & py -3 $Rcon "--file" $tmp | Out-Null; Remove-Item $tmp -Force -EA SilentlyContinue; Write-Host "      автозапись возобновлена" }
    Remove-Item $Staging -Recurse -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $Archive) -or (Get-Item $Archive).Length -eq 0) {
    Write-Host "ОШИБКА: архив не создан. Старые бэкапы НЕ удаляются." -ForegroundColor Red
    exit 1
}

$size = [math]::Round((Get-Item $Archive).Length / 1MB, 1)
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Готово: $Archive ($size МБ)" -ForegroundColor Green

# Ротация — только после успешного архива
$old = Get-ChildItem $BackupDir -Filter "world_*.zip" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$KeepDays) }
if ($old) {
    $old | Remove-Item -Force
    Write-Host "      удалено старых копий: $($old.Count) (старше $KeepDays дн.)"
}
