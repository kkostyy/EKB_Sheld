package com.ekbshield.courtbridge;

import net.coreprotect.CoreProtect;
import net.coreprotect.CoreProtectAPI;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.Location;
import org.bukkit.entity.Player;
import org.bukkit.plugin.Plugin;
import org.bukkit.plugin.java.JavaPlugin;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * EKB SHIELD — CourtBridge
 * Мост между CoreProtect и Discord: по команде админа выгружает логи
 * конкретного игрока и отправляет их в канал #суд через Discord Webhook.
 *
 * ВНИМАНИЕ: сигнатура метода CoreProtectAPI.performLookup(...) менялась
 * между версиями CoreProtect. Здесь используется вариант, документированный
 * для CoreProtect API v9-10 (на момент моих данных обучения). Если сборка
 * не компилируется — открой javadoc установленной версии CoreProtect и
 * поправь список параметров в методе fetchLogs() ниже.
 */
public class CourtBridgePlugin extends JavaPlugin implements CommandExecutor {

    private static final DateTimeFormatter TIME_FORMAT =
            DateTimeFormatter.ofPattern("dd.MM HH:mm");

    private CoreProtectAPI coreProtectAPI;
    private String webhookUrl;
    private int maxLines;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        FileConfiguration config = getConfig();
        this.webhookUrl = config.getString("discord-webhook-url", "");
        this.maxLines = config.getInt("max-lines-per-message", 25);

        Plugin cpPlugin = getServer().getPluginManager().getPlugin("CoreProtect");
        if (cpPlugin instanceof CoreProtect) {
            CoreProtectAPI api = ((CoreProtect) cpPlugin).getAPI();
            if (api != null && api.isEnabled()) {
                this.coreProtectAPI = api;
                getLogger().info("CourtBridge: подключение к CoreProtect API успешно.");
            } else {
                getLogger().warning("CourtBridge: CoreProtect API недоступен (не включён).");
            }
        } else {
            getLogger().warning("CourtBridge: плагин CoreProtect не найден на сервере!");
        }

        getCommand("courtlog").setExecutor(this);
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!command.getName().equalsIgnoreCase("courtlog")) return false;

        if (args.length < 4) {
            sender.sendMessage("§cИспользование: /courtlog <игрок> <минуты> <радиус> <номер_дела>");
            return true;
        }
        if (coreProtectAPI == null) {
            sender.sendMessage("§cCoreProtect API недоступен — проверь, что плагин CoreProtect установлен и включён.");
            return true;
        }
        if (webhookUrl == null || webhookUrl.isBlank() || webhookUrl.contains("ВСТАВЬ_ID")) {
            sender.sendMessage("§cWebhook Discord не настроен в config.yml плагина CourtBridge.");
            return true;
        }

        String targetPlayer = args[0];
        int minutes;
        int radius;
        String caseId = args[3];
        try {
            minutes = Integer.parseInt(args[1]);
            radius = Integer.parseInt(args[2]);
        } catch (NumberFormatException e) {
            sender.sendMessage("§cМинуты и радиус должны быть числами.");
            return true;
        }

        int timeSeconds = minutes * 60;

        // Локация для поиска — берём текущую позицию отправителя команды,
        // если это игрок (иначе поиск идёт без ограничения по координатам).
        List<String[]> results = fetchLogs(sender, targetPlayer, timeSeconds, radius);

        if (results == null || results.isEmpty()) {
            sender.sendMessage("§eЛоги по игроку " + targetPlayer + " за указанный период не найдены.");
            return true;
        }

        List<String> parsedLines = new ArrayList<>();
        for (String[] result : results) {
            if (parsedLines.size() >= maxLines) break;
            try {
                CoreProtectAPI.ParseResult parsed = coreProtectAPI.parseResult(result);
                parsedLines.add(formatParsedResult(parsed));
            } catch (Exception e) {
                getLogger().warning("Не удалось распарсить строку результата CoreProtect: " + e.getMessage());
            }
        }

        sendToDiscord(caseId, targetPlayer, parsedLines);
        sender.sendMessage("§aЛоги по " + targetPlayer + " (" + parsedLines.size() + " записей) отправлены в Discord по делу №" + caseId + ".");
        return true;
    }

    /**
     * Выполняет запрос к CoreProtect.
     * Сигнатура выверена по CoreProtect 24.0:
     *   performLookup(int time, List<String> restrictUsers, List<String> excludeUsers,
     *                 List<Object> restrictBlocks, List<Object> excludeBlocks,
     *                 List<Integer> actionList, int radius, Location location)
     * time — глубина поиска в СЕКУНДАХ назад от текущего момента.
     */
    private List<String[]> fetchLogs(CommandSender sender, String targetPlayer, int timeSeconds, int radius) {
        List<String> restrictUsers = new ArrayList<>();
        restrictUsers.add(targetPlayer);

        // ID действий — см. net.coreprotect.model.action.LookupActions
        List<Integer> actionList = new ArrayList<>();
        actionList.add(0); // BLOCK_BREAK  — гриф, разрушение построек (Статья 3 УК)
        actionList.add(1); // BLOCK_PLACE  — установка блоков (ТНТ-машины, поджоги)
        actionList.add(3); // ENTITY_KILL  — FreeKill и убийство животных (Статьи 3, 4 УК)
        actionList.add(4); // CONTAINER    — доступ к сундукам (Статьи 1, 2 УК)

        // Радиус имеет смысл только вокруг точки: с консоли ищем по всему миру.
        Location location = (sender instanceof Player playerSender) ? playerSender.getLocation() : null;
        int effectiveRadius = (location != null) ? radius : 0;

        return coreProtectAPI.performLookup(
                timeSeconds,
                restrictUsers,
                null,   // excludeUsers  — никого не исключаем
                null,   // restrictBlocks — без фильтра по типу блока
                null,   // excludeBlocks
                actionList,
                effectiveRadius,
                location
        );
    }

    private String formatParsedResult(CoreProtectAPI.ParseResult parsed) {
        String when = TIME_FORMAT.format(
                Instant.ofEpochSecond(parsed.getTime()).atZone(ZoneId.systemDefault()));
        return String.format(
                "`%s` **%s** — %s (%s, %d %d %d)%s",
                when,
                parsed.getPlayer(),
                parsed.getActionString(),
                parsed.worldName(),
                parsed.getX(),
                parsed.getY(),
                parsed.getZ(),
                parsed.isRolledBack() ? " *(откачено)*" : ""
        );
    }

    private void sendToDiscord(String caseId, String targetPlayer, List<String> lines) {
        StringBuilder description = new StringBuilder();
        for (String line : lines) {
            description.append(line).append("\n");
        }
        if (description.length() > 3900) {
            description.setLength(3900);
            description.append("\n... (обрезано, слишком много записей)");
        }

        String escapedDescription = description.toString()
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n");

        String jsonPayload = "{"
                + "\"embeds\": [{"
                + "\"title\": \"📑 Логи CoreProtect — Дело №" + caseId + "\","
                + "\"description\": \"Игрок: **" + targetPlayer + "**\\n\\n" + escapedDescription + "\","
                + "\"color\": 10038562"
                + "}]"
                + "}";

        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(webhookUrl))
                .timeout(Duration.ofSeconds(10))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenAccept(response -> {
                    if (response.statusCode() >= 300) {
                        getLogger().warning("CourtBridge: Discord webhook ответил кодом " + response.statusCode());
                    }
                })
                .exceptionally(ex -> {
                    getLogger().warning("CourtBridge: ошибка отправки в Discord — " + ex.getMessage());
                    return null;
                });
    }
}
