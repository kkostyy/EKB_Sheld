require("dotenv").config();
const { REST, Routes, SlashCommandBuilder } = require("discord.js");

const commands = [
  new SlashCommandBuilder()
    .setName("иск")
    .setDescription("Подать иск в Суд EKB SHIELD")
    .addStringOption((opt) =>
      opt.setName("ответчик").setDescription("Ник игрока-ответчика").setRequired(true)
    )
    .addStringOption((opt) =>
      opt.setName("статья").setDescription("Статья УК (например: Статья 4 — FreeKill)").setRequired(true)
    )
    .addStringOption((opt) =>
      opt.setName("описание").setDescription("Описание произошедшего").setRequired(true)
    )
    .addStringOption((opt) =>
      opt.setName("координаты").setDescription("Координаты места (мир, x y z)").setRequired(false)
    )
    .toJSON(),

  new SlashCommandBuilder()
    .setName("дела")
    .setDescription("Показать список открытых дел")
    .toJSON(),

  new SlashCommandBuilder()
    .setName("закрыть_дело")
    .setDescription("Закрыть дело по номеру (только Судья/Администрация)")
    .addIntegerOption((opt) =>
      opt.setName("номер").setDescription("Номер дела").setRequired(true)
    )
    .addStringOption((opt) =>
      opt.setName("вердикт").setDescription("Итоговое решение суда").setRequired(true)
    )
    .toJSON(),
];

const rest = new REST({ version: "10" }).setToken(process.env.DISCORD_TOKEN);

(async () => {
  try {
    console.log("Регистрация слэш-команд...");
    await rest.put(
      Routes.applicationGuildCommands(process.env.CLIENT_ID, process.env.GUILD_ID),
      { body: commands }
    );
    console.log("Слэш-команды успешно зарегистрированы.");
  } catch (error) {
    console.error(error);
  }
})();
