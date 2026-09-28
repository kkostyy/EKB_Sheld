# EKB SHIELD — бот Суда без остановок.
# Запускает `node index.js` и поднимает его заново, если он упал (обрыв сети,
# рестарт Discord, исключение). Лог — discord_bot\bot.log.
# Ставится в автозапуск install_autostart.ps1, руками обычно не зовётся.

$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot

# Второй экземпляр не нужен: два бота с одним токеном отвечали бы на каждую
# команду дважды. Именованный мьютекс держится, пока жив этот скрипт.
$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Global\EKB_Court_Bot', [ref]$created)
if (-not $created) { exit 0 }

$node = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not $node) { $node = 'C:\Program Files\nodejs\node.exe' }

while ($true) {
    Add-Content -Encoding utf8 bot.log "$(Get-Date -Format s) === старт бота"
    # Через cmd, а не *>>: PowerShell 5.1 пишет перенаправление в UTF-16.
    cmd /c "`"$node`" index.js >> bot.log 2>&1"
    Add-Content -Encoding utf8 bot.log "$(Get-Date -Format s) === бот остановился (код $LASTEXITCODE), перезапуск через 15 с"
    # Лог не растёт бесконечно: больше 5 МБ — начинаем заново, старый в .old
    if ((Get-Item bot.log).Length -gt 5MB) { Move-Item -Force bot.log bot.log.old }
    Start-Sleep -Seconds 15
}
