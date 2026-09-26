package com.ekbshield.creative;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.network.chat.TextColor;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.item.component.ItemLore;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Вкладка творческого инвентаря с предметами конопли сервера EKB SHIELD.
 *
 * <p>Зачем мод, а не плагин: {@code CreativeModeTab} собирается НА КЛИЕНТЕ
 * из его собственных реестров — сервер их не шлёт, и ни плагин, ни датапак,
 * ни ресурспак туда ничего не добавляют. Вкладку может дать только
 * клиентский мод, а он у нас есть: сервер раздаёт свой модпак.
 *
 * <p>В списке только конопля. Напитки BreweryX, стволы QualityArmory,
 * настолки TablePlays, артефакты и Тетрадь Смерти — нет: у них внутри данные
 * плагина (закодированный рецепт, NBT-метка ствола) или номер экземпляра в
 * реестре скрипта, и клиент такой предмет собрать не может. Вышла бы копия,
 * которая правильно выглядит и не работает, а артефакты с Тетрадью ещё и
 * обошли бы лимит «два на мир». Их по-прежнему выдают каталоги
 * {@code /allitems} и {@code /newitems}.
 *
 * <p>Список лежит в {@code creative_items.json} и генерируется из
 * {@code docs/nirvana.sk} скриптом {@code build_creative_items.py}: править
 * его руками нельзя — разойдётся со скриптом, и сервер перестанет опознавать
 * предмет, который клиент выдал.
 *
 * <p>⚠ Имена классов здесь официальные имена 26.x, а не yarn и не старые
 * mojmap: клиент 26.1.2 поставляется РАЗОБФУСЦИРОВАННЫМ, маппингов Mojang
 * для него больше не публикует, и часть классов переименована
 * ({@code ResourceLocation} стал {@code Identifier}).
 */
public class EkbCreativeTab implements ClientModInitializer {
    public static final String MOD_ID = "ekbshield";
    private static final Logger LOG = LoggerFactory.getLogger("EKB SHIELD");
    private static final String ITEMS_PATH = "/assets/ekbshield/creative_items.json";

    /** Иконка вкладки — Шишка: вкладку узнают по ней раньше, чем прочитают подпись. */
    private static final int ICON_CMD = 2003;

    private static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
            Registries.CREATIVE_MODE_TAB,
            Identifier.fromNamespaceAndPath(MOD_ID, "items"));

    @Override
    public void onInitializeClient() {
        List<ItemStack> stacks = load();
        if (stacks.isEmpty()) {
            LOG.warn("[EKB SHIELD] список предметов пуст — вкладка не добавлена");
            return;
        }

        ItemStack icon = stacks.get(0);
        for (ItemStack stack : stacks) {
            CustomModelData cmd = stack.get(DataComponents.CUSTOM_MODEL_DATA);
            if (cmd != null && !cmd.floats().isEmpty()
                    && cmd.floats().get(0).intValue() == ICON_CMD) {
                icon = stack;
            }
        }
        final ItemStack tabIcon = icon.copy();

        Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY,
                FabricCreativeModeTab.builder()
                        .title(Component.literal("EKB SHIELD"))
                        .icon(() -> tabIcon)
                        .build());

        // ⚠ Содержимое добавляется событием, а не `displayItems(...)` у
        // строителя: в 26.x вложенный `CreativeModeTab.Output` объявлен
        // protected, и снаружи на него даже сослаться нельзя — javac падает
        // на «Output has protected access». Fabric отдаёт свой публичный
        // `FabricCreativeModeTabOutput` через это событие.
        CreativeModeTabEvents.modifyOutputEvent(TAB_KEY).register(output -> {
            for (ItemStack stack : stacks) {
                output.accept(stack.copy());
            }
        });

        LOG.info("[EKB SHIELD] вкладка креатива: {} предметов", stacks.size());
    }

    private List<ItemStack> load() {
        List<ItemStack> out = new ArrayList<>();
        try (InputStream in = EkbCreativeTab.class.getResourceAsStream(ITEMS_PATH)) {
            if (in == null) {
                LOG.error("[EKB SHIELD] не найден {}", ITEMS_PATH);
                return out;
            }
            JsonObject root = JsonParser.parseReader(
                    new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            for (JsonElement el : root.getAsJsonArray("items")) {
                ItemStack stack = build(el.getAsJsonObject());
                if (stack != null) {
                    out.add(stack);
                }
            }
        } catch (Exception e) {
            LOG.error("[EKB SHIELD] не прочитался список предметов", e);
        }
        return out;
    }

    private ItemStack build(JsonObject spec) {
        Identifier id = Identifier.parse(spec.get("item").getAsString());
        Item item = BuiltInRegistries.ITEM.getValue(id);
        if (item == null) {
            LOG.warn("[EKB SHIELD] нет такого предмета: {}", id);
            return null;
        }

        ItemStack stack = new ItemStack(item);

        // ⚠ Номер кладётся в floats: ресурспак проекта выбирает модель через
        // range_dispatch по custom_model_data, а тот читает именно floats[0].
        // В strings лежат значения для select — с ними модель не найдётся, и
        // предмет отрисуется ванильным (тот же разбор, что в CLAUDE.md).
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(
                List.of((float) spec.get("cmd").getAsInt()),
                List.of(), List.of(), List.of()));

        if (spec.has("name")) {
            stack.set(DataComponents.CUSTOM_NAME, text(spec.getAsJsonArray("name")));
        }
        if (spec.has("lore")) {
            List<Component> lore = new ArrayList<>();
            for (JsonElement row : spec.getAsJsonArray("lore")) {
                lore.add(text(row.getAsJsonArray()));
            }
            stack.set(DataComponents.LORE, new ItemLore(lore));
        }
        return stack;
    }

    /** Кусочки «текст + цвет» из json — в одну строку клиента. */
    private Component text(JsonArray parts) {
        MutableComponent out = Component.empty();
        for (JsonElement el : parts) {
            JsonObject part = el.getAsJsonObject();
            MutableComponent piece = Component.literal(part.get("text").getAsString());
            if (part.has("color")) {
                TextColor color = TextColor.parseColor(part.get("color").getAsString())
                        .result().orElse(null);
                if (color != null) {
                    piece.setStyle(Style.EMPTY.withColor(color));
                }
            }
            out.append(piece);
        }
        // Курсив у переименованного предмета ваниль включает сама, а на
        // сервере имена ставит Skript и выглядят они прямыми — гасим и здесь,
        // иначе один и тот же предмет в креативе и в руке выглядит по-разному.
        return out.setStyle(out.getStyle().withItalic(false));
    }
}
