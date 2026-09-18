require("dotenv").config();
const fs = require("fs");
const path = require("path");
const {
  Client,
  GatewayIntentBits,
  EmbedBuilder,
  ChannelType,
  PermissionsBitField,
} = require("discord.js");

const DB_PATH = path.join(__dirname, "cases.json");

function loadCases() {
  if (!fs.existsSync(DB_PATH)) return { nextId: 1, cases: [] };
  return JSON.parse(fs.readFileSync(DB_PATH, "utf8"));
}

function saveCases(db) {
  fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2), "utf8");
}

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages],
});

client.once("ready", () => {
  console.log(`Бот Суда EKB SHIELD запущен как ${client.user.tag}`);
});

client.on("interactionCreate", async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  // ---------- /иск ----------
  if (interaction.commandName === "иск") {
    const defendant = interaction.options.getString("ответчик");
    const article = interaction.options.getString("статья");
    const description = interaction.options.getString("описание");
    const coords = interaction.options.getString("координаты") || "не указаны";

    const db = loadCases();
    const caseId = db.nextId;
    db.nextId += 1;

    const newCase = {
      id: caseId,
      plaintiff: interaction.user.tag,
      defendant,
      article,
      description,
      coords,
      status: "open",
      createdAt: new Date().toISOString(),
      verdict: null,
    };
    db.cases.push(newCase);
    saveCases(db);

    const embed = new EmbedBuilder()
      .setColor(0xaa0000)
      .setTitle(`⚖️ Иск №${caseId}`)
      .addFields(
        { name: "Истец", value: newCase.plaintiff, inline: true },
        { name: "Ответчик", value: defendant, inline: true },
        { name: "Статья УК", value: article, inline: false },
        { name: "Описание", value: description, inline: false },
        { name: "Координаты", value: coords, inline: false },
        { name: "Статус", value: "🟡 На рассмотрении", inline: false }
      )
      .setTimestamp();

    const courtChannel = await client.channels.fetch(process.env.COURT_CHANNEL_ID);
    const sentMessage = await courtChannel.send({ embeds: [embed] });

    // Создаём тред для сбора доказательств по делу
    const thread = await sentMessage.startThread({
      name: `Дело №${caseId} — ${defendant}`,
      autoArchiveDuration: 1440,
      type: ChannelType.PublicThread,
    });
    await thread.send(
      `Тред открыт для дела №${caseId}. Прикрепите скриншоты/координаты/логи CoreProtect (\`/co lookup\`) в качестве доказательств.`
    );

    await interaction.reply({
      content: `✅ Иск №${caseId} подан и опубликован в <#${process.env.COURT_CHANNEL_ID}>.`,
      ephemeral: true,
    });
  }

  // ---------- /дела ----------
  if (interaction.commandName === "дела") {
    const db = loadCases();
    const openCases = db.cases.filter((c) => c.status === "open");

    if (openCases.length === 0) {
      await interaction.reply({ content: "Открытых дел нет.", ephemeral: true });
      return;
    }

    const embed = new EmbedBuilder()
      .setColor(0x0055aa)
      .setTitle("📋 Открытые дела EKB SHIELD")
      .setDescription(
        openCases
          .map((c) => `**№${c.id}** — ${c.defendant} (${c.article})`)
          .join("\n")
      );

    await interaction.reply({ embeds: [embed] });
  }

  // ---------- /закрыть_дело ----------
  if (interaction.commandName === "закрыть_дело") {
    const isAdmin = interaction.member.roles.cache.has(process.env.ADMIN_ROLE_ID);
    if (!isAdmin) {
      await interaction.reply({
        content: "❌ У тебя нет прав закрывать дела (нужна роль Судьи/Администрации).",
        ephemeral: true,
      });
      return;
    }

    const caseNumber = interaction.options.getInteger("номер");
    const verdict = interaction.options.getString("вердикт");

    const db = loadCases();
    const caseObj = db.cases.find((c) => c.id === caseNumber);
    if (!caseObj) {
      await interaction.reply({ content: `Дело №${caseNumber} не найдено.`, ephemeral: true });
      return;
    }

    caseObj.status = "closed";
    caseObj.verdict = verdict;
    saveCases(db);

    const embed = new EmbedBuilder()
      .setColor(0x00aa00)
      .setTitle(`⚖️ Дело №${caseNumber} закрыто`)
      .addFields(
        { name: "Ответчик", value: caseObj.defendant, inline: true },
        { name: "Вердикт", value: verdict, inline: false }
      )
      .setTimestamp();

    const courtChannel = await client.channels.fetch(process.env.COURT_CHANNEL_ID);
    await courtChannel.send({ embeds: [embed] });

    await interaction.reply({ content: `✅ Дело №${caseNumber} закрыто.`, ephemeral: true });
  }
});

client.login(process.env.DISCORD_TOKEN);
