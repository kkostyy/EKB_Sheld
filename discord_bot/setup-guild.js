// EKB SHIELD — достройка Discord-сервера: роли, категории, каналы.
//
// Основа — присланный план (gemini-code-1790606648060.js), но он создавал
// всё с нуля, а сервер уже живой: 43 канала и 15 ролей. Запуск «как есть»
// наплодил бы дублей rules, hall-of-shame, main-chat и второй суд рядом с
// настоящим #суд, куда пишет бот (COURT_CHANNEL_ID). Поэтому здесь всё
// ИДЕМПОТЕНТНО: существующее находится по имени и переиспользуется,
// создаётся только недостающее, второй запуск ничего не меняет.
//
// Что сознательно НЕ так, как в плане:
//   • полные права (Administrator) только у Admin Staff. Developer — без них:
//     вторая роль-«бог» означает, что Discord может снести любой, кому её
//     выдали, а в игре тот же принцип держит restricted_admin;
//   • роль Leader НЕ создаётся — на сервере уже есть «👑・Leader»;
//   • у существующих каналов права @everyone не трогаются. Добавляются
//     только правила для НОВЫХ ролей (запрет Заключённому, право судьи
//     писать в трибунал) — это ничего не отбирает у тех, кто уже там;
//   • счётчики статистики не создаются: их ведёт бот ServerStats, а
//     «Players Online: 0» из плана — застывшая надпись, её никто не обновлял бы;
//   • разделители «░░░» и «PlasmoBridge» не создаются: разделителей и так
//     пять, а моста между Plasmo Voice и Discord в проекте нет — канал с
//     таким именем обещал бы то, чего нет.
//
// Запуск:
//   node setup-guild.js           — показать план, ничего не меняя
//   node setup-guild.js --apply   — применить
//   node setup-guild.js --roles-only [--apply] — только роли и synchronization.yml
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { Client, GatewayIntentBits, ChannelType, PermissionFlagsBits: P } = require('discord.js');

const APPLY = process.argv.includes('--apply');
// ⚠ После rebuild-guild.js каналы названы иначе, чем ждёт этот план, и
// полный --apply наплодил бы дублей. Роли и их синхронизацию с игрой
// ставит --roles-only, каналы он не трогает.
const ROLES_ONLY = process.argv.includes('--roles-only');

// Сравнение имён без эмодзи, рамок и регистра: «📜・『ルール』・rules» и
// «rules» — один канал. Кандзи из имён тоже выбрасываются: в плане
// «サーバーの狀態», а на сервере «サーバーの状態» (другой иероглиф).
const norm = s => s.toLowerCase().replace(/[^a-zа-яё0-9#-]+/g, ' ').trim();
const hasWord = (name, word) => norm(name).split(' ').includes(word) || norm(name).endsWith(word);

const ROLES = [
    { key: 'admin', name: '👑 『 🛡️ 』 Admin Staff', color: 0xFF375F, hoist: true, mentionable: true, permissions: [P.Administrator] },
    { key: 'dev', name: '💻 『 ⚙️ 』 Developer', color: 0xBF5AF2, hoist: true, mentionable: true, permissions: [] },
    // `lp` — группа LuckPerms, с которой роль синхронизируется в обе стороны
    // через DiscordSRV (synchronization.yml пишется этим же скриптом).
    { key: 'mod', name: '🛡️ 『 ⚔️ 』 Moderator', color: 0xFF9F0A, hoist: true, mentionable: true, lp: 'restricted_admin' },
    { key: 'judge', name: '⚖️ 『 📜 』 Tribunal Judge', color: 0xFFD60A, hoist: true, mentionable: true, lp: 'judge' },
    { key: 'guard', name: '👮 『 🛡️ 』 Guard', color: 0x0A84FF, hoist: true, lp: 'guard' },
    { key: 'leader', name: '🏰 『 👑 』 Leader', color: 0x30D158, hoist: true, mentionable: true, reuse: 'leader' },
    { key: 'citizen', name: '📜 『 👤 』 Citizen', color: 0x64D2FF, hoist: true, lp: 'citizen' },
    { key: 'nomad', name: '🏕️ 『 🌲 』 Nomad', color: 0x98989D, hoist: true, lp: 'nomad' },
    { key: 'muted', name: '🔇 『 ⛓️ 』 Prisoner / Muted', color: 0x3A3A3C, hoist: true, permissions: [] },
    // Остальные игровые роли (menu_roles.sk). Без hoist: шестнадцать
    // отдельных блоков в списке участников утопили бы основные.
    // ⚠ «👑・Leader» наверху — роль ВЛАДЕЛЬЦА Discord, а не главы города:
    // главе города заведена своя роль Mayor, иначе синхронизация раздала
    // бы мэрам верх Discord-иерархии.
    // ⚠ Не синхронизируются намеренно: Admin Staff (группа admin через
    // Discord выдаваться не должна, как и через меню ролей) и Теневое
    // Сообщество — список участников роли в Discord видят все.
    { key: 'doctor', name: '🩺 Doctor', color: 0xFF6B6B, lp: 'doctor' },
    { key: 'capital', name: '🔔 Spawn Resident', color: 0x8FD3FF, lp: 'capital' },
    { key: 'mayor', name: '🏰 Mayor', color: 0x30D158, mentionable: true, lp: 'mayor' },
    { key: 'council', name: '🎩 Councillor', color: 0x5BC87A, lp: 'council' },
    { key: 'treasurer', name: '💰 Treasurer', color: 0xE0B84F, lp: 'treasurer' },
    { key: 'sheriff', name: '⭐ Sheriff', color: 0x3D7EFF, mentionable: true, lp: 'sheriff' },
    { key: 'builder', name: '⛏️ Builder', color: 0xB0874F, lp: 'builder' },
    { key: 'postman', name: '✉️ Postman', color: 0xC9A66B, lp: 'postman' },
    { key: 'clerk', name: '📋 Clerk', color: 0xA0A0C8, lp: 'clerk' },
    { key: 'barman', name: '🍺 Barman', color: 0xD9913A, lp: 'barman' },
    { key: 'dealer', name: '🎲 Croupier', color: 0x9B6BD6, lp: 'dealer' },
    { key: 'detective', name: '🔍 Detective', color: 0x6F8FAF, lp: 'detective' },
    { key: 'journalist', name: '📰 Journalist', color: 0xE8E8E8, lp: 'journalist' },
    { key: 'streamer', name: '🎥 Streamer', color: 0x9146FF, lp: 'streamer' },
    { key: 'youtuber', name: '▶️ YouTuber', color: 0xFF0000, lp: 'youtuber' },
];

// Карта «группа LuckPerms -> ID роли» для DiscordSRV. Ключ одной строкой
// JSON — ровно в том виде, в каком DiscordSRV кладёт его сам. Пишется и в
// репозиторий, и в установленный сервер: ID ролей знает только Discord,
// руками их переписывать — верный способ перепутать две роли.
const SYNC_KEY = 'GroupRoleSynchronizationGroupsAndRolesToSync';
function writeGroupSync(R) {
    const map = {};
    for (const s of ROLES) if (s.lp && R[s.key]) map[s.lp] = R[s.key].id;
    const line = `${SYNC_KEY}: ${JSON.stringify(map)}`;
    for (const rel of ['../plugins/DiscordSRV/synchronization.yml', '../server/plugins/DiscordSRV/synchronization.yml']) {
        const file = path.join(__dirname, rel);
        if (!fs.existsSync(file)) { plan(`! нет ${rel} — синхронизация ролей не записана`); continue; }
        const src = fs.readFileSync(file, 'utf8');
        const next = src.replace(new RegExp(`^${SYNC_KEY}:.*$`, 'm'), line);
        if (next === src) { plan(`= синхронизация ролей: ${rel}`); continue; }
        plan(`~ синхронизация ролей (${Object.keys(map).length} групп): ${rel}`);
        if (APPLY) fs.writeFileSync(file, next, 'utf8');
    }
}

const log = [];
const plan = (what) => log.push(what);

const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.once('clientReady', async () => {
    try {
        await run();
    } catch (e) {
        console.error('❌', e);
        process.exitCode = 1;
    }
    client.destroy();
});

async function run() {
    const guild = await client.guilds.fetch(process.env.GUILD_ID);
    const roles = await guild.roles.fetch();
    const chans = await guild.channels.fetch();
    console.log(`Сервер «${guild.name}». Режим: ${APPLY ? 'ПРИМЕНИТЬ' : 'только план'}\n`);

    // ---- роли ----
    const R = {};
    for (const spec of ROLES) {
        let r = roles.find(x => x.name === spec.name);
        if (!r && spec.reuse) r = roles.find(x => norm(x.name) === spec.reuse);  // точно «leader», не «co-leader»
        if (r) {
            R[spec.key] = r;
            plan(`= роль есть: ${r.name}`);
            continue;
        }
        plan(`+ роль: ${spec.name}${spec.permissions && spec.permissions.length ? ' (Administrator)' : ''}`);
        if (APPLY) {
            const { key, reuse, lp, ...data } = spec;
            R[spec.key] = await guild.roles.create(data);
        }
    }
    writeGroupSync(R);
    if (ROLES_ONLY) {
        console.log(log.join('\n'));
        return;
    }

    // ---- поиск существующего ----
    const find = (pred) => chans.find(x => x && pred(x));
    const text = (word) => find(x => x.type === ChannelType.GuildText && hasWord(x.name, word));
    const voice = (word) => find(x => x.type === ChannelType.GuildVoice && hasWord(x.name, word));
    const parentOf = (ch) => ch && ch.parent;

    // Категории находятся по каналу, который в них уже лежит: имена у
    // категорий декоративные («░░░…», «╭────🏮Чат…»), по ним не найти.
    const court = chans.get(process.env.COURT_CHANNEL_ID);
    const catInfo = parentOf(text('rules')) || parentOf(court);
    const catChat = parentOf(text('main-chat'));
    const catVoice = parentOf(voice('lobby'));

    // Правило для новой роли на существующем канале/категории — добавляется,
    // остальные правила не трогаются.
    async function allowFor(ch, roleKey, allow, deny, label) {
        const role = R[roleKey];
        const cur = role && ch.permissionOverwrites.cache.get(role.id);
        if (cur) return;
        plan(`~ ${label}: правило для роли ${role ? role.name : ROLES.find(s => s.key === roleKey).name}`);
        if (APPLY && role) await ch.permissionOverwrites.create(role, Object.fromEntries([
            ...allow.map(p => [p, true]), ...deny.map(p => [p, false])]));
    }
    const everyone = guild.roles.everyone;

    async function ensureText(word, name, parent, extra = {}) {
        const ex = text(word);
        if (ex) { plan(`= канал есть: #${ex.name}`); return ex; }
        plan(`+ канал: #${name}${parent ? ` в «${parent.name}»` : ''}`);
        if (!APPLY) return null;
        return guild.channels.create({ name, type: ChannelType.GuildText, parent: parent && parent.id, ...extra });
    }
    async function ensureVoice(word, name, parent) {
        const ex = voice(word);
        if (ex) { plan(`= голосовой есть: ${ex.name}`); return ex; }
        plan(`+ голосовой: ${name}${parent ? ` в «${parent.name}»` : ''}`);
        if (!APPLY) return null;
        return guild.channels.create({ name, type: ChannelType.GuildVoice, parent: parent && parent.id });
    }

    // ---- информация и законы ----
    if (catInfo) {
        await allowFor(catInfo, 'muted', [], ['ViewChannel'], `категория «${catInfo.name}»`);
        await allowFor(catInfo, 'admin', ['SendMessages'], [], `категория «${catInfo.name}»`);
    }
    await ensureText('criminal-code', '📖・『уголовный-кодекс』・criminal-code', catInfo, {
        permissionOverwrites: [{ id: everyone.id, allow: [P.ViewChannel], deny: [P.SendMessages] }],
    });
    await ensureText('server-status', '🟢・『接続』・server-status', catInfo, {
        permissionOverwrites: [{ id: everyone.id, allow: [P.ViewChannel], deny: [P.SendMessages] }],
    });
    if (court) {
        plan(`= суд: #${court.name} (COURT_CHANNEL_ID — второй «court» не создаётся)`);
        await allowFor(court, 'muted', [], ['SendMessages'], `#${court.name}`);
    }
    const tribunal = text('военный-трибунал') || text('military-tribunal');
    if (tribunal) {
        plan(`= трибунал есть: #${tribunal.name}`);
        await allowFor(tribunal, 'judge', ['SendMessages'], [], `#${tribunal.name}`);
        await allowFor(tribunal, 'leader', ['SendMessages'], [], `#${tribunal.name}`);
        await allowFor(tribunal, 'admin', ['SendMessages'], [], `#${tribunal.name}`);
    }
    await ensureText('hall-of-shame', '🩸・『恥の殿堂』・hall-of-shame', catInfo);
    await ensureText('announcements', '📢・『お知らせ』・announcements', catInfo);

    // ---- чат ----
    if (catChat) await allowFor(catChat, 'muted', [], ['SendMessages'], `категория «${catChat.name}»`);
    for (const [w, n] of [['main-chat', '💬・『チャット』・main-chat'], ['memes', '😂・『ミーム』・memes'],
                          ['media', '📷・『メディア』・media'], ['files', '📁・『ファイル』・files']]) {
        await ensureText(w, n, catChat);
    }

    // ---- закрытые логи ----
    // Видят только Admin Staff и Developer (и сам бот — у него Administrator).
    let catLogs = find(x => x.type === ChannelType.GuildCategory && hasWord(x.name, 'logs') && norm(x.name).includes('admin'));
    if (catLogs) plan(`= категория есть: ${catLogs.name}`);
    else {
        plan('+ категория: 🔒 『 秘密 』 Admin Logs (только Admin Staff и Developer)');
        if (APPLY) catLogs = await guild.channels.create({
            name: '🔒 『 秘密 』 Admin Logs', type: ChannelType.GuildCategory,
            permissionOverwrites: [
                { id: everyone.id, deny: [P.ViewChannel] },
                { id: R.admin.id, allow: [P.ViewChannel, P.SendMessages] },
                { id: R.dev.id, allow: [P.ViewChannel, P.SendMessages] },
            ],
        });
    }
    for (const [w, n] of [['contracts-audit', '🕵️・contracts-audit'], ['evidence-audit', '🔍・evidence-audit'],
                          ['war-audit', '💣・war-audit']]) {
        await ensureText(w, n, catLogs);
    }

    // ---- голос ----
    if (catVoice) await allowFor(catVoice, 'muted', [], ['Connect', 'Speak'], `категория «${catVoice.name}»`);
    await ensureVoice('lobby', '🔊・『ロビー』・Lobby', catVoice);
    await ensureVoice('court room', '⚖️・『Зал Суда』・Court Room', catVoice);
    await ensureVoice('tribunal room', '⚔️・『Трибунал』・Tribunal Room', catVoice);
    await ensureVoice('afk', '💤・『AFK』・Rest Room', catVoice);

    console.log(log.join('\n'));
    const todo = log.filter(l => !l.startsWith('=')).length;
    console.log(`\n${APPLY ? 'Применено' : 'К изменению'}: ${todo}. ${APPLY ? '' : 'Применить: node setup-guild.js --apply'}`);
}

client.login(process.env.DISCORD_TOKEN);
