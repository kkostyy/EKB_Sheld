# EKB SHIELD — автозапуск сервера и бота Суда при входе в Windows.
#
#   .\install_autostart.ps1              поставить (и сразу запустить бота)
#   .\install_autostart.ps1 -NoServer    только бот, сервер запускаешь сам
#   .\install_autostart.ps1 -Uninstall   убрать обе задачи
#
# Почему именно так:
#   • бот Суда (discord_bot) — задача «EKB Court Bot»: скрытое окно,
#     run-bot.ps1 перезапускает его после любого падения;
#   • бот DiscordSRV (SRVLOG, синхронизация ролей, чат, вход по привязке)
#     живёт ВНУТРИ сервера Minecraft. Отдельно его не запустить: выключен
#     сервер — выключен и бот. Поэтому вторая задача, «EKB Server», поднимает
#     сам сервер — обычным start.bat, окно сервера остаётся консолью;
#   • триггер — вход пользователя, а не старт Windows: задача «при старте
#     без входа» требует прав администратора и пароля, а окно консоли
#     сервера в таком режиме никто бы не увидел.
# ⚠ Всё это работает, пока включён компьютер. Спящий режим усыпляет и
#   сервер, и ботов — отключи сон при питании от сети (см. ниже).

param([switch]$NoServer, [switch]$Uninstall)

$root = $PSScriptRoot
$user = "$env:USERDOMAIN\$env:USERNAME"

if ($Uninstall) {
    foreach ($t in 'EKB Court Bot', 'EKB Server') {
        if (Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $t -Confirm:$false
            Write-Host "Снята задача: $t"
        }
    }
    exit 0
}

# Задачи без ограничения времени (по умолчанию Планировщик убивает через 72 ч),
# работают и от батареи, повторный запуск не плодит второй экземпляр.
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable

# --- бот Суда ---
$botAction = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$root\discord_bot\run-bot.ps1`"" `
    -WorkingDirectory "$root\discord_bot"
$botTrigger = New-ScheduledTaskTrigger -AtLogOn -User $user
# Сторож: раз в 5 минут задача пробует стартовать снова. Живой бот держит
# мьютекс в run-bot.ps1, и повтор просто выходит; убитый — поднимается.
# Нужно потому, что RestartCount Планировщика срабатывает только на ошибку
# ЗАПУСКА: 28.09.2026 бота закрыли сигналом (0xC000013A), и он лежал часами.
$botWatch = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName 'EKB Court Bot' -Action $botAction -Trigger @($botTrigger, $botWatch) `
    -Settings $settings -Description 'EKB SHIELD: Discord-бот Суда, перезапуск при падении' -Force | Out-Null
Write-Host 'Поставлена задача: EKB Court Bot'
Start-ScheduledTask -TaskName 'EKB Court Bot'
Write-Host 'Бот Суда запущен (лог: discord_bot\bot.log)'

# --- сервер ---
if (-not $NoServer) {
    $srvAction = New-ScheduledTaskAction -Execute "$root\server\start.bat" -WorkingDirectory "$root\server"
    $srvTrigger = New-ScheduledTaskTrigger -AtLogOn -User $user
    # Минута после входа: дать подняться сети, иначе DiscordSRV стартует
    # без интернета и бот остаётся оффлайн до перезапуска сервера.
    $srvTrigger.Delay = 'PT1M'
    # Для сервера перезапуск Планировщика выключен: `stop` в консоли — это
    # осознанная остановка (и purge.ps1 так делает), поднимать сервер
    # обратно поверх неё нельзя.
    $srvSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName 'EKB Server' -Action $srvAction -Trigger $srvTrigger `
        -Settings $srvSettings -Description 'EKB SHIELD: сервер Minecraft (и бот DiscordSRV внутри него)' -Force | Out-Null
    Write-Host 'Поставлена задача: EKB Server (старт через минуту после входа в Windows)'
}

Write-Host ''
Write-Host 'Чтобы компьютер не засыпал от сети (иначе боты уходят в оффлайн):'
Write-Host '  powercfg /change standby-timeout-ac 0'
Write-Host '  powercfg /change hibernate-timeout-ac 0'
