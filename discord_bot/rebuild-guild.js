// EKB SHIELD — полная пересборка Discord-сервера в едином оформлении
// «эмодзи・『японское』・русское имя», категории «╭────…», разделители «░░░».
//
// ⚠ Удаление в Discord необратимо. Поэтому:
//   • без --apply скрипт только печатает план;
//   • НЕ удаляются, а переносятся и переименовываются каналы, на чей ID
//     завязаны интеграции. Удалённый канал получил бы новый ID, и связка
//     отвалилась бы молча:
//       main-chat       — Channels.global DiscordSRV (мост с игровым чатом)
//       суд             — COURT_CHANNEL_ID бота + вебхук CourtBridge
//       konsol          — DiscordConsoleChannelId (из него выполняются команды!)
//       logi-minecraft  — Channels.admin-logs (алерты)
//   • категория статистики «サーバーの状態» не трогается — её ведёт ServerStats.
//
// Роль ботов: бот может управлять только ролями НИЖЕ своей высшей роли,
// а его высшая — старая «⚙️・ BOT». Новая роль ставится сразу под неё;
// старую удаляет человек руками (Настройки сервера → Роли).
//
// Запуск:  node rebuild-guild.js           — план
//          node rebuild-guild.js --apply   — выполнить
require('dotenv').config();
const { Client, GatewayIntentBits, ChannelType: T, PermissionFlagsBits: P } = require('discord.js');

const APPLY = process.argv.includes('--apply');
const SEP = '░'.repeat(80);
const KEEP = {
    chat: '1488998869898498090',     // main-chat
    court: process.env.COURT_CHANNEL_ID,
    console: '1549466491668398213',  // konsol
    logs: '1549458246580838442',     // logi-minecraft
};
const BOTS_ROLE = { name: '🤖 『 ⚙️ 』 Bots', color: 0x5E5CE6, hoist: true };

const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMembers] });
client.once('clientReady', async () => {
    try { await run(); } catch (e) { console.error('❌', e); process.exitCode = 1; }
    client.destroy();
});

async function run() {
    const g = await client.guilds.fetch(process.env.GUILD_ID);
    const roles = await g.roles.fetch();
    const all = [...(await g.channels.fetch()).values()].filter(Boolean);
    const me = await g.members.fetchMe();
    const role = part => roles.find(r => r.name.includes(part));
    const R = {
        everyone: g.roles.everyone, admin: role('Admin Staff'), dev: role('Developer'),
        judge: role('Tribunal Judge'), leader: roles.find(r => r.name === '👑・Leader'),
        muted: role('Prisoner'),
    };
    for (const [k, v] of Object.entries(R)) if (!v) throw new Error(`нет роли ${k} — сначала setup-guild.js`);
    const say = s => console.log(s);
    say(`Сервер «${g.name}». Режим: ${APPLY ? 'ВЫПОЛНИТЬ' : 'только план'}\n`);

    // ---------- роль ботов ----------
    let bots = roles.find(r => r.name === BOTS_ROLE.name);
    if (!bots) {
        say(`+ роль ${BOTS_ROLE.name} (под «${me.roles.highest.name}»)`);
        if (APPLY) bots = await g.roles.create({ ...BOTS_ROLE, position: me.roles.highest.position });
    }
    const members = await g.members.fetch();
    for (const m of members.filter(m => m.user.bot).values()) {
        if (bots && m.roles.cache.has(bots.id)) continue;
        say(`+ роль ботов → ${m.user.username}`);
        if (APPLY) await m.roles.add(bots);
    }
    R.bots = bots || { id: 'BOTS' };

    // ---------- права ----------
    const ow = (id, allow = [], deny = []) => ({ id, allow, deny });
    const PERMS = {
        info: [ow(R.everyone.id, [P.ViewChannel], [P.SendMessages, P.CreatePublicThreads]),
               ow(R.admin.id, [P.SendMessages])],
        court: [ow(R.everyone.id, [P.ViewChannel], [P.SendMessages]),
                ow(R.muted.id, [], [P.Connect, P.Speak]),
                ow(R.admin.id, [P.SendMessages]), ow(R.judge.id, [P.SendMessages])],
        chat: [ow(R.muted.id, [], [P.SendMessages, P.AddReactions, P.CreatePublicThreads])],
        voice: [ow(R.muted.id, [], [P.Connect, P.Speak])],
        admin: [ow(R.everyone.id, [], [P.ViewChannel, P.Connect]),
                ow(R.admin.id, [P.ViewChannel, P.SendMessages, P.Connect]),
                ow(R.dev.id, [P.ViewChannel, P.SendMessages, P.Connect]),
                ow(R.bots.id, [P.ViewChannel, P.SendMessages])],
    };

    // ---------- структура ----------
    // keep — ID существующего канала: он переносится и переименовывается.
    // own  — у канала свои права поверх категории (не синхронизировать).
    const TREE = [
        { cat: '╭────📜情報センター📜', perms: 'info', ch: [
            { t: T.GuildText, name: '📢・『お知らせ』・объявления' },
            { t: T.GuildText, name: '📜・『ルール』・правила' },
            { t: T.GuildText, name: '🏛️・『憲法』・конституция' },
            { t: T.GuildText, name: '📖・『刑法』・уголовный-кодекс' },
            { t: T.GuildText, name: '💎・『価格表』・прайс-лист' },
            { t: T.GuildText, name: '🔗・『接続』・как-зайти' },
        ]},
        { cat: '╭────⚖️裁判所⚖️', perms: 'court', ch: [
            // Иск подают здесь командой /иск — писать может каждый, кроме Заключённого.
            { t: T.GuildText, name: '⚖️・『裁判』・суд', keep: KEEP.court,
              own: [ow(R.everyone.id, [P.ViewChannel, P.SendMessages]), ow(R.muted.id, [P.ViewChannel], [P.SendMessages])] },
            // Войну объявляют главы государств (Конституция 5.1).
            { t: T.GuildText, name: '🎖️・『軍事法廷』・военный-трибунал',
              own: [ow(R.everyone.id, [P.ViewChannel], [P.SendMessages]), ow(R.leader.id, [P.SendMessages]),
                    ow(R.judge.id, [P.SendMessages]), ow(R.admin.id, [P.SendMessages])] },
            { t: T.GuildText, name: '🩸・『恥の殿堂』・зал-позора' },
            { t: T.GuildVoice, name: '| ⚖️・『法廷』・Зал Суда' },
            { t: T.GuildVoice, name: '| ⚔️・『軍法会議』・Трибунал' },
        ]},
        { cat: '╭────🏮チャット🏮', perms: 'chat', ch: [
            { t: T.GuildText, name: '💬・『チャット』・общий-чат', keep: KEEP.chat },
            { t: T.GuildText, name: '😂・『ミーム』・мемы' },
            { t: T.GuildText, name: '📷・『メディア』・медиа' },
            { t: T.GuildText, name: '📁・『ファイル』・файлы' },
        ]},
        { cat: '╭────🩸ボイスチャット🩸', perms: 'voice', ch: [
            { t: T.GuildVoice, name: '| 🔊・『ロビー』・Лобби #1' },
            { t: T.GuildVoice, name: '| 🔊・『ロビー』・Лобби #2' },
            { t: T.GuildVoice, name: '| 🔊・『ビルド』・Стройка' },
            { t: T.GuildVoice, name: '| 🔊・『ファーム』・Фарм' },
            { t: T.GuildVoice, name: '| 🌙・『チルゾーン』・Чилл' },
            { t: T.GuildVoice, name: '| 🔇・『AFK』・AFK', afk: true },
        ]},
        { cat: '╭────🕋管理室🕋', perms: 'admin', ch: [
            { t: T.GuildText, name: '📋・『ログ』・логи-minecraft', keep: KEEP.logs },
            // ⚠ Из консоли выполняются команды сервера — только Administrator
            // (главный админ). Admin Staff и Developer её не видят.
            { t: T.GuildText, name: '🖥️・『コンソール』・консоль', keep: KEEP.console,
              own: [ow(R.everyone.id, [], [P.ViewChannel, P.Connect])] },
            { t: T.GuildText, name: '🕵️・『契約』・аудит-контрактов' },
            { t: T.GuildText, name: '🔍・『証拠』・аудит-улик' },
            { t: T.GuildText, name: '💣・『戦争』・аудит-войн' },
            { t: T.GuildVoice, name: '| 🔒・『会議』・Совещание' },
        ]},
    ];

    const stats = all.find(c => c.type === T.GuildCategory && c.name.includes('サーバーの状態'));
    const keepIds = new Set([...Object.values(KEEP), stats && stats.id,
        ...all.filter(c => stats && c.parentId === stats.id).map(c => c.id)]);

    // ---------- 1. создать новое, перенести сохраняемое ----------
    const order = [];   // итоговый порядок категорий
    if (stats) order.push(stats);
    let afk = null;
    for (const block of TREE) {
        say(`\n+ разделитель «░░░»\n+ категория ${block.cat}`);
        let sep = null, cat = null;
        if (APPLY) {
            sep = await g.channels.create({ name: SEP, type: T.GuildCategory });  // пустая, только для вида
            cat = await g.channels.create({ name: block.cat, type: T.GuildCategory,
                permissionOverwrites: PERMS[block.perms] });
            order.push(sep, cat);
        }
        for (const spec of block.ch) {
            const icon = spec.t === T.GuildVoice ? '🔊' : '#';
            if (spec.keep) {
                const ex = all.find(c => c.id === spec.keep);
                say(`   ~ ${icon} ${ex ? ex.name : spec.keep} → ${spec.name} (перенос, ID сохраняется)`);
                if (APPLY && ex) {
                    await ex.edit({ name: spec.name, parent: cat.id, lockPermissions: false });
                    await ex.permissionOverwrites.set(spec.own || PERMS[block.perms]);
                }
                continue;
            }
            say(`   + ${icon} ${spec.name}`);
            if (APPLY) {
                const ch = await g.channels.create({ name: spec.name, type: spec.t, parent: cat.id,
                    permissionOverwrites: spec.own || PERMS[block.perms] });
                if (spec.afk) afk = ch;
            }
        }
    }

    // ---------- 2. удалить остальное ----------
    const doomed = all.filter(c => !keepIds.has(c.id));
    say(`\n- удалить ${doomed.length} каналов/категорий:`);
    for (const c of doomed.sort((a, b) => a.rawPosition - b.rawPosition))
        say(`   - ${c.type === T.GuildCategory ? 'КАТ' : c.type === T.GuildVoice ? '🔊' : '#'} ${c.name}`);
    if (APPLY) for (const c of doomed) await c.delete('Пересборка сервера EKB SHIELD').catch(e => say(`   ! ${c.name}: ${e.message}`));

    // ---------- 3. порядок и AFK ----------
    if (APPLY) {
        await g.channels.setPositions(order.map((c, i) => ({ channel: c.id, position: i })));
        if (afk) await g.setAFKChannel(afk);
        say('\nГотово. Старую роль «⚙️・ BOT» удалить руками: Настройки сервера → Роли.');
    }
}

client.login(process.env.DISCORD_TOKEN);
