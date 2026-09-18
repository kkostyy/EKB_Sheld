# EKB SHIELD — CourtBridge (Java-плагин)

Мост между CoreProtect и Discord: команда `/courtlog` выгружает логи игрока
и отправляет их embed-сообщением в Discord через Webhook — без Node.js-бота.

## Сборка
```bash
cd CourtBridge
mvn clean package
# итоговый файл: target/CourtBridge.jar
```
Положить `CourtBridge.jar` в `plugins/` рядом с `CoreProtect.jar`.

## Настройка
В `plugins/CourtBridge/config.yml` указать Discord Webhook URL
(Настройки канала `#суд` → Интеграции → Вебхуки → Создать вебхук → Копировать URL).

## Использование
```
/courtlog <игрок> <минуты> <радиус> <номер_дела>
```
Пример: `/courtlog Igor 120 50 7` — логи игрока Igor за последние 2 часа
в радиусе 50 блоков от текущей позиции админа, привязать к делу №7.

## Статус
Плагин **собирается** (проверено 2026-09-15): `paper-api 26.1.2.build.74-stable`,
CoreProtect 24.0, JDK 25 — paper-api скомпилирован под class file 69, более старым
JDK сборка не пройдёт. Сигнатура `CoreProtectAPI.performLookup(...)` выверена по jar
CoreProtect 24.0, ID действий взяты из `net.coreprotect.model.action.LookupActions`.

В игре плагин ещё не тестировался — проверь `/courtlog` на тестовом сервере.

## Остаётся учесть
1. Discord Webhook отклонит сообщение, если описание превышает лимиты Discord
   (4096 символов на поле embed) — в коде есть защитная обрезка, но лучше не
   запрашивать слишком большой радиус/период за раз.
2. При обновлении CoreProtect сигнатура API может снова измениться — сверяйся
   с `javap -cp coreprotect.jar net.coreprotect.CoreProtectAPI`.
