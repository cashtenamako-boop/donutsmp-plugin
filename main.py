

===== src/main/java/com/donsup/DonsupPlugin.java =====

package com.donsup;
import com.donsup.compat.ItemKey;

import com.donsup.command.SmpCommand;
import com.donsup.creator.CreatorManager;
import com.donsup.duel.DuelManager;
import com.donsup.economy.EconomyManager;
import com.donsup.gui.MenuManager;
import com.donsup.listener.AfkRewardListener;
import com.donsup.listener.BrandingListener;
import com.donsup.listener.CombatRewardListener;
import com.donsup.market.MarketManager;
import com.donsup.market.PriceTracker;
import com.donsup.moderation.ModerationManager;
import com.donsup.progression.DailyManager;
import com.donsup.progression.KitsManager;
import com.donsup.social.SocialManager;
import com.donsup.spawner.CustomSpawnerManager;
import com.donsup.tools.ToolManager;
import com.donsup.trade.TradeManager;
import com.donsup.util.Text;
import com.donsup.preset.PresetManager;
import org.bukkit.Bukkit;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.plugin.java.JavaPlugin;

import java.io.File;
import java.io.IOException;
import java.util.List;

public class DonsupPlugin extends JavaPlugin {
    private com.donsup.config.Customization customization;
    public com.donsup.config.Customization customization() { return customization; }
    private com.donsup.platform.ServerPlatform platform;
    public com.donsup.platform.ServerPlatform platform() { return platform; }
    private com.donsup.dialog.PlayerMenus dialogs;
    private com.donsup.features.ServerFeatures extensions;
    private com.donsup.features.TravelManager travel;
    private com.donsup.tools.SellAxe sellAxe;
    public com.donsup.tools.SellAxe sellAxe() { return sellAxe; }
    public com.donsup.dialog.PlayerMenus dialogs() { return dialogs; }
    public com.donsup.features.ServerFeatures extensions() { return extensions; }
    public com.donsup.features.TravelManager travel() { return travel; }
    private EconomyManager economy;
    private com.donsup.crates.CrateManager crates;
    private com.donsup.shop.ChestShopManager chestShops;
    public com.donsup.shop.ChestShopManager chestShops() { return chestShops; }
    public com.donsup.crates.CrateManager crates() { return crates; }
    private com.donsup.market.ShoppingLists shopping;
    public com.donsup.market.ShoppingLists shopping() { return shopping; }
    private com.donsup.features.RtpZoneMenu zoneMenu;
    public com.donsup.features.RtpZoneMenu zoneMenu() {return zoneMenu;}
    private com.donsup.features.PearlPreferences pearls;
    public com.donsup.features.PearlPreferences pearls(){return pearls;}
    private com.donsup.market.MarketRecovery recovery;
    private boolean recoveryFailed;
    public com.donsup.market.MarketRecovery recovery(){return recovery;}
    public boolean recoveryFailed(){return recoveryFailed;}
    public void stopForRecovery(Exception cause){
        recoveryFailed=true;
        getLogger().severe("Transaction storage failed; plugin saves stopped. Restart after checking disk space/permissions. "+cause);
        for(var player:Bukkit.getOnlinePlayers())platform.player(player,()->player.kickPlayer("Economy storage is temporarily unavailable. Please reconnect after staff restart the server."));
        platform.global(()->Bukkit.getPluginManager().disablePlugin(this));
    }
    private com.donsup.market.SellChest sellChest;
    public com.donsup.market.SellChest sellChest() { return sellChest; }
    private MarketManager market;
    private MenuManager menus;
    private CustomSpawnerManager spawners;
    private DuelManager duels;
    private ToolManager tools;
    private SocialManager social;
    private TradeManager trades;
    private KitsManager kits;
    private DailyManager daily;
    private ModerationManager moderation;
    private PriceTracker prices;
    private CreatorManager creator;
    private FileConfiguration shops;
    private String prefix;
    private PresetManager presetManager;
    private String presetError = "";

    @Override
    public void onEnable() {
        platform = new com.donsup.platform.ServerPlatform(this);
        saveDefaultConfig();
        saveResourceIfMissing("shops.yml");
        saveResourceIfMissing("features-plan.md");
        for (String preset : PresetManager.BUNDLED) {
            for (String file : List.of("config.yml", "shops.yml", "preset.yml")) extractPresetIfMissing(preset, file);
        }
        try {
            presetManager = new PresetManager(getDataFolder().toPath(),
                    name -> Bukkit.getPluginManager().getPlugin(name) != null);
            presetManager.recoverPending();
            reloadConfig();
            String initial = getConfig().getString("setup.preset", "").trim();
            if (!initial.isEmpty() && !presetManager.hasAppliedPreset()) {
                presetManager.apply(initial);
                reloadConfig();
                getLogger().info("Installed first-start preset: " + initial);
            }
        } catch (IOException ex) {
            getLogger().severe("Preset setup/recovery failed: " + ex.getMessage());
            Bukkit.getPluginManager().disablePlugin(this);
            return;
        }
        reloadLocalConfigs();

        try { this.recovery=new com.donsup.market.MarketRecovery(this); }
        catch(IOException | RuntimeException ex){getLogger().severe("Cannot recover transactions: "+ex);recoveryFailed=true;Bukkit.getPluginManager().disablePlugin(this);return;}
        this.economy = new EconomyManager(this);
        this.market = new MarketManager(this);
        this.sellChest = new com.donsup.market.SellChest(this);
        this.shopping = new com.donsup.market.ShoppingLists(this);
        this.spawners = new CustomSpawnerManager(this);
        this.duels = new DuelManager(this);
        this.tools = new ToolManager(this);
        this.social = new SocialManager(this);
        this.trades = new TradeManager(this);
        this.kits = new KitsManager(this);
        this.daily = new DailyManager(this);
        this.moderation = new ModerationManager(this);
        this.prices = new PriceTracker(this);
        this.creator = new CreatorManager(this);
        this.menus = new MenuManager(this);
        this.crates = new com.donsup.crates.CrateManager(this);
        this.travel = new com.donsup.features.TravelManager(this);
        this.extensions = new com.donsup.features.ServerFeatures(this);
        this.zoneMenu=new com.donsup.features.RtpZoneMenu(this);
        this.pearls=new com.donsup.features.PearlPreferences(this);
        this.dialogs = platform.nativeDialogs() ? new com.donsup.dialog.NativeMenus(this) : new com.donsup.dialog.InventoryMenus(this);
        this.sellAxe = new com.donsup.tools.SellAxe(this);
        this.chestShops = new com.donsup.shop.ChestShopManager(this);

        SmpCommand command = new SmpCommand(this);
        com.donsup.command.CommandRegistration.register(this, command);
        platform.register(dialogs);
        platform.register(extensions);
        platform.register(travel);
        platform.register(sellAxe);
        platform.register(new com.donsup.gui.OwnedInventory.Guard());

        platform.register(recovery);
        platform.register(sellChest);
        platform.register(shopping);
        platform.register(zoneMenu);
        platform.register(pearls);
        platform.register(menus);
        platform.register(crates);
        platform.register(chestShops);
        platform.register(spawners);
        platform.register(duels);
        platform.register(tools);
        platform.register(social);
        platform.register(trades);
        platform.register(kits);
        platform.register(daily);
        platform.register(moderation);
        platform.register(prices);
        platform.register(creator);
        platform.register(new BrandingListener(this));
        platform.register(new AfkRewardListener(this));
        platform.register(new CombatRewardListener(this));
        getLogger().info("Donut SMP All In One enabled. Platform: " + platform.name() + "; menus: " + (platform.nativeDialogs() ? "native dialogs" : "inventory"));
    }

    @Override
    public void onDisable() {
        if (platform != null) platform.locked(this::shutdownManagers);
    }

    private void shutdownManagers() {
        if (sellChest != null) sellChest.shutdown();
        if(recoveryFailed)return; // Never overwrite replayable files with uncommitted manager state.
        for (var player : Bukkit.getOnlinePlayers()) {
            if (platform.folia()) continue;
            if (com.donsup.compat.Views.top(player.getOpenInventory()).getHolder() instanceof com.donsup.gui.OwnedInventory)
                player.closeInventory();
        }
        if (extensions != null) extensions.shutdown();
        if (dialogs != null) dialogs.shutdown();
        if (duels != null) duels.shutdown();
        if (travel != null) travel.shutdown();
        if (pearls != null) pearls.shutdown();
        if (chestShops != null) chestShops.shutdown();
        if (trades != null) trades.shutdown();
        if (economy != null) {
            economy.save();
        }
        if (market != null) {
            market.save();
        }
        if (spawners != null) {
            spawners.save();
        }
        if (creator != null) {
            creator.save();
            creator.shutdown();
        }
        if (duels != null) {
            duels.save();
        }
        if (social != null) social.save();
        if (kits != null) kits.save();
        if (daily != null) daily.save();
        if (moderation != null) moderation.save();
        if (prices != null) prices.save();
    }

    public void reloadAll() {
        // Validate all presentation files before replacing any live presentation state.
        var nextLanguage = com.donsup.config.Lang.load(getDataFolder().toPath());
        var next = com.donsup.config.Customization.load(getDataFolder().toPath());
        next.validateRuntimeItems();
        var candidate=com.donsup.config.Customization.read(getDataFolder().toPath().resolve("config.yml"), "config.yml");
        com.donsup.features.RtpZones.read(candidate.getConfigurationSection("travel.zones"));
        var nextShops = com.donsup.config.Customization.read(getDataFolder().toPath().resolve("shops.yml"), "shops.yml");
        if (dialogs != null) dialogs.reload();
        reloadConfig();
        customization = next;
        com.donsup.config.Lang.activate(nextLanguage);
        shops = nextShops;
        prefix = com.donsup.config.Branding.chatPrefix(getConfig());
        if (travel != null) travel.rtp().reloadZones();
        if (extensions != null) extensions.refreshAll();
    }

    private void reloadLocalConfigs() {
        var language = com.donsup.config.Lang.load(getDataFolder().toPath());
        this.customization = com.donsup.config.Customization.load(getDataFolder().toPath());
        this.customization.validateRuntimeItems();
        com.donsup.config.Lang.activate(language);
        this.prefix = com.donsup.config.Branding.chatPrefix(getConfig());
        this.shops = YamlConfiguration.loadConfiguration(new File(getDataFolder(), "shops.yml"));
    }

    private void saveResourceIfMissing(String resource) {
        File file = new File(getDataFolder(), resource);
        if (!file.exists()) {
            saveResource(resource, false);
        }
    }

    private void extractPresetIfMissing(String preset, String fileName) {
        File file = new File(getDataFolder(), "presets/" + preset + "/" + fileName);
        if (file.exists()) {
            return;
        }
        file.getParentFile().mkdirs();
        saveResource("presets/" + preset + "/" + fileName, false);
    }

    public PresetManager presetManager() { return presetManager; }
    public String presetError() { return presetError; }
    public List<String> presets() { return presetManager.list(); }

    public boolean applyPreset(String preset) {
        try {
            presetManager.apply(preset);
            reloadAll();
            presetError = "";
            return true;
        } catch (IOException ex) {
            presetError = ex.getMessage();
            getLogger().warning("Preset install failed: " + presetError);
            return false;
        }
    }

    public boolean rollbackPreset() {
        try {
            presetManager.rollback();
            reloadAll();
            presetError = "";
            return true;
        } catch (IOException ex) {
            presetError = ex.getMessage();
            getLogger().warning("Preset rollback failed: " + presetError);
            return false;
        }
    }

    public EconomyManager economy() {
        return economy;
    }

    public MarketManager market() {
        return market;
    }

    public MenuManager menus() {
        return menus;
    }

    public CustomSpawnerManager spawners() {
        return spawners;
    }

    public DuelManager duels() {
        return duels;
    }

    public ToolManager tools() {
        return tools;
    }

    public SocialManager social() { return social; }
    public TradeManager trades() { return trades; }
    public KitsManager kits() { return kits; }
    public DailyManager daily() { return daily; }
    public ModerationManager moderation() { return moderation; }
    public PriceTracker prices() { return prices; }

    public CreatorManager creator() {
        return creator;
    }

    public void saveShops() {
        try {
            shops.save(new File(getDataFolder(), "shops.yml"));
        } catch (IOException ex) {
            getLogger().warning("Could not save shops.yml: " + ex.getMessage());
        }
    }

    public FileConfiguration shops() {
        return shops;
    }

    public String prefix() {
        return prefix;
    }

    public String serverName() {
        return com.donsup.config.Branding.name(getConfig());
    }

    public String menuTitlePrefix() {
        return Text.color(com.donsup.config.Branding.menuPrefix(getConfig()));
    }

    public String displayName() {
        return com.donsup.config.Branding.display(getConfig());
    }

    public void renameServer(String name) {
        getConfig().set("branding.server-name", com.donsup.config.Branding.validateName(name));
        saveConfig();
        prefix = com.donsup.config.Branding.chatPrefix(getConfig());
    }

    public org.bukkit.inventory.Inventory inventory(int size, String canonicalTitle, boolean storage) {
        String displayed = Text.color(customization.inventoryTitle(canonicalTitle, getConfig()));
        return com.donsup.gui.OwnedInventory.create(size, canonicalTitle, displayed, storage);
    }

    public org.bukkit.inventory.ItemStack button(org.bukkit.Material material, String name, List<String> lore,
                                                 com.donsup.compat.ItemKey key, String action) {
        return com.donsup.util.ItemUtil.button(material, customization.menuText(name),
                lore.stream().map(customization::menuText).toList(), key, action);
    }

    public void msg(org.bukkit.command.CommandSender sender, String message) {
        String rendered = customization == null ? message : customization.message(message);
        if (rendered.isEmpty()) return;
        String output = com.donsup.config.Branding.expand(rendered, getConfig());
        if (sender instanceof org.bukkit.entity.Player player && platform != null) platform.playerNow(player, () -> Text.send(sender, prefix, output));
        else Text.send(sender, prefix, output);
    }
}


===== src/main/java/com/donsup/command/CommandRegistration.java =====

package com.donsup.command;

import com.donsup.config.Lang;
import com.donsup.DonsupPlugin;
import org.bukkit.configuration.file.YamlConfiguration;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
public final class CommandRegistration {
    public static void register(DonsupPlugin plugin,SmpCommand legacy) {
        if(plugin.platform().modernCommands()) { PaperCommandRegistration.register(plugin,legacy); return; }
        var yaml=YamlConfiguration.loadConfiguration(new InputStreamReader(Objects.requireNonNull(plugin.getResource("plugin.yml")),StandardCharsets.UTF_8));
        for(String name:Objects.requireNonNull(yaml.getConfigurationSection("commands")).getKeys(false)) {
            org.bukkit.command.PluginCommand command=null;
            try { command=plugin.getCommand(name); } catch(UnsupportedOperationException ignored) { }
            if(command==null) { registerDynamic(plugin,legacy,yaml,name); continue; }
            command.setDescription(Lang.label("commands",name,yaml.getString("commands."+name+".description","SMP command")));
            command.setExecutor((sender,cmd,label,args) -> plugin.platform().locked(() -> {
                if(!sender.hasPermission("donsup.use")) { plugin.msg(sender,Lang.text("command-registration.no-permission", "&cNo permission.")); return true; }
                if(name.equals("chestshop")) { plugin.chestShops().command(sender,args);return true; }
                if(name.equals("keys")||name.equals("keyall")) { plugin.crates().command(sender,name,args);return true; }
                return plugin.extensions().command(sender,name,args) || legacy.onCommand(sender,cmd,name,args);
            }));
            command.setTabCompleter((sender,cmd,label,args) -> plugin.platform().locked(() -> legacy.onTabComplete(sender,cmd,name,args)));
        }
    }
    private static void registerDynamic(DonsupPlugin plugin,SmpCommand legacy,YamlConfiguration yaml,String name) {
        var command=new LegacyPaperCommand(plugin,legacy,name,Lang.label("commands",name,yaml.getString("commands."+name+".description","SMP command")),yaml.getStringList("commands."+name+".aliases"));
        var map=(org.bukkit.command.CommandMap)com.donsup.compat.BukkitCompat.call(plugin.getServer(),"getCommandMap");
        map.register(plugin.getName().toLowerCase(java.util.Locale.ROOT),command);
    }
    private static final class LegacyPaperCommand extends org.bukkit.command.Command implements org.bukkit.command.PluginIdentifiableCommand {
        private final DonsupPlugin plugin;
        private final SmpCommand delegate;
        LegacyPaperCommand(DonsupPlugin plugin,SmpCommand delegate,String name,String description,java.util.List<String> aliases) {
            super(name,description,"/"+name,aliases); this.plugin=plugin; this.delegate=delegate; setPermission("donsup.use");
        }
        @Override public org.bukkit.plugin.Plugin getPlugin() { return plugin; }
        @Override public boolean execute(org.bukkit.command.CommandSender sender,String label,String[] args) {
            return plugin.platform().locked(() -> {
                if(!sender.hasPermission("donsup.use")) { plugin.msg(sender,Lang.text("command-registration.no-permission", "&cNo permission.")); return true; }
                String name=getName();
                if(name.equals("chestshop")) { plugin.chestShops().command(sender,args); return true; }
                if(name.equals("keys") || name.equals("keyall")) { plugin.crates().command(sender,name,args); return true; }
                return plugin.extensions().command(sender,name,args) || delegate.onCommand(sender,this,name,args);
            });
        }
        @Override public java.util.List<String> tabComplete(org.bukkit.command.CommandSender sender,String alias,String[] args) {
            return plugin.platform().locked(() -> delegate.onTabComplete(sender,this,getName(),args));
        }
    }
}


===== src/main/java/com/donsup/command/PaperCommandRegistration.java =====

package com.donsup.command;

import com.donsup.DonsupPlugin;
import io.papermc.paper.command.brigadier.BasicCommand;
import io.papermc.paper.command.brigadier.CommandSourceStack;
import io.papermc.paper.plugin.lifecycle.event.types.LifecycleEvents;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.file.YamlConfiguration;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class PaperCommandRegistration {
    public static void register(DonsupPlugin plugin, SmpCommand legacy) {
        var manifest = YamlConfiguration.loadConfiguration(new InputStreamReader(
            Objects.requireNonNull(plugin.getResource("plugin.yml")), StandardCharsets.UTF_8));
        var commands = Objects.requireNonNull(manifest.getConfigurationSection("commands"));
        plugin.getLifecycleManager().registerEventHandler(LifecycleEvents.COMMANDS, event -> {
            for (String name : commands.getKeys(false)) {
                Command delegate = new Command(name) {
                    @Override public boolean execute(CommandSender sender, String label, String[] args) {
                        return legacy.onCommand(sender, this, label, args);
                    }
                };
                event.registrar().register(name, com.donsup.config.Lang.label("commands",name,commands.getString(name + ".description", "Donsup command")),
                    commands.getStringList(name + ".aliases"), new BasicCommand() {
                        @Override public boolean canUse(CommandSender sender) { return sender.hasPermission("donsup.use"); }
                        @Override public void execute(CommandSourceStack stack, String[] args) {
                            plugin.platform().locked(() -> executeLocked(stack,args));
                        }
                        private void executeLocked(CommandSourceStack stack,String[] args) {
                            if (name.equals("chestshop")) { plugin.chestShops().command(stack.getSender(), args); return; }
                            if (name.equals("keys") || name.equals("keyall")) {
                                plugin.crates().command(stack.getSender(), name, args); return;
                            }
                            if (!plugin.extensions().command(stack.getSender(), name, args))
                                delegate.execute(stack.getSender(), name, args);
                        }
                        @Override public Collection<String> suggest(CommandSourceStack stack, String[] args) {
                            return plugin.platform().locked(() -> legacy.onTabComplete(stack.getSender(), delegate, name, args));
                        }
                    });
            }
        });
    }
}


===== src/main/java/com/donsup/command/SmpCommand.java =====

package com.donsup.command;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.gui.AfkSessions;
import com.donsup.market.MarketListing;
import com.donsup.util.Text;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.OfflinePlayer;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

public class SmpCommand implements CommandExecutor, TabCompleter {
    private final DonsupPlugin plugin;

    public SmpCommand(DonsupPlugin plugin) {
        this.plugin = plugin;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        String name = command.getName().toLowerCase();
        if(plugin.recoveryFailed()){plugin.msg(sender,Lang.text("smp-command.trading-is-stopped-pending-server-recovery", "&cTrading is stopped pending server recovery."));return true;}
        if(name.equals("smp")&&args.length>0&&args[0].equalsIgnoreCase("recovery")){plugin.recovery().command(sender,args);return true;}
        if (!(sender instanceof Player player) && !name.equals("smp")) {
            plugin.msg(sender, Lang.text("smp-command.only-players-can-use-that-command", "&cOnly players can use that command."));
            return true;
        }
        if (sender instanceof Player player) {
            plugin.economy().ensure(player);
        }
        switch (name) {
            case "shop" -> plugin.menus().openShop((Player) sender);
            case "sell" -> sell((Player) sender, args);
            case "ah" -> auction((Player) sender, args, "auction");
            case "market" -> auction((Player) sender, args, "market");
            case "orders" -> orders((Player) sender, args);
            case "shards" -> plugin.menus().openShardShop((Player) sender);
            case "crates" -> plugin.menus().openCrates((Player) sender);
            case "homes" -> plugin.menus().openHomes((Player) sender);
            case "sethome" -> setHome((Player) sender, args);
            case "home" -> home((Player) sender, args);
            case "delhome" -> delHome((Player) sender, args);
            case "bounty" -> bounty((Player) sender, args);
            case "bounties" -> plugin.menus().openBounties((Player) sender);
            case "pay" -> payDirect((Player) sender, args);
            case "balance", "bal" -> balance((Player) sender);
            case "afk" -> afk((Player) sender);
            case "settings" -> plugin.menus().openSettings((Player) sender);
            case "profile" -> plugin.menus().openProfile((Player) sender);
            case "premium" -> plugin.menus().openPremium((Player) sender);
            case "pvault" -> plugin.menus().openPremiumVault((Player) sender);
            case "nightvision" -> nightVision((Player) sender);
            case "spawners" -> spawners((Player) sender, args);
            case "creator" -> creator((Player) sender, args);
            case "leaderboard" -> plugin.menus().openLeaderboards((Player) sender);
            case "premiumkit" -> premiumKit((Player) sender);
            case "repair" -> repair((Player) sender);
            case "feed" -> feed((Player) sender);
            case "workbench" -> workbench((Player) sender);
            case "duel" -> duel((Player) sender, args);
            case "drills", "drill", "veinminer" -> drills((Player) sender, args);
            case "team", "clan" -> plugin.social().team((Player) sender, args);
            case "pwarp" -> plugin.social().pwarp((Player) sender, args);
            case "trade" -> plugin.trades().trade((Player) sender, args);
            case "kit", "kits" -> plugin.kits().command((Player) sender, args);
            case "kitadmin" -> plugin.kits().admin((Player) sender, args);
            case "daily" -> {
                if (args.length > 0 && args[0].equalsIgnoreCase("claim")) plugin.daily().claim((Player) sender);
                else plugin.daily().open((Player) sender);
            }
            case "mod" -> plugin.moderation().command((Player) sender, args);
            case "report" -> plugin.moderation().report((Player) sender, args);
            case "prices" -> plugin.prices().open((Player) sender);
            case "smp" -> smp(sender, args);
            default -> {
                if (sender instanceof Player player) {
                    plugin.menus().openMain(player);
                }
            }
        }
        return true;
    }

    private void smp(CommandSender sender, String[] args) {
        if (args.length == 0) {
            if (sender instanceof Player player) {
                plugin.menus().openMain(player);
            } else {
                plugin.msg(sender, Lang.text("smp-command.smp-reload", "&e/smp reload"));
            }
            return;
        }
        switch (args[0].toLowerCase()) {
            case "reload" -> {
                if (!sender.hasPermission("donsup.admin")) {
                    plugin.msg(sender, Lang.text("smp-command.no-permission", "&cNo permission."));
                    return;
                }
                try {
                    plugin.reloadAll();
                    plugin.msg(sender, Lang.text("smp-command.reloaded-smp-builder-configs", "&aReloaded SMP builder configs."));
                } catch (IllegalArgumentException ex) {
                    plugin.msg(sender, Lang.text("smp-command.reload-rejected-fix-the-configuration-and-try-again", "&cReload rejected; fix the configuration and try again: {0}", ex.getMessage()));
                }
            }
            case "brand" -> {
                if (!sender.hasPermission("donsup.admin")) { plugin.msg(sender,Lang.text("smp-command.no-permission", "&cNo permission.")); return; }
                if (args.length < 2) { plugin.msg(sender,Lang.text("smp-command.usage-smp-brand", "&eUsage: /smp brand <Your Server Name>")); return; }
                try {
                    plugin.renameServer(String.join(" ",java.util.Arrays.copyOfRange(args,1,args.length)));
                    plugin.msg(sender,Lang.text("smp-command.server-name-saved-menus-tab-and-sidebar-use-the-new-name-restart", "&aServer name saved. Menus, tab and sidebar use the new name. Restart for the pause-screen heading."));
                } catch (IllegalArgumentException ex) { plugin.msg(sender,Lang.text("smp-command.text", "&c{0}", ex.getMessage())); }
            }
            case "balance", "bal" -> {
                if (sender instanceof Player player) {
                    balance(player);
                }
            }
            case "pay" -> pay(sender, args);
            case "premium" -> premium(sender, args);
            case "givekey" -> giveKey(sender, args);
            case "setsellmulti" -> setSellMulti(sender, args);
            case "preset" -> preset(sender, args);
            case "setup" -> {
                if (sender instanceof Player player) plugin.creator().openPresetTools(player);
                else plugin.msg(sender, Lang.text("smp-command.use-smp-preset-list-or-smp-preset-apply", "&eUse /smp preset list or /smp preset apply <name>."));
            }
            case "creator" -> {
                if (sender instanceof Player player) {
                    creator(player, new String[0]);
                }
            }
            default -> {
                if (sender instanceof Player player) {
                    plugin.menus().openMain(player);
                }
            }
        }
    }

    private void pay(CommandSender sender, String[] args) {
        if (!(sender instanceof Player player)) {
            plugin.msg(sender, Lang.text("smp-command.only-players-can-pay-money", "&cOnly players can pay money."));
            return;
        }
        if (args.length < 3) {
            plugin.msg(player, Lang.text("smp-command.usage-smp-pay", "&eUsage: /smp pay <player> <amount>"));
            return;
        }
        Player target = Bukkit.getPlayerExact(args[1]);
        double amount = parseDouble(args[2], -1);
        if (target == null || target.equals(player) || !Double.isFinite(amount) || amount <= 0) {
            plugin.msg(player, Lang.text("smp-command.invalid-player-or-amount", "&cInvalid player or amount."));
            return;
        }
        if (!plugin.economy().setting(target.getUniqueId(), "payments")) {
            plugin.msg(player, Lang.text("smp-command.that-player-has-payments-disabled", "&cThat player has payments disabled."));
            return;
        }
        if (!plugin.economy().exchange(player.getUniqueId(), target.getUniqueId(), amount, 0, 0, 0)) {
            plugin.msg(player, Lang.text("smp-command.you-do-not-have-enough-money", "&cYou do not have enough money."));
            return;
        }

        plugin.msg(player, Lang.text("smp-command.paid", "&aPaid &e{0} &a{1}.", target.getName(), Text.money(amount)));
        plugin.msg(target, Lang.text("smp-command.received-from", "&aReceived {0} from &e{1}&a.", Text.money(amount), player.getName()));
    }

    private void payDirect(Player player, String[] args) {
        if (args.length < 2) {
            plugin.msg(player, Lang.text("smp-command.usage-pay", "&eUsage: /pay <player> <amount>"));
            return;
        }
        pay(player, new String[]{"pay", args[0], args[1]});
    }

    private void balance(Player player) {
        plugin.msg(player, Lang.text("smp-command.money-shards", "&7Money: &a{0} &8| &7Shards: &d{1}", Text.money(plugin.economy().money(player.getUniqueId())), plugin.economy().shards(player.getUniqueId())));
    }

    private void premium(CommandSender sender, String[] args) {
        if (!sender.hasPermission("donsup.admin")) {
            plugin.msg(sender, Lang.text("smp-command.no-permission", "&cNo permission."));
            return;
        }
        if (args.length < 3) {
            plugin.msg(sender, Lang.text("smp-command.usage-smp-premium", "&eUsage: /smp premium <player> <days>"));
            return;
        }
        OfflinePlayer target = Bukkit.getOfflinePlayer(args[1]);
        long days = Math.max(1, parseLong(args[2], 30));
        plugin.economy().setPremium(target.getUniqueId(), Duration.ofDays(days).toMillis());
        plugin.msg(sender, Lang.text("smp-command.added-premium-to-for-days", "&aAdded premium to &e{0}&a for &e{1} days&a.", args[1], days));
    }

    private void giveKey(CommandSender sender, String[] args) {
        if (!sender.hasPermission("donsup.admin")) {
            plugin.msg(sender, Lang.text("smp-command.no-permission", "&cNo permission."));
            return;
        }
        if (args.length < 4) {
            plugin.msg(sender, Lang.text("smp-command.usage-smp-givekey", "&eUsage: /smp givekey <player> <type> <amount>"));
            return;
        }
        plugin.crates().command(sender, "keys", new String[]{"give", args[1], args[2], args[3]});
    }

    private void setSellMulti(CommandSender sender, String[] args) {
        if (!sender.hasPermission("donsup.admin")) {
            plugin.msg(sender, Lang.text("smp-command.no-permission", "&cNo permission."));
            return;
        }
        if (args.length < 3) {
            plugin.msg(sender, Lang.text("smp-command.usage-smp-setsellmulti", "&eUsage: /smp setsellmulti <player> <multiplier>"));
            return;
        }
        OfflinePlayer target = Bukkit.getOfflinePlayer(args[1]);
        double value = parseDouble(args[2], 1.0);
        plugin.economy().setSellMultiplier(target.getUniqueId(), value);
        plugin.msg(sender, Lang.text("smp-command.set-sell-multiplier-for-to-x", "&aSet sell multiplier for &e{0}&a to &e{1}x&a.", args[1], value));
    }

    private void preset(CommandSender sender, String[] args) {
        if (!sender.hasPermission("donsup.admin")) {
            plugin.msg(sender, Lang.text("smp-command.no-permission", "&cNo permission."));
            return;
        }
        String action = args.length < 2 ? "list" : args[1].toLowerCase(java.util.Locale.ROOT);
        if (action.equals("list")) {
            plugin.msg(sender, Lang.text("smp-command.available-presets", "&eAvailable presets: &f{0}", String.join(", ", plugin.presets())));
            plugin.msg(sender, Lang.text("smp-command.smp-setup-opens-the-installer-smp-preset-preview", "&e/smp setup &7opens the installer. &e/smp preset preview <name>"));
        } else if (action.equals("rollback")) {
            plugin.msg(sender, plugin.rollbackPreset() ? Lang.text("smp-command.restored-the-previous-config-and-shops-player-data-was-preserved", "&aRestored the previous config and shops. Player data was preserved.")
                    : Lang.text("smp-command.rollback-failed", "&cRollback failed: {0}", plugin.presetError()));
        } else if ((action.equals("preview") || action.equals("apply")) && args.length == 3) {
            if (action.equals("apply")) {
                plugin.msg(sender, plugin.applyPreset(args[2]) ? Lang.text("smp-command.applied-use-smp-preset-rollback-to-undo", "&aApplied {0}. Use /smp preset rollback to undo.", args[2])
                        : Lang.text("smp-command.install-failed", "&cInstall failed: {0}", plugin.presetError()));
                return;
            }
            try {
                var preview = plugin.presetManager().preview(args[2]);
                plugin.msg(sender, Lang.text("smp-command.text-84dc37", "&e{0} &7- {1}", preview.profile().name(), preview.profile().description()));
                plugin.msg(sender, Lang.text("smp-command.settings-change-branding-is-preserved-by-default-player-data-is-u", "&e{0} settings change. &7Branding is preserved by default; player data is untouched.", preview.changes().size()));
                preview.changes().stream().limit(16).forEach(key -> plugin.msg(sender, "&7- " + key));
                if (!preview.ready()) plugin.msg(sender, Lang.text("smp-command.missing-plugins", "&cMissing plugins: {0}", String.join(", ", preview.missingPlugins())));
                else plugin.msg(sender, Lang.text("smp-command.apply-smp-preset-apply", "&eApply: /smp preset apply {0}", args[2]));
            } catch (java.io.IOException ex) {
                plugin.msg(sender, Lang.text("smp-command.invalid-preset", "&cInvalid preset: {0}", ex.getMessage()));
            }
        } else {
            plugin.msg(sender, Lang.text("smp-command.smp-preset-apply-rollback", "&e/smp preset <list|preview <name>|apply <name>|rollback>"));
        }
    }

    private void sell(Player player, String[] args) {
        if (args.length == 0 || args[0].equalsIgnoreCase("gui")) { plugin.sellChest().open(player); return; }
        if (args[0].equalsIgnoreCase("options")) { plugin.dialogs().sellOptions(player); return; }
        if (args[0].equalsIgnoreCase("claim")) { plugin.sellChest().claim(player); return; }
        if(plugin.recovery()==null){sellUncommitted(player,args);return;}
        plugin.recovery().run(player,()->sellUncommitted(player,args));
    }

    private void sellUncommitted(Player player, String[] args) {
        if (args[0].equalsIgnoreCase("hand")) {
            plugin.menus().sellHand(player);
            return;
        }
        if (args[0].equalsIgnoreCase("all")) {
            plugin.menus().sellAll(player);
            return;
        }
        if (args[0].equalsIgnoreCase("shulker")) {
            plugin.market().sellShulkerContents(player); return;
        }
        if (args[0].equalsIgnoreCase("exact")) {
            ItemStack held = com.donsup.compat.BukkitCompat.hand(player.getInventory());
            double earned = plugin.market().sellExact(player, held);
            com.donsup.compat.BukkitCompat.hand(player.getInventory(), held.getAmount() == 0 ? null : held);
            plugin.msg(player, earned > 0 ? Lang.text("smp-command.sold-matching-held-items-for", "&aSold matching held items for {0}", Text.money(earned)) : Lang.text("smp-command.no-matching-order-is-buying-this-exact-item", "&7No matching order is buying this exact item."));
            return;
        }
        plugin.msg(player, Lang.text("smp-command.usage-sell", "&eUsage: /sell [gui|hand|all|exact|shulker|options|claim]"));
    }

    private void auction(Player player, String[] args, String type) {
        if(plugin.recovery()==null){auctionUncommitted(player,args,type);return;}
        plugin.recovery().run(player,()->auctionUncommitted(player,args,type));
    }

    private void auctionUncommitted(Player player, String[] args, String type) {
        if (args.length == 0) {
            plugin.menus().openListings(player, type);
            return;
        }
        if (args[0].equalsIgnoreCase("list") || args[0].equalsIgnoreCase("sell")) {
            if (args.length < 2) {
                plugin.msg(player, Lang.text("smp-command.usage-list", "&eUsage: /{0} list <price>", (type.equals("auction") ? "ah" : "market")));
                return;
            }
            double price = parseDouble(args[1], -1);
            ItemStack held = com.donsup.compat.BukkitCompat.hand(player.getInventory());
            if (!Double.isFinite(price) || price <= 0 || com.donsup.compat.BukkitCompat.air(held.getType())) {
                plugin.msg(player, Lang.text("smp-command.hold-an-item-and-provide-a-valid-price", "&cHold an item and provide a valid price."));
                return;
            }
            ItemStack listing = held.clone();
            com.donsup.compat.BukkitCompat.hand(player.getInventory(), null);
            if (!plugin.market().listItem(player, listing, price, type)) {
                player.getInventory().addItem(listing);
                plugin.msg(player, Lang.text("smp-command.could-not-list-item-check-listing-limit-and-listing-tax-money", "&cCould not list item. Check listing limit and listing tax money."));
                return;
            }
            plugin.msg(player, Lang.text("smp-command.listed-held-item-for", "&aListed held item for {0}.", Text.money(price)));
            plugin.menus().openListings(player, type);
            return;
        }
        if (args[0].equalsIgnoreCase("cancel") && args.length >= 2) {
            plugin.market().reclaim(player, args[1]);
            return;
        }
        plugin.msg(player, Lang.text("smp-command.usage-list-cancel", "&eUsage: /{0} [list <price>|cancel <id>]", (type.equals("auction") ? "ah" : "market")));
    }

    private void orders(Player player, String[] args) {
        if (args.length == 0) {
            plugin.menus().openOrders(player);
            return;
        }
        if (args[0].equalsIgnoreCase("hand")) {
            if (args.length != 3) { plugin.msg(player, Lang.text("smp-command.usage-orders-hand-copies-the-held-item-s-exact-properties", "&eUsage: /orders hand <amount> <priceEach> (copies the held item's exact properties)")); return; }
            long amount = parseLong(args[1], -1);
            double price = parseDouble(args[2], -1);
            if (amount < 1 || amount > 1000000 || !plugin.market().createExactOrder(player, com.donsup.compat.BukkitCompat.hand(player.getInventory()), (int) amount, price)) {
                plugin.msg(player, Lang.text("smp-command.hold-an-item-and-check-quantity-price-balance-and-order-limit", "&cHold an item and check quantity, price, balance and order limit.")); return;
            }
            plugin.msg(player, Lang.text("smp-command.created-exact-item-order-your-sample-item-was-kept", "&aCreated exact-item order. Your sample item was kept."));
            plugin.menus().openOrders(player); return;
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("deliver")) { plugin.menus().deliverOrder(player, args[1]); return; }
        if (args.length == 2 && args[0].equalsIgnoreCase("claim")) { plugin.menus().claimOrder(player, args[1]); return; }
        if (args[0].equalsIgnoreCase("create")) {
            if (args.length < 4) {
                plugin.msg(player, Lang.text("smp-command.usage-orders-create", "&eUsage: /orders create <material> <amount> <priceEach>"));
                return;
            }
            Material material = material(args[1]);
            long parsedAmount = parseLong(args[2], -1);
            int amount = parsedAmount > 0 && parsedAmount <= 1000000 ? (int) parsedAmount : -1;
            double priceEach = parseDouble(args[3], -1);
            if (material == null || amount <= 0 || priceEach <= 0) {
                plugin.msg(player, Lang.text("smp-command.invalid-material-amount-or-price", "&cInvalid material, amount or price."));
                return;
            }
            if (!plugin.market().createOrder(player, material, amount, priceEach)) {
                plugin.msg(player, Lang.text("smp-command.could-not-create-order-you-need-enough-money-for-escrow", "&cCould not create order. You need enough money for escrow."));
                return;
            }
            plugin.msg(player, Lang.text("smp-command.created-order-for-x", "&aCreated order for &e{0}x {1}&a.", amount, Lang.material(material)));
            plugin.menus().openOrders(player);
            return;
        }
        plugin.msg(player, Lang.text("smp-command.usage-orders-create-hand-deliver-claim", "&eUsage: /orders [create <material> <amount> <priceEach>|hand <amount> <priceEach>|deliver <id>|claim <id>]"));
    }

    private void setHome(Player player, String[] args) {
        String name = args.length == 0 ? "home" : args[0];
        if (!plugin.economy().setHome(player, name)) {
            plugin.msg(player, Lang.text("smp-command.home-limit-reached-premium-adds-more-homes", "&cHome limit reached. Premium adds more homes."));
            return;
        }
        plugin.msg(player, Lang.text("smp-command.set-home", "&aSet home &e{0}&a.", name));
    }

    private void home(Player player, String[] args) {
        String name = args.length == 0 ? "home" : args[0];
        var location = plugin.economy().home(player.getUniqueId(), name);
        if (location == null) {
            plugin.msg(player, Lang.text("smp-command.home-not-found", "&cHome not found."));
            return;
        }
        plugin.travel().teleport(player, location);
    }

    private void delHome(Player player, String[] args) {
        if (args.length == 0) {
            plugin.msg(player, Lang.text("smp-command.usage-delhome", "&eUsage: /delhome <name>"));
            return;
        }
        if (!plugin.economy().deleteHome(player.getUniqueId(), args[0])) {
            plugin.msg(player, Lang.text("smp-command.home-not-found", "&cHome not found."));
            return;
        }
        plugin.msg(player, Lang.text("smp-command.deleted-home", "&aDeleted home &e{0}&a.", args[0]));
    }

    private void bounty(Player player, String[] args) {
        if (args.length == 0) {
            plugin.menus().openBounties(player);
            return;
        }
        if ((args[0].equalsIgnoreCase("set") || args[0].equalsIgnoreCase("add")) && args.length >= 3) {
            placeBounty(player, args[1], args[2]);
            return;
        }
        if (args.length >= 2) {
            placeBounty(player, args[0], args[1]);
            return;
        }
        plugin.msg(player, Lang.text("smp-command.usage-bounty-or-bounty-set", "&eUsage: /bounty <player> <amount> &7or &e/bounty set <player> <amount>"));
    }

    private void placeBounty(Player player, String targetName, String amountText) {
            OfflinePlayer target = Bukkit.getOfflinePlayer(targetName);
            double amount = parseDouble(amountText, -1);
            if (amount <= 0 || !plugin.economy().withdraw(player.getUniqueId(), amount)) {
                plugin.msg(player, Lang.text("smp-command.invalid-amount-or-not-enough-money", "&cInvalid amount or not enough money."));
                return;
            }
            plugin.economy().setBounty(target.getUniqueId(), player.getUniqueId(), amount);
            plugin.msg(player, Lang.text("smp-command.placed-bounty-on-for", "&aPlaced bounty on &e{0}&a for {1}.", targetName, Text.money(amount)));
    }

    private void afk(Player player) {
        if (AfkSessions.ACTIVE.remove(player.getUniqueId())) {
            plugin.msg(player, Lang.text("smp-command.afk-rewards-disabled", "&cAFK rewards disabled."));
        } else {
            AfkSessions.ACTIVE.add(player.getUniqueId());
            plugin.msg(player, Lang.text("smp-command.afk-rewards-enabled-move-to-disable", "&aAFK rewards enabled. Move to disable."));
        }
    }

    private void nightVision(Player player) {
        if (!plugin.getConfig().getBoolean("settings.premium-night-vision", true)) {
            plugin.msg(player, Lang.text("smp-command.night-vision-is-disabled-by-this-server", "&cNight vision is disabled by this server.")); return;
        }
        if (!plugin.economy().premium(player)) {
            plugin.msg(player, Lang.text("smp-command.night-vision-is-a-premium-perk", "&cNight vision is a premium perk."));
            return;
        }
        boolean enabled = plugin.economy().toggleSetting(player.getUniqueId(), "night_vision");
        plugin.menus().applyNightVision(player);
        plugin.msg(player, Lang.text("smp-command.night-vision-is-now", "&bNight vision is now {0}&b.", (enabled ? Lang.text("smp-command.on", "&aON") : Lang.text("smp-command.off", "&cOFF"))));
    }

    private boolean requirePremium(Player player) {
        if (!plugin.economy().premium(player)) {
            plugin.msg(player, Lang.text("smp-command.this-is-a-premium-perk", "&cThis is a premium perk."));
            return false;
        }
        return true;
    }

    private void premiumKit(Player player) {
        if (!requirePremium(player)) return;
        long cooldown = Math.max(1, plugin.getConfig().getLong("settings.premium-kit-cooldown-hours", 24)) * 60L * 60L * 1000L;
        if (!plugin.economy().cooldownReady(player.getUniqueId(), "premium-kit", cooldown)) {
            plugin.msg(player, Lang.text("smp-command.premium-kit-cooldown-minutes", "&cPremium kit cooldown: &e{0} minutes&c.", (plugin.economy().cooldownRemaining(player.getUniqueId(), "premium-kit", cooldown) / 60000L)));
            return;
        }
        ConfigurationSection section = plugin.getConfig().getConfigurationSection("premium-kit");
        if (section == null) {
            plugin.msg(player, Lang.text("smp-command.premium-kit-is-not-configured", "&cPremium kit is not configured."));
            return;
        }
        java.util.List<ItemStack> rewards = new java.util.ArrayList<>();
        for (String materialName : section.getKeys(false)) {
            Material material = material(materialName);
            if (material != null) {
                rewards.add(new ItemStack(material, Math.max(1, section.getInt(materialName, 1))));
            }
        }
        if (!com.donsup.util.InventoryCapacity.fitsBatch(player, rewards)) {
            plugin.msg(player, Lang.text("smp-command.make-room-for-the-whole-kit-first-your-cooldown-has-not-started", "&cMake room for the whole kit first. Your cooldown has not started.")); return;
        }
        rewards.forEach(item -> player.getInventory().addItem(item));
        plugin.economy().markCooldown(player.getUniqueId(), "premium-kit");
        plugin.msg(player, Lang.text("smp-command.claimed-premium-kit", "&aClaimed premium kit."));
    }

    private void repair(Player player) {
        if (!requirePremium(player)) return;
        long cooldown = Math.max(1, plugin.getConfig().getLong("settings.premium-repair-cooldown-minutes", 60)) * 60L * 1000L;
        if (!plugin.economy().cooldownReady(player.getUniqueId(), "repair", cooldown)) {
            plugin.msg(player, Lang.text("smp-command.repair-cooldown-minutes", "&cRepair cooldown: &e{0} minutes&c.", (plugin.economy().cooldownRemaining(player.getUniqueId(), "repair", cooldown) / 60000L)));
            return;
        }
        ItemStack held = com.donsup.compat.BukkitCompat.hand(player.getInventory());
        if (com.donsup.compat.BukkitCompat.air(held.getType()) || held.getType().getMaxDurability() <= 0) {
            plugin.msg(player, Lang.text("smp-command.hold-a-damageable-item", "&cHold a damageable item."));
            return;
        }
        held.setDurability((short)0);
        plugin.economy().markCooldown(player.getUniqueId(), "repair");
        plugin.msg(player, Lang.text("smp-command.repaired-held-item", "&aRepaired held item."));
    }

    private void feed(Player player) {
        if (!requirePremium(player)) return;
        long cooldown = Math.max(1, plugin.getConfig().getLong("settings.premium-feed-cooldown-minutes", 30)) * 60L * 1000L;
        if (!plugin.economy().cooldownReady(player.getUniqueId(), "feed", cooldown)) {
            plugin.msg(player, Lang.text("smp-command.feed-cooldown-minutes", "&cFeed cooldown: &e{0} minutes&c.", (plugin.economy().cooldownRemaining(player.getUniqueId(), "feed", cooldown) / 60000L)));
            return;
        }
        player.setFoodLevel(20);
        player.setSaturation(10F);
        plugin.economy().markCooldown(player.getUniqueId(), "feed");
        plugin.msg(player, Lang.text("smp-command.fed", "&aFed."));
    }

    private void workbench(Player player) {
        if (!requirePremium(player)) return;
        if (!plugin.getConfig().getBoolean("settings.premium-portable-workbench", true)) {
            plugin.msg(player, Lang.text("smp-command.portable-workbench-is-disabled", "&cPortable workbench is disabled."));
            return;
        }
        player.openWorkbench(null, true);
    }

    private void spawners(Player player, String[] args) {
        if (args.length == 0) {
            plugin.spawners().openShop(player);
            return;
        }
        if (args[0].equalsIgnoreCase("give") && player.hasPermission("donsup.admin")) {
            if (args.length < 3) {
                plugin.msg(player, Lang.text("smp-command.usage-spawners-give", "&eUsage: /spawners give <type> <amount>"));
                return;
            }
            int amount = (int) Math.max(1, parseLong(args[2], 1));
            player.getInventory().addItem(plugin.spawners().spawnerItem(args[1], amount));
            plugin.msg(player, Lang.text("smp-command.gave-custom-spawners", "&aGave custom spawners."));
            return;
        }
        plugin.msg(player, Lang.text("smp-command.usage-spawners-give-8601de", "&eUsage: /spawners [give <type> <amount>]"));
    }

    private void duel(Player player, String[] args) {
        if (args.length == 0) {
            plugin.duels().open(player);
            return;
        }
        switch (args[0].toLowerCase()) {
            case "accept" -> {
                if (args.length < 2) {
                    plugin.msg(player, Lang.text("smp-command.usage-duel-accept", "&eUsage: /duel accept <player>"));
                    return;
                }
                plugin.duels().accept(player, args[1]);
            }
            case "deny", "decline" -> plugin.duels().deny(player, args.length >= 2 ? args[1] : "");
            case "leave", "forfeit" -> plugin.duels().leave(player);
            case "arena" -> {
                if (!player.hasPermission("donsup.admin")) {
                    plugin.msg(player, Lang.text("smp-command.no-permission", "&cNo permission."));
                    return;
                }
                if (args.length >= 4 && args[1].equalsIgnoreCase("set")) {
                    plugin.duels().setArenaSpawn(player, args[2], parseInt(args[3], 0));
                    return;
                }
                if (args.length >= 3 && args[1].equalsIgnoreCase("delete")) {
                    plugin.duels().deleteArena(player, args[2]);
                    return;
                }
                plugin.msg(player, Lang.text("smp-command.usage-duel-arena-set-or-duel-arena-delete", "&eUsage: /duel arena set <id> <1|2> &7or &e/duel arena delete <id>"));
            }
            default -> {
                Player target = Bukkit.getPlayerExact(args[0]);
                double wager = args.length >= 2 ? parseDouble(args[1], 0) : 0;
                if (target == null) {
                    plugin.msg(player, Lang.text("smp-command.player-not-found", "&cPlayer not found."));
                    return;
                }
                plugin.duels().invite(player, target, Math.max(0, wager));
            }
        }
    }

    private void drills(Player player, String[] args) {
        if (args.length == 0) {
            plugin.tools().open(player);
            return;
        }
        if (args[0].equalsIgnoreCase("give")) {
            if (!player.hasPermission("donsup.admin")) {
                plugin.msg(player, Lang.text("smp-command.no-permission", "&cNo permission."));
                return;
            }
            if (args.length < 3) {
                plugin.msg(player, Lang.text("smp-command.usage-drill-give", "&eUsage: /drill give <player> <tier>"));
                return;
            }
            Player target = Bukkit.getPlayerExact(args[1]);
            if (target == null) {
                plugin.msg(player, Lang.text("smp-command.player-not-found", "&cPlayer not found."));
                return;
            }
            plugin.tools().give(target, args[2]);
            plugin.msg(player, Lang.text("smp-command.gave-drill-to", "&aGave drill to &e{0}&a.", target.getName()));
            return;
        }
        plugin.msg(player, Lang.text("smp-command.usage-drills-or-drill-give", "&eUsage: /drills &7or &e/drill give <player> <tier>"));
    }

    private void creator(Player player, String[] args) {
        if (!player.hasPermission("donsup.admin")) {
            plugin.msg(player, Lang.text("smp-command.no-permission", "&cNo permission."));
            return;
        }
        if (args.length == 0) {
            plugin.creator().openHub(player);
            return;
        }
        switch (args[0].toLowerCase()) {
            case "crate" -> {
                if (args.length >= 3 && args[1].equalsIgnoreCase("wand")) {
                    player.getInventory().addItem(plugin.creator().cratePlacer(args[2]));
                    plugin.msg(player, Lang.text("smp-command.gave-crate-placer-for", "&aGave crate placer for &e{0}&a.", args[2]));
                    return;
                }
                plugin.msg(player, Lang.text("smp-command.usage-creator-crate-wand", "&eUsage: /creator crate wand <type>"));
            }
            case "key" -> {
                if (args.length < 3) {
                    plugin.msg(player, Lang.text("smp-command.usage-creator-key", "&eUsage: /creator key <crateType> <amount>"));
                    return;
                }
                plugin.crates().command(player, "keys", new String[]{"give", player.getName(), args[1], args[2]});
            }
            case "shop" -> {
                if (args.length >= 7 && args[1].equalsIgnoreCase("add")) {
                    String category = args[2];
                    String id = args[3];
                    double buy = parseDouble(args[4], -1);
                    double sell = parseDouble(args[5], -1);
                    int amount = (int) Math.max(1, parseLong(args[6], com.donsup.compat.BukkitCompat.hand(player.getInventory()).getAmount()));
                    if (buy < 0 || sell < 0) {
                        plugin.msg(player, Lang.text("smp-command.buy-and-sell-prices-must-be-0-or-higher", "&cBuy and sell prices must be 0 or higher."));
                        return;
                    }
                    plugin.creator().addShopItem(player, category, id, buy, sell, amount);
                    return;
                }
                plugin.msg(player, Lang.text("smp-command.usage-creator-shop-add", "&eUsage: /creator shop add <category> <id> <buy> <sell> <amount>"));
            }
            case "dynamic" -> {
                if (args.length < 2) {
                    plugin.msg(player, Lang.text("smp-command.dynamic-pricing-is", "&eDynamic pricing is {0}&e.", (plugin.creator().dynamicEnabled() ? Lang.text("smp-command.enabled", "&aenabled") : Lang.text("smp-command.disabled", "&cdisabled"))));
                    plugin.msg(player, Lang.text("smp-command.usage-creator-dynamic", "&eUsage: /creator dynamic <on|off>"));
                    return;
                }
                boolean enabled = args[1].equalsIgnoreCase("on") || args[1].equalsIgnoreCase("true") || args[1].equalsIgnoreCase("enable");
                plugin.creator().setDynamicEnabled(enabled);
                plugin.msg(player, Lang.text("smp-command.dynamic-pricing-is-now", "&eDynamic pricing is now {0}&e.", (enabled ? Lang.text("smp-command.enabled", "&aenabled") : Lang.text("smp-command.disabled", "&cdisabled"))));
            }
            default -> plugin.creator().openHub(player);
        }
    }

    private Material material(String input) {
        try {
            return Material.valueOf(input.toUpperCase());
        } catch (IllegalArgumentException ex) {
            return null;
        }
    }

    private double parseDouble(String input, double fallback) {
        try {
            return Double.parseDouble(input);
        } catch (NumberFormatException ex) {
            return fallback;
        }
    }

    private long parseLong(String input, long fallback) {
        try {
            return Long.parseLong(input);
        } catch (NumberFormatException ex) {
            return fallback;
        }
    }

    private int parseInt(String input, int fallback) {
        try {
            return Integer.parseInt(input);
        } catch (NumberFormatException ex) {
            return fallback;
        }
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        List<String> out = new ArrayList<>();
        String name = command.getName().toLowerCase();
        if (args.length == 1) {
            if (name.equals("smp")) {
                out.addAll(List.of("balance", "pay", "reload", "premium", "givekey", "setsellmulti", "preset", "setup", "creator"));
                if (sender.hasPermission("donsup.admin")) out.add("brand");
            } else if (name.equals("sell")) {
                out.addAll(List.of("gui", "hand", "all", "exact", "shulker", "options", "claim"));
            } else if (name.equals("ah") || name.equals("market")) {
                out.addAll(List.of("list", "cancel"));
            } else if (name.equals("orders")) {
                out.addAll(List.of("create", "hand", "deliver", "claim"));
            } else if (name.equals("bounty")) {
                out.add("set");
                Bukkit.getOnlinePlayers().forEach(player -> out.add(player.getName()));
            } else if (name.equals("pay")) {
                Bukkit.getOnlinePlayers().forEach(player -> out.add(player.getName()));
            } else if (name.equals("spawners")) {
                out.add("give");
            } else if (name.equals("duel")) {
                out.addAll(List.of("accept", "deny", "leave"));
                if (sender.hasPermission("donsup.admin")) out.add("arena");
                Bukkit.getOnlinePlayers().forEach(player -> out.add(player.getName()));
            } else if (name.equals("drill") || name.equals("drills") || name.equals("veinminer")) {
                out.addAll(List.of("basic", "advanced", "mythic"));
                if (sender.hasPermission("donsup.admin")) out.add("give");
            } else if (name.equals("team") || name.equals("clan")) {
                out.addAll(List.of("create", "invite", "join", "leave", "chat", "sethome", "home", "vault", "bank", "friendlyfire"));
            } else if (name.equals("pwarp")) {
                out.addAll(List.of("set", "delete", "promote"));
            } else if (name.equals("trade")) {
                out.addAll(List.of("accept", "deny", "money", "shards"));
                Bukkit.getOnlinePlayers().forEach(player -> out.add(player.getName()));
            } else if (name.equals("kitadmin")) {
                out.addAll(List.of("save", "delete"));
            } else if (name.equals("daily")) {
                out.add("claim");
            } else if (name.equals("mod")) {
                out.addAll(List.of("mute", "warn", "freeze", "vanish", "note", "chat"));
            } else if (name.equals("creator")) {
                out.addAll(List.of("crate", "key", "shop", "dynamic"));
            }
        }
        if (name.equals("smp") && sender.hasPermission("donsup.admin") && args.length >= 2 && args[0].equalsIgnoreCase("preset")) {
            if (args.length == 2) out.addAll(List.of("list", "preview", "apply", "rollback"));
            if (args.length == 3 && (args[1].equalsIgnoreCase("apply") || args[1].equalsIgnoreCase("preview"))) out.addAll(plugin.presets());
        }
        return out.stream().filter(s -> args.length == 0 || s.toLowerCase().startsWith(args[args.length - 1].toLowerCase())).toList();
    }
}


===== src/main/java/com/donsup/compat/BlockTags.java =====

package com.donsup.compat;

import com.donsup.util.SafeYaml;
import java.io.*;
import org.bukkit.block.Block;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.plugin.Plugin;

/** Modern tile PDC, or an owner registry for legacy chest shops. Writes fail closed. */
public final class BlockTags {
    private final File file;
    private final YamlConfiguration legacy;
    private static final boolean MODERN=ItemTags.available("org.bukkit.block.TileState");
    public BlockTags(Plugin plugin) {
        file=new File(plugin.getDataFolder(),"legacy-container-owners.yml"); legacy=SafeYaml.load(file);
    }
    private String path(Block block) { return block.getWorld().getUID()+"."+block.getX()+"_"+block.getY()+"_"+block.getZ(); }
    public String get(ContainerHandle container,ItemKey key) {
        if(!MODERN) return legacy.getString(path(container.state().getBlock())+"."+key.key());
        String value=ModernBlockTags.get(container.state(),key);
        if(value!=null) return value;
        String path=path(container.state().getBlock());
        var old=legacy.getConfigurationSection(path);
        if(old==null) return null;
        for(String name:old.getKeys(false)) if(old.isString(name)) ModernBlockTags.set(container.state(),new ItemKey(key.namespace(),name),old.getString(name));
        if(!container.update(false,false)) throw new IllegalStateException("Legacy shop container changed during migration");
        value=ModernBlockTags.get(container.state(),key);
        forget(container.state().getBlock());
        return value;
    }
    public void set(ContainerHandle container,ItemKey key,String value) {
        if(MODERN) { ModernBlockTags.set(container.state(),key,value); return; }
        String path=path(container.state().getBlock())+"."+key.key(); Object previous=legacy.get(path);
        legacy.set(path,value);
        try { SafeYaml.save(legacy,file); }
        catch(IOException ex) { legacy.set(path,previous); throw new IllegalStateException("Could not save legacy chest ownership",ex); }
    }
    public void forget(Block block) {
        if(!legacy.contains(path(block))) return;
        String path=path(block); Object previous=legacy.get(path); legacy.set(path,null);
        try { SafeYaml.save(legacy,file); }
        catch(IOException ex) { legacy.set(path,previous); throw new IllegalStateException("Could not remove legacy chest ownership",ex); }
    }
}


===== src/main/java/com/donsup/compat/BukkitCompat.java =====

package com.donsup.compat;

import java.lang.reflect.*;
import java.util.*;
import org.bukkit.*;
import org.bukkit.block.Block;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.*;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.inventory.*;
import org.bukkit.plugin.Plugin;

/** Small version boundaries. Missing optional APIs have explicit, conservative fallbacks. */
public final class BukkitCompat {
    private BukkitCompat() {}
    public static boolean displays() { return ItemTags.available("org.bukkit.entity.BlockDisplay"); }
    public static org.bukkit.block.BlockFace facing(Block block) {
        if(method(Block.class,"getBlockData")) {
            Object data=call(block,"getBlockData");
            return method(data.getClass(),"getFacing") ? (org.bukkit.block.BlockFace)call(data,"getFacing") : org.bukkit.block.BlockFace.SELF;
        }
        var data=block.getState().getData();
        return data instanceof org.bukkit.material.Directional directional ? directional.getFacing() : org.bukkit.block.BlockFace.SELF;
    }
    public static org.bukkit.enchantments.Enchantment efficiency() {
        var enchant=org.bukkit.enchantments.Enchantment.getByName("EFFICIENCY");
        return enchant==null ? Objects.requireNonNull(org.bukkit.enchantments.Enchantment.getByName("DIG_SPEED")) : enchant;
    }
    public static void pling(Player player) {
        for(String name:new String[]{"BLOCK_NOTE_BLOCK_PLING","BLOCK_NOTE_PLING","NOTE_PLING"}) {
            try {
                Sound sound=(Sound)Sound.class.getMethod("valueOf",String.class).invoke(null,name);
                player.playSound(player.getLocation(),sound,1F,1.2F); return;
            } catch(InvocationTargetException ex) {
                if(!(ex.getCause() instanceof IllegalArgumentException)) throw new IllegalStateException(ex.getCause());
            } catch(ReflectiveOperationException ex) { throw new IllegalStateException("Sound lookup unavailable",ex); }
        }
    }
    public static void virtualSpawner(org.bukkit.block.CreatureSpawner state) {
        if(method(org.bukkit.block.CreatureSpawner.class,"setSpawnCount",int.class)) {
            for(String name:new String[]{"setMaxSpawnDelay","setMinSpawnDelay","setSpawnCount","setRequiredPlayerRange"})
                call(state,name,new Class<?>[]{int.class},name.endsWith("Delay") ? (int)Short.MAX_VALUE : 0);
        } else {
            Object spawner=call(call(state,"getTileEntity"),"getSpawner");
            for(String name:new String[]{"maxSpawnDelay","minSpawnDelay","spawnCount","requiredPlayerRange"})
                field(spawner,name,name.endsWith("Delay") ? (int)Short.MAX_VALUE : 0);
        }
        state.setDelay(Short.MAX_VALUE);
    }
    private static void field(Object object,String name,int value) {
        for(Class<?> type=object.getClass();type!=null;type=type.getSuperclass()) {
            try { Field field=type.getDeclaredField(name); field.setAccessible(true); field.setInt(object,value); return; }
            catch(NoSuchFieldException ignored) {} catch(IllegalAccessException ex) { throw new IllegalStateException(ex); }
        }
        throw new IllegalStateException("Server field unavailable: "+name);
    }
    public static boolean breakBlock(Player player,Block block) {
        if(method(Player.class,"breakBlock",Block.class)) return (boolean)call(player,"breakBlock",new Class<?>[]{Block.class},block);
        try {
            Object handle=call(player,"getHandle");
            Object manager=handle.getClass().getField("playerInteractManager").get(handle);
            Class<?> position=Class.forName(handle.getClass().getPackage().getName()+".BlockPosition");
            Object at=position.getConstructor(int.class,int.class,int.class).newInstance(block.getX(),block.getY(),block.getZ());
            return (boolean)call(manager,"breakBlock",new Class<?>[]{position},at);
        } catch(ReflectiveOperationException ex) { throw new IllegalStateException("Server block breaking API unavailable",ex); }
    }
    public static boolean method(Class<?> type, String name, Class<?>... parameters) {
        try { type.getMethod(name, parameters); return true; } catch (NoSuchMethodException ex) { return false; }
    }
    public static Object call(Object target, String name) { return call(target, name, new Class<?>[0]); }
    public static Object call(Object target, String name, Class<?>[] parameters, Object... arguments) {
        try {
            Method method=target.getClass().getMethod(name, parameters); method.setAccessible(true);
            return method.invoke(target, arguments);
        } catch (InvocationTargetException ex) {
            if(ex.getCause() instanceof RuntimeException cause) throw cause;
            throw new IllegalStateException("Server API failed: "+name, ex.getCause());
        } catch (ReflectiveOperationException ex) { throw new IllegalStateException("Server API unavailable: "+name, ex); }
    }
    public static boolean air(Material material) { return material==Material.AIR || "CAVE_AIR".equals(material.name()) || "VOID_AIR".equals(material.name()); }
    public static boolean legacy(Material material) { return material.name().startsWith("LEGACY_"); }
    public static boolean item(Material material) {
        if(method(Material.class,"isItem")) return (boolean)call(material,"isItem");
        return !air(material) && !Arrays.asList("WATER","STATIONARY_WATER","LAVA","STATIONARY_LAVA","FIRE","PORTAL","ENDER_PORTAL","PISTON_EXTENSION","PISTON_MOVING_PIECE","CROPS","CARROT","POTATO").contains(material.name());
    }
    public static ItemStack hand(PlayerInventory inventory) { return inventory.getItemInHand(); }
    public static void hand(PlayerInventory inventory, ItemStack item) { inventory.setItemInHand(item); }
    public static boolean offHand(PlayerInteractEvent event) {
        return method(PlayerInteractEvent.class,"getHand") && "OFF_HAND".equals(String.valueOf(call(event,"getHand")));
    }
    public static ItemStack[] storage(Inventory inventory) {
        if(method(Inventory.class,"getStorageContents")) return (ItemStack[])call(inventory,"getStorageContents");
        return inventory instanceof PlayerInventory ? Arrays.copyOf(inventory.getContents(),36) : inventory.getContents();
    }
    public static void storage(Inventory inventory,ItemStack[] items) {
        if(method(Inventory.class,"setStorageContents",ItemStack[].class)) call(inventory,"setStorageContents",new Class<?>[]{ItemStack[].class},(Object)items);
        else inventory.setContents(items);
    }
    public static int minHeight(World world) { return method(World.class,"getMinHeight") ? (int)call(world,"getMinHeight") : 0; }
    public static int logicalHeight(World world) { return method(World.class,"getLogicalHeight") ? (int)call(world,"getLogicalHeight") : world.getEnvironment()==World.Environment.NETHER ? 128 : world.getMaxHeight(); }
    @SuppressWarnings({"rawtypes","unchecked"}) public static int highest(World world,int x,int z) {
        if(ItemTags.available("org.bukkit.HeightMap")) {
            try {
                Class type=Class.forName("org.bukkit.HeightMap");
                if(method(World.class,"getHighestBlockYAt",int.class,int.class,type))
                    return (int)call(world,"getHighestBlockYAt",new Class<?>[]{int.class,int.class,type},x,z,Enum.valueOf(type,"MOTION_BLOCKING_NO_LEAVES"));
            } catch(ClassNotFoundException ex) { throw new IllegalStateException(ex); }
        }
        // Legacy height maps report the first air block above the ground.
        int y=Math.min(world.getMaxHeight()-1,world.getHighestBlockYAt(x,z));
        while(y>minHeight(world) && (air(world.getBlockAt(x,y,z).getType()) || world.getBlockAt(x,y,z).getType().name().contains("LEAVES"))) y--;
        return y;
    }
    public static boolean inside(WorldBorder border, Location at) {
        Location center=border.getCenter(); double half=border.getSize()/2;
        return at.getWorld()!=null && at.getWorld().equals(center.getWorld()) && at.getX()>=center.getX()-half && at.getX()<center.getX()+half && at.getZ()>=center.getZ()-half && at.getZ()<center.getZ()+half;
    }
    public static boolean fullHeight(Block block) {
        if(method(Block.class,"getBoundingBox")) return ((Number)call(call(block,"getBoundingBox"),"getHeight")).doubleValue()>=.999;
        String name=block.getType().name();
        return block.getType().isSolid() && !name.contains("STEP") && !name.contains("STAIRS") && !name.contains("FENCE") && !name.contains("WALL") && !name.contains("DOOR") && !name.contains("CHEST") && !name.contains("BED") && !name.contains("CAKE") && !name.contains("DAYLIGHT") && !name.contains("CAULDRON") && !name.contains("HOPPER") && !name.contains("ENCHANTMENT") && !name.contains("SOIL") && !name.equals("SNOW") && !name.contains("CARPET") && !name.contains("TRAP") && !name.contains("PISTON") && !name.contains("CACTUS");
    }
    public static Entity attacker(EntityDamageEvent event) {
        if(method(EntityDamageEvent.class,"getDamageSource")) return (Entity)call(call(event,"getDamageSource"),"getCausingEntity");
        if(!(event instanceof EntityDamageByEntityEvent byEntity)) return null;
        Entity damager=byEntity.getDamager();
        if(damager instanceof Projectile projectile && projectile.getShooter() instanceof Entity shooter) return shooter;
        return damager;
    }
    public static Location location(ConfigurationSection section,String path,Location fallback) {
        Object value=section.get(path); return value instanceof Location location ? location : fallback;
    }
    public static Block target(Player player,int range) {
        if(method(Player.class,"getTargetBlockExact",int.class)) return (Block)call(player,"getTargetBlockExact",new Class<?>[]{int.class},range);
        Block block=player.getTargetBlock((Set<Material>)null,range); return block==null || air(block.getType()) ? null : block;
    }
    public static void drops(BlockBreakEvent event,boolean drops) {
        if(method(BlockBreakEvent.class,"setDropItems",boolean.class)) call(event,"setDropItems",new Class<?>[]{boolean.class},drops);
        else if(!drops) { event.setCancelled(true); event.getBlock().setType(Material.AIR); }
    }
    public static void ticket(World world,int x,int z,Plugin plugin,boolean add) {
        String name=add ? "addPluginChunkTicket" : "removePluginChunkTicket";
        if(method(World.class,name,int.class,int.class,Plugin.class)) call(world,name,new Class<?>[]{int.class,int.class,Plugin.class},x,z,plugin);
        else if(add) world.getChunkAt(x,z).load();
    }
    public static void tab(Player player,String header,String footer) {
        if(method(Player.class,"setPlayerListHeaderFooter",String.class,String.class)) call(player,"setPlayerListHeaderFooter",new Class<?>[]{String.class,String.class},header,footer);
        else LegacyTab.send(player,header,footer);
    }
    public static String inventoryTitle(String title) {
        return ItemTags.available("org.bukkit.block.TileState") ? title : limit(title,32);
    }
    public static String scoreTitle(String title) { return Material.getMaterial("OAK_LOG")==null ? limit(title,32) : title; }
    public static String scoreLine(String line) { return Material.getMaterial("OAK_LOG")==null ? limit(line,38) : line; }
    private static String limit(String text,int length) {
        if(text.length()<=length) return text;
        int end=Character.isHighSurrogate(text.charAt(length-1)) ? length-1 : length;
        return text.substring(0,end).replaceAll("\u00a7$", "");
    }
    public static void visible(Plugin plugin,Player viewer,Player subject,boolean visible) {
        String name=visible ? "showPlayer" : "hidePlayer";
        if(method(Player.class,name,Plugin.class,Player.class)) call(viewer,name,new Class<?>[]{Plugin.class,Player.class},plugin,subject);
        else if(visible) viewer.showPlayer(subject); else viewer.hidePlayer(subject);
    }
}


===== src/main/java/com/donsup/compat/ContainerHandle.java =====

package com.donsup.compat;

import org.bukkit.block.*;
import org.bukkit.inventory.*;

/** Container was added after 1.8. BlockState + InventoryHolder is available on both APIs. */
public final class ContainerHandle {
    private final BlockState state;
    private final Inventory inventory;
    private ContainerHandle(BlockState state,Inventory inventory) { this.state=state; this.inventory=inventory; }
    public static ContainerHandle of(Block block) {
        if(block==null) return null;
        BlockState state=block.getState();
        return state instanceof InventoryHolder holder ? new ContainerHandle(state,holder.getInventory()) : null;
    }
    public BlockState state() { return state; }
    public org.bukkit.World getWorld() { return state.getWorld(); }
    public org.bukkit.Location getLocation() { return state.getLocation(); }
    public Inventory getInventory() { return inventory; }
    public boolean isLocked() { return BukkitCompat.method(state.getClass(),"isLocked") && (boolean)BukkitCompat.call(state,"isLocked"); }
    public boolean update(boolean force,boolean physics) { return state.update(force,physics); }
    public java.util.List<Block> parts() {
        if(inventory.getHolder() instanceof DoubleChest chest && chest.getLeftSide() instanceof BlockState left && chest.getRightSide() instanceof BlockState right) return java.util.List.of(left.getBlock(),right.getBlock());
        return java.util.List.of(state.getBlock());
    }
    public boolean singleShopContainer() {
        String name=state.getType().name();
        if(name.equals("BARREL")) return true;
        return (name.equals("CHEST") || name.equals("TRAPPED_CHEST")) && (inventory.getSize()==27 || inventory.getSize()==54);
    }
}


===== src/main/java/com/donsup/compat/DialogCapabilities.java =====

package com.donsup.compat;

/** Dialog rendering is enabled for the API generation this implementation targets. */
public final class DialogCapabilities {
    private DialogCapabilities() {}
    public static boolean available() {
        if(!ItemTags.available("io.papermc.paper.dialog.Dialog")) return false;
        try {
            Class<?> info=Class.forName("io.papermc.paper.ServerBuildInfo");
            Object build=info.getMethod("buildInfo").invoke(null);
            return supportedVersion((String)info.getMethod("minecraftVersionId").invoke(build));
        } catch(ReflectiveOperationException | LinkageError ex) { return false; }
    }
    public static boolean supportedVersion(String version) {
        String[] parts=version.split("\\.");
        try {
            int major=Integer.parseInt(parts[0]);
            if(major>=26) return true;
            if(major!=1 || parts.length<2) return false;
            int minor=Integer.parseInt(parts[1]);
            return minor>21 || minor==21 && parts.length>2 && Integer.parseInt(parts[2])>=11;
        } catch(NumberFormatException ex) { return false; }
    }
}


===== src/main/java/com/donsup/compat/ItemKey.java =====

package com.donsup.compat;

import java.util.Locale;
import java.util.Objects;
import org.bukkit.plugin.Plugin;

/** Keeps the existing namespace without loading Bukkit's post-1.8 NamespacedKey. */
public record ItemKey(String namespace, String key) {
    public ItemKey(Plugin plugin, String key) { this(plugin.getName().toLowerCase(Locale.ROOT), key); }
    public ItemKey {
        Objects.requireNonNull(namespace); Objects.requireNonNull(key);
        if (!namespace.matches("[a-z0-9._-]+") || !key.matches("[a-z0-9/._-]+"))
            throw new IllegalArgumentException("Invalid item data key");
    }
    @Override public String toString() { return namespace + ":" + key; }
}


===== src/main/java/com/donsup/compat/ItemTags.java =====

package com.donsup.compat;

import java.lang.reflect.*;
import java.util.Map;
import org.bukkit.Bukkit;
import org.bukkit.inventory.meta.ItemMeta;

/** PDC on modern servers; preserved custom NBT on pre-1.14 CraftBukkit. Never uses editable lore as identity. */
public final class ItemTags {
    private static final boolean PDC = available("org.bukkit.persistence.PersistentDataContainer");
    private static final boolean CUSTOM = available("org.bukkit.inventory.meta.tags.ItemTagType");
    private ItemTags() {}
    static boolean available(String name) {
        try { Class.forName(name, false, ItemTags.class.getClassLoader()); return true; }
        catch (ClassNotFoundException | LinkageError ex) { return false; }
    }
    public static String getString(ItemMeta meta, ItemKey key) {
        if (PDC) return ModernItemTags.getString(meta, key);
        if (CUSTOM) return (String)custom(meta,key,"STRING","getCustomTag",null);
        Object compound=tags(meta).get("PublicBukkitValues");
        if(compound!=null && (boolean)BukkitCompat.call(compound,"hasKeyOfType",new Class<?>[]{String.class,int.class},key.toString(),8))
            return (String)BukkitCompat.call(compound,"getString",new Class<?>[]{String.class},key.toString());
        Object tag = tags(meta).get(key.toString());
        if (tag == null) return null;
        try {
            for (Field field : tag.getClass().getDeclaredFields()) if (field.getType() == String.class && !Modifier.isStatic(field.getModifiers())) {
                field.setAccessible(true); return (String) field.get(tag);
            }
            return null;
        } catch (ReflectiveOperationException ex) { throw failure(ex); }
    }
    public static void setString(ItemMeta meta, ItemKey key, String value) {
        if (PDC) { ModernItemTags.setString(meta, key, value); return; }
        if (CUSTOM) { custom(meta,key,"STRING","setCustomTag",value); return; }
        Object compound=copyCompound(meta);
        BukkitCompat.call(compound,"setString",new Class<?>[]{String.class,String.class},key.toString(),value);
        tags(meta).put("PublicBukkitValues",compound); tags(meta).remove(key.toString());
    }
    public static boolean hasByte(ItemMeta meta, ItemKey key) {
        if(PDC) return ModernItemTags.hasByte(meta,key);
        if(CUSTOM) return (boolean)custom(meta,key,"BYTE","hasCustomTag",null);
        Object compound=tags(meta).get("PublicBukkitValues");
        return compound!=null && (boolean)BukkitCompat.call(compound,"hasKeyOfType",new Class<?>[]{String.class,int.class},key.toString(),1)
                || "1".equals(getString(meta,key));
    }
    public static void setByte(ItemMeta meta, ItemKey key, byte value) {
        if (PDC) { ModernItemTags.setByte(meta,key,value); return; }
        if (CUSTOM) { custom(meta,key,"BYTE","setCustomTag",value); return; }
        Object compound=copyCompound(meta);
        BukkitCompat.call(compound,"setByte",new Class<?>[]{String.class,byte.class},key.toString(),value);
        tags(meta).put("PublicBukkitValues",compound); tags(meta).remove(key.toString());
    }
    private static Object copyCompound(ItemMeta meta) {
        Object existing=tags(meta).get("PublicBukkitValues");
        if(existing!=null) return BukkitCompat.call(existing,"clone");
        try {
            String revision=Bukkit.getServer().getClass().getPackage().getName().substring("org.bukkit.craftbukkit.".length());
            return Class.forName("net.minecraft.server."+revision+".NBTTagCompound").getConstructor().newInstance();
        } catch(ReflectiveOperationException ex) { throw failure(ex); }
    }
    // 1.13 consumes PublicBukkitValues into CustomItemTagContainer, before PDC was introduced.
    private static Object custom(ItemMeta meta,ItemKey key,String kind,String operation,Object value) {
        try {
            Class<?> namespaced=Class.forName("org.bukkit.NamespacedKey");
            Class<?> tagType=Class.forName("org.bukkit.inventory.meta.tags.ItemTagType");
            Object id=namespaced.getConstructor(String.class,String.class).newInstance(key.namespace(),key.key());
            Object type=tagType.getField(kind).get(null),container=BukkitCompat.call(meta,"getCustomTagContainer");
            return value==null ? BukkitCompat.call(container,operation,new Class<?>[]{namespaced,tagType},id,type)
                    : BukkitCompat.call(container,operation,new Class<?>[]{namespaced,tagType,Object.class},id,type,value);
        } catch(ReflectiveOperationException ex) { throw failure(ex); }
    }
    @SuppressWarnings("unchecked") private static Map<String, Object> tags(ItemMeta meta) {
        try {
            for (Class<?> type = meta.getClass(); type != null; type = type.getSuperclass()) {
                try { Field field = type.getDeclaredField("unhandledTags"); field.setAccessible(true); return (Map<String, Object>) field.get(meta); }
                catch (NoSuchFieldException ignored) {}
            }
            throw new NoSuchFieldException("CraftMetaItem.unhandledTags");
        } catch (ReflectiveOperationException ex) { throw failure(ex); }
    }
    private static IllegalStateException failure(Exception ex) { return new IllegalStateException("This server cannot preserve custom item tags", ex); }
}


===== src/main/java/com/donsup/compat/LegacyTab.java =====

package com.donsup.compat;

import java.lang.reflect.*;
import org.bukkit.entity.Player;

/** The 1.8-1.12 protocol already supports tab headers; Bukkit did not expose them yet. */
final class LegacyTab {
    private LegacyTab() {}
    static void send(Player player,String header,String footer) {
        try {
            Object handle=BukkitCompat.call(player,"getHandle");
            String nms=handle.getClass().getPackage().getName()+".";
            Class<?> text=Class.forName(nms+"ChatComponentText");
            Class<?> packetClass=Class.forName(nms+"PacketPlayOutPlayerListHeaderFooter");
            Object packet=packetClass.getConstructor().newInstance();
            Field top=packetClass.getDeclaredField("a"),bottom=packetClass.getDeclaredField("b");
            top.setAccessible(true); bottom.setAccessible(true);
            top.set(packet,text.getConstructor(String.class).newInstance(header));
            bottom.set(packet,text.getConstructor(String.class).newInstance(footer));
            Object connection=handle.getClass().getField("playerConnection").get(handle);
            BukkitCompat.call(connection,"sendPacket",new Class<?>[]{Class.forName(nms+"Packet")},packet);
        } catch(ReflectiveOperationException ex) { throw new IllegalStateException("Legacy tab header API unavailable",ex); }
    }
}


===== src/main/java/com/donsup/compat/Materials.java =====

package com.donsup.compat;

import java.util.*;
import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;
import org.bukkit.configuration.ConfigurationSection;

/** Renamed materials retain their identity. Visual fallbacks are separate from tradable item lookup. */
public final class Materials {
    private Materials() {}
    private static final Map<String,String> ALIASES = new HashMap<>();
    private static final Map<String,String> ICONS = new HashMap<>();
    static {
        ALIASES.put("SPAWNER", "MOB_SPAWNER");
        ALIASES.put("WRITABLE_BOOK", "BOOK_AND_QUILL");
        ALIASES.put("GRAY_STAINED_GLASS_PANE", "STAINED_GLASS_PANE");
        ALIASES.put("BLACK_STAINED_GLASS_PANE", "STAINED_GLASS_PANE");
        ALIASES.put("RED_BED", "BED");
        ALIASES.put("LIME_BED", "BED");
        ALIASES.put("GRAY_DYE", "INK_SACK");
        ALIASES.put("LIME_DYE", "INK_SACK");
        ALIASES.put("COMPARATOR", "REDSTONE_COMPARATOR");
        ALIASES.put("PLAYER_HEAD", "SKULL_ITEM");
        ALIASES.put("CREEPER_HEAD", "SKULL_ITEM");
        ALIASES.put("OAK_SIGN", "SIGN");
        ALIASES.put("LIME_CONCRETE", "CONCRETE");
        ALIASES.put("RED_CONCRETE", "CONCRETE");
        ALIASES.put("CLOCK", "WATCH");
        ALIASES.put("COMMAND_BLOCK", "COMMAND");
        ALIASES.put("EXPERIENCE_BOTTLE", "EXP_BOTTLE");
        ALIASES.put("LIME_BANNER", "BANNER");
        ALIASES.put("REDSTONE_TORCH", "REDSTONE_TORCH_ON");
        ALIASES.put("SUNFLOWER", "DOUBLE_PLANT");
        ALIASES.put("END_STONE", "ENDER_STONE");
        ALIASES.put("GRASS_BLOCK", "GRASS");
        ALIASES.put("OAK_DOOR", "WOOD_DOOR");
        ALIASES.put("OAK_LOG", "LOG");
        ALIASES.put("CRAFTING_TABLE", "WORKBENCH");
        ALIASES.put("CAVE_AIR", "AIR");
        ALIASES.put("VOID_AIR", "AIR");
        ALIASES.put("GUNPOWDER", "SULPHUR");
        ALIASES.put("CARROT", "CARROT_ITEM");
        ALIASES.put("POTATO", "POTATO_ITEM");
        ALIASES.put("WHITE_BANNER", "BANNER");
        ALIASES.put("CHEST_MINECART", "STORAGE_MINECART");
        ALIASES.put("BEEF", "RAW_BEEF");
        ALIASES.put("PORKCHOP", "PORK");
        ALIASES.put("CHICKEN", "RAW_CHICKEN");
        ALIASES.put("COOKED_PORKCHOP", "GRILLED_PORK");
        ALIASES.put("WHITE_WOOL", "WOOL");
        ALIASES.put("SPRUCE_LOG", "LOG");
        ALIASES.put("BIRCH_LOG", "LOG");
        ALIASES.put("JUNGLE_LOG", "LOG");
        ALIASES.put("ACACIA_LOG", "LOG_2");
        ALIASES.put("DARK_OAK_LOG", "LOG_2");
        ALIASES.put("PISTON", "PISTON_BASE");
        ALIASES.put("STICKY_PISTON", "PISTON_STICKY_BASE");
        ICONS.put("AMETHYST_SHARD", "PRISMARINE_SHARD");
        ICONS.put("TARGET", "BOW");
        ICONS.put("SPYGLASS", "COMPASS");
        ICONS.put("SHIELD", "IRON_CHESTPLATE");
        ICONS.put("LECTERN", "BOOKSHELF");
        ICONS.put("BARREL", "CHEST");
        ICONS.put("SHULKER_BOX", "CHEST");
        ICONS.put("BELL", "GOLD_INGOT");
        ICONS.put("AMETHYST_CLUSTER", "PRISMARINE");
        ICONS.put("POWDER_SNOW", "SNOW");
        ICONS.put("POINTED_DRIPSTONE", "CACTUS");
        ICONS.put("CAMPFIRE", "FIRE");
        ICONS.put("SOUL_CAMPFIRE", "FIRE");
        ICONS.put("MAGMA_BLOCK", "NETHERRACK");
    }
    private static Material direct(String name) {
        try { return Material.valueOf(name); } catch (IllegalArgumentException ex) { return null; }
    }
    public static Material match(String input) {
        if(input==null) return null;
        String name=input.toUpperCase(Locale.ROOT).replace("MINECRAFT:", "");
        // Before flattening, CARROT and POTATO refer to planted blocks, not inventory items.
        if (direct("OAK_LOG")==null && (name.equals("CARROT") || name.equals("POTATO"))) return direct(ALIASES.get(name));
        Material material=direct(name);
        if(material!=null) return material;
        String alias=ALIASES.get(name);
        if(alias!=null) return direct(alias);
        for(var entry:ALIASES.entrySet()) if(entry.getValue().equals(name)) {
            material=direct(entry.getKey()); if(material!=null) return material;
        }
        return null;
    }
    public static Material icon(String name) {
        Material material=match(name);
        if(material!=null) return material;
        String fallback=ICONS.get(name.toUpperCase(Locale.ROOT));
        return fallback==null ? null : match(fallback);
    }
    public static Set<Material> presentSet(String... names) {
        Set<Material> result=new HashSet<>();
        for(String name:names) { Material material=direct(name); if(material!=null) result.add(material); }
        return Collections.unmodifiableSet(result);
    }
    public static ItemStack stack(String name,int amount) {
        Material material=match(name);
        if(material==null || !BukkitCompat.item(material)) return null;
        ItemStack item=new ItemStack(material,amount);
        if(direct("OAK_LOG")==null) {
            String normalized=name.toUpperCase(Locale.ROOT).replace("MINECRAFT:","");
            int data=switch(normalized) {
                case "SPRUCE_LOG", "DARK_OAK_LOG" -> 1;
                case "BIRCH_LOG" -> 2;
                case "JUNGLE_LOG", "PLAYER_HEAD" -> 3;
                case "CREEPER_HEAD" -> 4;
                case "GRAY_DYE" -> 8;
                case "BLACK_STAINED_GLASS_PANE", "WHITE_BANNER" -> 15;
                case "LIME_DYE", "LIME_BANNER" -> 10;
                case "GRAY_STAINED_GLASS_PANE" -> 7;
                case "LIME_CONCRETE" -> 5;
                case "RED_CONCRETE" -> 14;
                case "RED_BED" -> direct("CONCRETE")==null ? 0 : 14;
                case "LIME_BED" -> direct("CONCRETE")==null ? 0 : 5;
                default -> 0;
            };
            item.setDurability((short)data);
        }
        return item;
    }
    public static double price(ConfigurationSection prices,ItemStack item) {
        if(prices==null) return 0;
        if(prices.contains(item.getType().name())) return prices.getDouble(item.getType().name());
        for(String name:prices.getKeys(false)) {
            ItemStack configured=stack(name,1);
            if(configured!=null && configured.getType()==item.getType() && configured.getDurability()==item.getDurability()) return prices.getDouble(name);
        }
        return 0;
    }
    private static Material fallback(String name,String fallback) {
        Material material=match(name); return material==null ? Objects.requireNonNull(match(fallback), fallback) : material;
    }
    private static Material visual(String name,String fallback) {
        Material material=direct(name);return material==null ? Objects.requireNonNull(match(fallback),fallback) : material;
    }
    public static final Material SPAWNER = fallback("SPAWNER","MOB_SPAWNER");
    public static final Material WRITABLE_BOOK = fallback("WRITABLE_BOOK","BOOK_AND_QUILL");
    public static final Material GRAY_STAINED_GLASS_PANE = fallback("GRAY_STAINED_GLASS_PANE","STAINED_GLASS_PANE");
    public static final Material BLACK_STAINED_GLASS_PANE = fallback("BLACK_STAINED_GLASS_PANE","STAINED_GLASS_PANE");
    public static final Material RED_BED = fallback("RED_BED","BED");
    public static final Material LIME_BED = fallback("LIME_BED","BED");
    public static final Material GRAY_DYE = visual("GRAY_DYE","STONE_BUTTON");
    public static final Material LIME_DYE = visual("LIME_DYE","SLIME_BALL");
    public static final Material COMPARATOR = fallback("COMPARATOR","REDSTONE_COMPARATOR");
    public static final Material PLAYER_HEAD = fallback("PLAYER_HEAD","SKULL_ITEM");
    public static final Material CREEPER_HEAD = fallback("CREEPER_HEAD","SKULL_ITEM");
    public static final Material OAK_SIGN = fallback("OAK_SIGN","SIGN");
    public static final Material LIME_CONCRETE = visual("LIME_CONCRETE","EMERALD_BLOCK");
    public static final Material RED_CONCRETE = visual("RED_CONCRETE","REDSTONE_BLOCK");
    public static final Material CLOCK = fallback("CLOCK","WATCH");
    public static final Material COMMAND_BLOCK = fallback("COMMAND_BLOCK","COMMAND");
    public static final Material EXPERIENCE_BOTTLE = fallback("EXPERIENCE_BOTTLE","EXP_BOTTLE");
    public static final Material LIME_BANNER = fallback("LIME_BANNER","BANNER");
    public static final Material REDSTONE_TORCH = fallback("REDSTONE_TORCH","REDSTONE_TORCH_ON");
    public static final Material SUNFLOWER = fallback("SUNFLOWER","DOUBLE_PLANT");
    public static final Material END_STONE = fallback("END_STONE","ENDER_STONE");
    public static final Material GRASS_BLOCK = fallback("GRASS_BLOCK","GRASS");
    public static final Material OAK_DOOR = fallback("OAK_DOOR","WOOD_DOOR");
    public static final Material OAK_LOG = fallback("OAK_LOG","LOG");
    public static final Material CRAFTING_TABLE = fallback("CRAFTING_TABLE","WORKBENCH");
    public static final Material CAVE_AIR = fallback("CAVE_AIR","AIR");
    public static final Material VOID_AIR = fallback("VOID_AIR","AIR");
    public static final Material AMETHYST_SHARD = fallback("AMETHYST_SHARD","PRISMARINE_SHARD");
    public static final Material TARGET = fallback("TARGET","BOW");
    public static final Material SPYGLASS = fallback("SPYGLASS","COMPASS");
    public static final Material SHIELD = fallback("SHIELD","IRON_CHESTPLATE");
    public static final Material LECTERN = fallback("LECTERN","BOOKSHELF");
    public static final Material BARREL = fallback("BARREL","CHEST");
    public static final Material SHULKER_BOX = fallback("SHULKER_BOX","CHEST");
    public static final Material BELL = fallback("BELL","GOLD_INGOT");
    public static final Material AMETHYST_CLUSTER = fallback("AMETHYST_CLUSTER","PRISMARINE");
    public static final Material POWDER_SNOW = fallback("POWDER_SNOW","SNOW");
    public static final Material POINTED_DRIPSTONE = fallback("POINTED_DRIPSTONE","CACTUS");
    public static final Material CAMPFIRE = fallback("CAMPFIRE","FIRE");
    public static final Material SOUL_CAMPFIRE = fallback("SOUL_CAMPFIRE","FIRE");
    public static final Material MAGMA_BLOCK = fallback("MAGMA_BLOCK","NETHERRACK");
}


===== src/main/java/com/donsup/compat/ModernBlockTags.java =====

package com.donsup.compat;

import org.bukkit.NamespacedKey;
import org.bukkit.block.*;
import org.bukkit.persistence.PersistentDataType;

final class ModernBlockTags {
    static String get(BlockState state,ItemKey key) { return ((TileState)state).getPersistentDataContainer().get(new NamespacedKey(key.namespace(),key.key()),PersistentDataType.STRING); }
    static void set(BlockState state,ItemKey key,String value) {
        var data=((TileState)state).getPersistentDataContainer(); var name=new NamespacedKey(key.namespace(),key.key());
        if(value==null) data.remove(name); else data.set(name,PersistentDataType.STRING,value);
    }
}


===== src/main/java/com/donsup/compat/ModernItemTags.java =====

package com.donsup.compat;

import org.bukkit.NamespacedKey;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;

/** Loaded only when the server actually provides persistent item data. */
final class ModernItemTags {
    private static NamespacedKey key(ItemKey key) { return new NamespacedKey(key.namespace(), key.key()); }
    static String getString(ItemMeta meta, ItemKey key) { return meta.getPersistentDataContainer().get(key(key), PersistentDataType.STRING); }
    static void setString(ItemMeta meta, ItemKey key, String value) { meta.getPersistentDataContainer().set(key(key), PersistentDataType.STRING, value); }
    static boolean hasByte(ItemMeta meta, ItemKey key) { return meta.getPersistentDataContainer().has(key(key), PersistentDataType.BYTE); }
    static void setByte(ItemMeta meta, ItemKey key, byte value) { meta.getPersistentDataContainer().set(key(key), PersistentDataType.BYTE, value); }
}


===== src/main/java/com/donsup/compat/ModernVisuals.java =====

package com.donsup.compat;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.Text;
import org.bukkit.*;
import org.bukkit.block.*;
import org.bukkit.entity.*;

/** Optional display entities and ray tracing; this class is never linked on legacy servers. */
public final class ModernVisuals {
    private ModernVisuals() {}
    public static Location previewLocation(Player player,int range) {
        var result=player.rayTraceBlocks(range);
        if(result==null || result.getHitBlock()==null) return null;
        BlockFace face=result.getHitBlockFace();
        Block target=face==null ? result.getHitBlock() : result.getHitBlock().getRelative(face);
        return target.getType().isAir() ? target.getLocation() : null;
    }
    public static Entity preview(DonsupPlugin plugin,Player player,Location location,Material material,String label) {
        BlockDisplay spawned=location.getWorld().spawn(location,BlockDisplay.class,entity -> {
            entity.setBlock(Bukkit.createBlockData(material)); entity.setGlowing(true);
            entity.setGlowColorOverride(Color.AQUA); entity.setBillboard(Display.Billboard.FIXED);
            entity.setViewRange(16F); entity.setPersistent(false);
            entity.setCustomName(Text.color(Lang.text("modern-visuals.preview-crate", "&bPreview: {0} Crate", label))); entity.setCustomNameVisible(false);
        });
        for(Player other:Bukkit.getOnlinePlayers()) if(!other.equals(player)) plugin.platform().playerNow(other,()->other.hideEntity(plugin,spawned));
        player.showEntity(plugin,spawned);
        return spawned;
    }
}


===== src/main/java/com/donsup/compat/Views.java =====

package com.donsup.compat;

import org.bukkit.inventory.Inventory;

/** InventoryView changed from a class to an interface; reflect across that binary boundary. */
public final class Views {
    private Views() {}
    public static Inventory top(Object view) { return (Inventory) BukkitCompat.call(view, "getTopInventory"); }
    public static String title(Object view) { return (String) BukkitCompat.call(view, "getTitle"); }
    public static boolean same(Inventory a,Inventory b) { return a==b || a!=null && a.equals(b); }
}


===== src/main/java/com/donsup/config/Branding.java =====

package com.donsup.config;

import org.bukkit.configuration.ConfigurationSection;

/** Display branding only. Plugin IDs, permissions and saved item keys stay stable. */
public final class Branding {
    private Branding() { }
    public static String name(ConfigurationSection config) {
        return config.getString("branding.server-name", "Donut SMP All In One");
    }
    public static String expand(String text, ConfigurationSection config) {
        return text.replace("%server%", name(config));
    }
    public static String display(ConfigurationSection config) {
        String value = config.getString("branding.display-name", "&6&l%server%");
        if (value.equals("&6&lDonsup All In One")) value = "&6&l%server%";
        return expand(value, config);
    }
    public static String menuPrefix(ConfigurationSection config) {
        String value = config.getString("branding.menu-title-prefix", "%server% | ");
        if (value.equals("Donsup | ") || value.equals("SMP | ")) value = "%server% | ";
        return expand(value, config);
    }
    public static String dialogTitle(String value) {
        return value.equals("<gold>Donsup</gold> <white>All In One</white>") || value.equals("Donsup All In One")
                ? "<gold>%server%</gold>" : value;
    }
    public static String chatPrefix(ConfigurationSection config) {
        String value=config.getString("messages.prefix","&6&l%server% &8>> &f");
        if(value.equals("&6&lSMP &8>> &f")) value="&6&l%server% &8>> &f";
        return expand(value,config);
    }
    public static String validateName(String input) {
        String name = input.trim();
        if (name.isEmpty() || name.length() > 48 || name.chars().anyMatch(Character::isISOControl))
            throw new IllegalArgumentException("Use a server name of 1-48 characters without control characters.");
        return name;
    }
}


===== src/main/java/com/donsup/config/Customization.java =====

package com.donsup.config;

import org.bukkit.Material;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Validated, immutable presentation snapshot. A failed load never replaces the active snapshot. */
public final class Customization {
    public record Button(String id, String label, Material icon, int slot, String command, String permission, boolean enabled, List<String> lore) {
        public boolean visible(Player player) { return enabled && (permission.isEmpty() || player.hasPermission(permission)); }
    }
    private final YamlConfiguration menus;
    private final List<Button> buttons;
    private final Map<String, String> menuText;
    private final Map<String, String> messages;
    private final Map<String, String> titles;

    private Customization(YamlConfiguration menus, List<Button> buttons, Map<String,String> menuText,
                          Map<String,String> messages, Map<String,String> titles) {
        this.menus=menus; this.buttons=List.copyOf(buttons); this.menuText=Map.copyOf(menuText);
        this.messages=Map.copyOf(messages); this.titles=Map.copyOf(titles);
    }
    public static Customization load(Path directory) {
        var menus=read(directory.resolve("menus.yml"), "menus.yml");
        var messages=read(directory.resolve("messages.yml"), "messages.yml");
        return parse(menus,messages);
    }
    public static YamlConfiguration defaults(String resource) {
        var config=new YamlConfiguration();
        try (var input=Customization.class.getResourceAsStream("/"+resource)) {
            if(input==null) throw new IOException("Missing bundled resource "+resource);
            config.load(new InputStreamReader(input,StandardCharsets.UTF_8));
            return config;
        } catch(Exception ex) { throw new IllegalArgumentException(resource+": "+ex.getMessage(),ex); }
    }
    public static YamlConfiguration read(Path file, String resource) {
        try {
            if(!Files.exists(file)) {
                Files.createDirectories(file.getParent());
                try(var input=Objects.requireNonNull(Customization.class.getResourceAsStream("/"+resource))) { Files.copy(input,file); }
            }
            var result=new YamlConfiguration();
            result.load(file.toFile());
            result.setDefaults(defaults(resource));
            return result;
        } catch(Exception ex) { throw new IllegalArgumentException(file.getFileName()+": "+ex.getMessage(),ex); }
    }
    public static Customization parse(YamlConfiguration menus, YamlConfiguration messages) {
        menus.setDefaults(defaults("menus.yml")); messages.setDefaults(defaults("messages.yml"));
        int rows=integer(menus,"dashboard.inventory-rows",1,6);
        integer(menus,"dashboard.columns",1,4);
        string(menus,"dashboard.summary");
        int close=integer(menus,"dashboard.close-slot",0,rows*9-1);
        integer(menus,"pause.button-width",150,400);
        string(menus,"pause.title"); string(menus,"pause.external-title"); string(menus,"pause.close-label");
        var order=strings(menus,"dashboard.order");
        if(order.isEmpty() || order.size()>53) throw invalid("dashboard.order", "must contain 1-53 unique button IDs");
        var seen=new HashSet<String>(); var slots=new HashSet<Integer>(); slots.add(close);
        var buttons=new ArrayList<Button>();
        for(String id:order) {
            if(!id.matches("[a-z0-9_-]+") || !seen.add(id)) throw invalid("dashboard.order", "invalid or duplicate ID: "+id);
            String key="dashboard.buttons."+id;
            if(!menus.isConfigurationSection(key)) throw invalid(key,"missing button definition");
            String label=string(menus,key+".label");
            String icon=string(menus,key+".icon"); Material material=com.donsup.compat.Materials.icon(icon);
            // Paper bootstrap runs before Bukkit's item registry is available.
            if(material==null || material==Material.AIR || material==com.donsup.compat.Materials.CAVE_AIR || material==com.donsup.compat.Materials.VOID_AIR || com.donsup.compat.BukkitCompat.legacy(material))
                throw invalid(key+".icon","unknown item material: "+icon);
            int slot=integer(menus,key+".slot",0,rows*9-1);
            boolean enabled=bool(menus,key+".enabled");
            if(enabled && !slots.add(slot)) throw invalid(key+".slot","overlaps another button or the close slot");
            String command=string(menus,key+".command").replaceFirst("^/", "");
            if(command.isBlank() || command.length()>256 || command.chars().anyMatch(Character::isISOControl)) throw invalid(key+".command","must be one player command");
            if(menus.contains(key+".permission") && !menus.isString(key+".permission")) throw invalid(key+".permission","must be text");
            String permission=menus.getString(key+".permission", "");
            if(!permission.isEmpty() && !permission.matches("[A-Za-z0-9_.*-]+")) throw invalid(key+".permission","invalid permission node");
            buttons.add(new Button(id,label,material,slot,command,permission,enabled,List.copyOf(strings(menus,key+".lore"))));
        }
        var pauseSeen=new HashSet<String>();
        for(String route:strings(menus,"pause.order")) {
            if(!Set.of("main","settings","auction","orders","homes","friends").contains(route) || !pauseSeen.add(route))
                throw invalid("pause.order","invalid or duplicate route: "+route);
            string(menus,"pause.labels."+route);
        }
        if(pauseSeen.isEmpty()) throw invalid("pause.order","at least one route is required");
        Map<String,String> titles=new LinkedHashMap<>();
        if(!menus.isConfigurationSection("inventory-titles")) throw invalid("inventory-titles","must be a mapping of headings to text");
        var titleKeys = new LinkedHashSet<>(defaults("menus.yml").getConfigurationSection("inventory-titles").getKeys(false));
        titleKeys.addAll(menus.getConfigurationSection("inventory-titles").getKeys(false));
        for(String key:titleKeys)
            titles.put(key,string(menus,"inventory-titles."+key));
        return new Customization(menus,buttons,catalog(menus,"menus.yml","text"),catalog(messages,"messages.yml","messages"),titles);
    }
    private static Map<String,String> catalog(YamlConfiguration loaded,String resource,String section) {
        var bundled=defaults(resource).getConfigurationSection(section);
        Map<String,String> result=new HashMap<>();
        for(String key:bundled.getKeys(false)) {
            String path=section+"."+key;
            if(!loaded.isString(path)) throw invalid(path,"must be a text string");
            result.put(bundled.getString(key),loaded.getString(path));
        }
        return result;
    }
    private static String string(ConfigurationSection c,String path) {
        if(!c.isString(path) || c.getString(path).isBlank()) throw invalid(path,"must be nonempty text");
        return c.getString(path);
    }
    private static int integer(ConfigurationSection c,String path,int min,int max) {
        if(!c.isInt(path) || c.getInt(path)<min || c.getInt(path)>max) throw invalid(path,"must be an integer between "+min+" and "+max);
        return c.getInt(path);
    }
    private static boolean bool(ConfigurationSection c,String path) {
        if(!c.isBoolean(path)) throw invalid(path,"must be true or false");
        return c.getBoolean(path);
    }
    private static List<String> strings(ConfigurationSection c,String path) {
        if(!c.isList(path) || c.getList(path).stream().anyMatch(v->!(v instanceof String))) throw invalid(path,"must be a list of text values");
        return c.getStringList(path);
    }
    private static IllegalArgumentException invalid(String path,String message) { return new IllegalArgumentException(path+": "+message); }
    public List<Button> buttons() { return buttons; }
    public void validateRuntimeItems() {
        for(var button:buttons) if(!com.donsup.compat.BukkitCompat.item(button.icon())) throw invalid("dashboard.buttons."+button.id()+".icon","material has no item form");
    }
    public int rows() { return menus.getInt("dashboard.inventory-rows"); }
    public int columns() { return menus.getInt("dashboard.columns"); }
    public int closeSlot() { return menus.getInt("dashboard.close-slot"); }
    public String summary(String money,int shards) {
        return menus.getString("dashboard.summary").replace("%money%",money).replace("%shards%",Integer.toString(shards));
    }
    public String menuText(String original) { return menuText.getOrDefault(original,original); }
    public String message(String original) { return messages.getOrDefault(original,original); }
    public List<String> pauseOrder() { return menus.getStringList("pause.order"); }
    public String pause(String key) { return menus.getString("pause."+key); }
    public int pauseWidth() { return menus.getInt("pause.button-width"); }
    public String inventoryTitle(String canonical,ConfigurationSection config) {
        String suffix=canonical.startsWith("SMP | ")?canonical.substring(6):
                canonical.startsWith("menu:")?canonical.substring(5):
                canonical.startsWith("creator:")?"Creator | "+canonical.substring(8):canonical;
        // Match the fixed part only. Player-created names and storage identities are never translated.
        String original=suffix;
        // An owner's existing broad rename wins over a newly added, unchanged default heading.
        String longest=titles.keySet().stream().filter(k->original.equals(k)||original.startsWith(k+" "))
                .max(Comparator.<String,Boolean>comparing(k -> !titles.get(k).equals(k))
                        .thenComparingInt(String::length)).orElse(null);
        if(longest!=null) suffix=Branding.expand(titles.get(longest),config)+suffix.substring(longest.length());
        return Branding.menuPrefix(config)+suffix;
    }
}


===== src/main/java/com/donsup/config/Lang.java =====

package com.donsup.config;

import org.bukkit.Material;
import org.bukkit.configuration.file.YamlConfiguration;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

/** Immutable server-wide presentation catalogue. Never used for commands or storage identities. */
public final class Lang {
    private static final Pattern ARGUMENT = Pattern.compile("\\{(\\d+)\\}");
    private static volatile Lang active = new Lang(Map.of(), Map.of());
    private final Map<String,String> text;
    private final Map<String,String> names;

    private Lang(Map<String,String> text, Map<String,String> names) {
        this.text = Map.copyOf(text);
        this.names = Map.copyOf(names);
    }

    public static Lang load(Path directory) {
        var defaults = Customization.defaults("language.yml");
        var file = directory.resolve("language.yml");
        var loaded = Customization.read(file, "language.yml");
        var labels = Customization.read(directory.resolve("language-names.yml"), "language-names.yml");
        Lang result = parse(loaded, defaults, labels);
        // Reference files can be replaced on upgrades. The owner's editable files are never rewritten.
        try {
            writeReference(directory.resolve("language-defaults.yml"), defaults.saveToString());
            var nameDefaults = Customization.defaults("language-names.yml");
            for (Material material : Material.values()) {
                String key = "materials." + material.name();
                if (!nameDefaults.contains(key)) nameDefaults.set(key, material.name());
            }
            writeReference(directory.resolve("language-names-reference.yml"), nameDefaults.saveToString());
        } catch (IOException ex) {
            throw new IllegalArgumentException("Cannot write language reference files: " + ex.getMessage(), ex);
        }
        return result;
    }

    private static void writeReference(Path path, String value) throws IOException {
        Path temporary = Files.createTempFile(path.getParent(), "language-reference-", ".tmp");
        try {
            Files.writeString(temporary, value, StandardCharsets.UTF_8);
            try { Files.move(temporary, path, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING); }
            catch (AtomicMoveNotSupportedException ex) { Files.move(temporary, path, StandardCopyOption.REPLACE_EXISTING); }
        } finally { Files.deleteIfExists(temporary); }
    }

    static Lang parse(YamlConfiguration loaded, YamlConfiguration defaults, YamlConfiguration labels) {
        Map<String,String> values = new HashMap<>();
        for (String path : loaded.getKeys(true)) {
            if (loaded.isConfigurationSection(path)) continue;
            if (!defaults.contains(path)) throw new IllegalArgumentException("language.yml: unknown key " + path);
        }
        for (String path : defaults.getKeys(true)) {
            if (defaults.isConfigurationSection(path)) {
                if (loaded.contains(path) && !loaded.isConfigurationSection(path))
                    throw new IllegalArgumentException("language.yml: " + path + " must be a section");
                continue;
            }
            Object raw = loaded.get(path, defaults.get(path));
            if (!(raw instanceof String value)) throw new IllegalArgumentException("language.yml: " + path + " must be quoted text");
            String fallback = defaults.getString(path);
            if (!value.isEmpty() && !arguments(value).equals(arguments(fallback)))
                throw new IllegalArgumentException("language.yml: " + path + " must keep placeholders " + arguments(fallback));
            values.put(path.substring("text.".length()), value);
        }
        Map<String,String> nameValues = new HashMap<>();
        for (String path : labels.getKeys(true)) {
            if (labels.isConfigurationSection(path)) continue;
            Object raw = labels.get(path);
            if (!(raw instanceof String value)) throw new IllegalArgumentException("language-names.yml: " + path + " must be quoted text");
            nameValues.put(path, value);
        }
        return new Lang(values, nameValues);
    }

    private static Set<String> arguments(String value) {
        var found = new TreeSet<String>();
        var matcher = ARGUMENT.matcher(value);
        while (matcher.find()) found.add(matcher.group());
        return found;
    }

    public static void activate(Lang next) { active = Objects.requireNonNull(next); }
    public static void reset() { active = new Lang(Map.of(), Map.of()); }

    public static String text(String key, String fallback, Object... args) {
        Lang snapshot = active;
        return format(snapshot.text.getOrDefault(key, fallback), args, snapshot);
    }

    static String format(String template, Object[] args, Lang snapshot) {
        var result = new StringBuffer();
        var matcher = ARGUMENT.matcher(template);
        while (matcher.find()) {
            int index;
            try { index = Integer.parseInt(matcher.group(1)); }
            catch (NumberFormatException ex) { continue; }
            if (index >= args.length) continue;
            Object arg = args[index];
            String value = arg instanceof Material material ? snapshot.name("materials", material.name(), material.name())
                    : arg instanceof Boolean flag ? snapshot.name("states", flag.toString(), flag.toString()) : String.valueOf(arg);
            // A single pass: user-provided {0}, $, backslashes and translated fragments are literal values.
            matcher.appendReplacement(result, Matcher.quoteReplacement(value));
        }
        matcher.appendTail(result);
        return result.toString();
    }

    private String name(String group, String id, String fallback) { return names.getOrDefault(group + "." + id, fallback); }
    public static String label(String group, String id, String fallback) { return active.name(group, id, fallback); }
    public static String material(Material material) { return label("materials", material.name(), material.name()); }
    public static String materialName(String id) { return label("materials", id, id); }
}


===== src/main/java/com/donsup/crates/CrateManager.java =====

package com.donsup.crates;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.gui.OwnedInventory;
import com.donsup.util.InventoryCapacity;
import com.donsup.util.ItemUtil;
import org.bukkit.*;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.inventory.*;
import java.io.File;
import java.util.*;

/** Account keys and persisted choice menus; physical keys remain an optional legacy mode. */
public final class CrateManager implements Listener {
    private final DonsupPlugin plugin;
    private final KeyLedger ledger;
    private long retryKeyAllAfter;
    private final Map<UUID, Session> sessions = new HashMap<>();
    private record Session(Inventory inventory, String drawId) {}
    public CrateManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        ledger = new KeyLedger(new File(plugin.getDataFolder(), "keys.yml"));
        recoverAccounts();
        plugin.platform().globalTimer(this::tick, 20L, 20L);
    }
    public boolean accountMode() { return plugin.getConfig().getBoolean("crate-system.account-keys", true); }
    public boolean known(String type) { return KeyLedger.validType(type) && plugin.getConfig().isConfigurationSection("crates." + type); }
    public long balance(UUID player, String type) { return ledger.balance(player, type); }
    public boolean hasPending(UUID player) { return !ledger.pending(player).isEmpty(); }
    public boolean grant(Player player, String type, int amount) {
        if (!known(type) || amount < 1 || amount > 1_000_000) return false;
        try {
            if (accountMode()) ledger.grant(List.of(player.getUniqueId()), type, amount);
            else {
                ItemStack key = plugin.menus().keyItem(type, 1);
                if (!InventoryCapacity.fits(player, key, amount)) return false;
                int left = amount;
                while (left > 0) {
                    ItemStack stack = key.clone(); int batch = Math.min(left, stack.getMaxStackSize()); stack.setAmount(batch);
                    player.getInventory().addItem(stack); left -= batch;
                }
            }
            return true;
        } catch (Exception ex) { failure(player, ex); return false; }
    }
    public void command(CommandSender sender, String name, String[] args) {
        try {
            if (name.equals("keyall")) {
                if (!admin(sender)) return;
                if (args.length != 2 || !known(args[0])) { plugin.msg(sender, Lang.text("crate.keyall", "&e/keyall <crate> <amount>")); return; }
                int amount = amount(args[1]);
                if (!accountMode()) { plugin.msg(sender, Lang.text("crate.key-all-requires-account-keys-to-be-enabled", "&cKey-all requires account keys to be enabled.")); return; }
                int count = keyAll(args[0], amount, null);
                plugin.msg(sender, Lang.text("crate.granted-keys-to-online-players", "&aGranted {0} {1} keys to {2} online players.", amount, args[0], count));
            } else if (args.length > 0 && args[0].equalsIgnoreCase("give")) {
                if (!admin(sender)) return;
                if (args.length != 4 || !known(args[2])) { plugin.msg(sender, Lang.text("crate.keys-give", "&e/keys give <player> <crate> <amount>")); return; }
                int amount = amount(args[3]);
                OfflinePlayer target = knownPlayer(args[1]);
                if (target == null) { plugin.msg(sender, Lang.text("crate.that-player-must-have-joined-this-server-before", "&cThat player must have joined this server before.")); return; }
                if (accountMode()) ledger.grant(List.of(target.getUniqueId()), args[2], amount);
                else if(target.getPlayer()!=null && plugin.platform().folia()) {
                    Player receiver=target.getPlayer();
                    plugin.platform().onPlayer(receiver,() -> {
                        boolean granted=grant(receiver,args[2],amount);
                        plugin.msg(sender,granted?Lang.text("crate.physical-keys-granted", "&aPhysical keys granted."):Lang.text("crate.physical-keys-need-inventory-space", "&cPhysical keys need inventory space."));
                    });
                    return;
                } else if (target.getPlayer() == null || !grant(target.getPlayer(), args[2], amount)) {
                    plugin.msg(sender, Lang.text("crate.physical-keys-need-an-online-player-with-inventory-space", "&cPhysical keys need an online player with inventory space.")); return;
                }
                plugin.msg(sender, Lang.text("crate.gave-keys-to", "&aGave {0} {1} keys to {2}.", amount, args[2], target.getName()));
            } else if (args.length > 0 && args[0].equalsIgnoreCase("resolve")) {
                if (!admin(sender)) return;
                if (args.length != 3 || !(args[2].equals("refund") || args[2].equals("complete"))) {
                    plugin.msg(sender, Lang.text("crate.keys-resolve-after-checking-an-interrupted-delivery", "&e/keys resolve <player> <refund|complete> &7after checking an interrupted delivery.")); return;
                }
                OfflinePlayer target = knownPlayer(args[1]);
                if (target != null && !ledger.accountReward(target.getUniqueId()).isEmpty()) {
                    recoverAccount(target.getUniqueId());
                    plugin.msg(sender, Lang.text("crate.recovered-the-saved-account-reward-no-key-refund-was-issued", "&aRecovered the saved account reward. No key refund was issued.")); return;
                }
                if (target == null || !ledger.resolve(target.getUniqueId(), args[2].equals("refund"))) {
                    plugin.msg(sender, Lang.text("crate.no-interrupted-delivery-to-resolve", "&cNo interrupted delivery to resolve.")); return;
                }
                plugin.getLogger().info(sender.getName() + " resolved interrupted crate delivery for " + target.getUniqueId() + ": " + args[2]);
                plugin.msg(sender, Lang.text("crate.interrupted-delivery-resolved", "&aInterrupted delivery resolved: {0}.", args[2]));
            } else if (sender instanceof Player player) {
                if (args.length == 2 && args[0].equalsIgnoreCase("open")) { plugin.menus().openCrate(player, args[1]); return; }
                if (args.length == 1 && args[0].equalsIgnoreCase("claim")) { showPending(player); return; }
                if (args.length == 1 && args[0].equalsIgnoreCase("redeem")) { redeem(player); return; }
                if (args.length != 0) { plugin.msg(sender, Lang.text("crate.keys-open-claim-redeem", "&e/keys [open <crate>|claim|redeem]")); return; }
                var crates = plugin.getConfig().getConfigurationSection("crates");
                if (crates != null) for (String type : crates.getKeys(false))
                    plugin.msg(player, Lang.text("crate.account-keys", "&b{0}: &f{1} account keys", Lang.label("labels", type, type), balance(player.getUniqueId(), type)));
                if (hasPending(player.getUniqueId())) plugin.msg(player, Lang.text("crate.you-have-a-saved-reward-choice-use-keys-claim", "&eYou have a saved reward choice. Use /keys claim."));
            } else plugin.msg(sender, Lang.text("crate.keys-give-or-keyall", "&e/keys give <player> <crate> <amount> or /keyall <crate> <amount>"));
        } catch (IllegalArgumentException ex) { plugin.msg(sender, Lang.text("crate.invalid-type-amount-or-key-balance-limit-amount-must-be-1-to-1-00", "&cInvalid type, amount or key balance limit. Amount must be 1 to 1,000,000.")); }
        catch (Exception ex) { failure(sender, ex); }
    }
    private int amount(String value) {
        int amount = Integer.parseInt(value);
        if (amount < 1 || amount > 1_000_000) throw new IllegalArgumentException();
        return amount;
    }
    private boolean admin(CommandSender sender) {
        if (sender.hasPermission("donsup.admin")) return true;
        plugin.msg(sender, Lang.text("crate.no-permission", "&cNo permission.")); return false;
    }
    private OfflinePlayer knownPlayer(String name) {
        Player online = Bukkit.getPlayerExact(name);
        if (online != null) return online;
        return plugin.economy().knownPlayer(name);
    }
    private void redeem(Player player) throws Exception {
        if (!accountMode()) { plugin.msg(player, Lang.text("crate.account-keys-are-disabled", "&cAccount keys are disabled.")); return; }
        ItemStack hand = com.donsup.compat.BukkitCompat.hand(player.getInventory());
        String type = plugin.menus().physicalKeyType(hand);
        if (!known(type)) { plugin.msg(player, Lang.text("crate.hold-a-valid-physical-crate-key-to-redeem-it", "&cHold a valid physical crate key to redeem it.")); return; }
        int count = hand.getAmount();
        ledger.grant(List.of(player.getUniqueId()), type, count);
        com.donsup.compat.BukkitCompat.hand(player.getInventory(), null);
        player.saveData();
        plugin.msg(player, Lang.text("crate.redeemed-account-keys", "&aRedeemed {0} {1} account keys.", count, Lang.label("labels", type, type)));
    }
    public void open(Player player, String type) {
        try {
            if (hasPending(player.getUniqueId())) { showPending(player); return; }
            if (!accountMode() || !known(type)) { plugin.msg(player, Lang.text("crate.unknown-crate-or-account-keys-are-disabled", "&cUnknown crate or account keys are disabled.")); return; }
            if (balance(player.getUniqueId(), type) < 1) {
                plugin.msg(player, Lang.text("crate.you-need-a-account-key-hold-an-old-physical-key-and-use-keys-rede", "&cYou need a {0} account key. Hold an old physical key and use /keys redeem to convert it.", Lang.label("labels", type, type))); return;
            }
            ConfigurationSection rewards = plugin.getConfig().getConfigurationSection("crates." + type + ".rewards");
            if (rewards == null || rewards.getKeys(false).isEmpty()) { plugin.msg(player, Lang.text("crate.this-crate-has-no-rewards-configured", "&cThis crate has no rewards configured.")); return; }
            List<Map<String, Object>> pool = new ArrayList<>();
            for (String name : rewards.getKeys(false)) {
                Map<String,Object> reward=snapshot(name,rewards.getConfigurationSection(name));
                if(reward!=null) pool.add(reward);
            }
            if(pool.isEmpty()) { plugin.msg(player,Lang.text("crate.this-crate-has-no-rewards-available-on-this-server-version-your-k", "&cThis crate has no rewards available on this server version. Your key was kept.")); return; }
            List<Map<String, Object>> choices = new ArrayList<>();
            for (int i = 0; i < 7; i++) choices.add(pick(pool));
            if (ledger.open(player.getUniqueId(), type, choices)) showPending(player);
        } catch (Exception ex) { failure(player, ex); }
    }
    private Map<String, Object> snapshot(String name, ConfigurationSection reward) {
        if (reward == null) throw new IllegalArgumentException("Invalid reward " + name);
        Map<String, Object> value = new LinkedHashMap<>();
        double money = reward.getDouble("money"); int shards = reward.getInt("shards");
        int amount = reward.getInt("amount", 1);
        if (!Double.isFinite(money) || money < 0 || money > 1e12 || shards < 0 || shards > 1_000_000 || amount < 1 || amount > 2304)
            throw new IllegalArgumentException("Invalid reward " + name);
        value.put("name", name); value.put("money", money); value.put("shards", shards);
        value.put("weight", Math.max(1, Math.min(1_000_000, reward.getInt("weight", 1))));
        String keyType = reward.getString("key-type"); String spawner = reward.getString("spawner-type");
        Material icon = Material.GOLD_INGOT;
        if (keyType != null) {
            if (!known(keyType)) throw new IllegalArgumentException("Unknown key reward");
            value.put("key-type", keyType); value.put("key-amount", amount); icon = Material.TRIPWIRE_HOOK;
        } else if (spawner != null) {
            if (!plugin.getConfig().isConfigurationSection("custom-spawners.types." + spawner)) throw new IllegalArgumentException("Unknown spawner reward");
            ItemStack item = plugin.spawners().spawnerItem(spawner, 1);
            value.put("item", item); value.put("amount", amount); icon = item.getType();
        } else if (money == 0 && shards == 0) {
            ItemStack item = com.donsup.compat.Materials.stack(reward.getString("material", "DIAMOND"),1);
            if (item == null) return null;
            value.put("item", item); value.put("amount", amount); icon = item.getType();
        } else if (money == 0) icon = com.donsup.compat.Materials.AMETHYST_SHARD;
        value.put("icon", icon.name());
        return value;
    }
    private Map<String, Object> pick(List<Map<String, Object>> pool) {
        long total = pool.stream().mapToLong(value -> ((Number)value.get("weight")).longValue()).sum();
        long selected = com.donsup.util.RandomBounded.nextLong(java.util.concurrent.ThreadLocalRandom.current(),total);
        for (var value : pool) { selected -= ((Number)value.get("weight")).longValue(); if (selected < 0) return new LinkedHashMap<>(value); }
        throw new IllegalStateException("No reward selected");
    }
    public void showPending(Player player) {
        try { if (recoverAccount(player.getUniqueId())) { plugin.msg(player, Lang.text("crate.recovered-your-interrupted-account-reward", "&aRecovered your interrupted account reward.")); return; } }
        catch (Exception ex) { failure(player, ex); return; }
        Map<String, Object> pending = ledger.pending(player.getUniqueId());
        if (pending.isEmpty()) { plugin.msg(player, Lang.text("crate.no-saved-choice-open-a-crate-using-crates", "&eNo saved choice. Open a crate using /crates.")); return; }
        if (!"choice".equals(pending.get("state"))) {
            plugin.msg(player, Lang.text("crate.your-previous-reward-delivery-was-interrupted-ask-staff-to-review", "&cYour previous reward delivery was interrupted. Ask staff to review it before opening another crate.")); return;
        }
        Inventory inventory = plugin.inventory(27, "SMP | Choose a Crate Reward", false);
        List<?> choices = (List<?>) pending.get("choices");
        for (int i = 0; i < choices.size(); i++) {
            Map<?, ?> reward = (Map<?, ?>) choices.get(i);
            List<String> lore = new ArrayList<>();
            if (((Number)reward.get("money")).doubleValue() > 0) lore.add(Lang.text("crate.money", "&7Money: &a{0}", reward.get("money")));
            if (((Number)reward.get("shards")).intValue() > 0) lore.add(Lang.text("crate.shards", "&7Shards: &d{0}", reward.get("shards")));
            if (reward.containsKey("key-type")) lore.add(Lang.text("crate.keys", "&7Keys: {0} {1}", reward.get("key-amount"), reward.get("key-type")));
            if (reward.containsKey("amount")) lore.add(Lang.text("crate.amount", "&7Amount: {0}", reward.get("amount")));
            lore.add(Lang.text("crate.choose-this-reward-you-receive-one-choice", "&aChoose this reward. You receive ONE choice."));
            inventory.setItem(10 + i, ItemUtil.named(Material.valueOf(String.valueOf(reward.get("icon"))), 1, Lang.text("crate.text", "&e{0}", reward.get("name")), lore));
        }
        inventory.setItem(22, ItemUtil.named(Material.BOOK, 1, Lang.text("crate.choose-one-of-seven", "&bChoose one of seven"), List.of(Lang.text("crate.your-key-was-spent-once", "&7Your key was spent once."), Lang.text("crate.close-and-resume-with-keys-claim", "&7Close and resume with /keys claim."), Lang.text("crate.repeated-rewards-are-possible", "&7Repeated rewards are possible."))));
        sessions.put(player.getUniqueId(), new Session(inventory, String.valueOf(pending.get("id"))));
        player.openInventory(inventory);
    }
    @EventHandler public void click(InventoryClickEvent event) {
        if (!(event.getWhoClicked() instanceof Player player)) return;
        Session session = sessions.get(player.getUniqueId());
        if (session == null || !com.donsup.compat.Views.same(session.inventory(),com.donsup.compat.Views.top(event.getView()))) return;
        event.setCancelled(true);
        int choice = event.getRawSlot() - 10;
        if (choice < 0 || choice > 6 || !event.isLeftClick()) return;
        plugin.platform().player(player, () -> {
            if (player.isOnline() && com.donsup.compat.Views.same(com.donsup.compat.Views.top(player.getOpenInventory()),session.inventory())) claim(player, session.drawId(), choice);
        });
    }
    @EventHandler public void quit(org.bukkit.event.player.PlayerQuitEvent event) { sessions.remove(event.getPlayer().getUniqueId()); }
    private void claim(Player player, String drawId, int choice) {
        try {
            Map<String, Object> pending = ledger.pending(player.getUniqueId());
            if (!drawId.equals(pending.get("id")) || !"choice".equals(pending.get("state"))) return;
            List<?> choices = (List<?>) pending.get("choices");
            if (choice >= choices.size()) return;
            Map<?, ?> reward = (Map<?, ?>) choices.get(choice);
            ItemStack item = (ItemStack)reward.get("item");
            int count = reward.get("amount") instanceof Number n ? n.intValue() : 0;
            if (item != null && !InventoryCapacity.fits(player, item, count)) {
                plugin.msg(player, Lang.text("crate.make-inventory-space-first-your-choices-are-saved", "&cMake inventory space first. Your choices are saved.")); return;
            }
            String keyType = (String)reward.get("key-type");
            int keys = reward.get("key-amount") instanceof Number n ? n.intValue() : 0;
            if (keyType != null && balance(player.getUniqueId(), keyType) > KeyLedger.MAX_KEYS - keys) {
                plugin.msg(player, Lang.text("crate.your-key-balance-is-full-choose-another-reward-or-use-some-keys-f", "&cYour key balance is full. Choose another reward or use some keys first.")); return;
            }
            double money = ((Number)reward.get("money")).doubleValue();
            int shards = ((Number)reward.get("shards")).intValue();
            if (!Double.isFinite(plugin.economy().money(player.getUniqueId()) + money)
                    || (long)plugin.economy().shards(player.getUniqueId()) + shards > Integer.MAX_VALUE) {
                plugin.msg(player, Lang.text("crate.this-reward-would-exceed-your-balance-limit-your-choice-is-still", "&cThis reward would exceed your balance limit. Your choice is still saved.")); return;
            }
            if (!ledger.beginClaim(player.getUniqueId(), drawId, choice)) return;
            if (item == null) {
                if (!recoverAccount(player.getUniqueId())) throw new java.io.IOException("Account reward is pending recovery");
                sessions.remove(player.getUniqueId()); player.closeInventory();
                plugin.msg(player, Lang.text("crate.claimed-crate-reward", "&aClaimed crate reward: {0}.", reward.get("name"))); return;
            }
            if ((money > 0 || shards > 0) && !plugin.economy().creditReward(player.getUniqueId(), money, shards))
                throw new java.io.IOException("Could not commit reward currencies; pending delivery retained for review");
            if (keyType != null) ledger.grant(List.of(player.getUniqueId()), keyType, keys);
            if (item != null) while (count > 0) {
                ItemStack stack = item.clone(); int batch = Math.min(count, item.getMaxStackSize()); stack.setAmount(batch);
                player.getInventory().addItem(stack); count -= batch;
            }
            player.saveData();
            ledger.finish(player.getUniqueId(), drawId);
            sessions.remove(player.getUniqueId()); player.closeInventory();
            plugin.msg(player, Lang.text("crate.claimed-crate-reward", "&aClaimed crate reward: {0}.", reward.get("name")));
        } catch (Exception ex) { failure(player, ex); }
    }
    private boolean recoverAccount(UUID player) throws Exception {
        Map<?, ?> reward = ledger.accountReward(player);
        if (reward.isEmpty()) return false;
        String drawId = String.valueOf(ledger.pending(player).get("id"));
        double money = ((Number)reward.get("money")).doubleValue();
        int shards = ((Number)reward.get("shards")).intValue();
        if (!plugin.economy().creditReward(drawId, player, money, shards))
            throw new java.io.IOException("Could not save reward payment " + drawId + "; claim remains pending");
        if (!ledger.finishAccountReward(player, drawId)) throw new java.io.IOException("Could not finish account reward " + drawId);
        // Remove only after the durable key ledger no longer contains a replayable claim.
        plugin.economy().forgetRewardPayment(drawId);
        return true;
    }
    private void recoverAccounts() {
        int recovered = 0;
        for (UUID player : ledger.recoverableClaims()) {
            try { if (recoverAccount(player)) recovered++; }
            catch (Exception ex) { plugin.getLogger().warning("Account reward recovery deferred for " + player + ": " + ex.getMessage()); }
        }
        if (recovered > 0) plugin.getLogger().info("Recovered " + recovered + " interrupted account crate rewards.");
    }
    private int keyAll(String type, int amount, Long next) throws Exception {
        List<UUID> players = Bukkit.getOnlinePlayers().stream().map(Player::getUniqueId).toList();
        ledger.grant(players, type, amount, next);
        for (Player player : Bukkit.getOnlinePlayers()) plugin.msg(player, Lang.text("crate.key-all-you-received-keys", "&bKey-all! &fYou received {0} {1} keys.", amount, Lang.label("labels", type, type)));
        return players.size();
    }
    private void tick() {
        if (!accountMode() || !plugin.getConfig().getBoolean("crate-system.keyall.enabled", false)) return;
        if (System.currentTimeMillis() < retryKeyAllAfter) return;
        try {
            long interval = Math.max(60, Math.min(604800, plugin.getConfig().getLong("crate-system.keyall.interval-seconds", 3600))) * 1000;
            long now = System.currentTimeMillis();
            if (ledger.nextKeyAll() == 0) { ledger.schedule(now + interval); return; }
            if (now < ledger.nextKeyAll()) return;
            String type = plugin.getConfig().getString("crate-system.keyall.type", "common");
            int amount = amount(String.valueOf(plugin.getConfig().getInt("crate-system.keyall.amount", 1)));
            if (!known(type)) throw new IllegalArgumentException("Unknown scheduled key-all crate");
            keyAll(type, amount, now + interval);
        } catch (Exception ex) {
            retryKeyAllAfter = System.currentTimeMillis() + 60000;
            plugin.getLogger().warning("Scheduled key-all could not run: " + ex.getMessage());
        }
    }
    private void failure(CommandSender sender, Exception ex) {
        plugin.getLogger().warning("Crate operation failed: " + ex.getMessage());
        plugin.msg(sender, Lang.text("crate.could-not-complete-the-crate-operation-your-saved-choice-may-need", "&cCould not complete the crate operation. Your saved choice may need staff review; check the server log."));
    }
}


===== src/main/java/com/donsup/crates/KeyLedger.java =====

package com.donsup.crates;

import com.donsup.config.Lang;

import com.donsup.util.SafeYaml;
import org.bukkit.configuration.file.YamlConfiguration;
import java.io.File;
import java.io.IOException;
import java.util.*;
import java.util.function.Consumer;

/** Key debit and its saved choices share one atomic file replacement. */
public final class KeyLedger {
    public static final long MAX_KEYS = 1_000_000_000L;
    private final File file;
    private YamlConfiguration data;
    public KeyLedger(File file) { this.file = file; data = SafeYaml.load(file); }
    public static boolean validType(String type) { return type != null && type.matches("[a-z0-9_-]{1,48}"); }
    private String root(UUID player) { return "players." + player; }
    public long balance(UUID player, String type) { return data.getLong(root(player) + ".keys." + type); }
    public long nextKeyAll() { return data.getLong("next-keyall"); }
    public Map<String, Object> pending(UUID player) {
        var section = data.getConfigurationSection(root(player) + ".pending");
        return section == null ? Map.of() : Collections.unmodifiableMap(section.getValues(false));
    }
    public void grant(Collection<UUID> players, String type, long amount) throws IOException {
        grant(players, type, amount, null);
    }
    public void grant(Collection<UUID> players, String type, long amount, Long nextKeyAll) throws IOException {
        if (!validType(type) || amount < 1 || amount > MAX_KEYS) throw new IllegalArgumentException(Lang.text("key-ledger.invalid-key-type-or-amount", "Invalid key type or amount"));
        Set<UUID> unique = new HashSet<>(players);
        for (UUID id : unique) if (balance(id, type) > MAX_KEYS - amount) throw new IllegalArgumentException(Lang.text("key-ledger.key-balance-limit-reached", "Key balance limit reached"));
        update(copy -> {
            for (UUID id : unique) copy.set(root(id) + ".keys." + type, balance(id, type) + amount);
            if (nextKeyAll != null) copy.set("next-keyall", nextKeyAll);
        });
    }
    public void schedule(long next) throws IOException { update(copy -> copy.set("next-keyall", next)); }
    public boolean open(UUID player, String type, List<Map<String, Object>> choices) throws IOException {
        if (!validType(type) || choices.isEmpty() || choices.size() > 7 || !pending(player).isEmpty() || balance(player, type) < 1) return false;
        update(copy -> {
            copy.set(root(player) + ".keys." + type, balance(player, type) - 1);
            String path = root(player) + ".pending";
            copy.set(path + ".id", UUID.randomUUID().toString());
            copy.set(path + ".type", type);
            copy.set(path + ".state", "choice");
            copy.set(path + ".choices", choices);
        });
        return true;
    }
    public boolean beginClaim(UUID player, String id, int index) throws IOException {
        Map<String, Object> pending = pending(player);
        if (!id.equals(pending.get("id")) || !"choice".equals(pending.get("state"))) return false;
        Object raw = pending.get("choices");
        if (!(raw instanceof List<?> choices) || index < 0 || index >= choices.size()) return false;
        update(copy -> {
            copy.set(root(player) + ".pending.state", "claiming");
            copy.set(root(player) + ".pending.selected", index);
            copy.set(root(player) + ".pending.recovery-version", 1);
        });
        return true;
    }
    public List<UUID> recoverableClaims() {
        var players = data.getConfigurationSection("players");
        if (players == null) return List.of();
        return players.getKeys(false).stream().map(UUID::fromString).filter(id -> !accountReward(id).isEmpty()).toList();
    }
    /** Legacy ambiguous claims and item deliveries deliberately require staff review. */
    public Map<?, ?> accountReward(UUID player) {
        var pending = pending(player);
        if (!"claiming".equals(pending.get("state")) || !(pending.get("recovery-version") instanceof Number version) || version.intValue() != 1) return Map.of();
        if (!(pending.get("selected") instanceof Number index) || !(pending.get("choices") instanceof List<?> choices)
                || index.intValue() < 0 || index.intValue() >= choices.size() || !(choices.get(index.intValue()) instanceof Map<?, ?> reward)
                || reward.containsKey("item")) return Map.of();
        return reward;
    }
    /** Key reward and claim completion share the same replacement; there is no replay window. */
    public boolean finishAccountReward(UUID player, String drawId) throws IOException {
        Map<?, ?> reward = accountReward(player);
        if (reward.isEmpty() || !drawId.equals(pending(player).get("id"))) return false;
        String type = (String)reward.get("key-type");
        long amount = reward.get("key-amount") instanceof Number n ? n.longValue() : 0;
        if (type != null && (!validType(type) || amount < 1 || amount > MAX_KEYS || balance(player, type) > MAX_KEYS - amount))
            throw new IllegalArgumentException(Lang.text("key-ledger.key-reward-would-exceed-the-account-limit", "Key reward would exceed the account limit"));
        update(copy -> {
            if (type != null) copy.set(root(player) + ".keys." + type, balance(player, type) + amount);
            copy.set(root(player) + ".pending", null);
        });
        return true;
    }
    public boolean finish(UUID player, String id) throws IOException {
        Map<String, Object> pending = pending(player);
        if (!id.equals(pending.get("id")) || !"claiming".equals(pending.get("state"))) return false;
        update(copy -> copy.set(root(player) + ".pending", null));
        return true;
    }
    /** Explicit staff resolution only: uncertain deliveries never automatically repeat. */
    public boolean resolve(UUID player, boolean refund) throws IOException {
        Map<String, Object> pending = pending(player);
        if (!"claiming".equals(pending.get("state"))) return false;
        String type = String.valueOf(pending.get("type"));
        if (refund && balance(player, type) >= MAX_KEYS) throw new IllegalArgumentException(Lang.text("key-ledger.key-balance-limit-reached", "Key balance limit reached"));
        update(copy -> {
            if (refund) copy.set(root(player) + ".keys." + type, balance(player, type) + 1);
            copy.set(root(player) + ".pending", null);
        });
        return true;
    }
    private void update(Consumer<YamlConfiguration> mutation) throws IOException {
        YamlConfiguration copy = new YamlConfiguration();
        try { copy.loadFromString(data.saveToString()); }
        catch (Exception ex) { throw new IOException(Lang.text("key-ledger.cannot-snapshot-key-data", "Cannot snapshot key data"), ex); }
        mutation.accept(copy);
        SafeYaml.save(copy, file);
        data = copy; // A failed save must not change the live balance or pending draw.
    }
}


===== src/main/java/com/donsup/creator/CreatorManager.java =====

package com.donsup.creator;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.ItemUtil;
import com.donsup.util.Text;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.block.BlockFace;
import org.bukkit.block.Block;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.player.AsyncPlayerChatEvent;
import org.bukkit.event.player.PlayerCommandPreprocessEvent;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.event.player.PlayerItemHeldEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.ArrayList;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

public class CreatorManager implements Listener {
    private static final String ONE_CLICK_PRESET = "donutsmp-style";
    private final DonsupPlugin plugin;
    private final ItemKey actionKey;
    private final ItemKey cratePlacerKey;
    private final File file;
    private final Map<UUID, Prompt> prompts = new ConcurrentHashMap<>();
    private final Map<UUID, Entity> previews = new ConcurrentHashMap<>();
    private final Map<UUID, String> previewKeys = new ConcurrentHashMap<>();
    private FileConfiguration data;

    public CreatorManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.actionKey = new ItemKey(plugin, "creator_action");
        this.cratePlacerKey = new ItemKey(plugin, "crate_placer_type");
        this.file = new File(plugin.getDataFolder(), "creator.yml");
        reload();
        plugin.platform().globalTimer(this::decayDynamicPricing, 20L * 60L * 60L, 20L * 60L * 60L);
        long previewTicks = Math.max(2L, plugin.getConfig().getLong("creator.ghost-preview-ticks", 5L));
        plugin.platform().globalTimer(this::updateGhostPreviews, previewTicks, previewTicks);
    }

    public void reload() {
        this.data = com.donsup.util.SafeYaml.load(file);
    }

    public void save() {
        try {
            com.donsup.util.SafeYaml.save(data, file);
        } catch (IOException ex) {
            plugin.getLogger().warning("Could not save creator.yml: " + ex.getMessage());
        }
    }

    public void shutdown() {
        if (plugin.platform().folia()) { previews.clear(); previewKeys.clear(); return; }
        for (Entity display : previews.values()) {
            if (display != null && !display.isDead()) {
                display.remove();
            }
        }
        previews.clear();
        previewKeys.clear();
    }

    public void openHub(Player player) {
        if (!admin(player)) {
            return;
        }
        Inventory inv = inv("Hub", 6);
        fill(inv);
        inv.setItem(4, button(com.donsup.compat.Materials.COMMAND_BLOCK, Lang.text("creator.smp-creator-toolkit", "&6&lSMP Creator Toolkit"), List.of(
                Lang.text("creator.build-the-server-from-in-game", "&7Build the server from in-game."),
                Lang.text("creator.no-yaml-editing-required-for-common-tasks", "&7No YAML editing required for common tasks.")
        ), "NONE"));
        inv.setItem(10, button(Material.CHEST, Lang.text("creator.placeable-crates", "&aPlaceable Crates"), List.of(
                Lang.text("creator.create-crate-blocks-players-can-click", "&7Create crate blocks players can click."),
                Lang.text("creator.click-to-choose-a-crate-type", "&7Click to choose a crate type.")
        ), "OPEN:CRATES"));
        inv.setItem(11, button(Material.TRIPWIRE_HOOK, Lang.text("creator.keys", "&bKeys"), List.of(
                Lang.text("creator.give-keys-attached-to-a-crate-type", "&7Give keys attached to a crate type."),
                Lang.text("creator.click-to-choose-type-and-amount", "&7Click to choose type and amount.")
        ), "OPEN:KEYS"));
        inv.setItem(12, button(Material.EMERALD, Lang.text("creator.shop-builder", "&aShop Builder"), List.of(
                Lang.text("creator.hold-an-item-and-add-it-to-a-shop", "&7Hold an item and add it to a shop."),
                Lang.text("creator.click-for-guided-setup", "&7Click for guided setup.")
        ), "OPEN:SHOPS"));
        inv.setItem(13, button(com.donsup.compat.Materials.COMPARATOR, Lang.text("creator.dynamic-pricing", "&eDynamic Pricing"), List.of(
                Lang.text("creator.status", "&7Status: {0}", (dynamicEnabled() ? Lang.text("creator.enabled", "&aEnabled") : Lang.text("creator.disabled", "&cDisabled"))),
                Lang.text("creator.supply-and-demand-can-move-server-prices", "&7Supply and demand can move server prices.")
        ), "OPEN:DYNAMIC"));
        inv.setItem(14, button(com.donsup.compat.Materials.SPAWNER, Lang.text("creator.spawner-setup", "&dSpawner Setup"), List.of(
                Lang.text("creator.configure-spawner-price-speed-and-drops", "&7Configure spawner price, speed and drops."),
                Lang.text("creator.give-test-spawners-from-the-gui", "&7Give test spawners from the GUI.")
        ), "OPEN:SPAWNER_SETUP"));
        inv.setItem(15, button(Material.BOOK, Lang.text("creator.preset-packs", "&fPreset Packs"), List.of(
                Lang.text("creator.apply-presets-from-a-gui", "&7Apply presets from a GUI."),
                Lang.text("creator.backups-are-made-automatically", "&7Backups are made automatically.")
        ), "OPEN:PRESETS"));
        inv.setItem(19, button(com.donsup.compat.Materials.LIME_DYE, Lang.text("creator.one-click-smp-setup", "&a&lOne-Click SMP Setup"), List.of(
                Lang.text("creator.apply-the-bundled-smp-config-and-shops", "&7Apply the bundled SMP config and shops."),
                Lang.text("creator.creates-backups-before-changing-files", "&7Creates backups before changing files."),
                Lang.text("creator.click-once-to-set-up-the-smp", "&aClick once to set up the SMP.")
        ), "ONE_CLICK_SETUP"));
        inv.setItem(21, button(Material.ENDER_PEARL, Lang.text("creator.command-teleports", "&bCommand Teleports"), List.of(
                Lang.text("creator.make-crates-or-custom-commands-teleport", "&7Make /crates or custom commands teleport."),
                Lang.text("creator.set-locations-from-this-gui", "&7Set locations from this GUI.")
        ), "OPEN:TELEPORTS"));
        inv.setItem(22, button(Material.MAP, Lang.text("creator.config-studio", "&bConfig Studio"), List.of(
                Lang.text("creator.edit-branding-menus-messages-and-gameplay-yaml", "&7Edit branding, menus, messages and gameplay YAML."),
                Lang.text("creator.click-for-file-paths-and-workflow", "&7Click for file paths and workflow.")
        ), "OPEN:CONFIG_STUDIO"));
        inv.setItem(23, button(Material.NETHER_STAR, Lang.text("creator.premium-setup", "&bPremium Setup"), List.of(
                Lang.text("creator.tune-premium-perks-from-a-gui", "&7Tune premium perks from a GUI."),
                Lang.text("creator.edit-values-toggles-and-kit-items", "&7Edit values, toggles and kit items.")
        ), "OPEN:PREMIUM_SETUP"));
        inv.setItem(24, button(com.donsup.compat.Materials.LIME_BANNER, Lang.text("creator.launch-checklist", "&aLaunch Checklist"), setupChecklistLore(), "OPEN:CHECKLIST"));
        inv.setItem(16, button(com.donsup.compat.Materials.REDSTONE_TORCH, Lang.text("creator.reload", "&cReload"), List.of(Lang.text("creator.reload-config-and-storage", "&7Reload config and storage.")), "RELOAD"));
        player.openInventory(inv);
    }

    public void openLaunchChecklist(Player player) {
        if (!admin(player)) {
            return;
        }
        Inventory inv = inv("Launch Checklist", 6);
        fill(inv);
        inv.setItem(4, button(com.donsup.compat.Materials.LIME_BANNER, Lang.text("creator.smp-launch-checklist", "&a&lSMP Launch Checklist"), List.of(
                Lang.text("creator.use-this-before-opening-the-server", "&7Use this before opening the server."),
                Lang.text("creator.green-means-ready-yellow-means-optional-setup", "&7Green means ready. Yellow means optional setup.")
        ), "NONE"));
        checklist(inv, 10, com.donsup.compat.Materials.LIME_DYE, Lang.text("creator.one-click-preset", "One-Click Preset"), plugin.getConfig().contains("branding.server-name"), "OPEN:PRESETS", Lang.text("creator.apply-a-full-economy-preset", "Apply a full economy preset."));
        checklist(inv, 11, Material.NAME_TAG, Lang.text("creator.branding", "Branding"), !plugin.serverName().equalsIgnoreCase("Your SMP"), "OPEN:CONFIG_STUDIO", Lang.text("creator.set-your-server-name-menu-title-and-chat-prefix", "Set your server name, menu title and chat prefix."));
        checklist(inv, 12, Material.EMERALD, Lang.text("creator.shop-categories", "Shop Categories"), sectionSize(plugin.shops(), "categories") > 0, "OPEN:SHOPS", Lang.text("creator.create-or-review-player-shop-categories", "Create or review player shop categories."));
        checklist(inv, 13, Material.TRIPWIRE_HOOK, Lang.text("creator.crate-rewards", "Crate Rewards"), sectionSize(plugin.getConfig(), "crates") > 0, "OPEN:CRATES", Lang.text("creator.review-crate-tiers-and-give-place-keys", "Review crate tiers and give/place keys."));
        checklist(inv, 14, com.donsup.compat.Materials.SPAWNER, Lang.text("creator.spawner-economy", "Spawner Economy"), sectionSize(plugin.getConfig(), "custom-spawners.types") > 0, "OPEN:SPAWNER_SETUP", Lang.text("creator.review-spawner-prices-drops-and-stack-scaling", "Review spawner prices, drops and stack scaling."));
        checklist(inv, 15, Material.CHEST, Lang.text("creator.placed-crates", "Placed Crates"), sectionSize(data, "crates") > 0, "OPEN:CRATES", Lang.text("creator.place-crate-blocks-at-spawn-or-crate-room", "Place crate blocks at spawn or crate room."));
        checklist(inv, 16, Material.ENDER_PEARL, Lang.text("creator.command-teleports-af9c9f", "Command Teleports"), sectionSize(data, "teleports.commands") > 0, "OPEN:TELEPORTS", Lang.text("creator.bind-commands-like-crates-to-physical-areas", "Bind commands like /crates to physical areas."));
        checklist(inv, 28, Material.NETHER_STAR, Lang.text("creator.premium-perks", "Premium Perks"), plugin.getConfig().contains("premium-kit"), "OPEN:PREMIUM_SETUP", Lang.text("creator.review-rank-perks-cooldowns-and-premium-kit", "Review rank perks, cooldowns and premium kit."));
        checklist(inv, 29, Material.MAP, Lang.text("creator.scoreboard-tablist", "Scoreboard/Tablist"), plugin.getConfig().getBoolean("branding.scoreboard.enabled", true), "OPEN:CONFIG_STUDIO", Lang.text("creator.built-in-scoreboard-and-tablist-branding-are-enabled", "Built-in scoreboard and tablist branding are enabled."));
        checklist(inv, 30, Material.DIAMOND_SWORD, Lang.text("creator.pvp-economy", "PvP Economy"), plugin.getConfig().getInt("settings.kill-shards", 0) > 0, "NONE", Lang.text("creator.kills-bounties-and-duels-are-configured", "Kills, bounties and duels are configured."));
        checklist(inv, 31, com.donsup.compat.Materials.SUNFLOWER, Lang.text("creator.retention-loops", "Retention Loops"), plugin.getConfig().contains("daily"), "NONE", Lang.text("creator.daily-rewards-kits-and-afk-shards-are-available", "Daily rewards, kits and AFK shards are available."));
        checklist(inv, 32, com.donsup.compat.Materials.SHIELD, Lang.text("creator.staff-tools", "Staff Tools"), true, "NONE", Lang.text("creator.reports-moderation-gui-and-staff-commands-are-registered", "Reports, moderation GUI and staff commands are registered."));
        inv.setItem(49, button(Material.ARROW, Lang.text("creator.back", "&7Back"), List.of(), "OPEN:HUB"));
        player.openInventory(inv);
    }

    public void openCrateTools(Player player) {
        if (!admin(player)) {
            return;
        }
        Inventory inv = inv("Crate Tools", 6);
        fill(inv);
        int slot = 10;
        var section = plugin.getConfig().getConfigurationSection("crates");
        if (section != null) {
            for (String crate : section.getKeys(false)) {
                Material icon = ItemUtil.material(section.getString(crate + ".icon"), Material.CHEST);
                inv.setItem(slot++, button(icon, section.getString(crate + ".display", "&b" + crate), List.of(
                        Lang.text("creator.click-get-placer-block", "&7Click: get placer block."),
                        Lang.text("creator.players-click-placed-crate-with-matching-key", "&7Players click placed crate with matching key.")
                ), "CRATE_WAND:" + crate));
            }
        }
        inv.setItem(49, button(Material.ARROW, Lang.text("creator.back", "&7Back"), List.of(), "OPEN:HUB"));
        player.openInventory(inv);
    }

    public void openKeyTools(Player player) {
        if (!admin(player)) {
            return;
        }
        Inventory inv = inv("Key Tools", 6);
        fill(inv);
        int slot = 10;
        var section = plugin.getConfig().getConfigurationSection("crates");
        if (section != null) {
            for (String crate : section.getKeys(false)) {
                Material icon = ItemUtil.material(section.getString(crate + ".icon"), Material.TRIPWIRE_HOOK);
                inv.setItem(slot++, button(icon, section.getString(crate + ".display", "&b" + crate), List.of(
                        Lang.text("creator.click-and-type-an-amount-in-chat", "&7Click and type an amount in chat."),
                        Lang.text("creator.keys-will-be-attached-to-this-crate-type", "&7Keys will be attached to this crate type.")
                ), "PROMPT_KEY:" + crate));
            }
        }
        inv.setItem(49, button(Material.ARROW, Lang.text("creator.back", "&7Back"), List.of(), "OPEN:HUB"));
        player.openInventory(inv);
    }

    public void openShopTools(Player player) {
        if (!admin(player)) {
            return;
        }
        Inventory inv = inv("Shop Builder", 6);
        fill(inv);
        inv.setItem(4, button(Material.EMERALD, Lang.text("creator.shop-builder-2e770e", "&a&lShop Builder"), List.of(
                Lang.text("creator.hold-the-item-you-want-to-sell", "&7Hold the item you want to sell."),
                Lang.text("creator.click-the-anvil-to-add-it-with-a-guided-prompt", "&7Click the anvil to add it with a guided prompt.")
        ), "NONE"));
        inv.setItem(8, button(Material.ANVIL, Lang.text("creator.add-held-item", "&aAdd Held Item"), List.of(
                Lang.text("creator.format-after-clicking", "&7Format after clicking:"),
                Lang.text("creator.category-id-buy-sell-amount", "&fcategory id buy sell amount"),
                Lang.text("creator.example-combat-pearls-480-18-16", "&8Example: combat pearls 480 18 16")
        ), "PROMPT_SHOP_ADD"));
        int slot = 10;
        var categories = plugin.shops().getConfigurationSection("categories");
        if (categories != null) {
            for (String category : categories.getKeys(false)) {
                Material icon = ItemUtil.material(categories.getString(category + ".icon"), Material.CHEST);
                inv.setItem(slot++, button(icon, categories.getString(category + ".name", "&a" + category), List.of(
                        Lang.text("creator.existing-category-id", "&7Existing category id: &f{0}", category),
                        Lang.text("creator.items", "&7Items: &e{0}", (categories.getConfigurationSection(category + ".items") == null ? 0 : categories.getConfigurationSection(category + ".items").getKeys(false).size())),
                        Lang.text("creator.click-to-edit-this-category", "&aClick to edit this category.")
                ), "SHOP_CATEGORY:" + category));
            }
        }
        inv.setItem(49, button(Material.ARROW, Lang.text("creator.back", "&7Back"), List.of(), "OPEN:HUB"));
        player.openInventory(inv);
    }

    public void openShopCategoryTools(Player player, String category) {
        if (!admin(player)) {
            return;
        }
        Inventory inv = inv("Shop " + category, 6);
        fill(inv);
        inv.setItem(4, button(Material.EMERALD, Lang.text("creator.text", "&a&l{0}", title(category)), List.of(
                Lang.text("creator.click-the-anvil-to-add-your-held-item-here", "&7Click the anvil to add your held item here."),
                Lang.text("creator.prompt-format-id-buy-sell-amount", "&7Prompt format: &fid buy sell amount")
        ), "NONE"));
        inv.setItem(8, button(Material.ANVIL, Lang.text("creator.add-held-item-here", "&aAdd Held Item Here"), List.of(
                Lang.text("creator.hold-item-click-then-type", "&7Hold item, click, then type:"),
                Lang.text("creator.id-buy-sell-amount", "&fid buy sell amount"),
                Lang.text("creator.example-pearls-480-18-16", "&8Example: pearls 480 18 16")
        ), "PROMPT_SHOP_ADD_CATEGORY:" + category));
        var items = plugin.shops().getConfigurationSection("categories." + category + ".items");
        int slot = 10;
        if (items != null) {
            for (String id : items.getKeys(false)) {
                Material material = ItemUtil.material(items.getString(id + ".material"), Material.STONE);
                inv.setItem(slot++, button(material, Lang.text("creator.text-5c01bc", "&f{0}", id), List.of(
                        Lang.text("creator.material", "&7Material: &e{0}", Lang.material(material)),
                        Lang.text("creator.amount", "&7Amount: &e{0}", items.getInt(id + ".amount", 1)),
                        Lang.text("creator.buy", "&7Buy: &a{0}", Text.money(items.getDouble(id + ".buy", 0))),
                        Lang.text("creator.sell", "&7Sell: &6{0}", Text.money(items.getDouble(id + ".sell", 0)))
                ), "NONE"));
                if (slot >= 45) {
                    break;
                }
            }
        }
        inv.setItem(49, button(Material.ARROW, Lang.text("creator.back", "&7Back"), List.of(), "OPEN:SHOPS"));
        player.openInventory(inv);
    }

    public void openPresetTools(Player player) { openPresetTools(player, 0); }

    private void openPresetTools(Player player, int requestedPage) {
        if (!admin(player)) return;
        List<String> presets = plugin.presets();
        int page = Math.max(0, Math.min(requestedPage, Math.max(0, (presets.size() - 1) / 28)));
        Inventory inv = inv("Presets", 6);
        fill(inv);
        inv.setItem(4, button(Material.BOOK, Lang.text("creator.smp-presets", "&f&lSMP Presets"), List.of(
                Lang.text("creator.choose-a-style-preview-changes-then-install", "&7Choose a style, preview changes, then install."),
                Lang.text("creator.automatic-backups-and-rollback-included", "&7Automatic backups and rollback included."),
                Lang.text("creator.page", "&7Page {0}", (page + 1))), "NONE"));
        for (int i = page * 28; i < Math.min(presets.size(), (page + 1) * 28); i++) {
            String id = presets.get(i);
            int local = i - page * 28;
            try {
                var profile = plugin.presetManager().profile(id);
                inv.setItem(10 + (local / 7) * 9 + local % 7, button(com.donsup.compat.Materials.WRITABLE_BOOK,
                        Lang.text("creator.text-0c9112", "&e{0}", profile.name()), List.of("&7" + profile.description(), Lang.text("creator.click-to-preview", "&aClick to preview")), "PREVIEW_PRESET:" + id));
            } catch (IOException ex) {
                inv.setItem(10 + (local / 7) * 9 + local % 7, button(Material.BARRIER, Lang.text("creator.text-83e4bb", "&c{0}", id),
                        List.of(Lang.text("creator.invalid-preset-manifest-check-preset-yml", "&7Invalid preset manifest; check preset.yml.")), "NONE"));
            }
        }
        if (page > 0) inv.setItem(45, button(Material.ARROW, Lang.text("creator.previous", "&ePrevious"), List.of(), "PRESET_PAGE:" + (page - 1)));
        if ((page + 1) * 28 < presets.size()) inv.setItem(53, button(Material.ARROW, Lang.text("creator.next", "&eNext"), List.of(), "PRESET_PAGE:" + (page + 1)));
        if (plugin.presetManager().hasAppliedPreset()) inv.setItem(48, button(com.donsup.compat.Materials.CLOCK, Lang.text("creator.undo-last-preset", "&6Undo last preset"),
                List.of(Lang.text("creator.preview-rollback-to-your-previous-settings", "&7Preview rollback to your previous settings.")), "PREVIEW_ROLLBACK"));
        inv.setItem(49, button(Material.ARROW, Lang.text("creator.back", "&7Back"), List.of(), "OPEN:HUB"));
        player.openInventory(inv);
    }

    private void previewPreset(Player player, String id) {
        if (!admin(player)) return;
        try {
            var preview = plugin.presetManager().preview(id);
            Inventory inv = inv("Preset Preview", 6);
            fill(inv);
            List<String> lore = new ArrayList<>();
            lore.add("&7" + preview.profile().description());
            lore.add(Lang.text("creator.settings-change", "&e{0} settings change", preview.changes().size()));
            preview.changes().stream().limit(12).forEach(key -> lore.add("&7" + key));
            lore.add(Lang.text("creator.player-data-is-preserved", "&7Player data is preserved."));
            lore.add(Lang.text("creator.your-current-config-and-shops-are-backed-up", "&7Your current config and shops are backed up."));
            inv.setItem(22, button(Material.BOOK, Lang.text("creator.text-5c01bc", "&f{0}", preview.profile().name()), lore, "NONE"));
            inv.setItem(39, button(preview.ready() ? com.donsup.compat.Materials.LIME_CONCRETE : Material.BARRIER,
                    preview.ready() ? Lang.text("creator.install-preset", "&aInstall preset") : Lang.text("creator.missing-required-plugins", "&cMissing required plugins"),
                    preview.ready() ? List.of(Lang.text("creator.click-to-apply-use-rollback-to-undo", "&7Click to apply. Use rollback to undo."))
                            : List.of("&7" + String.join(", ", preview.missingPlugins())),
                    preview.ready() ? "APPLY_PRESET:" + id : "NONE"));
            inv.setItem(41, button(com.donsup.compat.Materials.RED_CONCRETE, Lang.text("creator.cancel", "&cCancel"), List.of(), "OPEN:PRESETS"));
            player.openInventory(inv);
        } catch (IOException ex) {
            plugin.msg(player, Lang.text("creator.cannot-install-this-preset", "&cCannot install this preset: {0}", ex.getMessage()));
        }
    }

    public void openDynamicTools(Player player) {
        if (!admin(player)) {
            return;
        }
        Inventory inv = inv("Dynamic Market", 6);
        fill(inv);
        inv.setItem(4, button(com.donsup.compat.Materials.COMPARATOR, Lang.text("creator.dynamic-market", "&e&lDynamic Market"), List.of(
                Lang.text("creator.status", "&7Status: {0}", (dynamicEnabled() ? Lang.text("creator.enabled", "&aEnabled") : Lang.text("creator.disabled", "&cDisabled"))),
                Lang.text("creator.buy-pressure-raises-prices", "&7Buy pressure raises prices."),
                Lang.text("creator.sell-supply-lowers-prices", "&7Sell supply lowers prices.")
        ), "NONE"));
        inv.setItem(20, button(dynamicEnabled() ? com.donsup.compat.Materials.LIME_DYE : com.donsup.compat.Materials.GRAY_DYE, dynamicEnabled() ? Lang.text("creator.enabled", "&aEnabled") : Lang.text("creator.disabled", "&cDisabled"), List.of(Lang.text("creator.click-to-toggle", "&7Click to toggle.")), "TOGGLE:DYNAMIC"));
        inv.setItem(22, button(com.donsup.compat.Materials.CLOCK, Lang.text("creator.decay", "&eDecay"), List.of(Lang.text("creator.hourly-decay", "&7Hourly decay: &e{0}%", plugin.getConfig().getDouble("dynamic-pricing.decay-percent-per-hour", 8.0)), Lang.text("creator.edit-exact-values-in-config-studio", "&7Edit exact values in Config Studio.")), "NONE"));
        inv.setItem(24, button(Material.GOLD_INGOT, Lang.text("creator.limits", "&6Limits"), List.of(Lang.text("creator.min-x", "&7Min: &e{0}x", plugin.getConfig().getDouble("dynamic-pricing.min-multiplier", 0.5)), Lang.text("creator.max-x", "&7Max: &e{0}x", plugin.getConfig().getDouble("dynamic-pricing.max-multiplier", 2.5))), "NONE"));
        inv.setItem(49, button(Material.ARROW, Lang.text("creator.back", "&7Back"), List.of(), "OPEN:HUB"));
        player.openInventory(inv);
    }

    public void openPremiumSetup(Player player) {
        if (!admin(player)) {
            return;
        }
        Inventory inv = inv("Premium Setup", 6);
        fill(inv);
        inv.setItem(4, button(Material.NETHER_STAR, Lang.text("creator.premium-setup-83a5e8", "&b&lPremium Setup"), List.of(
                Lang.text("creator.click-values-to-edit-them-in-chat", "&7Click values to edit them in chat."),
                Lang.text("creator.click-toggles-to-enable-or-disable-features", "&7Click toggles to enable or disable features."),
                Lang.text("creator.kit-items-are-read-from-config-yml-premium-kit", "&7Kit items are read from config.yml premium-kit.")
        ), "NONE"));

        number(inv, 10, com.donsup.compat.Materials.RED_BED, Lang.text("creator.bonus-homes", "Bonus Homes"), "settings.premium-home-bonus", Lang.text("creator.extra-homes", "extra homes"));
        number(inv, 11, Material.GOLD_NUGGET, Lang.text("creator.listing-tax", "Listing Tax"), "settings.premium-listing-tax-percent", "%");
        number(inv, 12, Material.CHEST, Lang.text("creator.listing-bonus", "Listing Bonus"), "settings.premium-listing-bonus", Lang.text("creator.extra-listings", "extra listings"));
        number(inv, 13, Material.EMERALD, Lang.text("creator.sell-multiplier", "Sell Multiplier"), "settings.premium-sell-multiplier", Lang.text("creator.x", "x"));
        number(inv, 14, com.donsup.compat.Materials.AMETHYST_SHARD, Lang.text("creator.online-shards", "Online Shards"), "settings.premium-online-shards-per-minute", Lang.text("creator.shards-min", "shards/min"));
        number(inv, 15, com.donsup.compat.Materials.EXPERIENCE_BOTTLE, Lang.text("creator.shard-interest", "Shard Interest"), "settings.premium-shard-interest", Lang.text("creator.per-minute", "per minute"));
        number(inv, 16, com.donsup.compat.Materials.AMETHYST_CLUSTER, Lang.text("creator.interest-cap", "Interest Cap"), "settings.premium-shard-interest-cap", Lang.text("creator.shards", "shards"));
        number(inv, 19, Material.ENDER_CHEST, Lang.text("creator.vault-rows", "Vault Rows"), "settings.premium-vault-rows", Lang.text("creator.rows", "rows"));
        number(inv, 20, Material.DIAMOND, Lang.text("creator.kit-cooldown", "Kit Cooldown"), "settings.premium-kit-cooldown-hours", Lang.text("creator.hours", "hours"));
        number(inv, 21, Material.ANVIL, Lang.text("creator.repair-cooldown", "Repair Cooldown"), "settings.premium-repair-cooldown-minutes", Lang.text("creator.minutes", "minutes"));
        number(inv, 22, Material.COOKED_BEEF, Lang.text("creator.feed-cooldown", "Feed Cooldown"), "settings.premium-feed-cooldown-minutes", Lang.text("creator.minutes", "minutes"));

        toggle(inv, 24, com.donsup.compat.Materials.CRAFTING_TABLE, Lang.text("creator.portable-workbench", "Portable Workbench"), "settings.premium-portable-workbench");
        toggle(inv, 25, com.donsup.compat.Materials.SPYGLASS, Lang.text("creator.market-alerts", "Market Alerts"), "settings.premium-market-alerts");
        toggle(inv, 28, com.donsup.compat.Materials.TARGET, Lang.text("creator.bounty-radar", "Bounty Radar"), "settings.premium-bounty-radar");
        toggle(inv, 29, Material.POTION, Lang.text("creator.night-vision", "Night Vision"), "settings.premium-night-vision");

        inv.setItem(34, button(Material.ANVIL, Lang.text("creator.add-held-item-to-kit", "&aAdd Held Item To Kit"), List.of(
                Lang.text("creator.hold-an-item-click-then-type-amount", "&7Hold an item, click, then type amount."),
                Lang.text("creator.existing-material-entries-are-replaced", "&7Existing material entries are replaced.")
        ), "PROMPT_PREMIUM_KIT_ADD"));

        int slot = 37;
        var kit = plugin.getConfig().getConfigurationSection("premium-kit");
        if (kit != null) {
            for (String materialName : kit.getKeys(false)) {
                Material material = ItemUtil.material(materialName, Material.CHEST);
                inv.setItem(slot++, button(material, Lang.text("creator.text-5c01bc", "&f{0}", Lang.materialName(materialName)), List.of(
                        Lang.text("creator.amount", "&7Amount: &e{0}", kit.getInt(materialName, 1)),
                        Lang.text("creator.right-click-remove-from-kit", "&eRight click: remove from kit")
                ), "PREMIUM_KIT_ITEM:" + materialName));
                if (slot >= 45) {
                    break;
                }
            }
        }
        inv.setItem(49, button(Material.ARROW, Lang.text("creator.back", "&7Back"), List.of(), "OPEN:HUB"));
        player.openInventory(inv);
    }

    public void openSpawnerSetup(Player player) {
        if (!admin(player)) {
            return;
        }
        Inventory inv = inv("Spawner Setup", 6);
        fill(inv);
        inv.setItem(4, button(com.donsup.compat.Materials.SPAWNER, Lang.text("creator.spawner-setup-515e4c", "&d&lSpawner Setup"), List.of(
                Lang.text("creator.tune-custom-spawners-from-in-game", "&7Tune custom spawners from in-game."),
                Lang.text("creator.left-click-a-type-to-get-one", "&7Left-click a type to get one."),
                Lang.text("creator.right-click-a-type-to-add-the-held-item-as-a-drop", "&7Right-click a type to add the held item as a drop.")
        ), "NONE"));
        number(inv, 10, com.donsup.compat.Materials.AMETHYST_SHARD, Lang.text("creator.spawner-price", "Spawner Price"), "custom-spawners.price-shards", Lang.text("creator.shards", "shards"));
        number(inv, 11, com.donsup.compat.Materials.CLOCK, Lang.text("creator.drop-interval", "Drop Interval"), "custom-spawners.drop-generation-seconds", Lang.text("creator.seconds", "seconds"));
        number(inv, 12, com.donsup.compat.Materials.COMPARATOR, Lang.text("creator.stack-scaling", "Stack Scaling"), "custom-spawners.stack-scaling-exponent", Lang.text("creator.exponent", "exponent"));
        toggle(inv, 13, Material.SLIME_BALL, Lang.text("creator.sneak-to-stack", "Sneak To Stack"), "custom-spawners.stack-requires-sneak");
        toggle(inv, 14, Material.BEACON, Lang.text("creator.smp-stack-curve", "SMP Stack Curve"), "custom-spawners.donut-style-curve.enabled");
        number(inv, 15, Material.NETHER_STAR, Lang.text("creator.curve-cap", "Curve Cap"), "custom-spawners.donut-style-curve.asymptote", Lang.text("creator.items-min-cap", "items/min cap"));

        int slot = 19;
        var types = plugin.getConfig().getConfigurationSection("custom-spawners.types");
        if (types != null) {
            for (String type : types.getKeys(false)) {
                Material icon = ItemUtil.material(types.getString(type + ".icon"), com.donsup.compat.Materials.SPAWNER);
                inv.setItem(slot++, button(icon, types.getString(type + ".name", "&d" + title(type)), List.of(
                        Lang.text("creator.entity", "&7Entity: &e{0}", types.getString(type + ".entity", "PIG")),
                        Lang.text("creator.drops", "&7Drops: &f{0}", spawnerDrops(type)),
                        Lang.text("creator.left-click-give-one", "&aLeft click: give one"),
                        Lang.text("creator.right-click-add-held-item-as-drop", "&eRight click: add held item as drop")
                ), "SPAWNER_TYPE:" + type));
                if (slot >= 45) break;
            }
        }
        inv.setItem(49, button(Material.ARROW, Lang.text("creator.back", "&7Back"), List.of(), "OPEN:HUB"));
        player.openInventory(inv);
    }

    public void openConfigStudio(Player player) {
        if (!admin(player)) {
            return;
        }
        Inventory inv = inv("Config Studio", 6);
        fill(inv);
        inv.setItem(4, button(Material.MAP, Lang.text("creator.config-studio-0a8581", "&b&lConfig Studio"), List.of(
                Lang.text("creator.for-advanced-editing-use-the-web-editor", "&7For advanced editing, use the web editor:"),
                "&f" + new File(plugin.getDataFolder().getParentFile().getParentFile(), "config-editor.html").getPath(),
                Lang.text("creator.edit-generated-yaml-then-paste-save-into-plugin-configs", "&7Edit generated YAML, then paste/save into plugin configs.")
        ), "NONE"));
        inv.setItem(20, button(Material.PAPER, Lang.text("creator.editable-files", "&fEditable Files"), List.of(
                Lang.text("creator.config-yml", "&7config.yml"),
                Lang.text("creator.menus-yml-and-messages-yml", "&7menus.yml and messages.yml"),
                Lang.text("creator.dialogs-yml", "&7dialogs.yml"),
                Lang.text("creator.shops-yml", "&7shops.yml"),
                Lang.text("creator.bundled-competitive-preset-config-yml", "&7Bundled competitive preset config.yml"),
                Lang.text("creator.bundled-competitive-preset-shops-yml", "&7Bundled competitive preset shops.yml"),
                Lang.text("creator.bundled-donutsmp-style-preset-files", "&7Bundled DonutSMP-style preset files")
        ), "NONE"));
        inv.setItem(22, button(Material.BOOK, Lang.text("creator.recommended-flow", "&eRecommended Flow"), List.of(
                Lang.text("creator.1-rename-smp-brand-your-server-name", "&71. Rename: /smp brand Your Server Name"),
                Lang.text("creator.2-use-config-studio-for-bulk-edits", "&72. Use Config Studio for bulk edits."),
                Lang.text("creator.3-click-reload-in-creator-hub", "&73. Click reload in Creator Hub.")
        ), "NONE"));
        inv.setItem(24, button(com.donsup.compat.Materials.REDSTONE_TORCH, Lang.text("creator.reload-after-editing", "&aReload After Editing"), List.of(Lang.text("creator.reload-config-and-storage", "&7Reload config and storage.")), "RELOAD"));
        inv.setItem(49, button(Material.ARROW, Lang.text("creator.back", "&7Back"), List.of(), "OPEN:HUB"));
        player.openInventory(inv);
    }

    public void openTeleportTools(Player player) {
        if (!admin(player)) {
            return;
        }
        Inventory inv = inv("Command Teleports", 6);
        fill(inv);
        inv.setItem(4, button(Material.ENDER_PEARL, Lang.text("creator.command-teleports-c3356d", "&b&lCommand Teleports"), List.of(
                Lang.text("creator.make-command-aliases-teleport-players", "&7Make command aliases teleport players."),
                Lang.text("creator.example-crates-can-go-to-your-crate-room", "&7Example: /crates can go to your crate room.")
        ), "NONE"));
        inv.setItem(10, button(Material.CHEST, Lang.text("creator.set-crates-here", "&aSet /crates Here"), List.of(
                Lang.text("creator.uses-your-current-location", "&7Uses your current location."),
                Lang.text("creator.players-running-crates-will-teleport-here", "&7Players running /crates will teleport here.")
        ), Lang.text("creator.set-route-crates", "SET_ROUTE:crates")));
        inv.setItem(11, button(com.donsup.compat.Materials.OAK_SIGN, Lang.text("creator.add-custom-command-here", "&aAdd Custom Command Here"), List.of(
                Lang.text("creator.uses-your-current-location", "&7Uses your current location."),
                Lang.text("creator.you-will-type-the-command-name-in-chat", "&7You will type the command name in chat."),
                Lang.text("creator.example-market-warps-keys", "&8Example: market, warps, keys")
        ), "PROMPT_ROUTE"));
        int slot = 19;
        var commands = data.getConfigurationSection("teleports.commands");
        if (commands != null) {
            for (String command : commands.getKeys(false)) {
                Location location = routeLocation(command);
                inv.setItem(slot++, button(Material.COMPASS, Lang.text("creator.text-891249", "&f/{0}", command), List.of(
                        Lang.text("creator.world", "&7World: &e{0}", (location == null || location.getWorld() == null ? Lang.text("creator.missing", "missing") : location.getWorld().getName())),
                        location == null ? Lang.text("creator.location-invalid", "&cLocation invalid") : Lang.text("creator.xyz", "&7XYZ: &e{0}, {1}, {2}", location.getBlockX(), location.getBlockY(), location.getBlockZ()),
                        Lang.text("creator.left-click-teleport-there", "&aLeft click: teleport there"),
                        Lang.text("creator.right-click-update-to-your-current-location", "&eRight click: update to your current location"),
                        Lang.text("creator.shift-right-click-delete-route", "&cShift-right click: delete route")
                ), "ROUTE:" + command));
                if (slot >= 45) {
                    break;
                }
            }
        }
        inv.setItem(49, button(Material.ARROW, Lang.text("creator.back", "&7Back"), List.of(), "OPEN:HUB"));
        player.openInventory(inv);
    }

    public void addShopItem(Player player, String category, String id, double buy, double sell, int amount) {
        if (!admin(player)) {
            return;
        }
        ItemStack held = com.donsup.compat.BukkitCompat.hand(player.getInventory());
        if (com.donsup.compat.BukkitCompat.air(held.getType())) {
            plugin.msg(player, Lang.text("creator.hold-the-item-you-want-to-add-to-the-shop", "&cHold the item you want to add to the shop."));
            return;
        }
        category = clean(category);
        id = clean(id);
        String categoryPath = "categories." + category;
        if (!plugin.shops().contains(categoryPath + ".name")) {
            plugin.shops().set(categoryPath + ".name", "&a" + title(category));
            plugin.shops().set(categoryPath + ".icon", plugin.getConfig().getString("creator.default-shop-category-icon", "CHEST"));
        }
        String itemPath = categoryPath + ".items." + id;
        plugin.shops().set(itemPath + ".material", held.getType().name());
        plugin.shops().set(itemPath + ".amount", Math.max(1, amount));
        plugin.shops().set(itemPath + ".buy", Math.max(0, buy));
        plugin.shops().set(itemPath + ".sell", Math.max(0, sell));
        plugin.saveShops();
        plugin.reloadAll();
        plugin.msg(player, Lang.text("creator.added-to-shop-as", "&aAdded &e{0} &ato shop &e{1}&a as &e{2}&a.", Lang.material(held.getType()), category, id));
    }

    public void startShopPrompt(Player player) {
        startShopPrompt(player, "");
    }

    public void startShopPrompt(Player player, String category) {
        if (!admin(player)) {
            return;
        }
        if (com.donsup.compat.BukkitCompat.air(com.donsup.compat.BukkitCompat.hand(player.getInventory()).getType())) {
            plugin.msg(player, Lang.text("creator.hold-the-item-you-want-to-add-before-starting-the-shop-builder", "&cHold the item you want to add before starting the shop builder."));
            return;
        }
        prompts.put(player.getUniqueId(), new Prompt(PromptType.SHOP_ADD, clean(category)));
        player.closeInventory();
        if (category == null || category.isBlank()) {
            plugin.msg(player, Lang.text("creator.type-shop-details-in-chat-category-id-buy-sell-amount", "&eType shop details in chat: &fcategory id buy sell amount"));
            plugin.msg(player, Lang.text("creator.example-combat-pearls-480-18-16-type-cancel-to-stop", "&7Example: &fcombat pearls 480 18 16 &8| type &ccancel &8to stop."));
        } else {
            plugin.msg(player, Lang.text("creator.type-item-details-for-id-buy-sell-amount", "&eType item details for &f{0}&e: &fid buy sell amount", clean(category)));
            plugin.msg(player, Lang.text("creator.example-pearls-480-18-16-type-cancel-to-stop", "&7Example: &fpearls 480 18 16 &8| type &ccancel &8to stop."));
        }
    }

    public void startKeyPrompt(Player player, String crateType) {
        if (!admin(player)) {
            return;
        }
        prompts.put(player.getUniqueId(), new Prompt(PromptType.KEY_AMOUNT, crateType));
        player.closeInventory();
        plugin.msg(player, Lang.text("creator.type-the-key-amount-for-crate-type-cancel-to-stop", "&eType the key amount for crate &f{0}&e. Type &ccancel &eto stop.", crateType));
    }

    public void startRoutePrompt(Player player) {
        if (!admin(player)) {
            return;
        }
        prompts.put(player.getUniqueId(), new Prompt(PromptType.ROUTE_COMMAND, ""));
        player.closeInventory();
        plugin.msg(player, Lang.text("creator.type-the-command-name-to-bind-to-your-current-location", "&eType the command name to bind to your current location."));
        plugin.msg(player, Lang.text("creator.example-crates-or-market-type-cancel-to-stop", "&7Example: &fcrates &8or &fmarket &8| type &ccancel &8to stop."));
    }

    public void startNumberPrompt(Player player, String path) {
        if (!admin(player)) {
            return;
        }
        prompts.put(player.getUniqueId(), new Prompt(PromptType.PREMIUM_NUMBER, path));
        player.closeInventory();
        plugin.msg(player, Lang.text("creator.type-the-new-value-for-type-cancel-to-stop", "&eType the new value for &f{0}&e. Type &ccancel &eto stop.", path));
        plugin.msg(player, Lang.text("creator.current", "&7Current: &f{0}", plugin.getConfig().get(path)));
    }

    public void startPremiumKitPrompt(Player player) {
        if (!admin(player)) {
            return;
        }
        ItemStack held = com.donsup.compat.BukkitCompat.hand(player.getInventory());
        if (held == null || com.donsup.compat.BukkitCompat.air(held.getType())) {
            plugin.msg(player, Lang.text("creator.hold-the-item-you-want-to-add-to-the-premium-kit", "&cHold the item you want to add to the premium kit."));
            openPremiumSetup(player);
            return;
        }
        prompts.put(player.getUniqueId(), new Prompt(PromptType.PREMIUM_KIT_AMOUNT, held.getType().name()));
        player.closeInventory();
        plugin.msg(player, Lang.text("creator.type-the-premium-kit-amount-for-type-cancel-to-stop", "&eType the premium kit amount for &f{0}&e. Type &ccancel &eto stop.", Lang.material(held.getType())));
    }

    public void startSpawnerDropPrompt(Player player, String type) {
        if (!admin(player)) {
            return;
        }
        ItemStack held = com.donsup.compat.BukkitCompat.hand(player.getInventory());
        if (held == null || com.donsup.compat.BukkitCompat.air(held.getType())) {
            plugin.msg(player, Lang.text("creator.hold-the-item-this-spawner-should-generate", "&cHold the item this spawner should generate."));
            openSpawnerSetup(player);
            return;
        }
        prompts.put(player.getUniqueId(), new Prompt(PromptType.SPAWNER_DROP_AMOUNT, clean(type) + ":" + held.getType().name()));
        player.closeInventory();
        plugin.msg(player, Lang.text("creator.type-drops-per-cycle-for-on-spawner", "&eType drops per cycle for &f{0} &eon spawner &f{1}&e.", Lang.material(held.getType()), clean(type)));
        plugin.msg(player, Lang.text("creator.type-cancel-to-stop", "&7Type &ccancel &7to stop."));
    }

    public void setRoute(Player player, String command) {
        command = cleanCommand(command);
        if (command.isBlank()) {
            plugin.msg(player, Lang.text("creator.invalid-command-name", "&cInvalid command name."));
            return;
        }
        Location loc = player.getLocation();
        String path = "teleports.commands." + command;
        data.set(path + ".world", loc.getWorld().getName());
        data.set(path + ".x", loc.getX());
        data.set(path + ".y", loc.getY());
        data.set(path + ".z", loc.getZ());
        data.set(path + ".yaw", loc.getYaw());
        data.set(path + ".pitch", loc.getPitch());
        data.set(path + ".display", "/" + command);
        save();
        plugin.msg(player, Lang.text("creator.command-now-teleports-to-your-current-location", "&aCommand &e/{0} &anow teleports to your current location.", command));
    }

    public void deleteRoute(Player player, String command) {
        command = cleanCommand(command);
        if (command.isBlank()) {
            plugin.msg(player, Lang.text("creator.invalid-command-name", "&cInvalid command name."));
            return;
        }
        data.set("teleports.commands." + command, null);
        save();
        plugin.msg(player, Lang.text("creator.deleted-teleport-route", "&cDeleted teleport route &e/{0}&c.", command));
    }

    public boolean routeCommand(Player player, String command) {
        command = cleanCommand(command);
        Location location = routeLocation(command);
        if (location == null) {
            return false;
        }
        plugin.travel().teleport(player, location);
        plugin.msg(player, Lang.text("creator.teleported-to-destination", "&aTeleported to &e/{0}&a destination.", command));
        return true;
    }

    public ItemStack cratePlacer(String type) {
        type = clean(type);
        Material material = ItemUtil.material(plugin.getConfig().getString("crates." + type + ".icon"), Material.CHEST);
        ItemStack item = ItemUtil.named(material, 1, Lang.text("creator.crate-placer", "&6{0} Crate Placer", title(type)), List.of(
                Lang.text("creator.place-this-block-to-create-a-clickable-crate", "&7Place this block to create a clickable crate."),
                Lang.text("creator.crate-type", "&8Crate type: {0}", Lang.label("labels", type, type))
        ));
        ItemMeta meta = item.getItemMeta();
        com.donsup.compat.ItemTags.setString(meta, cratePlacerKey, type);
        item.setItemMeta(meta);
        return item;
    }

    public double dynamicPrice(Material material, double base) {
        if (!dynamicEnabled() || base <= 0) {
            return base;
        }
        double pressure = data.getDouble("pricing." + material.name() + ".pressure", 0.0);
        double min = plugin.getConfig().getDouble("dynamic-pricing.min-multiplier", 0.5);
        double max = plugin.getConfig().getDouble("dynamic-pricing.max-multiplier", 2.5);
        double multiplier = Math.max(min, Math.min(max, 1.0 + pressure));
        return Math.max(0.01, base * multiplier);
    }

    public void recordTrade(Material material, int amount, boolean boughtFromServer) {
        if (!dynamicEnabled() || amount <= 0) {
            return;
        }
        String path = "pricing." + material.name() + ".pressure";
        double impact = plugin.getConfig().getDouble(boughtFromServer ? "dynamic-pricing.buy-pressure-per-item" : "dynamic-pricing.sell-pressure-per-item", 0.002);
        double next = data.getDouble(path, 0.0) + (boughtFromServer ? impact * amount : -impact * amount);
        data.set(path, Math.max(-0.95, Math.min(5.0, next)));
        data.set("pricing." + material.name() + ".last-trade", System.currentTimeMillis());
        save();
    }

    public boolean dynamicEnabled() {
        return plugin.getConfig().getBoolean("dynamic-pricing.enabled", false);
    }

    public void setDynamicEnabled(boolean enabled) {
        plugin.getConfig().set("dynamic-pricing.enabled", enabled);
        plugin.saveConfig();
        plugin.reloadConfig();
    }

    @EventHandler
    public void onPlace(BlockPlaceEvent event) {
        String type = crateType(event.getItemInHand());
        if (type == null) {
            return;
        }
        removePreview(event.getPlayer());
        if (!admin(event.getPlayer())) {
            event.setCancelled(true);
            return;
        }
        if (!plugin.getConfig().getBoolean("creator.placeable-crates", true)) {
            plugin.msg(event.getPlayer(), Lang.text("creator.placeable-crates-are-disabled", "&cPlaceable crates are disabled."));
            event.setCancelled(true);
            return;
        }
        Block block = event.getBlockPlaced();
        data.set("crates." + key(block.getLocation()) + ".type", type);
        save();
        plugin.msg(event.getPlayer(), Lang.text("creator.placed-clickable-crate", "&aPlaced clickable crate &e{0}&a.", Lang.label("labels", type, type)));
    }

    @EventHandler
    public void onHeld(PlayerItemHeldEvent event) {
        plugin.platform().player(event.getPlayer(), () -> {
            if (crateType(com.donsup.compat.BukkitCompat.hand(event.getPlayer().getInventory())) == null) {
                removePreview(event.getPlayer());
            }
        });
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        removePreview(event.getPlayer());
        prompts.remove(event.getPlayer().getUniqueId());
    }

    public boolean isCrate(Block block) { return data.contains("crates." + key(block.getLocation()) + ".type"); }

    @EventHandler
    public void onInteract(PlayerInteractEvent event) {
        if (com.donsup.compat.BukkitCompat.offHand(event) || event.getClickedBlock() == null) {
            return;
        }
        String path = "crates." + key(event.getClickedBlock().getLocation());
        if (!data.contains(path + ".type")) {
            return;
        }
        event.setCancelled(true);
        String type = data.getString(path + ".type", "common");
        plugin.menus().openCrate(event.getPlayer(), type);
    }

    @EventHandler
    public void onBreak(BlockBreakEvent event) {
        String path = "crates." + key(event.getBlock().getLocation());
        if (!data.contains(path + ".type")) {
            return;
        }
        if (plugin.getConfig().getBoolean("creator.protect-placed-crates", true) && !admin(event.getPlayer())) {
            event.setCancelled(true);
            plugin.msg(event.getPlayer(), Lang.text("creator.this-crate-is-protected", "&cThis crate is protected."));
            return;
        }
        String type = data.getString(path + ".type", "common");
        data.set(path, null);
        save();
        if (admin(event.getPlayer())) {
            com.donsup.compat.BukkitCompat.drops(event, false);
            event.getPlayer().getInventory().addItem(cratePlacer(type));
            plugin.msg(event.getPlayer(), Lang.text("creator.removed-crate", "&aRemoved crate &e{0}&a.", Lang.label("labels", type, type)));
        }
    }

    @EventHandler
    public void onClick(InventoryClickEvent event) {
        if (!com.donsup.gui.OwnedInventory.buttonClick(event)) return;
        if (!(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        if (!com.donsup.gui.OwnedInventory.title(event.getView()).startsWith(titlePrefix())) {
            return;
        }
        event.setCancelled(true);
        if (!admin(player) || event.getClickedInventory() != com.donsup.compat.Views.top(event.getView())) return;
        ItemStack item = event.getCurrentItem();
        if (item == null || !item.hasItemMeta()) {
            return;
        }
        String action = com.donsup.compat.ItemTags.getString(item.getItemMeta(), actionKey);
        if (action == null) {
            return;
        }
        if (action.equals("OPEN:HUB")) {
            openHub(player);
        } else if (action.equals("OPEN:CRATES")) {
            openCrateTools(player);
        } else if (action.equals("OPEN:KEYS")) {
            openKeyTools(player);
        } else if (action.equals("OPEN:SHOPS")) {
            openShopTools(player);
        } else if (action.equals("OPEN:PRESETS")) {
            openPresetTools(player);
        } else if (action.equals("OPEN:CHECKLIST")) {
            openLaunchChecklist(player);
        } else if (action.equals("OPEN:DYNAMIC")) {
            openDynamicTools(player);
        } else if (action.equals("OPEN:CONFIG_STUDIO")) {
            openConfigStudio(player);
        } else if (action.equals("OPEN:TELEPORTS")) {
            openTeleportTools(player);
        } else if (action.equals("OPEN:PREMIUM_SETUP")) {
            openPremiumSetup(player);
        } else if (action.equals("OPEN:SPAWNER_SETUP")) {
            openSpawnerSetup(player);
        } else if (action.equals("ONE_CLICK_SETUP")) {
            applyOneClickSetup(player);
        } else if (action.equals("TOGGLE:DYNAMIC")) {
            setDynamicEnabled(!dynamicEnabled());
            plugin.msg(player, Lang.text("creator.dynamic-pricing-is-now", "&eDynamic pricing is now {0}&e.", (dynamicEnabled() ? Lang.text("creator.enabled-f8bd80", "&aenabled") : Lang.text("creator.disabled-381605", "&cdisabled"))));
            openDynamicTools(player);
        } else if (action.startsWith("TOGGLE_CONFIG:")) {
            toggleConfig(action.substring("TOGGLE_CONFIG:".length()));
            openPremiumSetup(player);
        } else if (action.startsWith("PROMPT_NUMBER:")) {
            startNumberPrompt(player, action.substring("PROMPT_NUMBER:".length()));
        } else if (action.equals("PROMPT_PREMIUM_KIT_ADD")) {
            startPremiumKitPrompt(player);
        } else if (action.startsWith("PREMIUM_KIT_ITEM:")) {
            if (event.isRightClick()) {
                removePremiumKitItem(player, action.substring("PREMIUM_KIT_ITEM:".length()));
            }
            openPremiumSetup(player);
        } else if (action.startsWith("SPAWNER_TYPE:")) {
            String type = action.substring("SPAWNER_TYPE:".length());
            if (event.isRightClick()) {
                startSpawnerDropPrompt(player, type);
            } else {
                player.getInventory().addItem(plugin.spawners().spawnerItem(type, 1));
                plugin.msg(player, Lang.text("creator.gave-spawner", "&aGave &e{0} Spawner&a.", title(type)));
                openSpawnerSetup(player);
            }
        } else if (action.equals("RELOAD")) {
            plugin.reloadAll();
            plugin.msg(player, Lang.text("creator.reloaded", "&aReloaded."));
            openHub(player);
        } else if (action.startsWith("CRATE_WAND:")) {
            player.getInventory().addItem(cratePlacer(action.substring("CRATE_WAND:".length())));
            plugin.msg(player, Lang.text("creator.gave-crate-placer", "&aGave crate placer."));
        } else if (action.startsWith("PROMPT_KEY:")) {
            startKeyPrompt(player, action.substring("PROMPT_KEY:".length()));
        } else if (action.equals("PROMPT_SHOP_ADD")) {
            startShopPrompt(player);
        } else if (action.startsWith("PROMPT_SHOP_ADD_CATEGORY:")) {
            startShopPrompt(player, action.substring("PROMPT_SHOP_ADD_CATEGORY:".length()));
        } else if (action.startsWith("SHOP_CATEGORY:")) {
            openShopCategoryTools(player, action.substring("SHOP_CATEGORY:".length()));
        } else if (action.equals("PROMPT_ROUTE")) {
            startRoutePrompt(player);
        } else if (action.startsWith("SET_ROUTE:")) {
            setRoute(player, action.substring("SET_ROUTE:".length()));
            openTeleportTools(player);
        } else if (action.startsWith("ROUTE:")) {
            String command = action.substring("ROUTE:".length());
            if (event.isRightClick() && event.isShiftClick()) {
                deleteRoute(player, command);
                openTeleportTools(player);
            } else if (event.isRightClick()) {
                setRoute(player, command);
                openTeleportTools(player);
            } else {
                routeCommand(player, command);
            }
        } else if (action.startsWith("PRESET_PAGE:")) {
            openPresetTools(player, Integer.parseInt(action.substring("PRESET_PAGE:".length())));
        } else if (action.startsWith("PREVIEW_PRESET:")) {
            previewPreset(player, action.substring("PREVIEW_PRESET:".length()));
        } else if (action.equals("PREVIEW_ROLLBACK")) {
            Inventory inv = inv("Rollback Preset", 3);
            fill(inv);
            inv.setItem(11, button(com.donsup.compat.Materials.LIME_CONCRETE, Lang.text("creator.restore-previous-settings", "&aRestore previous settings"),
                    List.of(Lang.text("creator.restores-config-and-shops-from-the-last-backup", "&7Restores config and shops from the last backup."), Lang.text("creator.player-data-is-preserved", "&7Player data is preserved.")), "ROLLBACK_PRESET"));
            inv.setItem(15, button(com.donsup.compat.Materials.RED_CONCRETE, Lang.text("creator.cancel", "&cCancel"), List.of(), "OPEN:PRESETS"));
            player.openInventory(inv);
        } else if (action.equals("ROLLBACK_PRESET")) {
            plugin.msg(player, plugin.rollbackPreset() ? Lang.text("creator.previous-settings-restored", "&aPrevious settings restored.")
                    : Lang.text("creator.rollback-failed", "&cRollback failed: {0}", plugin.presetError()));
            openPresetTools(player);
        } else if (action.startsWith("APPLY_PRESET:")) {
            String preset = action.substring("APPLY_PRESET:".length());
            if (plugin.applyPreset(preset)) {
                plugin.msg(player, Lang.text("creator.applied-preset-backups-were-created", "&aApplied preset &e{0}&a. Backups were created.", presetName(preset)));
            } else {
                plugin.msg(player, Lang.text("creator.could-not-apply-preset", "&cCould not apply preset: {0}", plugin.presetError()));
            }
            openPresetTools(player);
        }
    }

    @EventHandler
    public void onCommand(PlayerCommandPreprocessEvent event) {
        String raw = event.getMessage().substring(1).trim();
        if (raw.isBlank()) {
            return;
        }
        String command = raw.split("\\s+")[0];
        if (routeCommand(event.getPlayer(), command)) {
            event.setCancelled(true);
        }
    }

    @EventHandler
    public void onChat(AsyncPlayerChatEvent event) {
        Prompt prompt = prompts.remove(event.getPlayer().getUniqueId());
        if (prompt == null) {
            return;
        }
        event.setCancelled(true);
        String message = event.getMessage().trim();
        plugin.platform().player(event.getPlayer(), () -> handlePrompt(event.getPlayer(), prompt, message));
    }

    private void handlePrompt(Player player, Prompt prompt, String message) {
        if (message.equalsIgnoreCase("cancel")) {
            plugin.msg(player, Lang.text("creator.creator-prompt-cancelled", "&cCreator prompt cancelled."));
            openHub(player);
            return;
        }
        if (prompt.type == PromptType.KEY_AMOUNT) {
            int amount;
            try {
                amount = Math.max(1, Integer.parseInt(message));
            } catch (NumberFormatException ex) {
                plugin.msg(player, Lang.text("creator.that-was-not-a-valid-amount", "&cThat was not a valid amount."));
                startKeyPrompt(player, prompt.context);
                return;
            }
            if (plugin.crates().grant(player, prompt.context, amount))
                plugin.msg(player, Lang.text("creator.gave-x-crate-keys", "&aGave &e{0}x {1} &acrate keys.", amount, prompt.context));
            else plugin.msg(player, Lang.text("creator.could-not-grant-keys-check-the-type-amount-and-inventory-space", "&cCould not grant keys. Check the type, amount and inventory space."));
            openKeyTools(player);
            return;
        }
        if (prompt.type == PromptType.SHOP_ADD) {
            String[] parts = message.split("\\s+");
            try {
                if (prompt.context == null || prompt.context.isBlank()) {
                    if (parts.length < 5) {
                        plugin.msg(player, Lang.text("creator.use-category-id-buy-sell-amount", "&cUse: category id buy sell amount"));
                        startShopPrompt(player);
                        return;
                    }
                    addShopItem(player, parts[0], parts[1], Double.parseDouble(parts[2]), Double.parseDouble(parts[3]), Integer.parseInt(parts[4]));
                    openShopTools(player);
                } else {
                    if (parts.length < 4) {
                        plugin.msg(player, Lang.text("creator.use-id-buy-sell-amount", "&cUse: id buy sell amount"));
                        startShopPrompt(player, prompt.context);
                        return;
                    }
                    addShopItem(player, prompt.context, parts[0], Double.parseDouble(parts[1]), Double.parseDouble(parts[2]), Integer.parseInt(parts[3]));
                    openShopCategoryTools(player, prompt.context);
                }
            } catch (NumberFormatException ex) {
                plugin.msg(player, Lang.text("creator.buy-sell-and-amount-must-be-numbers", "&cBuy, sell and amount must be numbers."));
                startShopPrompt(player, prompt.context);
            }
            return;
        }
        if (prompt.type == PromptType.ROUTE_COMMAND) {
            setRoute(player, message);
            openTeleportTools(player);
            return;
        }
        if (prompt.type == PromptType.PREMIUM_NUMBER) {
            setPremiumNumber(player, prompt.context, message);
            openPremiumSetup(player);
            return;
        }
        if (prompt.type == PromptType.PREMIUM_KIT_AMOUNT) {
            addPremiumKitItem(player, prompt.context, message);
            openPremiumSetup(player);
            return;
        }
        if (prompt.type == PromptType.SPAWNER_DROP_AMOUNT) {
            addSpawnerDrop(player, prompt.context, message);
            openSpawnerSetup(player);
        }
    }

    private void applyOneClickSetup(Player player) {
        previewPreset(player, ONE_CLICK_PRESET);
    }

    private String presetName(String preset) {
        if (ONE_CLICK_PRESET.equalsIgnoreCase(preset)) {
            return Lang.text("creator.donutsmp-style", "DonutSMP Style");
        }
        if ("donut-style".equalsIgnoreCase(preset)) {
            return Lang.text("creator.competitive-smp", "Competitive SMP");
        }
        return title(preset.replace('-', ' '));
    }

    private void decayDynamicPricing() {
        if (!dynamicEnabled()) {
            return;
        }
        var section = data.getConfigurationSection("pricing");
        if (section == null) {
            return;
        }
        double decay = Math.max(0, Math.min(100, plugin.getConfig().getDouble("dynamic-pricing.decay-percent-per-hour", 8.0))) / 100D;
        for (String material : section.getKeys(false)) {
            double pressure = section.getDouble(material + ".pressure", 0.0);
            data.set("pricing." + material + ".pressure", pressure * (1D - decay));
        }
        save();
    }

    private void updateGhostPreviews() {
        if (!com.donsup.compat.BukkitCompat.displays()) return;
        if(plugin.platform().folia()){
            plugin.platform().eachPlayer(player -> {
                String type = crateType(com.donsup.compat.BukkitCompat.hand(player.getInventory()));
                if(!plugin.getConfig().getBoolean("creator.ghost-preview",true) || type==null || !player.hasPermission("donsup.admin")){removePreview(player);return;}
                Location target=previewLocation(player);
                if(target==null || !plugin.platform().owns(target)){removePreview(player);return;}
                showPreview(player,type,target);
            });
            return;
        }
        if (!plugin.getConfig().getBoolean("creator.ghost-preview", true)) {
            previews.keySet().forEach(uuid -> {
                Player player = Bukkit.getPlayer(uuid);
                if (player != null) {
                    removePreview(player);
                }
            });
            return;
        }
        for (Player player : Bukkit.getOnlinePlayers()) {
            String type = crateType(com.donsup.compat.BukkitCompat.hand(player.getInventory()));
            if (type == null || !player.hasPermission("donsup.admin")) {
                removePreview(player);
                continue;
            }
            Location target = previewLocation(player);
            if (target == null) {
                removePreview(player);
                continue;
            }
            showPreview(player, type, target);
        }
    }

    private Location previewLocation(Player player) {
        int range = Math.max(1, plugin.getConfig().getInt("creator.ghost-preview-range", 6));
        return com.donsup.compat.ModernVisuals.previewLocation(player, range);
    }

    private void showPreview(Player player, String type, Location location) {
        String key = type + "@" + key(location);
        Entity display = previews.get(player.getUniqueId());
        if (display != null && plugin.platform().owns(display) && !display.isDead() && key.equals(previewKeys.get(player.getUniqueId()))) {
            return;
        }
        removePreview(player);
        Material material = previewMaterial(type);
        Entity spawned = com.donsup.compat.ModernVisuals.preview(plugin, player, location, material, title(type));
        previews.put(player.getUniqueId(), spawned);
        previewKeys.put(player.getUniqueId(), key);
    }

    private Material previewMaterial(String type) {
        Material configured = ItemUtil.material(plugin.getConfig().getString("crates." + type + ".icon"), Material.CHEST);
        if (configured.isBlock()) {
            return configured;
        }
        return Material.CHEST;
    }

    private void removePreview(Player player) {
        Entity display = previews.remove(player.getUniqueId());
        previewKeys.remove(player.getUniqueId());
        if (display != null && !display.isDead()) {
            display.remove();
        }
    }

    private ItemStack button(Material material, String name, List<String> lore, String action) {
        return plugin.button(material, name, lore, actionKey, action);
    }

    private void checklist(Inventory inv, int slot, Material icon, String name, boolean ready, String action, String detail) {
        inv.setItem(slot, button(ready ? com.donsup.compat.Materials.LIME_DYE : icon, (ready ? Lang.text("creator.text-d2cb95", "&a") : Lang.text("creator.text-d05e90", "&e")) + name, List.of(
                ready ? Lang.text("creator.ready", "&aReady") : Lang.text("creator.needs-review", "&eNeeds review"),
                "&7" + detail,
                action.equals("NONE") ? Lang.text("creator.no-action-required", "&8No action required.") : Lang.text("creator.click-to-configure", "&aClick to configure.")
        ), action));
    }

    private List<String> setupChecklistLore() {
        int ready = 0;
        int total = 7;
        if (plugin.getConfig().contains("branding.server-name")) ready++;
        if (!plugin.serverName().equalsIgnoreCase("Your SMP")) ready++;
        if (sectionSize(plugin.shops(), "categories") > 0) ready++;
        if (sectionSize(plugin.getConfig(), "crates") > 0) ready++;
        if (sectionSize(plugin.getConfig(), "custom-spawners.types") > 0) ready++;
        if (sectionSize(data, "crates") > 0) ready++;
        if (sectionSize(data, "teleports.commands") > 0) ready++;
        return List.of(
                Lang.text("creator.progress", "&7Progress: &a{0}&7/&a{1}", ready, total),
                Lang.text("creator.check-branding-shops-crates-spawners", "&7Check branding, shops, crates, spawners,"),
                Lang.text("creator.placed-crate-blocks-and-command-teleports", "&7placed crate blocks and command teleports.")
        );
    }

    private int sectionSize(FileConfiguration config, String path) {
        var section = config.getConfigurationSection(path);
        return section == null ? 0 : section.getKeys(false).size();
    }

    private void number(Inventory inv, int slot, Material icon, String name, String path, String suffix) {
        Object value = plugin.getConfig().get(path);
        inv.setItem(slot, button(icon, Lang.text("creator.text-0c9112", "&e{0}", name), List.of(
                Lang.text("creator.current-f6e1d7", "&7Current: &f{0}{1}", value, (suffix.isBlank() ? "" : " " + suffix)),
                Lang.text("creator.click-to-edit", "&aClick to edit.")
        ), "PROMPT_NUMBER:" + path));
    }

    private void toggle(Inventory inv, int slot, Material icon, String name, String path) {
        boolean enabled = plugin.getConfig().getBoolean(path, true);
        inv.setItem(slot, button(enabled ? com.donsup.compat.Materials.LIME_DYE : com.donsup.compat.Materials.GRAY_DYE, (enabled ? Lang.text("creator.text-d2cb95", "&a") : Lang.text("creator.text-ef9d5f", "&c")) + name, List.of(
                Lang.text("creator.config", "&7Config: &f{0}", path),
                Lang.text("creator.status", "&7Status: {0}", (enabled ? Lang.text("creator.enabled", "&aEnabled") : Lang.text("creator.disabled", "&cDisabled"))),
                Lang.text("creator.click-to-toggle-4ce56f", "&aClick to toggle.")
        ), "TOGGLE_CONFIG:" + path));
    }

    private void toggleConfig(String path) {
        plugin.getConfig().set(path, !plugin.getConfig().getBoolean(path, true));
        plugin.saveConfig();
        plugin.reloadAll();
    }

    private void setPremiumNumber(Player player, String path, String input) {
        double value;
        try {
            value = Double.parseDouble(input);
        } catch (NumberFormatException ex) {
            plugin.msg(player, Lang.text("creator.that-was-not-a-valid-number", "&cThat was not a valid number."));
            startNumberPrompt(player, path);
            return;
        }
        value = Math.max(0, value);
        if (integerSetting(path)) {
            plugin.getConfig().set(path, (int) Math.round(value));
        } else {
            plugin.getConfig().set(path, value);
        }
        plugin.saveConfig();
        plugin.reloadAll();
        plugin.msg(player, Lang.text("creator.updated", "&aUpdated &e{0}&a.", path));
    }

    private boolean integerSetting(String path) {
        return path.endsWith("-bonus")
                || path.endsWith("-minute")
                || path.endsWith("-minutes")
                || path.endsWith("-hours")
                || path.endsWith("-rows")
                || path.endsWith("-cap")
                || path.endsWith("-listings")
                || path.endsWith("-seconds")
                || path.endsWith("-shards");
    }

    private void addPremiumKitItem(Player player, String materialName, String input) {
        int amount;
        try {
            amount = Math.max(1, Integer.parseInt(input));
        } catch (NumberFormatException ex) {
            plugin.msg(player, Lang.text("creator.that-was-not-a-valid-amount", "&cThat was not a valid amount."));
            startPremiumKitPrompt(player);
            return;
        }
        Material material = ItemUtil.material(materialName, Material.AIR);
        if (com.donsup.compat.BukkitCompat.air(material)) {
            plugin.msg(player, Lang.text("creator.invalid-kit-material", "&cInvalid kit material."));
            return;
        }
        plugin.getConfig().set("premium-kit." + material.name(), amount);
        plugin.saveConfig();
        plugin.reloadAll();
        plugin.msg(player, Lang.text("creator.added-x-to-the-premium-kit", "&aAdded &e{0}x {1} &ato the premium kit.", amount, Lang.material(material)));
    }

    private void removePremiumKitItem(Player player, String materialName) {
        materialName = clean(materialName).toUpperCase(Locale.ROOT);
        plugin.getConfig().set("premium-kit." + materialName, null);
        plugin.saveConfig();
        plugin.reloadAll();
        plugin.msg(player, Lang.text("creator.removed-from-the-premium-kit", "&cRemoved &e{0} &cfrom the premium kit.", Lang.materialName(materialName)));
    }

    private void addSpawnerDrop(Player player, String context, String input) {
        String[] parts = context.split(":", 2);
        if (parts.length < 2) {
            plugin.msg(player, Lang.text("creator.invalid-spawner-drop-prompt", "&cInvalid spawner drop prompt."));
            return;
        }
        int amount;
        try {
            amount = Math.max(1, Integer.parseInt(input));
        } catch (NumberFormatException ex) {
            plugin.msg(player, Lang.text("creator.that-was-not-a-valid-amount", "&cThat was not a valid amount."));
            startSpawnerDropPrompt(player, parts[0]);
            return;
        }
        String type = clean(parts[0]);
        Material material = ItemUtil.material(parts[1], Material.AIR);
        if (com.donsup.compat.BukkitCompat.air(material)) {
            plugin.msg(player, Lang.text("creator.invalid-drop-material", "&cInvalid drop material."));
            return;
        }
        plugin.getConfig().set("custom-spawners.types." + type + ".drops." + material.name(), amount);
        plugin.getConfig().set("custom-spawners.types." + type + ".icon", plugin.getConfig().getString("custom-spawners.types." + type + ".icon", material.name()));
        plugin.saveConfig();
        plugin.reloadAll();
        plugin.msg(player, Lang.text("creator.set-to-generate-x-per-cycle", "&aSet &e{0} &ato generate &e{1}x {2}&a per cycle.", title(type), amount, Lang.material(material)));
    }

    private String spawnerDrops(String type) {
        var drops = plugin.getConfig().getConfigurationSection("custom-spawners.types." + clean(type) + ".drops");
        if (drops == null || drops.getKeys(false).isEmpty()) {
            return Lang.text("creator.none", "none");
        }
        StringBuilder out = new StringBuilder();
        for (String material : drops.getKeys(false)) {
            if (!out.isEmpty()) out.append(", ");
            out.append(Lang.materialName(material)).append(" x").append(drops.getInt(material, 1));
        }
        return out.toString();
    }

    private Inventory inv(String name, int rows) {
        return plugin.inventory(rows * 9, titlePrefix() + name, false);
    }

    private String titlePrefix() {
        return "creator:";
    }

    private void fill(Inventory inv) {
        ItemStack glass = button(com.donsup.compat.Materials.GRAY_STAINED_GLASS_PANE, " ", List.of(), "NONE");
        for (int i = 0; i < inv.getSize(); i++) {
            inv.setItem(i, glass);
        }
    }

    private boolean admin(Player player) {
        if (!player.hasPermission("donsup.admin")) {
            plugin.msg(player, Lang.text("creator.creator-tools-require-donsup-admin", "&cCreator tools require &edonsup.admin&c."));
            return false;
        }
        return true;
    }

    private String crateType(ItemStack item) {
        if (item == null || com.donsup.compat.BukkitCompat.air(item.getType()) || !item.hasItemMeta()) {
            return null;
        }
        return com.donsup.compat.ItemTags.getString(item.getItemMeta(), cratePlacerKey);
    }

    private String key(Location location) {
        return location.getWorld().getName() + "," + location.getBlockX() + "," + location.getBlockY() + "," + location.getBlockZ();
    }

    private String clean(String input) {
        return input == null ? "default" : input.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9_-]", "");
    }

    private String cleanCommand(String input) {
        return input == null ? "" : input.toLowerCase(Locale.ROOT).replaceFirst("^/", "").replaceAll("[^a-z0-9:_-]", "");
    }

    private Location routeLocation(String command) {
        command = cleanCommand(command);
        String path = "teleports.commands." + command;
        String world = data.getString(path + ".world");
        if (world == null || Bukkit.getWorld(world) == null) {
            return null;
        }
        return new Location(
                Bukkit.getWorld(world),
                data.getDouble(path + ".x"),
                data.getDouble(path + ".y"),
                data.getDouble(path + ".z"),
                (float) data.getDouble(path + ".yaw"),
                (float) data.getDouble(path + ".pitch")
        );
    }

    private String title(String key) {
        String lower = clean(key).replace('_', ' ').replace('-', ' ');
        StringBuilder out = new StringBuilder();
        boolean cap = true;
        for (char c : lower.toCharArray()) {
            if (cap && Character.isLetter(c)) {
                out.append(Character.toUpperCase(c));
                cap = false;
            } else {
                out.append(c);
            }
            if (c == ' ') {
                cap = true;
            }
        }
        return Lang.label("labels", key, out.toString());
    }

    private enum PromptType {
        SHOP_ADD,
        KEY_AMOUNT,
        ROUTE_COMMAND,
        PREMIUM_NUMBER,
        PREMIUM_KIT_AMOUNT,
        SPAWNER_DROP_AMOUNT
    }

    private record Prompt(PromptType type, String context) {
    }
}


===== src/main/java/com/donsup/dialog/DonsupBootstrap.java =====

package com.donsup.dialog;

import io.papermc.paper.plugin.bootstrap.BootstrapContext;
import io.papermc.paper.plugin.bootstrap.PluginBootstrap;

/** Keep the base Paper loader linkable before the dialog APIs existed. */
public final class DonsupBootstrap implements PluginBootstrap {
    @Override public void bootstrap(BootstrapContext context) {
        if(com.donsup.compat.DialogCapabilities.available()) new DonsupNativeBootstrap().bootstrap(context);
    }
}


===== src/main/java/com/donsup/dialog/DonsupNativeBootstrap.java =====

package com.donsup.dialog;

import io.papermc.paper.plugin.bootstrap.BootstrapContext;
import io.papermc.paper.plugin.bootstrap.PluginBootstrap;
import io.papermc.paper.plugin.lifecycle.event.types.LifecycleEvents;
import io.papermc.paper.registry.RegistryKey;
import io.papermc.paper.registry.event.RegistryEvents;
import io.papermc.paper.registry.keys.DialogKeys;
import io.papermc.paper.registry.keys.tags.DialogTagKeys;
import io.papermc.paper.registry.data.dialog.*;
import io.papermc.paper.registry.data.dialog.action.DialogAction;
import io.papermc.paper.registry.data.dialog.type.DialogType;
import net.kyori.adventure.key.Key;
import net.kyori.adventure.text.Component;
import java.util.List;

/** Only public navigation is registered globally. All mutations use player-bound callbacks. */
public final class DonsupNativeBootstrap implements PluginBootstrap {
    @Override public void bootstrap(BootstrapContext context) {
        var menus = com.donsup.config.Customization.load(context.getDataDirectory());
        var config = com.donsup.config.Customization.read(context.getDataDirectory().resolve("config.yml"), "config.yml");
        String server = com.donsup.config.Branding.name(config);
        var key = DialogKeys.create(Key.key("donsup:menu"));
        context.getLifecycleManager().registerEventHandler(RegistryEvents.DIALOG.compose(), event ->
            event.registry().register(key, builder -> builder
                .base(DialogBase.builder(NativeText.component(menus.pause("title"), server))
                    .externalTitle(NativeText.component(menus.pause("external-title"), server))
                    .canCloseWithEscape(true).pause(false).build())
                .type(DialogType.multiAction(menus.pauseOrder().stream().map(route ->
                    button(menus.pause("labels." + route), route, menus.pauseWidth(), server)).toList())
                    .columns(1).exitAction(ActionButton.builder(NativeText.component(menus.pause("close-label"), server)).build()).build())));
        context.getLifecycleManager().registerEventHandler(LifecycleEvents.TAGS.postFlatten(RegistryKey.DIALOG), event -> {
            event.registrar().addToTag(DialogTagKeys.PAUSE_SCREEN_ADDITIONS, List.of(key));
            event.registrar().addToTag(DialogTagKeys.QUICK_ACTIONS, List.of(key));
        });
    }
    private ActionButton button(String label, String route, int width, String server) {
        return ActionButton.builder(NativeText.component(label, server)).width(width)
            .action(DialogAction.customClick(Key.key("donsup:open/" + route), null)).build();
    }
}


===== src/main/java/com/donsup/dialog/InventoryMenus.java =====

package com.donsup.dialog;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.market.*;
import com.donsup.util.*;
import org.bukkit.*;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.inventory.*;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.*;
import java.io.File;
import java.util.*;

/** Bukkit-only menu implementation: holder identity and one-use sessions authorize callbacks. */
public final class InventoryMenus implements PlayerMenus {
    private final DonsupPlugin plugin;
    private final Map<UUID,Screen> screens=new HashMap<>();
    private YamlConfiguration config;
    private static final List<String> CATEGORIES=List.of("chat","notifications","pvp","visuals","privacy","scoreboard");
    private static final class Screen implements InventoryHolder {
        final UUID owner;
        final Map<Integer,Runnable> actions=new HashMap<>();
        Inventory inventory;
        Screen(UUID owner){this.owner=owner;}
        public Inventory getInventory(){return inventory;}
    }
    public InventoryMenus(DonsupPlugin plugin){this.plugin=plugin;reload();}
    public void reload(){
        File file=new File(plugin.getDataFolder(),"dialogs.yml");
        if(!file.exists())plugin.saveResource("dialogs.yml",false);
        YamlConfiguration next=new YamlConfiguration();
        try{next.load(file);}catch(Exception ex){throw new IllegalArgumentException("Invalid dialogs.yml",ex);}
        for(String category:CATEGORIES)for(String setting:next.getStringList("categories."+category+".settings"))
            if(!com.donsup.features.ServerFeatures.SETTINGS.contains(setting))throw new IllegalArgumentException("Unknown setting: "+setting);
        config=next;screens.clear();
    }
    public void shutdown(){screens.clear();}
    private String plain(String text){return com.donsup.config.Branding.expand(plugin.customization().menuText(text).replaceAll("<[^>]*>",""),plugin.getConfig());}
    private Screen screen(Player player,String title){
        Screen s=new Screen(player.getUniqueId());
        s.inventory=Bukkit.createInventory(s,54,com.donsup.compat.BukkitCompat.inventoryTitle(plain(title)));return s;
    }
    private ItemStack item(Material material,String name,String... detail){
        ItemStack item=new ItemStack(material);var meta=item.getItemMeta();
        meta.setDisplayName(Text.color(Lang.text("inventory-menus.text", "&e{0}", plain(name))));
        meta.setLore(Arrays.stream(detail).flatMap(s->Arrays.stream(plain(s).split("\n"))).map(s->Text.color("&7"+s)).toList());
        item.setItemMeta(meta);return item;
    }
    private void button(Screen s,int slot,Material material,String label,Runnable action,String... detail){
        s.inventory.setItem(slot,item(material,label,detail));s.actions.put(slot,action);
    }
    private void display(Player p,Screen s){
        if(!p.hasPermission("donsup.use"))return;
        p.openInventory(s.inventory);screens.put(p.getUniqueId(),s);
    }
    private void back(Screen s,Player p){button(s,49,Material.ARROW,Lang.text("inventory-menus.back", "Back"),()->main(p));}
    private void command(Player p,String command){p.closeInventory();p.performCommand(command);}
    private void help(Player p,String message){p.closeInventory();plugin.msg(p,Lang.text("inventory-menus.text", "&e{0}", message));}
    @EventHandler(priority=EventPriority.HIGHEST) public void click(InventoryClickEvent e){
        if(!(com.donsup.compat.Views.top(e.getView()).getHolder() instanceof Screen s))return;
        e.setCancelled(true);
        if(!(e.getWhoClicked() instanceof Player p)||!p.getUniqueId().equals(s.owner)||screens.get(s.owner)!=s)return;
        Runnable action=s.actions.get(e.getRawSlot());
        if(action==null)return;
        screens.remove(s.owner);
        plugin.platform().player(p,()->{
            if(!p.isOnline()||!p.hasPermission("donsup.use")||com.donsup.compat.Views.top(p.getOpenInventory()).getHolder()!=s)return;
            p.closeInventory();action.run();
        });
    }
    @EventHandler(priority=EventPriority.HIGHEST) public void drag(InventoryDragEvent e){
        if(com.donsup.compat.Views.top(e.getView()).getHolder() instanceof Screen)e.setCancelled(true);
    }
    @EventHandler public void close(InventoryCloseEvent e){
        if(e.getInventory().getHolder() instanceof Screen s)screens.remove(s.owner,s);
    }
    @EventHandler public void quit(PlayerQuitEvent e){screens.remove(e.getPlayer().getUniqueId());}
    public void notice(Player p,String title,String message){
        Screen s=screen(p,title);s.inventory.setItem(22,item(Material.BOOK,title,message));back(s,p);display(p,s);
    }
    public void confirm(Player p,String title,String detail,Runnable yes,Runnable no){
        Screen s=screen(p,title);s.inventory.setItem(13,item(Material.BOOK,title,detail));
        button(s,30,com.donsup.compat.Materials.LIME_CONCRETE,Lang.text("inventory-menus.confirm", "Confirm"),yes);button(s,32,com.donsup.compat.Materials.RED_CONCRETE,Lang.text("inventory-menus.cancel", "Cancel"),no);display(p,s);
    }
    public void confirmItem(Player p,String title,ItemStack item,String detail,Runnable yes){
        Screen s=screen(p,title);s.inventory.setItem(13,item.clone());s.inventory.setItem(22,item(Material.PAPER,Lang.text("inventory-menus.transaction", "Transaction"),detail));
        button(s,30,com.donsup.compat.Materials.LIME_CONCRETE,Lang.text("inventory-menus.confirm", "Confirm"),yes);button(s,32,com.donsup.compat.Materials.RED_CONCRETE,Lang.text("inventory-menus.cancel", "Cancel"),p::closeInventory);display(p,s);
    }
    public void main(Player p){
        Screen s=new Screen(p.getUniqueId());
        s.inventory=Bukkit.createInventory(s,plugin.customization().rows()*9,com.donsup.compat.BukkitCompat.inventoryTitle(Text.color(plugin.serverName())));
        for(var entry:plugin.customization().buttons()) {
            if(!entry.visible(p))continue;
            button(s,entry.slot(),entry.icon(),entry.label(),()->{
                if(entry.visible(p))command(p,entry.command().replace("%player%",p.getName()));
            },entry.lore().toArray(String[]::new));
        }
        button(s,plugin.customization().closeSlot(),Material.BARRIER,Lang.text("inventory-menus.close", "Close"),p::closeInventory);
        display(p,s);
    }
    public void settings(Player p){
        Screen s=screen(p,config.getString("settings-title","Settings"));
        Material[] icons={com.donsup.compat.Materials.WRITABLE_BOOK,com.donsup.compat.Materials.BELL,Material.IRON_SWORD,com.donsup.compat.Materials.SPYGLASS,Material.IRON_DOOR,com.donsup.compat.Materials.OAK_SIGN};
        for(int i=0;i<CATEGORIES.size();i++){String c=CATEGORIES.get(i);button(s,19+i,icons[i],config.getString("categories."+c+".label",c),()->category(p,c),config.getString("categories."+c+".description",""));}
        back(s,p);display(p,s);
    }
    public void category(Player p,String category){
        if(!CATEGORIES.contains(category))return;
        Screen s=screen(p,config.getString("categories."+category+".label",category));int slot=10;
        var settingKeys=new ArrayList<>(config.getStringList("categories."+category+".settings"));
        if(category.equals("pvp")&&!settingKeys.contains("keep_pearls_on_death"))settingKeys.add("keep_pearls_on_death");
        for(String key:settingKeys){
            if(key.equals("keep_pearls_on_death")&&!plugin.pearls().supported())continue;
            boolean enabled=plugin.economy().setting(p.getUniqueId(),key);
            button(s,slot++,enabled?com.donsup.compat.Materials.LIME_DYE:com.donsup.compat.Materials.GRAY_DYE,config.getString("labels."+key,key),()->{
                if(key.equals("night_vision")&&!plugin.economy().premium(p)){plugin.msg(p,Lang.text("inventory-menus.night-vision-requires-premium", "&cNight vision requires premium."));category(p,category);return;}
                plugin.economy().setSettings(p.getUniqueId(),Map.of(key,!plugin.economy().setting(p.getUniqueId(),key)));
                plugin.menus().applyNightVision(p);category(p,category);
            },enabled?Lang.text("inventory-menus.enabled-click-to-disable", "Enabled - click to disable"):Lang.text("inventory-menus.disabled-click-to-enable", "Disabled - click to enable"));
        }
        button(s,49,Material.ARROW,Lang.text("inventory-menus.settings", "Settings"),()->settings(p));display(p,s);
    }
    public void profile(Player p,Player target){
        if(!p.equals(target)&&!plugin.economy().setting(target.getUniqueId(),"public_profile")){notice(p,Lang.text("inventory-menus.profile", "Profile"),Lang.text("inventory-menus.this-player-has-a-private-profile", "This player has a private profile."));return;}
        UUID id=target.getUniqueId();notice(p,target.getName(),Lang.text("inventory-menus.money-shards-kills-deaths", "Money: {0}\nShards: {1}\nKills: {2}\nDeaths: {3}", Text.money(plugin.economy().money(id)), plugin.economy().shards(id), plugin.economy().stat(id,"kills"), plugin.economy().stat(id,"deaths")));
    }
    public void homes(Player p){
        Screen s=screen(p,Lang.text("inventory-menus.homes", "Homes"));int slot=0;
        for(String name:plugin.economy().homeNames(p.getUniqueId()).stream().sorted().limit(45).toList()){
            button(s,slot++,com.donsup.compat.Materials.RED_BED,name,()->confirm(p,name,Lang.text("inventory-menus.teleport-to-this-home", "Teleport to this home?"),()->plugin.travel().teleport(p,plugin.economy().home(p.getUniqueId(),name)),()->homes(p)),Lang.text("inventory-menus.delete-with-delhome", "Delete with /delhome {0}", name));
        }
        button(s,45,com.donsup.compat.Materials.WRITABLE_BOOK,Lang.text("inventory-menus.set-a-home", "Set a home"),()->help(p,Lang.text("inventory-menus.sethome", "/sethome <name>")));back(s,p);display(p,s);
    }
    public void friends(Player p){
        Screen s=screen(p,Lang.text("inventory-menus.friends", "Friends"));int slot=0;
        for(UUID id:plugin.extensions().friends(p.getUniqueId()).stream().limit(36).toList())
            button(s,slot++,com.donsup.compat.Materials.PLAYER_HEAD,plugin.economy().playerName(id),()->confirm(p,Lang.text("inventory-menus.remove-friend", "Remove friend?"),Lang.text("inventory-menus.remove", "Remove {0}?", plugin.economy().playerName(id)),()->{plugin.extensions().removeFriend(p,id);friends(p);},()->friends(p)));
        for(Player from:plugin.extensions().friendRequests(p).stream().limit(9).toList())
            button(s,slot++,com.donsup.compat.Materials.LIME_DYE,Lang.text("inventory-menus.accept", "Accept {0}", from.getName()),()->{plugin.extensions().friend(p,new String[]{"accept",from.getName()});friends(p);});
        button(s,45,com.donsup.compat.Materials.WRITABLE_BOOK,Lang.text("inventory-menus.add-friend", "Add Friend"),()->help(p,Lang.text("inventory-menus.friend-add", "/friend add <player>")));back(s,p);display(p,s);
    }
    public void travel(Player p){
        Screen s=screen(p,Lang.text("inventory-menus.random-teleport", "Random Teleport"));
        String[] dims={"overworld","nether","end"};Material[] icons={com.donsup.compat.Materials.GRASS_BLOCK,Material.NETHERRACK,com.donsup.compat.Materials.END_STONE};
        for(int i=0;i<3;i++){String d=dims[i];button(s,11+i*2,icons[i],Lang.text("inventory-menus.solo", "{0} solo", Lang.label("dimensions", d, d)),()->command(p,"rtp "+d));button(s,29+i*2,icons[i],Lang.text("inventory-menus.paired-queue", "{0} paired queue", Lang.label("dimensions", d, d)),()->command(p,"rtp queue "+d));}
        button(s,47,Material.COMPASS,Lang.text("inventory-menus.regions-zones", "Regions / Zones"),()->plugin.zoneMenu().open(p,0));
        button(s,45,Material.PAPER,Lang.text("inventory-menus.queue-status", "Queue status"),()->notice(p,Lang.text("inventory-menus.rtp-status", "RTP Status"),plugin.travel().rtp().status(p)));
        button(s,53,Material.BARRIER,Lang.text("inventory-menus.leave-queue", "Leave queue"),()->command(p,"rtp leave"));back(s,p);display(p,s);
    }
    public void listings(Player p,String type,String search,int page,boolean mine){
        var all=(mine?plugin.market().ownedListings(p.getUniqueId(),type):plugin.market().listings(type)).stream()
            .filter(l->l.item().getType().name().toLowerCase(Locale.ROOT).contains(search.toLowerCase(Locale.ROOT)))
            .sorted(Comparator.comparingDouble(l->l.price()/l.item().getAmount())).toList();
        int index=Math.min(Math.max(page,0),Math.max(0,(all.size()-1)/36));
        Screen s=screen(p,Lang.text("inventory-menus.auction-house", "Auction House - {0}", (index+1)));int slot=0;
        for(var l:all.stream().skip(index*36L).limit(36).toList()){
            ItemStack shown=l.item().clone();var meta=shown.getItemMeta();var lore=meta.hasLore()?new ArrayList<>(meta.getLore()):new ArrayList<String>();
            lore.add(Text.color(Lang.text("inventory-menus.seller", "&a{0} &7Seller: {1}", Text.money(l.price()), l.ownerName())));meta.setLore(lore);shown.setItemMeta(meta);
            s.inventory.setItem(slot,shown);s.actions.put(slot++,()->listing(p,l,false,()->listings(p,type,search,index,mine)));
        }
        if(index>0)button(s,45,Material.ARROW,Lang.text("inventory-menus.previous", "Previous"),()->listings(p,type,search,index-1,mine));
        if((index+1)*36<all.size())button(s,53,Material.ARROW,Lang.text("inventory-menus.next", "Next"),()->listings(p,type,search,index+1,mine));
        button(s,46,Material.CHEST,mine?Lang.text("inventory-menus.all-listings", "All listings"):Lang.text("inventory-menus.my-listings-returns", "My listings / returns"),()->listings(p,type,"",0,!mine));
        button(s,47,com.donsup.compat.Materials.WRITABLE_BOOK,Lang.text("inventory-menus.list-held-item", "List held item"),()->help(p,Lang.text("inventory-menus.list", "/{0} list <price>", (type.equals("auction")?"ah":"market"))));
        back(s,p);display(p,s);
    }
    private void listing(Player p,MarketListing l,boolean quick,Runnable back){
        confirmItem(p,l.owner().equals(p.getUniqueId())?Lang.text("inventory-menus.reclaim-listing", "Reclaim Listing"):Lang.text("inventory-menus.buy-listing", "Buy Listing"),l.item(),Lang.text("inventory-menus.seller-total", "Seller: {0}\nTotal: {1}", l.ownerName(), Text.money(l.price())),()->{
            if(quick&&plugin.travel().tagged(p)){plugin.msg(p,Lang.text("inventory-menus.quick-buy-is-unavailable-during-combat", "&cQuick Buy is unavailable during combat."));return;}
            if(l.owner().equals(p.getUniqueId()))plugin.market().reclaim(p,l.id());else plugin.menus().buyListing(p,l.id());back.run();
        });
    }
    public void quickBuy(Player p,int page,ItemStack match){
        if(plugin.travel().tagged(p)){plugin.msg(p,Lang.text("inventory-menus.quick-buy-is-unavailable-during-combat", "&cQuick Buy is unavailable during combat."));return;}
        Map<Material,MarketListing> best=new LinkedHashMap<>();
        plugin.market().listings("auction").stream().filter(l->!l.owner().equals(p.getUniqueId()))
            .filter(l->match==null?!l.item().hasItemMeta():l.item().isSimilar(match))
            .sorted(Comparator.comparingDouble(l->l.price()/l.item().getAmount())).forEach(l->best.putIfAbsent(l.item().getType(),l));
        int index=Math.min(Math.max(page,0),Math.max(0,(best.size()-1)/36));Screen s=screen(p,Lang.text("inventory-menus.quick-buy", "Quick Buy - {0}", (index+1)));int slot=0;
        for(var l:best.values().stream().skip(index*36L).limit(36).toList()){
            button(s,slot++,l.item().getType(),l.item().getType().name(),()->listing(p,l,true,()->quickBuy(p,index,match)),Text.money(l.price()/l.item().getAmount())+"/item",Lang.text("inventory-menus.total-for", "{0} total for {1}", Text.money(l.price()), l.item().getAmount()));
        }
        if(index>0)button(s,45,Material.ARROW,Lang.text("inventory-menus.previous", "Previous"),()->quickBuy(p,index-1,match));
        if((index+1)*36<best.size())button(s,53,Material.ARROW,Lang.text("inventory-menus.next", "Next"),()->quickBuy(p,index+1,match));
        button(s,46,Material.HOPPER,Lang.text("inventory-menus.match-held-item", "Match held item"),()->{ItemStack held=com.donsup.compat.BukkitCompat.hand(p.getInventory());if(com.donsup.compat.BukkitCompat.air(held.getType()))notice(p,Lang.text("inventory-menus.quick-buy-a3fa2a", "Quick Buy"),Lang.text("inventory-menus.hold-an-item-first", "Hold an item first."));else quickBuy(p,0,held.clone());});
        button(s,47,Material.CHEST,Lang.text("inventory-menus.saved-favourites-loadouts", "Saved favourites / loadouts"),()->plugin.shopping().open(p,null));
        back(s,p);display(p,s);
    }
    public void orders(Player p,int page,boolean mine){
        var all=plugin.market().orders().stream().filter(o->!mine||o.owner().equals(p.getUniqueId())).sorted(Comparator.comparingDouble(BulkOrder::priceEach).reversed()).toList();
        int index=Math.min(Math.max(page,0),Math.max(0,(all.size()-1)/36));Screen s=screen(p,Lang.text("inventory-menus.orders", "Orders - {0}", (index+1)));int slot=0;
        for(var o:all.stream().skip(index*36L).limit(36).toList())button(s,slot++,o.material(),o.material().name()+(o.exact()?Lang.text("inventory-menus.exact", " (exact)"):""),
            ()->confirmItem(p,o.owner().equals(p.getUniqueId())?Lang.text("inventory-menus.close-and-claim", "Close and Claim"):Lang.text("inventory-menus.deliver-items", "Deliver Items"),o.item(),Lang.text("inventory-menus.remaining-price-each", "Remaining: {0}\nPrice each: {1}", o.remaining(), Text.money(o.priceEach())),()->{
                if(o.owner().equals(p.getUniqueId()))plugin.menus().claimOrder(p,o.id());else plugin.menus().deliverOrder(p,o.id());orders(p,index,mine);
            }),Lang.text("inventory-menus.buyer", "Buyer: {0}", o.ownerName()),Lang.text("inventory-menus.each", "{0} each", Text.money(o.priceEach())));
        if(index>0)button(s,45,Material.ARROW,Lang.text("inventory-menus.previous", "Previous"),()->orders(p,index-1,mine));
        if((index+1)*36<all.size())button(s,53,Material.ARROW,Lang.text("inventory-menus.next", "Next"),()->orders(p,index+1,mine));
        button(s,46,com.donsup.compat.Materials.WRITABLE_BOOK,Lang.text("inventory-menus.create-order", "Create order"),()->help(p,Lang.text("inventory-menus.orders-create", "/orders create <material> <amount> <priceEach>")));
        button(s,47,Material.HOPPER,Lang.text("inventory-menus.order-exact-held-item", "Order exact held item"),()->help(p,Lang.text("inventory-menus.orders-hand", "/orders hand <amount> <priceEach>")));
        button(s,48,Material.CHEST,mine?Lang.text("inventory-menus.all-orders", "All orders"):Lang.text("inventory-menus.my-orders-claims", "My orders / claims"),()->orders(p,0,!mine));back(s,p);display(p,s);
    }
    public void sell(Player p){plugin.sellChest().open(p);}
    public void sellOptions(Player p){
        Screen s=screen(p,Lang.text("inventory-menus.sell", "Sell"));
        button(s,10,Material.GOLD_INGOT,Lang.text("inventory-menus.sell-held-item", "Sell held item"),()->{plugin.menus().sellHand(p);sell(p);});
        button(s,12,Material.CHEST,Lang.text("inventory-menus.sell-inventory", "Sell inventory"),()->confirm(p,Lang.text("inventory-menus.sell-inventory-c769d1", "Sell Inventory?"),Lang.text("inventory-menus.sells-supported-plain-items-in-your-storage-slots", "Sells supported plain items in your storage slots."),()->{plugin.menus().sellAll(p);sell(p);},()->sell(p)));
        button(s,14,Material.DIAMOND,Lang.text("inventory-menus.sell-exact-held-item", "Sell exact held item"),()->heldSale(p,false));
        button(s,16,com.donsup.compat.Materials.SHULKER_BOX,Lang.text("inventory-menus.sell-shulker-contents", "Sell shulker contents"),()->heldSale(p,true));
        button(s,31,Material.BOOK,Lang.text("inventory-menus.sell-history", "Sell history"),()->plugin.extensions().history(p));back(s,p);display(p,s);
    }
    private void heldSale(Player p,boolean shulker){
        ItemStack held=com.donsup.compat.BukkitCompat.hand(p.getInventory()).clone();
        if(com.donsup.compat.BukkitCompat.air(held.getType())){notice(p,Lang.text("inventory-menus.sell", "Sell"),Lang.text("inventory-menus.hold-an-item-first", "Hold an item first."));return;}
        confirmItem(p,shulker?Lang.text("inventory-menus.sell-shulker-contents-aeb7c8", "Sell Shulker Contents?"):Lang.text("inventory-menus.sell-exact-item", "Sell Exact Item?"),held,shulker?Lang.text("inventory-menus.keeps-the-box-and-protected-custom-items", "Keeps the box and protected custom items."):Lang.text("inventory-menus.only-matching-orders-may-buy-this-exact-item", "Only matching orders may buy this exact item."),()->{
            if(!held.equals(com.donsup.compat.BukkitCompat.hand(p.getInventory()))){plugin.msg(p,Lang.text("inventory-menus.your-held-item-changed", "&cYour held item changed."));return;}
            command(p,shulker?"sell shulker":"sell exact");
        });
    }
}


===== src/main/java/com/donsup/dialog/NativeMenus.java =====

package com.donsup.dialog;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.market.*;
import com.donsup.util.Text;
import io.papermc.paper.connection.PlayerGameConnection;
import io.papermc.paper.dialog.*;
import io.papermc.paper.event.player.PlayerCustomClickEvent;
import io.papermc.paper.registry.data.dialog.*;
import io.papermc.paper.registry.data.dialog.action.DialogAction;
import io.papermc.paper.registry.data.dialog.body.DialogBody;
import io.papermc.paper.registry.data.dialog.input.DialogInput;
import io.papermc.paper.registry.data.dialog.type.DialogType;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.event.ClickCallback;
import net.kyori.adventure.text.minimessage.MiniMessage;
import org.bukkit.*;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;
import java.io.File;
import java.time.Duration;
import java.util.*;
import java.util.function.Consumer;

public final class NativeMenus implements PlayerMenus {
    private final DonsupPlugin plugin;
    private final SessionGate sessions = new SessionGate();
    private YamlConfiguration config;
    private final Map<UUID, Long> opens = new HashMap<>();
    private static final List<String> CATEGORIES = List.of("chat", "notifications", "pvp", "visuals", "privacy", "scoreboard");
    public NativeMenus(DonsupPlugin plugin) { this.plugin = plugin; reload(); }
    public void reload() {
        File file = new File(plugin.getDataFolder(), "dialogs.yml");
        if (!file.exists()) plugin.saveResource("dialogs.yml", false);
        YamlConfiguration next = new YamlConfiguration();
        try { next.load(file); }
        catch (Exception ex) { throw new IllegalArgumentException(Lang.text("native-menus.invalid-dialogs-yml", "Invalid dialogs.yml: {0}", ex.getMessage()), ex); }
        for (String category : CATEGORIES) {
            if (!next.isConfigurationSection("categories." + category))
                throw new IllegalArgumentException(Lang.text("native-menus.missing-dialog-category", "Missing dialog category: {0}", category));
            for (String key : next.getStringList("categories." + category + ".settings"))
                if (!com.donsup.features.ServerFeatures.SETTINGS.contains(key))
                    throw new IllegalArgumentException(Lang.text("native-menus.unknown-player-setting", "Unknown player setting: {0}", key));
        }
        config = next;
        sessions.clear();
    }
    private Component text(String raw) {
        return NativeText.component(plugin.customization().menuText(com.donsup.config.Branding.dialogTitle(raw)), plugin.serverName());
    }
    private Component plainText(String raw) {
        return Component.text(com.donsup.config.Branding.expand(plugin.customization().menuText(raw), plugin.getConfig()));
    }
    private int width() { return Math.max(150, Math.min(400, config.getInt("button-width", 300))); }
    private UUID start(Player player) { return sessions.open(player.getUniqueId()); }
    private ActionButton action(Player player, UUID token, String label, Consumer<DialogResponseView> run) {
        UUID owner = player.getUniqueId();
        return ActionButton.builder(text(label)).width(width()).action(DialogAction.customClick((response, audience) -> {
            if (!(audience instanceof Player actor) || !actor.getUniqueId().equals(owner) || !plugin.isEnabled()) return;
            plugin.platform().player(actor, () -> {
                if (!actor.isOnline() || !actor.hasPermission("donsup.use") || !sessions.consume(owner, actor.getUniqueId(), token)) return;
                try { run.accept(response); }
                catch (IllegalArgumentException ex) { plugin.msg(actor, Lang.text("native-menus.text", "&c{0}", ex.getMessage())); }
            });
        }, ClickCallback.Options.builder().uses(ClickCallback.UNLIMITED_USES).lifetime(Duration.ofMinutes(5)).build())).build();
    }
    private void show(Player player, String title, List<DialogBody> body, List<DialogInput> inputs, List<ActionButton> buttons, int columns) {
        if (!player.hasPermission("donsup.use")) { plugin.msg(player, Lang.text("native-menus.no-permission", "&cNo permission.")); return; }
        player.closeInventory();
        List<ActionButton> fitted = columns > 1 ? buttons.stream().map(button -> ActionButton.create(
            button.label(), button.tooltip(), Math.max(100, width() / columns), button.action())).toList() : buttons;
        player.showDialog(Dialog.create(builder -> builder.empty()
            .base(DialogBase.builder(text(title)).canCloseWithEscape(true).pause(false)
                .afterAction(DialogBase.DialogAfterAction.CLOSE).body(body).inputs(inputs).build())
            .type(DialogType.multiAction(fitted).columns(columns)
                .exitAction(ActionButton.builder(plainText(Lang.text("native-menus.close", "Close"))).width(width()).build()).build())));
        if (plugin.economy().setting(player.getUniqueId(), "menu_sounds"))
            player.playSound(player.getLocation(), Sound.UI_BUTTON_CLICK, .25f, 1.1f);
    }
    private List<DialogBody> body(String message) { return List.of(DialogBody.plainMessage(text(message), 400)); }
    public void notice(Player player, String title, String message) {
        UUID token = start(player);
        show(player, title, body(message), List.of(), List.of(action(player, token, Lang.text("native-menus.back", "Back"), r -> main(player))), 1);
    }
    public void confirm(Player player, String title, String detail, Runnable yes, Runnable no) {
        UUID token = start(player);
        show(player, title, body(detail), List.of(), List.of(action(player, token, Lang.text("native-menus.confirm", "<green>Confirm"), r -> yes.run()),
            action(player, token, Lang.text("native-menus.cancel", "Cancel"), r -> no.run())), 1);
    }
    public void confirmItem(Player player, String title, ItemStack item, String detail, Runnable yes) {
        UUID token = start(player);
        show(player, title, List.of(DialogBody.item(item.clone()).build(), DialogBody.plainMessage(plainText(detail))),
                List.of(), List.of(action(player, token, Lang.text("native-menus.confirm", "<green>Confirm"), r -> yes.run()),
                        action(player, token, Lang.text("native-menus.cancel", "Cancel"), r -> {})), 1);
    }
    public void route(Player player, String route) {
        switch (route) {
            case "main" -> main(player);
            case "settings" -> settings(player);
            case "auction" -> listings(player, "auction", "", 0, false);
            case "orders" -> orders(player, 0, false);
            case "homes" -> homes(player);
            case "friends" -> friends(player);
            default -> { if (CATEGORIES.contains(route)) category(player, route); }
        }
    }
    @EventHandler public void pauseClick(PlayerCustomClickEvent event) {
        if (!event.getIdentifier().namespace().equals("donsup") || !event.getIdentifier().value().startsWith("open/")) return;
        if (!(event.getCommonConnection() instanceof PlayerGameConnection connection)) return;
        Player player = connection.getPlayer();
        plugin.platform().player(player, () -> {
            long now = System.currentTimeMillis();
            if (!player.isOnline() || now - opens.getOrDefault(player.getUniqueId(), 0L) < 250) return;
            opens.put(player.getUniqueId(), now);
            route(player, event.getIdentifier().value().substring(5));
        });
    }
    @EventHandler public void quit(PlayerQuitEvent event) { sessions.close(event.getPlayer().getUniqueId()); opens.remove(event.getPlayer().getUniqueId()); }
    public void shutdown() { sessions.clear(); if (!plugin.platform().folia()) for (Player player : Bukkit.getOnlinePlayers()) player.closeDialog(); }
    public void main(Player player) {
        UUID token = start(player);
        List<ActionButton> buttons = new ArrayList<>();
        for (var button : plugin.customization().buttons()) {
            if (!button.visible(player)) continue;
            buttons.add(action(player, token, button.label(), r -> {
                if (button.visible(player)) player.performCommand(button.command().replace("%player%", player.getName()));
            }));
        }
        show(player, config.getString("title", "<gold>%server%</gold>"), body(plugin.customization().summary(
            Text.money(plugin.economy().money(player.getUniqueId())),plugin.economy().shards(player.getUniqueId()))), List.of(), buttons, plugin.customization().columns());
    }
    public void settings(Player player) {
        UUID token = start(player);
        var buttons = CATEGORIES.stream().map(category -> action(player, token,
            config.getString("categories." + category + ".label", category), r -> category(player, category))).toList();
        show(player, config.getString("settings-title", "Settings"), List.of(), List.of(), buttons, 1);
    }
    public void travel(Player player) {
        UUID token = start(player);
        List<ActionButton> buttons = new ArrayList<>();
        for (String dimension : com.donsup.features.RtpManager.DIMENSIONS) {
            if (plugin.travel().rtp().world(dimension) == null) continue;
            String label = Lang.label("dimensions", dimension, dimension.substring(0, 1).toUpperCase(Locale.ROOT) + dimension.substring(1));
            buttons.add(action(player, token, Lang.text("native-menus.solo", "{0} - Solo", label), r -> plugin.travel().rtp().solo(player, dimension)));
            if (plugin.getConfig().getBoolean("travel.queue.enabled", true) && player.hasPermission("donsup.rtp.queue"))
                buttons.add(action(player, token, Lang.text("native-menus.find-a-partner", "{0} - Find a partner", label), r -> plugin.travel().rtp().join(player, dimension)));
        }
        buttons.add(action(player, token, Lang.text("native-menus.regions-zones", "Regions / Zones"), r -> plugin.zoneMenu().open(player,0)));
        buttons.add(action(player, token, Lang.text("native-menus.leave-rtp-queue-cancel", "Leave RTP queue / cancel"), r -> plugin.travel().rtp().cancel(player.getUniqueId(), Lang.text("native-menus.rtp-cancelled", "RTP cancelled."))));
        show(player, Lang.text("native-menus.random-teleport", "Random Teleport"), body(Lang.text("native-menus.find-a-partner-sends-two-players-to-nearby-wilderness-locations-p", "<gray>{0}\nFind a partner sends two players to nearby wilderness locations. PvP may be enabled there.", plugin.travel().rtp().status(player))), List.of(), buttons, 1);
    }
    public void category(Player player, String category) {
        UUID token = start(player);
        List<String> keys = new ArrayList<>(config.getStringList("categories." + category + ".settings"));
        if(category.equals("pvp")&&!keys.contains("keep_pearls_on_death"))keys.add("keep_pearls_on_death");
        keys.removeIf(k->k.equals("keep_pearls_on_death")&&!plugin.pearls().supported());
        List<DialogInput> inputs = keys.stream().filter(key -> !key.equals("night_vision") || plugin.economy().premium(player))
            .map(key -> (DialogInput) DialogInput.bool(key, text(config.getString("labels." + key, key)))
                .initial(plugin.economy().setting(player.getUniqueId(), key)).build()).toList();
        show(player, config.getString("categories." + category + ".label", category),
            body(config.getString("categories." + category + ".description", "")), inputs,
            List.of(action(player, token, Lang.text("native-menus.save", "<green>Save"), response -> {
                Map<String, Boolean> changes = new HashMap<>();
                for (DialogInput input : inputs) {
                    if (input.key().equals("night_vision") && !plugin.economy().premium(player)) continue;
                    Boolean value = response.getBoolean(input.key());
                    if (value == null) throw new IllegalArgumentException(Lang.text("native-menus.invalid-setting-value-reopen-settings", "Invalid setting value. Reopen /settings."));
                    changes.put(input.key(), value);
                }
                plugin.economy().setSettings(player.getUniqueId(), changes);
                plugin.menus().applyNightVision(player);
                plugin.msg(player, Lang.text("native-menus.settings-saved", "&aSettings saved.")); settings(player);
            }), action(player, token, Lang.text("native-menus.back", "Back"), r -> settings(player))), 1);
    }
    public void profile(Player viewer, Player target) {
        if (!viewer.equals(target) && !plugin.economy().setting(target.getUniqueId(), "public_profile")) {
            notice(viewer, Lang.text("native-menus.private-profile", "Private profile"), Lang.text("native-menus.this-player-keeps-their-statistics-private", "This player keeps their statistics private.")); return;
        }
        UUID id = target.getUniqueId();
        notice(viewer, target.getName(), Lang.text("native-menus.money-shards-kills-deaths-playtime-hours-rank", "<gray>Money: <green>{0}\n<gray>Shards: <light_purple>{1}\n<gray>Kills: <white>{2}\n<gray>Deaths: <white>{3}\n<gray>Playtime: <white>{4} hours\n<gray>Rank: <gold>{5}", Text.money(plugin.economy().money(id)), plugin.economy().shards(id), plugin.economy().stat(id, "kills"), plugin.economy().stat(id, "deaths"), target.getStatistic(Statistic.PLAY_ONE_MINUTE) / 72000, plugin.economy().rank(target)));
    }
    public void homes(Player player) {
        UUID token = start(player);
        List<ActionButton> buttons = new ArrayList<>();
        for (String name : plugin.economy().homeNames(player.getUniqueId()).stream().sorted().limit(100).toList())
            buttons.add(action(player, token, name, r -> homeDetail(player, name)));
        buttons.add(action(player, token, Lang.text("native-menus.set-a-home", "<green>Set a home"), r -> {
            UUID next = start(player);
            show(player, Lang.text("native-menus.set-home", "Set Home"), body(Lang.text("native-menus.save-your-current-location", "Save your current location.")), List.of(DialogInput.text("name", plainText(Lang.text("native-menus.home-name", "Home name"))).maxLength(24).build()),
                List.of(action(player, next, Lang.text("native-menus.save-1509f5", "Save"), response -> {
                    String name = required(response, "name");
                    if (!name.matches("[a-zA-Z0-9_-]{1,24}")) throw new IllegalArgumentException(Lang.text("native-menus.use-1-24-letters-numbers-or", "Use 1-24 letters, numbers, _ or -."));
                    if (!plugin.economy().setHome(player, name)) plugin.msg(player, Lang.text("native-menus.home-limit-reached", "&cHome limit reached."));
                    homes(player);
                }), action(player, next, Lang.text("native-menus.back", "Back"), response -> homes(player))), 1);
        }));
        buttons.add(action(player, token, Lang.text("native-menus.back", "Back"), r -> main(player)));
        show(player, Lang.text("native-menus.homes", "Homes"), body(Lang.text("native-menus.saved", "<gray>Saved {0} / {1}", plugin.economy().homeNames(player.getUniqueId()).size(), plugin.economy().homeLimit(player))), List.of(), buttons, 1);
    }
    private void homeDetail(Player player, String name) {
        UUID token = start(player);
        show(player, name, List.of(), List.of(), List.of(
            action(player, token, Lang.text("native-menus.teleport", "Teleport"), r -> plugin.travel().teleport(player, plugin.economy().home(player.getUniqueId(), name))),
            action(player, token, Lang.text("native-menus.delete", "<red>Delete"), r -> confirm(player, Lang.text("native-menus.delete-home", "Delete home?"), name, () -> { plugin.economy().deleteHome(player.getUniqueId(), name); homes(player); }, () -> homes(player))),
            action(player, token, Lang.text("native-menus.back", "Back"), r -> homes(player))), 1);
    }
    public void friends(Player player) {
        UUID token = start(player);
        List<ActionButton> buttons = new ArrayList<>();
        for (UUID id : plugin.extensions().friends(player.getUniqueId())) {
            String name = plugin.economy().playerName(id);
            Player online = Bukkit.getPlayer(id);
            buttons.add(action(player, token, (online == null || !player.canSee(online) ? Lang.text("native-menus.text-a2d378", "<gray>") : Lang.text("native-menus.text-b8bc61", "<green>")) + name,
                r -> confirm(player, Lang.text("native-menus.remove-friend", "Remove friend?"), name, () -> { plugin.extensions().removeFriend(player, id); friends(player); }, () -> friends(player))));
        }
        for (Player from : plugin.extensions().friendRequests(player))
            buttons.add(action(player, token, Lang.text("native-menus.accept", "Accept {0}", from.getName()), r -> { plugin.extensions().friend(player, new String[]{"accept", from.getName()}); friends(player); }));
        buttons.add(action(player, token, Lang.text("native-menus.add-friend", "Add Friend"), r -> {
            UUID next = start(player);
            show(player, Lang.text("native-menus.add-friend", "Add Friend"), List.of(), List.of(DialogInput.text("name", plainText(Lang.text("native-menus.online-player", "Online player"))).maxLength(16).build()),
                List.of(action(player, next, Lang.text("native-menus.send-request", "Send Request"), response -> { plugin.extensions().friend(player, new String[]{"add", required(response, "name")}); friends(player); })), 1);
        }));
        buttons.add(action(player, token, Lang.text("native-menus.back", "Back"), r -> main(player)));
        show(player, Lang.text("native-menus.friends", "Friends"), body(Lang.text("native-menus.friend-chat-fc", "<gray>Friend chat: /fc <message>")), List.of(), buttons, 1);
    }
    public void listings(Player player, String type, String search, int page, boolean mine) {
        UUID token = start(player);
        var all = (mine ? plugin.market().ownedListings(player.getUniqueId(), type) : plugin.market().listings(type)).stream()
            .filter(l -> l.item().getType().name().toLowerCase(Locale.ROOT).contains(search.toLowerCase(Locale.ROOT)))
            .sorted(Comparator.comparingDouble(l -> l.price() / l.item().getAmount())).toList();
        int index = Math.min(Math.max(0, page), Math.max(0, (all.size() - 1) / 8));
        List<ActionButton> buttons = new ArrayList<>();
        for (var listing : all.stream().skip(index * 8L).limit(8).toList())
            buttons.add(action(player, token, Lang.text("native-menus.x", "{0}x {1} • {2}", listing.item().getAmount(), pretty(listing.item().getType()), Text.money(listing.price())),
                r -> listingDetail(player, listing, type, search, index, mine)));
        if (index > 0) buttons.add(action(player, token, Lang.text("native-menus.previous", "Previous"), r -> listings(player, type, search, index - 1, mine)));
        if ((index + 1) * 8 < all.size()) buttons.add(action(player, token, Lang.text("native-menus.next", "Next"), r -> listings(player, type, search, index + 1, mine)));
        buttons.add(action(player, token, Lang.text("native-menus.search", "Search"), r -> search(player, type)));
        buttons.add(action(player, token, mine ? Lang.text("native-menus.all-listings", "All Listings") : Lang.text("native-menus.my-listings-returns", "My Listings / Returns"), r -> listings(player, type, "", 0, !mine)));
        buttons.add(action(player, token, Lang.text("native-menus.list-held-item", "List Held Item"), r -> listForm(player, type)));
        buttons.add(action(player, token, Lang.text("native-menus.shard-shop", "Shard Shop"), r -> plugin.menus().openShardShop(player)));
        buttons.add(action(player, token, Lang.text("native-menus.back", "Back"), r -> main(player)));
        show(player, type.equals("auction") ? Lang.text("native-menus.auction-house", "Auction House") : Lang.text("native-menus.player-market", "Player Market"), body(Lang.text("native-menus.listings-page-lowest-unit-price-first", "<gray>{0} listings • page {1} • lowest unit price first", all.size(), (index + 1))), List.of(), buttons, 2);
    }
    private void listingDetail(Player player, MarketListing listing, String type, String query, int page, boolean mine) {
        listingDetail(player, listing, type, query, page, mine, false);
    }
    private void listingDetail(Player player, MarketListing listing, String type, String query, int page, boolean mine, boolean quickBuy) {
        UUID token = start(player);
        boolean own = listing.owner().equals(player.getUniqueId());
        var body = List.of(DialogBody.item(listing.item().clone()).build(), DialogBody.plainMessage(plainText(
            Lang.text("native-menus.seller-total-per-item", "Seller: {0}\nTotal: {1}\nPer item: {2}", listing.ownerName(), Text.money(listing.price()), Text.money(listing.price() / listing.item().getAmount())))));
        show(player, Lang.text("native-menus.listing", "Listing"), body, List.of(), List.of(action(player, token, own ? Lang.text("native-menus.cancel-reclaim", "Cancel / Reclaim") : Lang.text("native-menus.confirm-purchase", "<green>Confirm Purchase"), r -> {
            if (quickBuy && plugin.travel().tagged(player)) { plugin.msg(player, Lang.text("native-menus.quick-buy-is-unavailable-during-combat", "&cQuick Buy is unavailable during combat.")); return; }
            if (own) plugin.market().reclaim(player, listing.id()); else plugin.menus().buyListing(player, listing.id());
            listings(player, type, query, page, mine);
        }), action(player, token, Lang.text("native-menus.back", "Back"), r -> listings(player, type, query, page, mine))), 1);
    }
    private void search(Player player, String type) {
        UUID token = start(player);
        show(player, Lang.text("native-menus.search", "Search"), List.of(), List.of(DialogInput.text("query", plainText(Lang.text("native-menus.material-name", "Material name"))).maxLength(64).build()),
            List.of(action(player, token, Lang.text("native-menus.search", "Search"), r -> listings(player, type, Objects.requireNonNullElse(r.getText("query"), "").trim(), 0, false))), 1);
    }

    public void quickBuy(Player player, int page, ItemStack match) {
        if (plugin.travel().tagged(player)) { plugin.msg(player, Lang.text("native-menus.quick-buy-is-unavailable-during-combat", "&cQuick Buy is unavailable during combat.")); return; }
        UUID token = start(player);
        var offers = plugin.market().listings("auction").stream().filter(listing -> !listing.owner().equals(player.getUniqueId()))
            .filter(listing -> match == null ? !listing.item().hasItemMeta() : listing.item().isSimilar(match))
            .sorted(Comparator.comparingDouble(listing -> listing.price() / listing.item().getAmount())).toList();
        Map<Material, MarketListing> cheapest = new LinkedHashMap<>();
        offers.forEach(listing -> cheapest.putIfAbsent(listing.item().getType(), listing));
        int index = Math.min(Math.max(page, 0), Math.max(0, (cheapest.size() - 1) / 8));
        List<ActionButton> buttons = new ArrayList<>();
        for (MarketListing listing : cheapest.values().stream().skip(index * 8L).limit(8).toList())
            buttons.add(action(player, token, Lang.text("native-menus.item", "{0} • {1}/item", pretty(listing.item().getType()), Text.money(listing.price() / listing.item().getAmount())), r -> {
                if (plugin.travel().tagged(player)) { plugin.msg(player, Lang.text("native-menus.quick-buy-is-unavailable-during-combat", "&cQuick Buy is unavailable during combat.")); return; }
                listingDetail(player, listing, "auction", "", 0, false, true);
            }));
        if (index > 0) buttons.add(action(player, token, Lang.text("native-menus.previous", "Previous"), r -> quickBuy(player, index - 1, match)));
        if ((index + 1) * 8 < cheapest.size()) buttons.add(action(player, token, Lang.text("native-menus.next", "Next"), r -> quickBuy(player, index + 1, match)));
        buttons.add(action(player, token, Lang.text("native-menus.match-held-item-exactly", "Match Held Item Exactly"), r -> {
            var held = player.getInventory().getItemInMainHand();
            if (held.getType().isAir()) notice(player, Lang.text("native-menus.quick-buy", "Quick Buy"), Lang.text("native-menus.hold-an-item-to-find-an-exact-match-including-enchantments-and-da", "Hold an item to find an exact match, including enchantments and damage."));
            else quickBuy(player, 0, held.clone());
        }));
        buttons.add(action(player, token, Lang.text("native-menus.back", "Back"), r -> main(player)));
        buttons.add(action(player, token, Lang.text("native-menus.saved-favourites-loadouts", "Saved favourites / loadouts"), r -> plugin.shopping().open(player,null)));
        show(player, Lang.text("native-menus.quick-buy", "Quick Buy"), body(Lang.text("native-menus.cheapest-live-offers-confirm-the-complete-stack-before-buying", "Cheapest live offers • confirm the complete stack before buying.\n{0}", (match == null ? Lang.text("native-menus.plain-items-use-match-held-item-for-enchanted-or-custom-items", "Plain items. Use Match Held Item for enchanted or custom items.") : Lang.text("native-menus.exact-matches-for-your-held-item", "Exact matches for your held item.")))), List.of(), buttons, 1);
    }
    private void listForm(Player player, String type) {
        UUID token = start(player);
        ItemStack preview = player.getInventory().getItemInMainHand().clone();
        if (preview.getType().isAir()) { notice(player, Lang.text("native-menus.list-item", "List item"), Lang.text("native-menus.hold-the-item-you-want-to-list", "Hold the item you want to list.")); return; }
        show(player, Lang.text("native-menus.list-held-item", "List Held Item"), List.of(DialogBody.item(preview).build(), DialogBody.plainMessage(plainText(Lang.text("native-menus.listing-fee", "Listing fee: {0}%", plugin.economy().listingTaxPercent(player))))),
            List.of(DialogInput.text("price", plainText(Lang.text("native-menus.total-asking-price", "Total asking price"))).maxLength(16).build()),
            List.of(action(player, token, Lang.text("native-menus.create-listing", "Create Listing"), response -> {
                double price = positiveMoney(required(response, "price"));
                if (!preview.equals(player.getInventory().getItemInMainHand())) throw new IllegalArgumentException(Lang.text("native-menus.your-held-item-changed-reopen-this-form", "Your held item changed; reopen this form."));
                player.performCommand((type.equals("auction") ? "ah" : "market") + " list " + price);
            })), 1);
    }
    public void orders(Player player, int page, boolean mine) {
        UUID token = start(player);
        var all = plugin.market().orders().stream().filter(o -> mine ? o.owner().equals(player.getUniqueId()) : o.remaining() > 0 && o.expiresAt() > System.currentTimeMillis())
            .sorted(Comparator.comparingDouble(BulkOrder::priceEach).reversed()).toList();
        int index = Math.min(Math.max(page, 0), Math.max(0, (all.size() - 1) / 8));
        List<ActionButton> buttons = new ArrayList<>();
        for (var order : all.stream().skip(index * 8L).limit(8).toList())
            buttons.add(action(player, token, Lang.text("native-menus.each", "{0} • {1} each", pretty(order.material()) + (order.exact() ? Lang.text("native-menus.exact", " (exact)") : ""), Text.money(order.priceEach())), r -> {
                boolean own = order.owner().equals(player.getUniqueId());
                UUID detail = start(player);
                show(player, own ? Lang.text("native-menus.close-claim-order", "Close & Claim Order") : Lang.text("native-menus.deliver-items", "Deliver Items"), List.of(DialogBody.item(order.item()).build(),
                    DialogBody.plainMessage(plainText(Lang.text("native-menus.requested-delivered-remaining-price-each", "Requested: {0}\nDelivered: {1}\nRemaining: {2}\nPrice each: {3}{4}", order.requested(), order.delivered(), order.remaining(), Text.money(order.priceEach()), (own ? Lang.text("native-menus.closes-this-order-and-refunds-unfilled-demand", "\nCloses this order and refunds unfilled demand.") : order.exact()
                        ? Lang.text("native-menus.only-identical-items-qualify-including-name-enchantments-damage-a", "\nOnly identical items qualify, including name, enchantments, damage and custom data.")
                        : Lang.text("native-menus.delivers-matching-plain-items-from-your-inventory", "\nDelivers matching plain items from your inventory.")))))), List.of(),
                    List.of(action(player, detail, Lang.text("native-menus.confirm-eebdd2", "Confirm"), response -> {
                        if (own) plugin.menus().claimOrder(player, order.id()); else plugin.menus().deliverOrder(player, order.id()); orders(player, index, mine);
                    }), action(player, detail, Lang.text("native-menus.back", "Back"), response -> orders(player, index, mine))), 1);
            }));
        if (index > 0) buttons.add(action(player, token, Lang.text("native-menus.previous", "Previous"), r -> orders(player, index - 1, mine)));
        if ((index + 1) * 8 < all.size()) buttons.add(action(player, token, Lang.text("native-menus.next", "Next"), r -> orders(player, index + 1, mine)));
        buttons.add(action(player, token, Lang.text("native-menus.create-order", "Create Order"), r -> createOrder(player)));
        buttons.add(action(player, token, Lang.text("native-menus.order-held-item-exactly", "Order Held Item Exactly"), r -> exactOrder(player)));
        buttons.add(action(player, token, mine ? Lang.text("native-menus.all-orders", "All Orders") : Lang.text("native-menus.my-orders-claims", "My Orders / Claims"), r -> orders(player, 0, !mine)));
        buttons.add(action(player, token, Lang.text("native-menus.shard-shop", "Shard Shop"), r -> plugin.menus().openShardShop(player)));
        buttons.add(action(player, token, Lang.text("native-menus.back", "Back"), r -> main(player)));
        show(player, Lang.text("native-menus.orders", "Orders"), body(Lang.text("native-menus.orders-page", "<gray>{0} orders • page {1}", all.size(), (index + 1))), List.of(), buttons, 2);
    }
    private void exactOrder(Player player) {
        ItemStack sample = player.getInventory().getItemInMainHand().clone();
        if (sample.getType().isAir()) { notice(player, Lang.text("native-menus.exact-item-order", "Exact Item Order"), Lang.text("native-menus.hold-an-item-to-use-as-the-sample", "Hold an item to use as the sample.")); return; }
        sample.setAmount(1);
        UUID token = start(player);
        show(player, Lang.text("native-menus.exact-item-order", "Exact Item Order"), List.of(DialogBody.item(sample).build(), DialogBody.plainMessage(plainText(
            Lang.text("native-menus.your-sample-is-kept-only-identical-items-qualify-including-spawne", "Your sample is kept. Only identical items qualify, including spawner type, enchantments, damage, name and custom data. Funds are held in escrow.")))),
            List.of(DialogInput.text("amount", plainText(Lang.text("native-menus.quantity", "Quantity"))).maxLength(7).build(),
                DialogInput.text("price", plainText(Lang.text("native-menus.maximum-price-per-item", "Maximum price per item"))).maxLength(16).build()),
            List.of(action(player, token, Lang.text("native-menus.create-order", "Create Order"), response -> {
                int amount;
                try { amount = Integer.parseInt(required(response, "amount")); }
                catch (NumberFormatException ex) { throw new IllegalArgumentException(Lang.text("native-menus.enter-a-whole-quantity", "Enter a whole quantity.")); }
                double price = positiveMoney(required(response, "price"));
                if (!plugin.market().createExactOrder(player, sample, amount, price)) plugin.msg(player, Lang.text("native-menus.could-not-create-order-check-quantity-balance-and-order-limit", "&cCould not create order. Check quantity, balance and order limit."));
                orders(player, 0, true);
            }), action(player, token, Lang.text("native-menus.back", "Back"), response -> orders(player, 0, false))), 1);
    }
    private void createOrder(Player player) {
        UUID token = start(player);
        show(player, Lang.text("native-menus.create-order", "Create Order"), body(Lang.text("native-menus.funds-are-held-in-escrow-plain-unmodified-items-only", "Funds are held in escrow. Plain, unmodified items only.")), List.of(
            DialogInput.text("material", plainText(Lang.text("native-menus.material-e-g-iron-ingot", "Material (e.g. IRON_INGOT)"))).maxLength(64).build(),
            DialogInput.text("amount", plainText(Lang.text("native-menus.quantity", "Quantity"))).maxLength(7).build(),
            DialogInput.text("price", plainText(Lang.text("native-menus.price-per-item", "Price per item"))).maxLength(16).build()), List.of(action(player, token, Lang.text("native-menus.create-order", "Create Order"), r -> {
                Material material = Material.matchMaterial(required(r, "material"));
                int amount;
                try { amount = Integer.parseInt(required(r, "amount")); } catch (NumberFormatException ex) { throw new IllegalArgumentException(Lang.text("native-menus.enter-a-whole-quantity", "Enter a whole quantity.")); }
                double price = positiveMoney(required(r, "price"));
                if (material == null || !material.isItem() || material.isAir() || amount < 1 || amount > 1000000) throw new IllegalArgumentException(Lang.text("native-menus.invalid-material-or-quantity-1-1-000-000", "Invalid material or quantity (1-1,000,000)."));
                if (!plugin.market().createOrder(player, material, amount, price)) plugin.msg(player, Lang.text("native-menus.could-not-create-order-check-your-balance-and-order-limit", "&cCould not create order. Check your balance and order limit."));
                orders(player, 0, true);
            })), 1);
    }
    public void sell(Player player) { plugin.sellChest().open(player); }
    public void sellOptions(Player player) {
        UUID token = start(player);
        show(player, Lang.text("native-menus.sell", "Sell"), body(Lang.text("native-menus.sell-plain-items-at-the-best-available-order-price-or-server-pric", "Sell plain items at the best available order price or server price. Named, enchanted and custom items are protected.")), List.of(),
            List.of(action(player, token, Lang.text("native-menus.sell-held-item", "Sell Held Item"), r -> { plugin.menus().sellHand(player); sell(player); }),
                action(player, token, Lang.text("native-menus.sell-inventory", "Sell Inventory"), r -> confirm(player, Lang.text("native-menus.sell-inventory-c769d1", "Sell Inventory?"), Lang.text("native-menus.this-sells-supported-plain-items-in-your-storage-slots", "This sells supported plain items in your storage slots."),
                    () -> { plugin.menus().sellAll(player); sell(player); }, () -> sell(player))),
                action(player, token, Lang.text("native-menus.sell-exact-held-item", "Sell Exact Held Item"), r -> sellHeldConfirmation(player, false)),
                action(player, token, Lang.text("native-menus.sell-shulker-contents", "Sell Shulker Contents"), r -> sellHeldConfirmation(player, true)),
                action(player, token, Lang.text("native-menus.sell-history", "Sell History"), r -> plugin.extensions().history(player)),
                action(player, token, Lang.text("native-menus.back", "Back"), r -> main(player))), 1);
    }
    private void sellHeldConfirmation(Player player, boolean shulker) {
        ItemStack preview = player.getInventory().getItemInMainHand().clone();
        if (preview.getType().isAir()) { notice(player, Lang.text("native-menus.sell", "Sell"), Lang.text("native-menus.hold-the-item-you-want-to-sell", "Hold the item you want to sell.")); return; }
        UUID token = start(player);
        show(player, shulker ? Lang.text("native-menus.sell-shulker-contents-aeb7c8", "Sell Shulker Contents?") : Lang.text("native-menus.sell-exact-held-item-d23d13", "Sell Exact Held Item?"),
            List.of(DialogBody.item(preview).build(), DialogBody.plainMessage(plainText(shulker
                ? Lang.text("native-menus.sells-supported-plain-contents-keeps-the-box-and-all-custom-items", "Sells supported plain contents. Keeps the box and all custom items.")
                : Lang.text("native-menus.sells-this-item-only-to-matching-orders-names-enchantments-damage", "Sells this item only to matching orders. Names, enchantments, damage and custom data must match. Unsold items stay with you.")))),
            List.of(), List.of(action(player, token, Lang.text("native-menus.confirm-eebdd2", "Confirm"), response -> {
                if (!preview.equals(player.getInventory().getItemInMainHand())) throw new IllegalArgumentException(Lang.text("native-menus.your-held-item-changed-reopen-the-confirmation", "Your held item changed; reopen the confirmation."));
                player.performCommand(shulker ? "sell shulker" : "sell exact"); sell(player);
            }), action(player, token, Lang.text("native-menus.cancel", "Cancel"), response -> sell(player))), 1);
    }
    public static double positiveMoney(String value) {
        try { double amount = Double.parseDouble(value); if (Double.isFinite(amount) && amount > 0 && amount <= 1.0e12) return amount; }
        catch (NumberFormatException ignored) { }
        throw new IllegalArgumentException(Lang.text("native-menus.enter-a-finite-price-between-0-and-1-trillion", "Enter a finite price between 0 and 1 trillion."));
    }
    private static String required(DialogResponseView response, String key) {
        String text = response.getText(key);
        if (text == null || text.isBlank()) throw new IllegalArgumentException(Lang.text("native-menus.fill-in", "Fill in {0}.", key));
        return text.trim();
    }
    private String pretty(Material material) { return Lang.label("materials", material.name(), material.name().toLowerCase(Locale.ROOT).replace('_', ' ')); }
}


===== src/main/java/com/donsup/dialog/NativeText.java =====

package com.donsup.dialog;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.minimessage.MiniMessage;
import net.kyori.adventure.text.minimessage.tag.resolver.Placeholder;
import net.kyori.adventure.text.serializer.legacy.LegacyComponentSerializer;

/** Branding is inserted as a component, never evaluated as MiniMessage markup. */
final class NativeText {
    private NativeText() { }
    static Component component(String raw,String server) {
        return MiniMessage.miniMessage().deserialize(raw.replace("%server%","<server>"),
                Placeholder.component("server",LegacyComponentSerializer.legacyAmpersand().deserialize(server)));
    }
}


===== src/main/java/com/donsup/dialog/PlayerMenus.java =====

package com.donsup.dialog;
import org.bukkit.entity.Player;
import org.bukkit.event.Listener;
import org.bukkit.inventory.ItemStack;
public interface PlayerMenus extends Listener {
    void reload();
    void shutdown();
    void notice(Player p,String title,String message);
    void confirm(Player p,String title,String detail,Runnable yes,Runnable no);
    void confirmItem(Player p,String title,ItemStack item,String detail,Runnable yes);
    void main(Player p);
    void settings(Player p);
    void travel(Player p);
    void category(Player p,String category);
    void profile(Player p,Player target);
    void homes(Player p);
    void friends(Player p);
    void listings(Player p,String type,String search,int page,boolean mine);
    void quickBuy(Player p,int page,ItemStack match);
    void orders(Player p,int page,boolean mine);
    void sell(Player p);
    void sellOptions(Player p);
}


===== src/main/java/com/donsup/dialog/SessionGate.java =====

package com.donsup.dialog;

import java.util.*;

/** Accessed on the server thread. A fresh screen invalidates every callback from older screens. */
public final class SessionGate {
    private final Map<UUID, UUID> screens = new HashMap<>();
    public UUID open(UUID player) { UUID token = UUID.randomUUID(); screens.put(player, token); return token; }
    public boolean consume(UUID owner, UUID actor, UUID token) {
        return owner.equals(actor) && screens.remove(owner, token);
    }
    public void close(UUID player) { screens.remove(player); }
    public void clear() { screens.clear(); }
}


===== src/main/java/com/donsup/duel/DuelManager.java =====

package com.donsup.duel;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.ItemUtil;
import com.donsup.util.Text;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.Sound;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.PlayerDeathEvent;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerRespawnEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.Set;
import java.util.HashSet;

public class DuelManager implements Listener {
    private static final String TITLE = "SMP | Duels";
    private final DonsupPlugin plugin;
    private final ItemKey actionKey;
    private final File file;
    private FileConfiguration data;
    private final Map<UUID, DuelInvite> invites = new HashMap<>();
    private final Map<UUID, ActiveDuel> active = new HashMap<>();
    private final Set<UUID> entering = new HashSet<>();
    private final Set<String> enteringArenas = new HashSet<>();
    private final Map<UUID,Location> expectedTransfers = new HashMap<>();
    public boolean expectedTeleport(Player player, Location to) { return to != null && to.equals(expectedTransfers.get(player.getUniqueId())); }

    private void startRegionDuel(Player a,Player b,String arena,double pot) {
        if(entering.contains(a.getUniqueId()) || entering.contains(b.getUniqueId()) || enteringArenas.contains(arena)) return;
        Location spawn1=readLocation("arenas."+arena+".spawn1"),spawn2=readLocation("arenas."+arena+".spawn2");
        if(spawn1==null || spawn2==null)return;
        entering.add(a.getUniqueId());entering.add(b.getUniqueId());enteringArenas.add(arena);
        Map<UUID,Location> origins=new HashMap<>();
        var snapshotA=plugin.platform().onPlayer(a,()->{if(a.isOnline()&&!a.isDead()&&!plugin.travel().tagged(a))origins.put(a.getUniqueId(),a.getLocation());});
        var snapshotB=plugin.platform().onPlayer(b,()->{if(b.isOnline()&&!b.isDead()&&!plugin.travel().tagged(b))origins.put(b.getUniqueId(),b.getLocation());});
        java.util.concurrent.CompletableFuture.allOf(snapshotA,snapshotB).whenComplete((ignored,error)->plugin.platform().global(()->{
            if(error!=null || origins.size()!=2 || !entering.containsAll(List.of(a.getUniqueId(),b.getUniqueId()))) {
                endEntry(a,b,arena);plugin.msg(a,Lang.text("duel.duel-cancelled-a-player-became-unavailable", "&cDuel cancelled: a player became unavailable."));plugin.msg(b,Lang.text("duel.duel-cancelled-a-player-became-unavailable", "&cDuel cancelled: a player became unavailable."));return;
            }
            ActiveDuel duel=new ActiveDuel(UUID.randomUUID(),a.getUniqueId(),b.getUniqueId(),origins.get(a.getUniqueId()),origins.get(b.getUniqueId()),pot,arena);
            if(!plugin.economy().reserveDuel(duel.id(),duel.a(),duel.b(),pot/2)){
                endEntry(a,b,arena);plugin.msg(a,Lang.text("duel.duel-funding-failed", "&cDuel funding failed."));plugin.msg(b,Lang.text("duel.duel-funding-failed", "&cDuel funding failed."));return;
            }
            writeLocation("returns."+duel.a(),duel.returnA());writeLocation("returns."+duel.b(),duel.returnB());save();
            var moveA=moveForDuel(a,spawn1);
            var moveB=moveForDuel(b,spawn2);
            java.util.concurrent.CompletableFuture.allOf(moveA,moveB).whenComplete((v,problem)->plugin.platform().global(()->{
                boolean success=problem==null && Boolean.TRUE.equals(moveA.getNow(false)) && Boolean.TRUE.equals(moveB.getNow(false))
                    && entering.containsAll(List.of(duel.a(),duel.b()));
                endEntry(a,b,arena);
                if(!success){
                    plugin.economy().settleDuel(duel.id(),null);
                    plugin.platform().player(a,()->{if(a.isOnline()&&!a.isDead())returnPlayer(a);});
                    plugin.platform().player(b,()->{if(b.isOnline()&&!b.isDead())returnPlayer(b);});
                    plugin.msg(a,Lang.text("duel.duel-cancelled-because-a-teleport-was-blocked", "&cDuel cancelled because a teleport was blocked."));plugin.msg(b,Lang.text("duel.duel-cancelled-because-a-teleport-was-blocked", "&cDuel cancelled because a teleport was blocked."));return;
                }
                active.put(duel.a(),duel);active.put(duel.b(),duel);
                for(Player player:List.of(a,b))plugin.platform().player(player,()->{
                    if(!player.isOnline()||player.isDead()){leave(player);return;}
                    if(active.get(player.getUniqueId())!=duel)return;
                    player.setHealth(Math.min(player.getMaxHealth(),20));player.setFoodLevel(20);
                    plugin.msg(player,Lang.text("duel.duel-started", "&cDuel started."));
                });
            }));
        }));
    }
    private java.util.concurrent.CompletableFuture<Boolean> moveForDuel(Player player,Location destination){
        var result=new java.util.concurrent.CompletableFuture<Boolean>();
        plugin.platform().onPlayer(player,()->{
            if(!player.isOnline()||player.isDead()||plugin.travel().tagged(player)||!entering.contains(player.getUniqueId())){result.complete(false);return;}
            expectedTransfers.put(player.getUniqueId(),destination);
            try {
                plugin.platform().teleport(player,destination).whenComplete((ok,error)->plugin.platform().global(()->{
                    expectedTransfers.remove(player.getUniqueId(),destination);result.complete(error==null&&Boolean.TRUE.equals(ok));
                }));
            } catch(RuntimeException ex){expectedTransfers.remove(player.getUniqueId());result.complete(false);}
        }).whenComplete((ran,error)->{if(error!=null||!Boolean.TRUE.equals(ran))result.complete(false);});
        return result;
    }
    private void endEntry(Player a,Player b,String arena){entering.remove(a.getUniqueId());entering.remove(b.getUniqueId());enteringArenas.remove(arena);}

    public DuelManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.actionKey = new ItemKey(plugin, "duel_action");
        this.file = new File(plugin.getDataFolder(), "duels.yml");
        reload();
        plugin.platform().globalTimer(() -> invites.values().removeIf(this::expired), 100, 100);
    }

    public void reload() {
        data = com.donsup.util.SafeYaml.load(file);
    }

    public void save() {
        try {
            com.donsup.util.SafeYaml.save(data, file);
        } catch (IOException ex) {
            plugin.getLogger().warning("Could not save duels.yml: " + ex.getMessage());
        }
    }

    public void open(Player player) {
        Inventory inv = plugin.inventory(54, TITLE, false);
        fill(inv);
        inv.setItem(4, button(Material.DIAMOND_SWORD, Lang.text("duel.duels", "&c&lDuels"), List.of(
                Lang.text("duel.challenge-players-accept-pending-duels", "&7Challenge players, accept pending duels,"),
                Lang.text("duel.and-fight-in-configured-arena-spawns", "&7and fight in configured arena spawns.")
        ), "NONE"));
        inv.setItem(20, button(com.donsup.compat.Materials.WRITABLE_BOOK, Lang.text("duel.how-to-challenge", "&aHow To Challenge"), List.of(
                Lang.text("duel.duel-wager", "&f/duel <player> [wager]"),
                Lang.text("duel.wager-is-optional-and-paid-to-the-winner", "&7Wager is optional and paid to the winner.")
        ), "NONE"));
        inv.setItem(22, button(Material.EMERALD, Lang.text("duel.pending-invites", "&ePending Invites"), List.of(
                Lang.text("duel.invites-sent-to-you", "&7Invites sent to you: &e{0}", incoming(player)),
                Lang.text("duel.use-duel-accept", "&7Use &f/duel accept <player>&7.")
        ), "NONE"));
        inv.setItem(24, button(Material.IRON_SWORD, Lang.text("duel.arenas", "&bArenas"), List.of(
                Lang.text("duel.ready-arenas", "&7Ready arenas: &e{0}", readyArenaCount()),
                Lang.text("duel.admins-duel-arena-set-1-2", "&7Admins: &f/duel arena set <id> 1|2")
        ), "NONE"));
        int slot = 37;
        for (String arena : arenas()) {
            inv.setItem(slot++, button(Material.BEACON, Lang.text("duel.text", "&f{0}", arena), List.of(
                    readyArena(arena) ? Lang.text("duel.ready", "&aReady") : Lang.text("duel.needs-spawn-1-and-spawn-2", "&cNeeds spawn 1 and spawn 2"),
                    Lang.text("duel.admin-delete-duel-arena-delete", "&7Admin delete: &f/duel arena delete {0}", arena)
            ), "NONE"));
            if (slot >= 44) break;
        }
        player.openInventory(inv);
    }

    public void invite(Player challenger, Player target, double wager) {
        if (!Double.isFinite(wager) || wager < 0 || wager > 1.0e12
                || (wager > 0 && !plugin.getConfig().getBoolean("duels.allow-wagers", true))) {
            plugin.msg(challenger, Lang.text("duel.invalid-or-disabled-wager", "&cInvalid or disabled wager.")); return;
        }
        if (target == null || !challenger.canSee(target) || plugin.extensions().blocks(target.getUniqueId(), challenger.getUniqueId())) {
            plugin.msg(challenger, Lang.text("duel.player-unavailable", "&cPlayer unavailable.")); return;
        }
        if (challenger.equals(target)) {
            plugin.msg(challenger, Lang.text("duel.you-cannot-duel-yourself", "&cYou cannot duel yourself."));
            return;
        }
        if (inDuel(challenger) || inDuel(target)) {
            plugin.msg(challenger, Lang.text("duel.one-of-those-players-is-already-in-a-duel", "&cOne of those players is already in a duel."));
            return;
        }
        if (!plugin.economy().setting(target.getUniqueId(), "duel_requests")) {
            plugin.msg(challenger, Lang.text("duel.that-player-is-not-accepting-duel-requests", "&cThat player is not accepting duel requests."));
            return;
        }
        if (wager > plugin.economy().money(challenger.getUniqueId())) {
            plugin.msg(challenger, Lang.text("duel.you-do-not-have-enough-money-for-that-wager", "&cYou do not have enough money for that wager."));
            return;
        }
        invites.put(target.getUniqueId(), new DuelInvite(challenger.getUniqueId(), target.getUniqueId(), wager, System.currentTimeMillis()));
        plugin.msg(challenger, Lang.text("duel.sent-duel-request-to-for", "&aSent duel request to &e{0}&a for &e{1}&a.", target.getName(), Text.money(wager)));
        plugin.msg(target, Lang.text("duel.has-challenged-you-to-a-duel-for", "&e{0} &ahas challenged you to a duel for &e{1}&a.", challenger.getName(), Text.money(wager)));
        plugin.msg(target, Lang.text("duel.use-duel-accept-or-duel-deny", "&7Use &f/duel accept {0} &7or &f/duel deny {1}&7.", challenger.getName(), challenger.getName()));
        plugin.platform().playerNow(target, () -> com.donsup.compat.BukkitCompat.pling(target));
    }

    public void accept(Player target, String challengerName) {
        DuelInvite invite = invites.get(target.getUniqueId());
        Player challenger = challengerName == null || challengerName.isBlank() ? null : Bukkit.getPlayerExact(challengerName);
        if (invite == null || challenger == null || !invite.challenger().equals(challenger.getUniqueId())) {
            plugin.msg(target, Lang.text("duel.no-matching-duel-invite", "&cNo matching duel invite."));
            return;
        }
        if (expired(invite)) {
            invites.remove(target.getUniqueId());
            plugin.msg(target, Lang.text("duel.that-duel-invite-expired", "&cThat duel invite expired."));
            return;
        }
        if (inDuel(challenger) || inDuel(target) || (!plugin.platform().folia() && challenger.isDead()) || target.isDead()
                || plugin.travel().tagged(challenger) || plugin.travel().tagged(target)) {
            plugin.msg(target, Lang.text("duel.both-players-must-be-alive-out-of-combat-and-outside-a-duel", "&cBoth players must be alive, out of combat and outside a duel."));
            return;
        }
        String arena = firstReadyArena();
        if (arena == null) {
            plugin.msg(target, Lang.text("duel.no-free-duel-arena-is-ready-ask-an-admin-to-set-one", "&cNo free duel arena is ready. Ask an admin to set one."));
            return;
        }
        start(challenger, target, arena, invite.wager() * 2.0);
        invites.remove(target.getUniqueId());
    }

    public void deny(Player target, String challengerName) {
        DuelInvite invite = invites.get(target.getUniqueId());
        if (invite == null) {
            plugin.msg(target, Lang.text("duel.no-duel-invite-to-deny", "&cNo duel invite to deny."));
            return;
        }
        if (challengerName != null && !challengerName.isBlank()) {
            Player named = Bukkit.getPlayerExact(challengerName);
            if (named == null || !named.getUniqueId().equals(invite.challenger())) {
                plugin.msg(target, Lang.text("duel.no-matching-duel-invite", "&cNo matching duel invite.")); return;
            }
        }
        invites.remove(target.getUniqueId());
        Player challenger = Bukkit.getPlayer(invite.challenger());
        if (challenger != null) plugin.msg(challenger, Lang.text("duel.denied-your-duel-request", "&c{0} denied your duel request.", target.getName()));
        plugin.msg(target, Lang.text("duel.denied-duel-request", "&cDenied duel request."));
    }

    public void leave(Player player) {
        ActiveDuel duel = active.get(player.getUniqueId());
        if (duel == null) {
            plugin.msg(player, Lang.text("duel.you-are-not-in-a-duel", "&cYou are not in a duel."));
            return;
        }
        Player other = Bukkit.getPlayer(duel.opponent(player.getUniqueId()));
        finish(other, player, "forfeit");
    }

    public void setArenaSpawn(Player player, String arena, int point) {
        arena = clean(arena);
        if (arena.isBlank() || arena.length() > 32 || occupied(arena)) { plugin.msg(player, Lang.text("duel.invalid-or-occupied-arena", "&cInvalid or occupied arena.")); return; }
        if (point != 1 && point != 2) {
            plugin.msg(player, Lang.text("duel.arena-point-must-be-1-or-2", "&cArena point must be 1 or 2."));
            return;
        }
        writeLocation("arenas." + arena + ".spawn" + point, player.getLocation());
        save();
        plugin.msg(player, Lang.text("duel.set-duel-arena-spawn", "&aSet duel arena &e{0} &aspawn &e{1}&a.", arena, point));
    }

    public void deleteArena(Player player, String arena) {
        arena = clean(arena);
        if (arena.isBlank() || occupied(arena)) { plugin.msg(player, Lang.text("duel.invalid-or-occupied-arena", "&cInvalid or occupied arena.")); return; }
        data.set("arenas." + arena, null);
        save();
        plugin.msg(player, Lang.text("duel.deleted-duel-arena", "&cDeleted duel arena &e{0}&c.", arena));
    }

    private void start(Player a, Player b, String arena, double pot) {
        if(plugin.platform().folia()){startRegionDuel(a,b,arena,pot);return;}
        Location spawn1 = readLocation("arenas." + arena + ".spawn1");
        Location spawn2 = readLocation("arenas." + arena + ".spawn2");
        if (spawn1 == null || spawn2 == null) return;
        ActiveDuel duel = new ActiveDuel(UUID.randomUUID(), a.getUniqueId(), b.getUniqueId(), a.getLocation(), b.getLocation(), pot, arena);
        if (!plugin.economy().reserveDuel(duel.id(), duel.a(), duel.b(), pot / 2)) {
            plugin.msg(a, Lang.text("duel.duel-cancelled-both-players-must-afford-the-wager-and-payment-mus", "&cDuel cancelled: both players must afford the wager and payment must save."));
            plugin.msg(b, Lang.text("duel.duel-cancelled-both-players-must-afford-the-wager-and-payment-mus", "&cDuel cancelled: both players must afford the wager and payment must save.")); return;
        }
        writeLocation("returns." + duel.a(), duel.returnA());
        writeLocation("returns." + duel.b(), duel.returnB());
        save();
        if (!a.teleport(spawn1) || !b.teleport(spawn2)) {
            plugin.economy().settleDuel(duel.id(), null);
            returnPlayer(a); returnPlayer(b);
            plugin.msg(a, Lang.text("duel.duel-cancelled-because-a-teleport-was-blocked", "&cDuel cancelled because a teleport was blocked."));
            plugin.msg(b, Lang.text("duel.duel-cancelled-because-a-teleport-was-blocked", "&cDuel cancelled because a teleport was blocked.")); return;
        }
        active.put(a.getUniqueId(), duel);
        active.put(b.getUniqueId(), duel);
        a.setHealth(Math.min(a.getMaxHealth(), 20.0));
        b.setHealth(Math.min(b.getMaxHealth(), 20.0));
        a.setFoodLevel(20);
        b.setFoodLevel(20);
        plugin.msg(a, Lang.text("duel.duel-started-against", "&cDuel started against &e{0}&c.", b.getName()));
        plugin.msg(b, Lang.text("duel.duel-started-against", "&cDuel started against &e{0}&c.", a.getName()));
    }

    private void finish(Player winner, Player loser, String reason) {
        if (winner == null && loser == null) return;
        UUID key = winner != null ? winner.getUniqueId() : loser.getUniqueId();
        ActiveDuel duel = active.remove(key);
        if (duel == null) return;
        active.remove(duel.a());
        active.remove(duel.b());
        if (!plugin.economy().settleDuel(duel.id(), winner == null ? null : winner.getUniqueId())) {
            plugin.getLogger().severe("Duel " + duel.id() + " could not settle. Its escrow remains for recovery.");
            if (winner != null) plugin.msg(winner, Lang.text("duel.your-wager-payment-could-not-be-saved-contact-staff-the-escrow-is", "&cYour wager payment could not be saved. Contact staff; the escrow is retained."));
        }
        if (winner != null) plugin.travel().clearCombat(winner);
        if (loser != null) plugin.travel().clearCombat(loser);
        if (winner != null) {
            plugin.economy().incrementStat(winner.getUniqueId(), "duel_wins", 1);
            plugin.msg(winner, Lang.text("duel.you-won-the-duel-by-pot", "&aYou won the duel by &e{0}&a. Pot: &e{1}&a.", reason, Text.money(duel.pot())));
        }
        if (loser != null) {
            plugin.economy().incrementStat(loser.getUniqueId(), "duel_losses", 1);
            plugin.msg(loser, Lang.text("duel.you-lost-the-duel-by", "&cYou lost the duel by &e{0}&c.", reason));
        }
        plugin.platform().globalLater(() -> {
            if (winner != null) plugin.platform().player(winner, () -> { if(winner.isOnline() && !winner.isDead()) returnPlayer(winner); });
            if (loser != null) plugin.platform().player(loser, () -> { if(loser.isOnline() && !loser.isDead()) returnPlayer(loser); });
        }, 40L);
    }

    @EventHandler
    public void onDamage(EntityDamageByEntityEvent event) {
        if (!(event.getEntity() instanceof Player victim) || !(com.donsup.compat.BukkitCompat.attacker(event) instanceof Player attacker)) return;
        if (entering.contains(victim.getUniqueId()) || entering.contains(attacker.getUniqueId())) {
            event.setCancelled(true);
            return;
        }
        ActiveDuel victimDuel = active.get(victim.getUniqueId());
        ActiveDuel attackerDuel = active.get(attacker.getUniqueId());
        if (victimDuel == null && attackerDuel == null) return;
        if (victimDuel == null || attackerDuel == null || victimDuel != attackerDuel || !victimDuel.opponent(attacker.getUniqueId()).equals(victim.getUniqueId())) {
            event.setCancelled(true);
            plugin.msg(attacker, Lang.text("duel.that-player-is-not-your-duel-opponent", "&cThat player is not your duel opponent."));
        }
    }

    @EventHandler
    public void onDeath(PlayerDeathEvent event) {
        Player loser = event.getEntity();
        ActiveDuel duel = active.get(loser.getUniqueId());
        if (duel == null) return;
        Player winner = Bukkit.getPlayer(duel.opponent(loser.getUniqueId()));
        finish(winner, loser, "kill");
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        UUID id = event.getPlayer().getUniqueId();
        entering.remove(id);
        invites.values().removeIf(invite -> invite.challenger().equals(id) || invite.target().equals(id));
        if (!active.containsKey(event.getPlayer().getUniqueId())) return;
        leave(event.getPlayer());
    }

    @EventHandler public void onJoin(PlayerJoinEvent event) {
        plugin.platform().player(event.getPlayer(), () -> { if (event.getPlayer().isOnline()) returnPlayer(event.getPlayer()); });
    }

    @EventHandler public void onRespawn(PlayerRespawnEvent event) {
        Location destination = readLocation("returns." + event.getPlayer().getUniqueId());
        if (destination != null) {
            event.setRespawnLocation(destination);
            data.set("returns." + event.getPlayer().getUniqueId(), null); save();
        }
    }

    private void returnPlayer(Player player) {
        String key = "returns." + player.getUniqueId();
        Location destination = readLocation(key);
        if(destination==null)return;
        if(plugin.platform().folia()){
            plugin.platform().teleport(player,destination).whenComplete((ok,error) -> plugin.platform().global(() -> {
                if(error==null && Boolean.TRUE.equals(ok) && destination.equals(readLocation(key))){data.set(key,null);save();}
            }));
        } else if(player.teleport(destination)){data.set(key,null);save();}
    }

    public void shutdown() {
        for (ActiveDuel duel : new java.util.HashSet<>(active.values())) {
            active.remove(duel.a()); active.remove(duel.b());
            plugin.economy().settleDuel(duel.id(), null);
            for (UUID id : List.of(duel.a(), duel.b())) {
                Player player = Bukkit.getPlayer(id);
                if (!plugin.platform().folia() && player != null && !player.isDead()) { plugin.travel().clearCombat(player); returnPlayer(player); }
            }
        }
        invites.clear(); save();
    }

    @EventHandler
    public void onClick(InventoryClickEvent event) {
        if (!com.donsup.gui.OwnedInventory.buttonClick(event)) return;
        if (!com.donsup.gui.OwnedInventory.title(event.getView()).equals(TITLE)) return;
        event.setCancelled(true);
    }

    private boolean expired(DuelInvite invite) {
        return System.currentTimeMillis() - invite.createdAt() > Math.max(1, Math.min(600, plugin.getConfig().getLong("duels.invite-timeout-seconds", 60))) * 1000L;
    }

    private int incoming(Player player) {
        return invites.containsKey(player.getUniqueId()) ? 1 : 0;
    }

    public boolean inDuel(Player player) {
        return active.containsKey(player.getUniqueId()) || entering.contains(player.getUniqueId());
    }

    public boolean opponents(Player a, Player b) {
        ActiveDuel duel = active.get(a.getUniqueId());
        return duel != null && duel.opponent(a.getUniqueId()).equals(b.getUniqueId());
    }

    private List<String> arenas() {
        ConfigurationSection section = data.getConfigurationSection("arenas");
        return section == null ? List.of() : List.copyOf(section.getKeys(false));
    }

    private int readyArenaCount() {
        int count = 0;
        for (String arena : arenas()) if (readyArena(arena)) count++;
        return count;
    }

    private String firstReadyArena() {
        for (String arena : arenas()) if (readyArena(arena) && !occupied(arena)) return arena;
        return null;
    }

    private boolean readyArena(String arena) {
        return readLocation("arenas." + arena + ".spawn1") != null && readLocation("arenas." + arena + ".spawn2") != null;
    }

    private boolean occupied(String arena) { return enteringArenas.contains(arena) || active.values().stream().anyMatch(duel -> duel.arena().equals(arena)); }

    private void writeLocation(String path, Location loc) {
        data.set(path + ".world", loc.getWorld().getName());
        data.set(path + ".x", loc.getX());
        data.set(path + ".y", loc.getY());
        data.set(path + ".z", loc.getZ());
        data.set(path + ".yaw", loc.getYaw());
        data.set(path + ".pitch", loc.getPitch());
    }

    private Location readLocation(String path) {
        String world = data.getString(path + ".world");
        if (world == null || Bukkit.getWorld(world) == null) return null;
        return new Location(Bukkit.getWorld(world), data.getDouble(path + ".x"), data.getDouble(path + ".y"), data.getDouble(path + ".z"), (float) data.getDouble(path + ".yaw"), (float) data.getDouble(path + ".pitch"));
    }

    private void fill(Inventory inv) {
        ItemStack glass = button(com.donsup.compat.Materials.GRAY_STAINED_GLASS_PANE, " ", List.of(), "NONE");
        for (int i = 0; i < inv.getSize(); i++) inv.setItem(i, glass);
    }

    private ItemStack button(Material material, String name, List<String> lore, String action) {
        return plugin.button(material, name, lore, actionKey, action);
    }

    private String clean(String input) {
        return input == null ? "arena" : input.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9_-]", "");
    }

    private record DuelInvite(UUID challenger, UUID target, double wager, long createdAt) {}

    private record ActiveDuel(UUID id, UUID a, UUID b, Location returnA, Location returnB, double pot, String arena) {
        UUID opponent(UUID uuid) {
            return uuid.equals(a) ? b : a;
        }

        Location returnFor(UUID uuid) {
            return uuid.equals(a) ? returnA : returnB;
        }
    }
}


===== src/main/java/com/donsup/economy/EconomyManager.java =====

package com.donsup.economy;

import com.donsup.DonsupPlugin;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.OfflinePlayer;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.LinkedHashMap;
import java.util.Comparator;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

public class EconomyManager {
    private final DonsupPlugin plugin;
    private final File file;
    private FileConfiguration data;

    public EconomyManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.file = new File(plugin.getDataFolder(), "players.yml");
        reload();
        ConfigurationSection escrows = data.getConfigurationSection("duel-escrows");
        if (escrows != null) for (String id : new ArrayList<>(escrows.getKeys(false))) {
            if (!settleDuel(UUID.fromString(id), null)) throw new IllegalStateException("Could not refund interrupted duel " + id);
        }
    }

    public void reload() {
        this.data = com.donsup.util.SafeYaml.load(file);
    }
    /** Uses this plugin's known accounts; never performs a blocking name lookup. */
    public OfflinePlayer knownPlayer(String name) {
        Player online=Bukkit.getPlayerExact(name);
        if(online!=null)return online;
        var accounts=data.getConfigurationSection("players");
        if(accounts!=null)for(String id:accounts.getKeys(false)){
            if(name.equalsIgnoreCase(accounts.getString(id+".name",""))){
                try{return Bukkit.getOfflinePlayer(UUID.fromString(id));}catch(IllegalArgumentException ignored){}
            }
        }
        return null;
    }

    public void save() {
        try {
            com.donsup.util.SafeYaml.save(data, file);
        } catch (IOException ex) {
            plugin.getLogger().warning("Could not save players.yml: " + ex.getMessage());
        }
    }

    public void ensure(Player player) {
        String path = playerPath(player.getUniqueId());
        if (!data.contains(path + ".money")) {
            data.set(path + ".name", player.getName());
            data.set(path + ".money", plugin.getConfig().getDouble("settings.starting-money", 1000));
            data.set(path + ".shards", plugin.getConfig().getInt("settings.starting-shards", 0));
            data.set(path + ".sell-multiplier", 1.0);
            seedDefaultSettings(player.getUniqueId());
            save();
        }
        if (!data.contains(path + ".settings.public_chat")) {
            seedDefaultSettings(player.getUniqueId());
            save();
        }
    }

    public double money(UUID uuid) {
        return data.getDouble(playerPath(uuid) + ".money", plugin.getConfig().getDouble("settings.starting-money", 1000));
    }

    public int shards(UUID uuid) {
        return data.getInt(playerPath(uuid) + ".shards", plugin.getConfig().getInt("settings.starting-shards", 0));
    }

    public double sellMultiplier(UUID uuid) {
        return Math.max(0.0, data.getDouble(playerPath(uuid) + ".sell-multiplier", 1.0));
    }

    public double effectiveSellMultiplier(Player player) {
        double value = sellMultiplier(player.getUniqueId());
        if (premium(player)) {
            value *= plugin.getConfig().getDouble("settings.premium-sell-multiplier", 1.25);
        }
        return value;
    }

    public void setSellMultiplier(UUID uuid, double value) {
        if (!Double.isFinite(value) || value < 0) return;
        data.set(playerPath(uuid) + ".sell-multiplier", value);
        save();
    }

    public synchronized void deposit(UUID uuid, double amount) {
        if (!Double.isFinite(amount) || amount < 0 || !Double.isFinite(money(uuid) + amount)) return;
        if (!commitMoney(Map.of(playerPath(uuid) + ".money", money(uuid) + amount)))
            throw new IllegalStateException("Money credit could not be saved");
    }

    public synchronized boolean withdraw(UUID uuid, double amount) {
        if (!Double.isFinite(amount) || amount < 0 || !Double.isFinite(money(uuid)) || money(uuid) < amount) {
            return false;
        }
        return commitMoney(Map.of(playerPath(uuid) + ".money", money(uuid) - amount));
    }

    public synchronized void addShards(UUID uuid, int amount) {
        if (amount < 0 || (long) shards(uuid) + amount > Integer.MAX_VALUE) return;
        if (!commitMoney(Map.of(playerPath(uuid) + ".shards", shards(uuid) + amount)))
            throw new IllegalStateException("Shard credit could not be saved");
    }

    public synchronized boolean takeShards(UUID uuid, int amount) {
        if (amount < 0 || shards(uuid) < amount) {
            return false;
        }
        return commitMoney(Map.of(playerPath(uuid) + ".shards", shards(uuid) - amount));
    }

    /** A crate claim can retry after a process crash without crediting either currency twice. */
    public synchronized boolean creditReward(String transaction, UUID uuid, double money, int shards) {
        if (transaction == null || !transaction.matches("[0-9a-f-]{36}") || !Double.isFinite(money) || money < 0 || shards < 0) return false;
        String path = "reward-payments." + transaction;
        ConfigurationSection receipt = data.getConfigurationSection(path);
        if (receipt != null) return uuid.toString().equals(receipt.getString("player"))
                && money == receipt.getDouble("money") && shards == receipt.getInt("shards");
        if (!Double.isFinite(money(uuid) + money) || (long)shards(uuid) + shards > Integer.MAX_VALUE) return false;
        return commitMoney(Map.of(playerPath(uuid) + ".money", money(uuid) + money,
                playerPath(uuid) + ".shards", shards(uuid) + shards,
                path, Map.of("player", uuid.toString(), "money", money, "shards", shards)));
    }
    public synchronized boolean forgetRewardPayment(String transaction) {
        if (transaction == null || !transaction.matches("[0-9a-f-]{36}")) return false;
        Map<String, Object> change = new LinkedHashMap<>(); change.put("reward-payments." + transaction, null);
        return commitMoney(change);
    }

    /** Save both reward currencies together; a failed write restores the live values. */
    public synchronized boolean creditReward(UUID uuid, double money, int shards) {
        if (!Double.isFinite(money) || money < 0 || shards < 0
                || !Double.isFinite(money(uuid) + money) || (long) shards(uuid) + shards > Integer.MAX_VALUE) return false;
        return commitMoney(Map.of(playerPath(uuid) + ".money", money(uuid) + money,
                playerPath(uuid) + ".shards", shards(uuid) + shards));
    }

    /** Receipt and both balances are committed together for interrupted shop review. */
    public synchronized boolean payShop(String transaction, UUID payer, UUID payee, double amount) {
        if (transaction == null || !transaction.matches("[0-9a-f-]{36}") || payer.equals(payee)
                || !Double.isFinite(amount) || amount <= 0 || amount > 1e9) return false;
        String path = "shop-payments." + transaction;
        ConfigurationSection receipt = data.getConfigurationSection(path);
        if (receipt != null) return !receipt.getBoolean("refunded") && payer.toString().equals(receipt.getString("payer"))
                && payee.toString().equals(receipt.getString("payee")) && amount == receipt.getDouble("amount");
        double from = money(payer), to = money(payee);
        if (!Double.isFinite(from) || !Double.isFinite(to) || from < amount || !Double.isFinite(to + amount)) return false;
        return commitMoney(Map.of(playerPath(payer) + ".money", from - amount, playerPath(payee) + ".money", to + amount,
                path, Map.of("payer", payer.toString(), "payee", payee.toString(), "amount", amount)));
    }
    public synchronized boolean forgetShopPayment(String transaction) {
        if (transaction == null || !transaction.matches("[0-9a-f-]{36}")) return false;
        Map<String, Object> change = new LinkedHashMap<>(); change.put("shop-payments." + transaction, null);
        return commitMoney(change);
    }
    /** Used only for a journal that proves item delivery never started. Refund and receipt are atomic. */
    public synchronized boolean refundUnstartedShop(String transaction) {
        if (transaction == null || !transaction.matches("[0-9a-f-]{36}")) return false;
        String path = "shop-payments." + transaction;
        ConfigurationSection receipt = data.getConfigurationSection(path);
        if (receipt == null || receipt.getBoolean("refunded")) return true;
        UUID payer = UUID.fromString(receipt.getString("payer")), payee = UUID.fromString(receipt.getString("payee"));
        double amount = receipt.getDouble("amount");
        if (!Double.isFinite(amount) || amount <= 0 || !Double.isFinite(money(payee)) || money(payee) < amount || !Double.isFinite(money(payer) + amount)) return false;
        return commitMoney(Map.of(playerPath(payer) + ".money", money(payer) + amount,
                playerPath(payee) + ".money", money(payee) - amount, path + ".refunded", true));
    }

    /** Validates both offers, commits all four balances once, and restores memory on disk failure. */
    public synchronized boolean exchange(UUID a, UUID b, double offeredA, double offeredB, int shardsA, int shardsB) {
        if (a.equals(b) || !Double.isFinite(offeredA) || !Double.isFinite(offeredB)
                || offeredA < 0 || offeredB < 0 || shardsA < 0 || shardsB < 0) return false;
        double balanceA = money(a), balanceB = money(b);
        int oldShardsA = shards(a), oldShardsB = shards(b);
        if (!Double.isFinite(balanceA) || !Double.isFinite(balanceB)
                || balanceA < offeredA || balanceB < offeredB || oldShardsA < shardsA || oldShardsB < shardsB) return false;
        double nextA = balanceA - offeredA + offeredB, nextB = balanceB - offeredB + offeredA;
        long nextShardsA = (long) oldShardsA - shardsA + shardsB, nextShardsB = (long) oldShardsB - shardsB + shardsA;
        if (!Double.isFinite(nextA) || !Double.isFinite(nextB) || nextShardsA > Integer.MAX_VALUE || nextShardsB > Integer.MAX_VALUE) return false;
        Map<String, Object> previous = new LinkedHashMap<>();
        for (String path : List.of(playerPath(a) + ".money", playerPath(b) + ".money", playerPath(a) + ".shards", playerPath(b) + ".shards"))
            previous.put(path, data.get(path));
        data.set(playerPath(a) + ".money", nextA);
        data.set(playerPath(b) + ".money", nextB);
        data.set(playerPath(a) + ".shards", (int) nextShardsA);
        data.set(playerPath(b) + ".shards", (int) nextShardsB);
        try {
            com.donsup.util.SafeYaml.save(data,file);
            return true;
        } catch (IOException ex) {
            previous.forEach(data::set);
            plugin.getLogger().warning("Trade payment could not be saved: " + ex.getMessage());
            return false;
        }
    }

    /** Both stakes and their recovery record are saved in the same atomic file replacement. */
    public synchronized boolean reserveDuel(UUID id, UUID a, UUID b, double wager) {
        if (a.equals(b) || !Double.isFinite(wager) || wager < 0 || wager > 1.0e12
                || data.contains("duel-escrows." + id)) return false;
        double balanceA = money(a), balanceB = money(b);
        if (!Double.isFinite(balanceA) || !Double.isFinite(balanceB) || balanceA < wager || balanceB < wager) return false;
        Map<String, Object> changes = new LinkedHashMap<>();
        changes.put(playerPath(a) + ".money", balanceA - wager);
        changes.put(playerPath(b) + ".money", balanceB - wager);
        changes.put("duel-escrows." + id, Map.of("a", a.toString(), "b", b.toString(), "wager", wager));
        return commitMoney(changes);
    }

    /** Null winner refunds both players; removing escrow in the same commit makes settlement idempotent. */
    public synchronized boolean settleDuel(UUID id, UUID winner) {
        String key = "duel-escrows." + id;
        ConfigurationSection escrow = data.getConfigurationSection(key);
        if (escrow == null) return true;
        UUID a = UUID.fromString(escrow.getString("a")), b = UUID.fromString(escrow.getString("b"));
        double wager = escrow.getDouble("wager");
        if (winner != null && !winner.equals(a) && !winner.equals(b)) return false;
        double nextA = money(a) + (winner == null ? wager : winner.equals(a) ? wager * 2 : 0);
        double nextB = money(b) + (winner == null ? wager : winner.equals(b) ? wager * 2 : 0);
        if (!Double.isFinite(wager) || wager < 0 || !Double.isFinite(nextA) || !Double.isFinite(nextB)) return false;
        Map<String, Object> changes = new LinkedHashMap<>();
        changes.put(playerPath(a) + ".money", nextA);
        changes.put(playerPath(b) + ".money", nextB);
        changes.put(key, null);
        return commitMoney(changes);
    }

    private boolean commitMoney(Map<String, Object> changes) {
        Map<String, Object> previous = new LinkedHashMap<>();
        changes.forEach((key, value) -> {
            Object old = data.get(key);
            previous.put(key, old instanceof ConfigurationSection section ? new LinkedHashMap<>(section.getValues(false)) : old);
            assignMoneyValue(key, value);
        });
        try {
            com.donsup.util.SafeYaml.save(data, file);
            return true;
        } catch (IOException ex) {
            previous.forEach(this::assignMoneyValue);
            plugin.getLogger().severe("Economy transaction could not be saved: " + ex.getMessage());
            return false;
        }
    }

    private void assignMoneyValue(String key, Object value) {
        if (value instanceof Map<?, ?> map) data.createSection(key, map);
        else data.set(key, value);
    }

    public boolean premium(Player player) {
        return !rank(player).equals("member");
    }

    public String rank(Player player) {
        String saved = data.getLong(playerPath(player.getUniqueId()) + ".rank-until", 0L) > System.currentTimeMillis()
            ? data.getString(playerPath(player.getUniqueId()) + ".rank", "member") : "member";
        for (String rank : List.of("legend", "elite", "plus")) {
            if (player.hasPermission("donsup.rank." + rank) || saved.equals(rank)) return rank;
        }
        return player.hasPermission("donsup.premium") || data.getLong(playerPath(player.getUniqueId()) + ".premium-until", 0L) > System.currentTimeMillis() ? "plus" : "member";
    }

    public void setRank(UUID player, String rank, int days) {
        data.set(playerPath(player) + ".rank", rank);
        data.set(playerPath(player) + ".rank-until", System.currentTimeMillis() + days * 86400000L);
        save();
    }

    public long premiumUntil(UUID uuid) {
        return data.getLong(playerPath(uuid) + ".premium-until", 0L);
    }

    public void setPremium(UUID uuid, long durationMillis) {
        long current = Math.max(System.currentTimeMillis(), data.getLong(playerPath(uuid) + ".premium-until", 0L));
        data.set(playerPath(uuid) + ".premium-until", current + durationMillis);
        save();
    }

    public int homeLimit(Player player) {
        int limit = plugin.getConfig().getInt("settings.default-home-limit", 2);
        if (premium(player)) {
            limit += plugin.getConfig().getInt("ranks." + rank(player) + ".home-bonus", plugin.getConfig().getInt("settings.premium-home-bonus", 3));
        }
        return limit;
    }

    public boolean setting(UUID uuid, String key) {
        return data.getBoolean(playerPath(uuid) + ".settings." + key, plugin.getConfig().getBoolean("player-settings." + key, true));
    }

    public boolean toggleSetting(UUID uuid, String key) {
        boolean next = !setting(uuid, key);
        data.set(playerPath(uuid) + ".settings." + key, next);
        save();
        if (plugin.extensions() != null) plugin.extensions().refresh(uuid);
        return next;
    }

    public void setSettings(UUID uuid, Map<String, Boolean> values) {
        values.forEach((key, value) -> data.set(playerPath(uuid) + ".settings." + key, value));
        save();
        if (plugin.extensions() != null) plugin.extensions().refresh(uuid);
    }

    public Map<String, Boolean> settings(UUID uuid) {
        Map<String, Boolean> out = new LinkedHashMap<>();
        ConfigurationSection section = plugin.getConfig().getConfigurationSection("player-settings");
        if (section != null) {
            for (String key : section.getKeys(false)) {
                out.put(key, setting(uuid, key));
            }
        }
        return out;
    }

    public void incrementStat(UUID uuid, String key, int amount) {
        data.set(playerPath(uuid) + ".stats." + key, stat(uuid, key) + amount);
        save();
    }

    public int stat(UUID uuid, String key) {
        return data.getInt(playerPath(uuid) + ".stats." + key, 0);
    }

    public String playerName(UUID uuid) {
        return data.getString(playerPath(uuid) + ".name", Bukkit.getOfflinePlayer(uuid).getName() == null ? uuid.toString().substring(0, 8) : Bukkit.getOfflinePlayer(uuid).getName());
    }

    public Map<UUID, Double> topMoney(int limit) {
        return topDouble("money", limit);
    }

    public Map<UUID, Double> topShards(int limit) {
        return topDouble("shards", limit);
    }

    public Map<UUID, Double> topStat(String key, int limit) {
        Map<UUID, Double> result = new LinkedHashMap<>();
        ConfigurationSection section = data.getConfigurationSection("players");
        if (section == null) return result;
        section.getKeys(false).stream()
                .map(this::uuidOrNull)
                .filter(java.util.Objects::nonNull)
                .sorted(Comparator.comparingDouble((UUID uuid) -> stat(uuid, key)).reversed())
                .limit(limit)
                .forEach(uuid -> result.put(uuid, (double) stat(uuid, key)));
        return result;
    }

    public boolean cooldownReady(UUID uuid, String key, long cooldownMillis) {
        return System.currentTimeMillis() >= data.getLong(playerPath(uuid) + ".cooldowns." + key, 0L) + cooldownMillis;
    }

    public long cooldownRemaining(UUID uuid, String key, long cooldownMillis) {
        long expires = data.getLong(playerPath(uuid) + ".cooldowns." + key, 0L) + cooldownMillis;
        return Math.max(0L, expires - System.currentTimeMillis());
    }

    public void markCooldown(UUID uuid, String key) {
        data.set(playerPath(uuid) + ".cooldowns." + key, System.currentTimeMillis());
        save();
    }

    private Map<UUID, Double> topDouble(String key, int limit) {
        Map<UUID, Double> result = new LinkedHashMap<>();
        ConfigurationSection section = data.getConfigurationSection("players");
        if (section == null) return result;
        section.getKeys(false).stream()
                .map(this::uuidOrNull)
                .filter(java.util.Objects::nonNull)
                .sorted(Comparator.comparingDouble((UUID uuid) -> data.getDouble(playerPath(uuid) + "." + key, 0.0)).reversed())
                .limit(limit)
                .forEach(uuid -> result.put(uuid, data.getDouble(playerPath(uuid) + "." + key, 0.0)));
        return result;
    }

    private UUID uuidOrNull(String raw) {
        try {
            return UUID.fromString(raw);
        } catch (IllegalArgumentException ex) {
            return null;
        }
    }

    public double listingTaxPercent(Player player) {
        if (premium(player)) {
            return plugin.getConfig().getDouble("settings.premium-listing-tax-percent", 0.5);
        }
        return plugin.getConfig().getDouble("settings.listing-tax-percent", 2.5);
    }

    public int listingLimit(Player player, String type) {
        int base = plugin.getConfig().getInt(type.equals("auction") ? "settings.max-auction-listings" : "settings.max-market-listings", 18);
        return premium(player) ? base + plugin.getConfig().getInt("ranks." + rank(player) + ".listing-bonus", plugin.getConfig().getInt("settings.premium-listing-bonus", 18)) : base;
    }

    public List<ItemStack> vault(UUID uuid) {
        List<ItemStack> items = new ArrayList<>();
        List<?> raw = data.getList(playerPath(uuid) + ".premium-vault", List.of());
        for (Object entry : raw) {
            items.add(entry instanceof ItemStack stack ? stack : null);
        }
        return items;
    }

    public void setVault(UUID uuid, ItemStack[] contents) {
        data.set(playerPath(uuid) + ".premium-vault", new ArrayList<>(Arrays.asList(contents)));
        save();
    }

    public Set<String> homeNames(UUID uuid) {
        ConfigurationSection section = data.getConfigurationSection(playerPath(uuid) + ".homes");
        return section == null ? Set.of() : section.getKeys(false);
    }

    public boolean setHome(Player player, String name) {
        name = cleanHome(name);
        if (name.isBlank() || name.length() > 24) return false;
        if (!homeNames(player.getUniqueId()).contains(name) && homeNames(player.getUniqueId()).size() >= homeLimit(player)) {
            return false;
        }
        Location loc = player.getLocation();
        String path = playerPath(player.getUniqueId()) + ".homes." + cleanHome(name);
        data.set(path + ".world", loc.getWorld().getName());
        data.set(path + ".x", loc.getX());
        data.set(path + ".y", loc.getY());
        data.set(path + ".z", loc.getZ());
        data.set(path + ".yaw", loc.getYaw());
        data.set(path + ".pitch", loc.getPitch());
        save();
        return true;
    }

    public boolean deleteHome(UUID uuid, String name) {
        String path = playerPath(uuid) + ".homes." + cleanHome(name);
        if (!data.contains(path)) {
            return false;
        }
        data.set(path, null);
        save();
        return true;
    }

    public Location home(UUID uuid, String name) {
        String path = playerPath(uuid) + ".homes." + cleanHome(name);
        String world = data.getString(path + ".world");
        if (world == null || Bukkit.getWorld(world) == null) {
            return null;
        }
        return new Location(
                Bukkit.getWorld(world),
                data.getDouble(path + ".x"),
                data.getDouble(path + ".y"),
                data.getDouble(path + ".z"),
                (float) data.getDouble(path + ".yaw"),
                (float) data.getDouble(path + ".pitch")
        );
    }

    public void setBounty(UUID target, UUID issuer, double amount) {
        String path = "bounties." + target;
        data.set(path + ".issuer", issuer.toString());
        data.set(path + ".amount", data.getDouble(path + ".amount", 0.0) + amount);
        OfflinePlayer offline = Bukkit.getOfflinePlayer(target);
        data.set(path + ".target-name", offline.getName() == null ? target.toString() : offline.getName());
        save();
    }

    public double bounty(UUID target) {
        return data.getDouble("bounties." + target + ".amount", 0.0);
    }

    public void clearBounty(UUID target) {
        data.set("bounties." + target, null);
        save();
    }

    public Map<UUID, Double> bounties() {
        Map<UUID, Double> result = new LinkedHashMap<>();
        ConfigurationSection section = data.getConfigurationSection("bounties");
        if (section == null) {
            return result;
        }
        for (String key : section.getKeys(false)) {
            try {
                UUID uuid = UUID.fromString(key);
                double amount = section.getDouble(key + ".amount", 0.0);
                if (amount > 0) {
                    result.put(uuid, amount);
                }
            } catch (IllegalArgumentException ignored) {
            }
        }
        return result;
    }

    public String bountyName(UUID target) {
        return data.getString("bounties." + target + ".target-name", target.toString());
    }

    private void seedDefaultSettings(UUID uuid) {
        ConfigurationSection section = plugin.getConfig().getConfigurationSection("player-settings");
        if (section == null) {
            return;
        }
        String path = playerPath(uuid) + ".settings.";
        for (String key : section.getKeys(false)) {
            if (!data.contains(path + key)) {
                data.set(path + key, section.getBoolean(key));
            }
        }
    }

    private String cleanHome(String input) {
        return input == null ? "home" : input.toLowerCase().replaceAll("[^a-z0-9_-]", "");
    }

    private String playerPath(UUID uuid) {
        return "players." + uuid;
    }
}


===== src/main/java/com/donsup/features/PearlPreferences.java =====

package com.donsup.features;

import com.donsup.DonsupPlugin;
import com.donsup.compat.BukkitCompat;
import com.donsup.util.SafeYaml;
import org.bukkit.*;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.world.*;
import java.io.*;
import java.util.*;

/** Native pearl survival with per-player cleanup, including pearls reloaded from disk. */
public final class PearlPreferences implements Listener {
    private static final String PREFIX="donsup_pearl_epoch_";
    private final DonsupPlugin plugin;
    private final File file;
    private final org.bukkit.configuration.file.YamlConfiguration data;
    private final Map<UUID,Map<UUID,EnderPearl>> tracked=new HashMap<>();
    private final Map<UUID,String> rules=new HashMap<>();
    public PearlPreferences(DonsupPlugin plugin){
        this.plugin=plugin;file=new File(plugin.getDataFolder(),"pearl-preferences.yml");data=SafeYaml.load(file);
        if(enabled()){
            registerEntityLoads();
            for(World world:Bukkit.getWorlds()){
                configure(world);
                for(Chunk chunk:world.getLoadedChunks()){
                    int x=chunk.getX(),z=chunk.getZ();
                    plugin.platform().region(new Location(world,x*16,0,z*16),()->{
                        if(world.isChunkLoaded(x,z))for(Entity entity:world.getChunkAt(x,z).getEntities())if(entity instanceof EnderPearl pearl)track(pearl);
                    });
                }
            }
        }
    }
    /** Modern servers can load saved entities after ChunkLoadEvent has fired. */
    private void registerEntityLoads(){
        try{
            Class<? extends Event> type=Class.forName("org.bukkit.event.world.EntitiesLoadEvent").asSubclass(Event.class);
            Bukkit.getPluginManager().registerEvent(type,this,EventPriority.MONITOR,(listener,event)->{
                if(!type.isInstance(event))return;
                plugin.platform().locked(()->{
                    for(Object entity:(Iterable<?>)BukkitCompat.call(event,"getEntities"))if(entity instanceof EnderPearl pearl)track(pearl);
                });
            },plugin);
        }catch(ClassNotFoundException ignored){ /* Legacy servers use ChunkLoadEvent. */ }
    }
    private boolean enabled(){return plugin.getConfig().getBoolean("pearls.player-preferences",true);}
    public boolean supported(){return enabled()&&!rules.isEmpty();}
    private Object rule(World world,String rule,Boolean value){
        try {
            String method=value==null?"getGameRuleValue":"setGameRuleValue";
            Class<?>[] legacy=value==null?new Class<?>[]{String.class}:new Class<?>[]{String.class,String.class};
            if(BukkitCompat.method(World.class,method,legacy))return value==null?BukkitCompat.call(world,method,legacy,rule):BukkitCompat.call(world,method,legacy,rule,value.toString());
            Class<?> type=Class.forName("org.bukkit.GameRule");Object key=type.getMethod("getByName",String.class).invoke(null,rule);
            if(key==null)throw new IllegalStateException("Unknown native gamerule "+rule);
            return value==null?BukkitCompat.call(world,"getGameRuleValue",new Class<?>[]{type},key):BukkitCompat.call(world,"setGameRule",new Class<?>[]{type,Object.class},key,value);
        }catch(ReflectiveOperationException e){throw new IllegalStateException("Native pearl gamerule is unavailable",e);}
    }
    private void configure(World world){
        String rule=Arrays.stream(world.getGameRules()).filter(s->s.equals("enderPearlsVanishOnDeath")||s.equals("minecraft:ender_pearls_vanish_on_death")||s.equals("ender_pearls_vanish_on_death")).findFirst().orElse(null);
        if(rule==null)return;
        String path="world-rules."+world.getUID();
        if(!data.contains(path)){data.set(path,String.valueOf(rule(world,rule,null)));save();}
        if(Boolean.TRUE.equals(rule(world,rule,false)))rules.put(world.getUID(),rule);
    }
    private void save(){try{SafeYaml.save(data,file);}catch(IOException e){throw new IllegalStateException("Could not save pearl preferences",e);}}
    private UUID owner(EnderPearl pearl){
        if(pearl.getShooter() instanceof Player p)return p.getUniqueId();
        try{if(BukkitCompat.method(pearl.getClass(),"getOwnerUniqueId"))return (UUID)BukkitCompat.call(pearl,"getOwnerUniqueId");}catch(RuntimeException ignored){}
        return null;
    }
    @SuppressWarnings("unchecked") private Set<String> tags(EnderPearl pearl){return (Set<String>)BukkitCompat.call(pearl,"getScoreboardTags");}
    private long epoch(UUID owner){return data.getLong("deaths."+owner,0);}
    private void track(EnderPearl pearl){
        if(!enabled()||!rules.containsKey(pearl.getWorld().getUID()))return;
        UUID owner=owner(pearl);if(owner==null)return;
        Set<String> tags=tags(pearl);String current=PREFIX+epoch(owner);
        Optional<String> old=tags.stream().filter(t->t.startsWith(PREFIX)).findFirst();
        if(old.isPresent()&&!old.get().equals(current)){pearl.remove();return;}
        if(old.isEmpty())BukkitCompat.call(pearl,"addScoreboardTag",new Class<?>[]{String.class},current);
        tracked.computeIfAbsent(owner,k->new HashMap<>()).put(pearl.getUniqueId(),pearl);
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)public void launch(ProjectileLaunchEvent e){if(e.getEntity() instanceof EnderPearl pearl)track(pearl);}
    @EventHandler(priority=EventPriority.MONITOR)public void death(PlayerDeathEvent e){
        if(!supported()||plugin.economy().setting(e.getEntity().getUniqueId(),"keep_pearls_on_death"))return;
        UUID id=e.getEntity().getUniqueId();data.set("deaths."+id,epoch(id)+1);save();
        var pearls=tracked.remove(id);if(pearls!=null)for(EnderPearl pearl:pearls.values())plugin.platform().entity(pearl,pearl::remove);
    }
    @EventHandler(priority=EventPriority.MONITOR)public void load(WorldLoadEvent e){if(enabled())configure(e.getWorld());}
    @EventHandler(priority=EventPriority.MONITOR)public void load(ChunkLoadEvent e){if(enabled())for(Entity entity:e.getChunk().getEntities())if(entity instanceof EnderPearl pearl)track(pearl);}
    @EventHandler(priority=EventPriority.MONITOR)public void unload(ChunkUnloadEvent e){for(Entity entity:e.getChunk().getEntities())if(entity instanceof EnderPearl pearl)forget(pearl);}
    @EventHandler(priority=EventPriority.MONITOR)public void hit(ProjectileHitEvent e){if(e.getEntity() instanceof EnderPearl pearl)forget(pearl);}
    private void forget(EnderPearl pearl){UUID id=owner(pearl);var pearls=tracked.get(id);if(pearls!=null){pearls.remove(pearl.getUniqueId());if(pearls.isEmpty())tracked.remove(id);}}
    public void shutdown(){
        for(World world:Bukkit.getWorlds()){String rule=rules.get(world.getUID());if(rule!=null&&"false".equals(String.valueOf(rule(world,rule,null))))rule(world,rule,Boolean.parseBoolean(data.getString("world-rules."+world.getUID(),"true")));}
        tracked.clear();
    }
}


===== src/main/java/com/donsup/features/RegionRtp.java =====

package com.donsup.features;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.platform.TaskHandle;
import org.bukkit.*;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import java.util.*;
import java.util.concurrent.*;

/** Folia coordinator. World reads run at the destination; player checks/transfers run on entity schedulers. */
final class RegionRtp {
    private final DonsupPlugin plugin;
    private final RtpManager dimensions;
    private final RtpQueue queue=new RtpQueue();
    private final Map<UUID,Trip> trips=new HashMap<>();
    private final Map<String,Integer> tickets=new HashMap<>();
    private final Set<UUID> transferring=new HashSet<>();
    private int loads;
    private static final Set<Material> HAZARDS=com.donsup.compat.Materials.presentSet("MAGMA_BLOCK","MAGMA","CACTUS","CAMPFIRE","SOUL_CAMPFIRE","POWDER_SNOW","POINTED_DRIPSTONE");
    private static final class Trip {
        final List<UUID> ids;
        final World world;
        final String destination;
        final Map<UUID,Location> origins=new HashMap<>();
        final Map<UUID,Location> countdownOrigins=new HashMap<>();
        final Map<UUID,Location> targets=new HashMap<>();
        final Set<UUID> arrived=new HashSet<>();
        long expires=System.currentTimeMillis()+60000;
        boolean countdown,transit,cancelled,finished;
        String reason=Lang.text("region-rtp.rtp-cancelled", "RTP cancelled.");
        Location ticket;
        TaskHandle task=TaskHandle.NONE;
        Trip(List<UUID> ids,World world,String destination){this.ids=ids;this.world=world;this.destination=destination;}
    }
    RegionRtp(DonsupPlugin plugin,RtpManager dimensions){this.plugin=plugin;this.dimensions=dimensions;}
    private int capacity(){return Math.max(1,Math.min(16,plugin.getConfig().getInt("travel.max-concurrent-searches",8)));}
    private long active(){return trips.values().stream().distinct().count();}
    private boolean ready(Player p){
        if(!p.hasPermission("donsup.use")||!plugin.travel().available(p))return false;
        long duration=Math.max(1,Math.min(86400,plugin.getConfig().getLong("travel.rtp-cooldown-seconds",15)))*1000;
        if(!plugin.economy().cooldownReady(p.getUniqueId(),"rtp",duration)){plugin.msg(p,Lang.text("region-rtp.rtp-is-on-cooldown", "&cRTP is on cooldown."));return false;}
        return true;
    }
    private boolean occupied(Player p){
        if(queue.get(p.getUniqueId())==null&&!trips.containsKey(p.getUniqueId()))return false;
        plugin.msg(p,Lang.text("region-rtp.you-already-have-an-rtp-request-rtp-leave-to-cancel-it", "&eYou already have an RTP request. /rtp leave to cancel it."));return true;
    }
    void solo(Player p,String dimension){
        if(!ready(p)||occupied(p))return;
        World world=dimensions.world(dimension);
        if(world==null){plugin.msg(p,Lang.text("region-rtp.that-rtp-dimension-is-disabled-or-unavailable", "&cThat RTP dimension is disabled or unavailable."));return;}
        if(active()>=capacity()||loads>=capacity()){plugin.msg(p,Lang.text("region-rtp.rtp-searches-are-busy-try-again-shortly", "&cRTP searches are busy. Try again shortly."));return;}
        plugin.travel().cancelWarmup(p);start(List.of(p.getUniqueId()),world,dimension);
    }
    void join(Player p,String dimension){
        if(!plugin.getConfig().getBoolean("travel.queue.enabled",true)){plugin.msg(p,Lang.text("region-rtp.rtp-queues-are-disabled", "&cRTP queues are disabled."));return;}
        if(!p.hasPermission("donsup.rtp.queue")){plugin.msg(p,Lang.text("region-rtp.no-permission-for-rtp-queues", "&cNo permission for RTP queues."));return;}
        if(!ready(p)||occupied(p))return;
        if(dimensions.world(dimension)==null){plugin.msg(p,Lang.text("region-rtp.that-rtp-dimension-is-disabled-or-unavailable", "&cThat RTP dimension is disabled or unavailable."));return;}
        long timeout=Math.max(5,Math.min(3600,plugin.getConfig().getInt("travel.queue.timeout-seconds",120)))*1000L;
        if(!queue.add(p.getUniqueId(),dimension,System.currentTimeMillis()+timeout,Math.max(2,Math.min(2000,plugin.getConfig().getInt("travel.queue.max-players",200))))){plugin.msg(p,Lang.text("region-rtp.the-rtp-queue-is-full", "&cThe RTP queue is full."));return;}
        plugin.travel().cancelWarmup(p);plugin.msg(p,Lang.text("region-rtp.joined-the-rtp-queue-waiting-for-a-partner-rtp-leave-to-cancel", "&aJoined the {0} RTP queue. &7Waiting for a partner; /rtp leave to cancel.", plugin.travel().rtp().label(dimension)));match();
    }
    String status(Player p){
        var waiting=queue.get(p.getUniqueId());
        if(waiting!=null)return Lang.text("region-rtp.waiting-for-a-partner-in-rtp-leave-to-cancel", "Waiting for a partner in {0}. /rtp leave to cancel.", plugin.travel().rtp().label(waiting.dimension()));
        Trip trip=trips.get(p.getUniqueId());
        return trip==null?Lang.text("region-rtp.you-are-not-waiting-for-rtp", "You are not waiting for RTP."):trip.countdown?Lang.text("region-rtp.rtp-countdown-stay-still-rtp-leave-to-cancel", "RTP countdown: stay still. /rtp leave to cancel."):Lang.text("region-rtp.finding-a-safe-destination-rtp-leave-to-cancel", "Finding a safe destination. /rtp leave to cancel.");
    }
    void tick(){
        for(var entry:queue.expire(System.currentTimeMillis()))message(entry.player(),Lang.text("region-rtp.rtp-queue-timed-out-join-again-when-ready", "&7RTP queue timed out. Join again when ready."));
        for(Trip trip:new HashSet<>(trips.values()))if(trip.expires<=System.currentTimeMillis())cancel(trip.ids.getFirst(),Lang.text("region-rtp.rtp-request-timed-out", "RTP request timed out."));
        match();
    }
    private void match(){
        for(String dimension:dimensions.destinations())while(active()<capacity()&&loads<capacity()){
            var pair=queue.pair(dimension);if(pair.isEmpty())break;
            World world=dimensions.world(dimension);List<UUID> ids=pair.stream().map(RtpQueue.Entry::player).toList();
            if(world==null||!plugin.getConfig().getBoolean("travel.queue.enabled",true)){ids.forEach(id->message(id,Lang.text("region-rtp.rtp-dimension-or-queues-unavailable", "&cRTP dimension or queues unavailable.")));continue;}
            ids.forEach(id->message(id,Lang.text("region-rtp.partner-found-finding-a-safe-location-together", "&aPartner found! Finding a safe location together.")));start(ids,world,dimension);
        }
    }
    private void start(List<UUID> ids,World world,String destination){
        Trip trip=new Trip(ids,world,destination);ids.forEach(id->{trips.put(id,trip);message(id,Lang.text("region-rtp.finding-a-safe-wilderness-location", "&7Finding a safe wilderness location..."));});
        validate(trip,()->attempt(trip,0));
    }
    private boolean current(Trip trip){return !trip.finished&&!trip.cancelled&&trip.ids.stream().allMatch(id->trips.get(id)==trip);}
    private void validate(Trip trip,Runnable next){
        List<CompletableFuture<Boolean>> checks=new ArrayList<>();
        for(UUID id:trip.ids){
            Player p=Bukkit.getPlayer(id);if(p==null){cancel(id,Lang.text("region-rtp.rtp-cancelled-a-player-disconnected", "RTP cancelled: a player disconnected."));return;}
            checks.add(plugin.platform().onPlayer(p,()->{
                if(!current(trip)||!dimensions.allowed(p,trip.destination)||!ready(p)||(trip.ids.size()>1&&!p.hasPermission("donsup.rtp.queue")))trip.cancelled=true;
                else if (trip.countdown) {
                    Location before=trip.countdownOrigins.get(id),now=p.getLocation();
                    // Some Folia command teleports do not emit the usual movement/teleport events.
                    // Recheck on the entity's owner before any RTP transfer can begin.
                    if(before==null || !before.getWorld().equals(now.getWorld()) || before.distanceSquared(now)>0.0001)
                        cancel(id,Lang.text("region-rtp.rtp-cancelled-a-player-moved-or-teleported-during-the-countdown", "RTP cancelled: a player moved or teleported during the countdown."));
                } else trip.countdownOrigins.put(id,p.getLocation());
            }));
        }
        CompletableFuture.allOf(checks.toArray(CompletableFuture[]::new)).whenComplete((v,error)->plugin.platform().global(()->{
            if(error!=null||checks.stream().anyMatch(f->!Boolean.TRUE.equals(f.getNow(false))))trip.cancelled=true;
            if(!current(trip)){finish(trip,Lang.text("region-rtp.rtp-cancelled-a-player-became-unavailable", "RTP cancelled: a player became unavailable."));return;}
            next.run();
        }));
    }
    private void attempt(Trip trip,int attempt){
        if(!current(trip))return;
        if(attempt>=32||trip.expires<=System.currentTimeMillis()){finish(trip,Lang.text("region-rtp.no-safe-rtp-location-found-try-again", "No safe RTP location found. Try again."));return;}
        int[] sample;
        try { sample=dimensions.sample(trip.destination,trip.world,trip.ids.size()==2?8:0,true); }
        catch(IllegalArgumentException e){finish(trip,e.getMessage());return;}
        int x=sample[0],z=sample[1];
        Location anchor=new Location(trip.world,x,0,z);loads++;
        try{
            plugin.platform().chunk(trip.world,x>>4,z>>4).whenComplete((chunk,error)->plugin.platform().global(()->{
                loads--;
                if(!current(trip))return;
                if(error!=null){finish(trip,Lang.text("region-rtp.rtp-chunk-loading-failed", "RTP chunk loading failed."));return;}
                plugin.platform().region(anchor,()->{
                    if(!current(trip))return;
                    Location a=safeColumn(trip.world,x,z),b=trip.ids.size()==2?safeColumn(trip.world,x+8,z):a;
                    if(!dimensions.within(trip.destination,x,z,trip.ids.size()==2?8:0)||a==null||b==null||Math.abs(a.getY()-b.getY())>6){plugin.platform().global(()->attempt(trip,attempt+1));return;}
                    String key=ticketKey(anchor);
                    if(!tickets.containsKey(key)) com.donsup.compat.BukkitCompat.ticket(trip.world, x>>4,z>>4,plugin, true);
                    tickets.merge(key,1,Integer::sum);trip.ticket=anchor;
                    trip.targets.put(trip.ids.getFirst(),a);if(trip.ids.size()==2)trip.targets.put(trip.ids.get(1),b);
                    validate(trip,()->{
                        int seconds=Math.max(0,Math.min(60,plugin.getConfig().getInt("travel.warmup-seconds",3)));
                        trip.countdown=true;trip.expires=System.currentTimeMillis()+seconds*1000L+30000;
                        trip.ids.forEach(id->message(id,Lang.text("region-rtp.rtp-in-seconds-stay-still-moving-cancels-the-whole-match", "&7RTP in {0} seconds. Stay still; moving cancels the whole match.", seconds)));
                        trip.task=plugin.platform().globalLater(()->arrive(trip),Math.max(1,seconds*20L));
                    });
                });
            }));
        }catch(RuntimeException ex){loads--;finish(trip,Lang.text("region-rtp.rtp-chunk-loading-failed", "RTP chunk loading failed."));}
    }
    private Location safeColumn(World world,int x,int z){
        int top=world.getEnvironment()==World.Environment.NETHER?Math.min(world.getMaxHeight()-3,com.donsup.compat.BukkitCompat.minHeight(world)+com.donsup.compat.BukkitCompat.logicalHeight(world)-3):Math.min(world.getMaxHeight()-3,com.donsup.compat.BukkitCompat.highest(world, x, z));
        for(int y=top;y>com.donsup.compat.BukkitCompat.minHeight(world);y--){
            Location at=new Location(world,x+.5,y+1,z+.5);
            if(safe(at))return at;
            if(world.getEnvironment()!=World.Environment.NETHER)return null;
        }return null;
    }
    private boolean safe(Location at){
        World world=at.getWorld();if(!com.donsup.compat.BukkitCompat.inside(world.getWorldBorder(), at))return false;
        Location spawn=world.getSpawnLocation();if(Math.pow(at.getX()-spawn.getX(),2)+Math.pow(at.getZ()-spawn.getZ(),2)<4096)return false;
        Block feet=at.getBlock(),ground=feet.getRelative(0,-1,0);
        return ground.getType().isSolid()&&!HAZARDS.contains(ground.getType())&&com.donsup.compat.BukkitCompat.fullHeight(ground)&&com.donsup.compat.BukkitCompat.air(feet.getType())&&com.donsup.compat.BukkitCompat.air(feet.getRelative(0,1,0).getType());
    }
    private void arrive(Trip trip){
        if(!current(trip))return;
        validate(trip,()->plugin.platform().region(trip.ticket,()->{
            if(!current(trip))return;
            if(trip.targets.values().stream().anyMatch(at->!safe(at))){finish(trip,Lang.text("region-rtp.rtp-cancelled-destination-became-unsafe", "RTP cancelled: destination became unsafe."));return;}
            trip.transit=true;trip.countdown=false;
            List<CompletableFuture<Boolean>> transfers=new ArrayList<>();
            for(UUID id:trip.ids){
                Player p=Bukkit.getPlayer(id);CompletableFuture<Boolean> result=new CompletableFuture<>();transfers.add(result);
                if(p==null){result.complete(false);continue;}
                plugin.platform().onPlayer(p,()->{
                    if(!current(trip)||!ready(p)){result.complete(false);return;}
                    trip.origins.put(id,p.getLocation());transferring.add(id);
                    try{plugin.platform().teleport(p,trip.targets.get(id)).whenComplete((ok,error)->plugin.platform().global(()->{
                        transferring.remove(id);if(Boolean.TRUE.equals(ok))trip.arrived.add(id);result.complete(error==null&&Boolean.TRUE.equals(ok));
                    }));}catch(RuntimeException ex){transferring.remove(id);result.complete(false);}
                }).whenComplete((ran,error)->{if(error!=null||!Boolean.TRUE.equals(ran))result.complete(false);});
            }
            CompletableFuture.allOf(transfers.toArray(CompletableFuture[]::new)).whenComplete((v,error)->plugin.platform().global(()->{
                trip.transit=false;
                if(!trip.cancelled&&error==null&&transfers.stream().allMatch(f->Boolean.TRUE.equals(f.getNow(false)))){
                    trip.ids.forEach(id->plugin.economy().markCooldown(id,"rtp"));finish(trip,trip.ids.size()==2?Lang.text("region-rtp.rtp-complete-your-partner-is-nearby", "RTP complete. Your partner is nearby."):Lang.text("region-rtp.rtp-complete", "RTP complete."));
                }else rollback(trip);
            }));
        }));
    }
    private void rollback(Trip trip){
        for(UUID id:trip.arrived){
            Player p=Bukkit.getPlayer(id);Location origin=trip.origins.get(id);
            if(p==null||origin==null){plugin.getLogger().warning("RTP return requires staff review for "+id+" to "+origin);continue;}
            plugin.platform().onPlayer(p,()->{
                transferring.add(id);
                try { plugin.platform().teleport(p,origin).whenComplete((ok,error)->plugin.platform().global(()->{
                    transferring.remove(id);
                    if(error!=null||!Boolean.TRUE.equals(ok)){message(id,Lang.text("region-rtp.your-return-was-blocked-contact-staff", "&cYour return was blocked. Contact staff."));plugin.getLogger().warning("RTP return blocked for "+id+" to "+origin);}
                })); } catch(RuntimeException ex) {
                    transferring.remove(id);
                    plugin.getLogger().warning("RTP return failed for "+id+" to "+origin+": "+ex.getMessage());
                }
            }).whenComplete((ran,error)-> {
                if(error!=null || !Boolean.TRUE.equals(ran))plugin.platform().global(()-> {
                    transferring.remove(id);
                    plugin.getLogger().warning("RTP return requires staff review for "+id+" to "+origin);
                });
            });
        }
        finish(trip,Lang.text("region-rtp.rtp-cancelled-no-cooldown-was-charged", "RTP cancelled. No cooldown was charged."));
    }
    void moved(Player p){Trip t=trips.get(p.getUniqueId());if(t!=null&&t.countdown&&!transferring.contains(p.getUniqueId()))cancel(p.getUniqueId(),Lang.text("region-rtp.rtp-cancelled-a-player-moved-during-the-countdown", "RTP cancelled: a player moved during the countdown."));}
    void externalTeleport(Player p){if(!transferring.contains(p.getUniqueId()))cancel(p.getUniqueId(),Lang.text("region-rtp.rtp-cancelled-because-a-player-teleported", "RTP cancelled because a player teleported."));}
    boolean cancel(UUID id,String reason){
        Trip trip=trips.get(id);
        if(trip!=null){trip.cancelled=true;trip.reason=reason;if(!trip.transit)finish(trip,reason);return true;}
        if(queue.remove(id)!=null){message(id,"&7"+reason);return true;}return false;
    }
    private String ticketKey(Location at){return at.getWorld().getUID()+":"+((int)at.getX()>>4)+":"+((int)at.getZ()>>4);}
    private void finish(Trip trip,String reason){
        if(trip.finished)return;trip.finished=true;trip.task.cancel();
        trip.ids.forEach(id->{trips.remove(id,trip);message(id,"&7"+reason);});
        if(trip.ticket!=null){Location anchor=trip.ticket;trip.ticket=null;plugin.platform().region(anchor,()->{
            String key=ticketKey(anchor);int count=tickets.getOrDefault(key,0);
            if(count>1)tickets.put(key,count-1);else{tickets.remove(key);com.donsup.compat.BukkitCompat.ticket(anchor.getWorld(), anchor.getBlockX()>>4,anchor.getBlockZ()>>4,plugin, false);}
        });}
    }
    private void message(UUID id,String message){Player p=Bukkit.getPlayer(id);if(p!=null)plugin.msg(p,message);}
    void shutdown(){trips.clear();queue.clear();tickets.clear();transferring.clear();}
}


===== src/main/java/com/donsup/features/RtpManager.java =====

package com.donsup.features;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import org.bukkit.*;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.event.player.PlayerTeleportEvent.TeleportCause;
import com.donsup.platform.TaskHandle;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ThreadLocalRandom;

/** Paper main-thread coordinator. Async work loads chunks only, never reads live world/player state. */
public final class RtpManager {
    public static final List<String> DIMENSIONS = List.of("overworld", "nether", "end");
    private static final Set<Material> HAZARDS = com.donsup.compat.Materials.presentSet("MAGMA_BLOCK", "MAGMA", "CACTUS",
            "CAMPFIRE", "SOUL_CAMPFIRE", "POWDER_SNOW", "POINTED_DRIPSTONE");
    private final DonsupPlugin plugin;
    private final RegionRtp region;
    private Map<String,RtpZones.Zone> zones=Map.of();
    public void reloadZones() { zones=RtpZones.read(plugin.getConfig().getConfigurationSection("travel.zones")); }
    public List<String> destinations() { var all=new ArrayList<>(DIMENSIONS);all.addAll(zones.keySet());return all; }
    public String label(String key) { var z=zones.get(key);return z==null?Lang.label("dimensions",key,key):z.region()+" / "+z.label(); }
    public boolean allowed(Player p,String key) { var z=zones.get(key);return destinations().contains(key)&&(z==null||z.permission().isEmpty()||p.hasPermission(z.permission())); }
    public boolean within(String key,int x,int z,int offset) { var zone=zones.get(key);return zone==null||zone.contains(x,z,offset); }
    public int[] sample(String key,World world,int offset,boolean sameChunk) {
        var zone=zones.get(key);if(zone!=null)return zone.sample(new java.util.Random(),offset,sameChunk);
        double radius=Math.min(Math.max(128,Math.min(100000,plugin.getConfig().getInt("travel.rtp-radius",5000))),world.getWorldBorder().getSize()/2-32);
        if(radius<16)throw new IllegalArgumentException("World border is too small for RTP.");
        Location c=world.getWorldBorder().getCenter();
        int x=(int)Math.floor(c.getX()+ThreadLocalRandom.current().nextDouble()*2*radius-radius),z=(int)Math.floor(c.getZ()+ThreadLocalRandom.current().nextDouble()*2*radius-radius);
        return sameChunk?new int[]{(x>>4)*16+3,(z>>4)*16+3}:new int[]{x,z};
    }
    private final RtpQueue queue = new RtpQueue();
    private final Map<UUID, Journey> journeys = new HashMap<>();
    private record ChunkKey(World world, int x, int z) {}
    private final Map<ChunkKey, Integer> tickets = new HashMap<>();
    private int searchesInFlight;
    private boolean teleporting;
    private static final class Journey {
        final List<UUID> players;
        final World world;
        final String destination;
        long expires = System.currentTimeMillis() + 60000;
        List<Location> destinations;
        Set<ChunkKey> chunks = Set.of();
        TaskHandle warmup;
        Journey(List<UUID> players, World world,String destination) { this.players = players; this.world = world; this.destination=destination; }
    }
    public RtpManager(DonsupPlugin plugin) { this.plugin = plugin; reloadZones(); this.region = plugin.platform().folia() ? new RegionRtp(plugin,this) : null; }
    public void command(Player player, String[] args, boolean queueAlias) {
        if (args.length == 0) { if (queueAlias) join(player, "overworld"); else plugin.dialogs().travel(player); return; }
        String action = args[0].toLowerCase(Locale.ROOT);
        if (Set.of("leave", "cancel").contains(action)) {
            if (!cancel(player.getUniqueId(), Lang.text("rtp.rtp-cancelled", "RTP cancelled."))) plugin.msg(player, Lang.text("rtp.you-are-not-waiting-for-rtp", "&7You are not waiting for RTP."));
        } else if(action.equals("zone") && args.length==2) {if(queueAlias)join(player,"zone:"+args[1].toLowerCase(Locale.ROOT));else solo(player,"zone:"+args[1].toLowerCase(Locale.ROOT));}
        else if(action.equals("zones")) plugin.zoneMenu().open(player,0);
        else if (action.equals("status")) plugin.msg(player, "&7" + status(player));
        else if (action.equals("queue") && (args.length <= 2 || (args.length==3 && args[1].equalsIgnoreCase("zone")))) join(player, args.length == 3 && args[1].equalsIgnoreCase("zone") ? "zone:"+args[2].toLowerCase(Locale.ROOT) : args.length == 2 ? args[1].toLowerCase(Locale.ROOT) : "overworld");
        else if (DIMENSIONS.contains(action) && args.length == 1) { if (queueAlias) join(player, action); else solo(player, action); }
        else plugin.msg(player, Lang.text("rtp.rtp-overworld-nether-end-or-rtp-queue-dimension-or-rtp-leave", "&e/rtp [overworld|nether|end] &7or &e/rtp queue [dimension] &7or &e/rtp leave"));
    }
    public String status(Player player) {
        if(region!=null)return region.status(player);
        var entry = queue.get(player.getUniqueId());
        if (entry != null) return Lang.text("rtp.waiting-for-a-partner-in-queued-rtp-leave-to-cancel", "Waiting for a partner in {0} ({1} queued). /rtp leave to cancel.", plugin.travel().rtp().label(entry.dimension()), queue.size(entry.dimension()));
        Journey journey = journeys.get(player.getUniqueId());
        return journey == null ? Lang.text("rtp.you-are-not-waiting-for-rtp-0ce41a", "You are not waiting for RTP.") : journey.warmup == null ? Lang.text("rtp.finding-a-safe-destination-rtp-leave-to-cancel", "Finding a safe destination. /rtp leave to cancel.") : Lang.text("rtp.rtp-countdown-stay-still-rtp-leave-to-cancel", "RTP countdown: stay still. /rtp leave to cancel.");
    }
    public World world(String dimension) {
        if (zones.containsKey(dimension)) dimension=zones.get(dimension).dimension();
        if (!DIMENSIONS.contains(dimension) || !plugin.getConfig().getBoolean("travel.dimensions." + dimension + ".enabled", true)) return null;
        String name = plugin.getConfig().getString("travel.dimensions." + dimension + ".world", "");
        if (dimension.equals("overworld") && name.isBlank()) name = plugin.getConfig().getString("travel.rtp-world", "");
        World.Environment environment = switch (dimension) {
            case "nether" -> World.Environment.NETHER; case "end" -> World.Environment.THE_END; default -> World.Environment.NORMAL;
        };
        World world = name.isBlank() ? Bukkit.getWorlds().stream().filter(w -> w.getEnvironment() == environment).findFirst().orElse(null) : Bukkit.getWorld(name);
        return world != null && world.getEnvironment() == environment ? world : null;
    }
    private boolean ready(Player player) {
        if (!player.hasPermission("donsup.use") || !plugin.travel().available(player)) return false;
        long cooldown = Math.max(1, Math.min(86400, plugin.getConfig().getLong("travel.rtp-cooldown-seconds", 15))) * 1000;
        if (!plugin.economy().cooldownReady(player.getUniqueId(), "rtp", cooldown)) { plugin.msg(player, Lang.text("rtp.rtp-is-on-cooldown", "&cRTP is on cooldown.")); return false; }
        return true;
    }
    private boolean occupied(Player player) {
        if (queue.get(player.getUniqueId()) == null && !journeys.containsKey(player.getUniqueId())) return false;
        plugin.msg(player, Lang.text("rtp.you-already-have-an-rtp-request-rtp-leave-to-cancel-it", "&eYou already have an RTP request. /rtp leave to cancel it.")); return true;
    }
    private World destination(Player player, String dimension) {
        if(!allowed(player,dimension)){plugin.msg(player,Lang.text("rtp.that-rtp-destination-is-unavailable-or-requires-permission", "&cThat RTP destination is unavailable or requires permission."));return null;}
        World world = world(dimension);
        if (world == null) plugin.msg(player, Lang.text("rtp.that-rtp-dimension-is-disabled-or-unavailable", "&cThat RTP dimension is disabled or unavailable."));
        return world;
    }
    public void solo(Player player, String dimension) {
        if(!allowed(player,dimension)){plugin.msg(player,Lang.text("rtp.that-rtp-destination-is-unavailable-or-requires-permission", "&cThat RTP destination is unavailable or requires permission."));return;}
        if(region!=null){region.solo(player,dimension);return;}
        if (!ready(player) || occupied(player)) return;
        World world = destination(player, dimension); if (world == null) return;
        if (active() >= capacity() || searchesInFlight >= capacity()) { plugin.msg(player, Lang.text("rtp.rtp-searches-are-busy-try-again-shortly", "&cRTP searches are busy. Try again shortly.")); return; }
        plugin.travel().cancelWarmup(player);
        start(List.of(player.getUniqueId()), world,dimension);
    }
    public void join(Player player, String dimension) {
        if(!allowed(player,dimension)){plugin.msg(player,Lang.text("rtp.that-rtp-destination-is-unavailable-or-requires-permission", "&cThat RTP destination is unavailable or requires permission."));return;}
        if(region!=null){region.join(player,dimension);return;}
        if (!plugin.getConfig().getBoolean("travel.queue.enabled", true)) { plugin.msg(player, Lang.text("rtp.rtp-queues-are-disabled", "&cRTP queues are disabled.")); return; }
        if (!player.hasPermission("donsup.rtp.queue")) { plugin.msg(player, Lang.text("rtp.no-permission-for-rtp-queues", "&cNo permission for RTP queues.")); return; }
        if (!ready(player) || occupied(player) || destination(player, dimension) == null) return;
        long timeout = Math.max(5, Math.min(3600, plugin.getConfig().getInt("travel.queue.timeout-seconds", 120))) * 1000L;
        int capacity = Math.max(2, Math.min(2000, plugin.getConfig().getInt("travel.queue.max-players", 200)));
        if (!queue.add(player.getUniqueId(), dimension, System.currentTimeMillis() + timeout, capacity)) {
            plugin.msg(player, Lang.text("rtp.the-rtp-queue-is-full", "&cThe RTP queue is full.")); return;
        }
        plugin.travel().cancelWarmup(player);
        plugin.msg(player, Lang.text("rtp.joined-the-rtp-queue-waiting-for-a-partner-rtp-leave-to-cancel", "&aJoined the {0} RTP queue. &7Waiting for a partner; /rtp leave to cancel.", plugin.travel().rtp().label(dimension)));
        match();
    }
    private int capacity() { return Math.max(1, Math.min(16, plugin.getConfig().getInt("travel.max-concurrent-searches", 8))); }
    private long active() { return journeys.values().stream().distinct().count(); }
    public void tick() {
        if(region!=null){region.tick();return;}
        long now = System.currentTimeMillis();
        for (var expired : queue.expire(now)) message(expired.player(), Lang.text("rtp.rtp-queue-timed-out-join-again-when-ready", "&7RTP queue timed out. Join again when ready."));
        for (Journey journey : new HashSet<>(journeys.values())) {
            if (journey.expires <= now || !valid(journey)) finish(journey, Lang.text("rtp.rtp-cancelled-a-player-or-destination-became-unavailable", "RTP cancelled: a player or destination became unavailable."));
        }
        match();
    }
    private void match() {
        for (var expired : queue.expire(System.currentTimeMillis())) message(expired.player(), Lang.text("rtp.rtp-queue-timed-out-join-again-when-ready", "&7RTP queue timed out. Join again when ready."));
        for (String dimension : destinations()) while (active() < capacity() && searchesInFlight < capacity()) {
            List<RtpQueue.Entry> pair = queue.pair(dimension); if (pair.isEmpty()) break;
            World world = world(dimension);
            List<UUID> players = pair.stream().map(RtpQueue.Entry::player).toList();
            if (world == null || !plugin.getConfig().getBoolean("travel.queue.enabled", true)
                    || players.stream().anyMatch(id -> Bukkit.getPlayer(id) == null || !ready(Bukkit.getPlayer(id))
                        || !Bukkit.getPlayer(id).hasPermission("donsup.rtp.queue"))) {
                players.forEach(id -> message(id, Lang.text("rtp.rtp-match-cancelled-a-player-or-dimension-became-unavailable", "&cRTP match cancelled: a player or dimension became unavailable."))); continue;
            }
            players.forEach(id -> message(id, Lang.text("rtp.partner-found-finding-a-safe-location-together", "&aPartner found! Finding a safe location together.")));
            start(players, world,dimension);
        }
    }
    private void start(List<UUID> players, World world,String destination) {
        Journey journey = new Journey(players, world,destination);
        players.forEach(id -> { journeys.put(id, journey); message(id, Lang.text("rtp.finding-a-safe-wilderness-location", "&7Finding a safe wilderness location...")); });
        attempt(journey, 0);
    }
    private boolean valid(Journey journey) {
        return journey.players.stream().allMatch(id -> {
            Player player = Bukkit.getPlayer(id);
            return journeys.get(id) == journey && player != null && player.isOnline() && !player.isDead()
                    && allowed(player,journey.destination) && player.hasPermission("donsup.use") && !plugin.travel().tagged(player) && !plugin.duels().inDuel(player)
                    && (journey.players.size() == 1 || player.hasPermission("donsup.rtp.queue"));
        });
    }
    private void attempt(Journey journey, int attempt) {
        if (!valid(journey)) { finish(journey, Lang.text("rtp.rtp-cancelled-a-player-became-unavailable", "RTP cancelled: a player became unavailable.")); return; }
        if (attempt >= 32 || journey.expires <= System.currentTimeMillis()) { finish(journey, Lang.text("rtp.no-safe-rtp-location-found-try-again", "No safe RTP location found. Try again.")); return; }
        World world = journey.world;
        int[] sample;
        try { sample=sample(journey.destination,world,journey.players.size()==2?8:0,false); }
        catch(IllegalArgumentException e){finish(journey,e.getMessage());return;}
        int x=sample[0],z=sample[1];
        int secondX = x + (journey.players.size() == 2 ? 8 : 0);
        searchesInFlight++;
        CompletableFuture.allOf(loadChunk(world, x >> 4, z >> 4), loadChunk(world, secondX >> 4, z >> 4))
                .whenComplete((ignored, error) -> {
            if (!plugin.isEnabled()) return;
            plugin.platform().global(() -> {
                // Cancellation invalidates a journey, but the underlying chunk requests
                // still occupy capacity until they actually finish.
                searchesInFlight--;
                if (!valid(journey)) return;
                if (error != null) { finish(journey, Lang.text("rtp.rtp-chunk-loading-failed-try-again", "RTP chunk loading failed. Try again.")); return; }
                Location first = safeColumn(world, x, z), second = journey.players.size() == 2 ? safeColumn(world, secondX, z) : first;
                if (!within(journey.destination,x,z,journey.players.size()==2?8:0) || first == null || second == null || Math.abs(first.getY() - second.getY()) > 6) { attempt(journey, attempt + 1); return; }
                journey.destinations = journey.players.size() == 2 ? List.of(first, second) : List.of(first);
                Set<ChunkKey> chunks = new HashSet<>();
                journey.destinations.forEach(p -> chunks.add(new ChunkKey(world, p.getBlockX() >> 4, p.getBlockZ() >> 4)));
                journey.chunks = chunks;
                for (ChunkKey key : chunks) {
                    if (!tickets.containsKey(key)) com.donsup.compat.BukkitCompat.ticket(key.world(), key.x(), key.z(), plugin, true);
                    tickets.merge(key, 1, Integer::sum);
                }
                int delay = Math.max(0, Math.min(60, plugin.getConfig().getInt("travel.warmup-seconds", 3)));
                journey.expires = System.currentTimeMillis() + delay * 1000L + 5000;
                journey.players.forEach(id -> message(id, Lang.text("rtp.rtp-in-seconds-stay-still-moving-cancels-the-whole-match", "&7RTP in {0} seconds. Stay still; moving cancels the whole match.", delay)));
                journey.warmup = plugin.platform().globalLater(() -> arrive(journey), Math.max(1, delay * 20L));
            });
        });
    }
    private CompletableFuture<Chunk> loadChunk(World world, int x, int z) {
        try { return plugin.platform().chunk(world, x, z); }
        catch (RuntimeException ex) { return CompletableFuture.failedFuture(ex); }
    }
    private Location safeColumn(World world, int x, int z) {
        int top = world.getEnvironment() == World.Environment.NETHER
                ? Math.min(world.getMaxHeight() - 3, com.donsup.compat.BukkitCompat.minHeight(world) + com.donsup.compat.BukkitCompat.logicalHeight(world) - 3)
                : Math.min(world.getMaxHeight() - 3, com.donsup.compat.BukkitCompat.highest(world, x, z));
        for (int y = top; y > com.donsup.compat.BukkitCompat.minHeight(world); y--) {
            Location location = new Location(world, x + .5, y + 1, z + .5);
            if (safe(location)) return location;
            if (world.getEnvironment() != World.Environment.NETHER) return null;
        }
        return null;
    }
    private boolean safe(Location location) {
        World world = location.getWorld();
        if (!com.donsup.compat.BukkitCompat.inside(world.getWorldBorder(), location)) return false;
        Location spawn = world.getSpawnLocation();
        if (Math.pow(location.getX() - spawn.getX(), 2) + Math.pow(location.getZ() - spawn.getZ(), 2) < 4096) return false;
        Block feet = location.getBlock(), ground = feet.getRelative(0, -1, 0);
        return ground.getType().isSolid() && !HAZARDS.contains(ground.getType()) && com.donsup.compat.BukkitCompat.fullHeight(ground)
                && com.donsup.compat.BukkitCompat.air(feet.getType()) && com.donsup.compat.BukkitCompat.air(feet.getRelative(0, 1, 0).getType());
    }
    private void arrive(Journey journey) {
        if (!valid(journey) || journey.destinations.stream().anyMatch(p -> !p.getWorld().isChunkLoaded(p.getBlockX() >> 4, p.getBlockZ() >> 4) || !safe(p))) {
            finish(journey, Lang.text("rtp.rtp-cancelled-a-player-or-destination-became-unsafe", "RTP cancelled: a player or destination became unsafe.")); return;
        }
        List<Player> players = journey.players.stream().map(Bukkit::getPlayer).toList();
        List<Location> origins = players.stream().map(player -> player.getLocation()).toList();
        int moved = 0;
        teleporting = true;
        try {
            // Chunks are already loaded. Both synchronous teleports occur in this server tick.
            for (int i = 0; i < players.size(); i++) {
                if (!players.get(i).teleport(journey.destinations.get(i), TeleportCause.PLUGIN)) break;
                moved++;
            }
            if (moved == players.size()) {
                players.forEach(p -> plugin.economy().markCooldown(p.getUniqueId(), "rtp"));
                finish(journey, players.size() == 2 ? Lang.text("rtp.rtp-complete-your-partner-is-nearby", "RTP complete. Your partner is nearby.") : Lang.text("rtp.rtp-complete", "RTP complete."));
            } else {
                for (int i = 0; i < moved; i++) if (!players.get(i).teleport(origins.get(i), TeleportCause.PLUGIN)) {
                    plugin.getLogger().warning("Another plugin blocked RTP rollback for " + players.get(i).getUniqueId() + " to " + origins.get(i));
                    plugin.msg(players.get(i), Lang.text("rtp.a-protection-plugin-blocked-your-return-contact-staff-for-help-re", "&cA protection plugin blocked your return. Contact staff for help returning."));
                }
                finish(journey, Lang.text("rtp.rtp-cancelled-by-server-protection-no-cooldown-was-charged", "RTP cancelled by server protection. No cooldown was charged."));
            }
        } finally { teleporting = false; }
    }
    public void moved(Player player) {
        if(region!=null){region.moved(player);return;}
        Journey journey = journeys.get(player.getUniqueId());
        if (!teleporting && journey != null && journey.warmup != null) cancel(player.getUniqueId(), Lang.text("rtp.rtp-cancelled-a-player-moved-during-the-countdown", "RTP cancelled: a player moved during the countdown."));
    }
    public void externalTeleport(Player player) { if(region!=null){region.externalTeleport(player);return;} if (!teleporting) cancel(player.getUniqueId(), Lang.text("rtp.rtp-cancelled-because-a-player-teleported", "RTP cancelled because a player teleported.")); }
    public boolean cancel(UUID id, String reason) {
        if(region!=null)return region.cancel(id,reason);
        Journey journey = journeys.get(id);
        if (journey != null) { finish(journey, reason); return true; }
        if (queue.remove(id) != null) { message(id, "&7" + reason); return true; }
        return false;
    }
    private void finish(Journey journey, String reason) {
        if (journey.warmup != null) journey.warmup.cancel();
        for (ChunkKey key : journey.chunks) {
            Integer count = tickets.get(key);
            if (count != null && count > 1) tickets.put(key, count - 1);
            else if (tickets.remove(key) != null) com.donsup.compat.BukkitCompat.ticket(key.world(), key.x(), key.z(), plugin, false);
        }
        journey.chunks = Set.of();
        journey.players.forEach(id -> { if (journeys.remove(id, journey)) message(id, "&7" + reason); });
    }
    private void message(UUID id, String message) { Player player = Bukkit.getPlayer(id); if (player != null) plugin.msg(player, message); }
    public void shutdown() {
        if(region!=null){region.shutdown();return;}
        for (Journey journey : new HashSet<>(journeys.values())) finish(journey, Lang.text("rtp.rtp-cancelled-because-the-server-is-stopping", "RTP cancelled because the server is stopping."));
        queue.clear();
    }
}


===== src/main/java/com/donsup/features/RtpQueue.java =====

package com.donsup.features;

import java.util.*;

/** FIFO waiting room. Accessed only from the Paper server thread. */
public final class RtpQueue {
    public record Entry(UUID player, String dimension, long expires) {}
    private final Map<UUID, Entry> waiting = new LinkedHashMap<>();
    public boolean add(UUID player, String dimension, long expires, int capacity) {
        if (waiting.containsKey(player) || waiting.size() >= capacity) return false;
        waiting.put(player, new Entry(player, dimension, expires)); return true;
    }
    public Entry get(UUID player) { return waiting.get(player); }
    public Entry remove(UUID player) { return waiting.remove(player); }
    public List<Entry> expire(long now) {
        List<Entry> expired = waiting.values().stream().filter(e -> e.expires() <= now).toList();
        expired.forEach(e -> waiting.remove(e.player())); return expired;
    }
    public List<Entry> pair(String dimension) {
        List<Entry> pair = waiting.values().stream().filter(e -> e.dimension().equals(dimension)).limit(2).toList();
        if (pair.size() != 2) return List.of();
        pair.forEach(e -> waiting.remove(e.player())); return pair;
    }
    public long size(String dimension) { return waiting.values().stream().filter(e -> e.dimension().equals(dimension)).count(); }
    public void clear() { waiting.clear(); }
}


===== src/main/java/com/donsup/features/RtpZoneMenu.java =====

package com.donsup.features;

import com.donsup.config.Lang;
import com.donsup.DonsupPlugin;
import com.donsup.util.Text;
import org.bukkit.Material;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.inventory.*;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.*;
import java.util.*;

public final class RtpZoneMenu implements Listener {
    private record Screen(Inventory inventory,Map<Integer,Runnable> actions){}
    private final DonsupPlugin plugin;
    private final Map<UUID,Screen> screens=new HashMap<>();
    public RtpZoneMenu(DonsupPlugin plugin){this.plugin=plugin;}
    private void button(Screen s,int slot,Material icon,String name,Runnable action){var item=new ItemStack(icon);var meta=item.getItemMeta();meta.setDisplayName(Text.color(Lang.text("rtp-zone-menu.text", "&b{0}", name)));item.setItemMeta(meta);s.inventory().setItem(slot,item);s.actions().put(slot,action);}
    public void open(Player player,int page){
        var rtp=plugin.travel().rtp();var zones=rtp.destinations().stream().filter(k->k.startsWith("zone:")&&rtp.allowed(player,k)&&rtp.world(k)!=null).toList();
        int index=Math.min(Math.max(0,page),Math.max(0,(zones.size()-1)/18));
        Screen s=new Screen(plugin.inventory(54,"RTP Regions / Zones",false),new HashMap<>());int slot=0;
        for(String key:zones.stream().skip(index*18L).limit(18).toList()){
            button(s,slot++,Material.COMPASS,Lang.text("rtp-zone-menu.solo", "{0} — Solo", rtp.label(key)),()->rtp.solo(player,key));
            button(s,slot++,Material.ENDER_PEARL,Lang.text("rtp-zone-menu.paired", "{0} — Paired", rtp.label(key)),()->rtp.join(player,key));
        }
        if(zones.isEmpty())button(s,22,Material.PAPER,Lang.text("rtp-zone-menu.no-configured-zones-available", "No configured zones available"),()->plugin.msg(player,Lang.text("rtp-zone-menu.staff-can-configure-named-regions-in-travel-zones-in-config-yml", "&7Staff can configure named regions in travel.zones in config.yml.")));
        if(index>0)button(s,45,Material.ARROW,Lang.text("rtp-zone-menu.previous", "Previous"),()->open(player,index-1));
        if((index+1)*18<zones.size())button(s,53,Material.ARROW,Lang.text("rtp-zone-menu.next", "Next"),()->open(player,index+1));
        button(s,49,Material.COMPASS,Lang.text("rtp-zone-menu.dimensions", "Dimensions"),()->plugin.dialogs().travel(player));player.openInventory(s.inventory());screens.put(player.getUniqueId(),s);
    }
    @EventHandler(priority=EventPriority.HIGHEST)public void click(InventoryClickEvent e){if(!(e.getWhoClicked() instanceof Player p))return;var s=screens.get(p.getUniqueId());if(s==null||com.donsup.compat.Views.top(e.getView())!=s.inventory())return;e.setCancelled(true);var a=s.actions().get(e.getRawSlot());if(a!=null){screens.remove(p.getUniqueId());p.closeInventory();plugin.platform().player(p,()->{if(p.isOnline()&&p.hasPermission("donsup.use"))a.run();});}}
    @EventHandler public void drag(InventoryDragEvent e){var s=screens.get(e.getWhoClicked().getUniqueId());if(s!=null&&com.donsup.compat.Views.top(e.getView())==s.inventory())e.setCancelled(true);}
    @EventHandler public void close(InventoryCloseEvent e){var s=screens.get(e.getPlayer().getUniqueId());if(s!=null&&s.inventory()==e.getInventory())screens.remove(e.getPlayer().getUniqueId());}
    @EventHandler public void quit(PlayerQuitEvent e){screens.remove(e.getPlayer().getUniqueId());}
}


===== src/main/java/com/donsup/features/RtpZones.java =====

package com.donsup.features;

import org.bukkit.configuration.ConfigurationSection;
import java.util.*;

/** Local-world geographic regions. Bounds include both players in paired travel. */
public final class RtpZones {
    public record Zone(String id,String label,String region,String dimension,String permission,int minX,int maxX,int minZ,int maxZ) {
        public boolean contains(int x,int z,int companionOffset) {return x>=minX&&x+companionOffset<=maxX&&z>=minZ&&z<=maxZ;}
        public int[] sample(Random random,int companionOffset,boolean sameChunk) {
            for(int i=0;i<128;i++){
                int x=minX+random.nextInt(maxX-minX+1),z=minZ+random.nextInt(maxZ-minZ+1);
                if(sameChunk){x=(x>>4)*16+3;z=(z>>4)*16+3;}
                if(contains(x,z,companionOffset))return new int[]{x,z};
            }
            throw new IllegalArgumentException("RTP zone is too narrow for this journey.");
        }
    }
    public static Map<String,Zone> read(ConfigurationSection root) {
        Map<String,Zone> out=new LinkedHashMap<>();if(root==null)return out;
        if(root.getKeys(false).size()>100)throw new IllegalArgumentException("At most 100 RTP zones are supported.");
        for(String id:root.getKeys(false)){
            var s=root.getConfigurationSection(id);if(s==null||!s.getBoolean("enabled",true))continue;
            if(!id.matches("[a-z0-9_-]{1,24}"))throw new IllegalArgumentException("Invalid RTP zone id: "+id);
            String dimension=s.getString("dimension","overworld");
            if(!RtpManager.DIMENSIONS.contains(dimension))throw new IllegalArgumentException("Invalid dimension for RTP zone "+id);
            for(String key:List.of("min-x","max-x","min-z","max-z"))if(!s.isInt(key))throw new IllegalArgumentException("Missing integer "+key+" for RTP zone "+id);
            int a=s.getInt("min-x"),b=s.getInt("max-x"),c=s.getInt("min-z"),d=s.getInt("max-z");
            if(a < -29000000 || b>29000000 || c < -29000000 || d>29000000 || (long)b-a<32 || (long)d-c<32)throw new IllegalArgumentException("Invalid or too narrow bounds for RTP zone "+id);
            out.put("zone:"+id,new Zone(id,s.getString("label",id),s.getString("region","Wilderness"),dimension,s.getString("permission",""),a,b,c,d));
        }
        return Collections.unmodifiableMap(out);
    }
}


===== src/main/java/com/donsup/features/ServerFeatures.java =====

package com.donsup.features;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.Text;
import org.bukkit.*;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.player.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/** Social features and thread-safe read snapshots for the asynchronous chat event. */
public final class ServerFeatures implements Listener {
    public static final Set<String> SETTINGS = Set.of("keep_pearls_on_death", "public_chat", "private_messages", "friend_chat", "market_alerts", "bounty_alerts",
        "friend_notifications", "menu_sounds", "duel_requests", "combat_alerts", "night_vision", "clear_weather", "personal_day",
        "teleport_requests", "friend_requests", "payments", "public_profile", "scoreboard", "scoreboard_coordinates", "scoreboard_balance");
    private final DonsupPlugin plugin;
    private final YamlConfiguration data = new YamlConfiguration();
    private final Path file;
    private final Map<UUID, Map<String, Boolean>> settings = new ConcurrentHashMap<>();
    private final Map<UUID, Set<UUID>> ignored = new ConcurrentHashMap<>();
    private final Map<UUID, Map<UUID, Long>> requests = new HashMap<>();
    private final Map<UUID, UUID> replies = new HashMap<>();
    private final Map<UUID, Long> lastRequest = new HashMap<>();
    public ServerFeatures(DonsupPlugin plugin) {
        this.plugin = plugin; file = plugin.getDataFolder().toPath().resolve("social-preferences.yml");
        try { if (Files.exists(file)) data.load(file.toFile()); }
        catch (Exception ex) { throw new IllegalStateException("Cannot load social-preferences.yml; refusing to overwrite it", ex); }
        refreshAll();
    }
    private void save() {
        try { com.donsup.util.SafeYaml.save(data,file.toFile()); }
        catch(IOException e){throw new IllegalStateException("Could not save social data",e);}
    }
    private Set<UUID> ids(String path) {
        Set<UUID> out = new LinkedHashSet<>();
        for (String raw : data.getStringList(path)) try { out.add(UUID.fromString(raw)); } catch (IllegalArgumentException ignored) { }
        return out;
    }
    private void ids(String path, Set<UUID> values) { data.set(path, values.stream().map(UUID::toString).toList()); }
    public Set<UUID> friends(UUID player) { return ids("friends." + player); }
    public boolean blocks(UUID receiver, UUID sender) { return ignored.getOrDefault(receiver, Set.of()).contains(sender); }
    public void refresh(UUID id) {
        Map<String, Boolean> snapshot = new HashMap<>();
        SETTINGS.forEach(key -> snapshot.put(key, plugin.economy().setting(id, key)));
        settings.put(id, Map.copyOf(snapshot));
        ignored.put(id, Set.copyOf(ids("ignored." + id)));
        Player player = Bukkit.getPlayer(id);
        if (player != null) plugin.platform().playerNow(player, () -> {
            if (snapshot.get("clear_weather")) player.setPlayerWeather(WeatherType.CLEAR); else player.resetPlayerWeather();
            if (snapshot.get("personal_day")) player.setPlayerTime(6000, false); else player.resetPlayerTime();
        });
    }
    public void refreshAll() { Bukkit.getOnlinePlayers().forEach(player -> refresh(player.getUniqueId())); }
    @EventHandler public void join(PlayerJoinEvent event) {
        Player player = event.getPlayer(); plugin.economy().ensure(player); refresh(player.getUniqueId());
        for (UUID id : friends(player.getUniqueId())) {
            Player friend = Bukkit.getPlayer(id);
            if (friend != null && friend.canSee(player) && plugin.economy().setting(id, "friend_notifications"))
                plugin.msg(friend, Lang.text("server-features.your-friend-is-online", "&aYour friend &f{0} &ais online.", player.getName()));
        }
    }
    @EventHandler public void quit(PlayerQuitEvent event) {
        UUID id = event.getPlayer().getUniqueId();
        settings.remove(id); ignored.remove(id); replies.remove(id); replies.values().removeIf(id::equals);
        requests.remove(id); requests.values().forEach(map -> map.remove(id)); lastRequest.remove(id);
    }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true)
    public void chat(AsyncPlayerChatEvent event) {
        UUID sender = event.getPlayer().getUniqueId();
        if (!settings.getOrDefault(sender, Map.of()).getOrDefault("public_chat", true)) { event.setCancelled(true); return; }
        event.getRecipients().removeIf(player -> !settings.getOrDefault(player.getUniqueId(), Map.of()).getOrDefault("public_chat", true) || blocks(player.getUniqueId(), sender));
    }
    @EventHandler public void changedWorld(PlayerChangedWorldEvent event) { refresh(event.getPlayer().getUniqueId()); }
    public List<Player> friendRequests(Player player) {
        var incoming = requests.getOrDefault(player.getUniqueId(), Map.of());
        return incoming.entrySet().stream().filter(e -> e.getValue() > System.currentTimeMillis()).map(e -> Bukkit.getPlayer(e.getKey()))
            .filter(Objects::nonNull).filter(player::canSee).toList();
    }
    public void friend(Player player, String[] args) {
        if (args.length < 2) { plugin.dialogs().friends(player); return; }
        String action = args[0].toLowerCase(Locale.ROOT);
        OfflinePlayer known = plugin.economy().knownPlayer(args[1]);
        Player target = Bukkit.getPlayerExact(args[1]);
        UUID id = known == null ? (target == null ? null : target.getUniqueId()) : known.getUniqueId();
        if (id == null || id.equals(player.getUniqueId())) { plugin.msg(player, Lang.text("server-features.unknown-player", "&cUnknown player.")); return; }
        if (action.equals("remove")) { removeFriend(player, id); return; }
        if (target == null || !player.canSee(target)) { plugin.msg(player, Lang.text("server-features.that-player-is-offline", "&cThat player is offline.")); return; }
        if (action.equals("deny")) { var pending = requests.get(player.getUniqueId()); if (pending != null) pending.remove(id); plugin.msg(player, Lang.text("server-features.friend-request-declined", "&7Friend request declined.")); return; }
        if (action.equals("accept")) {
            var pending = requests.get(player.getUniqueId());
            Long expires = pending == null ? null : pending.remove(id);
            if (expires == null || expires < System.currentTimeMillis()) { plugin.msg(player, Lang.text("server-features.no-active-request", "&cNo active request.")); return; }
            Set<UUID> a = friends(player.getUniqueId()), b = friends(id);
            if (a.size() >= 100 || b.size() >= 100) { plugin.msg(player, Lang.text("server-features.friend-limit-reached-100", "&cFriend limit reached (100).")); return; }
            a.add(id); b.add(player.getUniqueId()); ids("friends." + player.getUniqueId(), a); ids("friends." + id, b); save();
            plugin.msg(player, Lang.text("server-features.you-are-now-friends-with", "&aYou are now friends with {0}.", target.getName())); plugin.msg(target, Lang.text("server-features.accepted-your-friend-request", "&a{0} accepted your friend request.", player.getName())); return;
        }
        if (!action.equals("add")) { plugin.msg(player, Lang.text("server-features.friend", "&e/friend <add|accept|deny|remove> <player>")); return; }
        if (!plugin.economy().setting(id, "friend_requests") || blocks(id, player.getUniqueId()) || friends(player.getUniqueId()).contains(id)) {
            plugin.msg(player, Lang.text("server-features.friend-request-unavailable", "&cFriend request unavailable.")); return;
        }
        long now = System.currentTimeMillis();
        if (now - lastRequest.getOrDefault(player.getUniqueId(), 0L) < 3000) { plugin.msg(player, Lang.text("server-features.wait-before-sending-another-request", "&cWait before sending another request.")); return; }
        var incoming = requests.computeIfAbsent(id, k -> new HashMap<>());
        incoming.entrySet().removeIf(e -> e.getValue() < now);
        if (incoming.size() >= 20) { plugin.msg(player, Lang.text("server-features.that-player-has-too-many-pending-requests", "&cThat player has too many pending requests.")); return; }
        incoming.put(player.getUniqueId(), now + 120000); lastRequest.put(player.getUniqueId(), now);
        plugin.msg(target, Lang.text("server-features.sent-a-friend-request-friend-accept", "&e{0} &7sent a friend request. &f/friend accept {1}", player.getName(), player.getName()));
        plugin.msg(player, Lang.text("server-features.friend-request-sent-expires-in-2-minutes", "&aFriend request sent (expires in 2 minutes)."));
    }
    public void removeFriend(Player player, UUID id) {
        Set<UUID> a = friends(player.getUniqueId()), b = friends(id); a.remove(id); b.remove(player.getUniqueId());
        ids("friends." + player.getUniqueId(), a); ids("friends." + id, b); save(); plugin.msg(player, Lang.text("server-features.friend-removed", "&7Friend removed."));
    }
    private void message(Player player, String name, String message) {
        Player target = Bukkit.getPlayerExact(name);
        if (target == null || !player.canSee(target) || !plugin.economy().setting(target.getUniqueId(), "private_messages") || blocks(target.getUniqueId(), player.getUniqueId())) {
            plugin.msg(player, Lang.text("server-features.that-player-cannot-receive-messages", "&cThat player cannot receive messages.")); return;
        }
        if (message.isBlank() || message.length() > 256) { plugin.msg(player, Lang.text("server-features.messages-must-be-1-256-characters", "&cMessages must be 1-256 characters.")); return; }
        String safe = ChatColor.stripColor(message.replace('&', ' '));
        plugin.msg(target, Lang.text("server-features.you", "&d{0} → you: &f{1}", player.getName(), safe));
        plugin.msg(player, Lang.text("server-features.you-765019", "&dYou → {0}: &f{1}", target.getName(), safe));
        replies.put(target.getUniqueId(), player.getUniqueId()); replies.put(player.getUniqueId(), target.getUniqueId());
    }
    public void recordSale(Player player, String detail) {
        List<String> history = new ArrayList<>(data.getStringList("sales." + player.getUniqueId()));
        history.add(0, java.time.Instant.now() + " | " + detail);
        data.set("sales." + player.getUniqueId(), history.stream().limit(50).toList()); save();
    }
    public void history(Player player) {
        var lines = data.getStringList("sales." + player.getUniqueId());
        plugin.dialogs().notice(player, Lang.text("server-features.sell-history", "Sell History"), lines.isEmpty() ? Lang.text("server-features.no-sales-yet", "No sales yet.") : String.join("\n", lines.stream().limit(12).toList()));
    }
    public boolean command(CommandSender sender, String name, String[] args) {
        if ((name.equals("shop") || name.equals("quickbuy")) && sender instanceof Player player) { plugin.shopping().command(player, args); return true; }
        if (name.equals("servershop") && sender instanceof Player player) { plugin.menus().openShop(player); return true; }
        if (name.equals("smp")) {
            if (args.length == 0) { if (sender instanceof Player p) plugin.dialogs().main(p); else plugin.msg(sender, Lang.text("server-features.donsup-reload-money-shardadmin-rank", "&e/donsup reload | money | shardadmin | rank")); return true; }
            if (args[0].equalsIgnoreCase("legacy") && sender instanceof Player p) { plugin.menus().openLegacyMain(p); return true; }
            if (Set.of("money", "shardadmin", "rank").contains(args[0].toLowerCase(Locale.ROOT))) { admin(sender, args); return true; }
            return false;
        }
        Set<String> handled = Set.of("friends", "friend", "friendchat", "follow", "following", "unfollow", "msg", "reply", "ignore", "rtp", "rtpqueue", "tpa", "tpahere", "tpaccept", "tpdeny", "spawn", "setspawn", "stats", "sellhistory", "worth", "baltop", "trash", "rules", "quickbuy", "servershop");
        if (!handled.contains(name)) return false;
        if (!(sender instanceof Player player)) { plugin.msg(sender, Lang.text("server-features.use-this-command-in-game", "&cUse this command in game.")); return true; }
        switch (name) {
            case "friends", "friend" -> friend(player, args);
            case "friendchat" -> {
                String message = ChatColor.stripColor(String.join(" ", args).replace('&', ' '));
                if (message.isBlank() || message.length() > 256) break;
                for (UUID id : friends(player.getUniqueId())) {
                    Player target = Bukkit.getPlayer(id);
                    if (target != null && plugin.economy().setting(id, "friend_chat") && !blocks(id, player.getUniqueId()))
                        plugin.msg(target, Lang.text("server-features.friends", "&a[Friends] {0}: &f{1}", player.getName(), message));
                }
                plugin.msg(player, Lang.text("server-features.friends", "&a[Friends] {0}: &f{1}", player.getName(), message));
            }
            case "msg" -> { if (args.length < 2) plugin.msg(player, Lang.text("server-features.msg", "&e/msg <player> <message>")); else message(player, args[0], String.join(" ", Arrays.copyOfRange(args, 1, args.length))); }
            case "reply" -> { Player target = Bukkit.getPlayer(replies.getOrDefault(player.getUniqueId(), player.getUniqueId())); if (target == null || target.equals(player)) plugin.msg(player, Lang.text("server-features.no-one-to-reply-to", "&cNo one to reply to.")); else message(player, target.getName(), String.join(" ", args)); }
            case "ignore" -> {
                if (args.length != 1) { plugin.msg(player, Lang.text("server-features.ignore", "&e/ignore <player>")); break; }
                OfflinePlayer target = plugin.economy().knownPlayer(args[0]);
                if (target == null || target.getUniqueId().equals(player.getUniqueId())) break;
                Set<UUID> list = ids("ignored." + player.getUniqueId()); boolean removed = list.remove(target.getUniqueId());
                if (!removed) list.add(target.getUniqueId()); ids("ignored." + player.getUniqueId(), list); save(); refresh(player.getUniqueId());
                plugin.msg(player, removed ? Lang.text("server-features.player-unignored", "&aPlayer unignored.") : Lang.text("server-features.player-ignored", "&7Player ignored."));
            }
            case "follow", "unfollow", "following" -> {
                Set<UUID> list = ids("following." + player.getUniqueId());
                if (args.length == 1) {
                    OfflinePlayer target = plugin.economy().knownPlayer(args[0]);
                    if (target != null && !target.getUniqueId().equals(player.getUniqueId())) {
                        if (name.equals("unfollow")) list.remove(target.getUniqueId());
                        else if (list.size() < 100) list.add(target.getUniqueId());
                        ids("following." + player.getUniqueId(), list); save();
                    }
                }
                plugin.dialogs().notice(player, Lang.text("server-features.following", "Following"), list.isEmpty() ? Lang.text("server-features.use-follow", "Use /follow <player>.") : String.join("\n", list.stream().map(plugin.economy()::playerName).toList()));
            }
            case "rtp", "rtpqueue" -> plugin.travel().rtp().command(player, args, name.equals("rtpqueue"));
            case "tpa", "tpahere" -> { if (args.length == 1) plugin.travel().request(player, Bukkit.getPlayerExact(args[0]), name.equals("tpahere")); else plugin.msg(player, Lang.text("server-features.text", "&e/{0} <player>", name)); }
            case "tpaccept", "tpdeny" -> plugin.travel().respond(player, args.length == 0 ? "" : args[0], name.equals("tpaccept"));
            case "spawn" -> plugin.travel().teleport(player, com.donsup.compat.BukkitCompat.location(data, "spawn", player.getWorld().getSpawnLocation()));
            case "setspawn" -> { if (player.hasPermission("donsup.admin")) { data.set("spawn", player.getLocation()); save(); plugin.msg(player, Lang.text("server-features.spawn-saved", "&aSpawn saved.")); } else plugin.msg(player, Lang.text("server-features.no-permission", "&cNo permission.")); }
            case "stats" -> { Player target = args.length > 0 ? Bukkit.getPlayerExact(args[0]) : player; if (target != null && player.canSee(target)) plugin.dialogs().profile(player, target); }
            case "sellhistory" -> history(player);
            case "worth" -> {
                var item = com.donsup.compat.BukkitCompat.hand(player.getInventory());
                double price = plugin.market().serverPrice(player, item);
                plugin.msg(player, Lang.text("server-features.base-value-of-held-stack-orders-may-pay-more", "&7Base value of held stack: &a{0}&7. Orders may pay more.", Text.money(price * item.getAmount())));
            }
            case "baltop" -> plugin.menus().openLeaderboards(player);
            case "trash" -> player.openInventory(plugin.inventory(27, "SMP | Trash (deleted on close)", true));
            case "rules" -> plugin.dialogs().notice(player, Lang.text("server-features.server-rules", "Server Rules"), String.join("\n", plugin.getConfig().getStringList("server-rules")));
        }
        return true;
    }
    private void admin(CommandSender sender, String[] args) {
        if (!sender.hasPermission("donsup.admin")) { plugin.msg(sender, Lang.text("server-features.no-permission", "&cNo permission.")); return; }
        if (args.length != 4) { plugin.msg(sender, Lang.text("server-features.donsup-money-e-donsup-shardadmin-donsup-rank", "&e/donsup money <give|take> <player> <amount>\n& e/donsup shardadmin <give|take> <player> <amount>\n&e/donsup rank <player> <member|plus|elite|legend> <days>")); return; }
        boolean rank = args[0].equalsIgnoreCase("rank");
        OfflinePlayer target = plugin.economy().knownPlayer(args[rank ? 1 : 2]);
        if (target == null) { plugin.msg(sender, Lang.text("server-features.player-must-have-joined-before", "&cPlayer must have joined before.")); return; }
        try {
            if (rank) {
                int days = Integer.parseInt(args[3]);
                if (!Set.of("member", "plus", "elite", "legend").contains(args[2]) || days < 1 || days > 36500) throw new IllegalArgumentException();
                plugin.economy().setRank(target.getUniqueId(), args[2], days); plugin.msg(sender, Lang.text("server-features.rank-updated", "&aRank updated.")); return;
            }
            double amount = com.donsup.util.MoneyInput.positiveMoney(args[3]);
            if (!Set.of("give", "take").contains(args[1])) throw new IllegalArgumentException();
            boolean ok = true;
            if (args[0].equalsIgnoreCase("money")) {
                if (args[1].equals("take")) ok = plugin.economy().withdraw(target.getUniqueId(), amount);
                else plugin.economy().deposit(target.getUniqueId(), amount);
            } else {
                if (amount != Math.floor(amount) || amount > Integer.MAX_VALUE) throw new IllegalArgumentException();
                if (args[1].equals("take")) ok = plugin.economy().takeShards(target.getUniqueId(), (int) amount);
                else { ok = (long) plugin.economy().shards(target.getUniqueId()) + (long) amount <= Integer.MAX_VALUE; if (ok) plugin.economy().addShards(target.getUniqueId(), (int) amount); }
            }
            plugin.msg(sender, ok ? Lang.text("server-features.balance-updated", "&aBalance updated.") : Lang.text("server-features.insufficient-funds-or-balance-limit", "&cInsufficient funds or balance limit."));
        } catch (IllegalArgumentException ex) { plugin.msg(sender, Lang.text("server-features.invalid-action-rank-or-amount", "&cInvalid action, rank or amount.")); }
    }
    public void shutdown() { save(); if (plugin.platform().folia()) return; for (Player player : Bukkit.getOnlinePlayers()) { player.resetPlayerTime(); player.resetPlayerWeather(); } }
}


===== src/main/java/com/donsup/features/TravelManager.java =====

package com.donsup.features;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import org.bukkit.*;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.player.*;
import com.donsup.platform.TaskHandle;
import java.util.*;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Supplier;

public final class TravelManager implements Listener {
    private final DonsupPlugin plugin;
    private final Map<UUID, Long> combat = new HashMap<>();
    private final Map<UUID, TaskHandle> warmups = new HashMap<>();
    private final RtpManager rtp;
    private final Map<UUID, Map<UUID, Request>> requests = new HashMap<>();
    private final Map<UUID, Long> requestCooldown = new HashMap<>();
    private record Request(UUID from, boolean here, long expires) { }
    public TravelManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.rtp = new RtpManager(plugin);
        plugin.platform().globalTimer(() -> {
            long now = System.currentTimeMillis();
            combat.entrySet().removeIf(e -> e.getValue() <= now);
            rtp.tick();
            requests.values().forEach(map -> map.values().removeIf(r -> r.expires < now));
            requests.values().removeIf(Map::isEmpty);
        }, 20, 20);
    }
    public boolean tagged(Player player) { return combat.getOrDefault(player.getUniqueId(), 0L) > System.currentTimeMillis(); }
    public void clearCombat(Player player) { combat.remove(player.getUniqueId()); }
    public long seconds(Player player) { return Math.max(0, (combat.getOrDefault(player.getUniqueId(), 0L) - System.currentTimeMillis() + 999) / 1000); }
    public boolean available(Player player) {
        if (!player.isOnline() || player.isDead()) return false;
        if (plugin.duels().inDuel(player)) { plugin.msg(player, Lang.text("travel.leave-the-duel-before-teleporting", "&cLeave the duel before teleporting.")); return false; }
        if (tagged(player)) { plugin.msg(player, Lang.text("travel.teleporting-is-blocked-during-combat-for-seconds", "&cTeleporting is blocked during combat for {0} seconds.", seconds(player))); return false; }
        return true;
    }
    public void teleport(Player player, Location destination) { warmup(player, () -> destination, () -> { }); }
    public void teleport(Player player, Location destination, Runnable complete) { warmup(player, () -> destination, complete); }
    private void warmup(Player player, Supplier<Location> destination, Runnable complete) {
        if (!available(player)) return;
        cancel(player, false);
        rtp.cancel(player.getUniqueId(), Lang.text("travel.rtp-cancelled-by-another-teleport-request", "RTP cancelled by another teleport request."));
        int delay = Math.max(0, Math.min(60, plugin.getConfig().getInt("travel.warmup-seconds", 3)));
        plugin.msg(player, Lang.text("travel.teleporting-in-seconds-stay-still", "&7Teleporting in {0} seconds. Stay still.", delay));
        warmups.put(player.getUniqueId(), plugin.platform().playerLater(player, () -> {
            warmups.remove(player.getUniqueId());
            if (!available(player)) return;
            Location location = destination.get();
            if (location == null || location.getWorld() == null || !com.donsup.compat.BukkitCompat.inside(location.getWorld().getWorldBorder(), location)) {
                plugin.msg(player, Lang.text("travel.destination-is-unavailable", "&cDestination is unavailable.")); return;
            }
            plugin.platform().teleport(player, location).thenAccept(success -> {
                if (plugin.isEnabled()) plugin.platform().player(player, () -> {
                    if (!player.isOnline()) return;
                    if (success) { complete.run(); plugin.msg(player, Lang.text("travel.teleported", "&aTeleported.")); }
                    else plugin.msg(player, Lang.text("travel.teleport-was-cancelled", "&cTeleport was cancelled."));
                });
            });
        }, Math.max(1, delay * 20L)));
    }
    public void request(Player from, Player to, boolean here) {
        if (to == null || to.equals(from) || !from.canSee(to) || !available(from)) { plugin.msg(from, Lang.text("travel.player-unavailable", "&cPlayer unavailable.")); return; }
        if (!plugin.economy().setting(to.getUniqueId(), "teleport_requests") || plugin.extensions().blocks(to.getUniqueId(), from.getUniqueId())) {
            plugin.msg(from, Lang.text("travel.this-player-is-not-accepting-teleport-requests", "&cThis player is not accepting teleport requests.")); return;
        }
        long now = System.currentTimeMillis();
        if (requestCooldown.getOrDefault(from.getUniqueId(), 0L) > now) { plugin.msg(from, Lang.text("travel.wait-before-requesting-again", "&cWait before requesting again.")); return; }
        var pending = requests.computeIfAbsent(to.getUniqueId(), id -> new HashMap<>());
        pending.values().removeIf(r -> r.expires <= now);
        if (pending.size() >= 10) { plugin.msg(from, Lang.text("travel.this-player-has-too-many-requests", "&cThis player has too many requests.")); return; }
        pending.put(from.getUniqueId(), new Request(from.getUniqueId(), here, now + 60000));
        requestCooldown.put(from.getUniqueId(), now + 5000);
        plugin.msg(from, Lang.text("travel.request-sent-expires-in-60-seconds", "&aRequest sent; expires in 60 seconds."));
        plugin.msg(to, Lang.text("travel.tpaccept", "&e{0}{1} &f/tpaccept {2}", from.getName(), (here ? Lang.text("travel.asks-you-to-teleport-to-them", " &7asks you to teleport to them.") : Lang.text("travel.asks-to-teleport-to-you", " &7asks to teleport to you.")), from.getName()));
    }
    public void respond(Player to, String name, boolean accept) {
        var pending = requests.get(to.getUniqueId());
        if (pending == null) { plugin.msg(to, Lang.text("travel.no-pending-requests", "&cNo pending requests.")); return; }
        Request request;
        if (name.isBlank()) request = pending.values().stream().filter(r -> r.expires > System.currentTimeMillis()).max(Comparator.comparingLong(Request::expires)).orElse(null);
        else { Player from = Bukkit.getPlayerExact(name); request = from == null ? null : pending.get(from.getUniqueId()); }
        if (request == null || request.expires < System.currentTimeMillis()) { plugin.msg(to, Lang.text("travel.no-matching-request", "&cNo matching request.")); return; }
        pending.remove(request.from);
        Player from = Bukkit.getPlayer(request.from);
        if (!accept) { plugin.msg(to, Lang.text("travel.request-declined", "&7Request declined.")); return; }
        if (from == null || !available(to) || !to.canSee(from)) return;
        Player traveller = request.here ? to : from, destination = request.here ? from : to;
        if (plugin.platform().folia()) {
            plugin.platform().onPlayer(destination, () -> {
                if (!available(destination)) return;
                Location snapshot = destination.getLocation();
                plugin.platform().player(traveller, () -> {
                    if (available(traveller)) warmup(traveller, () -> snapshot, () -> {});
                });
            });
            return;
        }
        if (!available(from)) return;
        warmup(traveller, () -> destination.isOnline() && !destination.isDead() && !tagged(destination) ? destination.getLocation() : null, () -> { });
    }
    public RtpManager rtp() { return rtp; }
    public void random(Player player) { rtp.solo(player, "overworld"); }
    public void cancelWarmup(Player player) { cancel(player, false); }
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true) public void damage(EntityDamageEvent event) {
        if (event.getEntity() instanceof Player player) { cancel(player, true); rtp.cancel(player.getUniqueId(), Lang.text("travel.rtp-cancelled-because-a-player-took-damage", "RTP cancelled because a player took damage.")); }
        if (!(event.getEntity() instanceof Player victim) || !(com.donsup.compat.BukkitCompat.attacker(event) instanceof Player attacker) || victim.equals(attacker)) return;
        long expires = System.currentTimeMillis() + Math.max(1, plugin.getConfig().getInt("combat.tag-seconds", 15)) * 1000L;
        for (Player p : List.of(victim, attacker)) {
            if (!tagged(p) && plugin.economy().setting(p.getUniqueId(), "combat_alerts")) plugin.msg(p, Lang.text("travel.combat-tagged-teleports-are-temporarily-blocked", "&cCombat tagged. Teleports are temporarily blocked."));
            combat.put(p.getUniqueId(), expires);
            rtp.cancel(p.getUniqueId(), Lang.text("travel.rtp-cancelled-because-a-player-entered-combat", "RTP cancelled because a player entered combat."));
        }
    }
    @EventHandler(ignoreCancelled = true) public void move(PlayerMoveEvent event) {
        if (!event.getFrom().toVector().equals(event.getTo().toVector())) { cancel(event.getPlayer(), true); rtp.moved(event.getPlayer()); }
    }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true) public void teleportEvent(PlayerTeleportEvent event) {
        if (event.getCause() == PlayerTeleportEvent.TeleportCause.PLUGIN && !plugin.duels().expectedTeleport(event.getPlayer(),event.getTo()) && (tagged(event.getPlayer()) || plugin.duels().inDuel(event.getPlayer()))) event.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true) public void teleported(PlayerTeleportEvent event) { rtp.externalTeleport(event.getPlayer()); }
    @EventHandler public void death(PlayerDeathEvent event) { combat.remove(event.getEntity().getUniqueId()); cancel(event.getEntity(), false); rtp.cancel(event.getEntity().getUniqueId(), Lang.text("travel.rtp-cancelled-because-a-player-died", "RTP cancelled because a player died.")); }
    @EventHandler public void quit(PlayerQuitEvent event) {
        Player player = event.getPlayer(); UUID id = player.getUniqueId();
        if (tagged(player) && plugin.getConfig().getBoolean("combat.kill-on-logout", false) && !player.isDead()) player.setHealth(0);
        combat.remove(id); cancel(player, false); rtp.cancel(id, Lang.text("travel.rtp-cancelled-because-a-player-disconnected", "RTP cancelled because a player disconnected.")); requests.remove(id); requestCooldown.remove(id);
        requests.values().forEach(map -> map.remove(id));
    }
    private void cancel(Player player, boolean notify) {
        TaskHandle task = warmups.remove(player.getUniqueId());
        if (task != null) { task.cancel(); if (notify) plugin.msg(player, Lang.text("travel.teleport-cancelled-because-you-moved-or-took-damage", "&cTeleport cancelled because you moved or took damage.")); }
    }
    public void shutdown() { warmups.values().forEach(TaskHandle::cancel); warmups.clear(); rtp.shutdown(); requests.clear(); combat.clear(); }
}


===== src/main/java/com/donsup/gui/AfkSessions.java =====

package com.donsup.gui;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

public final class AfkSessions {
    private AfkSessions() {
    }

    public static final Set<UUID> ACTIVE = new HashSet<>();
}


===== src/main/java/com/donsup/gui/MenuManager.java =====

package com.donsup.gui;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.market.BulkOrder;
import com.donsup.market.MarketListing;
import com.donsup.util.ItemUtil;
import com.donsup.util.Text;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.OfflinePlayer;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryCloseEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.UUID;

public class MenuManager implements Listener {
    private final DonsupPlugin plugin;
    private final ItemKey actionKey;
    private final ItemKey crateKey;
    private final Random random = new Random();

    public MenuManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.actionKey = new ItemKey(plugin, "gui_action");
        this.crateKey = new ItemKey(plugin, "crate_key");
    }

    public void openMain(Player player) { plugin.dialogs().main(player); }
    public void openSettings(Player player) { plugin.dialogs().settings(player); }
    public void openProfile(Player player) { plugin.dialogs().profile(player, player); }
    public void openHomes(Player player) { plugin.dialogs().homes(player); }
    public void openListings(Player player, String type) { plugin.dialogs().listings(player, type, "", 0, false); }
    public void openOrders(Player player) { plugin.dialogs().orders(player, 0, false); }
    public ItemKey crateKey() {
        return crateKey;
    }

    public void openLegacyMain(Player player) {
        plugin.economy().ensure(player);
        Inventory inv = inv("Control Center", 6);
        fill(inv);
        inv.setItem(4, plugin.button(Material.NETHER_STAR, plugin.displayName(), List.of(
                Lang.text("menu.server", "&7Server: &f{0}", plugin.serverName()),
                Lang.text("menu.money", "&7Money: &a{0}", Text.money(plugin.economy().money(player.getUniqueId()))),
                Lang.text("menu.shards", "&7Shards: &d{0}", plugin.economy().shards(player.getUniqueId())),
                Lang.text("menu.premium", "&7Premium: {0}", (plugin.economy().premium(player) ? Lang.text("menu.active", "&aActive") : Lang.text("menu.inactive", "&cInactive")))
        ), actionKey, "BALANCE"));
        inv.setItem(10, plugin.button(Material.EMERALD, Lang.text("menu.server-shop", "&aServer Shop"), List.of(Lang.text("menu.buy-essentials-combat-items-and-farms", "&7Buy essentials, combat items and farms.")), actionKey, "OPEN:SHOP"));
        inv.setItem(11, plugin.button(Material.HOPPER, Lang.text("menu.sell-center", "&eSell Center"), List.of(Lang.text("menu.sell-inventory-clutter-instantly", "&7Sell inventory clutter instantly.")), actionKey, "SELL:ALL"));
        inv.setItem(12, plugin.button(Material.CHEST, Lang.text("menu.auction-house", "&6Auction House"), List.of(Lang.text("menu.browse-player-listings", "&7Browse player listings."), Lang.text("menu.use-ah-list-to-sell-held-item", "&8Use /ah list <price> to sell held item.")), actionKey, "OPEN:AUCTION"));
        inv.setItem(13, plugin.button(com.donsup.compat.Materials.BARREL, Lang.text("menu.bulk-orders", "&bBulk Orders"), List.of(Lang.text("menu.fulfill-buy-orders-in-quantity", "&7Fulfill buy orders in quantity."), Lang.text("menu.use-orders-create", "&8Use /orders create <material> <amount> <price>.")), actionKey, "OPEN:ORDERS"));
        inv.setItem(14, plugin.button(Material.ENDER_CHEST, Lang.text("menu.player-market", "&dPlayer Market"), List.of(Lang.text("menu.premium-style-market-board", "&7Premium-style market board."), Lang.text("menu.use-market-list-to-sell-held-item", "&8Use /market list <price> to sell held item.")), actionKey, "OPEN:MARKET"));
        inv.setItem(15, plugin.button(com.donsup.compat.Materials.AMETHYST_SHARD, Lang.text("menu.shard-shop", "&dShard Shop"), List.of(Lang.text("menu.spend-pvp-and-afk-shards", "&7Spend PvP and AFK shards.")), actionKey, "OPEN:SHARDS"));
        inv.setItem(16, plugin.button(Material.TRIPWIRE_HOOK, Lang.text("menu.crates", "&bCrates"), List.of(Lang.text("menu.open-reward-crates-with-keys", "&7Open reward crates with keys.")), actionKey, "OPEN:CRATES"));
        inv.setItem(28, plugin.button(com.donsup.compat.Materials.RED_BED, Lang.text("menu.homes", "&cHomes"), List.of(Lang.text("menu.set-view-and-teleport-home", "&7Set, view and teleport home.")), actionKey, "OPEN:HOMES"));
        inv.setItem(29, plugin.button(com.donsup.compat.Materials.TARGET, Lang.text("menu.bounties", "&cBounties"), List.of(Lang.text("menu.track-player-bounties", "&7Track player bounties.")), actionKey, "OPEN:BOUNTIES"));
        inv.setItem(30, plugin.button(com.donsup.compat.Materials.SPAWNER, Lang.text("menu.custom-spawners", "&dCustom Spawners"), List.of(Lang.text("menu.buy-and-manage-lag-friendly-drop-spawners", "&7Buy and manage lag-friendly drop spawners."), Lang.text("menu.price-shards", "&7Price: &d{0} shards", plugin.getConfig().getInt("custom-spawners.price-shards", 1500))), actionKey, "OPEN:SPAWNERS"));
        inv.setItem(31, plugin.button(com.donsup.compat.Materials.CLOCK, Lang.text("menu.afk-rewards", "&eAFK Rewards"), List.of(Lang.text("menu.toggle-afk-shard-earning", "&7Toggle AFK shard earning."), Lang.text("menu.current", "&7Current: {0}", (AfkSessions.ACTIVE.contains(player.getUniqueId()) ? Lang.text("menu.on", "&aOn") : Lang.text("menu.off", "&cOff")))), actionKey, "AFK:TOGGLE"));
        inv.setItem(32, plugin.button(Material.GOLD_INGOT, Lang.text("menu.pay", "&6Pay"), List.of(Lang.text("menu.use-pay", "&7Use &e/pay <player> <amount>&7.")), actionKey, "BALANCE"));
        inv.setItem(33, plugin.button(com.donsup.compat.Materials.COMPARATOR, Lang.text("menu.settings", "&fSettings"), List.of(Lang.text("menu.chat-messages-alerts-night-vision", "&7Chat, messages, alerts, night vision.")), actionKey, "OPEN:SETTINGS"));
        inv.setItem(34, plugin.button(Material.NAME_TAG, Lang.text("menu.premium-perks", "&bPremium Perks"), List.of(Lang.text("menu.view-configured-rank-benefits", "&7View configured rank benefits."), Lang.text("menu.click-to-inspect-rank-value", "&7Click to inspect rank value.")), actionKey, "OPEN:PREMIUM"));
        inv.setItem(37, plugin.button(Material.DIAMOND_SWORD, Lang.text("menu.duels", "&cDuels"), List.of(Lang.text("menu.challenge-players-and-fight-in-arenas", "&7Challenge players and fight in arenas."), Lang.text("menu.use-duel-wager", "&8Use /duel <player> [wager].")), actionKey, "OPEN:DUELS"));
        inv.setItem(38, plugin.button(com.donsup.compat.Materials.LECTERN, Lang.text("menu.leaderboards", "&eLeaderboards"), List.of(Lang.text("menu.top-money-shards-kills-and-bounties", "&7Top money, shards, kills and bounties.")), actionKey, "OPEN:LEADERBOARDS"));
        inv.setItem(41, plugin.button(Material.DIAMOND_PICKAXE, Lang.text("menu.drills", "&bDrills"), List.of(Lang.text("menu.buy-vein-miner-drills", "&7Buy vein miner drills."), Lang.text("menu.mine-ore-and-log-veins", "&7Mine ore and log veins.")), actionKey, "OPEN:DRILLS"));
        inv.setItem(40, plugin.button(com.donsup.compat.Materials.PLAYER_HEAD, Lang.text("menu.profile", "&eProfile"), List.of(Lang.text("menu.stats-balances-and-current-rank", "&7Stats, balances and current rank.")), actionKey, "OPEN:PROFILE"));
        if (player.hasPermission("donsup.admin")) {
            inv.setItem(39, plugin.button(com.donsup.compat.Materials.COMMAND_BLOCK, Lang.text("menu.creator-toolkit", "&6Creator Toolkit"), List.of(Lang.text("menu.build-shops-crates-and-economy-from-gui", "&7Build shops, crates and economy from GUI."), Lang.text("menu.click-to-open-admin-tools", "&7Click to open admin tools.")), actionKey, "OPEN:CREATOR"));
            inv.setItem(53, plugin.button(com.donsup.compat.Materials.COMMAND_BLOCK, Lang.text("menu.admin-reload", "&cAdmin Reload"), List.of(Lang.text("menu.reload-all-configs-and-storage", "&7Reload all configs and storage.")), actionKey, "ADMIN:RELOAD"));
        }
        player.openInventory(inv);
    }

    public void openLegacySettings(Player player) {
        Inventory inv = inv("Settings", 6);
        fill(inv);
        inv.setItem(4, plugin.button(com.donsup.compat.Materials.COMPARATOR, Lang.text("menu.player-settings", "&f&lPlayer Settings"), List.of(Lang.text("menu.competitive-smp-personal-toggles", "&7Competitive SMP personal toggles."), Lang.text("menu.click-any-item-to-flip-it", "&7Click any item to flip it.")), actionKey, "BALANCE"));
        int[] slots = {10, 11, 12, 13, 14, 15, 16, 28, 29, 30};
        int i = 0;
        for (Map.Entry<String, Boolean> entry : plugin.economy().settings(player.getUniqueId()).entrySet()) {
            if (i >= slots.length) {
                break;
            }
            Material icon = settingIcon(entry.getKey());
            String status = entry.getValue() ? Lang.text("menu.on-8eb5ba", "&a&lON") : Lang.text("menu.off-30106a", "&c&lOFF");
            inv.setItem(slots[i++], plugin.button(icon, Lang.text("menu.text", "&f{0}", title(entry.getKey())), List.of(
                    Lang.text("menu.currently", "&7Currently: {0}", status),
                    settingDescription(entry.getKey()),
                    Lang.text("menu.click-to-toggle", "&aClick to toggle")
            ), actionKey, "SETTING:" + entry.getKey()));
        }
        inv.setItem(49, back());
        player.openInventory(inv);
    }

    public void openLegacyProfile(Player player) {
        Inventory inv = inv("Profile", 6);
        fill(inv);
        inv.setItem(4, plugin.button(com.donsup.compat.Materials.PLAYER_HEAD, Lang.text("menu.text-4cfa8b", "&e&l{0}", player.getName()), List.of(
                Lang.text("menu.money", "&7Money: &a{0}", Text.money(plugin.economy().money(player.getUniqueId()))),
                Lang.text("menu.shards", "&7Shards: &d{0}", plugin.economy().shards(player.getUniqueId())),
                Lang.text("menu.premium", "&7Premium: {0}", (plugin.economy().premium(player) ? Lang.text("menu.active", "&aActive") : Lang.text("menu.inactive", "&cInactive"))),
                Lang.text("menu.kills", "&7Kills: &c{0}", plugin.economy().stat(player.getUniqueId(), "kills")),
                Lang.text("menu.deaths", "&7Deaths: &f{0}", plugin.economy().stat(player.getUniqueId(), "deaths")),
                Lang.text("menu.sell-boost", "&7Sell boost: &e{0}", String.format("%.2fx", plugin.economy().effectiveSellMultiplier(player)))
        ), actionKey, "BALANCE"));
        inv.setItem(20, plugin.button(Material.CHEST, Lang.text("menu.auctions", "&6Auctions"), List.of(Lang.text("menu.listings-limit", "&7Listings limit: &e{0}", plugin.economy().listingLimit(player, "auction")), Lang.text("menu.tax", "&7Tax: &e{0}%", plugin.economy().listingTaxPercent(player))), actionKey, "OPEN:AUCTION"));
        inv.setItem(22, plugin.button(com.donsup.compat.Materials.RED_BED, Lang.text("menu.homes", "&cHomes"), List.of(Lang.text("menu.homes-f83395", "&7Homes: &e{0}&7/&e{1}", plugin.economy().homeNames(player.getUniqueId()).size(), plugin.economy().homeLimit(player))), actionKey, "OPEN:HOMES"));
        inv.setItem(24, plugin.button(Material.ENDER_CHEST, Lang.text("menu.premium-vault", "&dPremium Vault"), List.of(Lang.text("menu.secure-personal-item-storage", "&7Secure personal item storage."), Lang.text("menu.premium-only", "&7Premium only.")), actionKey, "OPEN:VAULT"));
        inv.setItem(49, back());
        player.openInventory(inv);
    }

    public void openPremium(Player player) {
        Inventory inv = inv("Premium", 6);
        fill(inv);
        inv.setItem(4, plugin.button(Material.NETHER_STAR, Lang.text("menu.premium-suite", "&b&lPremium Suite"), List.of(
                Lang.text("menu.status", "&7Status: {0}", (plugin.economy().premium(player) ? Lang.text("menu.active", "&aActive") : Lang.text("menu.inactive", "&cInactive"))),
                Lang.text("menu.rank-benefits-on-this-server", "&7Rank benefits on this server.")
        ), actionKey, "BALANCE"));
        premium(inv, 10, com.donsup.compat.Materials.RED_BED, Lang.text("menu.expanded-homes", "Expanded Homes"), Lang.text("menu.homes-3bd810", "+{0} homes", plugin.getConfig().getInt("settings.premium-home-bonus", 3)));
        premium(inv, 11, Material.GOLD_NUGGET, Lang.text("menu.reduced-listing-tax", "Reduced Listing Tax"), Lang.text("menu.ah-market-tax", "{0}% AH/market tax", plugin.getConfig().getDouble("settings.premium-listing-tax-percent", 0.5)));
        premium(inv, 12, Material.CHEST, Lang.text("menu.listing-expansion", "Listing Expansion"), Lang.text("menu.active-listings", "+{0} active listings", plugin.getConfig().getInt("settings.premium-listing-bonus", 18)));
        premium(inv, 13, Material.EMERALD, Lang.text("menu.sell-multiplier", "Sell Multiplier"), Lang.text("menu.x-server-sell-value", "{0}x server sell value", plugin.getConfig().getDouble("settings.premium-sell-multiplier", 1.25)));
        premium(inv, 14, com.donsup.compat.Materials.AMETHYST_SHARD, Lang.text("menu.passive-shards", "Passive Shards"), Lang.text("menu.shards-min-online", "+{0} shards/min online", plugin.getConfig().getInt("settings.premium-online-shards-per-minute", 1)));
        premium(inv, 15, Material.ENDER_CHEST, Lang.text("menu.premium-vault-f0fab9", "Premium Vault"), Lang.text("menu.rows-private-storage", "{0} rows private storage", plugin.getConfig().getInt("settings.premium-vault-rows", 3)));
        premium(inv, 16, com.donsup.compat.Materials.SPYGLASS, Lang.text("menu.market-alerts", "Market Alerts"), Lang.text("menu.live-alerts-when-players-list-items", "Live alerts when players list items"));
        premium(inv, 28, com.donsup.compat.Materials.TARGET, Lang.text("menu.bounty-radar", "Bounty Radar"), Lang.text("menu.bounty-alerts-and-profile-visibility", "Bounty alerts and profile visibility"));
        premium(inv, 29, Material.POTION, Lang.text("menu.night-vision", "Night Vision"), Lang.text("menu.toggleable-infinite-night-vision", "Toggleable infinite night vision"));
        premium(inv, 30, Material.TRIPWIRE_HOOK, Lang.text("menu.portable-crafting", "Portable Crafting"), Lang.text("menu.open-a-workbench-wherever-you-are", "Open a workbench wherever you are"));
        inv.setItem(32, plugin.button(Material.ENDER_CHEST, Lang.text("menu.open-premium-vault", "&dOpen Premium Vault"), List.of(Lang.text("menu.requires-premium", "&7Requires premium.")), actionKey, "OPEN:VAULT"));
        inv.setItem(33, plugin.button(Material.POTION, Lang.text("menu.toggle-night-vision", "&bToggle Night Vision"), List.of(Lang.text("menu.uses-your-setting-state", "&7Uses your setting state.")), actionKey, "SETTING:night_vision"));
        inv.setItem(34, plugin.button(Material.DIAMOND, Lang.text("menu.claim-premium-kit", "&aClaim Premium Kit"), List.of(Lang.text("menu.use-premiumkit-or-click-here", "&7Use /premiumkit or click here.")), actionKey, "PREMIUM:KIT"));
        inv.setItem(35, plugin.button(Material.ANVIL, Lang.text("menu.repair-held-item", "&eRepair Held Item"), List.of(Lang.text("menu.use-repair-or-click-here", "&7Use /repair or click here.")), actionKey, "PREMIUM:REPAIR"));
        inv.setItem(41, plugin.button(Material.COOKED_BEEF, Lang.text("menu.feed", "&6Feed"), List.of(Lang.text("menu.use-feed-or-click-here", "&7Use /feed or click here.")), actionKey, "PREMIUM:FEED"));
        inv.setItem(42, plugin.button(com.donsup.compat.Materials.CRAFTING_TABLE, Lang.text("menu.workbench", "&fWorkbench"), List.of(Lang.text("menu.use-workbench-or-click-here", "&7Use /workbench or click here.")), actionKey, "PREMIUM:WORKBENCH"));
        inv.setItem(49, back());
        player.openInventory(inv);
    }

    public void openPremiumVault(Player player) {
        if (!plugin.economy().premium(player)) {
            plugin.msg(player, Lang.text("menu.premium-vault-requires-premium", "&cPremium vault requires premium."));
            return;
        }
        int rows = Math.max(1, Math.min(6, plugin.getConfig().getInt("settings.premium-vault-rows", 3)));
        Inventory inv = plugin.inventory(rows * 9, inventoryTitle("Premium Vault"), true);
        List<ItemStack> stored = plugin.economy().vault(player.getUniqueId());
        for (int i = 0; i < Math.min(inv.getSize(), stored.size()); i++) {
            inv.setItem(i, stored.get(i));
        }
        player.openInventory(inv);
    }

    public void openShop(Player player) {
        Inventory inv = inv("Shop", 6);
        fill(inv);
        inv.setItem(4, plugin.button(Material.EMERALD, Lang.text("menu.server-shop-ba6ea8", "&a&lServer Shop"), List.of(Lang.text("menu.pick-a-category", "&7Pick a category.")), actionKey, "OPEN:MAIN"));
        ConfigurationSection categories = plugin.shops().getConfigurationSection("categories");
        int slot = 20;
        if (categories != null) {
            for (String key : categories.getKeys(false)) {
                Material icon = ItemUtil.material(categories.getString(key + ".icon"), Material.CHEST);
                String name = categories.getString(key + ".name", "&a" + key);
                inv.setItem(slot++, plugin.button(icon, name, List.of(Lang.text("menu.open-category", "&7Open category.")), actionKey, "SHOP_CAT:" + key));
            }
        }
        inv.setItem(49, back());
        player.openInventory(inv);
    }

    public void openShopCategory(Player player, String category) {
        Inventory inv = inv("Shop " + category, 6);
        fill(inv);
        ConfigurationSection items = plugin.shops().getConfigurationSection("categories." + category + ".items");
        int slot = 10;
        if (items != null) {
            for (String key : items.getKeys(false)) {
                Material material = com.donsup.compat.Materials.match(items.getString(key + ".material"));
                if (material == null || !com.donsup.compat.BukkitCompat.item(material)) continue;
                int amount = items.getInt(key + ".amount", 1);
                double buy = items.getDouble(key + ".buy", 0);
                double sell = items.getDouble(key + ".sell", 0);
                double liveBuy = plugin.creator().dynamicPrice(material, buy);
                double liveSell = plugin.creator().dynamicPrice(material, sell);
                ItemStack item = plugin.button(material, Lang.text("menu.text", "&f{0}", nice(material)), List.of(
                        Lang.text("menu.amount", "&7Amount: &e{0}", amount),
                        Lang.text("menu.buy", "&7Buy: &a{0}", Text.money(liveBuy)),
                        Lang.text("menu.sell-each", "&7Sell each: &6{0}", Text.money(liveSell)),
                        plugin.creator().dynamicEnabled() ? Lang.text("menu.dynamic-pricing-active", "&eDynamic pricing active") : Lang.text("menu.dynamic-pricing-disabled", "&8Dynamic pricing disabled"),
                        "",
                        Lang.text("menu.left-click-buy", "&aLeft click: buy"),
                        Lang.text("menu.right-click-sell-one-stack", "&eRight click: sell one stack")
                ), actionKey, "SHOP_ITEM:" + category + ":" + key);
                item.setDurability(com.donsup.compat.Materials.stack(items.getString(key+".material"),1).getDurability());
                item.setAmount(Math.min(64, Math.max(1, amount)));
                inv.setItem(slot, item);
                slot++;
                if ((slot + 1) % 9 == 0) {
                    slot += 2;
                }
            }
        }
        inv.setItem(49, plugin.button(Material.ARROW, Lang.text("menu.back", "&7Back"), List.of(), actionKey, "OPEN:SHOP"));
        player.openInventory(inv);
    }

    public void openLegacyListings(Player player, String type) {
        Inventory inv = inv(type.equals("auction") ? "Auction House" : "Player Market", 6);
        fill(inv);
        int slot = 0;
        for (MarketListing listing : plugin.market().listings(type)) {
            if (slot >= 45) {
                break;
            }
            ItemStack item = listing.item().clone();
            ItemMeta meta = item.getItemMeta();
            List<String> lore = meta.hasLore() ? new ArrayList<>(meta.getLore()) : new ArrayList<>();
            lore.add("");
            lore.add(Text.color(Lang.text("menu.seller", "&7Seller: &f{0}", listing.ownerName())));
            lore.add(Text.color(Lang.text("menu.price", "&7Price: &a{0}", Text.money(listing.price()))));
            lore.add(Text.color(Lang.text("menu.id", "&8ID: {0}", listing.id())));
            lore.add(Text.color(Lang.text("menu.click-to-buy", "&aClick to buy")));
            meta.setLore(lore);
            com.donsup.compat.ItemTags.setString(meta, actionKey, "BUY_LISTING:" + listing.id());
            item.setItemMeta(meta);
            inv.setItem(slot++, item);
        }
        inv.setItem(45, plugin.button(Material.GOLD_INGOT, Lang.text("menu.list-held-item", "&eList Held Item"), List.of(Lang.text("menu.use-list", "&7Use &e/{0} list <price>&7.", (type.equals("auction") ? "ah" : "market"))), actionKey, "BALANCE"));
        inv.setItem(49, back());
        player.openInventory(inv);
    }

    public void openLegacyOrders(Player player) {
        Inventory inv = inv("Bulk Orders", 6);
        fill(inv);
        int slot = 0;
        long now = System.currentTimeMillis();
        for (BulkOrder order : plugin.market().orders()) {
            if (slot >= 45) {
                break;
            }
            boolean active = order.expiresAt() > now && order.remaining() > 0;
            String action = order.owner().equals(player.getUniqueId()) ? "ORDER_CLAIM:" + order.id() : "ORDER_DELIVER:" + order.id();
            inv.setItem(slot++, plugin.button(order.material(), Lang.text("menu.text-539ee5", "&b{0}", nice(order.material())), List.of(
                    Lang.text("menu.buyer", "&7Buyer: &f{0}", order.ownerName()),
                    Lang.text("menu.remaining", "&7Remaining: &e{0}&7/&e{1}", order.remaining(), order.requested()),
                    Lang.text("menu.price-each", "&7Price each: &a{0}", Text.money(order.priceEach())),
                    Lang.text("menu.status", "&7Status: {0}", (active ? Lang.text("menu.accepting-deliveries", "&aAccepting deliveries") : Lang.text("menu.claim-only", "&eClaim only"))),
                    order.owner().equals(player.getUniqueId()) ? Lang.text("menu.click-to-claim-delivered-items", "&aClick to claim delivered items") : Lang.text("menu.click-to-deliver-matching-items", "&aClick to deliver matching items")
            ), actionKey, action));
        }
        inv.setItem(45, plugin.button(com.donsup.compat.Materials.WRITABLE_BOOK, Lang.text("menu.create-order", "&eCreate Order"), List.of(Lang.text("menu.use-orders-create-b3ef9b", "&7Use &e/orders create <material> <amount> <priceEach>&7.")), actionKey, "BALANCE"));
        inv.setItem(49, back());
        player.openInventory(inv);
    }

    public void openShardShop(Player player) {
        Inventory inv = inv("Shard Shop", 6);
        fill(inv);
        inv.setItem(4, plugin.button(com.donsup.compat.Materials.AMETHYST_SHARD, Lang.text("menu.shard-shop", "&dShard Shop"), List.of(Lang.text("menu.your-shards", "&7Your shards: &d{0}", plugin.economy().shards(player.getUniqueId()))), actionKey, "BALANCE"));
        ConfigurationSection section = plugin.getConfig().getConfigurationSection("shard-shop");
        int slot = 10;
        if (section != null) {
            for (String key : section.getKeys(false)) {
                if (!shardAvailable(section.getConfigurationSection(key))) continue;
                Material icon = ItemUtil.material(section.getString(key + ".icon"), com.donsup.compat.Materials.AMETHYST_SHARD);
                int shards = section.getInt(key + ".shards", 0);
                inv.setItem(slot++, plugin.button(icon, section.getString(key + ".name", "&d" + key), List.of(
                        Lang.text("menu.cost-shards", "&7Cost: &d{0} shards", shards),
                        Lang.text("menu.click-to-purchase", "&aClick to purchase")
                ), actionKey, "SHARD_BUY:" + key));
            }
        }
        inv.setItem(49, back());
        player.openInventory(inv);
    }

    public void openCrates(Player player) {
        Inventory inv = inv("Crates", 6);
        fill(inv);
        ConfigurationSection section = plugin.getConfig().getConfigurationSection("crates");
        int slot = 20;
        if (section != null) {
            for (String key : section.getKeys(false)) {
                Material icon = ItemUtil.material(section.getString(key + ".icon"), Material.CHEST);
                inv.setItem(slot++, plugin.button(icon, section.getString(key + ".display", "&b" + key), List.of(
                        plugin.crates().accountMode() ? Lang.text("menu.keys", "&7Keys: &b{0}", plugin.crates().balance(player.getUniqueId(), key)) : Lang.text("menu.requires-a-matching-physical-key", "&7Requires a matching physical key."),
                        Lang.text("menu.click-to-open", "&aClick to open")
                ), actionKey, "CRATE_OPEN:" + key));
            }
        }
        inv.setItem(49, back());
        player.openInventory(inv);
    }

    public void openLegacyHomes(Player player) {
        Inventory inv = inv("Homes", 6);
        fill(inv);
        inv.setItem(4, plugin.button(com.donsup.compat.Materials.RED_BED, Lang.text("menu.homes", "&cHomes"), List.of(Lang.text("menu.limit", "&7Limit: &e{0}&7/&e{1}", plugin.economy().homeNames(player.getUniqueId()).size(), plugin.economy().homeLimit(player))), actionKey, "BALANCE"));
        int slot = 10;
        for (String home : plugin.economy().homeNames(player.getUniqueId())) {
            inv.setItem(slot++, plugin.button(com.donsup.compat.Materials.OAK_DOOR, Lang.text("menu.text", "&f{0}", home), List.of(Lang.text("menu.click-to-teleport", "&aClick to teleport."), Lang.text("menu.use-delhome-to-remove", "&8Use /delhome {0} to remove.", home)), actionKey, "HOME_TP:" + home));
        }
        inv.setItem(45, plugin.button(com.donsup.compat.Materials.LIME_BED, Lang.text("menu.set-home", "&aSet Home"), List.of(Lang.text("menu.use-sethome", "&7Use &e/sethome <name>&7.")), actionKey, "BALANCE"));
        inv.setItem(49, back());
        player.openInventory(inv);
    }

    public void openBounties(Player player) {
        Inventory inv = inv("Bounties", 6);
        fill(inv);
        int slot = 0;
        for (Map.Entry<UUID, Double> entry : plugin.economy().bounties().entrySet()) {
            if (slot >= 45) {
                break;
            }
            OfflinePlayer target = Bukkit.getOfflinePlayer(entry.getKey());
            inv.setItem(slot++, plugin.button(com.donsup.compat.Materials.TARGET, Lang.text("menu.text-83e4bb", "&c{0}", plugin.economy().bountyName(entry.getKey())), List.of(
                    Lang.text("menu.reward", "&7Reward: &a{0}", Text.money(entry.getValue())),
                    Lang.text("menu.online", "&7Online: {0}", (target.isOnline() ? Lang.text("menu.yes", "&aYes") : Lang.text("menu.no", "&cNo"))),
                    Lang.text("menu.kill-the-target-to-claim", "&8Kill the target to claim.")
            ), actionKey, "BALANCE"));
        }
        inv.setItem(45, plugin.button(com.donsup.compat.Materials.WRITABLE_BOOK, Lang.text("menu.create-bounty", "&eCreate Bounty"), List.of(Lang.text("menu.use-bounty-set", "&7Use &e/bounty set <player> <amount>&7.")), actionKey, "BALANCE"));
        inv.setItem(49, back());
        player.openInventory(inv);
    }

    public void openLeaderboards(Player player) {
        Inventory inv = inv("Leaderboards", 6);
        fill(inv);
        inv.setItem(4, plugin.button(com.donsup.compat.Materials.LECTERN, Lang.text("menu.leaderboards-bce360", "&e&lLeaderboards"), List.of(Lang.text("menu.server-economy-and-pvp-standings", "&7Server economy and PvP standings.")), actionKey, "BALANCE"));
        renderTop(inv, 10, Material.GOLD_INGOT, Lang.text("menu.top-money", "&6Top Money"), plugin.economy().topMoney(5), true);
        renderTop(inv, 12, com.donsup.compat.Materials.AMETHYST_SHARD, Lang.text("menu.top-shards", "&dTop Shards"), plugin.economy().topShards(5), false);
        renderTop(inv, 14, Material.DIAMOND_SWORD, Lang.text("menu.top-kills", "&cTop Kills"), plugin.economy().topStat("kills", 5), false);
        Map<UUID, Double> bountyTop = plugin.economy().bounties();
        renderTop(inv, 16, com.donsup.compat.Materials.TARGET, Lang.text("menu.top-bounties", "&cTop Bounties"), bountyTop, true);
        inv.setItem(49, back());
        player.openInventory(inv);
    }

    private void renderTop(Inventory inv, int slot, Material icon, String title, Map<UUID, Double> values, boolean money) {
        List<String> lore = new ArrayList<>();
        int rank = 1;
        for (Map.Entry<UUID, Double> entry : values.entrySet()) {
            if (rank > 5) break;
            String value = money ? Text.money(entry.getValue()) : String.valueOf(entry.getValue().intValue());
            lore.add("&e#" + rank + " &f" + plugin.economy().playerName(entry.getKey()) + " &7- &a" + value);
            rank++;
        }
        if (lore.isEmpty()) lore.add(Lang.text("menu.no-data-yet", "&7No data yet."));
        inv.setItem(slot, plugin.button(icon, title, lore, actionKey, "BALANCE"));
    }

    public ItemStack keyItem(String type, int amount) {
        ItemStack item = ItemUtil.named(Material.TRIPWIRE_HOOK, amount, Lang.text("menu.crate-key", "&b{0} Crate Key", Lang.label("labels", type, type)), List.of(Lang.text("menu.use-at-crates", "&7Use at /crates.")));
        ItemMeta meta = item.getItemMeta();
        com.donsup.compat.ItemTags.setString(meta, crateKey, type);
        item.setItemMeta(meta);
        return item;
    }

    public String physicalKeyType(ItemStack item) {
        return item == null || !item.hasItemMeta() ? null : com.donsup.compat.ItemTags.getString(item.getItemMeta(), crateKey);
    }

    @EventHandler
    public void onClick(InventoryClickEvent event) {
        if (!com.donsup.gui.OwnedInventory.buttonClick(event)) return;
        if (!(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        String title = com.donsup.gui.OwnedInventory.title(event.getView());
        if (!title.startsWith(titlePrefix())) {
            return;
        }
        if (title.equals(inventoryTitle("Premium Vault"))) {
            return;
        }
        event.setCancelled(true);
        ItemStack current = event.getCurrentItem();
        if (current == null || com.donsup.compat.BukkitCompat.air(current.getType()) || !current.hasItemMeta()) {
            return;
        }
        String action = com.donsup.compat.ItemTags.getString(current.getItemMeta(), actionKey);
        if (action == null) {
            return;
        }
        boolean rightClick = event.isRightClick();
        plugin.platform().player(player, () -> { if (player.isOnline()) handle(player, action, rightClick); });
    }

    @EventHandler
    public void onClose(InventoryCloseEvent event) {
        if (!(event.getInventory().getHolder() instanceof com.donsup.gui.OwnedInventory)) return;
        if (!(event.getPlayer() instanceof Player player)) {
            return;
        }
        if (com.donsup.gui.OwnedInventory.title(event.getView()).equals(inventoryTitle("Premium Vault"))) {
            plugin.economy().setVault(player.getUniqueId(), event.getInventory().getContents());
        }
    }

    private void handle(Player player, String action, boolean rightClick) {
        String[] parts = action.split(":", 4);
        switch (parts[0]) {
            case "OPEN" -> {
                if (parts.length < 2) {
                    return;
                }
                switch (parts[1]) {
                    case "MAIN" -> openMain(player);
                    case "SHOP" -> openShop(player);
                    case "AUCTION" -> openListings(player, "auction");
                    case "MARKET" -> openListings(player, "market");
                    case "ORDERS" -> openOrders(player);
                    case "SHARDS" -> openShardShop(player);
                    case "CRATES" -> openCrates(player);
                    case "HOMES" -> openHomes(player);
                    case "BOUNTIES" -> openBounties(player);
                    case "SETTINGS" -> openSettings(player);
                    case "PROFILE" -> openProfile(player);
                    case "PREMIUM" -> openPremium(player);
                    case "VAULT" -> openPremiumVault(player);
                    case "SPAWNERS" -> plugin.spawners().openShop(player);
                    case "CREATOR" -> plugin.creator().openHub(player);
                    case "LEADERBOARDS" -> openLeaderboards(player);
                    case "DUELS" -> plugin.duels().open(player);
                    case "DRILLS" -> plugin.tools().open(player);
                    default -> openMain(player);
                }
            }
            case "PREMIUM" -> {
                if (parts.length >= 2) handlePremiumAction(player, parts[1]);
            }
            case "SETTING" -> {
                if (parts.length >= 2) toggleSetting(player, parts[1]);
            }
            case "SHOP_CAT" -> {
                if (parts.length >= 2) openShopCategory(player, parts[1]);
            }
            case "SHOP_ITEM" -> {
                if (parts.length >= 3) buyOrSellShop(player, parts[1], parts[2], rightClick);
            }
            case "SELL" -> plugin.sellChest().open(player);
            case "BUY_LISTING" -> {
                if (parts.length >= 2) buyListing(player, parts[1]);
            }
            case "ORDER_DELIVER" -> {
                if (parts.length >= 2) deliverOrder(player, parts[1]);
            }
            case "ORDER_CLAIM" -> {
                if (parts.length >= 2) claimOrder(player, parts[1]);
            }
            case "SHARD_BUY" -> {
                if (parts.length >= 2) buyShardItem(player, parts[1]);
            }
            case "CRATE_OPEN" -> {
                if (parts.length >= 2) openCrate(player, parts[1]);
            }
            case "HOME_TP" -> {
                if (parts.length >= 2) teleportHome(player, parts[1]);
            }
            case "AFK" -> toggleAfk(player);
            case "ADMIN" -> {
                if (player.hasPermission("donsup.admin")) {
                    plugin.reloadAll();
                    plugin.msg(player, Lang.text("menu.reloaded-smp-builder-configs", "&aReloaded SMP builder configs."));
                    openMain(player);
                }
            }
            default -> {
            }
        }
    }

    private void buyOrSellShop(Player player, String category, String key, boolean sell) {
        String path = "categories." + category + ".items." + key;
        Material material = com.donsup.compat.Materials.match(plugin.shops().getString(path + ".material"));
        if (material == null || !com.donsup.compat.BukkitCompat.item(material)) {
            plugin.msg(player,Lang.text("menu.this-shop-item-is-unavailable-on-this-server-version", "&cThis shop item is unavailable on this server version.")); return;
        }
        int amount = plugin.shops().getInt(path + ".amount", 1);
        if (!sell) {
            double price = plugin.creator().dynamicPrice(material, plugin.shops().getDouble(path + ".buy", 0));
            if (!plugin.economy().withdraw(player.getUniqueId(), price)) {
                plugin.msg(player, Lang.text("menu.you-do-not-have-enough-money", "&cYou do not have enough money."));
                return;
            }
            giveOrDrop(player, com.donsup.compat.Materials.stack(plugin.shops().getString(path+".material"),amount));
            plugin.creator().recordTrade(material, amount, true);
            plugin.msg(player, Lang.text("menu.purchased-x-for", "&aPurchased &e{0}x {1}&a for {2}.", amount, nice(material), Text.money(price)));
        } else {
            double sellEach = plugin.creator().dynamicPrice(material, plugin.shops().getDouble(path + ".sell", 0));
            int removed = removeItems(player, com.donsup.compat.Materials.stack(plugin.shops().getString(path+".material"),1), amount);
            if (removed <= 0) {
                plugin.msg(player, Lang.text("menu.you-do-not-have-enough-items-to-sell", "&cYou do not have enough items to sell."));
                return;
            }
            double earned = removed * sellEach * plugin.economy().effectiveSellMultiplier(player);
            plugin.economy().deposit(player.getUniqueId(), earned);
            plugin.creator().recordTrade(material, removed, false);
            plugin.msg(player, Lang.text("menu.sold-x-for", "&aSold &e{0}x {1}&a for {2}.", removed, nice(material), Text.money(earned)));
        }
        openShopCategory(player, category);
    }

    private void handlePremiumAction(Player player, String action) {
        switch (action) {
            case "KIT" -> player.performCommand("premiumkit");
            case "REPAIR" -> player.performCommand("repair");
            case "FEED" -> player.performCommand("feed");
            case "WORKBENCH" -> player.performCommand("workbench");
            default -> {
            }
        }
    }

    private void toggleSetting(Player player, String key) {
        if (key.equals("night_vision") && !plugin.economy().premium(player)) {
            plugin.msg(player, Lang.text("menu.night-vision-is-a-premium-setting", "&cNight vision is a premium setting."));
            return;
        }
        boolean enabled = plugin.economy().toggleSetting(player.getUniqueId(), key);
        if (key.equals("night_vision")) {
            applyNightVision(player);
        }
        plugin.msg(player, Lang.text("menu.is-now", "&f{0} &7is now {1}&7.", title(key), (enabled ? Lang.text("menu.on-f7a464", "&aON") : Lang.text("menu.off-5ef0bf", "&cOFF"))));
        openSettings(player);
    }

    public void applyNightVision(Player player) {
        if (plugin.getConfig().getBoolean("settings.premium-night-vision", true)
                && plugin.economy().premium(player) && plugin.economy().setting(player.getUniqueId(), "night_vision")) {
            player.addPotionEffect(new PotionEffect(PotionEffectType.NIGHT_VISION, Integer.MAX_VALUE, 0, false, false));
        } else {
            player.removePotionEffect(PotionEffectType.NIGHT_VISION);
        }
    }

    public double sellAll(Player player) {
        return plugin.recovery()==null?sellAllUncommitted(player):plugin.recovery().run(player,()->sellAllUncommitted(player));
    }

    private double sellAllUncommitted(Player player) {
        double total = 0;
        ItemStack[] contents = com.donsup.compat.BukkitCompat.storage(player.getInventory());
        for (ItemStack item : contents) total += plugin.market().sell(player, item);
        com.donsup.compat.BukkitCompat.storage(player.getInventory(), contents);
        plugin.msg(player, total > 0 ? Lang.text("menu.sold-items-for", "&aSold items for {0}", Text.money(total)) : Lang.text("menu.no-supported-plain-items-to-sell", "&7No supported plain items to sell."));
        return total;
    }
    public double sellHand(Player player) {
        return plugin.recovery()==null?sellHandUncommitted(player):plugin.recovery().run(player,()->sellHandUncommitted(player));
    }

    private double sellHandUncommitted(Player player) {
        ItemStack item = com.donsup.compat.BukkitCompat.hand(player.getInventory());
        double total = plugin.market().sell(player, item);
        com.donsup.compat.BukkitCompat.hand(player.getInventory(), item.getAmount() == 0 ? null : item);
        plugin.msg(player, total > 0 ? Lang.text("menu.sold-held-items-for", "&aSold held items for {0}", Text.money(total)) : Lang.text("menu.no-supported-plain-item-to-sell", "&7No supported plain item to sell."));
        return total;
    }
    public void buyListing(Player player, String id) {
        if(plugin.recovery()==null){buyListingUncommitted(player,id);return;}
        plugin.recovery().run(player,()->buyListingUncommitted(player,id));
    }

    private void buyListingUncommitted(Player player, String id) {
        MarketListing listing = plugin.market().listing(id);
        if (listing == null) {
            plugin.msg(player, Lang.text("menu.that-listing-is-no-longer-available", "&cThat listing is no longer available."));
            return;
        }
        if (listing.owner().equals(player.getUniqueId())) {
            plugin.msg(player, Lang.text("menu.you-cannot-buy-your-own-listing", "&cYou cannot buy your own listing."));
            return;
        }
        if (!com.donsup.util.InventoryCapacity.fits(player, listing.item(), listing.item().getAmount())) { plugin.msg(player, Lang.text("menu.make-inventory-space-first", "&cMake inventory space first.")); return; }
        if (!plugin.economy().exchange(player.getUniqueId(), listing.owner(), listing.price(), 0, 0, 0)) {
            plugin.msg(player, Lang.text("menu.you-do-not-have-enough-money", "&cYou do not have enough money."));
            return;
        }

        plugin.market().removeListing(id);
        giveOrDrop(player, listing.item().clone());
        plugin.msg(player, Lang.text("menu.purchased-listing-for", "&aPurchased listing &e{0}&a for {1}.", id, Text.money(listing.price())));
        openListings(player, listing.type());
    }

    public void deliverOrder(Player player, String id) {
        BulkOrder order = plugin.market().order(id);
        if (order == null || order.remaining() <= 0 || order.expiresAt() < System.currentTimeMillis()) {
            plugin.msg(player, Lang.text("menu.that-order-is-not-accepting-deliveries", "&cThat order is not accepting deliveries."));
            return;
        }
        int delivered = plugin.market().deliver(player, id);
        if (delivered <= 0) {
            plugin.msg(player, Lang.text("menu.you-do-not-have-matching-items", "&cYou do not have matching items."));
            return;
        }
        plugin.msg(player, Lang.text("menu.delivered-x-for", "&aDelivered &e{0}x {1}&a for {2}.", delivered, nice(order.material()), Text.money(delivered * order.priceEach())));
        openOrders(player);
    }

    public void claimOrder(Player player, String id) { plugin.market().claim(player, id); }

    private void buyShardItem(Player player, String key) {
        String path = "shard-shop." + key;
        if(!shardAvailable(plugin.getConfig().getConfigurationSection(path))) {
            plugin.msg(player,Lang.text("menu.this-shard-offer-is-unavailable-on-this-server-version", "&cThis shard offer is unavailable on this server version.")); return;
        }
        int shards = plugin.getConfig().getInt(path + ".shards", 0);
        if (!plugin.economy().takeShards(player.getUniqueId(), shards)) {
            plugin.msg(player, Lang.text("menu.you-do-not-have-enough-shards", "&cYou do not have enough shards."));
            return;
        }
        String keyType = plugin.getConfig().getString(path + ".key-type");
        String spawnerType = plugin.getConfig().getString(path + ".spawner-type");
        if (plugin.getConfig().getBoolean(path + ".sell-axe", false)) {
            giveOrDrop(player, plugin.sellAxe().item());
        } else if (keyType != null) {
            if (!plugin.crates().grant(player, keyType, plugin.getConfig().getInt(path + ".amount", 1))) {
                plugin.economy().addShards(player.getUniqueId(), shards);
                plugin.msg(player, Lang.text("menu.could-not-grant-these-keys-shards-refunded-check-inventory-space", "&cCould not grant these keys. Shards refunded; check inventory space and configuration."));
                return;
            }
        } else if (spawnerType != null) {
            giveOrDrop(player, plugin.spawners().spawnerItem(spawnerType, plugin.getConfig().getInt(path + ".amount", 1)));
        } else {
            giveOrDrop(player, com.donsup.compat.Materials.stack(plugin.getConfig().getString(path+".material"),plugin.getConfig().getInt(path+".amount",1)));
        }
        plugin.msg(player, Lang.text("menu.purchased-shard-shop-item", "&aPurchased shard shop item."));
        openShardShop(player);
    }

    public void openCrate(Player player, String type) {
        if (plugin.crates().accountMode() || plugin.crates().hasPending(player.getUniqueId())) {
            plugin.crates().open(player, type); return;
        }
        ConfigurationSection rewards = plugin.getConfig().getConfigurationSection("crates." + type + ".rewards");
        if (rewards == null || availableRewards(rewards).isEmpty()) {
            plugin.msg(player, Lang.text("menu.this-crate-has-no-rewards-configured", "&cThis crate has no rewards configured."));
            return;
        }
        if (!consumeKey(player, type)) {
            plugin.msg(player, Lang.text("menu.you-need-a-crate-key", "&cYou need a {0} crate key.", Lang.label("labels", type, type)));
            return;
        }
        openCrateSlider(player, type, rewards);
    }

    private void openCrateSlider(Player player, String type, ConfigurationSection rewards) {
        // Settle on the server before the cosmetic animation. Quitting must not lose the reward.
        String winningReward = roll(rewards);
        giveCrateReward(player, type, winningReward);
        Inventory inv = plugin.inventory(27, inventoryTitle("Opening " + type), false);
        ItemStack glass = plugin.button(com.donsup.compat.Materials.BLACK_STAINED_GLASS_PANE, " ", List.of(), actionKey, "BALANCE");
        for (int i = 0; i < inv.getSize(); i++) {
            inv.setItem(i, glass);
        }
        inv.setItem(4, plugin.button(Material.HOPPER, Lang.text("menu.rolling", "&e&lRolling..."), List.of(Lang.text("menu.your-reward-is-sliding-into-place", "&7Your reward is sliding into place.")), actionKey, "BALANCE"));
        inv.setItem(13, plugin.button(Material.NETHER_STAR, "&6???", List.of(Lang.text("menu.watch-the-center-slot", "&7Watch the center slot.")), actionKey, "BALANCE"));
        player.openInventory(inv);

        List<String> rewardKeys = availableRewards(rewards);
        if (rewardKeys.isEmpty()) {
            player.closeInventory();
            plugin.msg(player, Lang.text("menu.this-crate-has-no-rewards-configured", "&cThis crate has no rewards configured."));
            return;
        }
        int[] sliderSlots = {10, 11, 12, 13, 14, 15, 16};
        int ticks = Math.max(20, plugin.getConfig().getInt("crates." + type + ".animation-ticks", 60));
        final int[] counter = {0};
        plugin.platform().playerTimer(player, task -> {
            if (!player.isOnline()) {
                task.cancel();
                return;
            }
            if (!com.donsup.gui.OwnedInventory.title(player.getOpenInventory()).equals(inventoryTitle("Opening " + type))) {
                player.openInventory(inv);
            }
            counter[0]++;
            for (int i = 0; i < sliderSlots.length; i++) {
                String reward = rewardKeys.get(Math.floorMod(counter[0] + i, rewardKeys.size()));
                inv.setItem(sliderSlots[i], rewardIcon(type, reward));
            }
            inv.setItem(13, rewardIcon(type, counter[0] >= ticks - 8 ? winningReward : rewardKeys.get(counter[0] % rewardKeys.size())));
            if (counter[0] >= ticks) {
                task.cancel();
                inv.setItem(13, rewardIcon(type, winningReward));
                inv.setItem(22, plugin.button(com.donsup.compat.Materials.LIME_DYE, Lang.text("menu.reward-claimed", "&a&lReward Claimed"), List.of("&7" + winningReward), actionKey, "BALANCE"));
                plugin.msg(player, Lang.text("menu.opened-crate-and-received", "&aOpened crate and received &e{0}&a.", winningReward));
            }
        }, 1L, 2L);
    }

    private ItemStack rewardIcon(String type, String reward) {
        String path = "crates." + type + ".rewards." + reward;
        Material material = ItemUtil.material(plugin.getConfig().getString(path + ".material"), Material.GOLD_INGOT);
        if (plugin.getConfig().contains(path + ".shards")) {
            material = com.donsup.compat.Materials.AMETHYST_SHARD;
        } else if (plugin.getConfig().contains(path + ".money")) {
            material = Material.GOLD_INGOT;
        } else if (plugin.getConfig().contains(path + ".spawner-type")) {
            material = com.donsup.compat.Materials.SPAWNER;
        } else if (plugin.getConfig().contains(path + ".key-type")) {
            material = Material.TRIPWIRE_HOOK;
        }
        return plugin.button(material, Lang.text("menu.text-0c9112", "&e{0}", reward), List.of(Lang.text("menu.possible-crate-reward", "&7Possible crate reward.")), actionKey, "BALANCE");
    }

    private void giveCrateReward(Player player, String type, String reward) {
        String path = "crates." + type + ".rewards." + reward;
        double money = plugin.getConfig().getDouble(path + ".money", 0);
        int shards = plugin.getConfig().getInt(path + ".shards", 0);
        String keyType = plugin.getConfig().getString(path + ".key-type");
        String spawnerType = plugin.getConfig().getString(path + ".spawner-type");
        ItemStack material = com.donsup.compat.Materials.stack(plugin.getConfig().getString(path + ".material","DIAMOND"),1);
        int amount = plugin.getConfig().getInt(path + ".amount", 1);
        if (money > 0) {
            plugin.economy().deposit(player.getUniqueId(), money);
        }
        if (shards > 0) {
            plugin.economy().addShards(player.getUniqueId(), shards);
        }
        if (keyType != null) {
            giveOrDrop(player, keyItem(keyType, amount));
        } else if (spawnerType != null) {
            giveOrDrop(player, plugin.spawners().spawnerItem(spawnerType, amount));
        } else if (money <= 0 && shards <= 0) {
            if(material==null) throw new IllegalStateException("Crate reward became unavailable");
            material.setAmount(amount); giveOrDrop(player,material);
        }
    }

    private boolean consumeKey(Player player, String type) {
        ItemStack[] contents = com.donsup.compat.BukkitCompat.storage(player.getInventory());
        for (int i = 0; i < contents.length; i++) {
            ItemStack item = contents[i];
            if (item == null || !item.hasItemMeta()) {
                continue;
            }
            String stored = com.donsup.compat.ItemTags.getString(item.getItemMeta(), crateKey);
            if (type.equalsIgnoreCase(stored)) {
                item.setAmount(item.getAmount() - 1);
                contents[i] = item.getAmount() <= 0 ? null : item;
                com.donsup.compat.BukkitCompat.storage(player.getInventory(), contents);
                return true;
            }
        }
        return false;
    }

    private String roll(ConfigurationSection rewards) {
        List<String> keys=availableRewards(rewards);
        long total=keys.stream().mapToLong(key -> Math.max(1,Math.min(1_000_000,rewards.getInt(key+".weight",1)))).sum();
        long selected=com.donsup.util.RandomBounded.nextLong(random,total);
        long cursor=0;
        for (String key : keys) {
            cursor += Math.max(1,Math.min(1_000_000,rewards.getInt(key+".weight",1)));
            if (selected < cursor) {
                return key;
            }
        }
        throw new IllegalStateException("No available crate reward");
    }
    private boolean shardAvailable(ConfigurationSection offer) {
        return offer!=null && (offer.getBoolean("sell-axe") || offer.isString("key-type") || offer.isString("spawner-type")
                || com.donsup.compat.Materials.stack(offer.getString("material"),1)!=null);
    }
    private List<String> availableRewards(ConfigurationSection rewards) {
        List<String> keys=new ArrayList<>();
        for(String key:rewards.getKeys(false)) {
            ConfigurationSection reward=rewards.getConfigurationSection(key);
            if(reward!=null && (reward.getDouble("money")>0 || reward.getInt("shards")>0 || reward.isString("key-type") || reward.isString("spawner-type")
                    || com.donsup.compat.Materials.stack(reward.getString("material","DIAMOND"),1)!=null)) keys.add(key);
        }
        return keys;
    }

    private void teleportHome(Player player, String name) {
        var location = plugin.economy().home(player.getUniqueId(), name);
        if (location == null) {
            plugin.msg(player, Lang.text("menu.that-home-is-not-available", "&cThat home is not available."));
            return;
        }
        plugin.travel().teleport(player, location);
        plugin.msg(player, Lang.text("menu.teleported-to-home", "&aTeleported to home &e{0}&a.", name));
    }

    private void toggleAfk(Player player) {
        if (AfkSessions.ACTIVE.contains(player.getUniqueId())) {
            AfkSessions.ACTIVE.remove(player.getUniqueId());
            plugin.msg(player, Lang.text("menu.afk-rewards-disabled", "&cAFK rewards disabled."));
        } else {
            AfkSessions.ACTIVE.add(player.getUniqueId());
            plugin.msg(player, Lang.text("menu.afk-rewards-enabled-move-to-disable", "&aAFK rewards enabled. Move to disable."));
        }
        openMain(player);
    }

    private int removeItems(Player player, ItemStack template, int requested) {
        int remaining = requested;
        ItemStack[] contents = com.donsup.compat.BukkitCompat.storage(player.getInventory());
        for (int i = 0; i < contents.length && remaining > 0; i++) {
            ItemStack item = contents[i];
            if (item == null || !item.isSimilar(template) || item.hasItemMeta()) {
                continue;
            }
            int take = Math.min(remaining, item.getAmount());
            item.setAmount(item.getAmount() - take);
            remaining -= take;
            contents[i] = item.getAmount() <= 0 ? null : item;
        }
        com.donsup.compat.BukkitCompat.storage(player.getInventory(), contents);
        return requested - remaining;
    }

    private void giveOrDrop(Player player, ItemStack item) {
        Map<Integer, ItemStack> leftovers = player.getInventory().addItem(item);
        if (leftovers.isEmpty()) {
            return;
        }
        leftovers.values().forEach(leftover -> player.getWorld().dropItemNaturally(player.getLocation(), leftover));
        plugin.msg(player, Lang.text("menu.your-inventory-was-full-so-leftover-items-were-dropped-at-your-fe", "&eYour inventory was full, so leftover items were dropped at your feet."));
    }

    private Inventory inv(String name, int rows) {
        return plugin.inventory(rows * 9, inventoryTitle(name), false);
    }

    private String inventoryTitle(String name) {
        return titlePrefix() + name;
    }

    private String titlePrefix() {
        return "menu:";
    }

    private void fill(Inventory inv) {
        ItemStack glass = plugin.button(com.donsup.compat.Materials.GRAY_STAINED_GLASS_PANE, " ", List.of(), actionKey, "BALANCE");
        for (int i = 0; i < inv.getSize(); i++) {
            inv.setItem(i, glass);
        }
    }

    private ItemStack back() {
        return plugin.button(Material.ARROW, Lang.text("menu.back", "&7Back"), List.of(), actionKey, "OPEN:MAIN");
    }

    private void premium(Inventory inv, int slot, Material icon, String name, String detail) {
        inv.setItem(slot, plugin.button(icon, Lang.text("menu.text-539ee5", "&b{0}", name), List.of("&7" + detail, Lang.text("menu.included-in-premium", "&aIncluded in premium.")), actionKey, "BALANCE"));
    }

    private Material settingIcon(String key) {
        return switch (key) {
            case "public_chat" -> com.donsup.compat.Materials.OAK_SIGN;
            case "private_messages" -> com.donsup.compat.Materials.WRITABLE_BOOK;
            case "payments" -> Material.GOLD_INGOT;
            case "duel_requests" -> Material.DIAMOND_SWORD;
            case "bounty_alerts" -> com.donsup.compat.Materials.TARGET;
            case "market_alerts" -> com.donsup.compat.Materials.SPYGLASS;
            case "scoreboard" -> Material.MAP;
            case "night_vision" -> Material.POTION;
            case "coordinate_spoof" -> Material.COMPASS;
            case "mob_spawn_hints" -> com.donsup.compat.Materials.CREEPER_HEAD;
            default -> Material.LEVER;
        };
    }

    private String settingDescription(String key) {
        return switch (key) {
            case "public_chat" -> Lang.text("menu.allow-yourself-to-send-public-chat", "&7Allow yourself to send public chat.");
            case "private_messages" -> Lang.text("menu.allow-private-message-systems-to-target-you", "&7Allow private message systems to target you.");
            case "payments" -> Lang.text("menu.allow-other-players-to-pay-you-money", "&7Allow other players to pay you money.");
            case "duel_requests" -> Lang.text("menu.allow-future-duel-systems-to-invite-you", "&7Allow future duel systems to invite you.");
            case "bounty_alerts" -> Lang.text("menu.show-bounty-and-combat-economy-alerts", "&7Show bounty and combat economy alerts.");
            case "market_alerts" -> Lang.text("menu.show-premium-live-market-alerts", "&7Show premium live market alerts.");
            case "scoreboard" -> Lang.text("menu.reserve-state-for-scoreboard-visibility", "&7Reserve state for scoreboard visibility.");
            case "night_vision" -> Lang.text("menu.premium-infinite-night-vision", "&7Premium infinite night vision.");
            case "coordinate_spoof" -> Lang.text("menu.reserve-state-for-coordinate-hiding", "&7Reserve state for coordinate hiding.");
            case "mob_spawn_hints" -> Lang.text("menu.reserve-state-for-spawn-safety-hints", "&7Reserve state for spawn safety hints.");
            default -> Lang.text("menu.personal-setting", "&7Personal setting.");
        };
    }

    private String title(String key) {
        String lower = key.toLowerCase().replace('_', ' ');
        StringBuilder out = new StringBuilder();
        boolean cap = true;
        for (char c : lower.toCharArray()) {
            if (cap && Character.isLetter(c)) {
                out.append(Character.toUpperCase(c));
                cap = false;
            } else {
                out.append(c);
            }
            if (c == ' ') {
                cap = true;
            }
        }
        return Lang.label("labels", key, out.toString());
    }

    private String nice(Material material) {
        String lower = material.name().toLowerCase().replace('_', ' ');
        StringBuilder out = new StringBuilder();
        boolean cap = true;
        for (char c : lower.toCharArray()) {
            if (cap && Character.isLetter(c)) {
                out.append(Character.toUpperCase(c));
                cap = false;
            } else {
                out.append(c);
            }
            if (c == ' ') {
                cap = true;
            }
        }
        return Lang.label("materials", material.name(), out.toString());
    }
}


===== src/main/java/com/donsup/gui/OwnedInventory.java =====

package com.donsup.gui;

import org.bukkit.Bukkit;
import org.bukkit.event.*;
import org.bukkit.event.inventory.*;
import org.bukkit.inventory.*;

/** Identity-based inventory ownership; container names never authorize an action. */
public final class OwnedInventory implements InventoryHolder {
    private Inventory inventory;
    private final boolean storage;
    private final String canonicalTitle;
    private OwnedInventory(boolean storage, String canonicalTitle) { this.storage = storage; this.canonicalTitle = canonicalTitle; }
    public static Inventory menu(int size, String title) { return create(size, title, false); }
    public static Inventory storage(int size, String title) { return create(size, title, true); }
    private static Inventory create(int size, String title, boolean storage) {
        return create(size,title,title,storage);
    }
    public static Inventory create(int size,String canonicalTitle,String displayedTitle,boolean storage) {
        var holder = new OwnedInventory(storage,canonicalTitle);
        holder.inventory = Bukkit.createInventory(holder, size, com.donsup.compat.BukkitCompat.inventoryTitle(displayedTitle));
        return holder.inventory;
    }
    public static String title(InventoryView view) {
        return com.donsup.compat.Views.top(view).getHolder() instanceof OwnedInventory holder ? holder.canonicalTitle : "";
    }
    @Override public Inventory getInventory() { return inventory; }
    public static boolean buttonClick(InventoryClickEvent event) {
        if (!(com.donsup.compat.Views.top(event.getView()).getHolder() instanceof OwnedInventory holder)) return false;
        if (!holder.storage) event.setCancelled(true);
        return event.getRawSlot() >= 0 && event.getRawSlot() < com.donsup.compat.Views.top(event.getView()).getSize();
    }
    public static class Guard implements Listener {
        @EventHandler(priority = EventPriority.LOWEST) public void drag(InventoryDragEvent event) {
            if (com.donsup.compat.Views.top(event.getView()).getHolder() instanceof OwnedInventory holder && !holder.storage)
                event.setCancelled(true);
        }
    }
}


===== src/main/java/com/donsup/listener/AfkRewardListener.java =====

package com.donsup.listener;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.gui.AfkSessions;
import org.bukkit.Bukkit;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.AsyncPlayerChatEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerMoveEvent;
import org.bukkit.event.player.PlayerQuitEvent;

public class AfkRewardListener implements Listener {
    private final DonsupPlugin plugin;

    public AfkRewardListener(DonsupPlugin plugin) {
        this.plugin = plugin;
        plugin.platform().globalTimer(this::rewardOnlinePlayers, 20L * 60L, 20L * 60L);
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent event) {
        plugin.economy().ensure(event.getPlayer());
        plugin.menus().applyNightVision(event.getPlayer());
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        AfkSessions.ACTIVE.remove(event.getPlayer().getUniqueId());
    }

    @EventHandler
    public void onMove(PlayerMoveEvent event) {
        if (!AfkSessions.ACTIVE.contains(event.getPlayer().getUniqueId())) {
            return;
        }
        if ((event.getFrom().getBlockX() != event.getTo().getBlockX() || event.getFrom().getBlockY() != event.getTo().getBlockY() || event.getFrom().getBlockZ() != event.getTo().getBlockZ())) {
            AfkSessions.ACTIVE.remove(event.getPlayer().getUniqueId());
            plugin.msg(event.getPlayer(), Lang.text("afk-reward-listener.afk-rewards-disabled-because-you-moved", "&cAFK rewards disabled because you moved."));
        }
    }

    private void rewardOnlinePlayers() {
        int afk = plugin.getConfig().getInt("settings.afk-shards-per-minute", 1);
        int premium = plugin.getConfig().getInt("settings.premium-online-shards-per-minute", 1);
        plugin.platform().eachPlayer(player -> {
            int total = 0;
            plugin.economy().incrementStat(player.getUniqueId(), "online-reward-minutes", 1);
            int interval = Math.max(1, plugin.getConfig().getInt("settings.online-shards-interval-minutes", 10));
            if (plugin.economy().stat(player.getUniqueId(), "online-reward-minutes") % interval == 0)
                total += Math.max(0, plugin.getConfig().getInt("settings.online-shards", 1));
            if (AfkSessions.ACTIVE.contains(player.getUniqueId())) {
                total += afk;
            }
            if (plugin.economy().premium(player)) {
                total += premium;
                int interest = Math.min(
                        plugin.getConfig().getInt("settings.premium-shard-interest-cap", 250),
                        (int) Math.floor(plugin.economy().shards(player.getUniqueId()) * plugin.getConfig().getDouble("settings.premium-shard-interest", 0.02))
                );
                total += Math.max(0, interest);
            }
            if (total > 0) {
                plugin.economy().addShards(player.getUniqueId(), total);
            }
        });
    }
}


===== src/main/java/com/donsup/listener/BrandingListener.java =====

package com.donsup.listener;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.Text;
import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.scoreboard.DisplaySlot;
import org.bukkit.scoreboard.Objective;
import org.bukkit.scoreboard.Scoreboard;
import org.bukkit.scoreboard.ScoreboardManager;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.HashMap;
import org.bukkit.event.player.PlayerQuitEvent;

public class BrandingListener implements Listener {
    private final DonsupPlugin plugin;
    private final Map<UUID, Scoreboard> boards = new HashMap<>();
    private final Map<UUID, Scoreboard> previous = new HashMap<>();

    public BrandingListener(DonsupPlugin plugin) {
        this.plugin = plugin;
        plugin.platform().globalTimer(this::updateAll, 20L, 20L * 5L);
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent event) {
        updatePlayer(event.getPlayer());
    }

    private void updateAll() {
        for (Player player : Bukkit.getOnlinePlayers()) {
            plugin.platform().player(player, () -> updatePlayer(player));
        }
    }

    private void updatePlayer(Player player) {
        if (plugin.getConfig().getBoolean("branding.tablist.enabled", true)) {
            com.donsup.compat.BukkitCompat.tab(player, 
                    replace(player, plugin.getConfig().getString("branding.tablist.header", "&6&l%server%")),
                    replace(player, plugin.getConfig().getString("branding.tablist.footer", "&7/shop &8| &7/ah &8| &7/bounties"))
            );
        }
        if (plugin.platform().folia()) return; // Folia does not implement the Bukkit scoreboard API.
        if (plugin.getConfig().getBoolean("branding.scoreboard.enabled", true)
                && plugin.economy().setting(player.getUniqueId(), "scoreboard")) {
            updateScoreboard(player);
        } else if (player.getScoreboard().getObjective("smp_sidebar") != null) {
            player.setScoreboard(previous.getOrDefault(player.getUniqueId(), Bukkit.getScoreboardManager().getMainScoreboard()));
            boards.remove(player.getUniqueId()); previous.remove(player.getUniqueId());
        }
    }

    private void updateScoreboard(Player player) {
        ScoreboardManager manager = Bukkit.getScoreboardManager();
        if (manager == null) {
            return;
        }
        Scoreboard current = player.getScoreboard();
        if (current.getObjective(DisplaySlot.SIDEBAR) != null && current != boards.get(player.getUniqueId())) return;
        Scoreboard board = boards.computeIfAbsent(player.getUniqueId(), key -> {
            previous.put(key, current); return manager.getNewScoreboard();
        });
        Objective objective = board.getObjective("smp_sidebar");
        if (objective == null) objective = board.registerNewObjective("smp_sidebar", "dummy");
        objective.setDisplayName(com.donsup.compat.BukkitCompat.scoreTitle(replace(player, plugin.getConfig().getString("branding.scoreboard.title", "&6&l%server%"))));
        board.getEntries().forEach(board::resetScores);
        plugin.platform().blankScores(objective);
        objective.setDisplaySlot(DisplaySlot.SIDEBAR);
        List<String> lines = plugin.getConfig().getStringList("branding.scoreboard.lines");
        if (lines.isEmpty()) {
            lines = List.of(
                    Lang.text("branding-listener.money-money", "&7Money: &a%money%"),
                    Lang.text("branding-listener.shards-shards", "&7Shards: &d%shards%"),
                    Lang.text("branding-listener.kills-kills", "&7Kills: &c%kills%"),
                    Lang.text("branding-listener.bounty-bounty", "&7Bounty: &6%bounty%"),
                    Lang.text("branding-listener.smp", "&8/smp")
            );
        }
        lines = new java.util.ArrayList<>(lines);
        if (!plugin.economy().setting(player.getUniqueId(), "scoreboard_balance")) lines.removeIf(line -> line.contains("%money%") || line.contains("%shards%"));
        if (plugin.economy().setting(player.getUniqueId(), "scoreboard_coordinates")) {
            var loc = player.getLocation();
            lines.add(Lang.text("branding-listener.xyz", "&7XYZ: &f{0} {1} {2}", loc.getBlockX(), loc.getBlockY(), loc.getBlockZ()));
        }
        int score = Math.min(15, lines.size());
        int duplicate = 0;
        for (String raw : lines.stream().limit(15).toList()) {
            String line = com.donsup.compat.BukkitCompat.scoreLine(replace(player, raw));
            while (board.getEntries().contains(line)) {
                line = line + ChatColor.values()[duplicate++ % ChatColor.values().length];
            }
            objective.getScore(line).setScore(score--);
        }
        if (player.getScoreboard() != board) player.setScoreboard(board);
    }

    @EventHandler public void quit(PlayerQuitEvent event) { boards.remove(event.getPlayer().getUniqueId()); previous.remove(event.getPlayer().getUniqueId()); }

    private String replace(Player player, String input) {
        return Text.color(input
                .replace("%server%", plugin.serverName())
                .replace("%player%", player.getName())
                .replace("%money%", Text.money(plugin.economy().money(player.getUniqueId())))
                .replace("%shards%", String.valueOf(plugin.economy().shards(player.getUniqueId())))
                .replace("%kills%", String.valueOf(plugin.economy().stat(player.getUniqueId(), "kills")))
                .replace("%deaths%", String.valueOf(plugin.economy().stat(player.getUniqueId(), "deaths")))
                .replace("%bounty%", Text.money(plugin.economy().bounty(player.getUniqueId())))
                .replace("%online%", String.valueOf(Bukkit.getOnlinePlayers().size())));
    }
}


===== src/main/java/com/donsup/listener/CombatRewardListener.java =====

package com.donsup.listener;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.Text;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.PlayerDeathEvent;

public class CombatRewardListener implements Listener {
    private final DonsupPlugin plugin;

    public CombatRewardListener(DonsupPlugin plugin) {
        this.plugin = plugin;
    }

    @EventHandler
    public void onDeath(PlayerDeathEvent event) {
        Player victim = event.getEntity();
        plugin.economy().incrementStat(victim.getUniqueId(), "deaths", 1);
        Player killer = victim.getKiller();
        if (killer == null || killer.equals(victim)) {
            return;
        }
        plugin.economy().incrementStat(killer.getUniqueId(), "kills", 1);
        int shards = plugin.getConfig().getInt("settings.kill-shards", 10);
        if (shards > 0) {
            plugin.economy().addShards(killer.getUniqueId(), shards);
            plugin.msg(killer, Lang.text("combat-reward-listener.shards-for-defeating", "&d+{0} shards &7for defeating &e{1}&7.", shards, victim.getName()));
        }
        double bounty = plugin.economy().bounty(victim.getUniqueId());
        if (bounty > 0) {
            plugin.economy().deposit(killer.getUniqueId(), bounty);
            plugin.economy().clearBounty(victim.getUniqueId());
            plugin.msg(killer, Lang.text("combat-reward-listener.claimed-bounty-on-for", "&aClaimed bounty on &e{0}&a for {1}.", victim.getName(), Text.money(bounty)));
        }
        if (plugin.getConfig().getBoolean("settings.premium-bounty-radar", true)) {
            for (Player online : plugin.getServer().getOnlinePlayers()) {
                if (online.equals(killer) || online.equals(victim)) {
                    continue;
                }
                if (plugin.economy().premium(online) && plugin.economy().setting(online.getUniqueId(), "bounty_alerts")) {
                    plugin.msg(online, Lang.text("combat-reward-listener.bounty-radar-defeated", "&cBounty radar: &e{0} &7defeated &f{1}&7.", killer.getName(), victim.getName()));
                }
            }
        }
    }
}


===== src/main/java/com/donsup/market/BulkOrder.java =====

package com.donsup.market;

import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;

import java.util.UUID;

public record BulkOrder(
        String id,
        UUID owner,
        String ownerName,
        Material material,
        int requested,
        int delivered,
        double priceEach,
        long createdAt,
        long expiresAt,
        long claimUntil,
        ItemStack template
) {
    public BulkOrder {
        if (template != null) { template = template.clone(); template.setAmount(1); }
    }
    @Override public ItemStack template() { return template == null ? null : template.clone(); }
    public ItemStack item() { return template == null ? new ItemStack(material) : template.clone(); }
    public boolean exact() { return template != null; }
    public boolean matches(ItemStack candidate) {
        return candidate != null && candidate.getAmount() > 0 && candidate.getType() == material
            && (template == null ? !candidate.hasItemMeta() : template.isSimilar(candidate));
    }
    public int remaining() {
        return Math.max(0, requested - delivered);
    }
}


===== src/main/java/com/donsup/market/ListingSplit.java =====

package com.donsup.market;

/** Splits one asking price without charging the buyer for unsold items. */
public record ListingSplit(int purchased, int remaining, double paid, double remainingPrice) {
    public static ListingSplit of(int listed, double total, int wanted) {
        if (listed <= 0 || wanted <= 0 || !Double.isFinite(total) || total <= 0)
            throw new IllegalArgumentException("Invalid listing split");
        int take = Math.min(listed, wanted);
        double paid = take == listed ? total : total * ((double) take / listed);
        return new ListingSplit(take, listed - take, paid, total - paid);
    }
}


===== src/main/java/com/donsup/market/MarketListing.java =====

package com.donsup.market;

import org.bukkit.inventory.ItemStack;

import java.util.UUID;

public record MarketListing(
        String id,
        UUID owner,
        String ownerName,
        ItemStack item,
        double price,
        String type,
        long createdAt,
        long expiresAt
) {
}


===== src/main/java/com/donsup/market/MarketManager.java =====

package com.donsup.market;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import org.bukkit.Material;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

public class MarketManager {
    private final DonsupPlugin plugin;
    private final File file;
    private FileConfiguration data;

    public MarketManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.file = new File(plugin.getDataFolder(), "market.yml");
        reload();
    }

    public void reload() {
        this.data = com.donsup.util.SafeYaml.load(file);
    }

    public void save() {
        try {
            com.donsup.util.SafeYaml.save(data, file);
        } catch (IOException ex) {
            plugin.getLogger().warning("Could not save market.yml: " + ex.getMessage());
        }
    }

    public boolean listItem(Player seller, ItemStack item, double price, String type) {
        if (!Double.isFinite(price) || price <= 0 || price > 1.0e12 || item == null || item.getAmount() <= 0 || com.donsup.compat.BukkitCompat.air(item.getType())) return false;
        int max = plugin.economy().listingLimit(seller, type);
        long active = listings(type).stream().filter(listing -> listing.owner().equals(seller.getUniqueId())).count();
        if (active >= max) {
            return false;
        }
        double tax = price * (plugin.economy().listingTaxPercent(seller) / 100D);
        if (!plugin.economy().withdraw(seller.getUniqueId(), tax)) {
            return false;
        }
        item = item.clone();
        if (plugin.getConfig().getBoolean("market.match-orders", true)) {
            int initial = item.getAmount(), remaining = initial;
            double unitAsk = price / initial, earned = 0;
            for (BulkOrder order : orders().stream().sorted(Comparator.comparingDouble(BulkOrder::priceEach).reversed()
                    .thenComparingLong(BulkOrder::createdAt).thenComparing(BulkOrder::id)).toList()) {
                if (remaining == 0) break;
                if (order.owner().equals(seller.getUniqueId()) || !order.matches(item) || order.remaining() == 0
                        || order.expiresAt() <= System.currentTimeMillis() || order.priceEach() <= unitAsk) continue;
                int take = Math.min(remaining, order.remaining());
                addDelivered(order.id(), take);
                remaining -= take; earned += order.priceEach() * take;
            }
            if (earned > 0) {
                plugin.economy().deposit(seller.getUniqueId(), earned);
                plugin.msg(seller, Lang.text("market.matched-items-to-higher-paying-orders-for", "&aMatched {0} items to higher-paying orders for {1}.", (initial - remaining), com.donsup.util.Text.money(earned)));
            }
            if (remaining == 0) return true;
            price *= (double) remaining / initial;
            item.setAmount(remaining);
        }
        String id = UUID.randomUUID().toString();
        String path = "listings." + id;
        data.set(path + ".owner", seller.getUniqueId().toString());
        data.set(path + ".owner-name", seller.getName());
        data.set(path + ".price", price);
        data.set(path + ".type", type);
        data.set(path + ".created", System.currentTimeMillis());
        data.set(path + ".expires", System.currentTimeMillis() + 7L * 24L * 60L * 60L * 1000L);
        data.set(path + ".item", item);
        save();
        if (plugin.getConfig().getBoolean("settings.premium-market-alerts", true)) {
            for (Player online : plugin.getServer().getOnlinePlayers()) {
                if (!online.equals(seller)
                        && plugin.economy().premium(online)
                        && plugin.economy().setting(online.getUniqueId(), "market_alerts")) {
                    plugin.msg(online, Lang.text("market.market-alert-listed-x-for", "&dMarket alert: &e{0} &7listed &f{1}x {2} &7for &a{3}&7.", seller.getName(), item.getAmount(), Lang.material(item.getType()), com.donsup.util.Text.money(price)));
                }
            }
        }
        return true;
    }

    public List<MarketListing> listings(String type) {
        return listings(type, false);
    }

    public List<MarketListing> ownedListings(UUID owner, String type) {
        return listings(type, true).stream().filter(listing -> listing.owner().equals(owner)).toList();
    }

    private List<MarketListing> listings(String type, boolean includeExpired) {
        List<MarketListing> result = new ArrayList<>();
        ConfigurationSection section = data.getConfigurationSection("listings");
        if (section == null) {
            return result;
        }
        long now = System.currentTimeMillis();
        for (String id : section.getKeys(false)) {
            String path = "listings." + id;
            if (!type.equalsIgnoreCase(data.getString(path + ".type", "auction"))) {
                continue;
            }
            if (!includeExpired && data.getLong(path + ".expires", 0L) < now) {
                continue;
            }
            ItemStack item = data.getItemStack(path + ".item");
            if (item == null || com.donsup.compat.BukkitCompat.air(item.getType())) {
                continue;
            }
            try {
                result.add(new MarketListing(
                        id,
                        UUID.fromString(data.getString(path + ".owner")),
                        data.getString(path + ".owner-name", Lang.text("market.unknown", "Unknown")),
                        item,
                        data.getDouble(path + ".price"),
                        data.getString(path + ".type", "auction"),
                        data.getLong(path + ".created"),
                        data.getLong(path + ".expires")
                ));
            } catch (IllegalArgumentException ignored) {
            }
        }
        result.sort(Comparator.comparingLong(MarketListing::createdAt).reversed());
        return result;
    }

    public MarketListing listing(String id) {
        for (String type : List.of("auction", "market")) {
            for (MarketListing listing : listings(type)) {
                if (listing.id().equals(id)) {
                    return listing;
                }
            }
        }
        return null;
    }

    public void removeListing(String id) {
        data.set("listings." + id, null);
        save();
    }

    public boolean createOrder(Player owner, Material material, int amount, double priceEach) {
        return createOrder(owner, material, null, amount, priceEach);
    }

    public boolean createExactOrder(Player owner, ItemStack template, int amount, double priceEach) {
        if (template == null || template.getAmount() <= 0) return false;
        ItemStack copy = template.clone(); copy.setAmount(1);
        return createOrder(owner, copy.getType(), copy, amount, priceEach);
    }

    private boolean createOrder(Player owner, Material material, ItemStack template, int amount, double priceEach) {
        return plugin.recovery()==null?createOrderUncommitted(owner,material,template,amount,priceEach):plugin.recovery().run(owner,()->createOrderUncommitted(owner,material,template,amount,priceEach));
    }

    private boolean createOrderUncommitted(Player owner, Material material, ItemStack template, int amount, double priceEach) {
        double total = amount * priceEach;
        if (amount <= 0 || amount > 1000000 || !Double.isFinite(priceEach) || priceEach <= 0 || !Double.isFinite(total) || total > 1.0e12
                || material == null || material == Material.AIR || material == com.donsup.compat.Materials.CAVE_AIR || material == com.donsup.compat.Materials.VOID_AIR || !com.donsup.compat.BukkitCompat.item(material)
                || orders().stream().filter(o -> o.owner().equals(owner.getUniqueId())).count() >= 100
                || !plugin.economy().withdraw(owner.getUniqueId(), total)) {
            return false;
        }
        String id = UUID.randomUUID().toString();
        long now = System.currentTimeMillis();
        long duration = plugin.getConfig().getLong("settings.order-duration-hours", 24) * 60L * 60L * 1000L;
        long claim = plugin.getConfig().getLong("settings.order-claim-hours", 90) * 60L * 60L * 1000L;
        String path = "orders." + id;
        data.set(path + ".owner", owner.getUniqueId().toString());
        data.set(path + ".owner-name", owner.getName());
        data.set(path + ".material", material.name());
        data.set(path + ".template", template);
        data.set(path + ".requested", amount);
        data.set(path + ".delivered", 0);
        data.set(path + ".price-each", priceEach);
        data.set(path + ".created", now);
        data.set(path + ".expires", now + duration);
        data.set(path + ".claim-until", now + duration + claim);
        save();
        if (plugin.getConfig().getBoolean("market.match-orders", true)) {
            int remaining = amount;
            BulkOrder created = order(id);
            for (MarketListing listing : listings("auction").stream().sorted(Comparator.comparingDouble(l -> l.price() / l.item().getAmount())).toList()) {
                if (remaining == 0) break;
                int quantity = listing.item().getAmount();
                if (listing.owner().equals(owner.getUniqueId()) || !created.matches(listing.item())
                        || listing.price() > priceEach * quantity) continue;
                ListingSplit split = ListingSplit.of(quantity, listing.price(), remaining);
                consumeListing(listing, split);
                addDelivered(id, split.purchased());
                plugin.economy().deposit(listing.owner(), split.paid());
                plugin.economy().deposit(owner.getUniqueId(), Math.max(0, priceEach * split.purchased() - split.paid()));
                remaining -= split.purchased();
            }
        }
        return true;
    }

    private void consumeListing(MarketListing listing, ListingSplit split) {
        String oldPath = "listings." + listing.id();
        if (split.remaining() > 0) {
            // New ID invalidates every open confirmation for the previous quantity and price.
            String newPath = "listings." + UUID.randomUUID();
            data.createSection(newPath, data.getConfigurationSection(oldPath).getValues(false));
            ItemStack rest = listing.item().clone(); rest.setAmount(split.remaining());
            data.set(newPath + ".item", rest); data.set(newPath + ".price", split.remainingPrice());
        }
        data.set(oldPath, null);
        save();
    }

    public List<BulkOrder> orders() {
        List<BulkOrder> result = new ArrayList<>();
        ConfigurationSection section = data.getConfigurationSection("orders");
        if (section == null) {
            return result;
        }
        long now = System.currentTimeMillis();
        for (String id : section.getKeys(false)) {
            String path = "orders." + id;
            // Expiry stops deliveries; escrow and collected items remain claimable indefinitely.
            Material material;
            try {
                material = Material.valueOf(data.getString(path + ".material", "STONE"));
            } catch (IllegalArgumentException ex) {
                material = Material.STONE;
            }
            try {
                result.add(new BulkOrder(
                        id,
                        UUID.fromString(data.getString(path + ".owner")),
                        data.getString(path + ".owner-name", Lang.text("market.unknown", "Unknown")),
                        material,
                        data.getInt(path + ".requested"),
                        data.getInt(path + ".delivered"),
                        data.getDouble(path + ".price-each"),
                        data.getLong(path + ".created"),
                        data.getLong(path + ".expires"),
                        data.getLong(path + ".claim-until"),
                        data.getItemStack(path + ".template")
                ));
            } catch (IllegalArgumentException ignored) {
            }
        }
        result.sort(Comparator.comparingLong(BulkOrder::createdAt).reversed());
        return result;
    }

    public BulkOrder order(String id) {
        for (BulkOrder order : orders()) {
            if (order.id().equals(id)) {
                return order;
            }
        }
        return null;
    }

    public void addDelivered(String id, int amount) {
        BulkOrder order = order(id);
        if (order == null || amount <= 0 || amount > order.remaining()) throw new IllegalArgumentException("Invalid order delivery");
        String path = "orders." + id + ".delivered";
        data.set(path, data.getInt(path, 0) + amount);
        save();
    }

    public void removeOrder(String id) {
        data.set("orders." + id, null);
        save();
    }

    public void reclaim(Player player, String id) {
        if(plugin.recovery()==null){reclaimUncommitted(player,id);return;}
        plugin.recovery().run(player,()->reclaimUncommitted(player,id));
    }

    private void reclaimUncommitted(Player player, String id) {
        MarketListing listing = java.util.stream.Stream.of("auction", "market")
            .flatMap(type -> ownedListings(player.getUniqueId(), type).stream()).filter(l -> l.id().equals(id)).findFirst().orElse(null);
        if (listing == null) { plugin.msg(player, Lang.text("market.that-listing-is-no-longer-yours-or-was-already-claimed", "&cThat listing is no longer yours or was already claimed.")); return; }
        if (!com.donsup.util.InventoryCapacity.fits(player, listing.item(), listing.item().getAmount())) {
            plugin.msg(player, Lang.text("market.make-inventory-space-before-reclaiming", "&cMake inventory space before reclaiming.")); return;
        }
        removeListing(id); player.getInventory().addItem(listing.item().clone());
        plugin.msg(player, Lang.text("market.listing-returned", "&aListing returned."));
    }

    public void claim(Player player, String id) {
        if(plugin.recovery()==null){claimUncommitted(player,id);return;}
        plugin.recovery().run(player,()->claimUncommitted(player,id));
    }

    private void claimUncommitted(Player player, String id) {
        BulkOrder order = order(id);
        if (order == null || !order.owner().equals(player.getUniqueId())) { plugin.msg(player, Lang.text("market.that-is-not-your-order", "&cThat is not your order.")); return; }
        ItemStack template = order.item();
        int count = Math.min(order.delivered(), template.getMaxStackSize() * 36);
        while (count > 0 && !com.donsup.util.InventoryCapacity.fits(player, template, count)) count--;
        if (order.delivered() > 0 && count == 0) { plugin.msg(player, Lang.text("market.make-inventory-space-first", "&cMake inventory space first.")); return; }
        double refund = order.remaining() * order.priceEach();
        int left = order.delivered() - count;
        if (left == 0) data.set("orders." + id, null);
        else {
            data.set("orders." + id + ".requested", left);
            data.set("orders." + id + ".delivered", left);
            data.set("orders." + id + ".expires", 0L);
        }
        save();
        plugin.economy().deposit(player.getUniqueId(), refund);
        com.donsup.util.InventoryCapacity.give(player, template, count);
        plugin.msg(player, Lang.text("market.claimed-items-refund", "&aClaimed {0} items. Refund: {1}{2}", count, com.donsup.util.Text.money(refund), (left > 0 ? Lang.text("market.remaining-items", ". Remaining items: {0}", left) : "")));
    }

    public double serverPrice(Player player, ItemStack item) {
        if (item == null || item.hasItemMeta() || com.donsup.compat.BukkitCompat.air(item.getType())) return 0;
        double value = plugin.creator().dynamicPrice(item.getType(), com.donsup.compat.Materials.price(plugin.getConfig().getConfigurationSection("sell-prices"),item))
            * plugin.economy().effectiveSellMultiplier(player);
        return Double.isFinite(value) && value > 0 ? value : 0;
    }

    /** Consumes only plain items, trying live escrow-backed orders before the server price. */
    public double sell(Player player, ItemStack item) {
        if (item == null || item.hasItemMeta()) return 0;
        return sellMatching(player, item, false);
    }

    /** Explicit opt-in for custom items: only an identical, escrow-backed order can buy them. */
    public double sellExact(Player player, ItemStack item) { return sellMatching(player, item, true); }

    private double sellMatching(Player player, ItemStack item, boolean exactOnly) {
        if (item == null || item.getAmount() <= 0 || com.donsup.compat.BukkitCompat.air(item.getType())) return 0;
        double base = exactOnly ? 0 : serverPrice(player, item), earned = 0;
        int initial = item.getAmount(), remaining = initial;
        if (exactOnly || plugin.getConfig().getBoolean("market.match-orders", true)) {
            for (BulkOrder order : orders().stream().sorted(Comparator.comparingDouble(BulkOrder::priceEach).reversed()).toList()) {
                if (remaining == 0) break;
                if (order.owner().equals(player.getUniqueId()) || !order.matches(item) || order.remaining() <= 0
                    || order.expiresAt() <= System.currentTimeMillis() || order.priceEach() <= base) continue;
                int take = Math.min(remaining, order.remaining());
                addDelivered(order.id(), take); remaining -= take; earned += take * order.priceEach();
            }
        }
        if (base > 0) { earned += remaining * base; remaining = 0; }
        if (earned > 0) {
            plugin.economy().deposit(player.getUniqueId(), earned);
            plugin.extensions().recordSale(player, (initial - remaining) + "x " + item.getType().name() + " = " + com.donsup.util.Text.money(earned));
            plugin.creator().recordTrade(item.getType(), initial - remaining, false);
            item.setAmount(remaining);
        }
        return earned;
    }

    public int deliver(Player player, String id) {
        return plugin.recovery()==null?deliverUncommitted(player,id):plugin.recovery().run(player,()->deliverUncommitted(player,id));
    }

    private int deliverUncommitted(Player player, String id) {
        BulkOrder order = order(id);
        if (order == null || order.owner().equals(player.getUniqueId()) || order.remaining() == 0 || order.expiresAt() <= System.currentTimeMillis()) return 0;
        ItemStack[] contents = com.donsup.compat.BukkitCompat.storage(player.getInventory());
        int delivered = 0;
        for (int slot = 0; slot < contents.length && delivered < order.remaining(); slot++) {
            ItemStack item = contents[slot];
            if (!order.matches(item)) continue;
            int take = Math.min(item.getAmount(), order.remaining() - delivered);
            item.setAmount(item.getAmount() - take);
            if (item.getAmount() == 0) contents[slot] = null;
            delivered += take;
        }
        if (delivered > 0) {
            com.donsup.compat.BukkitCompat.storage(player.getInventory(), contents);
            addDelivered(id, delivered);
            plugin.economy().deposit(player.getUniqueId(), delivered * order.priceEach());
        }
        return delivered;
    }

    /** Sell plain contents only; preserve the original box, its metadata and all unsupported items. */
    public double sellShulkerContents(Player player) {
        return plugin.recovery()==null?sellShulkerContentsUncommitted(player):plugin.recovery().run(player,()->sellShulkerContentsUncommitted(player));
    }

    private double sellShulkerContentsUncommitted(Player player) {
        ItemStack held = com.donsup.compat.BukkitCompat.hand(player.getInventory()).clone();
        if (held.getAmount() != 1 || !(held.getItemMeta() instanceof org.bukkit.inventory.meta.BlockStateMeta meta)
                || !held.getType().name().endsWith("SHULKER_BOX") || !(meta.getBlockState() instanceof org.bukkit.inventory.InventoryHolder box)) {
            plugin.msg(player, Lang.text("market.hold-a-single-shulker-box-to-sell-its-contents", "&cHold a single shulker box to sell its contents.")); return 0;
        }
        ItemStack[] contents = com.donsup.compat.BukkitCompat.storage(box.getInventory());
        double earned = 0;
        for (ItemStack item : contents) earned += sell(player, item);
        com.donsup.compat.BukkitCompat.storage(box.getInventory(), contents);
        meta.setBlockState((org.bukkit.block.BlockState)box); held.setItemMeta(meta);
        com.donsup.compat.BukkitCompat.hand(player.getInventory(), held);
        plugin.msg(player, earned > 0 ? Lang.text("market.shulker-contents-sold-for-box-retained", "&aShulker contents sold for {0}. Box retained.", com.donsup.util.Text.money(earned))
            : Lang.text("market.no-supported-plain-contents-to-sell-custom-items-are-protected", "&7No supported plain contents to sell. Custom items are protected."));
        return earned;
    }
}


===== src/main/java/com/donsup/market/MarketRecovery.java =====

package com.donsup.market;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.*;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.inventory.ItemStack;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.function.Supplier;

/** A market mutation commits all YAML together and records inventory before/after for login recovery. */
public final class MarketRecovery implements Listener {
    private final DonsupPlugin plugin;
    private final Path root;
    private final Map<UUID,List<Path>> pending=new HashMap<>();
    public MarketRecovery(DonsupPlugin plugin) throws IOException {
        this.plugin=plugin;root=plugin.getDataFolder().toPath();
        for(Path journal:YamlBatch.journals(root)){
            YamlBatch.apply(root,journal);
            var data=SafeYaml.load(journal.toFile());
            pending.computeIfAbsent(UUID.fromString(data.getString("player")),id->new ArrayList<>()).add(journal);
        }
    }
    public static ItemStack[] copy(ItemStack[] items){return Arrays.stream(items).map(i->i==null?null:i.clone()).toArray(ItemStack[]::new);}
    /** Some modern APIs expose extra equipment in getContents beyond setContents' accepted size. */
    public static ItemStack[] snapshot(org.bukkit.inventory.PlayerInventory inventory){
        ItemStack[] items=new ItemStack[inventory.getSize()];
        for(int slot=0;slot<items.length;slot++){ItemStack item=inventory.getItem(slot);items[slot]=item==null?null:item.clone();}
        return items;
    }
    private static boolean same(ItemStack a,ItemStack b){if(a!=null&&(a.getAmount()==0||a.getType().name().endsWith("AIR")))a=null;if(b!=null&&(b.getAmount()==0||b.getType().name().endsWith("AIR")))b=null;return Objects.equals(a,b);}
    /** Merge only touched slots. Any conflicting slot holds the whole transaction for review. */
    public static ItemStack[] reconcile(ItemStack[] current,ItemStack[] before,ItemStack[] after){
        if(current.length!=before.length||before.length!=after.length)throw new IllegalStateException("Inventory layout changed (current="+current.length+", before="+before.length+", after="+after.length+")");
        ItemStack[] merged=copy(current);
        for(int i=0;i<current.length;i++)if(!same(before[i],after[i])){
            if(!same(current[i],before[i])&&!same(current[i],after[i]))throw new IllegalStateException("Inventory slot "+i+" conflicts with the saved transaction");
            merged[i]=after[i]==null?null:after[i].clone();
        }
        return merged;
    }
    public <T>T run(Player player,Supplier<T> action){
        if(YamlBatch.active())return action.get();
        if(plugin.recoveryFailed())throw new IllegalStateException("Economy is stopped for recovery");
        if(pending.containsKey(player.getUniqueId()))throw new IllegalStateException("Your previous transaction needs recovery before trading");
        ItemStack[] before=snapshot(player.getInventory());Path journal=null;
        YamlBatch.begin();
        try{
            T result=action.get();
            var writes=YamlBatch.end();ItemStack[] after=snapshot(player.getInventory());
            if(writes.isEmpty()&&Arrays.equals(before,after))return result;
            YamlConfiguration data=new YamlConfiguration();data.set("player",player.getUniqueId().toString());data.set("before",Arrays.asList(before));data.set("after",Arrays.asList(after));data.set("created",System.currentTimeMillis());
            journal=YamlBatch.prepare(root,writes,data);
            YamlBatch.apply(root,journal);
            player.saveData();
            Files.delete(journal);
            return result;
        }catch(Exception e){
            if(YamlBatch.active())YamlBatch.end();
            if(journal==null)player.getInventory().setContents(before);
            plugin.stopForRecovery(e);
            throw new IllegalStateException("Transaction interrupted. Data retained for recovery; trading has stopped.",e);
        }
    }
    public void run(Player player,Runnable action){run(player,()->{action.run();return null;});}
    public void recover(Player player){
        var journals=pending.get(player.getUniqueId());if(journals==null)return;
        try{
            for(Path journal:new ArrayList<>(journals)){
                var data=SafeYaml.load(journal.toFile());
                ItemStack[] before=items(data,"before"),after=items(data,"after");
                player.getInventory().setContents(reconcile(snapshot(player.getInventory()),before,after));player.saveData();
                Files.delete(journal);journals.remove(journal);
            }
            pending.remove(player.getUniqueId());plugin.msg(player,Lang.text("market-recovery.recovered-your-interrupted-market-transaction", "&aRecovered your interrupted market transaction."));
        }catch(Exception e){plugin.getLogger().severe("Market inventory recovery held for "+player.getUniqueId()+": "+e.getMessage());player.kickPlayer(Lang.text("market-recovery.your-inventory-has-a-transaction-awaiting-staff-recovery-please-c", "Your inventory has a transaction awaiting staff recovery. Please contact staff."));}
    }
    private static ItemStack[] items(YamlConfiguration data,String key){return data.getList(key,List.of()).stream().map(v->v==null?null:(ItemStack)v).toArray(ItemStack[]::new);}
    @EventHandler(priority=EventPriority.LOWEST)public void join(PlayerJoinEvent e){recover(e.getPlayer());}
    public void command(org.bukkit.command.CommandSender sender,String[] args){
        if(!sender.hasPermission("donsup.admin")){plugin.msg(sender,Lang.text("market-recovery.no-permission", "&cNo permission."));return;}
        if(args.length==4&&args[1].equalsIgnoreCase("resolve")&&args[3].equals("acknowledge")){
            try{
                UUID id=UUID.fromString(args[2]);var journals=pending.get(id);
                if(journals!=null){Path archive=root.resolve("transactions-reviewed");Files.createDirectories(archive);for(Path path:journals)Files.move(path,archive.resolve(path.getFileName()));pending.remove(id);}
                plugin.getLogger().warning(sender.getName()+" acknowledged inventory recovery for "+id+" after manual reconciliation.");plugin.msg(sender,Lang.text("market-recovery.recovery-hold-removed-journal-archived-no-items-replayed", "&aRecovery hold removed. Journal archived; no items replayed."));
            }catch(Exception e){plugin.msg(sender,Lang.text("market-recovery.could-not-acknowledge-recovery", "&cCould not acknowledge recovery: {0}", e.getMessage()));}
        }else{
            plugin.msg(sender,Lang.text("market-recovery.pending-inventory-recovery-player-s-review-transactions-yml-again", "&ePending inventory recovery: {0} player(s). Review transactions/*.yml against player inventories before resolving.", pending.size()));
            pending.forEach((id,paths)->plugin.msg(sender,Lang.text("market-recovery.record-s", "&7{0} — {1} record(s)", id, paths.size())));
            plugin.msg(sender,Lang.text("market-recovery.smp-recovery-resolve-acknowledge-only-after-reconciling-the-recor", "&e/smp recovery resolve <player UUID> acknowledge &7only after reconciling the recorded items."));
        }
    }
}


===== src/main/java/com/donsup/market/PriceTracker.java =====

package com.donsup.market;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.ItemUtil;
import com.donsup.util.Text;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class PriceTracker implements Listener {
    private static final String TITLE = "SMP | Prices";
    private final DonsupPlugin plugin;
    private final ItemKey actionKey;
    private final File file;
    private FileConfiguration data;

    public PriceTracker(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.actionKey = new ItemKey(plugin, "price_action");
        this.file = new File(plugin.getDataFolder(), "prices.yml");
        reload();
    }

    public void reload() { data = com.donsup.util.SafeYaml.load(file); }
    public void save() { try { com.donsup.util.SafeYaml.save(data, file); } catch (IOException ex) { plugin.getLogger().warning("Could not save prices.yml: " + ex.getMessage()); } }

    public void record(Material material, double price, int amount) {
        String key = material.name();
        int sales = data.getInt("items." + key + ".sales", 0) + 1;
        double total = data.getDouble("items." + key + ".total", 0) + price;
        data.set("items." + key + ".sales", sales);
        data.set("items." + key + ".total", total);
        data.set("items." + key + ".last", price);
        data.set("items." + key + ".last-amount", amount);
        save();
    }

    public void open(Player player) {
        Inventory inv = plugin.inventory(54, TITLE, false);
        ItemStack glass = plugin.button(com.donsup.compat.Materials.GRAY_STAINED_GLASS_PANE, " ", List.of(), actionKey, "NONE");
        for (int i = 0; i < inv.getSize(); i++) inv.setItem(i, glass);
        inv.setItem(4, plugin.button(Material.GOLD_INGOT, Lang.text("price-tracker.price-tracker", "&6&lPrice Tracker"), List.of(Lang.text("price-tracker.average-sale-prices-from-auctions-and-markets", "&7Average sale prices from auctions and markets.")), actionKey, "NONE"));
        ConfigurationSection items = data.getConfigurationSection("items");
        int slot = 10;
        if (items != null) for (String key : items.getKeys(false)) {
            if (slot >= 45) break;
            Material material = ItemUtil.material(key, Material.STONE);
            int sales = data.getInt("items." + key + ".sales", 0);
            double avg = sales <= 0 ? 0 : data.getDouble("items." + key + ".total", 0) / sales;
            inv.setItem(slot++, plugin.button(material, Lang.text("price-tracker.text", "&f{0}", Lang.materialName(key)), List.of(Lang.text("price-tracker.sales", "&7Sales: &e{0}", sales), Lang.text("price-tracker.average", "&7Average: &a{0}", Text.money(avg)), Lang.text("price-tracker.last", "&7Last: &a{0}", Text.money(data.getDouble("items." + key + ".last", 0)))), actionKey, "NONE"));
        }
        player.openInventory(inv);
    }

    @EventHandler public void onClick(InventoryClickEvent event) {
        if (!com.donsup.gui.OwnedInventory.buttonClick(event)) return;
        if (com.donsup.gui.OwnedInventory.title(event.getView()).equals(TITLE)) event.setCancelled(true);
    }
}


===== src/main/java/com/donsup/market/SellChest.java =====

package com.donsup.market;

import com.donsup.DonsupPlugin;
import com.donsup.compat.BukkitCompat;
import com.donsup.compat.Views;
import com.donsup.config.Lang;
import com.donsup.util.SafeYaml;
import com.donsup.util.Text;
import org.bukkit.Bukkit;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.entity.PlayerDeathEvent;
import org.bukkit.event.inventory.*;
import org.bukkit.event.player.*;
import org.bukkit.inventory.*;
import java.io.File;
import java.io.IOException;
import java.util.*;

/** The chest and cursor are views of durable custody, never a second copy of owned items.
 * Each transfer commits custody and the player's inventory through the market journal.
 * A crash returns custody on login; only a normal close sells deposited chest slots. */
public final class SellChest implements Listener {
    static final int SIZE = 54;
    private final DonsupPlugin plugin;
    private final File file;
    private final YamlConfiguration data;
    private final Map<UUID, Session> sessions = new HashMap<>();
    private boolean stopping;

    static final class Custody {
        final ItemStack[] items = new ItemStack[SIZE];
        ItemStack cursor;
        boolean empty() { return Arrays.stream(items).allMatch(SellChest::empty) && SellChest.empty(cursor); }
    }
    private static final class Session implements InventoryHolder {
        final UUID owner;
        final Custody custody;
        Inventory inventory;
        Session(UUID owner, Custody custody) { this.owner = owner; this.custody = custody; }
        public Inventory getInventory() { return inventory; }
    }
    public SellChest(DonsupPlugin plugin) {
        this.plugin = plugin;
        file = new File(plugin.getDataFolder(), "sell-custody.yml");
        data = SafeYaml.load(file);
    }
    static boolean empty(ItemStack item) { return item == null || item.getAmount() <= 0 || BukkitCompat.air(item.getType()); }
    static ItemStack copy(ItemStack item) { return empty(item) ? null : item.clone(); }
    private Custody load(UUID owner) {
        var state = new Custody();
        var yaml = data.getConfigurationSection("players." + owner);
        if (yaml == null) return state;
        List<?> items = yaml.getList("items", List.of());
        if (items.size() > SIZE) throw new IllegalStateException("Invalid sell custody for " + owner);
        for (int i = 0; i < items.size(); i++) {
            if (items.get(i) != null && !(items.get(i) instanceof ItemStack)) throw new IllegalStateException("Invalid sell custody item for " + owner);
            state.items[i] = copy((ItemStack) items.get(i));
        }
        state.cursor = copy(yaml.getItemStack("cursor"));
        return state;
    }
    private void save(UUID owner, Custody state) {
        String path = "players." + owner;
        data.set(path, null);
        if (!state.empty()) {
            data.set(path + ".items", Arrays.asList(state.items));
            data.set(path + ".cursor", state.cursor);
        }
        try { SafeYaml.save(data, file); }
        catch (IOException ex) { throw new IllegalStateException("Could not save sell custody", ex); }
    }
    public void open(Player player) {
        if (stopping || plugin.recoveryFailed()) return;
        // A region-threaded plugin shutdown cannot synchronously clear every player's cursor.
        // Keep the existing tools available until the custody lifecycle is qualified there.
        if (plugin.platform().folia()) {
            plugin.msg(player, Lang.text("sell-chest.folia-tools", "&eThe deposit chest is unavailable on Folia. Use these selling tools instead."));
            plugin.dialogs().sellOptions(player);
            return;
        }
        player.closeInventory();
        // Do not adopt a cursor owned by another container/plugin.
        if (!empty(player.getItemOnCursor())) {
            plugin.msg(player, Lang.text("sell-chest.empty-cursor", "&ePut the item on your cursor away, then open /sell again."));
            return;
        }
        claim(player);
        if (plugin.recoveryFailed()) return;
        Custody state = load(player.getUniqueId());
        // A full inventory may leave an interrupted cursor in custody. Return it before opening.
        if (!empty(state.cursor)) {
            plugin.msg(player, Lang.text("sell-chest.make-space", "&eMake room in your inventory, then use /sell claim to collect your saved items."));
            return;
        }
        var session = new Session(player.getUniqueId(), state);
        session.inventory = Bukkit.createInventory(session, SIZE, BukkitCompat.inventoryTitle(Text.color(Lang.text("sell-chest.title", "Sell - close to sell"))));
        sessions.put(session.owner, session);
        render(player, session);
        player.openInventory(session.inventory);
        // An external plugin may cancel the open.
        if (!Views.same(Views.top(player.getOpenInventory()), session.inventory)) sessions.remove(session.owner);
        else plugin.msg(player, Lang.text("sell-chest.instructions", "&ePlace items in this chest, then close it to sell. &7Unsellable and custom items are returned. /sell options opens more selling tools."));
    }
    private Session session(Player player, Inventory inventory) {
        Session session = sessions.get(player.getUniqueId());
        return session != null && session.owner.equals(player.getUniqueId()) && Views.same(session.inventory, inventory) ? session : null;
    }
    private void render(Player player, Session session) {
        session.inventory.setContents(MarketRecovery.copy(session.custody.items));
        player.setItemOnCursor(copy(session.custody.cursor));
        player.updateInventory();
    }
    private void mutate(Player player, Session session, Runnable action) {
        if (plugin.recoveryFailed() || stopping) return;
        try {
            plugin.recovery().run(player, () -> { action.run(); save(session.owner, session.custody); });
            render(player, session);
        } catch (RuntimeException ex) {
            // The persisted custody/journal is authoritative; never spill display copies.
            session.inventory.clear(); player.setItemOnCursor(null);
            throw ex;
        }
    }
    static int playerSlot(int raw) {
        int relative = raw - SIZE;
        return relative < 0 || relative >= 36 ? -1 : relative < 27 ? relative + 9 : relative - 27;
    }
    private ItemStack get(Player player, Session session, int raw) {
        return raw < SIZE ? session.custody.items[raw] : player.getInventory().getItem(playerSlot(raw));
    }
    private void set(Player player, Session session, int raw, ItemStack value) {
        if (raw < SIZE) session.custody.items[raw] = copy(value);
        else player.getInventory().setItem(playerSlot(raw), copy(value));
    }
    /** Move up to amount, merge first, then use empty slots. Returns the remainder. */
    static ItemStack insert(ItemStack[] into, ItemStack source, int amount) {
        if (empty(source)) return null;
        ItemStack rest = source.clone();
        int remaining = Math.min(amount, rest.getAmount()), moved = 0;
        for (int pass = 0; pass < 2 && remaining > 0; pass++) for (int i = 0; i < into.length && remaining > 0; i++) {
            ItemStack target = into[i];
            if (pass == 0 && (empty(target) || !target.isSimilar(rest))) continue;
            if (pass == 1 && !empty(target)) continue;
            int room = empty(target) ? rest.getMaxStackSize() : target.getMaxStackSize() - target.getAmount();
            int take = Math.min(remaining, Math.max(0, room));
            if (take == 0) continue;
            ItemStack next = empty(target) ? rest.clone() : target.clone();
            next.setAmount((empty(target) ? 0 : target.getAmount()) + take);
            into[i] = next; remaining -= take; moved += take;
        }
        rest.setAmount(rest.getAmount() - moved);
        return copy(rest);
    }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true)
    public void click(InventoryClickEvent event) {
        if (!(event.getWhoClicked() instanceof Player player)) return;
        Session session = session(player, Views.top(event.getView()));
        if (session == null) return;
        event.setCancelled(true);
        int raw = event.getRawSlot();
        if (raw < 0 || raw >= SIZE + 36 || event instanceof InventoryCreativeEvent) { render(player, session); return; }
        if (!Objects.equals(copy(event.getCursor()), copy(session.custody.cursor))) { render(player, session); return; }
        // Dropping display copies and creative cloning are deliberately unavailable here.
        if (event.getAction().name().contains("DROP") || event.getAction() == InventoryAction.CLONE_STACK) { render(player, session); return; }
        mutate(player, session, () -> applyClick(player, session, raw, event));
    }
    private void applyClick(Player player, Session session, int raw, InventoryClickEvent event) {
        ItemStack slot = copy(get(player, session, raw)), cursor = copy(session.custody.cursor);
        switch (event.getAction()) {
            case MOVE_TO_OTHER_INVENTORY -> {
                if (raw < SIZE) {
                    ItemStack[] storage = BukkitCompat.storage(player.getInventory());
                    session.custody.items[raw] = insert(storage, slot, empty(slot) ? 0 : slot.getAmount());
                    BukkitCompat.storage(player.getInventory(), storage);
                } else set(player, session, raw, insert(session.custody.items, slot, empty(slot) ? 0 : slot.getAmount()));
            }
            case PICKUP_ALL, PICKUP_HALF, PICKUP_ONE, PICKUP_SOME -> {
                if (empty(slot) || !empty(cursor) && !cursor.isSimilar(slot)) return;
                int amount = event.getAction() == InventoryAction.PICKUP_HALF ? (slot.getAmount() + 1) / 2
                    : event.getAction() == InventoryAction.PICKUP_ONE ? 1 : slot.getAmount();
                int take = Math.min(amount, slot.getMaxStackSize() - (empty(cursor) ? 0 : cursor.getAmount()));
                ItemStack next = empty(cursor) ? slot.clone() : cursor;
                next.setAmount((empty(cursor) ? 0 : cursor.getAmount()) + take);
                slot.setAmount(slot.getAmount() - take);
                set(player, session, raw, slot); session.custody.cursor = copy(next);
            }
            case PLACE_ALL, PLACE_ONE, PLACE_SOME -> {
                if (empty(cursor) || !empty(slot) && !slot.isSimilar(cursor)) return;
                int amount = event.getAction() == InventoryAction.PLACE_ONE ? 1 : cursor.getAmount();
                int take = Math.min(amount, cursor.getMaxStackSize() - (empty(slot) ? 0 : slot.getAmount()));
                ItemStack next = empty(slot) ? cursor.clone() : slot;
                next.setAmount((empty(slot) ? 0 : slot.getAmount()) + take);
                cursor.setAmount(cursor.getAmount() - take);
                set(player, session, raw, next); session.custody.cursor = copy(cursor);
            }
            case SWAP_WITH_CURSOR -> { set(player, session, raw, cursor); session.custody.cursor = slot; }
            case HOTBAR_SWAP, HOTBAR_MOVE_AND_READD -> {
                int hotbar = event.getHotbarButton();
                if (hotbar < 0 || hotbar > 8) return;
                ItemStack held = copy(player.getInventory().getItem(hotbar));
                set(player, session, raw, held); player.getInventory().setItem(hotbar, slot);
            }
            case COLLECT_TO_CURSOR -> {
                if (empty(cursor)) return;
                for (int i = 0; i < SIZE + 36 && cursor.getAmount() < cursor.getMaxStackSize(); i++) {
                    ItemStack item = copy(get(player, session, i));
                    if (empty(item) || !item.isSimilar(cursor)) continue;
                    int take = Math.min(item.getAmount(), cursor.getMaxStackSize() - cursor.getAmount());
                    cursor.setAmount(cursor.getAmount() + take); item.setAmount(item.getAmount() - take);
                    set(player, session, i, item);
                }
                session.custody.cursor = cursor;
            }
            default -> { }
        }
    }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true)
    public void drag(InventoryDragEvent event) {
        if (!(event.getWhoClicked() instanceof Player player)) return;
        Session session = session(player, Views.top(event.getView()));
        if (session == null) return;
        event.setCancelled(true);
        if (event.getRawSlots().stream().anyMatch(slot -> slot < 0 || slot >= SIZE + 36)
            || !Objects.equals(copy(event.getOldCursor()), copy(session.custody.cursor))) { render(player, session); return; }
        mutate(player, session, () -> {
            event.getNewItems().forEach((raw, item) -> set(player, session, raw, item));
            session.custody.cursor = copy(event.getCursor());
        });
        // Bukkit restores the old cursor after a cancelled drag event. Repaint our committed view.
        plugin.platform().player(player, () -> {
            if (sessions.get(session.owner) == session) render(player, session);
        });
    }
    private static boolean normalClose(InventoryCloseEvent event) {
        // Legacy Bukkit has no close reason. Modern reasons distinguish disconnect/death/plugin opens.
        if (!BukkitCompat.method(event.getClass(), "getReason")) return true;
        Object reason = BukkitCompat.call(event, "getReason");
        return reason != null && (reason.toString().equals("PLAYER") || reason.toString().equals("UNKNOWN"));
    }
    @EventHandler(priority = EventPriority.LOWEST)
    public void close(InventoryCloseEvent event) {
        if (!(event.getPlayer() instanceof Player player)) return;
        Session session = session(player, event.getInventory());
        if (session == null) return;
        sessions.remove(session.owner);
        session.inventory.clear(); player.setItemOnCursor(null);
        if (plugin.recoveryFailed()) return;
        if (stopping || !player.isOnline() || player.isDead() || !normalClose(event)) return; // Claim on login or /sell claim.
        Custody state = session.custody;
        double earned = plugin.recovery().run(player, () -> {
            double total = 0;
            for (ItemStack item : state.items) total += plugin.market().sell(player, item);
            returnItems(player, state); save(session.owner, state);
            return total;
        });
        if (earned > 0) plugin.msg(player, Lang.text("sell-chest.sold", "&aSold deposited items for {0}.", Text.money(earned)));
        else plugin.msg(player, Lang.text("sell-chest.nothing-sold", "&7No deposited items were sellable. Your items have been returned or saved for collection."));
        if (!state.empty()) plugin.msg(player, Lang.text("sell-chest.make-space", "&eMake room in your inventory, then use /sell claim to collect your saved items."));
    }
    static void returnItems(Player player, Custody state) {
        ItemStack[] storage = BukkitCompat.storage(player.getInventory());
        for (int i = 0; i < SIZE; i++) state.items[i] = insert(storage, state.items[i], empty(state.items[i]) ? 0 : state.items[i].getAmount());
        state.cursor = insert(storage, state.cursor, empty(state.cursor) ? 0 : state.cursor.getAmount());
        BukkitCompat.storage(player.getInventory(), storage);
    }
    public void claim(Player player) {
        if (plugin.recoveryFailed() || sessions.containsKey(player.getUniqueId())) return;
        Custody state = load(player.getUniqueId());
        if (state.empty()) return;
        plugin.recovery().run(player, () -> { returnItems(player, state); save(player.getUniqueId(), state); });
        plugin.msg(player, state.empty() ? Lang.text("sell-chest.returned", "&aCollected your saved sell-menu items.")
            : Lang.text("sell-chest.make-space", "&eMake room in your inventory, then use /sell claim to collect your saved items."));
    }
    private void suspend(Player player) {
        Session session = sessions.remove(player.getUniqueId());
        if (session != null) { session.inventory.clear(); player.setItemOnCursor(null); }
    }
    @EventHandler(priority = EventPriority.LOWEST) public void quit(PlayerQuitEvent event) { suspend(event.getPlayer()); }
    @EventHandler(priority = EventPriority.LOWEST) public void death(PlayerDeathEvent event) { suspend(event.getEntity()); }
    @EventHandler(priority = EventPriority.MONITOR) public void join(PlayerJoinEvent event) {
        plugin.platform().player(event.getPlayer(), () -> { if (event.getPlayer().isOnline()) claim(event.getPlayer()); });
    }
    @EventHandler(priority = EventPriority.MONITOR) public void respawn(PlayerRespawnEvent event) {
        plugin.platform().player(event.getPlayer(), () -> claim(event.getPlayer()));
    }
    public void shutdown() {
        stopping = true;
        for (Player player : Bukkit.getOnlinePlayers()) if (!plugin.platform().folia()) {
            if (sessions.containsKey(player.getUniqueId())) { suspend(player); player.closeInventory(); }
        }
        // Custody is already durable, including on region-threaded shutdown.
    }
}


===== src/main/java/com/donsup/market/ShoppingLists.java =====

package com.donsup.market;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.compat.BukkitCompat;
import com.donsup.gui.OwnedInventory;
import com.donsup.util.Text;
import org.bukkit.*;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.inventory.*;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.*;
import java.io.File;
import java.util.*;

public final class ShoppingLists implements Listener {
    private record Screen(Inventory inventory,Map<Integer,Runnable> actions) {}
    private final DonsupPlugin plugin;
    private final ShoppingStore store;
    private final Map<UUID,Screen> screens=new HashMap<>();
    public ShoppingLists(DonsupPlugin plugin) { this.plugin=plugin;store=new ShoppingStore(new File(plugin.getDataFolder(),"shopping-lists.yml")); }
    public void command(Player p,String[] args) {
        if(!p.hasPermission("donsup.use"))return;
        try {
            if(args.length==0){plugin.dialogs().quickBuy(p,0,null);return;}
            switch(args[0].toLowerCase(Locale.ROOT)) {
                case "saved","favourites","favorites","loadouts" -> open(p,null);
                case "save","loadout" -> {
                    if(args.length!=2)throw new IllegalArgumentException(Lang.text("shopping-lists.quickbuy-save-for-the-held-item-quickbuy-loadout-for-your-hotbar", "/quickbuy save <name> for the held item; /quickbuy loadout <name> for your hotbar."));
                    List<ItemStack> items=new ArrayList<>();
                    if(args[0].equalsIgnoreCase("save")) { var held=BukkitCompat.hand(p.getInventory());if(held!=null&&!BukkitCompat.air(held.getType()))items.add(held.clone()); }
                    else for(int i=0;i<9;i++){var item=p.getInventory().getItem(i);if(item!=null&&!BukkitCompat.air(item.getType()))items.add(item.clone());}
                    store.save(p.getUniqueId(),args[1],items,plugin.getConfig().getInt("quick-buy.max-saved-lists",24));
                    plugin.msg(p,Lang.text("shopping-lists.saved-shopping-selection-your-items-were-kept", "&aSaved shopping selection '{0}'. Your items were kept.", ShoppingStore.name(args[1])));open(p,null);
                }
                case "open" -> {if(args.length!=2)throw new IllegalArgumentException(Lang.text("shopping-lists.quickbuy-open", "/quickbuy open <name>"));open(p,ShoppingStore.name(args[1]));}
                case "delete" -> {if(args.length!=2)throw new IllegalArgumentException(Lang.text("shopping-lists.quickbuy-delete", "/quickbuy delete <name>"));store.remove(p.getUniqueId(),args[1]);open(p,null);}
                default -> plugin.msg(p,Lang.text("shopping-lists.quickbuy-saved-save-loadout-open-delete", "&e/quickbuy saved | save <name> | loadout <name> | open <name> | delete <name>"));
            }
        } catch(Exception e){plugin.msg(p,Lang.text("shopping-lists.text", "&c{0}", e.getMessage()));}
    }
    private void button(Screen s,int slot,ItemStack icon,String title,String lore,Runnable action) {
        var item=icon.clone();item.setAmount(Math.min(item.getAmount(),item.getMaxStackSize()));var meta=item.getItemMeta();
        if(title!=null)meta.setDisplayName(Text.color(Lang.text("shopping-lists.text-539ee5", "&b{0}", title)));
        var lines=meta.hasLore()?new ArrayList<>(meta.getLore()):new ArrayList<String>();lines.add(Text.color("&7"+lore));meta.setLore(lines);item.setItemMeta(meta);
        s.inventory().setItem(slot,item);s.actions().put(slot,action);
    }
    public void open(Player p,String selected) {
        if(!p.hasPermission("donsup.use"))return;
        Screen s=new Screen(plugin.inventory(54,selected==null?"Saved Shopping":"Shopping: "+selected,false),new HashMap<>());
        int slot=0;
        if(selected==null) for(String name:store.names(p.getUniqueId())) {
            var items=store.items(p.getUniqueId(),name);if(items.isEmpty())continue;
            button(s,slot++,items.getFirst(),name,Lang.text("shopping-lists.saved-item-s-click-to-browse", "{0} saved item(s) — click to browse", items.size()),()->open(p,name));
        } else for(ItemStack item:store.items(p.getUniqueId(),selected)) {
            button(s,slot++,item,null,Lang.text("shopping-lists.wanted-browse-current-exact-matches-confirm-price-before-buying", "Wanted: {0}. Browse current exact matches; confirm price before buying.", item.getAmount()),()->plugin.dialogs().quickBuy(p,0,item.clone()));
        }
        button(s,45,new ItemStack(Material.PAPER),Lang.text("shopping-lists.save-held-item", "Save held item"),Lang.text("shopping-lists.use-quickbuy-save", "Use /quickbuy save <name>"),()->plugin.msg(p,Lang.text("shopping-lists.quickbuy-save", "&e/quickbuy save <name>")));
        button(s,46,new ItemStack(Material.CHEST),Lang.text("shopping-lists.save-hotbar-loadout", "Save hotbar loadout"),Lang.text("shopping-lists.use-quickbuy-loadout", "Use /quickbuy loadout <name>"),()->plugin.msg(p,Lang.text("shopping-lists.quickbuy-loadout", "&e/quickbuy loadout <name>")));
        button(s,49,new ItemStack(Material.ARROW),Lang.text("shopping-lists.back", "Back"),Lang.text("shopping-lists.saved-selections-live-market", "Saved selections / live market"),()->{if(selected==null)plugin.dialogs().quickBuy(p,0,null);else open(p,null);});
        if(selected!=null)button(s,53,new ItemStack(Material.BARRIER),Lang.text("shopping-lists.delete-selection", "Delete selection"),Lang.text("shopping-lists.your-actual-items-are-unaffected", "Your actual items are unaffected"),()->plugin.dialogs().confirm(p,Lang.text("shopping-lists.delete", "Delete {0}", selected),Lang.text("shopping-lists.delete-this-saved-shopping-selection", "Delete this saved shopping selection?"),()->command(p,new String[]{"delete",selected}),()->open(p,selected)));
        p.openInventory(s.inventory());screens.put(p.getUniqueId(),s);
    }
    @EventHandler(priority=EventPriority.HIGHEST) public void click(InventoryClickEvent e) {
        if(!(e.getWhoClicked() instanceof Player p))return;Screen s=screens.get(p.getUniqueId());
        if(s==null||com.donsup.compat.Views.top(e.getView())!=s.inventory())return;
        e.setCancelled(true);Runnable action=s.actions().get(e.getRawSlot());
        if(action!=null&&p.hasPermission("donsup.use")){screens.remove(p.getUniqueId());plugin.platform().player(p,()->{if(p.isOnline())action.run();});}
    }
    @EventHandler public void drag(InventoryDragEvent e){Screen s=screens.get(e.getWhoClicked().getUniqueId());if(s!=null&&com.donsup.compat.Views.top(e.getView())==s.inventory())e.setCancelled(true);}
    @EventHandler public void close(InventoryCloseEvent e){Screen s=screens.get(e.getPlayer().getUniqueId());if(s!=null&&s.inventory()==e.getInventory())screens.remove(e.getPlayer().getUniqueId());}
    @EventHandler public void quit(PlayerQuitEvent e){screens.remove(e.getPlayer().getUniqueId());}
}


===== src/main/java/com/donsup/market/ShoppingStore.java =====

package com.donsup.market;

import com.donsup.config.Lang;

import com.donsup.util.SafeYaml;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.inventory.ItemStack;
import java.io.*;
import java.util.*;

/** Saved exact item templates, never cached market prices or purchase authority. */
public final class ShoppingStore {
    private final File file;
    private YamlConfiguration data;
    public ShoppingStore(File file) { this.file=file; data=SafeYaml.load(file); }
    public static String name(String value) {
        if(value==null || !value.matches("[a-zA-Z0-9_-]{1,24}")) throw new IllegalArgumentException(Lang.text("shopping-store.use-1-24-letters-numbers-underscores-or-hyphens-for-the-name", "Use 1–24 letters, numbers, underscores or hyphens for the name."));
        return value.toLowerCase(Locale.ROOT);
    }
    private String path(UUID player,String name) { return "players."+player+"."+name(name); }
    public List<String> names(UUID player) {
        var section=data.getConfigurationSection("players."+player);
        return section==null?List.of():section.getKeys(false).stream().sorted().toList();
    }
    public List<ItemStack> items(UUID player,String name) {
        List<ItemStack> out=new ArrayList<>();
        for(Object item:data.getList(path(player,name)+".items",List.of())) if(item instanceof ItemStack stack) out.add(stack.clone());
        return out;
    }
    public void save(UUID player,String name,List<ItemStack> items,int limit) throws IOException {
        String p=path(player,name);
        if(!data.contains(p) && names(player).size()>=Math.max(1,Math.min(36,limit))) throw new IllegalArgumentException(Lang.text("shopping-store.your-saved-shopping-list-is-full-delete-an-entry-first", "Your saved shopping list is full. Delete an entry first."));
        if(items.isEmpty() || items.size()>9 || items.stream().anyMatch(i->i==null || i.getAmount()<1 || i.getType().name().endsWith("AIR"))) throw new IllegalArgumentException(Lang.text("shopping-store.hold-an-item-or-put-items-in-your-hotbar-for-a-loadout", "Hold an item, or put items in your hotbar for a loadout."));
        YamlConfiguration next=copy();
        next.set(p+".items",items.stream().map(ItemStack::clone).toList());
        SafeYaml.save(next,file);data=next;
    }
    public void remove(UUID player,String name) throws IOException {
        YamlConfiguration next=copy();next.set(path(player,name),null);SafeYaml.save(next,file);data=next;
    }
    private YamlConfiguration copy() throws IOException {
        var next=new YamlConfiguration();try{next.loadFromString(data.saveToString());}catch(Exception e){throw new IOException(e);}return next;
    }
}


===== src/main/java/com/donsup/moderation/ModerationManager.java =====

package com.donsup.moderation;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.ItemUtil;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.OfflinePlayer;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.AsyncPlayerChatEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerMoveEvent;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.UUID;

public class ModerationManager implements Listener {
    private static final String TITLE = "SMP | Staff";
    private final DonsupPlugin plugin;
    private final ItemKey actionKey;
    private final File file;
    private FileConfiguration data;
    private final java.util.Map<UUID, Long> mutes = new java.util.concurrent.ConcurrentHashMap<>();

    public ModerationManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.actionKey = new ItemKey(plugin, "mod_action");
        this.file = new File(plugin.getDataFolder(), "moderation.yml");
        reload();
    }

    public void reload() {
        data = com.donsup.util.SafeYaml.load(file); mutes.clear();
        var players = data.getConfigurationSection("players");
        if (players != null) for (String id : players.getKeys(false)) {
            try { mutes.put(UUID.fromString(id), players.getLong(id + ".muted-until")); } catch (IllegalArgumentException ignored) { }
        }
    }
    public void save() { try { com.donsup.util.SafeYaml.save(data, file); } catch (IOException ex) { plugin.getLogger().warning("Could not save moderation.yml: " + ex.getMessage()); } }

    public void command(Player player, String[] args) {
        if (!player.hasPermission("donsup.staff")) { plugin.msg(player, Lang.text("moderation.no-permission", "&cNo permission.")); return; }
        if (args.length == 0) { open(player); return; }
        switch (args[0].toLowerCase()) {
            case "mute" -> mute(player, args);
            case "warn" -> warn(player, args);
            case "freeze" -> toggle(player, args, "frozen");
            case "vanish" -> vanish(player);
            case "note" -> note(player, args);
            case "chat" -> staffChat(player, join(args, 1));
            default -> open(player);
        }
    }

    public void report(Player player, String[] args) {
        if (args.length < 2) { plugin.msg(player, Lang.text("moderation.usage-report", "&eUsage: /report <player> <reason>")); return; }
        String id = String.valueOf(System.currentTimeMillis());
        data.set("reports." + id + ".reporter", player.getName());
        data.set("reports." + id + ".target", args[0]);
        data.set("reports." + id + ".reason", join(args, 1));
        save();
        plugin.msg(player, Lang.text("moderation.report-submitted", "&aReport submitted."));
        staffBroadcast(Lang.text("moderation.report-reported", "&c[Report] &e{0} &7reported &e{1}&7: &f{2}", player.getName(), args[0], join(args, 1)));
    }

    public void open(Player player) {
        Inventory inv = plugin.inventory(27, TITLE, false);
        ItemStack glass = button(com.donsup.compat.Materials.GRAY_STAINED_GLASS_PANE, " ", List.of(), "NONE");
        for (int i = 0; i < inv.getSize(); i++) inv.setItem(i, glass);
        inv.setItem(4, button(com.donsup.compat.Materials.COMMAND_BLOCK, Lang.text("moderation.staff-tools", "&c&lStaff Tools"), List.of(Lang.text("moderation.mod-mute-warn-freeze-vanish", "&7/mod mute, warn, freeze, vanish"), Lang.text("moderation.report-for-player-reports", "&7/report for player reports")), "NONE"));
        inv.setItem(11, button(Material.PAPER, Lang.text("moderation.reports", "&eReports"), List.of(Lang.text("moderation.open-moderation-yml-for-full-report-list", "&7Open moderation.yml for full report list."), Lang.text("moderation.reports-afb3a2", "&7Reports: &e{0}", (data.getConfigurationSection("reports") == null ? 0 : data.getConfigurationSection("reports").getKeys(false).size()))), "NONE"));
        inv.setItem(13, button(Material.ICE, Lang.text("moderation.freeze", "&bFreeze"), List.of(Lang.text("moderation.use-mod-freeze", "&7Use &f/mod freeze <player>&7.")), "NONE"));
        inv.setItem(15, button(Material.GLASS, Lang.text("moderation.vanish", "&fVanish"), List.of(Lang.text("moderation.use-mod-vanish", "&7Use &f/mod vanish&7.")), "NONE"));
        player.openInventory(inv);
    }

    private void mute(Player sender, String[] args) {
        if (args.length < 3) { plugin.msg(sender, Lang.text("moderation.usage-mod-mute", "&eUsage: /mod mute <player> <minutes>")); return; }
        OfflinePlayer target = Bukkit.getOfflinePlayer(args[1]);
        long minutes = parse(args[2]);
        if (minutes < 1 || minutes > 5256000) { plugin.msg(sender, Lang.text("moderation.use-a-mute-length-of-1-5256000-minutes", "&cUse a mute length of 1-5256000 minutes.")); return; }
        long until = System.currentTimeMillis() + minutes * 60000L;
        data.set("players." + target.getUniqueId() + ".muted-until", until);
        mutes.put(target.getUniqueId(), until);
        save();
        plugin.msg(sender, Lang.text("moderation.muted", "&aMuted &e{0}&a.", args[1]));
    }

    private void warn(Player sender, String[] args) {
        if (args.length < 3) { plugin.msg(sender, Lang.text("moderation.usage-mod-warn", "&eUsage: /mod warn <player> <reason>")); return; }
        OfflinePlayer target = Bukkit.getOfflinePlayer(args[1]);
        data.set("players." + target.getUniqueId() + ".warnings." + System.currentTimeMillis(), join(args, 2));
        save();
        Player online = target.getPlayer();
        if (online != null) plugin.msg(online, Lang.text("moderation.warning", "&cWarning: &f{0}", join(args, 2)));
        plugin.msg(sender, Lang.text("moderation.warned", "&aWarned &e{0}&a.", args[1]));
    }

    private void note(Player sender, String[] args) {
        if (args.length < 3) { plugin.msg(sender, Lang.text("moderation.usage-mod-note", "&eUsage: /mod note <player> <note>")); return; }
        OfflinePlayer target = Bukkit.getOfflinePlayer(args[1]);
        data.set("players." + target.getUniqueId() + ".notes." + System.currentTimeMillis(), join(args, 2));
        save();
        plugin.msg(sender, Lang.text("moderation.added-staff-note", "&aAdded staff note."));
    }

    private void toggle(Player sender, String[] args, String key) {
        if (args.length < 2) { plugin.msg(sender, Lang.text("moderation.usage-mod", "&eUsage: /mod {0} <player>", key)); return; }
        OfflinePlayer target = Bukkit.getOfflinePlayer(args[1]);
        boolean next = !data.getBoolean("players." + target.getUniqueId() + "." + key, false);
        data.set("players." + target.getUniqueId() + "." + key, next);
        save();
        plugin.msg(sender, Lang.text("moderation.for", "&e{0} for {1}: {2}", key, args[1], next));
    }

    private void vanish(Player player) {
        boolean next = !data.getBoolean("players." + player.getUniqueId() + ".vanished", false);
        data.set("players." + player.getUniqueId() + ".vanished", next);
        save();
        for (Player online : Bukkit.getOnlinePlayers()) {
            if (!online.hasPermission("donsup.staff")) {
                plugin.platform().playerNow(online, () -> com.donsup.compat.BukkitCompat.visible(plugin,online,player,!next));
            }
        }
        plugin.msg(player, Lang.text("moderation.vanish-55d919", "&eVanish: {0}", (next ? Lang.text("moderation.on", "&aON") : Lang.text("moderation.off", "&cOFF"))));
    }

    private void staffChat(Player player, String msg) {
        if (msg.isBlank()) return;
        staffBroadcast(Lang.text("moderation.staff", "&b[Staff] &e{0}&7: &f{1}", player.getName(), msg));
    }

    private void staffBroadcast(String msg) {
        for (Player online : Bukkit.getOnlinePlayers()) if (online.hasPermission("donsup.staff")) plugin.msg(online, msg);
    }

    @EventHandler public void onChat(AsyncPlayerChatEvent event) {
        long muted = mutes.getOrDefault(event.getPlayer().getUniqueId(), 0L);
        if (muted > System.currentTimeMillis()) {
            event.setCancelled(true);
            plugin.platform().player(event.getPlayer(), () -> plugin.msg(event.getPlayer(), Lang.text("moderation.you-are-muted", "&cYou are muted.")));
        }
    }

    @EventHandler public void onMove(PlayerMoveEvent event) {
        if (data.getBoolean("players." + event.getPlayer().getUniqueId() + ".frozen", false)
                && !event.getFrom().toVector().equals(event.getTo().toVector())) {
            event.setTo(event.getFrom());
        }
    }

    @EventHandler public void onJoin(PlayerJoinEvent event) {
        for (Player online : Bukkit.getOnlinePlayers()) {
            if (data.getBoolean("players." + event.getPlayer().getUniqueId() + ".vanished", false) && !online.hasPermission("donsup.staff")) {
                plugin.platform().playerNow(online, () -> com.donsup.compat.BukkitCompat.visible(plugin,online,event.getPlayer(),false));
            }
            if (data.getBoolean("players." + online.getUniqueId() + ".vanished", false) && !event.getPlayer().hasPermission("donsup.staff")) {
                com.donsup.compat.BukkitCompat.visible(plugin,event.getPlayer(),online,false);
            }
        }
    }

    @EventHandler public void onClick(InventoryClickEvent event) {
        if (!com.donsup.gui.OwnedInventory.buttonClick(event)) return;
        if (com.donsup.gui.OwnedInventory.title(event.getView()).equals(TITLE)) event.setCancelled(true);
    }

    private ItemStack button(Material material, String name, List<String> lore, String action) { return plugin.button(material, name, lore, actionKey, action); }
    private String join(String[] args, int start) { return String.join(" ", java.util.Arrays.copyOfRange(args, start, args.length)); }
    private long parse(String input) { try { return Long.parseLong(input); } catch (Exception ex) { return -1; } }
}


===== src/main/java/com/donsup/platform/PaperAccess.java =====

package com.donsup.platform;

import org.bukkit.*;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.plugin.Plugin;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;

/** Never loaded by the Spigot path. */
final class PaperAccess {
    static boolean owns(Entity entity) { return Bukkit.isOwnedByCurrentRegion(entity); }
    static boolean owns(Location location) { return location!=null && location.getWorld()!=null && Bukkit.isOwnedByCurrentRegion(location); }
    static void entity(Plugin p,Entity entity,Runnable action,Runnable retired) {
        if(!entity.getScheduler().execute(p,action,retired,1)) retired.run();
    }
    static TaskHandle entityLater(Plugin p,Player entity,Runnable action,long delay) {
        var t=entity.getScheduler().runDelayed(p,ignored -> action.run(),null,Math.max(1,delay));return t==null?TaskHandle.NONE:t::cancel;
    }
    static TaskHandle entityTimer(Plugin p,Player entity,Consumer<TaskHandle> action,long delay,long period) {
        var t=entity.getScheduler().runAtFixedRate(p,task -> action.accept(task::cancel),null,Math.max(1,delay),Math.max(1,period));return t==null?TaskHandle.NONE:t::cancel;
    }
    static void global(Plugin p,Runnable action) { Bukkit.getGlobalRegionScheduler().execute(p,action); }
    static TaskHandle globalLater(Plugin p,Runnable action,long delay) {
        var t=Bukkit.getGlobalRegionScheduler().runDelayed(p,ignored -> action.run(),Math.max(1,delay));return t::cancel;
    }
    static TaskHandle globalTimer(Plugin p,Runnable action,long delay,long period) {
        var t=Bukkit.getGlobalRegionScheduler().runAtFixedRate(p,ignored -> action.run(),Math.max(1,delay),Math.max(1,period));return t::cancel;
    }
    static void region(Plugin p,Location at,Runnable action) { Bukkit.getRegionScheduler().execute(p,at,action); }
    static CompletableFuture<Boolean> teleport(Player player,Location target) { return player.teleportAsync(target); }
    static CompletableFuture<Chunk> chunk(World world,int x,int z) { return world.getChunkAtAsync(x,z,true); }
    static void blankScores(org.bukkit.scoreboard.Objective objective) { objective.numberFormat(io.papermc.paper.scoreboard.numbers.NumberFormat.blank()); }
}


===== src/main/java/com/donsup/platform/ServerPlatform.java =====

package com.donsup.platform;

import com.donsup.DonsupPlugin;
import org.bukkit.*;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import java.lang.reflect.InvocationTargetException;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;

/** Shared state is serialized; entity/world access still runs on its owning thread. */
public final class ServerPlatform {
    private final DonsupPlugin plugin;
    private final Object state = new Object();
    private final boolean folia;
    private final boolean paper;
    public ServerPlatform(DonsupPlugin plugin) {
        this(plugin,present("io.papermc.paper.configuration.GlobalConfiguration") || present("com.destroystokyo.paper.PaperConfig") || present("org.github.paperspigot.PaperSpigotConfig"),present("io.papermc.paper.threadedregions.RegionizedServer"));
    }
    ServerPlatform(DonsupPlugin plugin,boolean paper,boolean folia) {
        this.plugin = plugin;
        this.folia=folia;
        this.paper=paper;
    }
    private static boolean present(String name) {
        try { Class.forName(name, false, ServerPlatform.class.getClassLoader()); return true; }
        catch (ClassNotFoundException | LinkageError ex) { return false; }
    }
    public boolean folia() { return folia; }
    public boolean paper() { return paper; }
    public boolean nativeDialogs() { return com.donsup.compat.DialogCapabilities.available(); }
    public boolean modernCommands() { return present("io.papermc.paper.command.brigadier.BasicCommand"); }
    public String name() { return folia ? "Folia" : paper ? "Paper" : "Spigot/Bukkit"; }
    public void locked(Runnable action) { synchronized(state) { action.run(); } }
    public <T> T locked(java.util.function.Supplier<T> action) { synchronized(state) { return action.get(); } }
    private Runnable guard(Runnable action) { return () -> locked(action); }
    public boolean owns(Entity entity) { return !folia || PaperAccess.owns(entity); }
    public boolean owns(Location location) { return !folia || PaperAccess.owns(location); }
    public void entity(Entity entity,Runnable action) {
        if(!plugin.isEnabled())return;
        if(folia)PaperAccess.entity(plugin,entity,guard(action),()->{});else global(action);
    }
    public void player(Player player, Runnable action) {
        if (!plugin.isEnabled()) return;
        if (folia) PaperAccess.entity(plugin, player, guard(action), () -> {});
        else Bukkit.getScheduler().runTask(plugin, guard(action));
    }
    public void playerNow(Player player, Runnable action) {
        if (!plugin.isEnabled()) return;
        if (owns(player) && (folia || Bukkit.isPrimaryThread())) locked(action); else player(player, action);
    }
    public CompletableFuture<Boolean> onPlayer(Player player, Runnable action) {
        CompletableFuture<Boolean> result = new CompletableFuture<>();
        Runnable run = () -> { try { locked(action); result.complete(true); } catch(Throwable ex) { result.completeExceptionally(ex); } };
        if (!plugin.isEnabled()) { result.complete(false); return result; }
        if (folia) PaperAccess.entity(plugin, player, run, () -> result.complete(false));
        else Bukkit.getScheduler().runTask(plugin, run);
        return result;
    }
    public TaskHandle playerLater(Player player, Runnable action, long ticks) {
        if (folia) return PaperAccess.entityLater(plugin, player, guard(action), ticks);
        var task = Bukkit.getScheduler().runTaskLater(plugin, guard(action), Math.max(1,ticks));
        return task::cancel;
    }
    public TaskHandle playerTimer(Player player, Consumer<TaskHandle> action, long delay, long period) {
        if (folia) return PaperAccess.entityTimer(plugin,player,t -> locked(() -> action.accept(t)),delay,period);
        var task = new org.bukkit.scheduler.BukkitRunnable() {
            @Override public void run() { locked(() -> action.accept(this::cancel)); }
        };
        task.runTaskTimer(plugin,Math.max(1,delay),Math.max(1,period));
        return task::cancel;
    }
    public void global(Runnable action) {
        if (!plugin.isEnabled()) return;
        if (folia) PaperAccess.global(plugin,guard(action)); else Bukkit.getScheduler().runTask(plugin,guard(action));
    }
    public TaskHandle globalLater(Runnable action,long ticks) {
        if (folia) return PaperAccess.globalLater(plugin,guard(action),ticks);
        var task=Bukkit.getScheduler().runTaskLater(plugin,guard(action),Math.max(1,ticks));return task::cancel;
    }
    public TaskHandle globalTimer(Runnable action,long delay,long period) {
        if (folia) return PaperAccess.globalTimer(plugin,guard(action),delay,period);
        var task=Bukkit.getScheduler().runTaskTimer(plugin,guard(action),Math.max(1,delay),Math.max(1,period));return task::cancel;
    }
    public void region(Location location,Runnable action) {
        if (!plugin.isEnabled()) return;
        if (folia) PaperAccess.region(plugin,location,guard(action)); else global(action);
    }
    public void eachPlayer(Consumer<Player> action) {
        for(Player p:Bukkit.getOnlinePlayers()) player(p,() -> { if(p.isOnline()) action.accept(p); });
    }
    @SuppressWarnings("unchecked") public CompletableFuture<Boolean> teleport(Player player,Location target) {
        if((paper || folia) && com.donsup.compat.BukkitCompat.method(Player.class,"teleportAsync",Location.class))
            return (CompletableFuture<Boolean>)com.donsup.compat.BukkitCompat.call(player,"teleportAsync",new Class<?>[]{Location.class},target);
        try { return CompletableFuture.completedFuture(player.teleport(target)); }
        catch(RuntimeException ex) { return CompletableFuture.failedFuture(ex); }
    }
    @SuppressWarnings("unchecked") public CompletableFuture<Chunk> chunk(World world,int x,int z) {
        if((paper || folia) && com.donsup.compat.BukkitCompat.method(World.class,"getChunkAtAsync",int.class,int.class,boolean.class))
            return (CompletableFuture<Chunk>)com.donsup.compat.BukkitCompat.call(world,"getChunkAtAsync",new Class<?>[]{int.class,int.class,boolean.class},x,z,true);
        CompletableFuture<Chunk> future=new CompletableFuture<>();
        global(() -> { try { future.complete(world.getChunkAt(x,z)); } catch(Throwable ex) { future.completeExceptionally(ex); } });
        return future;
    }
    public void register(Listener listener) {
        for(var method:listener.getClass().getMethods()) {
            EventHandler handler=method.getAnnotation(EventHandler.class);
            if(handler==null || method.getParameterCount()!=1 || !Event.class.isAssignableFrom(method.getParameterTypes()[0])) continue;
            Class<? extends Event> type=method.getParameterTypes()[0].asSubclass(Event.class);
            Bukkit.getPluginManager().registerEvent(type,listener,handler.priority(),(ignored,event) -> {
                if(!type.isInstance(event))return;
                synchronized(state) {
                    try { method.invoke(listener,event); }
                    catch(InvocationTargetException ex) { throw new EventException(ex.getCause()); }
                    catch(ReflectiveOperationException ex) { throw new EventException(ex); }
                }
            },plugin,handler.ignoreCancelled());
        }
    }
    public void blankScores(org.bukkit.scoreboard.Objective objective) {
        if((paper || folia) && present("io.papermc.paper.scoreboard.numbers.NumberFormat")) PaperAccess.blankScores(objective);
    }
}


===== src/main/java/com/donsup/platform/TaskHandle.java =====

package com.donsup.platform;

@FunctionalInterface
public interface TaskHandle {
    void cancel();
    TaskHandle NONE = () -> {};
}


===== src/main/java/com/donsup/preset/PresetManager.java =====

package com.donsup.preset;

import com.donsup.config.Lang;

import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.InvalidConfigurationException;
import org.bukkit.configuration.file.YamlConfiguration;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.function.Predicate;

/** Versioned config overlays with backup, rollback, and interrupted-install recovery. */
public final class PresetManager {
    public static final List<String> BUNDLED = List.of("donutsmp-style", "donut-style", "community", "survival-plus", "pvp-economy");
    private static final List<String> FILES = List.of("config.yml", "shops.yml", "preset-state.yml");
    private static final long MAX_FILE_BYTES = 2 * 1024 * 1024;
    private final Path root;
    private final Predicate<String> pluginAvailable;

    public record Profile(String id, String name, String description, List<String> requirements) {}
    public record Preview(Profile profile, List<String> changes, List<String> missingPlugins) {
        public boolean ready() { return missingPlugins.isEmpty(); }
    }
    public record Result(String preset, String backupId, int changes) {}
    private record Prepared(Preview preview, Map<String, byte[]> contents) {}

    public PresetManager(Path root, Predicate<String> pluginAvailable) throws IOException {
        Files.createDirectories(root);
        this.root = root.toRealPath();
        this.pluginAvailable = pluginAvailable;
    }

    public List<String> list() {
        try (var entries = Files.list(safe("presets"))) {
            return entries.filter(p -> Files.isDirectory(p, LinkOption.NOFOLLOW_LINKS))
                    .map(p -> p.getFileName().toString()).filter(PresetManager::validId)
                    .filter(id -> Files.isRegularFile(root.resolve("presets/" + id + "/config.yml"), LinkOption.NOFOLLOW_LINKS))
                    .sorted().toList();
        } catch (IOException e) { return List.of(); }
    }

    public Profile profile(String id) throws IOException {
        requireId(id);
        Path folder = safe("presets/" + id);
        if (!Files.isDirectory(folder, LinkOption.NOFOLLOW_LINKS)) throw new IOException(Lang.text("preset.unknown-preset", "Unknown preset: {0}", id));
        Path manifest = safe("presets/" + id + "/preset.yml");
        YamlConfiguration info = Files.exists(manifest) ? read(manifest) : new YamlConfiguration();
        if (info.getInt("format", 1) != 1) throw new IOException(Lang.text("preset.unsupported-preset-format", "Unsupported preset format: {0}", id));
        return new Profile(id, info.getString("name", id), info.getString("description", "Custom SMP configuration"),
                List.copyOf(info.getStringList("requires-plugins")));
    }

    public synchronized Preview preview(String id) throws IOException { return prepare(id).preview(); }

    public synchronized Result apply(String id) throws IOException {
        recoverPending();
        Prepared prepared = prepare(id);
        if (!prepared.preview.ready()) throw new IOException(Lang.text("preset.install-the-required-plugins-first", "Install the required plugins first: {0}", String.join(Lang.text("preset.text", ", "), prepared.preview.missingPlugins)));
        return commit(id, prepared.contents, prepared.preview.changes.size());
    }

    public synchronized Result rollback() throws IOException {
        recoverPending();
        YamlConfiguration state = read(safe("preset-state.yml"));
        String backup = state.getString("backup-id", "");
        Map<String, byte[]> originals = backupContents(backup);
        // A rollback is itself backed up, so repeating rollback can undo it.
        return commit("rollback", originals, 2);
    }

    public boolean hasAppliedPreset() { return Files.isRegularFile(root.resolve("preset-state.yml")); }

    /** Run before loading live configuration. Keep the journal if recovery fails. */
    public synchronized void recoverPending() throws IOException {
        Path pending = safe("preset-pending.yml");
        if (!Files.exists(pending)) return;
        String backup = read(pending).getString("backup-id", "");
        restore(backupContents(backup));
        Files.delete(pending);
    }

    private Prepared prepare(String id) throws IOException {
        Profile profile = profile(id);
        YamlConfiguration current = read(safe("config.yml"));
        YamlConfiguration merged = parse(current.saveToString(), "current config");
        YamlConfiguration overlay = read(safe("presets/" + id + "/config.yml"));
        if (overlay.getKeys(false).isEmpty()) throw new IOException(Lang.text("preset.preset-config-is-empty", "Preset config is empty"));
        boolean preserveBranding = current.getBoolean("setup.preserve-branding", true);
        for (String key : overlay.getKeys(true)) {
            if (overlay.isConfigurationSection(key) || key.equals("setup") || key.startsWith("setup.")) continue;
            if (preserveBranding && (key.equals("branding") || key.startsWith("branding."))) continue;
            Object old = current.get(key), next = overlay.get(key);
            if (old != null && ((old instanceof Number && !(next instanceof Number))
                    || (old instanceof Boolean && !(next instanceof Boolean))))
                throw new IOException(Lang.text("preset.incorrect-value-type-at", "Incorrect value type at {0}", key));
            merged.set(key, overlay.get(key));
        }
        validateConfig(merged);
        List<String> changes = differences("config", current, merged);
        Map<String, byte[]> contents = new LinkedHashMap<>();
        contents.put("config.yml", bytes(merged.saveToString()));
        Path shopOverlay = safe("presets/" + id + "/shops.yml");
        YamlConfiguration shops = read(safe("shops.yml"));
        YamlConfiguration nextShops = Files.exists(shopOverlay) ? read(shopOverlay) : shops;
        validateShops(nextShops);
        changes.addAll(differences("shops", shops, nextShops));
        contents.put("shops.yml", bytes(nextShops.saveToString()));
        List<String> missing = profile.requirements.stream().filter(p -> !pluginAvailable.test(p)).toList();
        return new Prepared(new Preview(profile, List.copyOf(changes), missing), contents);
    }

    private Result commit(String id, Map<String, byte[]> desired, int changes) throws IOException {
        String backupId = System.currentTimeMillis() + "-" + UUID.randomUUID();
        Path backup = safe("backups/presets/" + backupId);
        Files.createDirectories(backup);
        YamlConfiguration metadata = new YamlConfiguration();
        for (String name : FILES) {
            Path original = safe(name);
            boolean exists = Files.exists(original);
            metadata.set("exists." + name.replace('.', '_'), exists);
            if (exists) Files.write(backup.resolve(name), boundedRead(original), StandardOpenOption.CREATE_NEW);
        }
        atomicWrite(backup.resolve("backup.yml"), bytes(metadata.saveToString()));
        YamlConfiguration pending = new YamlConfiguration();
        pending.set("backup-id", backupId);
        atomicWrite(safe("preset-pending.yml"), bytes(pending.saveToString()));
        try {
            for (String name : List.of("config.yml", "shops.yml")) {
                byte[] content = desired.get(name);
                if (content == null) Files.deleteIfExists(safe(name));
                else atomicWrite(safe(name), content);
            }
            YamlConfiguration state = new YamlConfiguration();
            state.set("preset", id);
            state.set("backup-id", backupId);
            state.set("applied-at", System.currentTimeMillis());
            atomicWrite(safe("preset-state.yml"), bytes(state.saveToString()));
            Files.delete(safe("preset-pending.yml"));
        } catch (IOException | RuntimeException failure) {
            try { recoverPending(); } catch (IOException recovery) { failure.addSuppressed(recovery); }
            throw new IOException(Lang.text("preset.preset-installation-failed-previous-configuration-recovery-was-at", "Preset installation failed; previous configuration recovery was attempted. {0}", failure.getMessage()), failure);
        }
        return new Result(id, backupId, changes);
    }

    private Map<String, byte[]> backupContents(String id) throws IOException {
        requireId(id);
        Path backup = safe("backups/presets/" + id);
        YamlConfiguration metadata = read(safe("backups/presets/" + id + "/backup.yml"));
        Map<String, byte[]> result = new LinkedHashMap<>();
        for (String name : FILES) {
            if (!metadata.contains("exists." + name.replace('.', '_'))) throw new IOException(Lang.text("preset.incomplete-backup", "Incomplete backup: {0}", id));
            result.put(name, metadata.getBoolean("exists." + name.replace('.', '_'))
                    ? boundedRead(safe("backups/presets/" + id + "/" + name)) : null);
        }
        return result;
    }

    private void restore(Map<String, byte[]> originals) throws IOException {
        for (String name : FILES) {
            if (originals.get(name) == null) Files.deleteIfExists(safe(name));
            else atomicWrite(safe(name), originals.get(name));
        }
    }

    private Path safe(String relative) throws IOException {
        Path path = root.resolve(relative).normalize();
        if (!path.startsWith(root) || path.equals(root)) throw new IOException(Lang.text("preset.path-must-stay-inside-the-plugin-folder", "Path must stay inside the plugin folder"));
        Path cursor = root;
        for (Path part : root.relativize(path)) {
            cursor = cursor.resolve(part);
            if (Files.isSymbolicLink(cursor) || (Files.exists(cursor) && !cursor.toRealPath().startsWith(root)))
                throw new IOException(Lang.text("preset.linked-paths-are-not-supported-for-preset-files", "Linked paths are not supported for preset files"));
        }
        return path;
    }

    private static boolean validId(String id) { return id != null && id.matches("[a-zA-Z0-9][a-zA-Z0-9_-]{0,100}"); }
    private static void requireId(String id) throws IOException { if (!validId(id)) throw new IOException(Lang.text("preset.invalid-preset-or-backup-id", "Invalid preset or backup ID")); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static byte[] boundedRead(Path path) throws IOException {
        if (Files.size(path) > MAX_FILE_BYTES) throw new IOException(Lang.text("preset.preset-file-exceeds-2-mib", "Preset file exceeds 2 MiB: {0}", path.getFileName()));
        return Files.readAllBytes(path);
    }
    private static YamlConfiguration read(Path path) throws IOException { return parse(new String(boundedRead(path), StandardCharsets.UTF_8), path.getFileName().toString()); }
    private static YamlConfiguration parse(String text, String name) throws IOException {
        YamlConfiguration yaml = new YamlConfiguration();
        try { yaml.loadFromString(text); } catch (InvalidConfigurationException e) { throw new IOException(Lang.text("preset.invalid-yaml-in", "Invalid YAML in {0}", name), e); }
        return yaml;
    }
    private static void atomicWrite(Path target, byte[] contents) throws IOException {
        Path temporary = target.resolveSibling(target.getFileName() + ".tmp-" + UUID.randomUUID());
        try {
            Files.write(temporary, contents, StandardOpenOption.CREATE_NEW);
            try { Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING); }
            catch (AtomicMoveNotSupportedException e) { Files.move(temporary, target, StandardCopyOption.REPLACE_EXISTING); }
        } finally { Files.deleteIfExists(temporary); }
    }
    private static List<String> differences(String prefix, YamlConfiguration before, YamlConfiguration after) {
        Set<String> keys = new TreeSet<>(before.getKeys(true)); keys.addAll(after.getKeys(true));
        List<String> changes = new ArrayList<>();
        for (String key : keys) if (!before.isConfigurationSection(key) && !after.isConfigurationSection(key)
                && !Objects.equals(before.get(key), after.get(key))) changes.add(prefix + "." + key);
        return changes;
    }
    private static void validateConfig(YamlConfiguration config) throws IOException {
        for (String key : config.getKeys(true)) {
            if (!List.of("settings", "daily", "dynamic-pricing", "duels", "drills", "custom-spawners",
                    "sell-prices", "shard-shop", "crates", "player-warps", "premium-kit").contains(key.split("\\.")[0])) continue;
            Object value = config.get(key);
            if (value instanceof Number n && (!Double.isFinite(n.doubleValue()) || n.doubleValue() < 0))
                throw new IOException(Lang.text("preset.expected-a-finite-non-negative-number-at", "Expected a finite, non-negative number at {0}", key));
        }
        for (String key : List.of("settings.starting-money", "settings.starting-shards", "settings.default-home-limit", "custom-spawners.drop-generation-seconds")) {
            if (!(config.get(key) instanceof Number)) throw new IOException(Lang.text("preset.expected-a-number-at", "Expected a number at {0}", key));
        }
        if (config.getDouble("custom-spawners.drop-generation-seconds") < 1) throw new IOException(Lang.text("preset.spawner-interval-must-be-at-least-1-second", "Spawner interval must be at least 1 second"));
        if (config.getDouble("dynamic-pricing.min-multiplier", 0.5) > config.getDouble("dynamic-pricing.max-multiplier", 2.5))
            throw new IOException(Lang.text("preset.dynamic-price-minimum-exceeds-maximum", "Dynamic price minimum exceeds maximum"));
    }
    private static void validateShops(YamlConfiguration shops) throws IOException {
        ConfigurationSection categories = shops.getConfigurationSection("categories");
        if (categories == null || categories.getKeys(false).isEmpty()) throw new IOException(Lang.text("preset.preset-shops-must-contain-categories", "Preset shops must contain categories"));
        for (String category : categories.getKeys(false)) {
            ConfigurationSection items = categories.getConfigurationSection(category + ".items");
            if (items == null) throw new IOException(Lang.text("preset.missing-items-in-shop-category", "Missing items in shop category {0}", category));
            for (String item : items.getKeys(false)) {
                String prefix = item + ".";
                if (items.getString(prefix + "material", "").isBlank()) throw new IOException(Lang.text("preset.missing-shop-material", "Missing shop material: {0}", item));
                for (String key : List.of("buy", "sell", "amount")) {
                    Object raw = items.get(prefix + key);
                    if (!(raw instanceof Number n) || !Double.isFinite(n.doubleValue()) || n.doubleValue() < 0)
                        throw new IOException(Lang.text("preset.invalid-shop", "Invalid shop {0}.{1}", item, key));
                }
                if (items.getDouble(prefix + "amount") < 1 || items.getDouble(prefix + "amount") > 64)
                    throw new IOException(Lang.text("preset.shop-amount-must-be-1-64", "Shop amount must be 1-64: {0}", item));
            }
        }
    }
}


===== src/main/java/com/donsup/progression/DailyManager.java =====

package com.donsup.progression;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.ItemUtil;
import com.donsup.util.Text;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;

import java.io.File;
import java.io.IOException;
import java.time.LocalDate;
import java.util.List;

public class DailyManager implements Listener {
    private static final String TITLE = "SMP | Daily Rewards";
    private final DonsupPlugin plugin;
    private final ItemKey actionKey;
    private final File file;
    private FileConfiguration data;

    public DailyManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.actionKey = new ItemKey(plugin, "daily_action");
        this.file = new File(plugin.getDataFolder(), "daily.yml");
        reload();
    }

    public void reload() { data = com.donsup.util.SafeYaml.load(file); }
    public void save() { try { com.donsup.util.SafeYaml.save(data, file); } catch (IOException ex) { plugin.getLogger().warning("Could not save daily.yml: " + ex.getMessage()); } }

    public void open(Player player) {
        Inventory inv = plugin.inventory(27, TITLE, false);
        ItemStack glass = button(com.donsup.compat.Materials.GRAY_STAINED_GLASS_PANE, " ", List.of(), "NONE");
        for (int i = 0; i < inv.getSize(); i++) inv.setItem(i, glass);
        int streak = streak(player);
        inv.setItem(4, button(com.donsup.compat.Materials.SUNFLOWER, Lang.text("daily.daily-rewards", "&e&lDaily Rewards"), List.of(Lang.text("daily.streak", "&7Streak: &e{0}", streak), Lang.text("daily.today", "&7Today: {0}", (claimable(player) ? Lang.text("daily.ready", "&aReady") : Lang.text("daily.claimed", "&cClaimed")))), "NONE"));
        inv.setItem(13, button(claimable(player) ? com.donsup.compat.Materials.LIME_DYE : com.donsup.compat.Materials.GRAY_DYE, Lang.text("daily.claim-daily", "&aClaim Daily"), rewardLore(player), "CLAIM"));
        player.openInventory(inv);
    }

    public void claim(Player player) {
        if (!claimable(player)) { plugin.msg(player, Lang.text("daily.you-already-claimed-today-s-reward", "&cYou already claimed today's reward.")); return; }
        int streak = streak(player) + 1;
        double money = plugin.getConfig().getDouble("daily.money", 1000) + (streak * plugin.getConfig().getDouble("daily.money-per-streak", 100));
        int shards = plugin.getConfig().getInt("daily.shards", 25) + (streak * plugin.getConfig().getInt("daily.shards-per-streak", 2));
        if (plugin.economy().premium(player)) {
            money *= plugin.getConfig().getDouble("daily.premium-multiplier", 1.5);
            shards = (int) Math.round(shards * plugin.getConfig().getDouble("daily.premium-multiplier", 1.5));
        }
        data.set("players." + player.getUniqueId() + ".last", today());
        data.set("players." + player.getUniqueId() + ".streak", streak);
        save();
        plugin.economy().deposit(player.getUniqueId(), money);
        plugin.economy().addShards(player.getUniqueId(), shards);
        plugin.msg(player, Lang.text("daily.daily-claimed-and-shards-streak", "&aDaily claimed: &e{0} &7and &d{1} shards&a. Streak: &e{2}", Text.money(money), shards, streak));
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent event) {
        plugin.platform().playerLater(event.getPlayer(), () -> { if (event.getPlayer().isOnline() && claimable(event.getPlayer())) plugin.msg(event.getPlayer(), Lang.text("daily.your-daily-reward-is-ready-daily", "&eYour daily reward is ready: &f/daily&e.")); }, 60L);
    }

    @EventHandler
    public void onClick(InventoryClickEvent event) {
        if (!com.donsup.gui.OwnedInventory.buttonClick(event)) return;
        if (!(event.getWhoClicked() instanceof Player player) || !com.donsup.gui.OwnedInventory.title(event.getView()).equals(TITLE)) return;
        event.setCancelled(true);
        ItemStack item = event.getCurrentItem();
        if (item == null || !item.hasItemMeta()) return;
        String action = com.donsup.compat.ItemTags.getString(item.getItemMeta(), actionKey);
        if ("CLAIM".equals(action)) { claim(player); open(player); }
    }

    private List<String> rewardLore(Player player) {
        return List.of(Lang.text("daily.money-and-shard-reward", "&7Money and shard reward."), Lang.text("daily.premium-multiplier-x", "&7Premium multiplier: &e{0}x", plugin.getConfig().getDouble("daily.premium-multiplier", 1.5)), Lang.text("daily.click-to-claim", "&aClick to claim."));
    }
    private boolean claimable(Player player) { return !today().equals(data.getString("players." + player.getUniqueId() + ".last", "")); }
    private int streak(Player player) {
        String key = "players." + player.getUniqueId();
        return DailyStreak.current(data.getString(key + ".last", ""), data.getInt(key + ".streak", 0), LocalDate.now());
    }
    private String today() { return LocalDate.now().toString(); }
    private ItemStack button(Material material, String name, List<String> lore, String action) { return plugin.button(material, name, lore, actionKey, action); }
}


===== src/main/java/com/donsup/progression/DailyStreak.java =====

package com.donsup.progression;

import java.time.LocalDate;
import java.time.format.DateTimeParseException;

/** Date-only rules use the server's local calendar, matching the daily claim key. */
public final class DailyStreak {
    private DailyStreak() { }
    public static int current(String lastClaim, int saved, LocalDate today) {
        try {
            LocalDate last = LocalDate.parse(lastClaim);
            return last.equals(today) || last.equals(today.minusDays(1)) ? Math.max(0, saved) : 0;
        } catch (DateTimeParseException | NullPointerException ex) {
            return 0;
        }
    }
}


===== src/main/java/com/donsup/progression/KitsManager.java =====

package com.donsup.progression;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.ItemUtil;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;

public class KitsManager implements Listener {
    private static final String TITLE = "SMP | Kits";
    private final DonsupPlugin plugin;
    private final ItemKey actionKey;
    private final File file;
    private FileConfiguration data;

    public KitsManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.actionKey = new ItemKey(plugin, "kit_action");
        this.file = new File(plugin.getDataFolder(), "kits.yml");
        reload();
        seedDefaults();
    }

    public void reload() { data = com.donsup.util.SafeYaml.load(file); }
    public void save() { try { com.donsup.util.SafeYaml.save(data, file); } catch (IOException ex) { plugin.getLogger().warning("Could not save kits.yml: " + ex.getMessage()); } }

    private void seedDefaults() {
        if (data.contains("kits.starter")) return;
        data.set("kits.starter.display", Lang.text("kits.starter-kit", "&aStarter Kit"));
        data.set("kits.starter.cooldown-hours", 24);
        data.set("kits.starter.icon", "IRON_SWORD");
        data.set("kits.starter.items", List.of(new ItemStack(Material.IRON_SWORD), new ItemStack(Material.COOKED_BEEF, 32), new ItemStack(com.donsup.compat.Materials.OAK_LOG, 64)));
        save();
    }

    public void open(Player player) {
        Inventory inv = plugin.inventory(54, TITLE, false);
        fill(inv);
        inv.setItem(4, button(Material.CHEST, Lang.text("kits.kits", "&a&lKits"), List.of(Lang.text("kits.preview-and-claim-cooldown-kits", "&7Preview and claim cooldown kits."), Lang.text("kits.admins-kitadmin-save", "&7Admins: /kitadmin save <id>")), "NONE"));
        ConfigurationSection kits = data.getConfigurationSection("kits");
        int slot = 10;
        if (kits != null) for (String id : kits.getKeys(false)) {
            if (slot >= 45) break;
            long remaining = remaining(player, id);
            inv.setItem(slot++, button(icon(id), data.getString("kits." + id + ".display", "&a" + title(id)), List.of(
                    remaining <= 0 ? Lang.text("kits.ready-to-claim", "&aReady to claim") : Lang.text("kits.cooldown-minutes", "&cCooldown: {0} minutes", (remaining / 60000L)),
                    Lang.text("kits.left-click-claim", "&7Left click: claim"),
                    Lang.text("kits.right-click-preview", "&7Right click: preview")
            ), "KIT:" + id));
        }
        player.openInventory(inv);
    }

    public void command(Player player, String[] args) {
        if (args.length == 0) { open(player); return; }
        claim(player, args[0]);
    }

    public void admin(Player player, String[] args) {
        if (!player.hasPermission("donsup.admin")) { plugin.msg(player, Lang.text("kits.no-permission", "&cNo permission.")); return; }
        if (args.length < 2) { plugin.msg(player, Lang.text("kits.usage-kitadmin", "&eUsage: /kitadmin <save|delete> <id>")); return; }
        String id = clean(args[1]);
        if (id.isBlank() || id.length() > 32) { plugin.msg(player, Lang.text("kits.use-a-kit-id-of-1-32-letters-numbers-underscores-or-hyphens", "&cUse a kit ID of 1-32 letters, numbers, underscores or hyphens.")); return; }
        if (args[0].equalsIgnoreCase("save")) {
            data.set("kits." + id + ".display", Lang.text("kits.kit", "&a{0} Kit", title(id)));
            data.set("kits." + id + ".cooldown-hours", 24);
            data.set("kits." + id + ".icon", com.donsup.compat.BukkitCompat.air(com.donsup.compat.BukkitCompat.hand(player.getInventory()).getType()) ? "CHEST" : com.donsup.compat.BukkitCompat.hand(player.getInventory()).getType().name());
            data.set("kits." + id + ".items", Arrays.stream(com.donsup.compat.BukkitCompat.storage(player.getInventory())).filter(item -> item != null && !com.donsup.compat.BukkitCompat.air(item.getType())).map(ItemStack::clone).toList());
            save();
            plugin.msg(player, Lang.text("kits.saved-kit-from-your-inventory", "&aSaved kit &e{0}&a from your inventory.", id));
        } else if (args[0].equalsIgnoreCase("delete")) {
            data.set("kits." + id, null);
            save();
            plugin.msg(player, Lang.text("kits.deleted-kit", "&cDeleted kit &e{0}&c.", id));
        }
    }

    private void claim(Player player, String id) {
        id = clean(id);
        if (id.isBlank() || !data.contains("kits." + id)) { plugin.msg(player, Lang.text("kits.kit-not-found", "&cKit not found.")); return; }
        long remaining = remaining(player, id);
        if (remaining > 0) { plugin.msg(player, Lang.text("kits.kit-cooldown-minutes", "&cKit cooldown: &e{0} minutes&c.", remaining / 60000L)); return; }
        List<ItemStack> items = data.getList("kits." + id + ".items", List.of()).stream()
                .filter(ItemStack.class::isInstance).map(ItemStack.class::cast).toList();
        if (!com.donsup.util.InventoryCapacity.fitsBatch(player, items)) {
            plugin.msg(player, Lang.text("kits.make-room-for-the-whole-kit-first-your-cooldown-has-not-started", "&cMake room for the whole kit first. Your cooldown has not started.")); return;
        }
        for (ItemStack item : items) player.getInventory().addItem(item.clone());
        data.set("claims." + player.getUniqueId() + "." + id, System.currentTimeMillis());
        save();
        plugin.msg(player, Lang.text("kits.claimed-kit", "&aClaimed kit &e{0}&a.", id));
    }

    private void preview(Player player, String id) {
        Inventory inv = plugin.inventory(54, TITLE + " Preview " + id, false);
        List<?> items = data.getList("kits." + clean(id) + ".items", List.of());
        int slot = 0;
        for (Object raw : items) if (raw instanceof ItemStack item && slot < 54) inv.setItem(slot++, item.clone());
        player.openInventory(inv);
    }

    @EventHandler
    public void onClick(InventoryClickEvent event) {
        if (!com.donsup.gui.OwnedInventory.buttonClick(event)) return;
        if (!(event.getWhoClicked() instanceof Player player) || !com.donsup.gui.OwnedInventory.title(event.getView()).startsWith(TITLE)) return;
        if (com.donsup.gui.OwnedInventory.title(event.getView()).contains(" Preview ")) { event.setCancelled(true); return; }
        event.setCancelled(true);
        ItemStack item = event.getCurrentItem();
        if (item == null || !item.hasItemMeta()) return;
        String action = com.donsup.compat.ItemTags.getString(item.getItemMeta(), actionKey);
        if (action == null || !action.startsWith("KIT:")) return;
        String id = action.substring(4);
        if (event.isRightClick()) preview(player, id); else claim(player, id);
    }

    private long remaining(Player player, String id) {
        long last = data.getLong("claims." + player.getUniqueId() + "." + id, 0);
        long cd = Math.max(0, data.getLong("kits." + id + ".cooldown-hours", 24)) * 3600000L;
        return Math.max(0, (last + cd) - System.currentTimeMillis());
    }

    private Material icon(String id) { return ItemUtil.material(data.getString("kits." + id + ".icon"), Material.CHEST); }
    private void fill(Inventory inv) { ItemStack glass = button(com.donsup.compat.Materials.GRAY_STAINED_GLASS_PANE, " ", List.of(), "NONE"); for (int i = 0; i < inv.getSize(); i++) inv.setItem(i, glass); }
    private ItemStack button(Material material, String name, List<String> lore, String action) { return plugin.button(material, name, lore, actionKey, action); }
    private String clean(String input) { return input == null ? "starter" : input.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9_-]", ""); }
    private String title(String key) { String[] parts = clean(key).replace('_', ' ').split(" "); StringBuilder out = new StringBuilder(); for (String p : parts) if (!p.isBlank()) out.append(Character.toUpperCase(p.charAt(0))).append(p.substring(1)).append(' '); return out.toString().trim(); }
}


===== src/main/java/com/donsup/shop/ChestShopManager.java =====

package com.donsup.shop;

import com.donsup.config.Lang;
import com.donsup.compat.ItemKey;

import com.donsup.DonsupPlugin;
import com.donsup.shop.ChestShopStore.Shop;
import com.donsup.util.Text;
import org.bukkit.*;
import org.bukkit.block.*;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.entity.EntityExplodeEvent;
import org.bukkit.event.inventory.*;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.inventory.*;
import com.donsup.compat.ContainerHandle;
import com.donsup.compat.BlockTags;
import java.io.File;
import java.math.BigDecimal;
import java.util.*;

/** Physical shops with exact stock, native confirmations and fail-closed review records. */
public final class ChestShopManager implements Listener {
    private final DonsupPlugin plugin;
    private final ChestShopStore store;
    private final ShopHolograms holograms;
    public void shutdown(){holograms.shutdown();}
    private final BlockTags blockTags;
    private final ItemKey placerKey, shopKey;
    private final Map<String, String> locations = new HashMap<>();
    public ChestShopManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.blockTags = new BlockTags(plugin);
        store = new ChestShopStore(new File(plugin.getDataFolder(), "chest-shops.yml"));
        recoverUnstarted();
        holograms=new ShopHolograms(plugin,store::shops);plugin.platform().register(holograms);
        placerKey = new ItemKey(plugin, "container_placer"); shopKey = new ItemKey(plugin, "chest_shop");
        for (Shop shop : store.shops()) for(String block:store.locations(shop)) locations.put(block, shop.id());
    }
    private void recoverUnstarted() {
        for (var trade : store.history()) {
            if (!"prepared".equals(trade.get("state")) || !(trade.get("recovery-version") instanceof Number v) || v.intValue() != 1) continue;
            String id = String.valueOf(trade.get("id"));
            try {
                if (!plugin.economy().refundUnstartedShop(id)) throw new java.io.IOException(Lang.text("chest-shop.refund-cannot-be-funded-staff-review-required", "Refund cannot be funded; staff review required"));
                store.finish(id, "recovered-refund"); plugin.economy().forgetShopPayment(id);
                plugin.getLogger().info("Recovered chest-shop trade " + id + ": cancelled before item delivery.");
            } catch (Exception ex) { plugin.getLogger().warning("Chest-shop recovery deferred for " + id + ": " + ex.getMessage()); }
        }
    }
    private String location(UUID world, int x, int y, int z) { return world + ":" + x + ":" + y + ":" + z; }
    private String location(Block block) { return location(block.getWorld().getUID(), block.getX(), block.getY(), block.getZ()); }
    private Block signContainer(Block block) {
        if(block==null || !(block.getState() instanceof Sign))return block;
        BlockFace face=com.donsup.compat.BukkitCompat.facing(block);
        if(block.getType().name().contains("WALL"))return block.getRelative(face.getOppositeFace());
        return block.getRelative(BlockFace.DOWN);
    }
    private Shop at(Block block) { block=signContainer(block);return block == null ? null : store.shop(locations.get(location(block))); }
    public boolean isShop(Block block) { return block != null && locations.containsKey(location(block)); }
    private boolean enabled() { return plugin.getConfig().getBoolean("chest-shops.enabled", true); }
    private boolean owner(Player player, Shop shop) { return player.getUniqueId().equals(shop.owner()) || player.hasPermission("donsup.admin"); }
    private boolean singleContainer(Block block) {
        ContainerHandle container=ContainerHandle.of(block);
        return container!=null && container.singleShopContainer();
    }
    private ContainerHandle container(Shop shop) {
        World world = Bukkit.getWorld(shop.world());
        if (world == null || !world.isChunkLoaded(shop.x() >> 4, shop.z() >> 4)) return null;
        if (!plugin.platform().owns(new Location(world,shop.x(),shop.y(),shop.z()))) return null;
        Block block = world.getBlockAt(shop.x(), shop.y(), shop.z());
        if (!singleContainer(block)) return null;
        ContainerHandle container = ContainerHandle.of(block);
        if(!new HashSet<>(container.parts().stream().map(this::location).toList()).equals(new HashSet<>(store.locations(shop))))return null;
        for(Block part:container.parts())if(!plugin.platform().owns(part.getLocation()) || !shop.id().equals(blockTags.get(ContainerHandle.of(part),shopKey)))return null;
        return container;
    }
    public void command(CommandSender sender, String[] args) {
        if (!(sender instanceof Player player)) { plugin.msg(sender, Lang.text("chest-shop.use-chest-shop-commands-in-game", "&cUse chest-shop commands in game.")); return; }
        try {
            if (args.length == 0) {
                plugin.dialogs().notice(player, Lang.text("chest-shop.player-chest-shops", "Player Chest Shops"), Lang.text("chest-shop.place-a-chest-or-barrel-hold-the-item-to-trade-then-use-chestshop", "Place a chest or barrel, hold the item to trade, then use:\n/chestshop create sell &lt;amount&gt; &lt;price&gt;\n/chestshop create buy &lt;amount&gt; &lt;price&gt;\nSell: players buy your stock. Buy: you pay players for their items.\nRight-click another player's shop to confirm a trade.\n/chestshop list, info, stock, price, pause, resume, remove, history")); return;
            }
            String action = args[0].toLowerCase(Locale.ROOT);
            if (action.equals("list")) {
                var shops = store.shops().stream().filter(s -> s.owner().equals(player.getUniqueId())).toList();
                plugin.msg(player, Lang.text("chest-shop.your-chest-shops", "&bYour chest shops: {0}", shops.size()));
                for (Shop shop : shops) plugin.msg(player, Lang.text("chest-shop.x-at", "&7{0} &f{1} {2}x {3} &a{4} &7at {5}, {6}, {7}", shop.id(), Lang.label("modes", shop.mode(), shop.mode()), shop.amount(), shop.item().getType(), Text.money(shop.price()), shop.x(), shop.y(), shop.z()));
                return;
            }
            if (action.equals("history")) {
                store.history().stream().filter(t -> player.getUniqueId().toString().equals(t.get("owner")) || player.getUniqueId().toString().equals(t.get("customer")))
                        .sorted((a, b) -> Long.compare(((Number)b.get("time")).longValue(), ((Number)a.get("time")).longValue())).limit(10)
                        .forEach(t -> plugin.msg(player, Lang.text("chest-shop.items-trade", "&7{0} &f{1} items &a{2} &7trade {3}", t.get("state"), t.get("amount"), Text.money(((Number)t.get("price")).doubleValue()), t.get("id"))));
                return;
            }
            if (action.equals("resolve")) {
                if (!player.hasPermission("donsup.admin")) { plugin.msg(player, Lang.text("chest-shop.no-permission", "&cNo permission.")); return; }
                if (args.length != 3 || !args[2].equals("acknowledge")) { plugin.msg(player, Lang.text("chest-shop.chestshop-resolve-acknowledge-after-auditing-its-items-and-paymen", "&e/chestshop resolve <shopId> acknowledge &7after auditing its items and payment.")); return; }
                int count = 0;
                for (var record : store.history()) if (args[1].equals(record.get("shop")) && ChestShopStore.unresolved(record)) {
                    String transaction = String.valueOf(record.get("id"));
                    store.finish(transaction, "reviewed"); plugin.economy().forgetShopPayment(transaction); count++;
                }
                plugin.getLogger().info(player.getName() + " acknowledged " + count + " interrupted chest-shop trades for " + args[1]);
                plugin.msg(player, Lang.text("chest-shop.acknowledged-reviewed-trades-no-items-or-money-were-replayed", "&aAcknowledged {0} reviewed trades. No items or money were replayed.", count)); return;
            }
            Block target = com.donsup.compat.BukkitCompat.target(player, 5);
            if (action.equals("create")) { create(player, target, args); return; }
            Shop shop = action.equals("remove") && args.length == 2 ? store.shop(args[1]) : at(target);
            if (shop == null) { plugin.msg(player, Lang.text("chest-shop.look-at-a-registered-shop-chest-or-barrel", "&cLook at a registered shop chest or barrel.")); return; }
            if (action.equals("info")) {
                plugin.msg(player, Lang.text("chest-shop.shop-owner", "&bShop {0} &7Owner: {1}", shop.id(), plugin.economy().playerName(shop.owner())));
                plugin.msg(player, Lang.text("chest-shop.x-per-batch", "&f{0} {1}x {2} &a{3} &7per batch; {4}", Lang.label("modes", shop.mode(), shop.mode()), shop.amount(), shop.item().getType(), Text.money(shop.price()), (shop.paused() ? Lang.text("chest-shop.paused", "paused") : Lang.text("chest-shop.active", "active")))); return;
            }
            if (!owner(player, shop)) { plugin.msg(player, Lang.text("chest-shop.only-the-owner-or-an-administrator-can-change-this-shop", "&cOnly the owner or an administrator can change this shop.")); return; }
            if (store.pending(shop.id())) { plugin.msg(player, Lang.text("chest-shop.this-shop-has-an-interrupted-trade-requiring-staff-review", "&cThis shop has an interrupted trade requiring staff review.")); return; }
            switch (action) {
                case "stock" -> {
                    ContainerHandle container = container(shop);
                    if (container == null) { plugin.msg(player, Lang.text("chest-shop.the-original-shop-container-is-unavailable", "&cThe original shop container is unavailable.")); return; }
                    player.openInventory(container.getInventory());
                }
                case "remove" -> {
                    ContainerHandle container = container(shop);
                    var blocks=store.locations(shop);store.remove(shop.id());blocks.forEach(locations::remove);
                    if (container != null) for(Block part:container.parts()){var half=ContainerHandle.of(part);blockTags.set(half,shopKey,null);half.update(false,false);}
                    plugin.msg(player, Lang.text("chest-shop.shop-removed-its-stock-stays-in-the-container", "&aShop removed. Its stock stays in the container."));
                }
                case "price" -> {
                    if (args.length != 2) { plugin.msg(player, Lang.text("chest-shop.chestshop-price", "&e/chestshop price <total per batch>")); return; }
                    store.edit(shop.id(), price(args[1]), shop.paused()); plugin.msg(player, Lang.text("chest-shop.shop-price-updated-earlier-confirmations-are-now-invalid", "&aShop price updated. Earlier confirmations are now invalid."));
                }
                case "pause", "resume" -> { store.edit(shop.id(), shop.price(), action.equals("pause")); plugin.msg(player, Lang.text("chest-shop.shop-d", "&aShop {0}d.", action)); }
                default -> plugin.msg(player, Lang.text("chest-shop.chestshop-create-list-info-stock-price-pause-resume-remove-histor", "&e/chestshop create|list|info|stock|price|pause|resume|remove|history"));
            }
        } catch (IllegalArgumentException ex) { plugin.msg(player, Lang.text("chest-shop.text", "&c{0}", ex.getMessage())); }
        catch (Exception ex) { failure(player, ex); }
    }
    public static double price(String raw) {
        try {
            BigDecimal value = new BigDecimal(raw);
            if (value.scale() > 2 || value.compareTo(new BigDecimal("0.01")) < 0 || value.compareTo(new BigDecimal("1000000000")) > 0) throw new NumberFormatException();
            return value.doubleValue();
        } catch (NumberFormatException ex) { throw new IllegalArgumentException(Lang.text("chest-shop.price-must-be-0-01-to-1-000-000-000-with-at-most-two-decimal-plac", "Price must be 0.01 to 1,000,000,000 with at most two decimal places.")); }
    }
    private void create(Player player, Block block, String[] args) throws Exception {create(player,block,args,null);}
    private void create(Player player, Block block, String[] args,ItemStack suppliedSample) throws Exception {
        if (!enabled()) { plugin.msg(player, Lang.text("chest-shop.chest-shops-are-disabled", "&cChest shops are disabled.")); return; }
        if (args.length != 4 || !(args[1].equals("buy") || args[1].equals("sell"))) { plugin.msg(player, Lang.text("chest-shop.chestshop-create", "&e/chestshop create <buy|sell> <amount> <total price>")); return; }
        if (!singleContainer(block)) { plugin.msg(player, Lang.text("chest-shop.look-at-a-chest-double-chest-or-barrel-within-five-blocks", "&cLook at a chest, double chest or barrel within five blocks.")); return; }
        if (isShop(block) || plugin.creator().isCrate(block)) { plugin.msg(player, Lang.text("chest-shop.that-container-already-belongs-to-a-shop-or-crate", "&cThat container already belongs to a shop or crate.")); return; }
        ContainerHandle container = ContainerHandle.of(block);
        if (container.isLocked()) { plugin.msg(player, Lang.text("chest-shop.remove-the-container-s-existing-lock-first", "&cRemove the container's existing lock first.")); return; }
        for(Block part:container.parts()) {
            if(!plugin.platform().owns(part.getLocation()) || isShop(part) || plugin.creator().isCrate(part)) {plugin.msg(player,Lang.text("chest-shop.both-halves-must-be-available-in-your-current-region", "&cBoth halves must be available in your current region."));return;}
            var half=ContainerHandle.of(part);
            if(half.isLocked() || (!player.hasPermission("donsup.admin")&&!player.getUniqueId().toString().equals(blockTags.get(half,placerKey)))) {plugin.msg(player,Lang.text("chest-shop.you-must-own-both-unlocked-halves-of-this-chest", "&cYou must own both unlocked halves of this chest."));return;}
        }
        String placer = blockTags.get(container, placerKey);
        if (!player.getUniqueId().toString().equals(placer) && !player.hasPermission("donsup.admin")) {
            plugin.msg(player, Lang.text("chest-shop.place-a-new-chest-or-barrel-yourself-before-creating-a-shop", "&cPlace a new chest or barrel yourself before creating a shop.")); return;
        }
        if (!container.getInventory().getViewers().isEmpty()) { plugin.msg(player, Lang.text("chest-shop.close-the-container-before-creating-a-shop", "&cClose the container before creating a shop.")); return; }
        int limit = Math.max(1, Math.min(1000, plugin.getConfig().getInt("chest-shops.max-per-player", 20)));
        if (!player.hasPermission("donsup.admin") && store.shops().stream().filter(s -> s.owner().equals(player.getUniqueId())).count() >= limit) {
            plugin.msg(player, Lang.text("chest-shop.you-have-reached-your-chest-shop-limit-of", "&cYou have reached your chest-shop limit of {0}.", limit)); return;
        }
        int amount;
        try { amount = Integer.parseInt(args[2]); } catch (NumberFormatException ex) { throw new IllegalArgumentException(Lang.text("chest-shop.amount-must-be-a-whole-number-from-1-to-2304", "Amount must be a whole number from 1 to 2304.")); }
        if (amount < 1 || amount > 2304) throw new IllegalArgumentException(Lang.text("chest-shop.amount-must-be-a-whole-number-from-1-to-2304", "Amount must be a whole number from 1 to 2304."));
        double price = price(args[3]);
        ItemStack sample = suppliedSample==null?com.donsup.compat.BukkitCompat.hand(player.getInventory()).clone():suppliedSample.clone();
        if (com.donsup.compat.BukkitCompat.air(sample.getType())) { plugin.msg(player, Lang.text("chest-shop.hold-the-exact-item-you-want-this-shop-to-trade-your-sample-is-ke", "&cHold the exact item you want this shop to trade. Your sample is kept.")); return; }
        sample.setAmount(1);
        String id = UUID.randomUUID().toString();
        Shop shop = new Shop(id, player.getUniqueId(), block.getWorld().getUID(), block.getX(), block.getY(), block.getZ(), args[1], sample, amount, price, UUID.randomUUID().toString(), false);
        try {
            store.create(shop);
            store.blocks(id,container.parts().stream().map(this::location).toList());
            for(Block part:container.parts()) {
                var half=ContainerHandle.of(part);blockTags.set(half,shopKey,id);
                if(!half.update(false,false))throw new IllegalArgumentException(Lang.text("chest-shop.the-container-changed-try-again", "The container changed. Try again."));
                locations.put(location(part),id);
            }
        } catch(Exception ex) {
            for(Block part:container.parts()){var half=ContainerHandle.of(part);blockTags.set(half,shopKey,null);half.update(false,false);locations.remove(location(part));}
            store.remove(id);throw ex;
        }
        plugin.msg(player, Lang.text("chest-shop.created-shop-x-for-per-batch", "&aCreated {0} shop: {1}x {2} for {3} per batch.", args[1], amount, sample.getType(), Text.money(price)));
        plugin.msg(player, Lang.text("chest-shop.open-your-chest-normally-to-manage-stock-other-players-get-a-purc", "&7Open your chest normally to manage stock. Other players get a purchase confirmation."));
    }
    private void offer(Player player, Shop shop) {
        ContainerHandle container = available(player, shop);
        if (container == null) return;
        String operation = shop.mode().equals("sell") ? Lang.text("chest-shop.buy", "Buy") : Lang.text("chest-shop.sell", "Sell");
        String itemName = shop.item().hasItemMeta() && shop.item().getItemMeta().hasDisplayName() ? shop.item().getItemMeta().getDisplayName() : Lang.material(shop.item().getType());
        plugin.dialogs().confirmItem(player, Lang.text("chest-shop.at-player-shop", "{0} at Player Shop", operation), shop.item(), Lang.text("chest-shop.x-total-owner-matching-stock-the-price-is-for-the-complete-batch", "{0} {1}x {2}\nTotal: {3}\nOwner: {4}\nMatching stock: {5}\nThe price is for the complete batch. Item properties must match exactly.", operation, shop.amount(), itemName, Text.money(shop.price()), plugin.economy().playerName(shop.owner()), StockTransfer.count(com.donsup.compat.BukkitCompat.storage(container.getInventory()), shop.item())),
                () -> trade(player, shop.id(), shop.revision()));
    }
    private ContainerHandle available(Player player, Shop shop) {
        if (!enabled() || shop.paused()) { plugin.msg(player, Lang.text("chest-shop.this-shop-is-paused", "&cThis shop is paused.")); return null; }
        if (!player.hasPermission("donsup.use") || player.isDead() || player.getUniqueId().equals(shop.owner())) return null;
        if (plugin.travel().tagged(player) || plugin.duels().inDuel(player)) { plugin.msg(player, Lang.text("chest-shop.chest-shop-trading-is-blocked-during-combat-or-a-duel", "&cChest-shop trading is blocked during combat or a duel.")); return null; }
        ContainerHandle container = container(shop);
        if (container == null || !container.getWorld().equals(player.getWorld()) || container.getLocation().add(.5, .5, .5).distanceSquared(player.getLocation()) > 36) {
            plugin.msg(player, Lang.text("chest-shop.stand-close-to-the-original-shop-container", "&cStand close to the original shop container.")); return null;
        }
        if (store.pending(shop.id())) { plugin.msg(player, Lang.text("chest-shop.this-shop-is-awaiting-staff-review-of-an-interrupted-trade", "&cThis shop is awaiting staff review of an interrupted trade.")); return null; }
        if (!container.getInventory().getViewers().isEmpty()) { plugin.msg(player, Lang.text("chest-shop.the-owner-is-managing-stock-try-again-after-they-close-the-contai", "&cThe owner is managing stock. Try again after they close the container.")); return null; }
        return container;
    }
    private void trade(Player player, String id, String revision) {
        try {
            Shop shop = store.shop(id);
            if (shop == null || !revision.equals(shop.revision())) { plugin.msg(player, Lang.text("chest-shop.this-shop-offer-changed-right-click-it-for-a-new-price", "&cThis shop offer changed. Right-click it for a new price.")); return; }
            ContainerHandle container = available(player, shop); if (container == null) return;
            Inventory stock = container.getInventory(); PlayerInventory bag = player.getInventory();
            boolean sell = shop.mode().equals("sell");
            var plan = StockTransfer.plan(sell ? com.donsup.compat.BukkitCompat.storage(stock) : com.donsup.compat.BukkitCompat.storage(bag),
                    sell ? com.donsup.compat.BukkitCompat.storage(bag) : com.donsup.compat.BukkitCompat.storage(stock), shop.item(), shop.amount());
            if (plan.isEmpty()) { plugin.msg(player, Lang.text("chest-shop.not-enough-matching-stock-or-inventory-space-for-the-complete-bat", "&cNot enough matching stock or inventory space for the complete batch.")); return; }
            UUID payer = sell ? player.getUniqueId() : shop.owner(), payee = sell ? shop.owner() : player.getUniqueId();
            if (plugin.economy().money(payer) < shop.price()) { plugin.msg(player, Lang.text("chest-shop.the-paying-account-does-not-have-enough-money", "&cThe paying account does not have enough money.")); return; }
            String transaction = store.prepare(shop, player.getUniqueId(), payer, payee);
            if (!plugin.economy().payShop(transaction, payer, payee, shop.price())) {
                store.finish(transaction, "cancelled"); plugin.msg(player, Lang.text("chest-shop.payment-could-not-be-completed-no-items-were-moved", "&cPayment could not be completed. No items were moved.")); return;
            }
            store.delivering(transaction, com.donsup.compat.BukkitCompat.storage(bag), com.donsup.compat.BukkitCompat.storage(stock),
                    sell ? plan.get().destination() : plan.get().source(), sell ? plan.get().source() : plan.get().destination());
            com.donsup.compat.BukkitCompat.storage(stock, sell ? plan.get().source() : plan.get().destination());
            com.donsup.compat.BukkitCompat.storage(bag, sell ? plan.get().destination() : plan.get().source());
            player.saveData();
            store.finish(transaction, "completed");
            plugin.economy().forgetShopPayment(transaction);
            plugin.msg(player, Lang.text("chest-shop.items-for", "&a{0}{1} items for {2}.", (sell ? Lang.text("chest-shop.bought", "Bought ") : Lang.text("chest-shop.sold", "Sold ")), shop.amount(), Text.money(shop.price())));
            Player owner = Bukkit.getPlayer(shop.owner());
            if (owner != null) plugin.msg(owner, Lang.text("chest-shop.chest-shop-items-for", "&bChest shop: &f{0}{1}{2} items for {3}.", player.getName(), (sell ? Lang.text("chest-shop.bought-5e5f7a", " bought ") : Lang.text("chest-shop.sold-95037f", " sold ")), shop.amount(), Text.money(shop.price())));
        } catch (Exception ex) { failure(player, ex); }
    }
    private void failure(Player player, Exception ex) {
        plugin.getLogger().severe("Chest shop operation failed: " + ex.getMessage());
        plugin.msg(player, Lang.text("chest-shop.the-shop-operation-could-not-finish-staff-can-inspect-chest-shops", "&cThe shop operation could not finish. Staff can inspect chest-shops.yml and any pending shop payment before resolving it."));
    }
    @EventHandler(priority=EventPriority.HIGH,ignoreCancelled=true) public void sign(SignChangeEvent event) {
        Shop attached=at(event.getBlock());
        if(attached!=null&&!owner(event.getPlayer(),attached)){event.setCancelled(true);return;}
        if(!"[shop]".equalsIgnoreCase(event.getLine(0)))return;
        Player p=event.getPlayer();
        if(!p.hasPermission("donsup.use")){event.setCancelled(true);return;}
        try {
            Block block=signContainer(event.getBlock());Shop existing=at(block);
            if(existing!=null){if(!owner(p,existing))throw new IllegalArgumentException(Lang.text("chest-shop.only-the-owner-can-attach-a-shop-sign", "Only the owner can attach a shop sign."));}
            else {
                String[] terms=event.getLine(1).trim().toLowerCase(Locale.ROOT).split("\\s+");
                if(terms.length!=2)throw new IllegalArgumentException(Lang.text("chest-shop.sign-shop-sell-64-or-buy-64-total-price-material-or-blank-for-che", "Sign: [Shop] / sell 64 (or buy 64) / total price / material or blank for chest stock."));
                ContainerHandle container=ContainerHandle.of(block);if(container==null)throw new IllegalArgumentException(Lang.text("chest-shop.attach-the-sign-to-your-chest-or-barrel", "Attach the sign to your chest or barrel."));
                ItemStack sample=null;String material=event.getLine(3).trim();
                if(!material.isEmpty()){Material type=Material.matchMaterial(material);if(type==null||com.donsup.compat.BukkitCompat.air(type))throw new IllegalArgumentException(Lang.text("chest-shop.unknown-item-material", "Unknown item material."));sample=new ItemStack(type);}
                else for(ItemStack stack:container.getInventory().getContents())if(stack!=null&&!com.donsup.compat.BukkitCompat.air(stack.getType())){sample=stack.clone();break;}
                if(sample==null)throw new IllegalArgumentException(Lang.text("chest-shop.put-a-sample-item-in-the-chest-or-write-its-material-on-line-four", "Put a sample item in the chest, or write its material on line four."));
                create(p,block,new String[]{"create",terms[0],terms[1],event.getLine(2).trim()},sample);existing=at(block);
                if(existing==null){event.setCancelled(true);return;}
            }
            event.setLine(0,Text.color(Lang.text("chest-shop.shop", "&b[Shop]")));event.setLine(1,Lang.label("modes",existing.mode(),existing.mode())+" "+existing.amount());event.setLine(2,Text.money(existing.price()));event.setLine(3,Lang.text("chest-shop.right-click", "Right-click"));
        } catch(Exception e){event.setCancelled(true);plugin.msg(p,Lang.text("chest-shop.text", "&c{0}", e.getMessage()));}
    }
    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true) public void interact(PlayerInteractEvent event) {
        if (com.donsup.compat.BukkitCompat.offHand(event) || event.getAction() != Action.RIGHT_CLICK_BLOCK) return;
        Shop shop = at(event.getClickedBlock()); if (shop == null) return;
        if (event.getPlayer().getUniqueId().equals(shop.owner()) || (event.getPlayer().hasPermission("donsup.admin") && event.getPlayer().isSneaking())) {
            if (store.pending(shop.id())) { event.setCancelled(true); plugin.msg(event.getPlayer(), Lang.text("chest-shop.this-shop-needs-staff-review-before-stock-can-change", "&cThis shop needs staff review before stock can change.")); }
            return;
        }
        event.setCancelled(true);
        plugin.platform().player(event.getPlayer(), () -> { if (event.getPlayer().isOnline()) offer(event.getPlayer(), shop); });
    }
    private Shop inventoryShop(Inventory inventory) {
        InventoryHolder holder = inventory.getHolder();
        if (holder instanceof BlockState block) return at(block.getBlock());
        if (holder instanceof DoubleChest chest) {
            if (chest.getLeftSide() instanceof BlockState left && isShop(left.getBlock())) return at(left.getBlock());
            if (chest.getRightSide() instanceof BlockState right) return at(right.getBlock());
        }
        return null;
    }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true) public void open(InventoryOpenEvent event) {
        Shop shop = inventoryShop(event.getInventory()); if (shop == null) return;
        if (!(event.getPlayer() instanceof Player player) || !owner(player, shop) || store.pending(shop.id())) event.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true) public void move(InventoryMoveItemEvent event) {
        if (inventoryShop(event.getSource()) != null || inventoryShop(event.getDestination()) != null) event.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true) public void dispense(BlockDispenseEvent event) {
        if (isShop(event.getBlock().getRelative(com.donsup.compat.BukkitCompat.facing(event.getBlock())))) event.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true) public void breakBlock(BlockBreakEvent event) {
        if(event.getBlock().getState() instanceof Sign){Shop shop=at(event.getBlock());if(shop!=null&&!owner(event.getPlayer(),shop)){event.setCancelled(true);return;}}
        if (isShop(event.getBlock())) { event.setCancelled(true); plugin.msg(event.getPlayer(), Lang.text("chest-shop.remove-this-shop-with-chestshop-remove-before-breaking-its-contai", "&cRemove this shop with /chestshop remove before breaking its container.")); }
    }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true) public void adjacentChest(BlockPlaceEvent event) {
        if (!event.getBlockPlaced().getType().name().equals("CHEST") && !event.getBlockPlaced().getType().name().equals("TRAPPED_CHEST")) return;
        for (BlockFace face : List.of(BlockFace.NORTH, BlockFace.SOUTH, BlockFace.EAST, BlockFace.WEST))
            if (isShop(event.getBlockPlaced().getRelative(face))) { event.setCancelled(true); plugin.msg(event.getPlayer(), Lang.text("chest-shop.leave-a-gap-beside-shop-containers-merging-them-is-blocked", "&cLeave a gap beside shop containers; merging them is blocked.")); return; }
    }
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true) public void placed(BlockPlaceEvent event) {
        blockTags.forget(event.getBlockPlaced());
        if (!singleContainer(event.getBlockPlaced())) return;
        ContainerHandle container = ContainerHandle.of(event.getBlockPlaced());
        blockTags.set(container, placerKey, event.getPlayer().getUniqueId().toString());
        container.update(false, false);
    }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true) public void explode(EntityExplodeEvent event) { event.blockList().removeIf(this::isShop); }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true) public void explode(BlockExplodeEvent event) { event.blockList().removeIf(this::isShop); }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true) public void burn(BlockBurnEvent event) { if (isShop(event.getBlock())) event.setCancelled(true); }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true) public void piston(BlockPistonExtendEvent event) { if (event.getBlocks().stream().anyMatch(this::isShop)) event.setCancelled(true); }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true) public void piston(BlockPistonRetractEvent event) { if (event.getBlocks().stream().anyMatch(this::isShop)) event.setCancelled(true); }
    @EventHandler(priority=EventPriority.MONITOR, ignoreCancelled=true)
    public void forgetBrokenOwner(BlockBreakEvent event) { blockTags.forget(event.getBlock()); }
    @EventHandler(priority=EventPriority.MONITOR, ignoreCancelled=true)
    public void forgetExplodedOwners(EntityExplodeEvent event) { event.blockList().forEach(blockTags::forget); }
    @EventHandler(priority=EventPriority.MONITOR, ignoreCancelled=true)
    public void forgetBlockExplodedOwners(BlockExplodeEvent event) { event.blockList().forEach(blockTags::forget); }

}


===== src/main/java/com/donsup/shop/ChestShopStore.java =====

package com.donsup.shop;

import com.donsup.util.SafeYaml;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.inventory.ItemStack;
import java.io.*;
import java.util.*;
import java.util.function.Consumer;

public final class ChestShopStore {
    public record Shop(String id, UUID owner, UUID world, int x, int y, int z, String mode,
                       ItemStack item, int amount, double price, String revision, boolean paused) {}
    private final File file;
    private YamlConfiguration data;
    public ChestShopStore(File file) { this.file = file; data = SafeYaml.load(file); }
    public Collection<Shop> shops() {
        ConfigurationSection section = data.getConfigurationSection("shops");
        if (section == null) return List.of();
        return section.getKeys(false).stream().map(this::shop).toList();
    }
    public Shop shop(String id) {
        if (id == null || !id.matches("[0-9a-f-]{36}")) return null;
        ConfigurationSection s = data.getConfigurationSection("shops." + id);
        if (s == null) return null;
        return new Shop(id, UUID.fromString(s.getString("owner")), UUID.fromString(s.getString("world")),
                s.getInt("x"), s.getInt("y"), s.getInt("z"), s.getString("mode"), s.getItemStack("item").clone(),
                s.getInt("amount"), s.getDouble("price"), s.getString("revision"), s.getBoolean("paused"));
    }
    public void create(Shop shop) throws IOException {
        update(copy -> {
            String p = "shops." + shop.id();
            copy.set(p + ".owner", shop.owner().toString()); copy.set(p + ".world", shop.world().toString());
            copy.set(p + ".x", shop.x()); copy.set(p + ".y", shop.y()); copy.set(p + ".z", shop.z());
            copy.set(p + ".mode", shop.mode()); copy.set(p + ".item", shop.item()); copy.set(p + ".amount", shop.amount());
            copy.set(p + ".price", shop.price()); copy.set(p + ".revision", shop.revision()); copy.set(p + ".paused", shop.paused());
        });
    }
    public List<String> locations(Shop shop) {
        List<String> saved=data.getStringList("shops."+shop.id()+".blocks");
        return saved.isEmpty()?List.of(shop.world()+":"+shop.x()+":"+shop.y()+":"+shop.z()):saved;
    }
    public void blocks(String id,List<String> locations) throws IOException { update(copy->copy.set("shops."+id+".blocks",locations)); }
    public void edit(String id, double price, boolean paused) throws IOException {
        update(copy -> {
            copy.set("shops." + id + ".price", price); copy.set("shops." + id + ".paused", paused);
            copy.set("shops." + id + ".revision", UUID.randomUUID().toString());
        });
    }
    public void remove(String id) throws IOException { update(copy -> copy.set("shops." + id, null)); }
    public List<Map<String, Object>> history() {
        ConfigurationSection section = data.getConfigurationSection("trades");
        if (section == null) return List.of();
        return section.getKeys(false).stream().map(key -> {
            Map<String, Object> trade = new LinkedHashMap<>(section.getConfigurationSection(key).getValues(false));
            trade.put("id", key); return trade;
        }).toList();
    }
    public boolean pending(String shop) {
        return history().stream().anyMatch(t -> shop.equals(t.get("shop")) && unresolved(t));
    }
    public static boolean unresolved(Map<String, Object> trade) { return Set.of("prepared", "delivering").contains(trade.get("state")); }
    public String prepare(Shop shop, UUID customer, UUID payer, UUID payee) throws IOException {
        String id = UUID.randomUUID().toString();
        update(copy -> {
            copy.createSection("trades." + id, Map.of(
                "shop", shop.id(), "customer", customer.toString(), "owner", shop.owner().toString(),
                "payer", payer.toString(), "payee", payee.toString(), "price", shop.price(),
                "amount", shop.amount(), "time", System.currentTimeMillis(), "state", "prepared"));
            copy.set("trades." + id + ".recovery-version", 1);
        });
        return id;
    }
    public void delivering(String id, ItemStack[] customerBefore, ItemStack[] stockBefore,
                           ItemStack[] customerAfter, ItemStack[] stockAfter) throws IOException {
        if (!"prepared".equals(data.getString("trades." + id + ".state"))) throw new IllegalStateException("Trade is not prepared");
        update(copy -> {
            String path = "trades." + id;
            copy.set(path + ".state", "delivering");
            copy.set(path + ".customer-before", Arrays.asList(customerBefore)); copy.set(path + ".stock-before", Arrays.asList(stockBefore));
            copy.set(path + ".customer-after", Arrays.asList(customerAfter)); copy.set(path + ".stock-after", Arrays.asList(stockAfter));
        });
    }
    public void finish(String id, String state) throws IOException {
        update(copy -> {
            copy.set("trades." + id + ".state", state);
            for (String snapshot : List.of("customer-before", "stock-before", "customer-after", "stock-after"))
                copy.set("trades." + id + "." + snapshot, null);
            // Keep every unresolved record and the newest 500 completed records.
            var section = copy.getConfigurationSection("trades");
            if (section == null) return;
            List<String> done = section.getKeys(false).stream().filter(key -> !Set.of("prepared", "delivering").contains(section.getString(key + ".state")))
                    .sorted(Comparator.comparingLong(key -> section.getLong(key + ".time"))).toList();
            for (int i = 0; i < done.size() - 500; i++) copy.set("trades." + done.get(i), null);
        });
    }
    private void update(Consumer<YamlConfiguration> mutation) throws IOException {
        YamlConfiguration next = new YamlConfiguration();
        try { next.loadFromString(data.saveToString()); }
        catch (Exception ex) { throw new IOException("Cannot snapshot chest shop data", ex); }
        mutation.accept(next); SafeYaml.save(next, file); data = next;
    }
}


===== src/main/java/com/donsup/shop/ShopHolograms.java =====

package com.donsup.shop;

import com.donsup.config.Lang;
import com.donsup.DonsupPlugin;
import com.donsup.compat.BukkitCompat;
import com.donsup.platform.TaskHandle;
import com.donsup.util.Text;
import org.bukkit.*;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.player.PlayerInteractEntityEvent;
import org.bukkit.event.world.ChunkUnloadEvent;
import java.util.*;
import java.util.function.Supplier;

/** One nonpersistent label per loaded shop. Never loads chunks just for decoration. */
public final class ShopHolograms implements Listener {
    private final DonsupPlugin plugin;
    private final Supplier<Collection<ChestShopStore.Shop>> shops;
    private final Map<String,ArmorStand> labels=new HashMap<>();
    private final Set<UUID> entities=new HashSet<>();
    private final Map<String,Location> positions=new HashMap<>();
    private final TaskHandle timer;
    public ShopHolograms(DonsupPlugin plugin,Supplier<Collection<ChestShopStore.Shop>> shops){
        this.plugin=plugin;this.shops=shops;timer=plugin.platform().globalTimer(this::refresh,20,100);
    }
    private void refresh(){
        var current=shops.get();var ids=new HashSet<String>();current.forEach(s->ids.add(s.id()));
        for(String id:new ArrayList<>(labels.keySet()))if(!ids.contains(id)||!plugin.getConfig().getBoolean("chest-shops.holograms",true))remove(id);
        if(!plugin.getConfig().getBoolean("chest-shops.holograms",true)||!BukkitCompat.method(Entity.class,"setPersistent",boolean.class))return;
        for(var shop:current){World world=Bukkit.getWorld(shop.world());if(world==null||!world.isChunkLoaded(shop.x()>>4,shop.z()>>4))continue;
            Location at=new Location(world,shop.x()+.5,shop.y()+1.25,shop.z()+.5);
            plugin.platform().region(at,()->{
                if(!world.isChunkLoaded(shop.x()>>4,shop.z()>>4)||!shops.get().stream().anyMatch(s->s.id().equals(shop.id())))return;
                ArmorStand label=labels.get(shop.id());
                if(label==null||label.isDead()){
                    label=world.spawn(at,ArmorStand.class);label.setVisible(false);label.setGravity(false);label.setSmall(true);label.setBasePlate(false);
                    if(BukkitCompat.method(label.getClass(),"setMarker",boolean.class))BukkitCompat.call(label,"setMarker",new Class<?>[]{boolean.class},true);
                    BukkitCompat.call(label,"setPersistent",new Class<?>[]{boolean.class},false);
                    label.setCustomNameVisible(true);labels.put(shop.id(),label);positions.put(shop.id(),at);entities.add(label.getUniqueId());
                }
                label.setCustomName(Text.color(Lang.text("shop-holograms.x", "{0} {1}x {2} &a{3}", (shop.paused()?Lang.text("shop-holograms.paused", "&7[Paused] "):Lang.text("shop-holograms.text", "&e"))+Lang.label("modes",shop.mode(),shop.mode().toUpperCase(Locale.ROOT)), shop.amount(), shop.item().getType(), Text.money(shop.price()))));
            });
        }
    }
    private void remove(String id){ArmorStand entity=labels.remove(id);positions.remove(id);if(entity==null)return;entities.remove(entity.getUniqueId());if(plugin.platform().owns(entity))entity.remove();else plugin.platform().entity(entity,entity::remove);}
    @EventHandler(priority=EventPriority.HIGHEST)public void damage(EntityDamageEvent e){if(entities.contains(e.getEntity().getUniqueId()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST)public void interact(PlayerInteractEntityEvent e){if(entities.contains(e.getRightClicked().getUniqueId()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)public void unload(ChunkUnloadEvent e){for(var entry:new ArrayList<>(positions.entrySet())){var loc=entry.getValue();if(loc.getWorld().equals(e.getWorld())&&(loc.getBlockX()>>4)==e.getChunk().getX()&&(loc.getBlockZ()>>4)==e.getChunk().getZ())remove(entry.getKey());}}
    public void shutdown(){timer.cancel();for(String id:new ArrayList<>(labels.keySet()))remove(id);}
}


===== src/main/java/com/donsup/shop/StockTransfer.java =====

package com.donsup.shop;

import org.bukkit.inventory.ItemStack;
import java.util.Optional;

/** Plan a whole exact-item transfer without changing either inventory. */
public final class StockTransfer {
    public record Plan(ItemStack[] source, ItemStack[] destination) {}
    public static Optional<Plan> plan(ItemStack[] source, ItemStack[] destination, ItemStack template, int amount) {
        if (template == null || com.donsup.compat.BukkitCompat.air(template.getType()) || amount < 1 || amount > 2304) return Optional.empty();
        ItemStack[] from = copy(source), to = copy(destination);
        int needed = amount;
        for (int i = 0; i < from.length && needed > 0; i++) {
            ItemStack item = from[i];
            if (item == null || !item.isSimilar(template)) continue;
            int count = Math.min(needed, item.getAmount()); needed -= count;
            item.setAmount(item.getAmount() - count);
            if (item.getAmount() == 0) from[i] = null;
        }
        if (needed > 0) return Optional.empty();
        int left = amount;
        for (ItemStack item : to) {
            if (item == null || !item.isSimilar(template)) continue;
            int add = Math.min(left, Math.max(0, template.getMaxStackSize() - item.getAmount()));
            item.setAmount(item.getAmount() + add); left -= add;
        }
        for (int i = 0; i < to.length && left > 0; i++) {
            if (to[i] != null && !com.donsup.compat.BukkitCompat.air(to[i].getType())) continue;
            int add = Math.min(left, template.getMaxStackSize());
            to[i] = template.clone(); to[i].setAmount(add); left -= add;
        }
        return left == 0 ? Optional.of(new Plan(from, to)) : Optional.empty();
    }
    public static ItemStack[] copy(ItemStack[] contents) {
        ItemStack[] copy = new ItemStack[contents.length];
        for (int i = 0; i < contents.length; i++) copy[i] = contents[i] == null ? null : contents[i].clone();
        return copy;
    }
    public static int count(ItemStack[] contents, ItemStack template) {
        int count = 0;
        for (ItemStack item : contents) if (item != null && item.isSimilar(template)) count += item.getAmount();
        return count;
    }
}


===== src/main/java/com/donsup/social/SocialManager.java =====

package com.donsup.social;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.ItemUtil;
import com.donsup.util.Text;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.OfflinePlayer;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryCloseEvent;
import org.bukkit.event.player.AsyncPlayerChatEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.Map;
import java.util.HashMap;

public class SocialManager implements Listener {
    private final Map<String, UUID> vaultUsers = new HashMap<>();
    private static final String TEAM_TITLE = "SMP | Teams";
    private static final String WARP_TITLE = "SMP | Player Warps";
    private final DonsupPlugin plugin;
    private final ItemKey actionKey;
    private final File file;
    private FileConfiguration data;
    private final java.util.Set<UUID> teamPlayers = java.util.concurrent.ConcurrentHashMap.newKeySet();

    public SocialManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.actionKey = new ItemKey(plugin, "social_action");
        this.file = new File(plugin.getDataFolder(), "social.yml");
        reload();
    }

    public void reload() {
        data = com.donsup.util.SafeYaml.load(file);
        teamPlayers.clear();
        ConfigurationSection players = data.getConfigurationSection("players");
        if (players != null) for (String id : players.getKeys(false)) {
            try { teamPlayers.add(UUID.fromString(id)); } catch (IllegalArgumentException ignored) { }
        }
    }

    public void save() {
        try {
            com.donsup.util.SafeYaml.save(data, file);
        } catch (IOException ex) {
            plugin.getLogger().warning("Could not save social.yml: " + ex.getMessage());
        }
    }

    public void openTeams(Player player) {
        Inventory inv = plugin.inventory(54, TEAM_TITLE, false);
        fill(inv);
        String team = teamOf(player.getUniqueId());
        inv.setItem(4, button(com.donsup.compat.Materials.SHIELD, Lang.text("social.teams-clans", "&b&lTeams / Clans"), List.of(
                Lang.text("social.team", "&7Team: &f{0}", (team == null ? Lang.text("social.none", "None") : team)),
                Lang.text("social.use-team-create-to-start", "&7Use &f/team create <name> &7to start.")
        ), "NONE"));
        if (team != null) {
            inv.setItem(20, button(Material.ENDER_CHEST, Lang.text("social.team-vault", "&dTeam Vault"), List.of(Lang.text("social.shared-team-storage", "&7Shared team storage.")), "TEAM:VAULT"));
            inv.setItem(21, button(com.donsup.compat.Materials.RED_BED, Lang.text("social.team-home", "&cTeam Home"), List.of(Lang.text("social.left-teleport", "&7Left: teleport"), Lang.text("social.set-team-sethome", "&7Set: /team sethome")), "TEAM:HOME"));
            inv.setItem(22, button(Material.GOLD_INGOT, Lang.text("social.team-bank", "&6Team Bank"), List.of(Lang.text("social.balance", "&7Balance: &a{0}", Text.money(data.getDouble("teams." + team + ".bank", 0))), Lang.text("social.team-bank-deposit", "&7/team bank deposit <amount>")), "NONE"));
            boolean ff = data.getBoolean("teams." + team + ".friendly-fire", false);
            inv.setItem(23, button(ff ? Material.LAVA_BUCKET : Material.WATER_BUCKET, Lang.text("social.friendly-fire", "&eFriendly Fire"), List.of(Lang.text("social.current", "&7Current: {0}", (ff ? Lang.text("social.on", "&cOn") : Lang.text("social.off", "&aOff"))), Lang.text("social.leader-team-friendlyfire", "&7Leader: /team friendlyfire")), "NONE"));
            inv.setItem(24, button(com.donsup.compat.Materials.OAK_SIGN, Lang.text("social.members", "&fMembers"), memberLore(team), "NONE"));
        } else {
            inv.setItem(22, button(com.donsup.compat.Materials.WRITABLE_BOOK, Lang.text("social.create-a-team", "&aCreate A Team"), List.of(Lang.text("social.use-team-create", "&7Use &f/team create <name>&7.")), "NONE"));
        }
        player.openInventory(inv);
    }

    public void openWarps(Player player) {
        Inventory inv = plugin.inventory(54, WARP_TITLE, false);
        fill(inv);
        inv.setItem(4, button(Material.ENDER_PEARL, Lang.text("social.player-warps", "&b&lPlayer Warps"), List.of(
                Lang.text("social.create-shops-farms-casinos-and-bases", "&7Create shops, farms, casinos and bases."),
                Lang.text("social.use-pwarp-set", "&7Use &f/pwarp set <name>&7.")
        ), "NONE"));
        List<String> warps = warps();
        warps.sort((a, b) -> Boolean.compare(data.getBoolean("warps." + b + ".promoted", false), data.getBoolean("warps." + a + ".promoted", false)));
        int slot = 10;
        for (String warp : warps) {
            if (slot >= 45) break;
            boolean promoted = data.getBoolean("warps." + warp + ".promoted", false);
            inv.setItem(slot++, button(promoted ? Material.NETHER_STAR : Material.ENDER_PEARL, (promoted ? Lang.text("social.text", "&e★ ") : Lang.text("social.text-a7f0cc", "&f")) + warp, List.of(
                    Lang.text("social.owner", "&7Owner: &f{0}", data.getString("warps." + warp + ".owner-name", Lang.text("social.unknown", "Unknown"))),
                    Lang.text("social.visits", "&7Visits: &e{0}", data.getInt("warps." + warp + ".visits", 0)),
                    Lang.text("social.click-to-teleport", "&aClick to teleport.")
            ), "PWARP:" + warp));
        }
        player.openInventory(inv);
    }

    public void team(Player player, String[] args) {
        if (args.length == 0) {
            openTeams(player);
            return;
        }
        switch (args[0].toLowerCase()) {
            case "create" -> {
                if (args.length < 2) { plugin.msg(player, Lang.text("social.usage-team-create", "&eUsage: /team create <name>")); return; }
                createTeam(player, args[1]);
            }
            case "invite" -> invite(player, args.length >= 2 ? Bukkit.getPlayerExact(args[1]) : null);
            case "join" -> join(player, args.length >= 2 ? args[1] : "");
            case "leave" -> leave(player);
            case "chat", "c" -> teamChat(player, joinArgs(args, 1));
            case "sethome" -> setHome(player);
            case "home" -> home(player);
            case "vault" -> openVault(player);
            case "friendlyfire" -> toggleFriendlyFire(player);
            case "bank" -> bank(player, args);
            default -> openTeams(player);
        }
    }

    public void pwarp(Player player, String[] args) {
        if (args.length == 0) {
            openWarps(player);
            return;
        }
        switch (args[0].toLowerCase()) {
            case "set" -> {
                if (args.length < 2) { plugin.msg(player, Lang.text("social.usage-pwarp-set", "&eUsage: /pwarp set <name>")); return; }
                setWarp(player, args[1]);
            }
            case "delete", "del" -> {
                if (args.length < 2) { plugin.msg(player, Lang.text("social.usage-pwarp-delete", "&eUsage: /pwarp delete <name>")); return; }
                deleteWarp(player, args[1]);
            }
            case "promote" -> {
                if (args.length < 2) { plugin.msg(player, Lang.text("social.usage-pwarp-promote", "&eUsage: /pwarp promote <name>")); return; }
                promoteWarp(player, args[1]);
            }
            default -> teleportWarp(player, args[0]);
        }
    }

    private void createTeam(Player player, String name) {
        name = clean(name);
        if (name.isBlank() || name.length() > 32) { plugin.msg(player, Lang.text("social.use-a-team-name-of-1-32-letters-numbers-underscores-or-hyphens", "&cUse a team name of 1-32 letters, numbers, underscores or hyphens.")); return; }
        if (teamOf(player.getUniqueId()) != null) { plugin.msg(player, Lang.text("social.leave-your-current-team-first", "&cLeave your current team first.")); return; }
        if (data.contains("teams." + name)) { plugin.msg(player, Lang.text("social.that-team-already-exists", "&cThat team already exists.")); return; }
        data.set("teams." + name + ".leader", player.getUniqueId().toString());
        data.set("teams." + name + ".members." + player.getUniqueId(), player.getName());
        data.set("players." + player.getUniqueId(), name);
        teamPlayers.add(player.getUniqueId());
        save();
        plugin.msg(player, Lang.text("social.created-team", "&aCreated team &e{0}&a.", name));
    }

    private void invite(Player player, Player target) {
        String team = teamOf(player.getUniqueId());
        if (team == null || target == null) { plugin.msg(player, Lang.text("social.invalid-team-or-player", "&cInvalid team or player.")); return; }
        if (!leader(player, team)) { plugin.msg(player, Lang.text("social.only-the-leader-can-invite", "&cOnly the leader can invite.")); return; }
        data.set("invites." + target.getUniqueId(), team);
        save();
        plugin.msg(player, Lang.text("social.invited", "&aInvited &e{0}&a.", target.getName()));
        plugin.msg(target, Lang.text("social.invited-you-to-team-use-team-join", "&e{0} &ainvited you to team &e{1}&a. Use &f/team join {2}&a.", player.getName(), team, team));
    }

    private void join(Player player, String team) {
        team = clean(team);
        if (teamOf(player.getUniqueId()) != null) { plugin.msg(player, Lang.text("social.leave-your-current-team-first", "&cLeave your current team first.")); return; }
        if (team.isBlank() || !data.contains("teams." + team)) { plugin.msg(player, Lang.text("social.team-not-found", "&cTeam not found.")); return; }
        if (!team.equals(data.getString("invites." + player.getUniqueId()))) { plugin.msg(player, Lang.text("social.no-invite-for-that-team", "&cNo invite for that team.")); return; }
        data.set("teams." + team + ".members." + player.getUniqueId(), player.getName());
        data.set("players." + player.getUniqueId(), team);
        teamPlayers.add(player.getUniqueId());
        data.set("invites." + player.getUniqueId(), null);
        save();
        plugin.msg(player, Lang.text("social.joined-team", "&aJoined team &e{0}&a.", team));
    }

    private void leave(Player player) {
        String team = teamOf(player.getUniqueId());
        if (team == null) { plugin.msg(player, Lang.text("social.you-are-not-in-a-team", "&cYou are not in a team.")); return; }
        if (leader(player, team)) { plugin.msg(player, Lang.text("social.leader-cannot-leave-delete-reassign-is-reserved-for-admin-cleanup", "&cLeader cannot leave. Delete/reassign is reserved for admin cleanup.")); return; }
        if (com.donsup.gui.OwnedInventory.title(player.getOpenInventory()).equals(TEAM_TITLE + " Vault " + team)) player.closeInventory();
        data.set("teams." + team + ".members." + player.getUniqueId(), null);
        data.set("players." + player.getUniqueId(), null);
        teamPlayers.remove(player.getUniqueId());
        save();
        plugin.msg(player, Lang.text("social.left-team", "&cLeft team &e{0}&c.", team));
    }

    private void teamChat(Player player, String message) {
        String team = teamOf(player.getUniqueId());
        if (team == null || message.isBlank()) { plugin.msg(player, Lang.text("social.usage-team-chat", "&eUsage: /team chat <message>")); return; }
        for (UUID uuid : members(team)) {
            Player online = Bukkit.getPlayer(uuid);
            if (online != null) plugin.msg(online, Lang.text("social.team-37bbcb", "&b[Team] &e{0}&7: &f{1}", player.getName(), message));
        }
    }

    private void setHome(Player player) {
        String team = teamOf(player.getUniqueId());
        if (team == null) { plugin.msg(player, Lang.text("social.you-are-not-in-a-team", "&cYou are not in a team.")); return; }
        writeLocation("teams." + team + ".home", player.getLocation());
        save();
        plugin.msg(player, Lang.text("social.set-team-home", "&aSet team home."));
    }

    private void home(Player player) {
        String team = teamOf(player.getUniqueId());
        Location loc = team == null ? null : readLocation("teams." + team + ".home");
        if (loc == null) { plugin.msg(player, Lang.text("social.no-team-home-set", "&cNo team home set.")); return; }
        plugin.travel().teleport(player, loc);
    }

    private void openVault(Player player) {
        String team = teamOf(player.getUniqueId());
        if (team == null) { plugin.msg(player, Lang.text("social.you-are-not-in-a-team", "&cYou are not in a team.")); return; }
        if (plugin.platform().folia()) {
            UUID viewer = vaultUsers.get(team);
            if (viewer != null && !viewer.equals(player.getUniqueId())) {
                plugin.msg(player, Lang.text("social.a-teammate-is-using-this-vault-try-again-when-they-close-it", "&eA teammate is using this vault. Try again when they close it.")); return;
            }
        }
        for (Player online : Bukkit.getOnlinePlayers()) {
            if (plugin.platform().folia()) break;
            var view = online.getOpenInventory();
            if (com.donsup.compat.Views.top(view).getHolder() instanceof com.donsup.gui.OwnedInventory && com.donsup.gui.OwnedInventory.title(view).equals(TEAM_TITLE + " Vault " + team)) {
                player.openInventory(com.donsup.compat.Views.top(view)); return;
            }
        }
        Inventory inv = plugin.inventory(54, TEAM_TITLE + " Vault " + team, true);
        List<?> stored = data.getList("teams." + team + ".vault", List.of());
        for (int i = 0; i < Math.min(stored.size(), inv.getSize()); i++) {
            if (stored.get(i) instanceof ItemStack item) inv.setItem(i, item);
        }
        player.openInventory(inv);
        if (plugin.platform().folia()) vaultUsers.put(team,player.getUniqueId());
    }

    private void toggleFriendlyFire(Player player) {
        String team = teamOf(player.getUniqueId());
        if (team == null || !leader(player, team)) { plugin.msg(player, Lang.text("social.only-the-leader-can-change-friendly-fire", "&cOnly the leader can change friendly fire.")); return; }
        boolean next = !data.getBoolean("teams." + team + ".friendly-fire", false);
        data.set("teams." + team + ".friendly-fire", next);
        save();
        plugin.msg(player, Lang.text("social.friendly-fire-is-now", "&eFriendly fire is now {0}&e.", (next ? Lang.text("social.on-b38b7b", "&cON") : Lang.text("social.off-f37a84", "&aOFF"))));
    }

    private void bank(Player player, String[] args) {
        String team = teamOf(player.getUniqueId());
        if (team == null || args.length < 3) { plugin.msg(player, Lang.text("social.usage-team-bank", "&eUsage: /team bank <deposit|withdraw> <amount>")); return; }
        double amount = parse(args[2]);
        if (!Double.isFinite(amount) || amount <= 0 || amount > 1.0e12) { plugin.msg(player, Lang.text("social.enter-a-positive-finite-amount-up-to-1-trillion", "&cEnter a positive, finite amount up to 1 trillion.")); return; }
        String path = "teams." + team + ".bank";
        if (args[1].equalsIgnoreCase("deposit")) {
            if (!plugin.economy().withdraw(player.getUniqueId(), amount)) { plugin.msg(player, Lang.text("social.not-enough-money", "&cNot enough money.")); return; }
            data.set(path, data.getDouble(path, 0) + amount);
        } else if (args[1].equalsIgnoreCase("withdraw")) {
            if (!leader(player, team)) { plugin.msg(player, Lang.text("social.only-the-leader-can-withdraw", "&cOnly the leader can withdraw.")); return; }
            if (data.getDouble(path, 0) < amount) { plugin.msg(player, Lang.text("social.team-bank-is-too-low", "&cTeam bank is too low.")); return; }
            data.set(path, data.getDouble(path, 0) - amount);
            plugin.economy().deposit(player.getUniqueId(), amount);
        }
        save();
        plugin.msg(player, Lang.text("social.team-bank-60b390", "&aTeam bank: &e{0}&a.", Text.money(data.getDouble(path, 0))));
    }

    private void setWarp(Player player, String name) {
        name = clean(name);
        if (name.isBlank() || name.length() > 32) { plugin.msg(player, Lang.text("social.use-a-warp-name-of-1-32-letters-numbers-underscores-or-hyphens", "&cUse a warp name of 1-32 letters, numbers, underscores or hyphens.")); return; }
        if (data.contains("warps." + name) && !ownsWarp(player, name)) { plugin.msg(player, Lang.text("social.you-do-not-own-that-warp", "&cYou do not own that warp.")); return; }
        writeLocation("warps." + name + ".location", player.getLocation());
        data.set("warps." + name + ".owner", player.getUniqueId().toString());
        data.set("warps." + name + ".owner-name", player.getName());
        save();
        plugin.msg(player, Lang.text("social.set-player-warp", "&aSet player warp &e{0}&a.", name));
    }

    private void deleteWarp(Player player, String name) {
        name = clean(name);
        if (!ownsWarp(player, name) && !player.hasPermission("donsup.admin")) { plugin.msg(player, Lang.text("social.you-do-not-own-that-warp", "&cYou do not own that warp.")); return; }
        data.set("warps." + name, null);
        save();
        plugin.msg(player, Lang.text("social.deleted-player-warp", "&cDeleted player warp &e{0}&c.", name));
    }

    private void promoteWarp(Player player, String name) {
        name = clean(name);
        if (!ownsWarp(player, name)) { plugin.msg(player, Lang.text("social.you-do-not-own-that-warp", "&cYou do not own that warp.")); return; }
        if (data.getBoolean("warps." + name + ".promoted", false)) { plugin.msg(player, Lang.text("social.that-warp-is-already-promoted", "&eThat warp is already promoted.")); return; }
        double cost = plugin.getConfig().getDouble("player-warps.promote-cost", 2500);
        if (!plugin.economy().withdraw(player.getUniqueId(), cost)) { plugin.msg(player, Lang.text("social.promotion-costs", "&cPromotion costs &e{0}&c.", Text.money(cost))); return; }
        data.set("warps." + name + ".promoted", true);
        save();
        plugin.msg(player, Lang.text("social.promoted-warp", "&aPromoted warp &e{0}&a.", name));
    }

    private void teleportWarp(Player player, String name) {
        name = clean(name);
        Location loc = readLocation("warps." + name + ".location");
        if (loc == null) { plugin.msg(player, Lang.text("social.warp-not-found", "&cWarp not found.")); return; }
        String key = "warps." + name;
        plugin.travel().teleport(player, loc, () -> {
            if (data.contains(key)) { data.set(key + ".visits", data.getInt(key + ".visits", 0) + 1); save(); }
        });
    }

    @EventHandler
    public void onDamage(EntityDamageByEntityEvent event) {
        if (!(event.getEntity() instanceof Player victim) || !(com.donsup.compat.BukkitCompat.attacker(event) instanceof Player attacker)) return;
        if (plugin.duels().opponents(attacker, victim)) return;
        String a = teamOf(attacker.getUniqueId());
        String b = teamOf(victim.getUniqueId());
        if (a != null && a.equals(b) && !data.getBoolean("teams." + a + ".friendly-fire", false)) {
            event.setCancelled(true);
            plugin.msg(attacker, Lang.text("social.friendly-fire-is-disabled-for-your-team", "&cFriendly fire is disabled for your team."));
        }
    }

    @EventHandler(priority = org.bukkit.event.EventPriority.HIGH, ignoreCancelled = true)
    public void onChat(AsyncPlayerChatEvent event) {
        String message = event.getMessage();
        if (!message.startsWith("!")) return;
        if (!teamPlayers.contains(event.getPlayer().getUniqueId())) return;
        event.setCancelled(true);
        plugin.platform().player(event.getPlayer(), () -> teamChat(event.getPlayer(), message.substring(1)));
    }

    @EventHandler
    public void onClick(InventoryClickEvent event) {
        if (!com.donsup.gui.OwnedInventory.buttonClick(event)) return;
        if (!(event.getWhoClicked() instanceof Player player)) return;
        String title = com.donsup.gui.OwnedInventory.title(event.getView());
        if (!title.equals(TEAM_TITLE) && !title.equals(WARP_TITLE)) return;
        event.setCancelled(true);
        ItemStack item = event.getCurrentItem();
        if (item == null || !item.hasItemMeta()) return;
        String action = com.donsup.compat.ItemTags.getString(item.getItemMeta(), actionKey);
        if (action == null) return;
        if (action.equals("TEAM:VAULT")) openVault(player);
        else if (action.equals("TEAM:HOME")) home(player);
        else if (action.startsWith("PWARP:")) teleportWarp(player, action.substring(6));
    }

    @EventHandler
    public void onClose(InventoryCloseEvent event) {
        if (!(event.getInventory().getHolder() instanceof com.donsup.gui.OwnedInventory)) return;
        String title = com.donsup.gui.OwnedInventory.title(event.getView());
        if (!title.startsWith(TEAM_TITLE + " Vault ")) return;
        String team = title.substring((TEAM_TITLE + " Vault ").length());
        vaultUsers.remove(team,event.getPlayer().getUniqueId());
        data.set("teams." + team + ".vault", java.util.Arrays.asList(event.getInventory().getContents()));
        save();
    }

    private String teamOf(UUID uuid) { return data.getString("players." + uuid); }
    private boolean leader(Player player, String team) { return player.getUniqueId().toString().equals(data.getString("teams." + team + ".leader")); }
    private boolean ownsWarp(Player player, String warp) { return player.getUniqueId().toString().equals(data.getString("warps." + warp + ".owner")); }

    private List<UUID> members(String team) {
        List<UUID> out = new ArrayList<>();
        ConfigurationSection section = data.getConfigurationSection("teams." + team + ".members");
        if (section != null) for (String key : section.getKeys(false)) try { out.add(UUID.fromString(key)); } catch (IllegalArgumentException ignored) {}
        return out;
    }

    private List<String> memberLore(String team) {
        List<String> lore = new ArrayList<>();
        for (UUID uuid : members(team)) lore.add("&7- &f" + data.getString("teams." + team + ".members." + uuid, uuid.toString().substring(0, 8)));
        return lore;
    }

    private List<String> warps() {
        ConfigurationSection section = data.getConfigurationSection("warps");
        return section == null ? new ArrayList<>() : new ArrayList<>(section.getKeys(false));
    }

    private void writeLocation(String path, Location loc) {
        data.set(path + ".world", loc.getWorld().getName());
        data.set(path + ".x", loc.getX());
        data.set(path + ".y", loc.getY());
        data.set(path + ".z", loc.getZ());
        data.set(path + ".yaw", loc.getYaw());
        data.set(path + ".pitch", loc.getPitch());
    }

    private Location readLocation(String path) {
        String world = data.getString(path + ".world");
        if (world == null || Bukkit.getWorld(world) == null) return null;
        return new Location(Bukkit.getWorld(world), data.getDouble(path + ".x"), data.getDouble(path + ".y"), data.getDouble(path + ".z"), (float) data.getDouble(path + ".yaw"), (float) data.getDouble(path + ".pitch"));
    }

    private void fill(Inventory inv) {
        ItemStack glass = button(com.donsup.compat.Materials.GRAY_STAINED_GLASS_PANE, " ", List.of(), "NONE");
        for (int i = 0; i < inv.getSize(); i++) inv.setItem(i, glass);
    }

    private ItemStack button(Material material, String name, List<String> lore, String action) {
        return plugin.button(material, name, lore, actionKey, action);
    }

    private String clean(String input) { return input == null ? "default" : input.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9_-]", ""); }
    private String joinArgs(String[] args, int start) { return String.join(" ", java.util.Arrays.copyOfRange(args, start, args.length)); }
    private double parse(String input) { try { return Double.parseDouble(input); } catch (Exception ex) { return -1; } }
}


===== src/main/java/com/donsup/spawner/CustomSpawnerManager.java =====

package com.donsup.spawner;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.ItemUtil;
import com.donsup.util.Text;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.block.Block;
import org.bukkit.block.CreatureSpawner;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.EntityType;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.io.File;
import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public class CustomSpawnerManager implements Listener {
    private static final String TITLE = "SMP | Spawners";
    private static final String BLOCK_TITLE = "SMP | Spawner";
    private final DonsupPlugin plugin;
    private final ItemKey itemTypeKey;
    private final ItemKey actionKey;
    private final File file;
    private FileConfiguration data;

    public CustomSpawnerManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.itemTypeKey = new ItemKey(plugin, "custom_spawner_type");
        this.actionKey = new ItemKey(plugin, "spawner_action");
        this.file = new File(plugin.getDataFolder(), "spawners.yml");
        reload();
    }

    public void reload() {
        this.data = com.donsup.util.SafeYaml.load(file);
    }

    public void save() {
        try {
            com.donsup.util.SafeYaml.save(data, file);
        } catch (IOException ex) {
            plugin.getLogger().warning("Could not save spawners.yml: " + ex.getMessage());
        }
    }

    public ItemStack spawnerItem(String type, int amount) {
        type = normalize(type);
        Material icon = com.donsup.compat.Materials.SPAWNER;
        String name = plugin.getConfig().getString("custom-spawners.types." + type + ".name", Lang.text("custom-spawner.spawner", "&d{0} Spawner", title(type)));
        ItemStack item = ItemUtil.named(icon, Math.max(1, amount), name, List.of(
                Lang.text("custom-spawner.virtual-drop-generator-no-mobs-spawn", "&7Virtual drop generator. No mobs spawn."),
                Lang.text("custom-spawner.right-click-placed-spawner-to-open-storage", "&7Right-click placed spawner to open storage."),
                Lang.text("custom-spawner.shift-right-click-same-type-to-stack", "&7Shift-right-click same type to stack."),
                Lang.text("custom-spawner.type", "&8Type: {0}", type)
        ));
        ItemMeta meta = item.getItemMeta();
        com.donsup.compat.ItemTags.setString(meta, itemTypeKey, type);
        item.setItemMeta(meta);
        return item;
    }

    public void openShop(Player player) {
        Inventory inv = plugin.inventory(54, TITLE, false);
        fill(inv);
        int price = plugin.getConfig().getInt("custom-spawners.price-shards", 1500);
        inv.setItem(4, button(com.donsup.compat.Materials.SPAWNER, Lang.text("custom-spawner.virtual-spawners", "&d&lVirtual Spawners"), List.of(
                Lang.text("custom-spawner.competitive-smp-virtual-drop-generators", "&7Competitive SMP virtual drop generators."),
                Lang.text("custom-spawner.they-do-not-spawn-live-mobs", "&7They do not spawn live mobs."),
                Lang.text("custom-spawner.right-click-placed-spawners-for-storage", "&7Right-click placed spawners for storage."),
                Lang.text("custom-spawner.price-shards-each", "&7Price: &d{0} shards each", price),
                Lang.text("custom-spawner.your-shards", "&7Your shards: &d{0}", plugin.economy().shards(player.getUniqueId()))
        ), "BALANCE"));
        ConfigurationSection section = plugin.getConfig().getConfigurationSection("custom-spawners.types");
        int[] slots = {10, 11, 12, 13, 14, 15, 16, 28, 29, 30, 31, 32, 33, 34};
        int index = 0;
        if (section != null) {
            for (String type : section.getKeys(false)) {
                if (index >= slots.length) {
                    break;
                }
                Material icon = ItemUtil.material(section.getString(type + ".icon"), com.donsup.compat.Materials.SPAWNER);
                inv.setItem(slots[index++], button(icon, section.getString(type + ".name", "&d" + title(type)), List.of(
                        Lang.text("custom-spawner.cost-shards", "&7Cost: &d{0} shards", price),
                        Lang.text("custom-spawner.produces", "&7Produces: &f{0}", dropsSummary(type)),
                        Lang.text("custom-spawner.mode-virtual-storage", "&7Mode: &bvirtual storage"),
                        Lang.text("custom-spawner.click-to-buy", "&aClick to buy")
                ), "BUY:" + type));
            }
        }
        inv.setItem(49, button(Material.ARROW, Lang.text("custom-spawner.back", "&7Back"), List.of(), "CLOSE"));
        player.openInventory(inv);
    }

    @EventHandler(priority = org.bukkit.event.EventPriority.HIGHEST, ignoreCancelled = true)
    public void onPlace(BlockPlaceEvent event) {
        ItemStack item = event.getItemInHand();
        String type = spawnerType(item);
        if (type == null) {
            return;
        }
        Block block = event.getBlockPlaced();
        block.setType(com.donsup.compat.Materials.SPAWNER);
        if (block.getState() instanceof CreatureSpawner state) {
            state.setSpawnedType(entity(type));
            // Paper validates min <= max on each call; vanilla stores these as signed shorts.
            com.donsup.compat.BukkitCompat.virtualSpawner(state);
            state.update(true, false);
        }
        String path = path(block.getLocation());
        data.set(path + ".type", type);
        data.set(path + ".stack", 1);
        data.set(path + ".last", System.currentTimeMillis());
        data.set(path + ".drops", null);
        save();
        plugin.msg(event.getPlayer(), Lang.text("custom-spawner.placed-spawner", "&aPlaced &e{0} Spawner&a.", title(type)));
    }

    @EventHandler(priority = org.bukkit.event.EventPriority.HIGHEST, ignoreCancelled = true)
    public void onInteract(PlayerInteractEvent event) {
        if (event.getAction() != org.bukkit.event.block.Action.RIGHT_CLICK_BLOCK || com.donsup.compat.BukkitCompat.offHand(event) || event.getClickedBlock() == null) {
            return;
        }
        Block block = event.getClickedBlock();
        String path = path(block.getLocation());
        if (!data.contains(path)) {
            return;
        }
        event.setCancelled(true);
        Player player = event.getPlayer();
        String placedType = data.getString(path + ".type", "pig");
        ItemStack held = com.donsup.compat.BukkitCompat.hand(player.getInventory());
        String heldType = spawnerType(held);
        boolean canStack = !plugin.getConfig().getBoolean("custom-spawners.stack-requires-sneak", true) || player.isSneaking();
        if (canStack && heldType != null && heldType.equals(placedType)) {
            int add = held.getAmount();
            long next = Math.min(Integer.MAX_VALUE, (long) data.getInt(path + ".stack", 1) + add);
            data.set(path + ".stack", (int) next);
            com.donsup.compat.BukkitCompat.hand(player.getInventory(), null);
            save();
            plugin.msg(player, Lang.text("custom-spawner.stacked-x-spawner-total", "&aStacked &e{0}x {1} Spawner&a. Total: &e{2}&a.", add, title(placedType), data.getInt(path + ".stack")));
            return;
        }
        openSpawner(player, block.getLocation());
    }

    @EventHandler(priority = org.bukkit.event.EventPriority.HIGHEST, ignoreCancelled = true)
    public void onBreak(BlockBreakEvent event) {
        Block block = event.getBlock();
        String path = path(block.getLocation());
        if (!data.contains(path)) {
            return;
        }
        com.donsup.compat.BukkitCompat.drops(event, false);
        generateDrops(block.getLocation());
        String type = data.getString(path + ".type", "pig");
        int stack = data.getInt(path + ".stack", 1);
        dropStoredItems(event.getPlayer(), block.getLocation());
        var remaining = data.getConfigurationSection(path + ".drops");
        if (remaining != null && remaining.getKeys(false).stream().anyMatch(name -> remaining.getInt(name) > 0)) {
            event.setCancelled(true); save();
            plugin.msg(event.getPlayer(), Lang.text("custom-spawner.make-space-or-sell-dump-the-stored-drops-before-picking-up-this-s", "&cMake space or sell/dump the stored drops before picking up this spawner.")); return;
        }
        giveSpawnerItems(event.getPlayer(), type, stack);
        event.getPlayer().giveExp(data.getInt(path + ".xp", 0));
        data.set(path, null);
        save();
        plugin.msg(event.getPlayer(), Lang.text("custom-spawner.picked-up-x-spawner", "&aPicked up &e{0}x {1} Spawner&a.", stack, title(type)));
    }

    @EventHandler
    public void onInventoryClick(InventoryClickEvent event) {
        if (!com.donsup.gui.OwnedInventory.buttonClick(event)) return;
        if (!(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        String title = com.donsup.gui.OwnedInventory.title(event.getView());
        if (!title.equals(TITLE) && !title.startsWith(BLOCK_TITLE)) {
            return;
        }
        event.setCancelled(true);
        ItemStack item = event.getCurrentItem();
        if (item == null || com.donsup.compat.BukkitCompat.air(item.getType()) || !item.hasItemMeta()) {
            return;
        }
        String action = com.donsup.compat.ItemTags.getString(item.getItemMeta(), actionKey);
        if (action == null) {
            return;
        }
        if (action.startsWith("BUY:")) {
            buy(player, action.substring(4));
            return;
        }
        if (action.startsWith("COLLECT:")) {
            collect(player, locationFromKey(action.substring(8)));
            return;
        }
        if (action.startsWith("DUMP:")) {
            dump(player, locationFromKey(action.substring(5)));
            return;
        }
        if (action.startsWith("SELL:")) { sellStored(player, locationFromKey(action.substring(5))); return; }
        if (action.startsWith("XP:")) {
            Location location = locationFromKey(action.substring(3));
            if (location == null) return;
            generateDrops(location);
            int xp = data.getInt(path(location) + ".xp", 0);
            data.set(path(location) + ".xp", 0); save(); player.giveExp(xp); openSpawner(player, location); return;
        }
        if (action.equals("CLOSE")) {
            player.closeInventory();
        }
    }

    private void openSpawner(Player player, Location location) {
        generateDrops(location);
        String path = path(location);
        String type = data.getString(path + ".type", "pig");
        int stack = data.getInt(path + ".stack", 1);
        Inventory inv = plugin.inventory(27, BLOCK_TITLE + " | " + title(type), false);
        fill(inv);
        inv.setItem(4, button(com.donsup.compat.Materials.SPAWNER, plugin.getConfig().getString("custom-spawners.types." + type + ".name", "&d" + title(type)), List.of(
                Lang.text("custom-spawner.stack-size", "&7Stack size: &e{0}", stack),
                Lang.text("custom-spawner.effective-output-x", "&7Effective output: &e{0}x", String.format("%.1f", effectiveStack(stack))),
                Lang.text("custom-spawner.estimated-min", "&7Estimated/min: &f{0}", productionSummary(type, stack)),
                Lang.text("custom-spawner.stored-drops", "&7Stored drops: &f{0}", storedSummary(location)),
                Lang.text("custom-spawner.no-mobs-spawn-hoppers-do-not-pull-drops", "&8No mobs spawn. Hoppers do not pull drops.")
        ), "BALANCE"));
        int slot = 10;
        ConfigurationSection drops = data.getConfigurationSection(path + ".drops");
        if (drops != null) {
            for (String materialName : drops.getKeys(false)) {
                Material material = ItemUtil.material(materialName, Material.STONE);
                int amount = drops.getInt(materialName, 0);
                if (amount > 0 && slot < 17) {
                    inv.setItem(slot++, button(material, Lang.text("custom-spawner.text", "&f{0}", nice(material)), List.of(Lang.text("custom-spawner.stored", "&7Stored: &e{0}", amount)), "BALANCE"));
                }
            }
        }
        inv.setItem(21, button(Material.HOPPER, Lang.text("custom-spawner.collect-drops", "&aCollect Drops"), List.of(Lang.text("custom-spawner.move-all-stored-drops-to-your-inventory", "&7Move all stored drops to your inventory.")), "COLLECT:" + key(location)));
        inv.setItem(20, button(Material.EMERALD, Lang.text("custom-spawner.sell-drops", "&aSell Drops"), List.of(Lang.text("custom-spawner.best-order-price-or-base-server-price", "&7Best order price or base server price."), Lang.text("custom-spawner.up-to-2-304-items-per-click", "&7Up to 2,304 items per click.")), "SELL:" + key(location)));
        inv.setItem(24, button(com.donsup.compat.Materials.EXPERIENCE_BOTTLE, Lang.text("custom-spawner.collect-xp", "&eCollect XP"), List.of(Lang.text("custom-spawner.stored-xp", "&7Stored XP: {0}", data.getInt(path + ".xp", 0))), "XP:" + key(location)));
        inv.setItem(23, button(Material.DROPPER, Lang.text("custom-spawner.dump-drops", "&bDump Drops"), List.of(
                Lang.text("custom-spawner.drops-stored-items-above-the-spawner", "&7Drops stored items above the spawner."),
                Lang.text("custom-spawner.use-water-streams-below-nearby-to-move-them", "&7Use water streams below/nearby to move them.")
        ), "DUMP:" + key(location)));
        player.openInventory(inv);
    }

    private void buy(Player player, String type) {
        type = normalize(type);
        ItemStack reward = spawnerItem(type, 1);
        if (!com.donsup.util.InventoryCapacity.fits(player, reward, 1)) {
            plugin.msg(player, Lang.text("custom-spawner.make-inventory-space-before-buying-a-spawner", "&cMake inventory space before buying a spawner.")); return;
        }
        int price = plugin.getConfig().getInt("custom-spawners.price-shards", 1500);
        if (!plugin.economy().takeShards(player.getUniqueId(), price)) {
            plugin.msg(player, Lang.text("custom-spawner.you-need-shards-to-buy-a-spawner", "&cYou need &d{0} shards &cto buy a spawner.", price));
            return;
        }
        player.getInventory().addItem(reward);
        plugin.msg(player, Lang.text("custom-spawner.purchased-spawner-for-shards", "&aPurchased &e{0} Spawner&a for &d{1} shards&a.", title(type), price));
        openShop(player);
    }

    private void collect(Player player, Location location) {
        generateDrops(location);
        dropStoredItems(player, location);
        save();
        openSpawner(player, location);
    }

    private void dump(Player player, Location location) {
        generateDrops(location);
        String path = path(location);
        ConfigurationSection drops = data.getConfigurationSection(path + ".drops");
        if (drops == null) {
            plugin.msg(player, Lang.text("custom-spawner.no-drops-stored", "&cNo drops stored."));
            openSpawner(player, location);
            return;
        }
        Location dropAt = location.clone().add(0.5, 1.15, 0.5);
        int budget = 2304;
        for (String materialName : drops.getKeys(false)) {
            ItemStack template=com.donsup.compat.Materials.stack(materialName,1);
            if(template==null) continue;
            int amount = drops.getInt(materialName, 0);
            while (amount > 0 && budget > 0) {
                int give = Math.min(Math.min(64, amount), budget);
                ItemStack item=template.clone(); item.setAmount(give);
                location.getWorld().dropItemNaturally(dropAt,item);
                amount -= give;
                budget -= give;
            }
            data.set(path + ".drops." + materialName, amount);
        }
        save();
        plugin.msg(player, Lang.text("custom-spawner.dumped-stored-drops", "&aDumped stored drops."));
        openSpawner(player, location);
    }

    private void generateDrops(Location location) {
        if (location == null) return;
        String path = path(location);
        if (!data.contains(path)) {
            return;
        }
        long now = System.currentTimeMillis();
        long last = data.getLong(path + ".last", now);
        long interval = plugin.getConfig().getLong("custom-spawners.drop-generation-seconds", 60) * 1000L;
        long cycles = interval <= 0 ? 0 : Math.min(10080L, Math.max(0, (now - last) / interval));
        if (cycles <= 0) {
            return;
        }
        String type = data.getString(path + ".type", "pig");
        int stack = data.getInt(path + ".stack", 1);
        double scaled = effectiveStack(stack);
        ConfigurationSection drops = plugin.getConfig().getConfigurationSection("custom-spawners.types." + type + ".drops");
        if (drops != null) {
            for (String material : drops.getKeys(false)) {
                long add = (long) Math.floor(drops.getInt(material, 1) * scaled * cycles);
                data.set(path + ".drops." + material, (int) Math.min(1000000L, Math.max(0L, data.getInt(path + ".drops." + material, 0)) + Math.max(0L, add)));
            }
        }
        data.set(path + ".last", now - Math.floorMod(now - last, Math.max(1L, interval)));
        data.set(path + ".xp", (int) Math.min(1000000L, data.getLong(path + ".xp", 0)
            + cycles * Math.max(0, plugin.getConfig().getInt("custom-spawners.xp-per-cycle", 5))));
        save();
    }

    private void sellStored(Player player, Location location) {
        if (location == null) return;
        generateDrops(location);
        ConfigurationSection drops = data.getConfigurationSection(path(location) + ".drops");
        if (drops == null) return;
        int budget = 2304; double earned = 0;
        for (String name : drops.getKeys(false)) {
            Material material = com.donsup.compat.Materials.match(name);
            if (material == null) continue;
            int remaining = drops.getInt(name);
            while (remaining > 0 && budget > 0) {
                int count = Math.min(Math.min(remaining, 64), budget);
                ItemStack item = new ItemStack(material, count);
                earned += plugin.market().sell(player, item);
                int sold = count - item.getAmount();
                remaining -= sold; budget -= count;
                if (sold == 0) break;
            }
            data.set(path(location) + ".drops." + name, remaining);
        }
        save(); plugin.msg(player, Lang.text("custom-spawner.spawner-sale", "&aSpawner sale: {0}", Text.money(earned))); openSpawner(player, location);
    }

    private void dropStoredItems(Player player, Location location) {
        String path = path(location);
        ConfigurationSection drops = data.getConfigurationSection(path + ".drops");
        if (drops == null) {
            return;
        }
        for (String materialName : drops.getKeys(false)) {
            ItemStack template=com.donsup.compat.Materials.stack(materialName,1);
            if(template==null) continue;
            int amount = drops.getInt(materialName, 0);
            while (amount > 0) {
                int give = Math.min(64, amount);
                ItemStack item=template.clone(); item.setAmount(give);
                var leftovers = player.getInventory().addItem(item);
                int returned = leftovers.values().stream().mapToInt(ItemStack::getAmount).sum();
                amount -= give;
                if (returned > 0) { amount += returned; break; }
            }
            data.set(path + ".drops." + materialName, amount);
        }
    }

    private void giveSpawnerItems(Player player, String type, int amount) {
        while (amount > 0) {
            int give = Math.min(64, amount);
            player.getInventory().addItem(spawnerItem(type, give)).values().forEach(item -> player.getWorld().dropItemNaturally(player.getLocation(), item));
            amount -= give;
        }
    }

    private String spawnerType(ItemStack item) {
        if (item == null || com.donsup.compat.BukkitCompat.air(item.getType()) || !item.hasItemMeta()) {
            return null;
        }
        return com.donsup.compat.ItemTags.getString(item.getItemMeta(), itemTypeKey);
    }

    private ItemStack button(Material material, String name, List<String> lore, String action) {
        return plugin.button(material, name, lore, actionKey, action);
    }

    private void fill(Inventory inv) {
        ItemStack glass = button(com.donsup.compat.Materials.GRAY_STAINED_GLASS_PANE, " ", List.of(), "BALANCE");
        for (int i = 0; i < inv.getSize(); i++) {
            inv.setItem(i, glass);
        }
    }

    private EntityType entity(String type) {
        String configured = plugin.getConfig().getString("custom-spawners.types." + type + ".entity", "PIG");
        try {
            if(configured.equalsIgnoreCase("ZOMBIFIED_PIGLIN")) {
                try { return EntityType.valueOf("ZOMBIFIED_PIGLIN"); }
                catch(IllegalArgumentException oldVersion) { return EntityType.valueOf("PIG_ZOMBIE"); }
            }
            return EntityType.valueOf(configured.toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            return EntityType.PIG;
        }
    }

    private String dropsSummary(String type) {
        ConfigurationSection drops = plugin.getConfig().getConfigurationSection("custom-spawners.types." + type + ".drops");
        if (drops == null) {
            return Lang.text("custom-spawner.none", "None");
        }
        StringBuilder out = new StringBuilder();
        for (String key : drops.getKeys(false)) {
            if (!out.isEmpty()) {
                out.append(", ");
            }
            out.append(nice(ItemUtil.material(key, Material.STONE)));
        }
        return out.toString();
    }

    private String productionSummary(String type, int stack) {
        ConfigurationSection drops = plugin.getConfig().getConfigurationSection("custom-spawners.types." + type + ".drops");
        if (drops == null) {
            return Lang.text("custom-spawner.none", "None");
        }
        double intervalSeconds = Math.max(1.0, plugin.getConfig().getDouble("custom-spawners.drop-generation-seconds", 60));
        double cyclesPerMinute = 60.0 / intervalSeconds;
        double scaled = effectiveStack(stack);
        StringBuilder out = new StringBuilder();
        for (String key : drops.getKeys(false)) {
            if (!out.isEmpty()) {
                out.append(", ");
            }
            double perMinute = drops.getInt(key, 1) * scaled * cyclesPerMinute;
            out.append(nice(ItemUtil.material(key, Material.STONE))).append(" ").append(String.format("%.1f", perMinute));
        }
        return out.toString();
    }

    private double effectiveStack(int stack) {
        stack = Math.max(1, stack);
        if (plugin.getConfig().getBoolean("custom-spawners.donut-style-curve.enabled", true)) {
            double base = donutCurve(1);
            return Math.max(1.0, donutCurve(stack) / Math.max(0.0001, base));
        }
        double exponent = plugin.getConfig().getDouble("custom-spawners.stack-scaling-exponent", 0.82);
        return Math.max(1.0, Math.pow(stack, exponent));
    }

    private double donutCurve(int stack) {
        double asymptote = plugin.getConfig().getDouble("custom-spawners.donut-style-curve.asymptote", 1505.35);
        double multiplier = plugin.getConfig().getDouble("custom-spawners.donut-style-curve.multiplier", 0.39567);
        double decay = plugin.getConfig().getDouble("custom-spawners.donut-style-curve.decay", 0.00134606);
        double offset = plugin.getConfig().getDouble("custom-spawners.donut-style-curve.offset", 8.24358);
        return Math.max(1.0, -multiplier * Math.exp((-decay * stack) + offset) + asymptote);
    }

    private String storedSummary(Location location) {
        ConfigurationSection drops = data.getConfigurationSection(path(location) + ".drops");
        if (drops == null) {
            return Lang.text("custom-spawner.none", "None");
        }
        int total = 0;
        for (String key : drops.getKeys(false)) {
            total += drops.getInt(key, 0);
        }
        return String.valueOf(total);
    }

    private String normalize(String type) {
        return type == null ? "pig" : type.toLowerCase(Locale.ROOT).replace('-', '_');
    }

    private String title(String key) {
        String lower = normalize(key).replace('_', ' ');
        StringBuilder out = new StringBuilder();
        boolean cap = true;
        for (char c : lower.toCharArray()) {
            if (cap && Character.isLetter(c)) {
                out.append(Character.toUpperCase(c));
                cap = false;
            } else {
                out.append(c);
            }
            if (c == ' ') {
                cap = true;
            }
        }
        return Lang.label("labels", key, out.toString());
    }

    private String nice(Material material) {
        return Lang.label("materials", material.name(), title(material.name()));
    }

    private String path(Location location) {
        return "spawners." + key(location);
    }

    private String key(Location location) {
        return location.getWorld().getName() + "," + location.getBlockX() + "," + location.getBlockY() + "," + location.getBlockZ();
    }

    private Location locationFromKey(String key) {
        String[] parts = key.split(",");
        return new Location(Bukkit.getWorld(parts[0]), Integer.parseInt(parts[1]), Integer.parseInt(parts[2]), Integer.parseInt(parts[3]));
    }
}


===== src/main/java/com/donsup/tools/SellAxe.java =====

package com.donsup.tools;

import com.donsup.config.Lang;
import com.donsup.compat.ItemKey;

import com.donsup.DonsupPlugin;
import com.donsup.util.*;
import org.bukkit.*;
import com.donsup.compat.ContainerHandle;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.block.Action;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.inventory.*;
import java.util.*;

/** Original shard utility: shift-right-click a container to sell its plain contents. */
public final class SellAxe implements Listener {
    private final DonsupPlugin plugin;
    private final ItemKey key;
    public SellAxe(DonsupPlugin plugin) { this.plugin = plugin; key = new ItemKey(plugin, "sell_axe"); }
    public ItemStack item() {
        ItemStack item = ItemUtil.named(Material.DIAMOND_AXE, 1, Lang.text("sell-axe.crystal-sell-axe", "&dCrystal Sell Axe"), List.of(Lang.text("sell-axe.shift-right-click-a-chest-or-barrel", "&7Shift-right-click a chest or barrel."), Lang.text("sell-axe.sells-plain-contents-at-the-best-available-price", "&7Sells plain contents at the best available price.")));
        var meta = item.getItemMeta(); com.donsup.compat.ItemTags.setByte(meta, key, (byte) 1); item.setItemMeta(meta); return item;
    }
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true)
    public void use(PlayerInteractEvent event) {
        if (com.donsup.compat.BukkitCompat.offHand(event) || event.getAction() != Action.RIGHT_CLICK_BLOCK || !event.getPlayer().isSneaking()) return;
        ItemStack tool = event.getItem();
        if (tool == null || !tool.hasItemMeta() || !com.donsup.compat.ItemTags.hasByte(tool.getItemMeta(), key)) return;
        ContainerHandle container=ContainerHandle.of(event.getClickedBlock());
        if (container == null || container.isLocked()) return;
        if (plugin.chestShops().isShop(event.getClickedBlock())) {
            event.setCancelled(true); plugin.msg(event.getPlayer(), Lang.text("sell-axe.manage-this-shop-s-stock-through-its-inventory-the-sell-axe-canno", "&cManage this shop's stock through its inventory; the Sell Axe cannot sell shop stock.")); return;
        }
        if (event.useInteractedBlock() == Event.Result.DENY) return;
        Player player = event.getPlayer();
        if (!player.hasPermission("donsup.use")) return;
        Inventory inventory = container.getInventory();
        ItemStack[] contents = com.donsup.compat.BukkitCompat.storage(inventory);
        double earned = 0;
        for (ItemStack item : contents) earned += plugin.market().sell(player, item);
        com.donsup.compat.BukkitCompat.storage(inventory, contents);
        event.setCancelled(true);
        plugin.msg(player, earned > 0 ? Lang.text("sell-axe.container-sale", "&aContainer sale: {0}", Text.money(earned)) : Lang.text("sell-axe.no-supported-plain-items-to-sell", "&7No supported plain items to sell."));
    }
}


===== src/main/java/com/donsup/tools/ToolManager.java =====

package com.donsup.tools;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.ItemUtil;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;

public class ToolManager implements Listener {
    private static final String TITLE = "SMP | Drills";
    private final DonsupPlugin plugin;
    private final ItemKey drillKey;
    private final ItemKey actionKey;
    private final Set<UUID> mining = new HashSet<>();

    public ToolManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.drillKey = new ItemKey(plugin, "drill_tier");
        this.actionKey = new ItemKey(plugin, "drill_action");
    }

    public void open(Player player) {
        Inventory inv = plugin.inventory(54, TITLE, false);
        fill(inv);
        inv.setItem(4, button(Material.DIAMOND_PICKAXE, Lang.text("tool.vein-miner-drills", "&b&lVein Miner Drills"), List.of(
                Lang.text("tool.break-ore-veins-and-logs-faster", "&7Break ore veins and logs faster."),
                Lang.text("tool.your-shards", "&7Your shards: &d{0}", plugin.economy().shards(player.getUniqueId()))
        ), "NONE"));
        int slot = 20;
        for (String tier : List.of("basic", "advanced", "mythic")) {
            inv.setItem(slot++, button(icon(tier), Lang.text("tool.drill", "&e{0} Drill", title(tier)), List.of(
                    Lang.text("tool.cost-shards", "&7Cost: &d{0} shards", cost(tier)),
                    Lang.text("tool.max-blocks", "&7Max blocks: &e{0}", maxBlocks(tier)),
                    Lang.text("tool.click-to-buy", "&aClick to buy")
            ), "BUY:" + tier));
        }
        player.openInventory(inv);
    }

    public ItemStack drill(String tier) {
        tier = clean(tier);
        ItemStack item = ItemUtil.named(icon(tier), 1, Lang.text("tool.drill-666972", "&b{0} Drill", title(tier)), List.of(
                Lang.text("tool.vein-mines-matching-ores-and-logs", "&7Vein mines matching ores and logs."),
                Lang.text("tool.max-blocks", "&7Max blocks: &e{0}", maxBlocks(tier)),
                Lang.text("tool.drill-tier", "&8Drill tier: {0}", tier)
        ));
        item.addUnsafeEnchantment(com.donsup.compat.BukkitCompat.efficiency(), Math.max(1, plugin.getConfig().getInt("drills.tiers." + tier + ".efficiency", 4)));
        ItemMeta meta = item.getItemMeta();
        com.donsup.compat.ItemTags.setString(meta, drillKey, tier);
        item.setItemMeta(meta);
        return item;
    }

    public void give(Player player, String tier) {
        plugin.platform().playerNow(player, () -> {
            player.getInventory().addItem(drill(tier)).values().forEach(item -> player.getWorld().dropItemNaturally(player.getLocation(), item));
            plugin.msg(player, Lang.text("tool.gave-drill", "&aGave &e{0} Drill&a.", title(tier)));
        });
    }

    @EventHandler(priority = org.bukkit.event.EventPriority.MONITOR, ignoreCancelled = true)
    public void onBreak(BlockBreakEvent event) {
        if (event.isCancelled() || mining.contains(event.getPlayer().getUniqueId())) return;
        Player player = event.getPlayer();
        ItemStack tool = com.donsup.compat.BukkitCompat.hand(player.getInventory());
        String tier = tier(tool);
        if (tier == null || !plugin.getConfig().getBoolean("drills.enabled", true)) return;
        Material material = event.getBlock().getType();
        if (!veinMaterial(material)) return;
        int max = maxBlocks(tier);
        Set<Block> blocks = vein(event.getBlock(), material, max);
        if (blocks.size() <= 1) return;
        mining.add(player.getUniqueId());
        try {
            int broken = 0;
            for (Block block : blocks) {
                if (block.equals(event.getBlock())) continue;
                if (com.donsup.compat.BukkitCompat.breakBlock(player,block)) broken++;
            }
            // breakBlock respects protection plugins, tool durability and normal drops.
            plugin.msg(player, Lang.text("tool.drill-mined-blocks", "&bDrill mined &e{0} &bblocks.", (broken + 1)));
        } finally {
            mining.remove(player.getUniqueId());
        }
    }

    @EventHandler
    public void onClick(InventoryClickEvent event) {
        if (!com.donsup.gui.OwnedInventory.buttonClick(event)) return;
        if (!(event.getWhoClicked() instanceof Player player) || !com.donsup.gui.OwnedInventory.title(event.getView()).equals(TITLE)) return;
        event.setCancelled(true);
        ItemStack item = event.getCurrentItem();
        if (item == null || !item.hasItemMeta()) return;
        String action = com.donsup.compat.ItemTags.getString(item.getItemMeta(), actionKey);
        if (action == null || !action.startsWith("BUY:")) return;
        String tier = action.substring(4);
        ItemStack reward = drill(tier);
        if (!com.donsup.util.InventoryCapacity.fits(player, reward, reward.getAmount())) {
            plugin.msg(player, Lang.text("tool.make-inventory-space-before-buying-a-drill", "&cMake inventory space before buying a drill.")); return;
        }
        int cost = cost(tier);
        if (!plugin.economy().takeShards(player.getUniqueId(), cost)) {
            plugin.msg(player, Lang.text("tool.you-need-shards-to-buy-that-drill", "&cYou need &d{0} shards &cto buy that drill.", cost));
            return;
        }
        player.getInventory().addItem(reward);
        plugin.msg(player, Lang.text("tool.purchased-drill", "&aPurchased &e{0} Drill&a.", title(tier)));
        open(player);
    }

    private Set<Block> vein(Block start, Material material, int max) {
        Set<Block> found = new HashSet<>();
        ArrayDeque<Block> queue = new ArrayDeque<>();
        queue.add(start);
        while (!queue.isEmpty() && found.size() < max) {
            Block block = queue.removeFirst();
            if (!found.add(block)) continue;
            for (BlockFace face : BlockFace.values()) {
                if (Math.abs(face.getModX()) + Math.abs(face.getModY()) + Math.abs(face.getModZ()) != 1) continue;
                Block next = block.getRelative(face);
                if (plugin.platform().owns(next.getLocation()) && next.getType() == material && !found.contains(next)) queue.add(next);
            }
        }
        return found;
    }

    private void damage(ItemStack tool, int amount) {
        if (tool.getType().getMaxDurability() > 0) tool.setDurability((short)(tool.getDurability() + Math.max(1,amount)));
    }

    private boolean veinMaterial(Material material) {
        String name = material.name();
        return name.endsWith("_ORE") || (name.endsWith("_LOG") || name.equals("LOG") || name.equals("LOG_2")) || name.endsWith("_STEM") || name.equals("ANCIENT_DEBRIS");
    }

    private String tier(ItemStack item) {
        if (item == null || com.donsup.compat.BukkitCompat.air(item.getType()) || !item.hasItemMeta()) return null;
        return com.donsup.compat.ItemTags.getString(item.getItemMeta(), drillKey);
    }

    private int cost(String tier) {
        return plugin.getConfig().getInt("drills.tiers." + clean(tier) + ".cost-shards", 500);
    }

    private int maxBlocks(String tier) {
        return Math.max(2, Math.min(512, plugin.getConfig().getInt("drills.tiers." + clean(tier) + ".max-blocks", 16)));
    }

    private Material icon(String tier) {
        return ItemUtil.material(plugin.getConfig().getString("drills.tiers." + clean(tier) + ".material"), Material.DIAMOND_PICKAXE);
    }

    private void fill(Inventory inv) {
        ItemStack glass = button(com.donsup.compat.Materials.GRAY_STAINED_GLASS_PANE, " ", List.of(), "NONE");
        for (int i = 0; i < inv.getSize(); i++) inv.setItem(i, glass);
    }

    private ItemStack button(Material material, String name, List<String> lore, String action) {
        return plugin.button(material, name, lore, actionKey, action);
    }

    private String clean(String input) {
        return input == null ? "basic" : input.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9_-]", "");
    }

    private String title(String key) {
        String lower = clean(key).replace('_', ' ').replace('-', ' ');
        StringBuilder out = new StringBuilder();
        boolean cap = true;
        for (char c : lower.toCharArray()) {
            if (cap && Character.isLetter(c)) {
                out.append(Character.toUpperCase(c));
                cap = false;
            } else {
                out.append(c);
            }
            if (c == ' ') cap = true;
        }
        return Lang.label("labels", key, out.toString());
    }
}


===== src/main/java/com/donsup/trade/TradeManager.java =====

package com.donsup.trade;

import com.donsup.config.Lang;

import com.donsup.DonsupPlugin;
import com.donsup.util.ItemUtil;
import com.donsup.util.Text;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryCloseEvent;
import org.bukkit.event.inventory.InventoryDragEvent;
import org.bukkit.event.inventory.ClickType;
import org.bukkit.event.inventory.InventoryAction;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;

import java.util.*;

public class TradeManager implements Listener {
    private static final String TITLE = "SMP | Trade";
    private final DonsupPlugin plugin;
    private final TradeReturns returns;
    private final ItemKey actionKey;
    private final Map<UUID, UUID> invites = new HashMap<>();
    private final Map<UUID, TradeSession> sessions = new HashMap<>();
    private final Set<UUID> closing = new HashSet<>();
    private final Set<Integer> leftSlots = Set.of(10, 11, 12, 19, 20, 21, 28, 29, 30);
    private final Set<Integer> rightSlots = Set.of(14, 15, 16, 23, 24, 25, 32, 33, 34);

    public TradeManager(DonsupPlugin plugin) {
        this.plugin = plugin;
        this.returns = new TradeReturns(plugin);
        this.actionKey = new ItemKey(plugin, "trade_action");
    }

    public void trade(Player player, String[] args) {
        if (args.length == 0) { plugin.msg(player, Lang.text("trade.usage-trade", "&eUsage: /trade <player|accept|deny|money|shards>")); return; }
        switch (args[0].toLowerCase()) {
            case "claim" -> returns.claim(player);
            case "accept" -> accept(player, args.length >= 2 ? args[1] : "");
            case "deny" -> deny(player);
            case "money" -> setMoney(player, args.length >= 2 ? parse(args[1]) : -1);
            case "shards" -> {
                double amount = args.length >= 2 ? parse(args[1]) : -1;
                if (!Double.isFinite(amount) || amount < 0 || amount > Integer.MAX_VALUE || amount != Math.floor(amount)) {
                    plugin.msg(player, Lang.text("trade.shards-must-be-a-whole-number-between-0-and-2147483647", "&cShards must be a whole number between 0 and 2147483647.")); return;
                }
                setShards(player, (int) amount);
            }
            default -> invite(player, Bukkit.getPlayerExact(args[0]));
        }
    }

    private void invite(Player player, Player target) {
        if (target == null || target.equals(player)) { plugin.msg(player, Lang.text("trade.invalid-player", "&cInvalid player.")); return; }
        if (sessions.containsKey(player.getUniqueId()) || sessions.containsKey(target.getUniqueId())) { plugin.msg(player, Lang.text("trade.a-player-is-already-trading", "&cA player is already trading.")); return; }
        invites.put(target.getUniqueId(), player.getUniqueId());
        plugin.msg(player, Lang.text("trade.sent-trade-request-to", "&aSent trade request to &e{0}&a.", target.getName()));
        plugin.msg(target, Lang.text("trade.wants-to-trade-use-trade-accept", "&e{0} &awants to trade. Use &f/trade accept {1}&a.", player.getName(), player.getName()));
    }

    private void accept(Player player, String from) {
        Player other = Bukkit.getPlayerExact(from);
        if (other == null || !other.getUniqueId().equals(invites.get(player.getUniqueId()))) { plugin.msg(player, Lang.text("trade.no-matching-trade-request", "&cNo matching trade request.")); return; }
        if (!plugin.platform().owns(other)) { plugin.msg(player, Lang.text("trade.meet-the-other-player-nearby-before-opening-a-trade-on-folia", "&eMeet the other player nearby before opening a trade on Folia.")); return; }
        if (sessions.containsKey(player.getUniqueId()) || sessions.containsKey(other.getUniqueId())) { plugin.msg(player, Lang.text("trade.a-player-is-already-trading", "&cA player is already trading.")); return; }
        TradeSession session = new TradeSession(other.getUniqueId(), player.getUniqueId(), plugin.inventory(45, TITLE + " | " + other.getName() + " & " + player.getName(), true));
        sessions.put(other.getUniqueId(), session);
        sessions.put(player.getUniqueId(), session);
        invites.remove(player.getUniqueId());
        render(session);
        other.openInventory(session.inv);
        player.openInventory(session.inv);
    }

    private void deny(Player player) {
        invites.remove(player.getUniqueId());
        plugin.msg(player, Lang.text("trade.denied-trade-request", "&cDenied trade request."));
    }

    private void setMoney(Player player, double amount) {
        TradeSession s = sessions.get(player.getUniqueId());
        if (s == null || !Double.isFinite(amount) || amount < 0) { plugin.msg(player, Lang.text("trade.usage-during-trade-trade-money", "&eUsage during trade: /trade money <amount>")); return; }
        if (s.a.equals(player.getUniqueId())) s.moneyA = amount; else s.moneyB = amount;
        s.confirmA = s.confirmB = false;
        render(s);
    }

    private void setShards(Player player, int amount) {
        TradeSession s = sessions.get(player.getUniqueId());
        if (s == null || !Double.isFinite(amount) || amount < 0) { plugin.msg(player, Lang.text("trade.usage-during-trade-trade-shards", "&eUsage during trade: /trade shards <amount>")); return; }
        if (s.a.equals(player.getUniqueId())) s.shardsA = amount; else s.shardsB = amount;
        s.confirmA = s.confirmB = false;
        render(s);
    }

    private void render(TradeSession s) {
        for (int slot : List.of(4, 13, 22, 31, 40)) s.inv.setItem(slot, button(com.donsup.compat.Materials.BLACK_STAINED_GLASS_PANE, " ", List.of(), "NONE"));
        Player a = Bukkit.getPlayer(s.a);
        Player b = Bukkit.getPlayer(s.b);
        s.inv.setItem(0, button(com.donsup.compat.Materials.PLAYER_HEAD, Lang.text("trade.text", "&a{0}", (a == null ? Lang.text("trade.player-a", "Player A") : a.getName())), List.of(Lang.text("trade.money", "&7Money: &a{0}", Text.money(s.moneyA)), Lang.text("trade.shards", "&7Shards: &d{0}", s.shardsA), s.confirmA ? Lang.text("trade.confirmed", "&aConfirmed") : Lang.text("trade.not-confirmed", "&cNot confirmed")), "NONE"));
        s.inv.setItem(8, button(com.donsup.compat.Materials.PLAYER_HEAD, Lang.text("trade.text-539ee5", "&b{0}", (b == null ? Lang.text("trade.player-b", "Player B") : b.getName())), List.of(Lang.text("trade.money", "&7Money: &a{0}", Text.money(s.moneyB)), Lang.text("trade.shards", "&7Shards: &d{0}", s.shardsB), s.confirmB ? Lang.text("trade.confirmed", "&aConfirmed") : Lang.text("trade.not-confirmed", "&cNot confirmed")), "NONE"));
        s.inv.setItem(36, button(s.confirmA ? com.donsup.compat.Materials.LIME_DYE : com.donsup.compat.Materials.GRAY_DYE, Lang.text("trade.left-confirm", "&aLeft Confirm"), List.of(Lang.text("trade.left-player-confirm", "&7Left player confirm.")), "CONFIRM:A"));
        s.inv.setItem(44, button(s.confirmB ? com.donsup.compat.Materials.LIME_DYE : com.donsup.compat.Materials.GRAY_DYE, Lang.text("trade.right-confirm", "&aRight Confirm"), List.of(Lang.text("trade.right-player-confirm", "&7Right player confirm.")), "CONFIRM:B"));
    }

    @EventHandler
    public void onClick(InventoryClickEvent event) {
        if (!(event.getWhoClicked() instanceof Player player) || !com.donsup.gui.OwnedInventory.title(event.getView()).startsWith(TITLE)) return;
        TradeSession s = sessions.get(player.getUniqueId());
        if (s == null || com.donsup.compat.Views.top(event.getView()) != s.inv) return;
        if (event.isShiftClick() || event.getClick() == ClickType.DOUBLE_CLICK
                || event.getClick() == ClickType.NUMBER_KEY || event.getClick().name().equals("SWAP_OFFHAND")
                || event.getAction() == InventoryAction.COLLECT_TO_CURSOR) {
            event.setCancelled(true);
            return;
        }
        int raw = event.getRawSlot();
        boolean playerA = s.a.equals(player.getUniqueId());
        if (raw >= 0 && raw < event.getInventory().getSize()) {
            boolean ownSlot = playerA ? leftSlots.contains(raw) : rightSlots.contains(raw);
            ItemStack current = event.getCurrentItem();
            String action = current == null || !current.hasItemMeta() ? null : com.donsup.compat.ItemTags.getString(current.getItemMeta(), actionKey);
            if (action != null && action.startsWith("CONFIRM:")) {
                event.setCancelled(true);
                if ((playerA && action.equals("CONFIRM:A")) || (!playerA && action.equals("CONFIRM:B"))) {
                    if (playerA) s.confirmA = !s.confirmA; else s.confirmB = !s.confirmB;
                    render(s);
                    if (s.confirmA && s.confirmB) complete(s);
                }
                return;
            }
            if (!ownSlot) {
                event.setCancelled(true);
                return;
            }
            s.confirmA = s.confirmB = false;
            plugin.platform().player(player, () -> { if (!s.finished) render(s); });
        }
    }

    @EventHandler
    public void onDrag(InventoryDragEvent event) {
        TradeSession s = sessions.get(event.getWhoClicked().getUniqueId());
        if (s != null && com.donsup.compat.Views.top(event.getView()) == s.inv
                && event.getRawSlots().stream().anyMatch(slot -> slot < s.inv.getSize())) event.setCancelled(true);
    }

    @EventHandler
    public void onClose(InventoryCloseEvent event) {
        if (!(event.getInventory().getHolder() instanceof com.donsup.gui.OwnedInventory)) return;
        if (closing.contains(event.getPlayer().getUniqueId())) return;
        TradeSession s = sessions.get(event.getPlayer().getUniqueId());
        if (s != null && event.getInventory() == s.inv) cancel(s);
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        UUID id = event.getPlayer().getUniqueId();
        invites.remove(id);
        invites.values().removeIf(id::equals);
        TradeSession s = sessions.get(id);
        if (s != null) cancel(s);
    }

    public void shutdown() {
        for (TradeSession s : new HashSet<>(sessions.values())) cancel(s);
        invites.clear();
    }

    private void cancel(TradeSession s) {
        if (s.finished) return;
        s.finished = true;
        returnItems(s);
        close(s);
    }

    private void complete(TradeSession s) {
        Player a = Bukkit.getPlayer(s.a); Player b = Bukkit.getPlayer(s.b);
        if (s.finished) return;
        if (a == null || b == null) { cancel(s); return; }
        if (!plugin.platform().owns(a) || !plugin.platform().owns(b)) {
            plugin.msg(a,Lang.text("trade.trade-cancelled-because-players-left-the-same-region", "&eTrade cancelled because players left the same region."));cancel(s);return;
        }
        if (!plugin.economy().exchange(s.a, s.b, s.moneyA, s.moneyB, s.shardsA, s.shardsB)) {
            plugin.msg(a, Lang.text("trade.trade-failed-insufficient-funds-invalid-amount-or-saving-failed-n", "&cTrade failed: insufficient funds, invalid amount, or saving failed. No payment was taken."));
            plugin.msg(b, Lang.text("trade.trade-failed-insufficient-funds-invalid-amount-or-saving-failed-n", "&cTrade failed: insufficient funds, invalid amount, or saving failed. No payment was taken."));
            cancel(s);
            return;
        }
        s.finished = true;
        for (int slot : leftSlots) { give(b, s.inv.getItem(slot)); s.inv.setItem(slot, null); }
        for (int slot : rightSlots) { give(a, s.inv.getItem(slot)); s.inv.setItem(slot, null); }
        plugin.msg(a, Lang.text("trade.trade-completed", "&aTrade completed."));
        plugin.msg(b, Lang.text("trade.trade-completed", "&aTrade completed."));
        close(s);
    }

    private void close(TradeSession s) {
        closing.add(s.a); closing.add(s.b);
        sessions.remove(s.a); sessions.remove(s.b);
        Player a = Bukkit.getPlayer(s.a); Player b = Bukkit.getPlayer(s.b);
        if (a != null) plugin.platform().playerNow(a, () -> { if(com.donsup.compat.Views.top(a.getOpenInventory())==s.inv)a.closeInventory(); });
        if (b != null) plugin.platform().playerNow(b, () -> { if(com.donsup.compat.Views.top(b.getOpenInventory())==s.inv)b.closeInventory(); });
        closing.remove(s.a); closing.remove(s.b);
    }

    private void returnItems(TradeSession s) {
        Player a = Bukkit.getPlayer(s.a); Player b = Bukkit.getPlayer(s.b);
        for (int slot : leftSlots) { returnItem(s.a,a,s.inv.getItem(slot));s.inv.setItem(slot,null); }
        for (int slot : rightSlots) { returnItem(s.b,b,s.inv.getItem(slot));s.inv.setItem(slot,null); }
    }
    private void returnItem(UUID owner,Player player,ItemStack item) {
        if(player==null || !plugin.platform().owns(player) || !plugin.isEnabled())returns.enqueue(owner,item);
        else give(player,item);
    }
    @EventHandler public void onJoin(org.bukkit.event.player.PlayerJoinEvent event) {
        plugin.platform().player(event.getPlayer(),()->returns.claim(event.getPlayer()));
    }
    @EventHandler(priority=org.bukkit.event.EventPriority.MONITOR,ignoreCancelled=true)
    public void onTeleport(org.bukkit.event.player.PlayerTeleportEvent event) {
        TradeSession session=sessions.get(event.getPlayer().getUniqueId());if(session!=null)cancel(session);
    }

    private void give(Player player, ItemStack item) {
        if (item != null && !com.donsup.compat.BukkitCompat.air(item.getType())) player.getInventory().addItem(item.clone()).values()
                .forEach(extra -> player.getWorld().dropItemNaturally(player.getLocation(), extra));
    }

    private ItemStack button(Material material, String name, List<String> lore, String action) {
        return plugin.button(material, name, lore, actionKey, action);
    }

    private double parse(String input) { try { double value = Double.parseDouble(input); return Double.isFinite(value) ? value : -1; } catch (Exception ex) { return -1; } }

    private static class TradeSession {
        final UUID a, b;
        final Inventory inv;
        double moneyA, moneyB;
        int shardsA, shardsB;
        boolean confirmA, confirmB, finished;
        TradeSession(UUID a, UUID b, Inventory inv) { this.a = a; this.b = b; this.inv = inv; }
    }
}


===== src/main/java/com/donsup/trade/TradeReturns.java =====

package com.donsup.trade;

import com.donsup.config.Lang;
import com.donsup.DonsupPlugin;
import com.donsup.util.*;
import org.bukkit.Bukkit;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import java.io.File;
import java.util.*;

/** Retains returns if a Folia entity retires before its owner-thread delivery runs. */
final class TradeReturns {
    private final DonsupPlugin plugin;
    private final File file;
    private final YamlConfiguration data;
    TradeReturns(DonsupPlugin plugin){this.plugin=plugin;file=new File(plugin.getDataFolder(),"trade-returns.yml");data=SafeYaml.load(file);}
    private void save(){try{SafeYaml.save(data,file);}catch(java.io.IOException ex){throw new IllegalStateException("Cannot save trade returns",ex);}}
    void enqueue(UUID owner,ItemStack item){
        if(item==null||com.donsup.compat.BukkitCompat.air(item.getType()))return;
        String key=owner+"."+UUID.randomUUID();
        data.set(key+".state","pending");data.set(key+".item",item.clone());save();
        Player player=Bukkit.getPlayer(owner);if(player!=null)plugin.platform().player(player,()->claim(player));
    }
    void claim(Player player){
        var section=data.getConfigurationSection(player.getUniqueId().toString());if(section==null)return;
        for(String id:new ArrayList<>(section.getKeys(false))){
            String key=player.getUniqueId()+"."+id;
            if(!"pending".equals(data.getString(key+".state")))continue;
            ItemStack item=data.getItemStack(key+".item");
            if(item==null||!InventoryCapacity.fits(player,item,item.getAmount())){plugin.msg(player,Lang.text("trade-returns.make-inventory-space-and-use-trade-claim-for-returned-items", "&eMake inventory space and use /trade claim for returned items."));continue;}
            // An interrupted physical delivery remains held for review instead of automatic duplication.
            data.set(key+".state","delivering");save();
            player.getInventory().addItem(item.clone());
            data.set(key,null);save();
        }
    }
}


===== src/main/java/com/donsup/util/InventoryCapacity.java =====

package com.donsup.util;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

public final class InventoryCapacity {
    /** Simulates a complete reward against storage slots without changing the inventory. */
    public static boolean fitsBatch(Player player, java.util.List<ItemStack> items) {
        return fitsBatch(com.donsup.compat.BukkitCompat.storage(player.getInventory()), items);
    }
    public static boolean fitsBatch(ItemStack[] contents, java.util.List<ItemStack> items) {
        ItemStack[] slots = new ItemStack[contents.length];
        for (int i = 0; i < slots.length; i++) slots[i] = contents[i] == null ? null : contents[i].clone();
        for (ItemStack item : items) {
            if (item == null || com.donsup.compat.BukkitCompat.air(item.getType()) || item.getAmount() <= 0) continue;
            int remaining = item.getAmount();
            for (ItemStack slot : slots) {
                if (slot == null || !slot.isSimilar(item)) continue;
                int added = Math.min(remaining, Math.max(0, item.getMaxStackSize() - slot.getAmount()));
                slot.setAmount(slot.getAmount() + added);
                remaining -= added;
            }
            for (int i = 0; remaining > 0 && i < slots.length; i++) {
                if (slots[i] != null && !com.donsup.compat.BukkitCompat.air(slots[i].getType())) continue;
                int added = Math.min(remaining, item.getMaxStackSize());
                slots[i] = item.clone(); slots[i].setAmount(added); remaining -= added;
            }
            if (remaining > 0) return false;
        }
        return true;
    }
    public static boolean fits(Player player, ItemStack item, int amount) {
        long free = 0;
        for (ItemStack slot : com.donsup.compat.BukkitCompat.storage(player.getInventory())) {
            if (slot == null || com.donsup.compat.BukkitCompat.air(slot.getType())) free += item.getMaxStackSize();
            else if (slot.isSimilar(item)) free += Math.max(0, item.getMaxStackSize() - slot.getAmount());
        }
        return amount >= 0 && free >= amount;
    }
    public static void give(Player player, ItemStack template, int amount) {
        while (amount > 0) {
            int count = Math.min(amount, template.getMaxStackSize());
            ItemStack item = template.clone(); item.setAmount(count);
            player.getInventory().addItem(item); amount -= count;
        }
    }
}


===== src/main/java/com/donsup/util/ItemUtil.java =====

package com.donsup.util;

import org.bukkit.Material;
import com.donsup.compat.ItemKey;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.util.ArrayList;
import java.util.List;

public final class ItemUtil {
    private ItemUtil() {
    }

    public static ItemStack button(Material material, String name, List<String> lore, ItemKey actionKey, String action) {
        ItemStack item = new ItemStack(material == null ? Material.STONE : material);
        ItemMeta meta = item.getItemMeta();
        meta.setDisplayName(Text.color(name));
        if (lore != null && !lore.isEmpty()) {
            List<String> colored = new ArrayList<>();
            for (String line : lore) {
                colored.add(Text.color(line));
            }
            meta.setLore(colored);
        }
        if (action != null && !action.isBlank()) {
            com.donsup.compat.ItemTags.setString(meta, actionKey, action);
        }
        item.setItemMeta(meta);
        return item;
    }

    public static ItemStack named(Material material, int amount, String name, List<String> lore) {
        ItemStack item = new ItemStack(material == null ? Material.STONE : material, Math.max(1, amount));
        ItemMeta meta = item.getItemMeta();
        meta.setDisplayName(Text.color(name));
        if (lore != null && !lore.isEmpty()) {
            List<String> colored = new ArrayList<>();
            for (String line : lore) {
                colored.add(Text.color(line));
            }
            meta.setLore(colored);
        }
        item.setItemMeta(meta);
        return item;
    }

    public static Material material(String input, Material fallback) {
        if (input == null) {
            return fallback;
        }
        try {
            Material material = com.donsup.compat.Materials.match(input);
            return material == null ? fallback : material;
        } catch (IllegalArgumentException ex) {
            return fallback;
        }
    }
}


===== src/main/java/com/donsup/util/MoneyInput.java =====

package com.donsup.util;

import com.donsup.config.Lang;
public final class MoneyInput {
    private MoneyInput() {}
    public static double positiveMoney(String value) {
        try { double amount=Double.parseDouble(value);if(Double.isFinite(amount)&&amount>0&&amount<=1.0e12)return amount; }
        catch(NumberFormatException ignored){}
        throw new IllegalArgumentException(Lang.text("money-input.enter-a-finite-price-between-0-and-1-trillion", "Enter a finite price between 0 and 1 trillion."));
    }
}


===== src/main/java/com/donsup/util/RandomBounded.java =====

package com.donsup.util;

import java.util.Random;

/** Rejection sampling using only Java 8's unbounded Random API. */
public final class RandomBounded {
    private RandomBounded() {}
    public static long nextLong(Random random,long bound) {
        if(bound<=0) throw new IllegalArgumentException("Bound must be positive");
        long bits, value;
        do { bits=random.nextLong()>>>1; value=bits%bound; } while(bits-value+(bound-1)<0);
        return value;
    }
}


===== src/main/java/com/donsup/util/SafeYaml.java =====

package com.donsup.util;

import org.bukkit.configuration.file.*;
import java.io.*;
import java.nio.file.*;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;

public final class SafeYaml {
    public static YamlConfiguration load(File file) {
        var yaml = new YamlConfiguration();
        if (!file.exists()) return yaml;
        try { yaml.load(file); return yaml; }
        catch (Exception ex) { throw new IllegalStateException("Could not read " + file + "; refusing to replace data", ex); }
    }
    public static void save(FileConfiguration yaml, File file) throws IOException {
        if (YamlBatch.stage(file, yaml.saveToString())) return;
        Path target = file.toPath(); Files.createDirectories(target.toAbsolutePath().getParent());
        Path temp = Files.createTempFile(target.toAbsolutePath().getParent(), file.getName(), ".tmp");
        try {
            // Flush the complete replacement before publishing its name. This is not a
            // cross-file transaction; callers still need receipts for multi-file work.
            try (FileChannel channel = FileChannel.open(temp, StandardOpenOption.WRITE, StandardOpenOption.TRUNCATE_EXISTING)) {
                ByteBuffer bytes = StandardCharsets.UTF_8.encode(yaml.saveToString());
                while (bytes.hasRemaining()) channel.write(bytes);
                channel.force(true);
            }
            try { Files.move(temp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE); }
            catch (AtomicMoveNotSupportedException ex) { Files.move(temp, target, StandardCopyOption.REPLACE_EXISTING); }
        } finally { Files.deleteIfExists(temp); }
    }
}


===== src/main/java/com/donsup/util/Text.java =====

package com.donsup.util;

import org.bukkit.ChatColor;
import org.bukkit.command.CommandSender;

public final class Text {
    private Text() {
    }

    public static String color(String input) {
        return ChatColor.translateAlternateColorCodes('&', input == null ? "" : input);
    }

    public static void send(CommandSender sender, String prefix, String message) {
        sender.sendMessage(color(prefix + message));
    }

    public static String money(double value) {
        if (value >= 1_000_000_000) {
            return com.donsup.config.Lang.text("currency.billions", "${0}b", decimal(value / 1_000_000_000D));
        }
        if (value >= 1_000_000) {
            return com.donsup.config.Lang.text("currency.millions", "${0}m", decimal(value / 1_000_000D));
        }
        if (value >= 1_000) {
            return com.donsup.config.Lang.text("currency.thousands", "${0}k", decimal(value / 1_000D));
        }
        return com.donsup.config.Lang.text("currency.units", "${0}", decimal(value));
    }

    private static String decimal(double value) { return String.format(java.util.Locale.ROOT, "%.2f", value); }
}


===== src/main/java/com/donsup/util/YamlBatch.java =====

package com.donsup.util;

import org.bukkit.configuration.file.YamlConfiguration;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Write-ahead commit for files in one plugin data directory. Replay precedes manager loading. */
public final class YamlBatch {
    private static final ThreadLocal<Map<Path,String>> CURRENT=new ThreadLocal<>();
    public static boolean active(){return CURRENT.get()!=null;}
    public static void begin(){if(active())throw new IllegalStateException("Nested file batch");CURRENT.set(new LinkedHashMap<>());}
    public static boolean stage(File file,String yaml){var writes=CURRENT.get();if(writes==null)return false;writes.put(file.toPath().toAbsolutePath().normalize(),yaml);return true;}
    public static Map<Path,String> end(){var writes=CURRENT.get();CURRENT.remove();return writes;}
    public static Path prepare(Path root,Map<Path,String> writes,YamlConfiguration payload) throws IOException {
        root=root.toAbsolutePath().normalize();int i=0;
        for(var entry:writes.entrySet()){
            Path target=entry.getKey().toAbsolutePath().normalize();
            if(!root.equals(target.getParent()))throw new IOException("Transaction target is outside the plugin directory: "+target);
            payload.set("files."+i+".name",target.getFileName().toString());payload.set("files."+i+".contents",entry.getValue());i++;
        }
        payload.set("files-applied",false);
        Path journal=root.resolve("transactions").resolve(UUID.randomUUID()+".yml");SafeYaml.save(payload,journal.toFile());return journal;
    }
    public static void apply(Path root,Path journal) throws IOException {
        var payload=SafeYaml.load(journal.toFile());if(payload.getBoolean("files-applied"))return;
        var files=payload.getConfigurationSection("files");
        if(files!=null)for(String key:files.getKeys(false)){
            String name=files.getString(key+".name","");
            if(!name.matches("[a-zA-Z0-9_-]+\\.yml"))throw new IOException("Invalid recovery target "+name);
            var yaml=new YamlConfiguration();try{yaml.loadFromString(files.getString(key+".contents",""));}catch(Exception e){throw new IOException("Invalid recovery YAML",e);}
            SafeYaml.save(yaml,root.resolve(name).toFile());
        }
        payload.set("files-applied",true);payload.set("files",null);SafeYaml.save(payload,journal.toFile());
    }
    public static List<Path> journals(Path root) throws IOException {
        Path folder=root.resolve("transactions");if(!Files.isDirectory(folder))return List.of();
        try(var paths=Files.list(folder)){return paths.filter(p->p.getFileName().toString().endsWith(".yml")).sorted().toList();}
    }
}


===== src/main/resources/config.yml =====

# Set to a preset ID before first start for automatic setup; later edits use /smp setup.
setup:
  preset: ''
  preserve-branding: true

branding:
  # One name feeds all default menu headings, tab, sidebar and chat prefix.
  # In game: /smp brand Your Server Name (admin). Pause-screen changes need a restart.
  server-name: 'Donut SMP All In One'
  display-name: '&6&l%server%'
  menu-title-prefix: '%server% | '
  tablist:
    enabled: true
    header: '&6&l%server%'
    footer: '&7/shop &8| &7/ah &8| &7/bounties &8| &7/crates'
  scoreboard:
    enabled: true
    title: '&6&l%server%'
    lines:
      - '&7%player%'
      - '&8&m------------'
      - '&fMoney: &a%money%'
      - '&fShards: &d%shards%'
      - '&fKills: &c%kills%'
      - '&fBounty: &6%bounty%'
      - '&8&m------------'
      - '&e/smp'

settings:
  online-shards: 1
  online-shards-interval-minutes: 10
  starting-money: 1000.0
  starting-shards: 0
  listing-tax-percent: 2.5
  max-auction-listings: 18
  max-market-listings: 18
  order-duration-hours: 24
  order-claim-hours: 90
  default-home-limit: 2
  premium-home-bonus: 3
  kill-shards: 0
  afk-shards-per-minute: 0
  premium-online-shards-per-minute: 0
  premium-listing-tax-percent: 0.5
  premium-listing-bonus: 18
  premium-sell-multiplier: 1.25
  premium-vault-rows: 3
  premium-bounty-radar: true
  premium-market-alerts: true
  premium-night-vision: true
  premium-shard-interest: 0.0
  premium-shard-interest-cap: 250
  premium-kit-cooldown-hours: 24
  premium-repair-cooldown-minutes: 60
  premium-feed-cooldown-minutes: 30
  premium-portable-workbench: true

premium-kit:
  DIAMOND: 4
  GOLDEN_APPLE: 8
  EXPERIENCE_BOTTLE: 32
  AMETHYST_SHARD: 16

dynamic-pricing:
  enabled: false
  min-multiplier: 0.50
  max-multiplier: 2.50
  buy-pressure-per-item: 0.003
  sell-pressure-per-item: 0.002
  decay-percent-per-hour: 8.0

duels:
  invite-timeout-seconds: 60
  allow-wagers: true
  restore-location-after-seconds: 2

drills:
  enabled: true
  tiers:
    basic:
      material: IRON_PICKAXE
      cost-shards: 500
      max-blocks: 16
      efficiency: 3
    advanced:
      material: DIAMOND_PICKAXE
      cost-shards: 1800
      max-blocks: 36
      efficiency: 5
    mythic:
      material: NETHERITE_PICKAXE
      cost-shards: 5000
      max-blocks: 72
      efficiency: 7

daily:
  money: 1000.0
  money-per-streak: 100.0
  shards: 25
  shards-per-streak: 2
  premium-multiplier: 1.5

player-warps:
  promote-cost: 2500.0

creator:
  placeable-crates: true
  protect-placed-crates: true
  default-shop-category-icon: CHEST
  ghost-preview: true
  ghost-preview-range: 6
  ghost-preview-ticks: 5

player-settings:
  keep_pearls_on_death: false
  public_chat: true
  private_messages: true
  payments: true
  duel_requests: true
  bounty_alerts: true
  market_alerts: true
  scoreboard: true
  night_vision: false
  friend_chat: true
  friend_notifications: true
  menu_sounds: true
  combat_alerts: true
  clear_weather: false
  personal_day: false
  teleport_requests: true
  friend_requests: true
  public_profile: true
  scoreboard_coordinates: false
  scoreboard_balance: true

sell-prices:
  COBBLESTONE: 0.25
  DIRT: 0.15
  OAK_LOG: 3.0
  SPRUCE_LOG: 3.0
  WHEAT: 2.0
  CARROT: 1.8
  POTATO: 1.8
  IRON_INGOT: 12.0
  GOLD_INGOT: 18.0
  DIAMOND: 150.0
  EMERALD: 80.0
  NETHERITE_INGOT: 2500.0
  ENDER_PEARL: 20.0
  BLAZE_ROD: 35.0
  GUNPOWDER: 8.0

shard-shop:
  sell_axe:
    icon: DIAMOND_AXE
    name: '&dCrystal Sell Axe'
    shards: 750
    sell-axe: true
    amount: 1
  spawner_token:
    icon: SPAWNER
    name: '&dSkeleton Spawner'
    shards: 500
    spawner-type: skeleton
    amount: 1
  common_key:
    icon: TRIPWIRE_HOOK
    name: '&aCommon Crate Key'
    shards: 100
    key-type: common
    amount: 1
  prime_key:
    icon: TRIPWIRE_HOOK
    name: '&bPrime Crate Key'
    shards: 350
    key-type: prime
    amount: 1

crate-system:
  # Set false to retain the legacy physical-key spinner. Saved choices remain claimable.
  account-keys: true
  keyall:
    enabled: false
    interval-seconds: 3600
    type: common
    amount: 1

crates:
  common:
    display: '&aCommon Crate'
    icon: CHEST
    rewards:
      steak:
        material: COOKED_BEEF
        amount: 32
        weight: 40
      money:
        money: 500
        material: GOLD_INGOT
        amount: 1
        weight: 35
      diamond:
        material: DIAMOND
        amount: 3
        weight: 15
      shards:
        shards: 50
        material: AMETHYST_SHARD
        amount: 1
        weight: 10
  prime:
    display: '&bPrime Crate'
    icon: ENDER_CHEST
    rewards:
      pearls:
        material: ENDER_PEARL
        amount: 16
        weight: 35
      money:
        money: 2500
        material: GOLD_BLOCK
        amount: 1
        weight: 25
      netherite:
        material: NETHERITE_INGOT
        amount: 1
        weight: 10
      shards:
        shards: 200
        material: AMETHYST_SHARD
        amount: 1
        weight: 30

custom-spawners:
  price-shards: 1500
  stack-requires-sneak: true
  drop-generation-seconds: 60
  stack-scaling-exponent: 0.82
  donut-style-curve:
    enabled: true
    asymptote: 1505.35
    multiplier: 0.39567
    decay: 0.00134606
    offset: 8.24358
  types:
    pig:
      name: '&dPig Spawner'
      entity: PIG
      icon: PORKCHOP
      drops:
        PORKCHOP: 7
    cow:
      name: '&dCow Spawner'
      entity: COW
      icon: BEEF
      drops:
        BEEF: 7
    spider:
      name: '&dSpider Spawner'
      entity: SPIDER
      icon: STRING
      drops:
        STRING: 5
        SPIDER_EYE: 2
    zombie_pigman:
      name: '&dZombie Pigman Spawner'
      entity: ZOMBIFIED_PIGLIN
      icon: GOLD_NUGGET
      drops:
        GOLD_NUGGET: 9
    skeleton:
      name: '&dSkeleton Spawner'
      entity: SKELETON
      icon: BONE
      drops:
        BONE: 7
        ARROW: 3
    blaze:
      name: '&dBlaze Spawner'
      entity: BLAZE
      icon: BLAZE_POWDER
      drops:
        BLAZE_POWDER: 5
    creeper:
      name: '&dCreeper Spawner'
      entity: CREEPER
      icon: GUNPOWDER
      drops:
        GUNPOWDER: 6
    iron_golem:
      name: '&dIron Golem Spawner'
      entity: IRON_GOLEM
      icon: IRON_INGOT
      drops:
        IRON_INGOT: 4

messages:
  prefix: '&6&l%server% &8>> &f'

# Additional all-in-one systems.
chest-shops:
  holograms: true
  enabled: true
  max-per-player: 20
travel:
  # Local geographic regions. Enable and adjust bounds to your world.
  zones:
    frontier:
      enabled: false
      label: Frontier
      region: Northern Wilds
      dimension: overworld
      permission: ''
      min-x: -5000
      max-x: 5000
      min-z: 1000
      max-z: 5000
  warmup-seconds: 3
  rtp-cooldown-seconds: 15
  rtp-radius: 5000
  rtp-world: ''
  max-concurrent-searches: 8
  dimensions:
    overworld:
      enabled: true
      world: ''
    nether:
      enabled: true
      world: ''
    end:
      enabled: true
      world: ''
  queue:
    enabled: true
    timeout-seconds: 120
    max-players: 200
combat:
  tag-seconds: 15
  kill-on-logout: false
market:
  match-orders: true
ranks:
  plus:
    home-bonus: 3
    listing-bonus: 18
  elite:
    home-bonus: 6
    listing-bonus: 36
  legend:
    home-bonus: 10
    listing-bonus: 54
server-rules:
  - 'Respect other players and server staff.'
  - 'No hacked clients, exploits, duplication or harassment.'
  - 'Survival PvP and raiding are enabled. Protect your valuables.'

quick-buy:
  max-saved-lists: 24
pearls:
  # Manages the native pearl-death gamerule; restores it on shutdown.
  # The setting is hidden on versions without that gamerule.
  player-preferences: true


===== src/main/resources/dialogs.yml =====

# Text uses MiniMessage colors. Native Minecraft controls need no texture pack.
# /donsup reload reloads this file. The ESC entry is registered at server startup.
title: '<gold>%server%</gold>'
settings-title: 'Settings'
button-width: 300
categories:
  chat:
    label: '✉ Chat'
    description: 'Choose which conversations reach you.'
    settings: [public_chat, private_messages, friend_chat]
  notifications:
    label: '⌛ Notifications'
    description: 'Personal alerts and interface sounds.'
    settings: [market_alerts, bounty_alerts, friend_notifications, menu_sounds]
  pvp:
    label: '⚔ PvP'
    description: 'Duel requests and combat notifications. Survival PvP remains enabled.'
    settings: [duel_requests, combat_alerts, keep_pearls_on_death]
  visuals:
    label: '☀ Visuals'
    description: 'Personal visual preferences. Night vision requires premium.'
    settings: [night_vision, clear_weather, personal_day]
  privacy:
    label: '▣ Privacy'
    description: 'Control requests, payments and public profile access.'
    settings: [teleport_requests, friend_requests, payments, public_profile]
  scoreboard:
    label: '▤ Scoreboard'
    description: 'Choose what appears on your sidebar.'
    settings: [scoreboard, scoreboard_coordinates, scoreboard_balance]
labels:
  keep_pearls_on_death: 'Keep thrown pearls after death'
  public_chat: 'Public chat'
  private_messages: 'Private messages'
  friend_chat: 'Friends chat'
  market_alerts: 'Market alerts'
  bounty_alerts: 'Bounty alerts'
  friend_notifications: 'Friend join alerts'
  menu_sounds: 'Menu sounds'
  duel_requests: 'Duel requests'
  combat_alerts: 'Combat tag alerts'
  night_vision: 'Night vision (premium)'
  clear_weather: 'Clear weather'
  personal_day: 'Always daytime'
  teleport_requests: 'Teleport requests'
  friend_requests: 'Friend requests'
  payments: 'Incoming payments'
  public_profile: 'Public statistics'
  scoreboard: 'Show scoreboard'
  scoreboard_coordinates: 'Show coordinates'
  scoreboard_balance: 'Show money and shards'


===== src/main/resources/language-names.yml =====

# Display names only. Keep the IDs on the left unchanged.
# Add materials from language-names-reference.yml (generated for your server version).
# Vanilla item names shown by Minecraft itself follow each player's client language.
# Examples for French: DIAMOND: "Diamant", true: "oui", false: "non".
materials:
  DIAMOND: "DIAMOND"
states:
  'true': 'true'
  'false': 'false'
dimensions:
  overworld: 'overworld'
  nether: 'nether'
  end: 'end'
modes:
  buy: 'buy'
  sell: 'sell'
stats:
  money: 'money'
  shards: 'shards'
  kills: 'kills'
  deaths: 'deaths'
  bounty: 'bounty'
settings:
  public_chat: 'Public Chat'
  private_messages: 'Private Messages'
  payments: 'Payments'
  duel_requests: 'Duel Requests'
  bounty_alerts: 'Bounty Alerts'
  market_alerts: 'Market Alerts'
  scoreboard: 'Scoreboard'
  night_vision: 'Night Vision'
  coordinate_spoof: 'Coordinate Spoof'
  mob_spawn_hints: 'Mob Spawn Hints'

# Generated menu labels; add a built-in ID here to override its displayed name.
labels:
  public_chat: "Public Chat"
  private_messages: "Private Messages"
  payments: "Payments"
  duel_requests: "Duel Requests"
  bounty_alerts: "Bounty Alerts"
  market_alerts: "Market Alerts"
  scoreboard: "Scoreboard"
  night_vision: "Night Vision"
  coordinate_spoof: "Coordinate Spoof"
  mob_spawn_hints: "Mob Spawn Hints"
  money: "Money"
  shards: "Shards"
  kills: "Kills"
  deaths: "Deaths"
  bounty: "Bounty"
  common: "Common"
  rare: "Rare"
  epic: "Epic"
  legendary: "Legendary"
  basic: "Basic"
  advanced: "Advanced"
  elite: "Elite"
  pig: "Pig"
  cow: "Cow"
  chicken: "Chicken"
  zombie: "Zombie"
  skeleton: "Skeleton"
  creeper: "Creeper"
  iron_golem: "Iron Golem"
  zombified_piglin: "Zombified Piglin"
  blaze: "Blaze"
  enderman: "Enderman"

# Command help descriptions; restart the server after editing this section.
commands:
  "chestshop": "Create and manage physical player shops with native trade confirmations."
  "smp": "Open the SMP control center."
  "shop": "Quick Buy from live auctions."
  "quickbuy": "Quick Buy from live auctions."
  "servershop": "Open the optional fixed-price server shop."
  "sell": "Sell plain items, exact items to orders, or held shulker contents."
  "ah": "Open or list in the auction house."
  "orders": "Create, deliver or claim plain-material and exact-item orders."
  "market": "Open the player market GUI."
  "shards": "Open the shard shop."
  "crates": "Open the crate GUI."
  "keys": "View keys, resume rewards, redeem physical keys or administer key grants."
  "keyall": "Give account keys to every online player (admin)."
  "homes": "Open the homes GUI."
  "sethome": "Set a home."
  "home": "Teleport to a home."
  "delhome": "Delete a home."
  "bounty": "Open or create bounties."
  "bounties": "Open the bounty board."
  "pay": "Pay another player."
  "balance": "View your money and shards."
  "bal": "View your money and shards."
  "afk": "Toggle AFK shard earning."
  "settings": "Open the player settings GUI."
  "profile": "Open your profile GUI."
  "premium": "Open the premium perks GUI."
  "pvault": "Open the premium vault."
  "nightvision": "Toggle premium night vision."
  "spawners": "Open the custom spawner shop."
  "creator": "Open the SMP creator toolkit."
  "leaderboard": "Open SMP leaderboards."
  "premiumkit": "Claim premium kit."
  "repair": "Premium repair held item."
  "feed": "Premium feed utility."
  "workbench": "Premium portable crafting table."
  "duel": "Challenge players, accept duels and manage duel arenas."
  "drills": "Open vein miner drill shop."
  "drill": "Drill admin/player command."
  "veinminer": "Open vein miner drill shop."
  "team": "Teams and clans."
  "clan": "Clan alias for teams."
  "pwarp": "Player warps GUI and commands."
  "trade": "Safe player trading."
  "kit": "Claim kits."
  "kits": "Open kits GUI."
  "kitadmin": "Admin kit builder."
  "daily": "Daily rewards and streaks."
  "mod": "Staff moderation tools."
  "report": "Report a player."
  "prices": "Auction and market price history."
  "friends": "Open friends and requests."
  "friend": "Add, accept, deny or remove a friend."
  "friendchat": "Chat with friends."
  "follow": "Follow a player."
  "following": "View followed players."
  "unfollow": "Unfollow a player."
  "msg": "Private message a player."
  "reply": "Reply to a private message."
  "ignore": "Block messages and requests from a player."
  "rtp": "Select an RTP dimension, travel solo, or queue with a partner."
  "rtpqueue": "Join a paired RTP queue or leave it."
  "tpa": "Request teleport to another player."
  "tpahere": "Ask another player to teleport to you."
  "tpaccept": "Accept a teleport request."
  "tpdeny": "Decline a teleport request."
  "spawn": "Teleport to spawn."
  "setspawn": "Set server spawn (admin)."
  "stats": "View player statistics."
  "sellhistory": "View your sale history."
  "worth": "Check the held item's server value."
  "baltop": "View economy leaderboards."
  "trash": "Discard unwanted items."
  "rules": "Read server rules."


===== src/main/resources/language.yml =====

# LANGUAGE / TRANSLATION — UTF-8 (French accents supported)
# Edit the text on the RIGHT. Keep keys and numbered {0}, {1}, ... placeholders.
# You may reorder or repeat placeholders. An empty value "" hides chat feedback.
# Apply with /donsup reload, then reopen menus. Invalid edits keep the last good language.
# Existing menus.yml/messages.yml edits continue to work while these values stay unchanged.
# Other editable presentation: menus.yml, dialogs.yml, config.yml, shops.yml, language-names.yml.
# Missing keys use English. language-defaults.yml is refreshed as an upgrade reference.
# Use the wiki visual editor to search English wording and edit without writing YAML.
text:
  afk-reward-listener:
    "afk-rewards-disabled-because-you-moved": "&cAFK rewards disabled because you moved."
  branding-listener:
    "bounty-bounty": "&7Bounty: &6%bounty%"
    "kills-kills": "&7Kills: &c%kills%"
    "money-money": "&7Money: &a%money%"
    "shards-shards": "&7Shards: &d%shards%"
    "smp": "&8/smp"
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    # {2}: dynamic value (keep this placeholder)
    "xyz": "&7XYZ: &f{0} {1} {2}"
  chest-shop:
    # {0}: count
    "acknowledged-reviewed-trades-no-items-or-money-were-replayed": "&aAcknowledged {0} reviewed trades. No items or money were replayed."
    "active": "active"
    "amount-must-be-a-whole-number-from-1-to-2304": "Amount must be a whole number from 1 to 2304."
    # {0}: operation
    "at-player-shop": "{0} at Player Shop"
    "attach-the-sign-to-your-chest-or-barrel": "Attach the sign to your chest or barrel."
    "both-halves-must-be-available-in-your-current-region": "&cBoth halves must be available in your current region."
    "bought": "Bought "
    "bought-5e5f7a": " bought "
    "buy": "Buy"
    # {0}: player name
    # {1}: dynamic value (keep this placeholder)
    # {2}: dynamic value (keep this placeholder)
    # {3}: formatted amount
    "chest-shop-items-for": "&bChest shop: &f{0}{1}{2} items for {3}."
    "chest-shop-trading-is-blocked-during-combat-or-a-duel": "&cChest-shop trading is blocked during combat or a duel."
    "chest-shops-are-disabled": "&cChest shops are disabled."
    "chestshop-create": "&e/chestshop create <buy|sell> <amount> <total price>"
    "chestshop-create-list-info-stock-price-pause-resume-remove-histor": "&e/chestshop create|list|info|stock|price|pause|resume|remove|history"
    "chestshop-price": "&e/chestshop price <total per batch>"
    "chestshop-resolve-acknowledge-after-auditing-its-items-and-paymen": "&e/chestshop resolve <shopId> acknowledge &7after auditing its items and payment."
    "close-the-container-before-creating-a-shop": "&cClose the container before creating a shop."
    # {0}: dynamic value (keep this placeholder)
    # {1}: amount
    # {2}: item/material display name
    # {3}: formatted amount
    "created-shop-x-for-per-batch": "&aCreated {0} shop: {1}x {2} for {3} per batch."
    "hold-the-exact-item-you-want-this-shop-to-trade-your-sample-is-ke": "&cHold the exact item you want this shop to trade. Your sample is kept."
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    # {2}: formatted amount
    "items-for": "&a{0}{1} items for {2}."
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    # {2}: formatted amount
    # {3}: dynamic value (keep this placeholder)
    "items-trade": "&7{0} &f{1} items &a{2} &7trade {3}"
    "leave-a-gap-beside-shop-containers-merging-them-is-blocked": "&cLeave a gap beside shop containers; merging them is blocked."
    "look-at-a-chest-double-chest-or-barrel-within-five-blocks": "&cLook at a chest, double chest or barrel within five blocks."
    "look-at-a-registered-shop-chest-or-barrel": "&cLook at a registered shop chest or barrel."
    "no-permission": "&cNo permission."
    "not-enough-matching-stock-or-inventory-space-for-the-complete-bat": "&cNot enough matching stock or inventory space for the complete batch."
    "only-the-owner-can-attach-a-shop-sign": "Only the owner can attach a shop sign."
    "only-the-owner-or-an-administrator-can-change-this-shop": "&cOnly the owner or an administrator can change this shop."
    "open-your-chest-normally-to-manage-stock-other-players-get-a-purc": "&7Open your chest normally to manage stock. Other players get a purchase confirmation."
    "paused": "paused"
    "payment-could-not-be-completed-no-items-were-moved": "&cPayment could not be completed. No items were moved."
    "place-a-chest-or-barrel-hold-the-item-to-trade-then-use-chestshop": "Place a chest or barrel, hold the item to trade, then use:\n/chestshop create sell &lt;amount&gt; &lt;price&gt;\n/chestshop create buy &lt;amount&gt; &lt;price&gt;\nSell: players buy your stock. Buy: you pay players for their items.\nRight-click another player's shop to confirm a trade.\n/chestshop list, info, stock, price, pause, resume, remove, history"
    "place-a-new-chest-or-barrel-yourself-before-creating-a-shop": "&cPlace a new chest or barrel yourself before creating a shop."
    "player-chest-shops": "Player Chest Shops"
    "price-must-be-0-01-to-1-000-000-000-with-at-most-two-decimal-plac": "Price must be 0.01 to 1,000,000,000 with at most two decimal places."
    "put-a-sample-item-in-the-chest-or-write-its-material-on-line-four": "Put a sample item in the chest, or write its material on line four."
    "refund-cannot-be-funded-staff-review-required": "Refund cannot be funded; staff review required"
    "remove-the-container-s-existing-lock-first": "&cRemove the container's existing lock first."
    "remove-this-shop-with-chestshop-remove-before-breaking-its-contai": "&cRemove this shop with /chestshop remove before breaking its container."
    "right-click": "Right-click"
    "sell": "Sell"
    "shop": "&b[Shop]"
    # {0}: dynamic value (keep this placeholder)
    "shop-d": "&aShop {0}d."
    # {0}: dynamic value (keep this placeholder)
    # {1}: player name
    "shop-owner": "&bShop {0} &7Owner: {1}"
    "shop-price-updated-earlier-confirmations-are-now-invalid": "&aShop price updated. Earlier confirmations are now invalid."
    "shop-removed-its-stock-stays-in-the-container": "&aShop removed. Its stock stays in the container."
    "sign-shop-sell-64-or-buy-64-total-price-material-or-blank-for-che": "Sign: [Shop] / sell 64 (or buy 64) / total price / material or blank for chest stock."
    "sold": "Sold "
    "sold-95037f": " sold "
    "stand-close-to-the-original-shop-container": "&cStand close to the original shop container."
    # {0}: error details
    "text": "&c{0}"
    "that-container-already-belongs-to-a-shop-or-crate": "&cThat container already belongs to a shop or crate."
    "the-container-changed-try-again": "The container changed. Try again."
    "the-original-shop-container-is-unavailable": "&cThe original shop container is unavailable."
    "the-owner-is-managing-stock-try-again-after-they-close-the-contai": "&cThe owner is managing stock. Try again after they close the container."
    "the-paying-account-does-not-have-enough-money": "&cThe paying account does not have enough money."
    "the-shop-operation-could-not-finish-staff-can-inspect-chest-shops": "&cThe shop operation could not finish. Staff can inspect chest-shops.yml and any pending shop payment before resolving it."
    "this-shop-has-an-interrupted-trade-requiring-staff-review": "&cThis shop has an interrupted trade requiring staff review."
    "this-shop-is-awaiting-staff-review-of-an-interrupted-trade": "&cThis shop is awaiting staff review of an interrupted trade."
    "this-shop-is-paused": "&cThis shop is paused."
    "this-shop-needs-staff-review-before-stock-can-change": "&cThis shop needs staff review before stock can change."
    "this-shop-offer-changed-right-click-it-for-a-new-price": "&cThis shop offer changed. Right-click it for a new price."
    "unknown-item-material": "Unknown item material."
    "use-chest-shop-commands-in-game": "&cUse chest-shop commands in game."
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    # {2}: dynamic value (keep this placeholder)
    # {3}: item/material display name
    # {4}: formatted amount
    # {5}: dynamic value (keep this placeholder)
    # {6}: dynamic value (keep this placeholder)
    # {7}: dynamic value (keep this placeholder)
    "x-at": "&7{0} &f{1} {2}x {3} &a{4} &7at {5}, {6}, {7}"
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    # {2}: item/material display name
    # {3}: formatted amount
    # {4}: status
    "x-per-batch": "&f{0} {1}x {2} &a{3} &7per batch; {4}"
    # {0}: operation
    # {1}: dynamic value (keep this placeholder)
    # {2}: dynamic value (keep this placeholder)
    # {3}: formatted amount
    # {4}: player name
    # {5}: count
    "x-total-owner-matching-stock-the-price-is-for-the-complete-batch": "{0} {1}x {2}\nTotal: {3}\nOwner: {4}\nMatching stock: {5}\nThe price is for the complete batch. Item properties must match exactly."
    # {0}: dynamic value (keep this placeholder)
    "you-have-reached-your-chest-shop-limit-of": "&cYou have reached your chest-shop limit of {0}."
    "you-must-own-both-unlocked-halves-of-this-chest": "&cYou must own both unlocked halves of this chest."
    # {0}: count
    "your-chest-shops": "&bYour chest shops: {0}"
  combat-reward-listener:
    # {0}: player name
    # {1}: player name
    "bounty-radar-defeated": "&cBounty radar: &e{0} &7defeated &f{1}&7."
    # {0}: player name
    # {1}: formatted amount
    "claimed-bounty-on-for": "&aClaimed bounty on &e{0}&a for {1}."
    # {0}: shard amount
    # {1}: player name
    "shards-for-defeating": "&d+{0} shards &7for defeating &e{1}&7."
  command-registration:
    "no-permission": "&cNo permission."
  crate:
    # {0}: type
    # {1}: dynamic value (keep this placeholder)
    "account-keys": "&b{0}: &f{1} account keys"
    "account-keys-are-disabled": "&cAccount keys are disabled."
    # {0}: dynamic value (keep this placeholder)
    "amount": "&7Amount: {0}"
    "choose-one-of-seven": "&bChoose one of seven"
    "choose-this-reward-you-receive-one-choice": "&aChoose this reward. You receive ONE choice."
    # {0}: dynamic value (keep this placeholder)
    "claimed-crate-reward": "&aClaimed crate reward: {0}."
    "close-and-resume-with-keys-claim": "&7Close and resume with /keys claim."
    "could-not-complete-the-crate-operation-your-saved-choice-may-need": "&cCould not complete the crate operation. Your saved choice may need staff review; check the server log."
    # {0}: amount
    # {1}: dynamic value (keep this placeholder)
    # {2}: player name
    "gave-keys-to": "&aGave {0} {1} keys to {2}."
    # {0}: amount
    # {1}: dynamic value (keep this placeholder)
    # {2}: count
    "granted-keys-to-online-players": "&aGranted {0} {1} keys to {2} online players."
    "hold-a-valid-physical-crate-key-to-redeem-it": "&cHold a valid physical crate key to redeem it."
    # {0}: dynamic value (keep this placeholder)
    "interrupted-delivery-resolved": "&aInterrupted delivery resolved: {0}."
    "invalid-type-amount-or-key-balance-limit-amount-must-be-1-to-1-00": "&cInvalid type, amount or key balance limit. Amount must be 1 to 1,000,000."
    "key-all-requires-account-keys-to-be-enabled": "&cKey-all requires account keys to be enabled."
    # {0}: amount
    # {1}: type
    "key-all-you-received-keys": "&bKey-all! &fYou received {0} {1} keys."
    "keyall": "&e/keyall <crate> <amount>"
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    "keys": "&7Keys: {0} {1}"
    "keys-give": "&e/keys give <player> <crate> <amount>"
    "keys-give-or-keyall": "&e/keys give <player> <crate> <amount> or /keyall <crate> <amount>"
    "keys-open-claim-redeem": "&e/keys [open <crate>|claim|redeem]"
    "keys-resolve-after-checking-an-interrupted-delivery": "&e/keys resolve <player> <refund|complete> &7after checking an interrupted delivery."
    "make-inventory-space-first-your-choices-are-saved": "&cMake inventory space first. Your choices are saved."
    # {0}: dynamic value (keep this placeholder)
    "money": "&7Money: &a{0}"
    "no-interrupted-delivery-to-resolve": "&cNo interrupted delivery to resolve."
    "no-permission": "&cNo permission."
    "no-saved-choice-open-a-crate-using-crates": "&eNo saved choice. Open a crate using /crates."
    "physical-keys-granted": "&aPhysical keys granted."
    "physical-keys-need-an-online-player-with-inventory-space": "&cPhysical keys need an online player with inventory space."
    "physical-keys-need-inventory-space": "&cPhysical keys need inventory space."
    "recovered-the-saved-account-reward-no-key-refund-was-issued": "&aRecovered the saved account reward. No key refund was issued."
    "recovered-your-interrupted-account-reward": "&aRecovered your interrupted account reward."
    # {0}: count
    # {1}: type
    "redeemed-account-keys": "&aRedeemed {0} {1} account keys."
    "repeated-rewards-are-possible": "&7Repeated rewards are possible."
    # {0}: shard amount
    "shards": "&7Shards: &d{0}"
    # {0}: dynamic value (keep this placeholder)
    "text": "&e{0}"
    "that-player-must-have-joined-this-server-before": "&cThat player must have joined this server before."
    "this-crate-has-no-rewards-available-on-this-server-version-your-k": "&cThis crate has no rewards available on this server version. Your key was kept."
    "this-crate-has-no-rewards-configured": "&cThis crate has no rewards configured."
    "this-reward-would-exceed-your-balance-limit-your-choice-is-still": "&cThis reward would exceed your balance limit. Your choice is still saved."
    "unknown-crate-or-account-keys-are-disabled": "&cUnknown crate or account keys are disabled."
    "you-have-a-saved-reward-choice-use-keys-claim": "&eYou have a saved reward choice. Use /keys claim."
    # {0}: type
    "you-need-a-account-key-hold-an-old-physical-key-and-use-keys-rede": "&cYou need a {0} account key. Hold an old physical key and use /keys redeem to convert it."
    "your-key-balance-is-full-choose-another-reward-or-use-some-keys-f": "&cYour key balance is full. Choose another reward or use some keys first."
    "your-key-was-spent-once": "&7Your key was spent once."
    "your-previous-reward-delivery-was-interrupted-ask-staff-to-review": "&cYour previous reward delivery was interrupted. Ask staff to review it before opening another crate."
  creator:
    "1-rename-smp-brand-your-server-name": "&71. Rename: /smp brand Your Server Name"
    "2-use-config-studio-for-bulk-edits": "&72. Use Config Studio for bulk edits."
    "3-click-reload-in-creator-hub": "&73. Click reload in Creator Hub."
    "add-custom-command-here": "&aAdd Custom Command Here"
    "add-held-item": "&aAdd Held Item"
    "add-held-item-here": "&aAdd Held Item Here"
    "add-held-item-to-kit": "&aAdd Held Item To Kit"
    # {0}: item/material display name
    # {1}: category
    # {2}: id
    "added-to-shop-as": "&aAdded &e{0} &ato shop &e{1}&a as &e{2}&a."
    # {0}: amount
    # {1}: item/material display name
    "added-x-to-the-premium-kit": "&aAdded &e{0}x {1} &ato the premium kit."
    # {0}: dynamic value (keep this placeholder)
    "amount": "&7Amount: &e{0}"
    # {0}: dynamic value (keep this placeholder)
    "applied-preset-backups-were-created": "&aApplied preset &e{0}&a. Backups were created."
    "apply-a-full-economy-preset": "Apply a full economy preset."
    "apply-presets-from-a-gui": "&7Apply presets from a GUI."
    "apply-the-bundled-smp-config-and-shops": "&7Apply the bundled SMP config and shops."
    "automatic-backups-and-rollback-included": "&7Automatic backups and rollback included."
    "back": "&7Back"
    "backups-are-made-automatically": "&7Backups are made automatically."
    "bind-commands-like-crates-to-physical-areas": "Bind commands like /crates to physical areas."
    "bonus-homes": "Bonus Homes"
    "bounty-radar": "Bounty Radar"
    "branding": "Branding"
    "build-the-server-from-in-game": "&7Build the server from in-game."
    "built-in-scoreboard-and-tablist-branding-are-enabled": "Built-in scoreboard and tablist branding are enabled."
    "bundled-competitive-preset-config-yml": "&7Bundled competitive preset config.yml"
    "bundled-competitive-preset-shops-yml": "&7Bundled competitive preset shops.yml"
    "bundled-donutsmp-style-preset-files": "&7Bundled DonutSMP-style preset files"
    # {0}: formatted amount
    "buy": "&7Buy: &a{0}"
    "buy-pressure-raises-prices": "&7Buy pressure raises prices."
    "buy-sell-and-amount-must-be-numbers": "&cBuy, sell and amount must be numbers."
    "cancel": "&cCancel"
    # {0}: error details
    "cannot-install-this-preset": "&cCannot install this preset: {0}"
    "category-id-buy-sell-amount": "&fcategory id buy sell amount"
    "check-branding-shops-crates-spawners": "&7Check branding, shops, crates, spawners,"
    "choose-a-style-preview-changes-then-install": "&7Choose a style, preview changes, then install."
    "click-and-type-an-amount-in-chat": "&7Click and type an amount in chat."
    "click-for-file-paths-and-workflow": "&7Click for file paths and workflow."
    "click-for-guided-setup": "&7Click for guided setup."
    "click-get-placer-block": "&7Click: get placer block."
    "click-once-to-set-up-the-smp": "&aClick once to set up the SMP."
    "click-the-anvil-to-add-it-with-a-guided-prompt": "&7Click the anvil to add it with a guided prompt."
    "click-the-anvil-to-add-your-held-item-here": "&7Click the anvil to add your held item here."
    "click-to-apply-use-rollback-to-undo": "&7Click to apply. Use rollback to undo."
    "click-to-choose-a-crate-type": "&7Click to choose a crate type."
    "click-to-choose-type-and-amount": "&7Click to choose type and amount."
    "click-to-configure": "&aClick to configure."
    "click-to-edit": "&aClick to edit."
    "click-to-edit-this-category": "&aClick to edit this category."
    "click-to-preview": "&aClick to preview"
    "click-to-toggle": "&7Click to toggle."
    "click-to-toggle-4ce56f": "&aClick to toggle."
    "click-toggles-to-enable-or-disable-features": "&7Click toggles to enable or disable features."
    "click-values-to-edit-them-in-chat": "&7Click values to edit them in chat."
    # {0}: dynamic value (keep this placeholder)
    "command-now-teleports-to-your-current-location": "&aCommand &e/{0} &anow teleports to your current location."
    "command-teleports": "&bCommand Teleports"
    "command-teleports-af9c9f": "Command Teleports"
    "command-teleports-c3356d": "&b&lCommand Teleports"
    "competitive-smp": "Competitive SMP"
    # {0}: dynamic value (keep this placeholder)
    "config": "&7Config: &f{0}"
    "config-studio": "&bConfig Studio"
    "config-studio-0a8581": "&b&lConfig Studio"
    "config-yml": "&7config.yml"
    "configure-spawner-price-speed-and-drops": "&7Configure spawner price, speed and drops."
    # {0}: error details
    "could-not-apply-preset": "&cCould not apply preset: {0}"
    "could-not-grant-keys-check-the-type-amount-and-inventory-space": "&cCould not grant keys. Check the type, amount and inventory space."
    # {0}: dynamic value (keep this placeholder)
    "crate-placer": "&6{0} Crate Placer"
    "crate-rewards": "Crate Rewards"
    # {0}: type
    "crate-type": "&8Crate type: {0}"
    "create-crate-blocks-players-can-click": "&7Create crate blocks players can click."
    "create-or-review-player-shop-categories": "Create or review player shop categories."
    "creates-backups-before-changing-files": "&7Creates backups before changing files."
    "creator-prompt-cancelled": "&cCreator prompt cancelled."
    "creator-tools-require-donsup-admin": "&cCreator tools require &edonsup.admin&c."
    # {0}: configured value
    "current": "&7Current: &f{0}"
    # {0}: value
    # {1}: dynamic value (keep this placeholder)
    "current-f6e1d7": "&7Current: &f{0}{1}"
    "curve-cap": "Curve Cap"
    "daily-rewards-kits-and-afk-shards-are-available": "Daily rewards, kits and AFK shards are available."
    "decay": "&eDecay"
    # {0}: dynamic value (keep this placeholder)
    "deleted-teleport-route": "&cDeleted teleport route &e/{0}&c."
    "dialogs-yml": "&7dialogs.yml"
    "disabled": "&cDisabled"
    "disabled-381605": "&cdisabled"
    "donutsmp-style": "DonutSMP Style"
    "drop-interval": "Drop Interval"
    # {0}: dynamic value (keep this placeholder)
    "drops": "&7Drops: &f{0}"
    "dynamic-market": "&e&lDynamic Market"
    "dynamic-pricing": "&eDynamic Pricing"
    # {0}: status
    "dynamic-pricing-is-now": "&eDynamic pricing is now {0}&e."
    "edit-branding-menus-messages-and-gameplay-yaml": "&7Edit branding, menus, messages and gameplay YAML."
    "edit-exact-values-in-config-studio": "&7Edit exact values in Config Studio."
    "edit-generated-yaml-then-paste-save-into-plugin-configs": "&7Edit generated YAML, then paste/save into plugin configs."
    "edit-values-toggles-and-kit-items": "&7Edit values, toggles and kit items."
    "editable-files": "&fEditable Files"
    "enabled": "&aEnabled"
    "enabled-f8bd80": "&aenabled"
    # {0}: dynamic value (keep this placeholder)
    "entity": "&7Entity: &e{0}"
    "example-combat-pearls-480-18-16": "&8Example: combat pearls 480 18 16"
    "example-combat-pearls-480-18-16-type-cancel-to-stop": "&7Example: &fcombat pearls 480 18 16 &8| type &ccancel &8to stop."
    "example-crates-can-go-to-your-crate-room": "&7Example: /crates can go to your crate room."
    "example-crates-or-market-type-cancel-to-stop": "&7Example: &fcrates &8or &fmarket &8| type &ccancel &8to stop."
    "example-market-warps-keys": "&8Example: market, warps, keys"
    "example-pearls-480-18-16": "&8Example: pearls 480 18 16"
    "example-pearls-480-18-16-type-cancel-to-stop": "&7Example: &fpearls 480 18 16 &8| type &ccancel &8to stop."
    # {0}: category
    "existing-category-id": "&7Existing category id: &f{0}"
    "existing-material-entries-are-replaced": "&7Existing material entries are replaced."
    "exponent": "exponent"
    "extra-homes": "extra homes"
    "extra-listings": "extra listings"
    "feed-cooldown": "Feed Cooldown"
    "for-advanced-editing-use-the-web-editor": "&7For advanced editing, use the web editor:"
    "format-after-clicking": "&7Format after clicking:"
    "gave-crate-placer": "&aGave crate placer."
    # {0}: dynamic value (keep this placeholder)
    "gave-spawner": "&aGave &e{0} Spawner&a."
    # {0}: amount
    # {1}: dynamic value (keep this placeholder)
    "gave-x-crate-keys": "&aGave &e{0}x {1} &acrate keys."
    "give-keys-attached-to-a-crate-type": "&7Give keys attached to a crate type."
    "give-test-spawners-from-the-gui": "&7Give test spawners from the GUI."
    "green-means-ready-yellow-means-optional-setup": "&7Green means ready. Yellow means optional setup."
    "hold-an-item-and-add-it-to-a-shop": "&7Hold an item and add it to a shop."
    "hold-an-item-click-then-type-amount": "&7Hold an item, click, then type amount."
    "hold-item-click-then-type": "&7Hold item, click, then type:"
    "hold-the-item-this-spawner-should-generate": "&cHold the item this spawner should generate."
    "hold-the-item-you-want-to-add-before-starting-the-shop-builder": "&cHold the item you want to add before starting the shop builder."
    "hold-the-item-you-want-to-add-to-the-premium-kit": "&cHold the item you want to add to the premium kit."
    "hold-the-item-you-want-to-add-to-the-shop": "&cHold the item you want to add to the shop."
    "hold-the-item-you-want-to-sell": "&7Hold the item you want to sell."
    # {0}: configured value
    "hourly-decay": "&7Hourly decay: &e{0}%"
    "hours": "hours"
    "id-buy-sell-amount": "&fid buy sell amount"
    "install-preset": "&aInstall preset"
    "interest-cap": "Interest Cap"
    "invalid-command-name": "&cInvalid command name."
    "invalid-drop-material": "&cInvalid drop material."
    "invalid-kit-material": "&cInvalid kit material."
    "invalid-preset-manifest-check-preset-yml": "&7Invalid preset manifest; check preset.yml."
    "invalid-spawner-drop-prompt": "&cInvalid spawner drop prompt."
    # {0}: configured value
    "items": "&7Items: &e{0}"
    "items-min-cap": "items/min cap"
    "keys": "&bKeys"
    "keys-will-be-attached-to-this-crate-type": "&7Keys will be attached to this crate type."
    "kills-bounties-and-duels-are-configured": "Kills, bounties and duels are configured."
    "kit-cooldown": "Kit Cooldown"
    "kit-items-are-read-from-config-yml-premium-kit": "&7Kit items are read from config.yml premium-kit."
    "launch-checklist": "&aLaunch Checklist"
    "left-click-a-type-to-get-one": "&7Left-click a type to get one."
    "left-click-give-one": "&aLeft click: give one"
    "left-click-teleport-there": "&aLeft click: teleport there"
    "limits": "&6Limits"
    "listing-bonus": "Listing Bonus"
    "listing-tax": "Listing Tax"
    "location-invalid": "&cLocation invalid"
    "make-command-aliases-teleport-players": "&7Make command aliases teleport players."
    "make-crates-or-custom-commands-teleport": "&7Make /crates or custom commands teleport."
    "market-alerts": "Market Alerts"
    # {0}: item/material display name
    "material": "&7Material: &e{0}"
    # {0}: configured value
    "max-x": "&7Max: &e{0}x"
    "menus-yml-and-messages-yml": "&7menus.yml and messages.yml"
    # {0}: configured value
    "min-x": "&7Min: &e{0}x"
    "minutes": "minutes"
    "missing": "missing"
    "missing-required-plugins": "&cMissing required plugins"
    "needs-review": "&eNeeds review"
    "next": "&eNext"
    "night-vision": "Night Vision"
    "no-action-required": "&8No action required."
    "no-yaml-editing-required-for-common-tasks": "&7No YAML editing required for common tasks."
    "none": "none"
    "one-click-preset": "One-Click Preset"
    "one-click-smp-setup": "&a&lOne-Click SMP Setup"
    "online-shards": "Online Shards"
    # {0}: page number
    "page": "&7Page {0}"
    "per-minute": "per minute"
    "place-crate-blocks-at-spawn-or-crate-room": "Place crate blocks at spawn or crate room."
    "place-this-block-to-create-a-clickable-crate": "&7Place this block to create a clickable crate."
    "placeable-crates": "&aPlaceable Crates"
    "placeable-crates-are-disabled": "&cPlaceable crates are disabled."
    # {0}: type
    "placed-clickable-crate": "&aPlaced clickable crate &e{0}&a."
    "placed-crate-blocks-and-command-teleports": "&7placed crate blocks and command teleports."
    "placed-crates": "Placed Crates"
    "player-data-is-preserved": "&7Player data is preserved."
    "players-click-placed-crate-with-matching-key": "&7Players click placed crate with matching key."
    "players-running-crates-will-teleport-here": "&7Players running /crates will teleport here."
    "portable-workbench": "Portable Workbench"
    "premium-perks": "Premium Perks"
    "premium-setup": "&bPremium Setup"
    "premium-setup-83a5e8": "&b&lPremium Setup"
    "preset-packs": "&fPreset Packs"
    "preview-rollback-to-your-previous-settings": "&7Preview rollback to your previous settings."
    "previous": "&ePrevious"
    "previous-settings-restored": "&aPrevious settings restored."
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    "progress": "&7Progress: &a{0}&7/&a{1}"
    "prompt-format-id-buy-sell-amount": "&7Prompt format: &fid buy sell amount"
    "pvp-economy": "PvP Economy"
    "ready": "&aReady"
    "recommended-flow": "&eRecommended Flow"
    "reload": "&cReload"
    "reload-after-editing": "&aReload After Editing"
    "reload-config-and-storage": "&7Reload config and storage."
    "reloaded": "&aReloaded."
    # {0}: type
    "removed-crate": "&aRemoved crate &e{0}&a."
    # {0}: item/material display name
    "removed-from-the-premium-kit": "&cRemoved &e{0} &cfrom the premium kit."
    "repair-cooldown": "Repair Cooldown"
    "reports-moderation-gui-and-staff-commands-are-registered": "Reports, moderation GUI and staff commands are registered."
    "restore-previous-settings": "&aRestore previous settings"
    "restores-config-and-shops-from-the-last-backup": "&7Restores config and shops from the last backup."
    "retention-loops": "Retention Loops"
    "review-crate-tiers-and-give-place-keys": "Review crate tiers and give/place keys."
    "review-rank-perks-cooldowns-and-premium-kit": "Review rank perks, cooldowns and premium kit."
    "review-spawner-prices-drops-and-stack-scaling": "Review spawner prices, drops and stack scaling."
    "right-click-a-type-to-add-the-held-item-as-a-drop": "&7Right-click a type to add the held item as a drop."
    "right-click-add-held-item-as-drop": "&eRight click: add held item as drop"
    "right-click-remove-from-kit": "&eRight click: remove from kit"
    "right-click-update-to-your-current-location": "&eRight click: update to your current location"
    # {0}: error details
    "rollback-failed": "&cRollback failed: {0}"
    "rows": "rows"
    "scoreboard-tablist": "Scoreboard/Tablist"
    "seconds": "seconds"
    # {0}: formatted amount
    "sell": "&7Sell: &6{0}"
    "sell-multiplier": "Sell Multiplier"
    "sell-supply-lowers-prices": "&7Sell supply lowers prices."
    "set-crates-here": "&aSet /crates Here"
    "set-locations-from-this-gui": "&7Set locations from this GUI."
    "set-route-crates": "SET_ROUTE:crates"
    # {0}: dynamic value (keep this placeholder)
    # {1}: amount
    # {2}: item/material display name
    "set-to-generate-x-per-cycle": "&aSet &e{0} &ato generate &e{1}x {2}&a per cycle."
    "set-your-server-name-menu-title-and-chat-prefix": "Set your server name, menu title and chat prefix."
    # {0}: count
    "settings-change": "&e{0} settings change"
    "shard-interest": "Shard Interest"
    "shards": "shards"
    "shards-min": "shards/min"
    "shift-right-click-delete-route": "&cShift-right click: delete route"
    "shop-builder": "&aShop Builder"
    "shop-builder-2e770e": "&a&lShop Builder"
    "shop-categories": "Shop Categories"
    "shops-yml": "&7shops.yml"
    "smp-creator-toolkit": "&6&lSMP Creator Toolkit"
    "smp-launch-checklist": "&a&lSMP Launch Checklist"
    "smp-presets": "&f&lSMP Presets"
    "smp-stack-curve": "SMP Stack Curve"
    "sneak-to-stack": "Sneak To Stack"
    "spawner-economy": "Spawner Economy"
    "spawner-price": "Spawner Price"
    "spawner-setup": "&dSpawner Setup"
    "spawner-setup-515e4c": "&d&lSpawner Setup"
    "stack-scaling": "Stack Scaling"
    "staff-tools": "Staff Tools"
    # {0}: dynamic value (keep this placeholder)
    "status": "&7Status: {0}"
    "supply-and-demand-can-move-server-prices": "&7Supply and demand can move server prices."
    # {0}: dynamic value (keep this placeholder)
    "teleported-to-destination": "&aTeleported to &e/{0}&a destination."
    # {0}: dynamic value (keep this placeholder)
    "text": "&a&l{0}"
    # {0}: dynamic value (keep this placeholder)
    "text-0c9112": "&e{0}"
    # {0}: id
    "text-5c01bc": "&f{0}"
    # {0}: id
    "text-83e4bb": "&c{0}"
    # {0}: dynamic value (keep this placeholder)
    "text-891249": "&f/{0}"
    "text-d05e90": "&e"
    "text-d2cb95": "&a"
    "text-ef9d5f": "&c"
    "that-was-not-a-valid-amount": "&cThat was not a valid amount."
    "that-was-not-a-valid-number": "&cThat was not a valid number."
    "this-crate-is-protected": "&cThis crate is protected."
    "tune-custom-spawners-from-in-game": "&7Tune custom spawners from in-game."
    "tune-premium-perks-from-a-gui": "&7Tune premium perks from a GUI."
    "type-cancel-to-stop": "&7Type &ccancel &7to stop."
    # {0}: item/material display name
    # {1}: dynamic value (keep this placeholder)
    "type-drops-per-cycle-for-on-spawner": "&eType drops per cycle for &f{0} &eon spawner &f{1}&e."
    # {0}: dynamic value (keep this placeholder)
    "type-item-details-for-id-buy-sell-amount": "&eType item details for &f{0}&e: &fid buy sell amount"
    "type-shop-details-in-chat-category-id-buy-sell-amount": "&eType shop details in chat: &fcategory id buy sell amount"
    "type-the-command-name-to-bind-to-your-current-location": "&eType the command name to bind to your current location."
    # {0}: dynamic value (keep this placeholder)
    "type-the-key-amount-for-crate-type-cancel-to-stop": "&eType the key amount for crate &f{0}&e. Type &ccancel &eto stop."
    # {0}: dynamic value (keep this placeholder)
    "type-the-new-value-for-type-cancel-to-stop": "&eType the new value for &f{0}&e. Type &ccancel &eto stop."
    # {0}: item/material display name
    "type-the-premium-kit-amount-for-type-cancel-to-stop": "&eType the premium kit amount for &f{0}&e. Type &ccancel &eto stop."
    "undo-last-preset": "&6Undo last preset"
    # {0}: dynamic value (keep this placeholder)
    "updated": "&aUpdated &e{0}&a."
    "use-category-id-buy-sell-amount": "&cUse: category id buy sell amount"
    "use-id-buy-sell-amount": "&cUse: id buy sell amount"
    "use-this-before-opening-the-server": "&7Use this before opening the server."
    "uses-your-current-location": "&7Uses your current location."
    "vault-rows": "Vault Rows"
    # {0}: player name
    "world": "&7World: &e{0}"
    "x": "x"
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    # {2}: dynamic value (keep this placeholder)
    "xyz": "&7XYZ: &e{0}, {1}, {2}"
    "you-will-type-the-command-name-in-chat": "&7You will type the command name in chat."
    "your-current-config-and-shops-are-backed-up": "&7Your current config and shops are backed up."
  currency:
    # {0}: formatted amount
    "billions": "${0}b"
    # {0}: formatted amount
    "millions": "${0}m"
    # {0}: formatted amount
    "thousands": "${0}k"
    # {0}: formatted amount
    "units": "${0}"
  custom-spawner:
    "back": "&7Back"
    "best-order-price-or-base-server-price": "&7Best order price or base server price."
    "click-to-buy": "&aClick to buy"
    "collect-drops": "&aCollect Drops"
    "collect-xp": "&eCollect XP"
    "competitive-smp-virtual-drop-generators": "&7Competitive SMP virtual drop generators."
    # {0}: price
    "cost-shards": "&7Cost: &d{0} shards"
    "drops-stored-items-above-the-spawner": "&7Drops stored items above the spawner."
    "dump-drops": "&bDump Drops"
    "dumped-stored-drops": "&aDumped stored drops."
    # {0}: dynamic value (keep this placeholder)
    "effective-output-x": "&7Effective output: &e{0}x"
    # {0}: dynamic value (keep this placeholder)
    "estimated-min": "&7Estimated/min: &f{0}"
    "make-inventory-space-before-buying-a-spawner": "&cMake inventory space before buying a spawner."
    "make-space-or-sell-dump-the-stored-drops-before-picking-up-this-s": "&cMake space or sell/dump the stored drops before picking up this spawner."
    "mode-virtual-storage": "&7Mode: &bvirtual storage"
    "move-all-stored-drops-to-your-inventory": "&7Move all stored drops to your inventory."
    "no-drops-stored": "&cNo drops stored."
    "no-mobs-spawn-hoppers-do-not-pull-drops": "&8No mobs spawn. Hoppers do not pull drops."
    "none": "None"
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    "picked-up-x-spawner": "&aPicked up &e{0}x {1} Spawner&a."
    # {0}: dynamic value (keep this placeholder)
    "placed-spawner": "&aPlaced &e{0} Spawner&a."
    # {0}: price
    "price-shards-each": "&7Price: &d{0} shards each"
    # {0}: dynamic value (keep this placeholder)
    "produces": "&7Produces: &f{0}"
    # {0}: dynamic value (keep this placeholder)
    # {1}: price
    "purchased-spawner-for-shards": "&aPurchased &e{0} Spawner&a for &d{1} shards&a."
    "right-click-placed-spawner-to-open-storage": "&7Right-click placed spawner to open storage."
    "right-click-placed-spawners-for-storage": "&7Right-click placed spawners for storage."
    "sell-drops": "&aSell Drops"
    "shift-right-click-same-type-to-stack": "&7Shift-right-click same type to stack."
    # {0}: dynamic value (keep this placeholder)
    "spawner": "&d{0} Spawner"
    # {0}: formatted amount
    "spawner-sale": "&aSpawner sale: {0}"
    # {0}: dynamic value (keep this placeholder)
    "stack-size": "&7Stack size: &e{0}"
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    # {2}: dynamic value (keep this placeholder)
    "stacked-x-spawner-total": "&aStacked &e{0}x {1} Spawner&a. Total: &e{2}&a."
    # {0}: amount
    "stored": "&7Stored: &e{0}"
    # {0}: dynamic value (keep this placeholder)
    "stored-drops": "&7Stored drops: &f{0}"
    # {0}: dynamic value (keep this placeholder)
    "stored-xp": "&7Stored XP: {0}"
    # {0}: item/material display name
    "text": "&f{0}"
    "they-do-not-spawn-live-mobs": "&7They do not spawn live mobs."
    # {0}: type
    "type": "&8Type: {0}"
    "up-to-2-304-items-per-click": "&7Up to 2,304 items per click."
    "use-water-streams-below-nearby-to-move-them": "&7Use water streams below/nearby to move them."
    "virtual-drop-generator-no-mobs-spawn": "&7Virtual drop generator. No mobs spawn."
    "virtual-spawners": "&d&lVirtual Spawners"
    # {0}: price
    "you-need-shards-to-buy-a-spawner": "&cYou need &d{0} shards &cto buy a spawner."
    # {0}: shard amount
    "your-shards": "&7Your shards: &d{0}"
  daily:
    "claim-daily": "&aClaim Daily"
    "claimed": "&cClaimed"
    "click-to-claim": "&aClick to claim."
    # {0}: formatted amount
    # {1}: shard amount
    # {2}: dynamic value (keep this placeholder)
    "daily-claimed-and-shards-streak": "&aDaily claimed: &e{0} &7and &d{1} shards&a. Streak: &e{2}"
    "daily-rewards": "&e&lDaily Rewards"
    "money-and-shard-reward": "&7Money and shard reward."
    # {0}: configured value
    "premium-multiplier-x": "&7Premium multiplier: &e{0}x"
    "ready": "&aReady"
    # {0}: dynamic value (keep this placeholder)
    "streak": "&7Streak: &e{0}"
    # {0}: dynamic value (keep this placeholder)
    "today": "&7Today: {0}"
    "you-already-claimed-today-s-reward": "&cYou already claimed today's reward."
    "your-daily-reward-is-ready-daily": "&eYour daily reward is ready: &f/daily&e."
  duel:
    # {0}: dynamic value (keep this placeholder)
    "admin-delete-duel-arena-delete": "&7Admin delete: &f/duel arena delete {0}"
    "admins-duel-arena-set-1-2": "&7Admins: &f/duel arena set <id> 1|2"
    "and-fight-in-configured-arena-spawns": "&7and fight in configured arena spawns."
    "arena-point-must-be-1-or-2": "&cArena point must be 1 or 2."
    "arenas": "&bArenas"
    "both-players-must-be-alive-out-of-combat-and-outside-a-duel": "&cBoth players must be alive, out of combat and outside a duel."
    "challenge-players-accept-pending-duels": "&7Challenge players, accept pending duels,"
    # {0}: dynamic value (keep this placeholder)
    "deleted-duel-arena": "&cDeleted duel arena &e{0}&c."
    "denied-duel-request": "&cDenied duel request."
    # {0}: player name
    "denied-your-duel-request": "&c{0} denied your duel request."
    "duel-cancelled-a-player-became-unavailable": "&cDuel cancelled: a player became unavailable."
    "duel-cancelled-because-a-teleport-was-blocked": "&cDuel cancelled because a teleport was blocked."
    "duel-cancelled-both-players-must-afford-the-wager-and-payment-mus": "&cDuel cancelled: both players must afford the wager and payment must save."
    "duel-funding-failed": "&cDuel funding failed."
    "duel-started": "&cDuel started."
    # {0}: player name
    "duel-started-against": "&cDuel started against &e{0}&c."
    "duel-wager": "&f/duel <player> [wager]"
    "duels": "&c&lDuels"
    # {0}: player name
    # {1}: formatted amount
    "has-challenged-you-to-a-duel-for": "&e{0} &ahas challenged you to a duel for &e{1}&a."
    "how-to-challenge": "&aHow To Challenge"
    "invalid-or-disabled-wager": "&cInvalid or disabled wager."
    "invalid-or-occupied-arena": "&cInvalid or occupied arena."
    # {0}: dynamic value (keep this placeholder)
    "invites-sent-to-you": "&7Invites sent to you: &e{0}"
    "needs-spawn-1-and-spawn-2": "&cNeeds spawn 1 and spawn 2"
    "no-duel-invite-to-deny": "&cNo duel invite to deny."
    "no-free-duel-arena-is-ready-ask-an-admin-to-set-one": "&cNo free duel arena is ready. Ask an admin to set one."
    "no-matching-duel-invite": "&cNo matching duel invite."
    "one-of-those-players-is-already-in-a-duel": "&cOne of those players is already in a duel."
    "pending-invites": "&ePending Invites"
    "player-unavailable": "&cPlayer unavailable."
    "ready": "&aReady"
    # {0}: count
    "ready-arenas": "&7Ready arenas: &e{0}"
    # {0}: player name
    # {1}: formatted amount
    "sent-duel-request-to-for": "&aSent duel request to &e{0}&a for &e{1}&a."
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    "set-duel-arena-spawn": "&aSet duel arena &e{0} &aspawn &e{1}&a."
    # {0}: dynamic value (keep this placeholder)
    "text": "&f{0}"
    "that-duel-invite-expired": "&cThat duel invite expired."
    "that-player-is-not-accepting-duel-requests": "&cThat player is not accepting duel requests."
    "that-player-is-not-your-duel-opponent": "&cThat player is not your duel opponent."
    "use-duel-accept": "&7Use &f/duel accept <player>&7."
    # {0}: player name
    # {1}: player name
    "use-duel-accept-or-duel-deny": "&7Use &f/duel accept {0} &7or &f/duel deny {1}&7."
    "wager-is-optional-and-paid-to-the-winner": "&7Wager is optional and paid to the winner."
    "you-are-not-in-a-duel": "&cYou are not in a duel."
    "you-cannot-duel-yourself": "&cYou cannot duel yourself."
    "you-do-not-have-enough-money-for-that-wager": "&cYou do not have enough money for that wager."
    # {0}: dynamic value (keep this placeholder)
    "you-lost-the-duel-by": "&cYou lost the duel by &e{0}&c."
    # {0}: dynamic value (keep this placeholder)
    # {1}: formatted amount
    "you-won-the-duel-by-pot": "&aYou won the duel by &e{0}&a. Pot: &e{1}&a."
    "your-wager-payment-could-not-be-saved-contact-staff-the-escrow-is": "&cYour wager payment could not be saved. Contact staff; the escrow is retained."
  inventory-menus:
    # {0}: player name
    "accept": "Accept {0}"
    "add-friend": "Add Friend"
    "all-listings": "All listings"
    "all-orders": "All orders"
    # {0}: page number
    "auction-house": "Auction House - {0}"
    "back": "Back"
    "buy-listing": "Buy Listing"
    # {0}: player name
    "buyer": "Buyer: {0}"
    "cancel": "Cancel"
    "close": "Close"
    "close-and-claim": "Close and Claim"
    "confirm": "Confirm"
    "create-order": "Create order"
    # {0}: name
    "delete-with-delhome": "Delete with /delhome {0}"
    "deliver-items": "Deliver Items"
    "disabled-click-to-enable": "Disabled - click to enable"
    # {0}: formatted amount
    "each": "{0} each"
    "enabled-click-to-disable": "Enabled - click to disable"
    "exact": " (exact)"
    "friend-add": "/friend add <player>"
    "friends": "Friends"
    "hold-an-item-first": "Hold an item first."
    "homes": "Homes"
    "keeps-the-box-and-protected-custom-items": "Keeps the box and protected custom items."
    "leave-queue": "Leave queue"
    # {0}: dynamic value (keep this placeholder)
    "list": "/{0} list <price>"
    "list-held-item": "List held item"
    "match-held-item": "Match held item"
    # {0}: formatted amount
    # {1}: shard amount
    # {2}: dynamic value (keep this placeholder)
    # {3}: dynamic value (keep this placeholder)
    "money-shards-kills-deaths": "Money: {0}\nShards: {1}\nKills: {2}\nDeaths: {3}"
    "my-listings-returns": "My listings / returns"
    "my-orders-claims": "My orders / claims"
    "next": "Next"
    "night-vision-requires-premium": "&cNight vision requires premium."
    "only-matching-orders-may-buy-this-exact-item": "Only matching orders may buy this exact item."
    "order-exact-held-item": "Order exact held item"
    # {0}: page number
    "orders": "Orders - {0}"
    "orders-create": "/orders create <material> <amount> <priceEach>"
    "orders-hand": "/orders hand <amount> <priceEach>"
    # {0}: dynamic value (keep this placeholder)
    "paired-queue": "{0} paired queue"
    "previous": "Previous"
    "profile": "Profile"
    "queue-status": "Queue status"
    # {0}: page number
    "quick-buy": "Quick Buy - {0}"
    "quick-buy-a3fa2a": "Quick Buy"
    "quick-buy-is-unavailable-during-combat": "&cQuick Buy is unavailable during combat."
    "random-teleport": "Random Teleport"
    "reclaim-listing": "Reclaim Listing"
    "regions-zones": "Regions / Zones"
    # {0}: dynamic value (keep this placeholder)
    # {1}: formatted amount
    "remaining-price-each": "Remaining: {0}\nPrice each: {1}"
    # {0}: player name
    "remove": "Remove {0}?"
    "remove-friend": "Remove friend?"
    "rtp-status": "RTP Status"
    "saved-favourites-loadouts": "Saved favourites / loadouts"
    "sell": "Sell"
    "sell-exact-held-item": "Sell exact held item"
    "sell-exact-item": "Sell Exact Item?"
    "sell-held-item": "Sell held item"
    "sell-history": "Sell history"
    "sell-inventory": "Sell inventory"
    "sell-inventory-c769d1": "Sell Inventory?"
    "sell-shulker-contents": "Sell shulker contents"
    "sell-shulker-contents-aeb7c8": "Sell Shulker Contents?"
    # {0}: formatted amount
    # {1}: player name
    "seller": "&a{0} &7Seller: {1}"
    # {0}: player name
    # {1}: formatted amount
    "seller-total": "Seller: {0}\nTotal: {1}"
    "sells-supported-plain-items-in-your-storage-slots": "Sells supported plain items in your storage slots."
    "set-a-home": "Set a home"
    "sethome": "/sethome <name>"
    "settings": "Settings"
    # {0}: dynamic value (keep this placeholder)
    "solo": "{0} solo"
    "teleport-to-this-home": "Teleport to this home?"
    # {0}: dynamic value (keep this placeholder)
    "text": "&e{0}"
    "this-player-has-a-private-profile": "This player has a private profile."
    # {0}: formatted amount
    # {1}: dynamic value (keep this placeholder)
    "total-for": "{0} total for {1}"
    "transaction": "Transaction"
    "your-held-item-changed": "&cYour held item changed."
  key-ledger:
    "cannot-snapshot-key-data": "Cannot snapshot key data"
    "invalid-key-type-or-amount": "Invalid key type or amount"
    "key-balance-limit-reached": "Key balance limit reached"
    "key-reward-would-exceed-the-account-limit": "Key reward would exceed the account limit"
  kits:
    "admins-kitadmin-save": "&7Admins: /kitadmin save <id>"
    # {0}: id
    "claimed-kit": "&aClaimed kit &e{0}&a."
    # {0}: dynamic value (keep this placeholder)
    "cooldown-minutes": "&cCooldown: {0} minutes"
    # {0}: id
    "deleted-kit": "&cDeleted kit &e{0}&c."
    # {0}: dynamic value (keep this placeholder)
    "kit": "&a{0} Kit"
    # {0}: dynamic value (keep this placeholder)
    "kit-cooldown-minutes": "&cKit cooldown: &e{0} minutes&c."
    "kit-not-found": "&cKit not found."
    "kits": "&a&lKits"
    "left-click-claim": "&7Left click: claim"
    "make-room-for-the-whole-kit-first-your-cooldown-has-not-started": "&cMake room for the whole kit first. Your cooldown has not started."
    "no-permission": "&cNo permission."
    "preview-and-claim-cooldown-kits": "&7Preview and claim cooldown kits."
    "ready-to-claim": "&aReady to claim"
    "right-click-preview": "&7Right click: preview"
    # {0}: id
    "saved-kit-from-your-inventory": "&aSaved kit &e{0}&a from your inventory."
    "starter-kit": "&aStarter Kit"
    "usage-kitadmin": "&eUsage: /kitadmin <save|delete> <id>"
    "use-a-kit-id-of-1-32-letters-numbers-underscores-or-hyphens": "&cUse a kit ID of 1-32 letters, numbers, underscores or hyphens."
  market:
    # {0}: count
    # {1}: formatted amount
    # {2}: dynamic value (keep this placeholder)
    "claimed-items-refund": "&aClaimed {0} items. Refund: {1}{2}"
    "hold-a-single-shulker-box-to-sell-its-contents": "&cHold a single shulker box to sell its contents."
    "listing-returned": "&aListing returned."
    "make-inventory-space-before-reclaiming": "&cMake inventory space before reclaiming."
    "make-inventory-space-first": "&cMake inventory space first."
    # {0}: player name
    # {1}: dynamic value (keep this placeholder)
    # {2}: item/material display name
    # {3}: formatted amount
    "market-alert-listed-x-for": "&dMarket alert: &e{0} &7listed &f{1}x {2} &7for &a{3}&7."
    # {0}: dynamic value (keep this placeholder)
    # {1}: formatted amount
    "matched-items-to-higher-paying-orders-for": "&aMatched {0} items to higher-paying orders for {1}."
    "no-supported-plain-contents-to-sell-custom-items-are-protected": "&7No supported plain contents to sell. Custom items are protected."
    # {0}: dynamic value (keep this placeholder)
    "remaining-items": ". Remaining items: {0}"
    # {0}: formatted amount
    "shulker-contents-sold-for-box-retained": "&aShulker contents sold for {0}. Box retained."
    "that-is-not-your-order": "&cThat is not your order."
    "that-listing-is-no-longer-yours-or-was-already-claimed": "&cThat listing is no longer yours or was already claimed."
    "unknown": "Unknown"
  market-recovery:
    # {0}: error details
    "could-not-acknowledge-recovery": "&cCould not acknowledge recovery: {0}"
    "no-permission": "&cNo permission."
    # {0}: count
    "pending-inventory-recovery-player-s-review-transactions-yml-again": "&ePending inventory recovery: {0} player(s). Review transactions/*.yml against player inventories before resolving."
    # {0}: id
    # {1}: count
    "record-s": "&7{0} — {1} record(s)"
    "recovered-your-interrupted-market-transaction": "&aRecovered your interrupted market transaction."
    "recovery-hold-removed-journal-archived-no-items-replayed": "&aRecovery hold removed. Journal archived; no items replayed."
    "smp-recovery-resolve-acknowledge-only-after-reconciling-the-recor": "&e/smp recovery resolve <player UUID> acknowledge &7only after reconciling the recorded items."
    "your-inventory-has-a-transaction-awaiting-staff-recovery-please-c": "Your inventory has a transaction awaiting staff recovery. Please contact staff."
  menu:
    "accepting-deliveries": "&aAccepting deliveries"
    "active": "&aActive"
    # {0}: configured value
    "active-listings": "+{0} active listings"
    "admin-reload": "&cAdmin Reload"
    "afk-rewards": "&eAFK Rewards"
    "afk-rewards-disabled": "&cAFK rewards disabled."
    "afk-rewards-enabled-move-to-disable": "&aAFK rewards enabled. Move to disable."
    # {0}: configured value
    "ah-market-tax": "{0}% AH/market tax"
    "allow-future-duel-systems-to-invite-you": "&7Allow future duel systems to invite you."
    "allow-other-players-to-pay-you-money": "&7Allow other players to pay you money."
    "allow-private-message-systems-to-target-you": "&7Allow private message systems to target you."
    "allow-yourself-to-send-public-chat": "&7Allow yourself to send public chat."
    # {0}: amount
    "amount": "&7Amount: &e{0}"
    "auction-house": "&6Auction House"
    "auctions": "&6Auctions"
    "back": "&7Back"
    "bounties": "&cBounties"
    "bounty-alerts-and-profile-visibility": "Bounty alerts and profile visibility"
    "bounty-radar": "Bounty Radar"
    "browse-player-listings": "&7Browse player listings."
    "build-shops-crates-and-economy-from-gui": "&7Build shops, crates and economy from GUI."
    "bulk-orders": "&bBulk Orders"
    # {0}: formatted amount
    "buy": "&7Buy: &a{0}"
    "buy-and-manage-lag-friendly-drop-spawners": "&7Buy and manage lag-friendly drop spawners."
    "buy-essentials-combat-items-and-farms": "&7Buy essentials, combat items and farms."
    "buy-vein-miner-drills": "&7Buy vein miner drills."
    # {0}: player name
    "buyer": "&7Buyer: &f{0}"
    "challenge-players-and-fight-in-arenas": "&7Challenge players and fight in arenas."
    "chat-messages-alerts-night-vision": "&7Chat, messages, alerts, night vision."
    "claim-only": "&eClaim only"
    "claim-premium-kit": "&aClaim Premium Kit"
    "click-any-item-to-flip-it": "&7Click any item to flip it."
    "click-to-buy": "&aClick to buy"
    "click-to-claim-delivered-items": "&aClick to claim delivered items"
    "click-to-deliver-matching-items": "&aClick to deliver matching items"
    "click-to-inspect-rank-value": "&7Click to inspect rank value."
    "click-to-open": "&aClick to open"
    "click-to-open-admin-tools": "&7Click to open admin tools."
    "click-to-purchase": "&aClick to purchase"
    "click-to-teleport": "&aClick to teleport."
    "click-to-toggle": "&aClick to toggle"
    "competitive-smp-personal-toggles": "&7Competitive SMP personal toggles."
    # {0}: shard amount
    "cost-shards": "&7Cost: &d{0} shards"
    "could-not-grant-these-keys-shards-refunded-check-inventory-space": "&cCould not grant these keys. Shards refunded; check inventory space and configuration."
    # {0}: type
    "crate-key": "&b{0} Crate Key"
    "crates": "&bCrates"
    "create-bounty": "&eCreate Bounty"
    "create-order": "&eCreate Order"
    "creator-toolkit": "&6Creator Toolkit"
    # {0}: dynamic value (keep this placeholder)
    "current": "&7Current: {0}"
    # {0}: status
    "currently": "&7Currently: {0}"
    "custom-spawners": "&dCustom Spawners"
    # {0}: dynamic value (keep this placeholder)
    "deaths": "&7Deaths: &f{0}"
    # {0}: dynamic value (keep this placeholder)
    # {1}: item/material display name
    # {2}: formatted amount
    "delivered-x-for": "&aDelivered &e{0}x {1}&a for {2}."
    "drills": "&bDrills"
    "duels": "&cDuels"
    "dynamic-pricing-active": "&eDynamic pricing active"
    "dynamic-pricing-disabled": "&8Dynamic pricing disabled"
    "expanded-homes": "Expanded Homes"
    "feed": "&6Feed"
    "fulfill-buy-orders-in-quantity": "&7Fulfill buy orders in quantity."
    "homes": "&cHomes"
    # {0}: configured value
    "homes-3bd810": "+{0} homes"
    # {0}: count
    # {1}: dynamic value (keep this placeholder)
    "homes-f83395": "&7Homes: &e{0}&7/&e{1}"
    # {0}: dynamic value (keep this placeholder)
    "id": "&8ID: {0}"
    "inactive": "&cInactive"
    "included-in-premium": "&aIncluded in premium."
    # {0}: dynamic value (keep this placeholder)
    # {1}: status
    "is-now": "&f{0} &7is now {1}&7."
    # {0}: dynamic value (keep this placeholder)
    "keys": "&7Keys: &b{0}"
    "kill-the-target-to-claim": "&8Kill the target to claim."
    # {0}: dynamic value (keep this placeholder)
    "kills": "&7Kills: &c{0}"
    "leaderboards": "&eLeaderboards"
    "leaderboards-bce360": "&e&lLeaderboards"
    "left-click-buy": "&aLeft click: buy"
    # {0}: count
    # {1}: dynamic value (keep this placeholder)
    "limit": "&7Limit: &e{0}&7/&e{1}"
    "list-held-item": "&eList Held Item"
    "listing-expansion": "Listing Expansion"
    # {0}: dynamic value (keep this placeholder)
    "listings-limit": "&7Listings limit: &e{0}"
    "live-alerts-when-players-list-items": "Live alerts when players list items"
    "make-inventory-space-first": "&cMake inventory space first."
    "market-alerts": "Market Alerts"
    "mine-ore-and-log-veins": "&7Mine ore and log veins."
    # {0}: formatted amount
    "money": "&7Money: &a{0}"
    "night-vision": "Night Vision"
    "night-vision-is-a-premium-setting": "&cNight vision is a premium setting."
    "no": "&cNo"
    "no-data-yet": "&7No data yet."
    "no-supported-plain-item-to-sell": "&7No supported plain item to sell."
    "no-supported-plain-items-to-sell": "&7No supported plain items to sell."
    "off": "&cOff"
    "off-30106a": "&c&lOFF"
    "off-5ef0bf": "&cOFF"
    "on": "&aOn"
    "on-8eb5ba": "&a&lON"
    "on-f7a464": "&aON"
    # {0}: dynamic value (keep this placeholder)
    "online": "&7Online: {0}"
    "open-a-workbench-wherever-you-are": "Open a workbench wherever you are"
    "open-category": "&7Open category."
    "open-premium-vault": "&dOpen Premium Vault"
    "open-reward-crates-with-keys": "&7Open reward crates with keys."
    # {0}: dynamic value (keep this placeholder)
    "opened-crate-and-received": "&aOpened crate and received &e{0}&a."
    "passive-shards": "Passive Shards"
    "pay": "&6Pay"
    "personal-setting": "&7Personal setting."
    "pick-a-category": "&7Pick a category."
    "player-market": "&dPlayer Market"
    "player-settings": "&f&lPlayer Settings"
    "portable-crafting": "Portable Crafting"
    "possible-crate-reward": "&7Possible crate reward."
    # {0}: dynamic value (keep this placeholder)
    "premium": "&7Premium: {0}"
    "premium-infinite-night-vision": "&7Premium infinite night vision."
    "premium-only": "&7Premium only."
    "premium-perks": "&bPremium Perks"
    "premium-style-market-board": "&7Premium-style market board."
    "premium-suite": "&b&lPremium Suite"
    "premium-vault": "&dPremium Vault"
    "premium-vault-f0fab9": "Premium Vault"
    "premium-vault-requires-premium": "&cPremium vault requires premium."
    # {0}: formatted amount
    "price": "&7Price: &a{0}"
    # {0}: formatted amount
    "price-each": "&7Price each: &a{0}"
    # {0}: shard amount
    "price-shards": "&7Price: &d{0} shards"
    "profile": "&eProfile"
    # {0}: id
    # {1}: formatted amount
    "purchased-listing-for": "&aPurchased listing &e{0}&a for {1}."
    "purchased-shard-shop-item": "&aPurchased shard shop item."
    # {0}: amount
    # {1}: item/material display name
    # {2}: formatted amount
    "purchased-x-for": "&aPurchased &e{0}x {1}&a for {2}."
    "rank-benefits-on-this-server": "&7Rank benefits on this server."
    "reduced-listing-tax": "Reduced Listing Tax"
    "reload-all-configs-and-storage": "&7Reload all configs and storage."
    "reloaded-smp-builder-configs": "&aReloaded SMP builder configs."
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    "remaining": "&7Remaining: &e{0}&7/&e{1}"
    "repair-held-item": "&eRepair Held Item"
    "requires-a-matching-physical-key": "&7Requires a matching physical key."
    "requires-premium": "&7Requires premium."
    "reserve-state-for-coordinate-hiding": "&7Reserve state for coordinate hiding."
    "reserve-state-for-scoreboard-visibility": "&7Reserve state for scoreboard visibility."
    "reserve-state-for-spawn-safety-hints": "&7Reserve state for spawn safety hints."
    # {0}: formatted amount
    "reward": "&7Reward: &a{0}"
    "reward-claimed": "&a&lReward Claimed"
    "right-click-sell-one-stack": "&eRight click: sell one stack"
    "rolling": "&e&lRolling..."
    # {0}: configured value
    "rows-private-storage": "{0} rows private storage"
    "secure-personal-item-storage": "&7Secure personal item storage."
    # {0}: dynamic value (keep this placeholder)
    "sell-boost": "&7Sell boost: &e{0}"
    "sell-center": "&eSell Center"
    # {0}: formatted amount
    "sell-each": "&7Sell each: &6{0}"
    "sell-inventory-clutter-instantly": "&7Sell inventory clutter instantly."
    "sell-multiplier": "Sell Multiplier"
    # {0}: player name
    "seller": "&7Seller: &f{0}"
    # {0}: dynamic value (keep this placeholder)
    "server": "&7Server: &f{0}"
    "server-economy-and-pvp-standings": "&7Server economy and PvP standings."
    "server-shop": "&aServer Shop"
    "server-shop-ba6ea8": "&a&lServer Shop"
    "set-home": "&aSet Home"
    "set-view-and-teleport-home": "&7Set, view and teleport home."
    "settings": "&fSettings"
    "shard-shop": "&dShard Shop"
    # {0}: shard amount
    "shards": "&7Shards: &d{0}"
    # {0}: shard amount
    "shards-min-online": "+{0} shards/min online"
    "show-bounty-and-combat-economy-alerts": "&7Show bounty and combat economy alerts."
    "show-premium-live-market-alerts": "&7Show premium live market alerts."
    # {0}: formatted amount
    "sold-held-items-for": "&aSold held items for {0}"
    # {0}: formatted amount
    "sold-items-for": "&aSold items for {0}"
    # {0}: dynamic value (keep this placeholder)
    # {1}: item/material display name
    # {2}: formatted amount
    "sold-x-for": "&aSold &e{0}x {1}&a for {2}."
    "spend-pvp-and-afk-shards": "&7Spend PvP and AFK shards."
    "stats-balances-and-current-rank": "&7Stats, balances and current rank."
    # {0}: dynamic value (keep this placeholder)
    "status": "&7Status: {0}"
    # {0}: dynamic value (keep this placeholder)
    "tax": "&7Tax: &e{0}%"
    # {0}: name
    "teleported-to-home": "&aTeleported to home &e{0}&a."
    # {0}: dynamic value (keep this placeholder)
    "text": "&f{0}"
    # {0}: dynamic value (keep this placeholder)
    "text-0c9112": "&e{0}"
    # {0}: player name
    "text-4cfa8b": "&e&l{0}"
    # {0}: item/material display name
    "text-539ee5": "&b{0}"
    # {0}: player name
    "text-83e4bb": "&c{0}"
    "that-home-is-not-available": "&cThat home is not available."
    "that-listing-is-no-longer-available": "&cThat listing is no longer available."
    "that-order-is-not-accepting-deliveries": "&cThat order is not accepting deliveries."
    "this-crate-has-no-rewards-configured": "&cThis crate has no rewards configured."
    "this-shard-offer-is-unavailable-on-this-server-version": "&cThis shard offer is unavailable on this server version."
    "this-shop-item-is-unavailable-on-this-server-version": "&cThis shop item is unavailable on this server version."
    "toggle-afk-shard-earning": "&7Toggle AFK shard earning."
    "toggle-night-vision": "&bToggle Night Vision"
    "toggleable-infinite-night-vision": "Toggleable infinite night vision"
    "top-bounties": "&cTop Bounties"
    "top-kills": "&cTop Kills"
    "top-money": "&6Top Money"
    "top-money-shards-kills-and-bounties": "&7Top money, shards, kills and bounties."
    "top-shards": "&dTop Shards"
    "track-player-bounties": "&7Track player bounties."
    "use-ah-list-to-sell-held-item": "&8Use /ah list <price> to sell held item."
    "use-at-crates": "&7Use at /crates."
    "use-bounty-set": "&7Use &e/bounty set <player> <amount>&7."
    # {0}: dynamic value (keep this placeholder)
    "use-delhome-to-remove": "&8Use /delhome {0} to remove."
    "use-duel-wager": "&8Use /duel <player> [wager]."
    "use-feed-or-click-here": "&7Use /feed or click here."
    # {0}: dynamic value (keep this placeholder)
    "use-list": "&7Use &e/{0} list <price>&7."
    "use-market-list-to-sell-held-item": "&8Use /market list <price> to sell held item."
    "use-orders-create": "&8Use /orders create <material> <amount> <price>."
    "use-orders-create-b3ef9b": "&7Use &e/orders create <material> <amount> <priceEach>&7."
    "use-pay": "&7Use &e/pay <player> <amount>&7."
    "use-premiumkit-or-click-here": "&7Use /premiumkit or click here."
    "use-repair-or-click-here": "&7Use /repair or click here."
    "use-sethome": "&7Use &e/sethome <name>&7."
    "use-workbench-or-click-here": "&7Use /workbench or click here."
    "uses-your-setting-state": "&7Uses your setting state."
    "view-configured-rank-benefits": "&7View configured rank benefits."
    "watch-the-center-slot": "&7Watch the center slot."
    "workbench": "&fWorkbench"
    # {0}: configured value
    "x-server-sell-value": "{0}x server sell value"
    "yes": "&aYes"
    "you-cannot-buy-your-own-listing": "&cYou cannot buy your own listing."
    "you-do-not-have-enough-items-to-sell": "&cYou do not have enough items to sell."
    "you-do-not-have-enough-money": "&cYou do not have enough money."
    "you-do-not-have-enough-shards": "&cYou do not have enough shards."
    "you-do-not-have-matching-items": "&cYou do not have matching items."
    # {0}: type
    "you-need-a-crate-key": "&cYou need a {0} crate key."
    "your-inventory-was-full-so-leftover-items-were-dropped-at-your-fe": "&eYour inventory was full, so leftover items were dropped at your feet."
    "your-reward-is-sliding-into-place": "&7Your reward is sliding into place."
    # {0}: shard amount
    "your-shards": "&7Your shards: &d{0}"
  moderation:
    "added-staff-note": "&aAdded staff note."
    # {0}: key
    # {1}: dynamic value (keep this placeholder)
    # {2}: dynamic value (keep this placeholder)
    "for": "&e{0} for {1}: {2}"
    "freeze": "&bFreeze"
    "mod-mute-warn-freeze-vanish": "&7/mod mute, warn, freeze, vanish"
    # {0}: dynamic value (keep this placeholder)
    "muted": "&aMuted &e{0}&a."
    "no-permission": "&cNo permission."
    "off": "&cOFF"
    "on": "&aON"
    "open-moderation-yml-for-full-report-list": "&7Open moderation.yml for full report list."
    "report-for-player-reports": "&7/report for player reports"
    # {0}: player name
    # {1}: dynamic value (keep this placeholder)
    # {2}: dynamic value (keep this placeholder)
    "report-reported": "&c[Report] &e{0} &7reported &e{1}&7: &f{2}"
    "report-submitted": "&aReport submitted."
    "reports": "&eReports"
    # {0}: configured value
    "reports-afb3a2": "&7Reports: &e{0}"
    # {0}: player name
    # {1}: dynamic value (keep this placeholder)
    "staff": "&b[Staff] &e{0}&7: &f{1}"
    "staff-tools": "&c&lStaff Tools"
    # {0}: key
    "usage-mod": "&eUsage: /mod {0} <player>"
    "usage-mod-mute": "&eUsage: /mod mute <player> <minutes>"
    "usage-mod-note": "&eUsage: /mod note <player> <note>"
    "usage-mod-warn": "&eUsage: /mod warn <player> <reason>"
    "usage-report": "&eUsage: /report <player> <reason>"
    "use-a-mute-length-of-1-5256000-minutes": "&cUse a mute length of 1-5256000 minutes."
    "use-mod-freeze": "&7Use &f/mod freeze <player>&7."
    "use-mod-vanish": "&7Use &f/mod vanish&7."
    "vanish": "&fVanish"
    # {0}: dynamic value (keep this placeholder)
    "vanish-55d919": "&eVanish: {0}"
    # {0}: dynamic value (keep this placeholder)
    "warned": "&aWarned &e{0}&a."
    # {0}: dynamic value (keep this placeholder)
    "warning": "&cWarning: &f{0}"
    "you-are-muted": "&cYou are muted."
  modern-visuals:
    # {0}: label
    "preview-crate": "&bPreview: {0} Crate"
  money-input:
    "enter-a-finite-price-between-0-and-1-trillion": "Enter a finite price between 0 and 1 trillion."
  native-menus:
    # {0}: player name
    "accept": "Accept {0}"
    "add-friend": "Add Friend"
    "all-listings": "All Listings"
    "all-orders": "All Orders"
    "auction-house": "Auction House"
    "back": "Back"
    "cancel": "Cancel"
    "cancel-reclaim": "Cancel / Reclaim"
    # {0}: dynamic value (keep this placeholder)
    "cheapest-live-offers-confirm-the-complete-stack-before-buying": "Cheapest live offers • confirm the complete stack before buying.\n{0}"
    "close": "Close"
    "close-claim-order": "Close & Claim Order"
    "closes-this-order-and-refunds-unfilled-demand": "\nCloses this order and refunds unfilled demand."
    "confirm": "<green>Confirm"
    "confirm-eebdd2": "Confirm"
    "confirm-purchase": "<green>Confirm Purchase"
    "could-not-create-order-check-quantity-balance-and-order-limit": "&cCould not create order. Check quantity, balance and order limit."
    "could-not-create-order-check-your-balance-and-order-limit": "&cCould not create order. Check your balance and order limit."
    "create-listing": "Create Listing"
    "create-order": "Create Order"
    "delete": "<red>Delete"
    "delete-home": "Delete home?"
    "deliver-items": "Deliver Items"
    "delivers-matching-plain-items-from-your-inventory": "\nDelivers matching plain items from your inventory."
    # {0}: item/material display name
    # {1}: formatted amount
    "each": "{0} • {1} each"
    "enter-a-finite-price-between-0-and-1-trillion": "Enter a finite price between 0 and 1 trillion."
    "enter-a-whole-quantity": "Enter a whole quantity."
    "exact": " (exact)"
    "exact-item-order": "Exact Item Order"
    "exact-matches-for-your-held-item": "Exact matches for your held item."
    # {0}: key
    "fill-in": "Fill in {0}."
    # {0}: label
    "find-a-partner": "{0} - Find a partner"
    # {0}: dynamic value (keep this placeholder)
    "find-a-partner-sends-two-players-to-nearby-wilderness-locations-p": "<gray>{0}\nFind a partner sends two players to nearby wilderness locations. PvP may be enabled there."
    "friend-chat-fc": "<gray>Friend chat: /fc <message>"
    "friends": "Friends"
    "funds-are-held-in-escrow-plain-unmodified-items-only": "Funds are held in escrow. Plain, unmodified items only."
    "hold-an-item-to-find-an-exact-match-including-enchantments-and-da": "Hold an item to find an exact match, including enchantments and damage."
    "hold-an-item-to-use-as-the-sample": "Hold an item to use as the sample."
    "hold-the-item-you-want-to-list": "Hold the item you want to list."
    "hold-the-item-you-want-to-sell": "Hold the item you want to sell."
    "home-limit-reached": "&cHome limit reached."
    "home-name": "Home name"
    "homes": "Homes"
    # {0}: error details
    "invalid-dialogs-yml": "Invalid dialogs.yml: {0}"
    "invalid-material-or-quantity-1-1-000-000": "Invalid material or quantity (1-1,000,000)."
    "invalid-setting-value-reopen-settings": "Invalid setting value. Reopen /settings."
    # {0}: item/material display name
    # {1}: formatted amount
    "item": "{0} • {1}/item"
    "leave-rtp-queue-cancel": "Leave RTP queue / cancel"
    "list-held-item": "List Held Item"
    "list-item": "List item"
    "listing": "Listing"
    # {0}: dynamic value (keep this placeholder)
    "listing-fee": "Listing fee: {0}%"
    # {0}: count
    # {1}: page number
    "listings-page-lowest-unit-price-first": "<gray>{0} listings • page {1} • lowest unit price first"
    "match-held-item-exactly": "Match Held Item Exactly"
    "material-e-g-iron-ingot": "Material (e.g. IRON_INGOT)"
    "material-name": "Material name"
    "maximum-price-per-item": "Maximum price per item"
    # {0}: category
    "missing-dialog-category": "Missing dialog category: {0}"
    # {0}: formatted amount
    # {1}: shard amount
    # {2}: dynamic value (keep this placeholder)
    # {3}: dynamic value (keep this placeholder)
    # {4}: dynamic value (keep this placeholder)
    # {5}: dynamic value (keep this placeholder)
    "money-shards-kills-deaths-playtime-hours-rank": "<gray>Money: <green>{0}\n<gray>Shards: <light_purple>{1}\n<gray>Kills: <white>{2}\n<gray>Deaths: <white>{3}\n<gray>Playtime: <white>{4} hours\n<gray>Rank: <gold>{5}"
    "my-listings-returns": "My Listings / Returns"
    "my-orders-claims": "My Orders / Claims"
    "next": "Next"
    "no-permission": "&cNo permission."
    "online-player": "Online player"
    "only-identical-items-qualify-including-name-enchantments-damage-a": "\nOnly identical items qualify, including name, enchantments, damage and custom data."
    "order-held-item-exactly": "Order Held Item Exactly"
    "orders": "Orders"
    # {0}: count
    # {1}: page number
    "orders-page": "<gray>{0} orders • page {1}"
    "plain-items-use-match-held-item-for-enchanted-or-custom-items": "Plain items. Use Match Held Item for enchanted or custom items."
    "player-market": "Player Market"
    "previous": "Previous"
    "price-per-item": "Price per item"
    "private-profile": "Private profile"
    "quantity": "Quantity"
    "quick-buy": "Quick Buy"
    "quick-buy-is-unavailable-during-combat": "&cQuick Buy is unavailable during combat."
    "random-teleport": "Random Teleport"
    "regions-zones": "Regions / Zones"
    "remove-friend": "Remove friend?"
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    # {2}: dynamic value (keep this placeholder)
    # {3}: formatted amount
    # {4}: dynamic value (keep this placeholder)
    "requested-delivered-remaining-price-each": "Requested: {0}\nDelivered: {1}\nRemaining: {2}\nPrice each: {3}{4}"
    "rtp-cancelled": "RTP cancelled."
    "save": "<green>Save"
    "save-1509f5": "Save"
    "save-your-current-location": "Save your current location."
    # {0}: count
    # {1}: dynamic value (keep this placeholder)
    "saved": "<gray>Saved {0} / {1}"
    "saved-favourites-loadouts": "Saved favourites / loadouts"
    "search": "Search"
    "sell": "Sell"
    "sell-exact-held-item": "Sell Exact Held Item"
    "sell-exact-held-item-d23d13": "Sell Exact Held Item?"
    "sell-held-item": "Sell Held Item"
    "sell-history": "Sell History"
    "sell-inventory": "Sell Inventory"
    "sell-inventory-c769d1": "Sell Inventory?"
    "sell-plain-items-at-the-best-available-order-price-or-server-pric": "Sell plain items at the best available order price or server price. Named, enchanted and custom items are protected."
    "sell-shulker-contents": "Sell Shulker Contents"
    "sell-shulker-contents-aeb7c8": "Sell Shulker Contents?"
    # {0}: player name
    # {1}: formatted amount
    # {2}: formatted amount
    "seller-total-per-item": "Seller: {0}\nTotal: {1}\nPer item: {2}"
    "sells-supported-plain-contents-keeps-the-box-and-all-custom-items": "Sells supported plain contents. Keeps the box and all custom items."
    "sells-this-item-only-to-matching-orders-names-enchantments-damage": "Sells this item only to matching orders. Names, enchantments, damage and custom data must match. Unsold items stay with you."
    "send-request": "Send Request"
    "set-a-home": "<green>Set a home"
    "set-home": "Set Home"
    "settings-saved": "&aSettings saved."
    "shard-shop": "Shard Shop"
    # {0}: label
    "solo": "{0} - Solo"
    "teleport": "Teleport"
    # {0}: error details
    "text": "&c{0}"
    "text-a2d378": "<gray>"
    "text-b8bc61": "<green>"
    "this-player-keeps-their-statistics-private": "This player keeps their statistics private."
    "this-sells-supported-plain-items-in-your-storage-slots": "This sells supported plain items in your storage slots."
    "total-asking-price": "Total asking price"
    # {0}: key
    "unknown-player-setting": "Unknown player setting: {0}"
    "use-1-24-letters-numbers-or": "Use 1-24 letters, numbers, _ or -."
    # {0}: dynamic value (keep this placeholder)
    # {1}: item/material display name
    # {2}: formatted amount
    "x": "{0}x {1} • {2}"
    "your-held-item-changed-reopen-the-confirmation": "Your held item changed; reopen the confirmation."
    "your-held-item-changed-reopen-this-form": "Your held item changed; reopen this form."
    "your-sample-is-kept-only-identical-items-qualify-including-spawne": "Your sample is kept. Only identical items qualify, including spawner type, enchantments, damage, name and custom data. Funds are held in escrow."
  preset:
    "dynamic-price-minimum-exceeds-maximum": "Dynamic price minimum exceeds maximum"
    # {0}: key
    "expected-a-finite-non-negative-number-at": "Expected a finite, non-negative number at {0}"
    # {0}: key
    "expected-a-number-at": "Expected a number at {0}"
    # {0}: id
    "incomplete-backup": "Incomplete backup: {0}"
    # {0}: key
    "incorrect-value-type-at": "Incorrect value type at {0}"
    # {0}: dynamic value (keep this placeholder)
    "install-the-required-plugins-first": "Install the required plugins first: {0}"
    "invalid-preset-or-backup-id": "Invalid preset or backup ID"
    # {0}: dynamic value (keep this placeholder)
    # {1}: key
    "invalid-shop": "Invalid shop {0}.{1}"
    # {0}: name
    "invalid-yaml-in": "Invalid YAML in {0}"
    "linked-paths-are-not-supported-for-preset-files": "Linked paths are not supported for preset files"
    # {0}: category
    "missing-items-in-shop-category": "Missing items in shop category {0}"
    # {0}: dynamic value (keep this placeholder)
    "missing-shop-material": "Missing shop material: {0}"
    "path-must-stay-inside-the-plugin-folder": "Path must stay inside the plugin folder"
    "preset-config-is-empty": "Preset config is empty"
    # {0}: dynamic value (keep this placeholder)
    "preset-file-exceeds-2-mib": "Preset file exceeds 2 MiB: {0}"
    # {0}: error details
    "preset-installation-failed-previous-configuration-recovery-was-at": "Preset installation failed; previous configuration recovery was attempted. {0}"
    "preset-shops-must-contain-categories": "Preset shops must contain categories"
    # {0}: dynamic value (keep this placeholder)
    "shop-amount-must-be-1-64": "Shop amount must be 1-64: {0}"
    "spawner-interval-must-be-at-least-1-second": "Spawner interval must be at least 1 second"
    "text": ", "
    # {0}: id
    "unknown-preset": "Unknown preset: {0}"
    # {0}: id
    "unsupported-preset-format": "Unsupported preset format: {0}"
  price-tracker:
    # {0}: formatted amount
    "average": "&7Average: &a{0}"
    "average-sale-prices-from-auctions-and-markets": "&7Average sale prices from auctions and markets."
    # {0}: formatted amount
    "last": "&7Last: &a{0}"
    "price-tracker": "&6&lPrice Tracker"
    # {0}: dynamic value (keep this placeholder)
    "sales": "&7Sales: &e{0}"
    # {0}: key
    "text": "&f{0}"
  region-rtp:
    "finding-a-safe-destination-rtp-leave-to-cancel": "Finding a safe destination. /rtp leave to cancel."
    "finding-a-safe-wilderness-location": "&7Finding a safe wilderness location..."
    # {0}: dimension
    "joined-the-rtp-queue-waiting-for-a-partner-rtp-leave-to-cancel": "&aJoined the {0} RTP queue. &7Waiting for a partner; /rtp leave to cancel."
    "no-permission-for-rtp-queues": "&cNo permission for RTP queues."
    "no-safe-rtp-location-found-try-again": "No safe RTP location found. Try again."
    "partner-found-finding-a-safe-location-together": "&aPartner found! Finding a safe location together."
    "rtp-cancelled": "RTP cancelled."
    "rtp-cancelled-a-player-became-unavailable": "RTP cancelled: a player became unavailable."
    "rtp-cancelled-a-player-disconnected": "RTP cancelled: a player disconnected."
    "rtp-cancelled-a-player-moved-during-the-countdown": "RTP cancelled: a player moved during the countdown."
    "rtp-cancelled-a-player-moved-or-teleported-during-the-countdown": "RTP cancelled: a player moved or teleported during the countdown."
    "rtp-cancelled-because-a-player-teleported": "RTP cancelled because a player teleported."
    "rtp-cancelled-destination-became-unsafe": "RTP cancelled: destination became unsafe."
    "rtp-cancelled-no-cooldown-was-charged": "RTP cancelled. No cooldown was charged."
    "rtp-chunk-loading-failed": "RTP chunk loading failed."
    "rtp-complete": "RTP complete."
    "rtp-complete-your-partner-is-nearby": "RTP complete. Your partner is nearby."
    "rtp-countdown-stay-still-rtp-leave-to-cancel": "RTP countdown: stay still. /rtp leave to cancel."
    "rtp-dimension-or-queues-unavailable": "&cRTP dimension or queues unavailable."
    # {0}: dynamic value (keep this placeholder)
    "rtp-in-seconds-stay-still-moving-cancels-the-whole-match": "&7RTP in {0} seconds. Stay still; moving cancels the whole match."
    "rtp-is-on-cooldown": "&cRTP is on cooldown."
    "rtp-queue-timed-out-join-again-when-ready": "&7RTP queue timed out. Join again when ready."
    "rtp-queues-are-disabled": "&cRTP queues are disabled."
    "rtp-request-timed-out": "RTP request timed out."
    "rtp-searches-are-busy-try-again-shortly": "&cRTP searches are busy. Try again shortly."
    "that-rtp-dimension-is-disabled-or-unavailable": "&cThat RTP dimension is disabled or unavailable."
    "the-rtp-queue-is-full": "&cThe RTP queue is full."
    # {0}: dynamic value (keep this placeholder)
    "waiting-for-a-partner-in-rtp-leave-to-cancel": "Waiting for a partner in {0}. /rtp leave to cancel."
    "you-already-have-an-rtp-request-rtp-leave-to-cancel-it": "&eYou already have an RTP request. /rtp leave to cancel it."
    "you-are-not-waiting-for-rtp": "You are not waiting for RTP."
    "your-return-was-blocked-contact-staff": "&cYour return was blocked. Contact staff."
  rtp:
    "a-protection-plugin-blocked-your-return-contact-staff-for-help-re": "&cA protection plugin blocked your return. Contact staff for help returning."
    "finding-a-safe-destination-rtp-leave-to-cancel": "Finding a safe destination. /rtp leave to cancel."
    "finding-a-safe-wilderness-location": "&7Finding a safe wilderness location..."
    # {0}: dimension
    "joined-the-rtp-queue-waiting-for-a-partner-rtp-leave-to-cancel": "&aJoined the {0} RTP queue. &7Waiting for a partner; /rtp leave to cancel."
    "no-permission-for-rtp-queues": "&cNo permission for RTP queues."
    "no-safe-rtp-location-found-try-again": "No safe RTP location found. Try again."
    "partner-found-finding-a-safe-location-together": "&aPartner found! Finding a safe location together."
    "rtp-cancelled": "RTP cancelled."
    "rtp-cancelled-a-player-became-unavailable": "RTP cancelled: a player became unavailable."
    "rtp-cancelled-a-player-moved-during-the-countdown": "RTP cancelled: a player moved during the countdown."
    "rtp-cancelled-a-player-or-destination-became-unavailable": "RTP cancelled: a player or destination became unavailable."
    "rtp-cancelled-a-player-or-destination-became-unsafe": "RTP cancelled: a player or destination became unsafe."
    "rtp-cancelled-because-a-player-teleported": "RTP cancelled because a player teleported."
    "rtp-cancelled-because-the-server-is-stopping": "RTP cancelled because the server is stopping."
    "rtp-cancelled-by-server-protection-no-cooldown-was-charged": "RTP cancelled by server protection. No cooldown was charged."
    "rtp-chunk-loading-failed-try-again": "RTP chunk loading failed. Try again."
    "rtp-complete": "RTP complete."
    "rtp-complete-your-partner-is-nearby": "RTP complete. Your partner is nearby."
    "rtp-countdown-stay-still-rtp-leave-to-cancel": "RTP countdown: stay still. /rtp leave to cancel."
    # {0}: dynamic value (keep this placeholder)
    "rtp-in-seconds-stay-still-moving-cancels-the-whole-match": "&7RTP in {0} seconds. Stay still; moving cancels the whole match."
    "rtp-is-on-cooldown": "&cRTP is on cooldown."
    "rtp-match-cancelled-a-player-or-dimension-became-unavailable": "&cRTP match cancelled: a player or dimension became unavailable."
    "rtp-overworld-nether-end-or-rtp-queue-dimension-or-rtp-leave": "&e/rtp [overworld|nether|end] &7or &e/rtp queue [dimension] &7or &e/rtp leave"
    "rtp-queue-timed-out-join-again-when-ready": "&7RTP queue timed out. Join again when ready."
    "rtp-queues-are-disabled": "&cRTP queues are disabled."
    "rtp-searches-are-busy-try-again-shortly": "&cRTP searches are busy. Try again shortly."
    "that-rtp-destination-is-unavailable-or-requires-permission": "&cThat RTP destination is unavailable or requires permission."
    "that-rtp-dimension-is-disabled-or-unavailable": "&cThat RTP dimension is disabled or unavailable."
    "the-rtp-queue-is-full": "&cThe RTP queue is full."
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    "waiting-for-a-partner-in-queued-rtp-leave-to-cancel": "Waiting for a partner in {0} ({1} queued). /rtp leave to cancel."
    "you-already-have-an-rtp-request-rtp-leave-to-cancel-it": "&eYou already have an RTP request. /rtp leave to cancel it."
    "you-are-not-waiting-for-rtp": "&7You are not waiting for RTP."
    "you-are-not-waiting-for-rtp-0ce41a": "You are not waiting for RTP."
  rtp-zone-menu:
    "dimensions": "Dimensions"
    "next": "Next"
    "no-configured-zones-available": "No configured zones available"
    # {0}: dynamic value (keep this placeholder)
    "paired": "{0} — Paired"
    "previous": "Previous"
    # {0}: dynamic value (keep this placeholder)
    "solo": "{0} — Solo"
    "staff-can-configure-named-regions-in-travel-zones-in-config-yml": "&7Staff can configure named regions in travel.zones in config.yml."
    # {0}: name
    "text": "&b{0}"
  sell-axe:
    # {0}: formatted amount
    "container-sale": "&aContainer sale: {0}"
    "crystal-sell-axe": "&dCrystal Sell Axe"
    "manage-this-shop-s-stock-through-its-inventory-the-sell-axe-canno": "&cManage this shop's stock through its inventory; the Sell Axe cannot sell shop stock."
    "no-supported-plain-items-to-sell": "&7No supported plain items to sell."
    "sells-plain-contents-at-the-best-available-price": "&7Sells plain contents at the best available price."
    "shift-right-click-a-chest-or-barrel": "&7Shift-right-click a chest or barrel."
  server-features:
    # {0}: player name
    "accepted-your-friend-request": "&a{0} accepted your friend request."
    "balance-updated": "&aBalance updated."
    # {0}: formatted amount
    "base-value-of-held-stack-orders-may-pay-more": "&7Base value of held stack: &a{0}&7. Orders may pay more."
    "donsup-money-e-donsup-shardadmin-donsup-rank": "&e/donsup money <give|take> <player> <amount>\n& e/donsup shardadmin <give|take> <player> <amount>\n&e/donsup rank <player> <member|plus|elite|legend> <days>"
    "donsup-reload-money-shardadmin-rank": "&e/donsup reload | money | shardadmin | rank"
    "following": "Following"
    "friend": "&e/friend <add|accept|deny|remove> <player>"
    "friend-limit-reached-100": "&cFriend limit reached (100)."
    "friend-removed": "&7Friend removed."
    "friend-request-declined": "&7Friend request declined."
    "friend-request-sent-expires-in-2-minutes": "&aFriend request sent (expires in 2 minutes)."
    "friend-request-unavailable": "&cFriend request unavailable."
    # {0}: player name
    # {1}: dynamic value (keep this placeholder)
    "friends": "&a[Friends] {0}: &f{1}"
    "ignore": "&e/ignore <player>"
    "insufficient-funds-or-balance-limit": "&cInsufficient funds or balance limit."
    "invalid-action-rank-or-amount": "&cInvalid action, rank or amount."
    "messages-must-be-1-256-characters": "&cMessages must be 1-256 characters."
    "msg": "&e/msg <player> <message>"
    "no-active-request": "&cNo active request."
    "no-one-to-reply-to": "&cNo one to reply to."
    "no-permission": "&cNo permission."
    "no-sales-yet": "No sales yet."
    "player-ignored": "&7Player ignored."
    "player-must-have-joined-before": "&cPlayer must have joined before."
    "player-unignored": "&aPlayer unignored."
    "rank-updated": "&aRank updated."
    "sell-history": "Sell History"
    # {0}: player name
    # {1}: player name
    "sent-a-friend-request-friend-accept": "&e{0} &7sent a friend request. &f/friend accept {1}"
    "server-rules": "Server Rules"
    "spawn-saved": "&aSpawn saved."
    # {0}: name
    "text": "&e/{0} <player>"
    "that-player-cannot-receive-messages": "&cThat player cannot receive messages."
    "that-player-has-too-many-pending-requests": "&cThat player has too many pending requests."
    "that-player-is-offline": "&cThat player is offline."
    "unknown-player": "&cUnknown player."
    "use-follow": "Use /follow <player>."
    "use-this-command-in-game": "&cUse this command in game."
    "wait-before-sending-another-request": "&cWait before sending another request."
    # {0}: player name
    # {1}: dynamic value (keep this placeholder)
    "you": "&d{0} → you: &f{1}"
    # {0}: player name
    # {1}: dynamic value (keep this placeholder)
    "you-765019": "&dYou → {0}: &f{1}"
    # {0}: player name
    "you-are-now-friends-with": "&aYou are now friends with {0}."
    # {0}: player name
    "your-friend-is-online": "&aYour friend &f{0} &ais online."
  shop-holograms:
    "paused": "&7[Paused] "
    "text": "&e"
    # {0}: status
    # {1}: dynamic value (keep this placeholder)
    # {2}: item/material display name
    # {3}: formatted amount
    "x": "{0} {1}x {2} &a{3}"
  shopping-lists:
    "back": "Back"
    # {0}: dynamic value (keep this placeholder)
    "delete": "Delete {0}"
    "delete-selection": "Delete selection"
    "delete-this-saved-shopping-selection": "Delete this saved shopping selection?"
    "quickbuy-delete": "/quickbuy delete <name>"
    "quickbuy-loadout": "&e/quickbuy loadout <name>"
    "quickbuy-open": "/quickbuy open <name>"
    "quickbuy-save": "&e/quickbuy save <name>"
    "quickbuy-save-for-the-held-item-quickbuy-loadout-for-your-hotbar": "/quickbuy save <name> for the held item; /quickbuy loadout <name> for your hotbar."
    "quickbuy-saved-save-loadout-open-delete": "&e/quickbuy saved | save <name> | loadout <name> | open <name> | delete <name>"
    "save-held-item": "Save held item"
    "save-hotbar-loadout": "Save hotbar loadout"
    # {0}: count
    "saved-item-s-click-to-browse": "{0} saved item(s) — click to browse"
    "saved-selections-live-market": "Saved selections / live market"
    # {0}: dynamic value (keep this placeholder)
    "saved-shopping-selection-your-items-were-kept": "&aSaved shopping selection '{0}'. Your items were kept."
    # {0}: error details
    "text": "&c{0}"
    # {0}: title
    "text-539ee5": "&b{0}"
    "use-quickbuy-loadout": "Use /quickbuy loadout <name>"
    "use-quickbuy-save": "Use /quickbuy save <name>"
    # {0}: dynamic value (keep this placeholder)
    "wanted-browse-current-exact-matches-confirm-price-before-buying": "Wanted: {0}. Browse current exact matches; confirm price before buying."
    "your-actual-items-are-unaffected": "Your actual items are unaffected"
  shopping-store:
    "hold-an-item-or-put-items-in-your-hotbar-for-a-loadout": "Hold an item, or put items in your hotbar for a loadout."
    "use-1-24-letters-numbers-underscores-or-hyphens-for-the-name": "Use 1–24 letters, numbers, underscores or hyphens for the name."
    "your-saved-shopping-list-is-full-delete-an-entry-first": "Your saved shopping list is full. Delete an entry first."
  smp-command:
    # {0}: dynamic value (keep this placeholder)
    # {1}: days
    "added-premium-to-for-days": "&aAdded premium to &e{0}&a for &e{1} days&a."
    "afk-rewards-disabled": "&cAFK rewards disabled."
    "afk-rewards-enabled-move-to-disable": "&aAFK rewards enabled. Move to disable."
    # {0}: dynamic value (keep this placeholder)
    "applied-use-smp-preset-rollback-to-undo": "&aApplied {0}. Use /smp preset rollback to undo."
    # {0}: dynamic value (keep this placeholder)
    "apply-smp-preset-apply": "&eApply: /smp preset apply {0}"
    # {0}: dynamic value (keep this placeholder)
    "available-presets": "&eAvailable presets: &f{0}"
    "buy-and-sell-prices-must-be-0-or-higher": "&cBuy and sell prices must be 0 or higher."
    "claimed-premium-kit": "&aClaimed premium kit."
    "could-not-create-order-you-need-enough-money-for-escrow": "&cCould not create order. You need enough money for escrow."
    "could-not-list-item-check-listing-limit-and-listing-tax-money": "&cCould not list item. Check listing limit and listing tax money."
    "created-exact-item-order-your-sample-item-was-kept": "&aCreated exact-item order. Your sample item was kept."
    # {0}: amount
    # {1}: item/material display name
    "created-order-for-x": "&aCreated order for &e{0}x {1}&a."
    # {0}: dynamic value (keep this placeholder)
    "deleted-home": "&aDeleted home &e{0}&a."
    "disabled": "&cdisabled"
    # {0}: status
    "dynamic-pricing-is": "&eDynamic pricing is {0}&e."
    # {0}: status
    "dynamic-pricing-is-now": "&eDynamic pricing is now {0}&e."
    "enabled": "&aenabled"
    "fed": "&aFed."
    # {0}: dynamic value (keep this placeholder)
    "feed-cooldown-minutes": "&cFeed cooldown: &e{0} minutes&c."
    # {0}: dynamic value (keep this placeholder)
    "gave-crate-placer-for": "&aGave crate placer for &e{0}&a."
    "gave-custom-spawners": "&aGave custom spawners."
    # {0}: player name
    "gave-drill-to": "&aGave drill to &e{0}&a."
    "hold-a-damageable-item": "&cHold a damageable item."
    "hold-an-item-and-check-quantity-price-balance-and-order-limit": "&cHold an item and check quantity, price, balance and order limit."
    "hold-an-item-and-provide-a-valid-price": "&cHold an item and provide a valid price."
    "home-limit-reached-premium-adds-more-homes": "&cHome limit reached. Premium adds more homes."
    "home-not-found": "&cHome not found."
    # {0}: error details
    "install-failed": "&cInstall failed: {0}"
    "invalid-amount-or-not-enough-money": "&cInvalid amount or not enough money."
    "invalid-material-amount-or-price": "&cInvalid material, amount or price."
    "invalid-player-or-amount": "&cInvalid player or amount."
    # {0}: error details
    "invalid-preset": "&cInvalid preset: {0}"
    # {0}: formatted amount
    "listed-held-item-for": "&aListed held item for {0}."
    "make-room-for-the-whole-kit-first-your-cooldown-has-not-started": "&cMake room for the whole kit first. Your cooldown has not started."
    # {0}: dynamic value (keep this placeholder)
    "missing-plugins": "&cMissing plugins: {0}"
    # {0}: formatted amount
    # {1}: shard amount
    "money-shards": "&7Money: &a{0} &8| &7Shards: &d{1}"
    "night-vision-is-a-premium-perk": "&cNight vision is a premium perk."
    "night-vision-is-disabled-by-this-server": "&cNight vision is disabled by this server."
    # {0}: status
    "night-vision-is-now": "&bNight vision is now {0}&b."
    "no-matching-order-is-buying-this-exact-item": "&7No matching order is buying this exact item."
    "no-permission": "&cNo permission."
    "off": "&cOFF"
    "on": "&aON"
    "only-players-can-pay-money": "&cOnly players can pay money."
    "only-players-can-use-that-command": "&cOnly players can use that command."
    # {0}: player name
    # {1}: formatted amount
    "paid": "&aPaid &e{0} &a{1}."
    # {0}: player name
    # {1}: formatted amount
    "placed-bounty-on-for": "&aPlaced bounty on &e{0}&a for {1}."
    "player-not-found": "&cPlayer not found."
    "portable-workbench-is-disabled": "&cPortable workbench is disabled."
    # {0}: dynamic value (keep this placeholder)
    "premium-kit-cooldown-minutes": "&cPremium kit cooldown: &e{0} minutes&c."
    "premium-kit-is-not-configured": "&cPremium kit is not configured."
    # {0}: formatted amount
    # {1}: player name
    "received-from": "&aReceived {0} from &e{1}&a."
    # {0}: error details
    "reload-rejected-fix-the-configuration-and-try-again": "&cReload rejected; fix the configuration and try again: {0}"
    "reloaded-smp-builder-configs": "&aReloaded SMP builder configs."
    # {0}: dynamic value (keep this placeholder)
    "repair-cooldown-minutes": "&cRepair cooldown: &e{0} minutes&c."
    "repaired-held-item": "&aRepaired held item."
    "restored-the-previous-config-and-shops-player-data-was-preserved": "&aRestored the previous config and shops. Player data was preserved."
    # {0}: error details
    "rollback-failed": "&cRollback failed: {0}"
    "server-name-saved-menus-tab-and-sidebar-use-the-new-name-restart": "&aServer name saved. Menus, tab and sidebar use the new name. Restart for the pause-screen heading."
    # {0}: name
    "set-home": "&aSet home &e{0}&a."
    # {0}: dynamic value (keep this placeholder)
    # {1}: value
    "set-sell-multiplier-for-to-x": "&aSet sell multiplier for &e{0}&a to &e{1}x&a."
    # {0}: count
    "settings-change-branding-is-preserved-by-default-player-data-is-u": "&e{0} settings change. &7Branding is preserved by default; player data is untouched."
    "smp-preset-apply-rollback": "&e/smp preset <list|preview <name>|apply <name>|rollback>"
    "smp-reload": "&e/smp reload"
    "smp-setup-opens-the-installer-smp-preset-preview": "&e/smp setup &7opens the installer. &e/smp preset preview <name>"
    # {0}: formatted amount
    "sold-matching-held-items-for": "&aSold matching held items for {0}"
    # {0}: error details
    "text": "&c{0}"
    # {0}: dynamic value (keep this placeholder)
    # {1}: dynamic value (keep this placeholder)
    "text-84dc37": "&e{0} &7- {1}"
    "that-player-has-payments-disabled": "&cThat player has payments disabled."
    "this-is-a-premium-perk": "&cThis is a premium perk."
    "trading-is-stopped-pending-server-recovery": "&cTrading is stopped pending server recovery."
    "usage-bounty-or-bounty-set": "&eUsage: /bounty <player> <amount> &7or &e/bounty set <player> <amount>"
    "usage-creator-crate-wand": "&eUsage: /creator crate wand <type>"
    "usage-creator-dynamic": "&eUsage: /creator dynamic <on|off>"
    "usage-creator-key": "&eUsage: /creator key <crateType> <amount>"
    "usage-creator-shop-add": "&eUsage: /creator shop add <category> <id> <buy> <sell> <amount>"
    "usage-delhome": "&eUsage: /delhome <name>"
    "usage-drill-give": "&eUsage: /drill give <player> <tier>"
    "usage-drills-or-drill-give": "&eUsage: /drills &7or &e/drill give <player> <tier>"
    "usage-duel-accept": "&eUsage: /duel accept <player>"
    "usage-duel-arena-set-or-duel-arena-delete": "&eUsage: /duel arena set <id> <1|2> &7or &e/duel arena delete <id>"
    # {0}: dynamic value (keep this placeholder)
    "usage-list": "&eUsage: /{0} list <price>"
    # {0}: dynamic value (keep this placeholder)
    "usage-list-cancel": "&eUsage: /{0} [list <price>|cancel <id>]"
    "usage-orders-create": "&eUsage: /orders create <material> <amount> <priceEach>"
    "usage-orders-create-hand-deliver-claim": "&eUsage: /orders [create <material> <amount> <priceEach>|hand <amount> <priceEach>|deliver <id>|claim <id>]"
    "usage-orders-hand-copies-the-held-item-s-exact-properties": "&eUsage: /orders hand <amount> <priceEach> (copies the held item's exact properties)"
    "usage-pay": "&eUsage: /pay <player> <amount>"
    "usage-sell": "&eUsage: /sell [gui|hand|all|exact|shulker|options|claim]"
    "usage-smp-brand": "&eUsage: /smp brand <Your Server Name>"
    "usage-smp-givekey": "&eUsage: /smp givekey <player> <type> <amount>"
    "usage-smp-pay": "&eUsage: /smp pay <player> <amount>"
    "usage-smp-premium": "&eUsage: /smp premium <player> <days>"
    "usage-smp-setsellmulti": "&eUsage: /smp setsellmulti <player> <multiplier>"
    "usage-spawners-give": "&eUsage: /spawners give <type> <amount>"
    "usage-spawners-give-8601de": "&eUsage: /spawners [give <type> <amount>]"
    "use-smp-preset-list-or-smp-preset-apply": "&eUse /smp preset list or /smp preset apply <name>."
    "you-do-not-have-enough-money": "&cYou do not have enough money."
  social:
    "a-teammate-is-using-this-vault-try-again-when-they-close-it": "&eA teammate is using this vault. Try again when they close it."
    # {0}: formatted amount
    "balance": "&7Balance: &a{0}"
    "click-to-teleport": "&aClick to teleport."
    "create-a-team": "&aCreate A Team"
    "create-shops-farms-casinos-and-bases": "&7Create shops, farms, casinos and bases."
    # {0}: name
    "created-team": "&aCreated team &e{0}&a."
    # {0}: dynamic value (keep this placeholder)
    "current": "&7Current: {0}"
    # {0}: name
    "deleted-player-warp": "&cDeleted player warp &e{0}&c."
    "enter-a-positive-finite-amount-up-to-1-trillion": "&cEnter a positive, finite amount up to 1 trillion."
    "friendly-fire": "&eFriendly Fire"
    "friendly-fire-is-disabled-for-your-team": "&cFriendly fire is disabled for your team."
    # {0}: dynamic value (keep this placeholder)
    "friendly-fire-is-now": "&eFriendly fire is now {0}&e."
    "invalid-team-or-player": "&cInvalid team or player."
    # {0}: player name
    "invited": "&aInvited &e{0}&a."
    # {0}: player name
    # {1}: dynamic value (keep this placeholder)
    # {2}: dynamic value (keep this placeholder)
    "invited-you-to-team-use-team-join": "&e{0} &ainvited you to team &e{1}&a. Use &f/team join {2}&a."
    # {0}: dynamic value (keep this placeholder)
    "joined-team": "&aJoined team &e{0}&a."
    "leader-cannot-leave-delete-reassign-is-reserved-for-admin-cleanup": "&cLeader cannot leave. Delete/reassign is reserved for admin cleanup."
    "leader-team-friendlyfire": "&7Leader: /team friendlyfire"
    "leave-your-current-team-first": "&cLeave your current team first."
    # {0}: dynamic value (keep this placeholder)
    "left-team": "&cLeft team &e{0}&c."
    "left-teleport": "&7Left: teleport"
    "members": "&fMembers"
    "no-invite-for-that-team": "&cNo invite for that team."
    "no-team-home-set": "&cNo team home set."
    "none": "None"
    "not-enough-money": "&cNot enough money."
    "off": "&aOff"
    "off-f37a84": "&aOFF"
    "on": "&cOn"
    "on-b38b7b": "&cON"
    "only-the-leader-can-change-friendly-fire": "&cOnly the leader can change friendly fire."
    "only-the-leader-can-invite": "&cOnly the leader can invite."
    "only-the-leader-can-withdraw": "&cOnly the leader can withdraw."
    # {0}: dynamic value (keep this placeholder)
    "owner": "&7Owner: &f{0}"
    "player-warps": "&b&lPlayer Warps"
    # {0}: name
    "promoted-warp": "&aPromoted warp &e{0}&a."
    # {0}: formatted amount
    "promotion-costs": "&cPromotion costs &e{0}&c."
    # {0}: name
    "set-player-warp": "&aSet player warp &e{0}&a."
    "set-team-home": "&aSet team home."
    "set-team-sethome": "&7Set: /team sethome"
    "shared-team-storage": "&7Shared team storage."
    # {0}: dynamic value (keep this placeholder)
    "team": "&7Team: &f{0}"
    # {0}: player name
    # {1}: dynamic value (keep this placeholder)
    "team-37bbcb": "&b[Team] &e{0}&7: &f{1}"
    "team-bank": "&6Team Bank"
    # {0}: formatted amount
    "team-bank-60b390": "&aTeam bank: &e{0}&a."
    "team-bank-deposit": "&7/team bank deposit <amount>"
    "team-bank-is-too-low": "&cTeam bank is too low."
    "team-home": "&cTeam Home"
    "team-not-found": "&cTeam not found."
    "team-vault": "&dTeam Vault"
    "teams-clans": "&b&lTeams / Clans"
    "text": "&e★ "
    "text-a7f0cc": "&f"
    "that-team-already-exists": "&cThat team already exists."
    "that-warp-is-already-promoted": "&eThat warp is already promoted."
    "unknown": "Unknown"
    "usage-pwarp-delete": "&eUsage: /pwarp delete <name>"
    "usage-pwarp-promote": "&eUsage: /pwarp promote <name>"
    "usage-pwarp-set": "&eUsage: /pwarp set <name>"
    "usage-team-bank": "&eUsage: /team bank <deposit|withdraw> <amount>"
    "usage-team-chat": "&eUsage: /team chat <message>"
    "usage-team-create": "&eUsage: /team create <name>"
    "use-a-team-name-of-1-32-letters-numbers-underscores-or-hyphens": "&cUse a team name of 1-32 letters, numbers, underscores or hyphens."
    "use-a-warp-name-of-1-32-letters-numbers-underscores-or-hyphens": "&cUse a warp name of 1-32 letters, numbers, underscores or hyphens."
    "use-pwarp-set": "&7Use &f/pwarp set <name>&7."
    "use-team-create": "&7Use &f/team create <name>&7."
    "use-team-create-to-start": "&7Use &f/team create <name> &7to start."
    # {0}: dynamic value (keep this placeholder)
    "visits": "&7Visits: &e{0}"
    "warp-not-found": "&cWarp not found."
    "you-are-not-in-a-team": "&cYou are not in a team."
    "you-do-not-own-that-warp": "&cYou do not own that warp."
  tool:
    "break-ore-veins-and-logs-faster": "&7Break ore veins and logs faster."
    "click-to-buy": "&aClick to buy"
    # {0}: dynamic value (keep this placeholder)
    "cost-shards": "&7Cost: &d{0} shards"
    # {0}: dynamic value (keep this placeholder)
    "drill": "&e{0} Drill"
    # {0}: dynamic value (keep this placeholder)
    "drill-666972": "&b{0} Drill"
    # {0}: dynamic value (keep this placeholder)
    "drill-mined-blocks": "&bDrill mined &e{0} &bblocks."
    # {0}: dynamic value (keep this placeholder)
    "drill-tier": "&8Drill tier: {0}"
    # {0}: dynamic value (keep this placeholder)
    "gave-drill": "&aGave &e{0} Drill&a."
    "make-inventory-space-before-buying-a-drill": "&cMake inventory space before buying a drill."
    # {0}: dynamic value (keep this placeholder)
    "max-blocks": "&7Max blocks: &e{0}"
    # {0}: dynamic value (keep this placeholder)
    "purchased-drill": "&aPurchased &e{0} Drill&a."
    "vein-miner-drills": "&b&lVein Miner Drills"
    "vein-mines-matching-ores-and-logs": "&7Vein mines matching ores and logs."
    # {0}: dynamic value (keep this placeholder)
    "you-need-shards-to-buy-that-drill": "&cYou need &d{0} shards &cto buy that drill."
    # {0}: shard amount
    "your-shards": "&7Your shards: &d{0}"
  trade:
    "a-player-is-already-trading": "&cA player is already trading."
    "confirmed": "&aConfirmed"
    "denied-trade-request": "&cDenied trade request."
    "invalid-player": "&cInvalid player."
    "left-confirm": "&aLeft Confirm"
    "left-player-confirm": "&7Left player confirm."
    "meet-the-other-player-nearby-before-opening-a-trade-on-folia": "&eMeet the other player nearby before opening a trade on Folia."
    # {0}: formatted amount
    "money": "&7Money: &a{0}"
    "no-matching-trade-request": "&cNo matching trade request."
    "not-confirmed": "&cNot confirmed"
    "player-a": "Player A"
    "player-b": "Player B"
    "right-confirm": "&aRight Confirm"
    "right-player-confirm": "&7Right player confirm."
    # {0}: player name
    "sent-trade-request-to": "&aSent trade request to &e{0}&a."
    # {0}: shard amount
    "shards": "&7Shards: &d{0}"
    "shards-must-be-a-whole-number-between-0-and-2147483647": "&cShards must be a whole number between 0 and 2147483647."
    # {0}: player name
    "text": "&a{0}"
    # {0}: player name
    "text-539ee5": "&b{0}"
    "trade-cancelled-because-players-left-the-same-region": "&eTrade cancelled because players left the same region."
    "trade-completed": "&aTrade completed."
    "trade-failed-insufficient-funds-invalid-amount-or-saving-failed-n": "&cTrade failed: insufficient funds, invalid amount, or saving failed. No payment was taken."
    "usage-during-trade-trade-money": "&eUsage during trade: /trade money <amount>"
    "usage-during-trade-trade-shards": "&eUsage during trade: /trade shards <amount>"
    "usage-trade": "&eUsage: /trade <player|accept|deny|money|shards>"
    # {0}: player name
    # {1}: player name
    "wants-to-trade-use-trade-accept": "&e{0} &awants to trade. Use &f/trade accept {1}&a."
  trade-returns:
    "make-inventory-space-and-use-trade-claim-for-returned-items": "&eMake inventory space and use /trade claim for returned items."
  travel:
    "asks-to-teleport-to-you": " &7asks to teleport to you."
    "asks-you-to-teleport-to-them": " &7asks you to teleport to them."
    "combat-tagged-teleports-are-temporarily-blocked": "&cCombat tagged. Teleports are temporarily blocked."
    "destination-is-unavailable": "&cDestination is unavailable."
    "leave-the-duel-before-teleporting": "&cLeave the duel before teleporting."
    "no-matching-request": "&cNo matching request."
    "no-pending-requests": "&cNo pending requests."
    "player-unavailable": "&cPlayer unavailable."
    "request-declined": "&7Request declined."
    "request-sent-expires-in-60-seconds": "&aRequest sent; expires in 60 seconds."
    "rtp-cancelled-because-a-player-died": "RTP cancelled because a player died."
    "rtp-cancelled-because-a-player-disconnected": "RTP cancelled because a player disconnected."
    "rtp-cancelled-because-a-player-entered-combat": "RTP cancelled because a player entered combat."
    "rtp-cancelled-because-a-player-took-damage": "RTP cancelled because a player took damage."
    "rtp-cancelled-by-another-teleport-request": "RTP cancelled by another teleport request."
    "teleport-cancelled-because-you-moved-or-took-damage": "&cTeleport cancelled because you moved or took damage."
    "teleport-was-cancelled": "&cTeleport was cancelled."
    "teleported": "&aTeleported."
    # {0}: dynamic value (keep this placeholder)
    "teleporting-in-seconds-stay-still": "&7Teleporting in {0} seconds. Stay still."
    # {0}: dynamic value (keep this placeholder)
    "teleporting-is-blocked-during-combat-for-seconds": "&cTeleporting is blocked during combat for {0} seconds."
    "this-player-has-too-many-requests": "&cThis player has too many requests."
    "this-player-is-not-accepting-teleport-requests": "&cThis player is not accepting teleport requests."
    # {0}: player name
    # {1}: dynamic value (keep this placeholder)
    # {2}: player name
    "tpaccept": "&e{0}{1} &f/tpaccept {2}"
    "wait-before-requesting-again": "&cWait before requesting again."

  sell-chest:
    "empty-cursor": "&ePut the item on your cursor away, then open /sell again."
    "make-space": "&eMake room in your inventory, then use /sell claim to collect your saved items."
    "title": "Sell - close to sell"
    "instructions": "&ePlace items in this chest, then close it to sell. &7Unsellable and custom items are returned. /sell options opens more selling tools."
    "sold": "&aSold deposited items for {0}."
    "nothing-sold": "&7No deposited items were sellable. Your items have been returned or saved for collection."
    "returned": "&aCollected your saved sell-menu items."
    "folia-tools": "&eThe deposit chest is unavailable on Folia. Use these selling tools instead."


===== src/main/resources/menus.yml =====

# Presentation configuration. Reload with /donsup reload; pause changes require a full restart.
# %server% uses branding.server-name. Native labels support MiniMessage tags; inventory labels strip those tags.
# Commands always run AS THE CLICKING PLAYER, with their normal permissions. Hiding a button does not disable a command.
# New buttons: add a definition, then add its ID to order. Slots are zero-based. Keep close-slot free.
dashboard:
  summary: '<gray>Money <green>%money% <dark_gray>• <gray>Shards <light_purple>%shards%'
  columns: 2
  inventory-rows: 6
  close-slot: 49
  order: ["settings", "auction", "orders", "quickbuy", "sell", "rtp", "homes", "friends", "keys", "shards", "spawners", "chestshops", "bounties", "stats", "leaderboards", "kits", "daily", "premium", "duels", "drills", "teams", "warps", "prices", "rules", "modules", "admin"]
  buttons:
    settings:
      label: "Settings"
      icon: COMPARATOR
      slot: 10
      command: "settings"
      permission: ""
      enabled: true
      lore: []
    auction:
      label: "Auction House"
      icon: GOLD_INGOT
      slot: 11
      command: "ah"
      permission: ""
      enabled: true
      lore: []
    orders:
      label: "Orders"
      icon: WRITABLE_BOOK
      slot: 12
      command: "orders"
      permission: ""
      enabled: true
      lore: []
    quickbuy:
      label: "Quick Buy"
      icon: CHEST
      slot: 13
      command: "shop"
      permission: ""
      enabled: true
      lore: []
    sell:
      label: "Sell"
      icon: EMERALD
      slot: 14
      command: "sell"
      permission: ""
      enabled: true
      lore: []
    rtp:
      label: "Random Teleport"
      icon: ENDER_PEARL
      slot: 15
      command: "rtp"
      permission: ""
      enabled: true
      lore: []
    homes:
      label: "Homes"
      icon: RED_BED
      slot: 16
      command: "homes"
      permission: ""
      enabled: true
      lore: []
    friends:
      label: "Friends"
      icon: PLAYER_HEAD
      slot: 19
      command: "friends"
      permission: ""
      enabled: true
      lore: []
    keys:
      label: "Keys / Crates"
      icon: TRIPWIRE_HOOK
      slot: 20
      command: "keys"
      permission: ""
      enabled: true
      lore: []
    shards:
      label: "Shard Shop"
      icon: AMETHYST_SHARD
      slot: 21
      command: "shards"
      permission: ""
      enabled: true
      lore: []
    spawners:
      label: "Spawners"
      icon: SPAWNER
      slot: 22
      command: "spawners"
      permission: ""
      enabled: true
      lore: []
    chestshops:
      label: "Player Chest Shops"
      icon: BARREL
      slot: 23
      command: "chestshop"
      permission: ""
      enabled: true
      lore: []
    bounties:
      label: "Bounties"
      icon: TARGET
      slot: 24
      command: "bounty"
      permission: ""
      enabled: true
      lore: []
    stats:
      label: "Statistics"
      icon: BOOK
      slot: 25
      command: "stats"
      permission: ""
      enabled: true
      lore: []
    leaderboards:
      label: "Leaderboards"
      icon: GOLD_BLOCK
      slot: 28
      command: "leaderboard"
      permission: ""
      enabled: true
      lore: []
    kits:
      label: "Kits"
      icon: CHEST_MINECART
      slot: 29
      command: "kits"
      permission: ""
      enabled: true
      lore: []
    daily:
      label: "Daily Rewards"
      icon: SUNFLOWER
      slot: 30
      command: "daily"
      permission: ""
      enabled: true
      lore: []
    premium:
      label: "Premium"
      icon: DIAMOND
      slot: 31
      command: "premium"
      permission: ""
      enabled: true
      lore: []
    duels:
      label: "Duels"
      icon: IRON_SWORD
      slot: 32
      command: "duel"
      permission: ""
      enabled: true
      lore: []
    drills:
      label: "Drills"
      icon: IRON_PICKAXE
      slot: 33
      command: "drills"
      permission: ""
      enabled: true
      lore: []
    teams:
      label: "Teams"
      icon: WHITE_BANNER
      slot: 34
      command: "team"
      permission: ""
      enabled: true
      lore: []
    warps:
      label: "Player Warps"
      icon: COMPASS
      slot: 37
      command: "pwarp"
      permission: ""
      enabled: true
      lore: []
    prices:
      label: "Price History"
      icon: PAPER
      slot: 38
      command: "prices"
      permission: ""
      enabled: true
      lore: []
    rules:
      label: "Rules"
      icon: OAK_SIGN
      slot: 39
      command: "rules"
      permission: ""
      enabled: true
      lore: []
    modules:
      label: "All Modules"
      icon: CRAFTING_TABLE
      slot: 40
      command: "donsup legacy"
      permission: ""
      enabled: true
      lore: []
    admin:
      label: "Admin Tools"
      icon: COMMAND_BLOCK
      slot: 41
      command: "creator"
      permission: "donsup.admin"
      enabled: true
      lore: []
pause:
  title: '<gold>%server%</gold>'
  external-title: 'Server Menu'
  close-label: 'Back'
  button-width: 300
  order: [main, settings, auction, orders, homes, friends]
  labels:
    main: 'Server Menu'
    settings: 'Settings'
    auction: 'Auction House'
    orders: 'Orders'
    homes: 'Homes'
    friends: 'Friends'

# Fixed inventory heading -> displayed heading. Do not rename the keys; change the values.
# The configured brand prefix is added automatically. Dynamic kit/team/player suffixes are preserved.
inventory-titles:
  "Control Center": "Control Center"
  "Shop": "Shop"
  "Auction House": "Auction House"
  "Player Market": "Player Market"
  "Bulk Orders": "Bulk Orders"
  "Opening": "Opening"
  "Main Menu": "Main Menu"
  "Premium Vault": "Premium Vault"
  "Choose a Crate Reward": "Choose a Crate Reward"
  "Trash (deleted on close)": "Trash (deleted on close)"
  "Staff": "Staff"
  "Prices": "Prices"
  "Duels": "Duels"
  "Trade": "Trade"
  "Drills": "Drills"
  "Kits": "Kits"
  "Spawners": "Spawners"
  "Spawner": "Spawner"
  "Daily Rewards": "Daily Rewards"
  "Teams": "Teams"
  "Player Warps": "Player Warps"
  "Creator": "Creator"
  "Shard Shop": "Shard Shop"
  "Crates": "Crates"
  "Bounties": "Bounties"
  "Premium": "Premium"
  "Leaderboards": "Leaderboards"
  "Server Shop": "Server Shop"
  "Settings": "Settings"
  "Homes": "Homes"
  "Profile": "Profile"

  "Teams Vault": "Teams Vault"
  "Kits Preview": "Kits Preview"
  "RTP Regions / Zones": "RTP Regions / Zones"
  "Saved Shopping": "Saved Shopping"
  "Shopping:": "Shopping:"
  "Creator | Hub": "Creator | Hub"
  "Creator | Launch Checklist": "Creator | Launch Checklist"
  "Creator | Crate Tools": "Creator | Crate Tools"
  "Creator | Key Tools": "Creator | Key Tools"
  "Creator | Shop Builder": "Creator | Shop Builder"
  "Creator | Shop": "Creator | Shop"
  "Creator | Presets": "Creator | Presets"
  "Creator | Preset Preview": "Creator | Preset Preview"
  "Creator | Dynamic Market": "Creator | Dynamic Market"
  "Creator | Premium Setup": "Creator | Premium Setup"
  "Creator | Spawner Setup": "Creator | Spawner Setup"
  "Creator | Config Studio": "Creator | Config Studio"
  "Creator | Command Teleports": "Creator | Command Teleports"
  "Creator | Rollback Preset": "Creator | Rollback Preset"

# Fixed native and inventory menu labels. Edit values only. Transaction amounts and player names remain dynamic.
text:
  settings-saved: "&aSettings saved."
  could-not-create-order-check-quantity-balance-and-order-limit: "&cCould not create order. Check quantity, balance and order limit."
  could-not-create-order-check-your-balance-and-order-limit: "&cCould not create order. Check your balance and order limit."
  home-limit-reached: "&cHome limit reached."
  night-vision-requires-premium: "&cNight vision requires premium."
  no-permission: "&cNo permission."
  quick-buy-is-unavailable-during-combat: "&cQuick Buy is unavailable during combat."
  your-held-item-changed: "&cYour held item changed."
  admin-tools: "<gold>Admin Tools"
  friend-chat-fc: "<gray>Friend chat: /fc <message>"
  money: "<gray>Money <green>"
  money-2: "<gray>Money: <green>"
  saved: "<gray>Saved "
  confirm: "<green>Confirm"
  confirm-purchase: "<green>Confirm Purchase"
  save: "<green>Save"
  set-a-home: "<green>Set a home"
  delete: "<red>Delete"
  accept: "Accept "
  add-friend: "Add Friend"
  all-listings: "All Listings"
  all-modules: "All Modules"
  all-orders: "All Orders"
  all-listings-2: "All listings"
  all-orders-2: "All orders"
  auction-house: "Auction House"
  auction-house-2: "Auction House - "
  back: "Back"
  bounties: "Bounties"
  buy-listing: "Buy Listing"
  buyer: "Buyer: "
  cancel: "Cancel"
  cancel-reclaim: "Cancel / Reclaim"
  chest-shops: "Chest Shops"
  close: "Close"
  close-claim-order: "Close & Claim Order"
  close-and-claim: "Close and Claim"
  confirm-2: "Confirm"
  crates: "Crates"
  create-listing: "Create Listing"
  create-order: "Create Order"
  create-order-2: "Create order"
  daily-rewards: "Daily Rewards"
  delete-home: "Delete home?"
  delete-with-delhome: "Delete with /delhome "
  deliver-items: "Deliver Items"
  disabled-click-to-enable: "Disabled - click to enable"
  donsup-all-in-one: "Donsup All In One"
  drills: "Drills"
  duels: "Duels"
  enabled-click-to-disable: "Enabled - click to disable"
  enter-a-finite-price-between-0-and-1-trillion: "Enter a finite price between 0 and 1 trillion."
  enter-a-whole-quantity: "Enter a whole quantity."
  exact-item-order: "Exact Item Order"
  exact-matches-for-your-held-item: "Exact matches for your held item."
  fill-in: "Fill in "
  friends: "Friends"
  funds-are-held-in-escrow-plain-unmodified-items-only: "Funds are held in escrow. Plain, unmodified items only."
  hold-an-item-first: "Hold an item first."
  hold-an-item-to-find-an-exact-match-including-enchantments-and-damage: "Hold an item to find an exact match, including enchantments and damage."
  hold-an-item-to-use-as-the-sample: "Hold an item to use as the sample."
  hold-the-item-you-want-to-list: "Hold the item you want to list."
  hold-the-item-you-want-to-sell: "Hold the item you want to sell."
  home-name: "Home name"
  homes: "Homes"
  invalid-dialogs-yml: "Invalid dialogs.yml"
  invalid-dialogs-yml-2: "Invalid dialogs.yml: "
  invalid-material-or-quantity-1-1-000-000: "Invalid material or quantity (1-1,000,000)."
  invalid-setting-value-reopen-settings: "Invalid setting value. Reopen /settings."
  keeps-the-box-and-protected-custom-items: "Keeps the box and protected custom items."
  keys-crates: "Keys / Crates"
  kits: "Kits"
  leaderboards: "Leaderboards"
  leave-rtp-queue-cancel: "Leave RTP queue / cancel"
  leave-queue: "Leave queue"
  list-held-item: "List Held Item"
  list-held-item-2: "List held item"
  list-item: "List item"
  listing: "Listing"
  listing-fee: "Listing fee: "
  match-held-item-exactly: "Match Held Item Exactly"
  match-held-item: "Match held item"
  material-e-g-iron-ingot: "Material (e.g. IRON_INGOT)"
  material-name: "Material name"
  maximum-price-per-item: "Maximum price per item"
  missing-dialog-category: "Missing dialog category: "
  money-3: "Money: "
  more-features: "More Features"
  my-listings-returns: "My Listings / Returns"
  my-orders-claims: "My Orders / Claims"
  my-listings-returns-2: "My listings / returns"
  my-orders-claims-2: "My orders / claims"
  next: "Next"
  online-player: "Online player"
  only-matching-orders-may-buy-this-exact-item: "Only matching orders may buy this exact item."
  order-held-item-exactly: "Order Held Item Exactly"
  order-exact-held-item: "Order exact held item"
  orders: "Orders"
  orders-2: "Orders - "
  plain-items-use-match-held-item-for-enchanted-or-custom-items: "Plain items. Use Match Held Item for enchanted or custom items."
  player-chest-shops: "Player Chest Shops"
  player-market: "Player Market"
  player-warps: "Player Warps"
  premium: "Premium"
  previous: "Previous"
  price-history: "Price History"
  price-per-item: "Price per item"
  private-profile: "Private profile"
  profile: "Profile"
  quantity: "Quantity"
  queue-status: "Queue status"
  quick-buy: "Quick Buy"
  quick-buy-2: "Quick Buy - "
  rtp-status: "RTP Status"
  rtp-cancelled: "RTP cancelled."
  random-teleport: "Random Teleport"
  reclaim-listing: "Reclaim Listing"
  remaining: "Remaining: "
  remove: "Remove "
  remove-friend: "Remove friend?"
  requested: "Requested: "
  rules: "Rules"
  save-2: "Save"
  save-your-current-location: "Save your current location."
  search: "Search"
  sell: "Sell"
  sell-exact-held-item: "Sell Exact Held Item"
  sell-exact-held-item-2: "Sell Exact Held Item?"
  sell-exact-item: "Sell Exact Item?"
  sell-held-item: "Sell Held Item"
  sell-history: "Sell History"
  sell-inventory: "Sell Inventory"
  sell-inventory-2: "Sell Inventory?"
  sell-shulker-contents: "Sell Shulker Contents"
  sell-shulker-contents-2: "Sell Shulker Contents?"
  sell-exact-held-item-3: "Sell exact held item"
  sell-held-item-2: "Sell held item"
  sell-history-2: "Sell history"
  sell-inventory-3: "Sell inventory"
  sell-plain-items-at-the-best-available-order-price-or-server-price-named-enchanted-and-cus: "Sell plain items at the best available order price or server price. Named, enchanted and custom items are protected."
  sell-shulker-contents-3: "Sell shulker contents"
  seller: "Seller: "
  sells-supported-plain-contents-keeps-the-box-and-all-custom-items: "Sells supported plain contents. Keeps the box and all custom items."
  sells-supported-plain-items-in-your-storage-slots: "Sells supported plain items in your storage slots."
  sells-this-item-only-to-matching-orders-names-enchantments-damage-and-custom-data-must-mat: "Sells this item only to matching orders. Names, enchantments, damage and custom data must match. Unsold items stay with you."
  send-request: "Send Request"
  set-home: "Set Home"
  set-a-home-2: "Set a home"
  settings: "Settings"
  shard-shop: "Shard Shop"
  shards: "Shards"
  spawners: "Spawners"
  statistics: "Statistics"
  teams: "Teams"
  teleport: "Teleport"
  teleport-to-this-home: "Teleport to this home?"
  this-player-has-a-private-profile: "This player has a private profile."
  this-player-keeps-their-statistics-private: "This player keeps their statistics private."
  this-sells-supported-plain-items-in-your-storage-slots: "This sells supported plain items in your storage slots."
  total-asking-price: "Total asking price"
  transaction: "Transaction"
  travel-rtp: "Travel / RTP"
  unknown-player-setting: "Unknown player setting: "
  unknown-setting: "Unknown setting: "
  use-1-24-letters-numbers-or: "Use 1-24 letters, numbers, _ or -."
  your-sample-is-kept-only-identical-items-qualify-including-spawner-type-enchantments-damag: "Your sample is kept. Only identical items qualify, including spawner type, enchantments, damage, name and custom data. Funds are held in escrow."


===== src/main/resources/messages.yml =====

# Fixed feedback messages, legacy & colour codes. Edit values, not keys.
# These exact messages are configurable; dynamic transaction receipts retain their amounts and server-generated text.
# Prefix is configured in config.yml under messages.prefix. %server% inserts the configured server name.
# Empty values suppress a fixed message. Reload with /donsup reload.
messages:
  brand-usage: '&eUsage: /smp brand <Your Server Name>'
  brand-saved: '&aServer name saved. Menus, tab and sidebar use the new name. Restart for the pause-screen heading.'
  example-combat-pearls-480-18-16-type-cancel-to-stop: "&7Example: &fcombat pearls 480 18 16 &8| type &ccancel &8to stop."
  example-crates-or-market-type-cancel-to-stop: "&7Example: &fcrates &8or &fmarket &8| type &ccancel &8to stop."
  example-pearls-480-18-16-type-cancel-to-stop: "&7Example: &fpearls 480 18 16 &8| type &ccancel &8to stop."
  friend-removed: "&7Friend removed."
  friend-request-declined: "&7Friend request declined."
  open-your-chest-normally-to-manage-stock-other-players-get-a-purchase-confirmation: "&7Open your chest normally to manage stock. Other players get a purchase confirmation."
  request-declined: "&7Request declined."
  type-cancel-to-stop: "&7Type &ccancel &7to stop."
  you-are-not-waiting-for-rtp: "&7You are not waiting for RTP."
  afk-rewards-enabled-move-to-disable: "&aAFK rewards enabled. Move to disable."
  added-staff-note: "&aAdded staff note."
  claimed-premium-kit: "&aClaimed premium kit."
  created-exact-item-order-your-sample-item-was-kept: "&aCreated exact-item order. Your sample item was kept."
  dumped-stored-drops: "&aDumped stored drops."
  fed: "&aFed."
  friend-request-sent-expires-in-2-minutes: "&aFriend request sent (expires in 2 minutes)."
  gave-crate-placer: "&aGave crate placer."
  gave-custom-spawners: "&aGave custom spawners."
  listing-returned: "&aListing returned."
  purchased-shard-shop-item: "&aPurchased shard shop item."
  rank-updated: "&aRank updated."
  recovered-the-saved-account-reward-no-key-refund-was-issued: "&aRecovered the saved account reward. No key refund was issued."
  recovered-your-interrupted-account-reward: "&aRecovered your interrupted account reward."
  reloaded-smp-builder-configs: "&aReloaded SMP builder configs."
  reloaded: "&aReloaded."
  repaired-held-item: "&aRepaired held item."
  report-submitted: "&aReport submitted."
  request-sent-expires-in-60-seconds: "&aRequest sent; expires in 60 seconds."
  set-team-home: "&aSet team home."
  settings-saved: "&aSettings saved."
  shop-price-updated-earlier-confirmations-are-now-invalid: "&aShop price updated. Earlier confirmations are now invalid."
  shop-removed-its-stock-stays-in-the-container: "&aShop removed. Its stock stays in the container."
  spawn-saved: "&aSpawn saved."
  teleported: "&aTeleported."
  trade-completed: "&aTrade completed."
  a-player-is-already-trading: "&cA player is already trading."
  a-protection-plugin-blocked-your-return-contact-staff-for-help-returning: "&cA protection plugin blocked your return. Contact staff for help returning."
  afk-rewards-disabled-because-you-moved: "&cAFK rewards disabled because you moved."
  afk-rewards-disabled: "&cAFK rewards disabled."
  account-keys-are-disabled: "&cAccount keys are disabled."
  arena-point-must-be-1-or-2: "&cArena point must be 1 or 2."
  both-players-must-be-alive-out-of-combat-and-outside-a-duel: "&cBoth players must be alive, out of combat and outside a duel."
  buy-and-sell-prices-must-be-0-or-higher: "&cBuy and sell prices must be 0 or higher."
  buy-sell-and-amount-must-be-numbers: "&cBuy, sell and amount must be numbers."
  chest-shops-are-disabled: "&cChest shops are disabled."
  chest-shop-trading-is-blocked-during-combat-or-a-duel: "&cChest-shop trading is blocked during combat or a duel."
  close-the-container-before-creating-a-shop: "&cClose the container before creating a shop."
  combat-tagged-teleports-are-temporarily-blocked: "&cCombat tagged. Teleports are temporarily blocked."
  could-not-complete-the-crate-operation-your-saved-choice-may-need-staff-review-check-the-s: "&cCould not complete the crate operation. Your saved choice may need staff review; check the server log."
  could-not-create-order-check-quantity-balance-and-order-limit: "&cCould not create order. Check quantity, balance and order limit."
  could-not-create-order-check-your-balance-and-order-limit: "&cCould not create order. Check your balance and order limit."
  could-not-create-order-you-need-enough-money-for-escrow: "&cCould not create order. You need enough money for escrow."
  could-not-grant-keys-check-the-type-amount-and-inventory-space: "&cCould not grant keys. Check the type, amount and inventory space."
  could-not-grant-these-keys-shards-refunded-check-inventory-space-and-configuration: "&cCould not grant these keys. Shards refunded; check inventory space and configuration."
  could-not-list-item-check-listing-limit-and-listing-tax-money: "&cCould not list item. Check listing limit and listing tax money."
  creator-prompt-cancelled: "&cCreator prompt cancelled."
  creator-tools-require-donsup-admin: "&cCreator tools require &edonsup.admin&c."
  denied-duel-request: "&cDenied duel request."
  denied-trade-request: "&cDenied trade request."
  destination-is-unavailable: "&cDestination is unavailable."
  duel-cancelled-because-a-teleport-was-blocked: "&cDuel cancelled because a teleport was blocked."
  duel-cancelled-a-player-became-unavailable: "&cDuel cancelled: a player became unavailable."
  duel-cancelled-both-players-must-afford-the-wager-and-payment-must-save: "&cDuel cancelled: both players must afford the wager and payment must save."
  duel-funding-failed: "&cDuel funding failed."
  duel-started: "&cDuel started."
  enter-a-positive-finite-amount-up-to-1-trillion: "&cEnter a positive, finite amount up to 1 trillion."
  friend-limit-reached-100: "&cFriend limit reached (100)."
  friend-request-unavailable: "&cFriend request unavailable."
  friendly-fire-is-disabled-for-your-team: "&cFriendly fire is disabled for your team."
  hold-a-damageable-item: "&cHold a damageable item."
  hold-a-single-shulker-box-to-sell-its-contents: "&cHold a single shulker box to sell its contents."
  hold-a-valid-physical-crate-key-to-redeem-it: "&cHold a valid physical crate key to redeem it."
  hold-an-item-and-check-quantity-price-balance-and-order-limit: "&cHold an item and check quantity, price, balance and order limit."
  hold-an-item-and-provide-a-valid-price: "&cHold an item and provide a valid price."
  hold-the-exact-item-you-want-this-shop-to-trade-your-sample-is-kept: "&cHold the exact item you want this shop to trade. Your sample is kept."
  hold-the-item-this-spawner-should-generate: "&cHold the item this spawner should generate."
  hold-the-item-you-want-to-add-before-starting-the-shop-builder: "&cHold the item you want to add before starting the shop builder."
  hold-the-item-you-want-to-add-to-the-premium-kit: "&cHold the item you want to add to the premium kit."
  hold-the-item-you-want-to-add-to-the-shop: "&cHold the item you want to add to the shop."
  home-limit-reached: "&cHome limit reached."
  home-limit-reached-premium-adds-more-homes: "&cHome limit reached. Premium adds more homes."
  home-not-found: "&cHome not found."
  invalid-action-rank-or-amount: "&cInvalid action, rank or amount."
  invalid-amount-or-not-enough-money: "&cInvalid amount or not enough money."
  invalid-command-name: "&cInvalid command name."
  invalid-drop-material: "&cInvalid drop material."
  invalid-kit-material: "&cInvalid kit material."
  invalid-material-amount-or-price: "&cInvalid material, amount or price."
  invalid-or-disabled-wager: "&cInvalid or disabled wager."
  invalid-or-occupied-arena: "&cInvalid or occupied arena."
  invalid-player-or-amount: "&cInvalid player or amount."
  invalid-player: "&cInvalid player."
  invalid-spawner-drop-prompt: "&cInvalid spawner drop prompt."
  invalid-team-or-player: "&cInvalid team or player."
  invalid-type-amount-or-key-balance-limit-amount-must-be-1-to-1-000-000: "&cInvalid type, amount or key balance limit. Amount must be 1 to 1,000,000."
  key-all-requires-account-keys-to-be-enabled: "&cKey-all requires account keys to be enabled."
  kit-not-found: "&cKit not found."
  leader-cannot-leave-delete-reassign-is-reserved-for-admin-cleanup: "&cLeader cannot leave. Delete/reassign is reserved for admin cleanup."
  leave-a-gap-beside-shop-containers-merging-them-is-blocked: "&cLeave a gap beside shop containers; merging them is blocked."
  leave-the-duel-before-teleporting: "&cLeave the duel before teleporting."
  leave-your-current-team-first: "&cLeave your current team first."
  look-at-a-registered-shop-chest-or-barrel: "&cLook at a registered shop chest or barrel."
  look-at-a-single-chest-or-barrel-within-five-blocks-double-chests-are-not-supported: "&cLook at a single chest or barrel within five blocks. Double chests are not supported."
  make-inventory-space-before-buying-a-drill: "&cMake inventory space before buying a drill."
  make-inventory-space-before-buying-a-spawner: "&cMake inventory space before buying a spawner."
  make-inventory-space-before-reclaiming: "&cMake inventory space before reclaiming."
  make-inventory-space-first: "&cMake inventory space first."
  make-inventory-space-first-your-choices-are-saved: "&cMake inventory space first. Your choices are saved."
  make-room-for-the-whole-kit-first-your-cooldown-has-not-started: "&cMake room for the whole kit first. Your cooldown has not started."
  make-space-or-sell-dump-the-stored-drops-before-picking-up-this-spawner: "&cMake space or sell/dump the stored drops before picking up this spawner."
  manage-this-shop-s-stock-through-its-inventory-the-sell-axe-cannot-sell-shop-stock: "&cManage this shop's stock through its inventory; the Sell Axe cannot sell shop stock."
  messages-must-be-1-256-characters: "&cMessages must be 1-256 characters."
  night-vision-is-a-premium-perk: "&cNight vision is a premium perk."
  night-vision-is-a-premium-setting: "&cNight vision is a premium setting."
  night-vision-is-disabled-by-this-server: "&cNight vision is disabled by this server."
  night-vision-requires-premium: "&cNight vision requires premium."
  no-active-request: "&cNo active request."
  no-drops-stored: "&cNo drops stored."
  no-duel-invite-to-deny: "&cNo duel invite to deny."
  no-free-duel-arena-is-ready-ask-an-admin-to-set-one: "&cNo free duel arena is ready. Ask an admin to set one."
  no-interrupted-delivery-to-resolve: "&cNo interrupted delivery to resolve."
  no-invite-for-that-team: "&cNo invite for that team."
  no-matching-duel-invite: "&cNo matching duel invite."
  no-matching-request: "&cNo matching request."
  no-matching-trade-request: "&cNo matching trade request."
  no-one-to-reply-to: "&cNo one to reply to."
  no-pending-requests: "&cNo pending requests."
  no-permission-for-rtp-queues: "&cNo permission for RTP queues."
  no-permission: "&cNo permission."
  no-team-home-set: "&cNo team home set."
  not-enough-matching-stock-or-inventory-space-for-the-complete-batch: "&cNot enough matching stock or inventory space for the complete batch."
  not-enough-money: "&cNot enough money."
  one-of-those-players-is-already-in-a-duel: "&cOne of those players is already in a duel."
  only-players-can-pay-money: "&cOnly players can pay money."
  only-players-can-use-that-command: "&cOnly players can use that command."
  only-the-leader-can-change-friendly-fire: "&cOnly the leader can change friendly fire."
  only-the-leader-can-invite: "&cOnly the leader can invite."
  only-the-leader-can-withdraw: "&cOnly the leader can withdraw."
  only-the-owner-or-an-administrator-can-change-this-shop: "&cOnly the owner or an administrator can change this shop."
  payment-could-not-be-completed-no-items-were-moved: "&cPayment could not be completed. No items were moved."
  physical-keys-need-an-online-player-with-inventory-space: "&cPhysical keys need an online player with inventory space."
  place-a-new-chest-or-barrel-yourself-before-creating-a-shop: "&cPlace a new chest or barrel yourself before creating a shop."
  placeable-crates-are-disabled: "&cPlaceable crates are disabled."
  player-must-have-joined-before: "&cPlayer must have joined before."
  player-not-found: "&cPlayer not found."
  player-unavailable: "&cPlayer unavailable."
  portable-workbench-is-disabled: "&cPortable workbench is disabled."
  premium-kit-is-not-configured: "&cPremium kit is not configured."
  premium-vault-requires-premium: "&cPremium vault requires premium."
  quick-buy-is-unavailable-during-combat: "&cQuick Buy is unavailable during combat."
  rtp-is-on-cooldown: "&cRTP is on cooldown."
  rtp-queues-are-disabled: "&cRTP queues are disabled."
  rtp-searches-are-busy-try-again-shortly: "&cRTP searches are busy. Try again shortly."
  remove-the-container-s-existing-lock-first: "&cRemove the container's existing lock first."
  remove-this-shop-with-chestshop-remove-before-breaking-its-container: "&cRemove this shop with /chestshop remove before breaking its container."
  shards-must-be-a-whole-number-between-0-and-2147483647: "&cShards must be a whole number between 0 and 2147483647."
  stand-close-to-the-original-shop-container: "&cStand close to the original shop container."
  team-bank-is-too-low: "&cTeam bank is too low."
  team-not-found: "&cTeam not found."
  teleport-cancelled-because-you-moved-or-took-damage: "&cTeleport cancelled because you moved or took damage."
  teleport-was-cancelled: "&cTeleport was cancelled."
  that-rtp-dimension-is-disabled-or-unavailable: "&cThat RTP dimension is disabled or unavailable."
  that-container-already-belongs-to-a-shop-or-crate: "&cThat container already belongs to a shop or crate."
  that-duel-invite-expired: "&cThat duel invite expired."
  that-home-is-not-available: "&cThat home is not available."
  that-is-not-your-order: "&cThat is not your order."
  that-listing-is-no-longer-available: "&cThat listing is no longer available."
  that-listing-is-no-longer-yours-or-was-already-claimed: "&cThat listing is no longer yours or was already claimed."
  that-order-is-not-accepting-deliveries: "&cThat order is not accepting deliveries."
  that-player-cannot-receive-messages: "&cThat player cannot receive messages."
  that-player-has-payments-disabled: "&cThat player has payments disabled."
  that-player-has-too-many-pending-requests: "&cThat player has too many pending requests."
  that-player-is-not-accepting-duel-requests: "&cThat player is not accepting duel requests."
  that-player-is-not-your-duel-opponent: "&cThat player is not your duel opponent."
  that-player-is-offline: "&cThat player is offline."
  that-player-must-have-joined-this-server-before: "&cThat player must have joined this server before."
  that-team-already-exists: "&cThat team already exists."
  that-was-not-a-valid-amount: "&cThat was not a valid amount."
  that-was-not-a-valid-number: "&cThat was not a valid number."
  the-rtp-queue-is-full: "&cThe RTP queue is full."
  the-original-shop-container-is-unavailable: "&cThe original shop container is unavailable."
  the-owner-is-managing-stock-try-again-after-they-close-the-container: "&cThe owner is managing stock. Try again after they close the container."
  the-paying-account-does-not-have-enough-money: "&cThe paying account does not have enough money."
  the-shop-operation-could-not-finish-staff-can-inspect-chest-shops-yml-and-any-pending-shop: "&cThe shop operation could not finish. Staff can inspect chest-shops.yml and any pending shop payment before resolving it."
  this-crate-has-no-rewards-configured: "&cThis crate has no rewards configured."
  this-crate-is-protected: "&cThis crate is protected."
  this-is-a-premium-perk: "&cThis is a premium perk."
  this-player-has-too-many-requests: "&cThis player has too many requests."
  this-player-is-not-accepting-teleport-requests: "&cThis player is not accepting teleport requests."
  this-reward-would-exceed-your-balance-limit-your-choice-is-still-saved: "&cThis reward would exceed your balance limit. Your choice is still saved."
  this-shop-has-an-interrupted-trade-requiring-staff-review: "&cThis shop has an interrupted trade requiring staff review."
  this-shop-is-awaiting-staff-review-of-an-interrupted-trade: "&cThis shop is awaiting staff review of an interrupted trade."
  this-shop-is-paused: "&cThis shop is paused."
  this-shop-needs-staff-review-before-stock-can-change: "&cThis shop needs staff review before stock can change."
  this-shop-offer-changed-right-click-it-for-a-new-price: "&cThis shop offer changed. Right-click it for a new price."
  trade-failed-insufficient-funds-invalid-amount-or-saving-failed-no-payment-was-taken: "&cTrade failed: insufficient funds, invalid amount, or saving failed. No payment was taken."
  unknown-crate-or-account-keys-are-disabled: "&cUnknown crate or account keys are disabled."
  unknown-player: "&cUnknown player."
  use-a-kit-id-of-1-32-letters-numbers-underscores-or-hyphens: "&cUse a kit ID of 1-32 letters, numbers, underscores or hyphens."
  use-a-mute-length-of-1-5256000-minutes: "&cUse a mute length of 1-5256000 minutes."
  use-a-team-name-of-1-32-letters-numbers-underscores-or-hyphens: "&cUse a team name of 1-32 letters, numbers, underscores or hyphens."
  use-a-warp-name-of-1-32-letters-numbers-underscores-or-hyphens: "&cUse a warp name of 1-32 letters, numbers, underscores or hyphens."
  use-chest-shop-commands-in-game: "&cUse chest-shop commands in game."
  use-this-command-in-game: "&cUse this command in game."
  use-category-id-buy-sell-amount: "&cUse: category id buy sell amount"
  use-id-buy-sell-amount: "&cUse: id buy sell amount"
  wait-before-requesting-again: "&cWait before requesting again."
  wait-before-sending-another-request: "&cWait before sending another request."
  warp-not-found: "&cWarp not found."
  you-already-claimed-today-s-reward: "&cYou already claimed today's reward."
  you-are-muted: "&cYou are muted."
  you-are-not-in-a-duel: "&cYou are not in a duel."
  you-are-not-in-a-team: "&cYou are not in a team."
  you-cannot-buy-your-own-listing: "&cYou cannot buy your own listing."
  you-cannot-duel-yourself: "&cYou cannot duel yourself."
  you-do-not-have-enough-items-to-sell: "&cYou do not have enough items to sell."
  you-do-not-have-enough-money-for-that-wager: "&cYou do not have enough money for that wager."
  you-do-not-have-enough-money: "&cYou do not have enough money."
  you-do-not-have-enough-shards: "&cYou do not have enough shards."
  you-do-not-have-matching-items: "&cYou do not have matching items."
  you-do-not-own-that-warp: "&cYou do not own that warp."
  your-held-item-changed: "&cYour held item changed."
  your-key-balance-is-full-choose-another-reward-or-use-some-keys-first: "&cYour key balance is full. Choose another reward or use some keys first."
  your-previous-reward-delivery-was-interrupted-ask-staff-to-review-it-before-opening-anothe: "&cYour previous reward delivery was interrupted. Ask staff to review it before opening another crate."
  your-wager-payment-could-not-be-saved-contact-staff-the-escrow-is-retained: "&cYour wager payment could not be saved. Contact staff; the escrow is retained."
  chestshop-create: "&e/chestshop create <buy|sell> <amount> <total price>"
  chestshop-create-list-info-stock-price-pause-resume-remove-history: "&e/chestshop create|list|info|stock|price|pause|resume|remove|history"
  chestshop-price: "&e/chestshop price <total per batch>"
  chestshop-resolve-acknowledge-after-auditing-its-items-and-payment: "&e/chestshop resolve <shopId> acknowledge &7after auditing its items and payment."
  donsup-money-e-donsup-shardadmin-donsup-rank: "&e/donsup money <give|take> <player> <amount>\n& e/donsup shardadmin <give|take> <player> <amount>\n&e/donsup rank <player> <member|plus|elite|legend> <days>"
  donsup-reload-money-shardadmin-rank: "&e/donsup reload | money | shardadmin | rank"
  friend: "&e/friend <add|accept|deny|remove> <player>"
  ignore: "&e/ignore <player>"
  keyall: "&e/keyall <crate> <amount>"
  keys-open-claim-redeem: "&e/keys [open <crate>|claim|redeem]"
  keys-give: "&e/keys give <player> <crate> <amount>"
  keys-give-or-keyall: "&e/keys give <player> <crate> <amount> or /keyall <crate> <amount>"
  keys-resolve-after-checking-an-interrupted-delivery: "&e/keys resolve <player> <refund|complete> &7after checking an interrupted delivery."
  msg: "&e/msg <player> <message>"
  rtp-overworld-nether-end-or-rtp-queue-dimension-or-rtp-leave: "&e/rtp [overworld|nether|end] &7or &e/rtp queue [dimension] &7or &e/rtp leave"
  smp-preset-apply-rollback: "&e/smp preset <list|preview <name>|apply <name>|rollback>"
  smp-reload: "&e/smp reload"
  smp-setup-opens-the-installer-smp-preset-preview: "&e/smp setup &7opens the installer. &e/smp preset preview <name>"
  a-teammate-is-using-this-vault-try-again-when-they-close-it: "&eA teammate is using this vault. Try again when they close it."
  make-inventory-space-and-use-trade-claim-for-returned-items: "&eMake inventory space and use /trade claim for returned items."
  meet-the-other-player-nearby-before-opening-a-trade-on-folia: "&eMeet the other player nearby before opening a trade on Folia."
  no-saved-choice-open-a-crate-using-crates: "&eNo saved choice. Open a crate using /crates."
  that-warp-is-already-promoted: "&eThat warp is already promoted."
  trade-cancelled-because-players-left-the-same-region: "&eTrade cancelled because players left the same region."
  type-shop-details-in-chat-category-id-buy-sell-amount: "&eType shop details in chat: &fcategory id buy sell amount"
  type-the-command-name-to-bind-to-your-current-location: "&eType the command name to bind to your current location."
  usage-during-trade-trade-money: "&eUsage during trade: /trade money <amount>"
  usage-during-trade-trade-shards: "&eUsage during trade: /trade shards <amount>"
  usage-bounty-or-bounty-set: "&eUsage: /bounty <player> <amount> &7or &e/bounty set <player> <amount>"
  usage-creator-crate-wand: "&eUsage: /creator crate wand <type>"
  usage-creator-dynamic: "&eUsage: /creator dynamic <on|off>"
  usage-creator-key: "&eUsage: /creator key <crateType> <amount>"
  usage-creator-shop-add: "&eUsage: /creator shop add <category> <id> <buy> <sell> <amount>"
  usage-delhome: "&eUsage: /delhome <name>"
  usage-drill-give: "&eUsage: /drill give <player> <tier>"
  usage-drills-or-drill-give: "&eUsage: /drills &7or &e/drill give <player> <tier>"
  usage-duel-accept: "&eUsage: /duel accept <player>"
  usage-duel-arena-set-or-duel-arena-delete: "&eUsage: /duel arena set <id> <1|2> &7or &e/duel arena delete <id>"
  usage-kitadmin: "&eUsage: /kitadmin <save|delete> <id>"
  usage-mod-mute: "&eUsage: /mod mute <player> <minutes>"
  usage-mod-note: "&eUsage: /mod note <player> <note>"
  usage-mod-warn: "&eUsage: /mod warn <player> <reason>"
  usage-orders-create-hand-deliver-claim: "&eUsage: /orders [create <material> <amount> <priceEach>|hand <amount> <priceEach>|deliver <id>|claim <id>]"
  usage-orders-create: "&eUsage: /orders create <material> <amount> <priceEach>"
  usage-orders-hand-copies-the-held-item-s-exact-properties: "&eUsage: /orders hand <amount> <priceEach> (copies the held item's exact properties)"
  usage-pay: "&eUsage: /pay <player> <amount>"
  usage-pwarp-delete: "&eUsage: /pwarp delete <name>"
  usage-pwarp-promote: "&eUsage: /pwarp promote <name>"
  usage-pwarp-set: "&eUsage: /pwarp set <name>"
  usage-report: "&eUsage: /report <player> <reason>"
  usage-sell: "&eUsage: /sell <hand|all|exact|shulker>"
  usage-smp-givekey: "&eUsage: /smp givekey <player> <type> <amount>"
  usage-smp-pay: "&eUsage: /smp pay <player> <amount>"
  usage-smp-premium: "&eUsage: /smp premium <player> <days>"
  usage-smp-setsellmulti: "&eUsage: /smp setsellmulti <player> <multiplier>"
  usage-spawners-give: "&eUsage: /spawners [give <type> <amount>]"
  usage-spawners-give-2: "&eUsage: /spawners give <type> <amount>"
  usage-team-bank: "&eUsage: /team bank <deposit|withdraw> <amount>"
  usage-team-chat: "&eUsage: /team chat <message>"
  usage-team-create: "&eUsage: /team create <name>"
  usage-trade: "&eUsage: /trade <player|accept|deny|money|shards>"
  use-smp-preset-list-or-smp-preset-apply: "&eUse /smp preset list or /smp preset apply <name>."
  you-already-have-an-rtp-request-rtp-leave-to-cancel-it: "&eYou already have an RTP request. /rtp leave to cancel it."
  you-have-a-saved-reward-choice-use-keys-claim: "&eYou have a saved reward choice. Use /keys claim."
  your-daily-reward-is-ready-daily: "&eYour daily reward is ready: &f/daily&e."
  your-inventory-was-full-so-leftover-items-were-dropped-at-your-feet: "&eYour inventory was full, so leftover items were dropped at your feet."


===== src/main/resources/paper-plugin.yml =====

name: DonsupAllInOne
version: ${project.version}
main: com.donsup.DonsupPlugin
bootstrapper: com.donsup.dialog.DonsupBootstrap
api-version: '1.19'
description: All-in-one survival economy and native dialog menus.
author: VexyAUS
folia-supported: true
permissions:
  donsup.rtp.queue:
    default: true
  donsup.use:
    default: true
  donsup.premium:
    default: false
  donsup.admin:
    default: op
  donsup.staff:
    default: op
  donsup.rank.plus:
    default: false
  donsup.rank.elite:
    default: false
  donsup.rank.legend:
    default: false


===== src/main/resources/plugin.yml =====

name: DonsupAllInOne
version: ${project.version}
main: com.donsup.DonsupPlugin
folia-supported: true
api-version: '1.13'
prefix: Donut SMP All In One
author: VexyAUS
description: GUI-heavy all-in-one competitive SMP maker with economy, shops, auctions, orders, homes, crates and premium perks.

commands:
  chestshop:
    description: Create and manage physical player shops with native trade confirmations.
    aliases: [cshop]
  smp:
    description: Open the SMP control center.
    aliases: [donsup, menu, servermenu]
  shop:
    description: Quick Buy from live auctions.
  quickbuy:
    description: Quick Buy from live auctions.
  servershop:
    description: Open the optional fixed-price server shop.
  sell:
    description: Sell plain items, exact items to orders, or held shulker contents.
  ah:
    description: Open or list in the auction house.
    aliases: [auction, auctions]
  orders:
    description: Create, deliver or claim plain-material and exact-item orders.
    aliases: [order]
  market:
    description: Open the player market GUI.
  shards:
    description: Open the shard shop.
  crates:
    description: Open the crate GUI.
    aliases: [crate]
  keys:
    description: View keys, resume rewards, redeem physical keys or administer key grants.
  keyall:
    description: Give account keys to every online player (admin).
  homes:
    description: Open the homes GUI.
    aliases: [homegui]
  sethome:
    description: Set a home.
  home:
    description: Teleport to a home.
  delhome:
    description: Delete a home.
  bounty:
    description: Open or create bounties.
    aliases: [bounties, contract, contracts]
  bounties:
    description: Open the bounty board.
  pay:
    description: Pay another player.
  balance:
    description: View your money and shards.
    aliases: [money]
  bal:
    description: View your money and shards.
  afk:
    description: Toggle AFK shard earning.
  settings:
    description: Open the player settings GUI.
  profile:
    description: Open your profile GUI.
  premium:
    description: Open the premium perks GUI.
    aliases: [perks, rankperks, ranks]
  pvault:
    description: Open the premium vault.
    aliases: [playervault]
  nightvision:
    description: Toggle premium night vision.
    aliases: [nv]
  spawners:
    description: Open the custom spawner shop.
    aliases: [spawner, spawnershop]
  creator:
    description: Open the SMP creator toolkit.
    aliases: [smpcreator, setupserver]
  leaderboard:
    description: Open SMP leaderboards.
    aliases: [leaderboards, top]
  premiumkit:
    description: Claim premium kit.
  repair:
    description: Premium repair held item.
  feed:
    description: Premium feed utility.
  workbench:
    description: Premium portable crafting table.
    aliases: [craft]
  duel:
    description: Challenge players, accept duels and manage duel arenas.
    aliases: [duels, 1v1]
  drills:
    description: Open vein miner drill shop.
    aliases: [drillshop]
  drill:
    description: Drill admin/player command.
  veinminer:
    description: Open vein miner drill shop.
    aliases: [veinmine]
  team:
    description: Teams and clans.
    aliases: [teams]
  clan:
    description: Clan alias for teams.
    aliases: [clans]
  pwarp:
    description: Player warps GUI and commands.
    aliases: [playerwarp, playerwarps]
  trade:
    description: Safe player trading.
  kit:
    description: Claim kits.
  kits:
    description: Open kits GUI.
  kitadmin:
    description: Admin kit builder.
  daily:
    description: Daily rewards and streaks.
  mod:
    description: Staff moderation tools.
  report:
    description: Report a player.
  prices:
    description: Auction and market price history.

  friends:
    description: Open friends and requests.
  friend:
    description: Add, accept, deny or remove a friend.
  friendchat:
    description: Chat with friends.
    aliases: [fc]
  follow:
    description: Follow a player.
  following:
    description: View followed players.
  unfollow:
    description: Unfollow a player.
  msg:
    description: Private message a player.
    aliases: [message, whisper, tell, w]
  reply:
    description: Reply to a private message.
    aliases: [r]
  ignore:
    description: Block messages and requests from a player.
  rtp:
    description: Select an RTP dimension, travel solo, or queue with a partner.
    aliases: [wild]
  rtpqueue:
    description: Join a paired RTP queue or leave it.
    aliases: [rtpq]
  tpa:
    description: Request teleport to another player.
  tpahere:
    description: Ask another player to teleport to you.
  tpaccept:
    description: Accept a teleport request.
  tpdeny:
    description: Decline a teleport request.
  spawn:
    description: Teleport to spawn.
  setspawn:
    description: Set server spawn (admin).
  stats:
    description: View player statistics.
  sellhistory:
    description: View your sale history.
  worth:
    description: Check the held item's server value.
  baltop:
    description: View economy leaderboards.
  trash:
    description: Discard unwanted items.
  rules:
    description: Read server rules.
permissions:
  donsup.rtp.queue:
    description: Join paired random teleports.
    default: true
  donsup.use:
    description: Access player features.
    default: true
  donsup.premium:
    description: Access premium perks while permission is held.
    default: false
  donsup.admin:
    description: Full admin access.
    default: op
  donsup.staff:
    description: Staff moderation access.
    default: op


===== src/main/resources/presets/community/config.yml =====

branding:
  server-name: Your SMP
  display-name: '&6&l%server%'
  menu-title-prefix: '%server% | '
  tablist:
    enabled: true
    header: '&6&l%server%'
    footer: '&7/shop &8| &7/ah &8| &7/bounties &8| &7/crates'
  scoreboard:
    enabled: true
    title: '&6&l%server%'
    lines:
    - '&7%player%'
    - '&8&m------------'
    - '&fMoney: &a%money%'
    - '&fShards: &d%shards%'
    - '&fKills: &c%kills%'
    - '&fBounty: &6%bounty%'
    - '&8&m------------'
    - '&e/smp'
settings:
  starting-money: 500.0
  starting-shards: 0
  listing-tax-percent: 0.5
  max-auction-listings: 18
  max-market-listings: 18
  order-duration-hours: 24
  order-claim-hours: 90
  default-home-limit: 8
  premium-home-bonus: 3
  kill-shards: 0
  afk-shards-per-minute: 0
  premium-online-shards-per-minute: 0
  premium-fast-buy: true
  premium-listing-tax-percent: 0.5
  premium-listing-bonus: 18
  premium-sell-multiplier: 1.0
  premium-vault-rows: 3
  premium-bounty-radar: true
  premium-market-alerts: true
  premium-night-vision: true
  premium-duel-rewards: true
  premium-crate-reroll: true
  premium-shard-interest: 0.0
  premium-shard-interest-cap: 0
  premium-kit-cooldown-hours: 24
  premium-repair-cooldown-minutes: 60
  premium-feed-cooldown-minutes: 30
  premium-portable-workbench: true
premium-kit:
  DIAMOND: 4
  GOLDEN_APPLE: 8
  EXPERIENCE_BOTTLE: 32
  AMETHYST_SHARD: 16
dynamic-pricing:
  enabled: false
  min-multiplier: 0.5
  max-multiplier: 2.5
  buy-pressure-per-item: 0.003
  sell-pressure-per-item: 0.002
  decay-percent-per-hour: 8.0
duels:
  invite-timeout-seconds: 60
  allow-wagers: false
  restore-location-after-seconds: 2
drills:
  enabled: false
  tiers:
    basic:
      material: IRON_PICKAXE
      cost-shards: 500
      max-blocks: 16
      efficiency: 3
    advanced:
      material: DIAMOND_PICKAXE
      cost-shards: 1800
      max-blocks: 36
      efficiency: 5
    mythic:
      material: NETHERITE_PICKAXE
      cost-shards: 5000
      max-blocks: 72
      efficiency: 7
daily:
  money: 150.0
  money-per-streak: 25.0
  shards: 10
  shards-per-streak: 1
  premium-multiplier: 1.5
player-warps:
  promote-cost: 2500.0
creator:
  placeable-crates: true
  protect-placed-crates: true
  default-shop-category-icon: CHEST
  ghost-preview: true
  ghost-preview-range: 6
  ghost-preview-ticks: 5
player-settings:
  public_chat: true
  private_messages: true
  payments: true
  duel_requests: true
  bounty_alerts: true
  market_alerts: true
  scoreboard: true
  night_vision: false
  coordinate_spoof: false
  mob_spawn_hints: true
  premium-hide-command: true
sell-prices:
  COBBLESTONE: 0.25
  DIRT: 0.15
  OAK_LOG: 3.0
  SPRUCE_LOG: 3.0
  WHEAT: 2.0
  CARROT: 1.8
  POTATO: 1.8
  IRON_INGOT: 12.0
  GOLD_INGOT: 18.0
  DIAMOND: 150.0
  EMERALD: 80.0
  NETHERITE_INGOT: 2500.0
  ENDER_PEARL: 20.0
  BLAZE_ROD: 35.0
  GUNPOWDER: 8.0
shard-shop:
  spawner_token:
    icon: SPAWNER
    name: '&dSkeleton Spawner'
    shards: 500
    spawner-type: skeleton
    amount: 1
  common_key:
    icon: TRIPWIRE_HOOK
    name: '&aCommon Crate Key'
    shards: 100
    key-type: common
    amount: 1
  prime_key:
    icon: TRIPWIRE_HOOK
    name: '&bPrime Crate Key'
    shards: 350
    key-type: prime
    amount: 1
crates:
  common:
    display: '&aCommon Crate'
    icon: CHEST
    rewards:
      steak:
        material: COOKED_BEEF
        amount: 32
        weight: 40
      money:
        money: 500
        material: GOLD_INGOT
        amount: 1
        weight: 35
      diamond:
        material: DIAMOND
        amount: 3
        weight: 15
      shards:
        shards: 50
        material: AMETHYST_SHARD
        amount: 1
        weight: 10
  prime:
    display: '&bPrime Crate'
    icon: ENDER_CHEST
    rewards:
      pearls:
        material: ENDER_PEARL
        amount: 16
        weight: 35
      money:
        money: 2500
        material: GOLD_BLOCK
        amount: 1
        weight: 25
      netherite:
        material: NETHERITE_INGOT
        amount: 1
        weight: 10
      shards:
        shards: 200
        material: AMETHYST_SHARD
        amount: 1
        weight: 30
custom-spawners:
  price-shards: 5000
  stack-requires-sneak: true
  drop-generation-seconds: 120
  stack-scaling-exponent: 0.82
  donut-style-curve:
    enabled: true
    asymptote: 1505.35
    multiplier: 0.39567
    decay: 0.00134606
    offset: 8.24358
  types:
    pig:
      name: '&dPig Spawner'
      entity: PIG
      icon: PORKCHOP
      drops:
        PORKCHOP: 7
    cow:
      name: '&dCow Spawner'
      entity: COW
      icon: BEEF
      drops:
        BEEF: 7
    spider:
      name: '&dSpider Spawner'
      entity: SPIDER
      icon: STRING
      drops:
        STRING: 5
        SPIDER_EYE: 2
    zombie_pigman:
      name: '&dZombie Pigman Spawner'
      entity: ZOMBIFIED_PIGLIN
      icon: GOLD_NUGGET
      drops:
        GOLD_NUGGET: 9
    skeleton:
      name: '&dSkeleton Spawner'
      entity: SKELETON
      icon: BONE
      drops:
        BONE: 7
        ARROW: 3
    blaze:
      name: '&dBlaze Spawner'
      entity: BLAZE
      icon: BLAZE_POWDER
      drops:
        BLAZE_POWDER: 5
    creeper:
      name: '&dCreeper Spawner'
      entity: CREEPER
      icon: GUNPOWDER
      drops:
        GUNPOWDER: 6
    iron_golem:
      name: '&dIron Golem Spawner'
      entity: IRON_GOLEM
      icon: IRON_INGOT
      drops:
        IRON_INGOT: 4
messages:
  prefix: '&6&l%server% &8>> &f'


===== src/main/resources/presets/community/preset.yml =====

format: 1
name: Community SMP
description: Low taxes, generous homes, and relaxed progression.
requires-plugins: []


===== src/main/resources/presets/community/shops.yml =====

categories:
  essentials:
    name: '&aEssentials'
    icon: COOKED_BEEF
    items:
      steak:
        material: COOKED_BEEF
        amount: 16
        buy: 250
        sell: 5
      oak_logs:
        material: OAK_LOG
        amount: 32
        buy: 480
        sell: 3
      pearls:
        material: ENDER_PEARL
        amount: 8
        buy: 320
        sell: 20
      golden_apples:
        material: GOLDEN_APPLE
        amount: 4
        buy: 900
        sell: 75
  combat:
    name: '&cCombat'
    icon: DIAMOND_SWORD
    items:
      arrows:
        material: ARROW
        amount: 64
        buy: 220
        sell: 1
      obsidian:
        material: OBSIDIAN
        amount: 16
        buy: 700
        sell: 18
      totem:
        material: TOTEM_OF_UNDYING
        amount: 1
        buy: 6000
        sell: 800
      xp_bottle:
        material: EXPERIENCE_BOTTLE
        amount: 32
        buy: 1600
        sell: 15
  farming:
    name: '&eFarming'
    icon: WHEAT
    items:
      wheat:
        material: WHEAT
        amount: 64
        buy: 360
        sell: 2
      carrots:
        material: CARROT
        amount: 64
        buy: 320
        sell: 1.8
      potatoes:
        material: POTATO
        amount: 64
        buy: 320
        sell: 1.8
      gunpowder:
        material: GUNPOWDER
        amount: 32
        buy: 650
        sell: 8


===== src/main/resources/presets/donut-style/config.yml =====

branding:
  server-name: 'Your SMP'
  display-name: '&6&l%server%'
  menu-title-prefix: '%server% | '
  tablist:
    enabled: true
    header: '&6&l%server%'
    footer: '&7/shop &8| &7/ah &8| &7/bounties &8| &7/crates'
  scoreboard:
    enabled: true
    title: '&6&l%server%'
    lines:
      - '&7%player%'
      - '&8&m------------'
      - '&fMoney: &a%money%'
      - '&fShards: &d%shards%'
      - '&fKills: &c%kills%'
      - '&fBounty: &6%bounty%'
      - '&8&m------------'
      - '&e/smp'

settings:
  starting-money: 1000.0
  starting-shards: 0
  listing-tax-percent: 2.5
  max-auction-listings: 18
  max-market-listings: 18
  order-duration-hours: 24
  order-claim-hours: 90
  default-home-limit: 2
  premium-home-bonus: 4
  kill-shards: 10
  afk-shards-per-minute: 1
  premium-online-shards-per-minute: 2
  premium-fast-buy: true
  premium-hide-command: true
  premium-listing-tax-percent: 0.5
  premium-listing-bonus: 24
  premium-sell-multiplier: 1.35
  premium-vault-rows: 4
  premium-bounty-radar: true
  premium-market-alerts: true
  premium-night-vision: true
  premium-duel-rewards: true
  premium-crate-reroll: true
  premium-shard-interest: 0.015
  premium-shard-interest-cap: 300
  premium-kit-cooldown-hours: 24
  premium-repair-cooldown-minutes: 45
  premium-feed-cooldown-minutes: 20
  premium-portable-workbench: true

premium-kit:
  DIAMOND: 6
  GOLDEN_APPLE: 12
  EXPERIENCE_BOTTLE: 48
  AMETHYST_SHARD: 24

dynamic-pricing:
  enabled: true
  min-multiplier: 0.55
  max-multiplier: 2.75
  buy-pressure-per-item: 0.0025
  sell-pressure-per-item: 0.0018
  decay-percent-per-hour: 10.0

duels:
  invite-timeout-seconds: 60
  allow-wagers: true
  restore-location-after-seconds: 2

drills:
  enabled: true
  tiers:
    basic:
      material: IRON_PICKAXE
      cost-shards: 450
      max-blocks: 18
      efficiency: 3
    advanced:
      material: DIAMOND_PICKAXE
      cost-shards: 1600
      max-blocks: 42
      efficiency: 5
    mythic:
      material: NETHERITE_PICKAXE
      cost-shards: 4500
      max-blocks: 84
      efficiency: 7

daily:
  money: 1250.0
  money-per-streak: 150.0
  shards: 35
  shards-per-streak: 3
  premium-multiplier: 1.6

player-warps:
  promote-cost: 3500.0

creator:
  placeable-crates: true
  protect-placed-crates: true
  default-shop-category-icon: CHEST
  ghost-preview: true
  ghost-preview-range: 6
  ghost-preview-ticks: 5

player-settings:
  public_chat: true
  private_messages: true
  payments: true
  duel_requests: true
  bounty_alerts: true
  market_alerts: true
  scoreboard: true
  night_vision: false
  coordinate_spoof: false
  mob_spawn_hints: true

sell-prices:
  COBBLESTONE: 0.20
  STONE: 0.35
  DIRT: 0.10
  SAND: 0.25
  OAK_LOG: 2.75
  SPRUCE_LOG: 2.75
  WHEAT: 1.75
  CARROT: 1.60
  POTATO: 1.60
  SUGAR_CANE: 2.10
  CACTUS: 1.40
  PORKCHOP: 4.0
  BEEF: 4.25
  STRING: 3.0
  SPIDER_EYE: 4.0
  BONE: 3.0
  ARROW: 1.5
  GOLD_NUGGET: 2.0
  IRON_INGOT: 10.0
  GOLD_INGOT: 18.0
  DIAMOND: 125.0
  EMERALD: 70.0
  NETHERITE_INGOT: 2250.0
  ENDER_PEARL: 18.0
  BLAZE_ROD: 32.0
  BLAZE_POWDER: 18.0
  GUNPOWDER: 7.5
  ROTTEN_FLESH: 1.25

shard-shop:
  pig_spawner:
    icon: PORKCHOP
    name: '&dPig Spawner'
    shards: 1500
    spawner-type: pig
    amount: 1
  cow_spawner:
    icon: BEEF
    name: '&dCow Spawner'
    shards: 1500
    spawner-type: cow
    amount: 1
  spider_spawner:
    icon: STRING
    name: '&dSpider Spawner'
    shards: 1500
    spawner-type: spider
    amount: 1
  zombie_pigman_spawner:
    icon: GOLD_NUGGET
    name: '&dZombie Pigman Spawner'
    shards: 1500
    spawner-type: zombie_pigman
    amount: 1
  skeleton_spawner:
    icon: BONE
    name: '&dSkeleton Spawner'
    shards: 1500
    spawner-type: skeleton
    amount: 1
  blaze_spawner:
    icon: BLAZE_POWDER
    name: '&dBlaze Spawner'
    shards: 1500
    spawner-type: blaze
    amount: 1
  creeper_spawner:
    icon: GUNPOWDER
    name: '&dCreeper Spawner'
    shards: 1500
    spawner-type: creeper
    amount: 1
  iron_golem_spawner:
    icon: IRON_INGOT
    name: '&dIron Golem Spawner'
    shards: 1500
    spawner-type: iron_golem
    amount: 1
  common_key:
    icon: TRIPWIRE_HOOK
    name: '&aCommon Crate Key'
    shards: 100
    key-type: common
    amount: 1
  rare_key:
    icon: TRIPWIRE_HOOK
    name: '&9Rare Crate Key'
    shards: 250
    key-type: rare
    amount: 1
  prime_key:
    icon: TRIPWIRE_HOOK
    name: '&bPrime Crate Key'
    shards: 500
    key-type: prime
    amount: 1

crates:
  common:
    display: '&aCommon Crate'
    icon: CHEST
    rewards:
      food:
        material: COOKED_BEEF
        amount: 48
        weight: 35
      money:
        money: 750
        material: GOLD_INGOT
        amount: 1
        weight: 30
      diamonds:
        material: DIAMOND
        amount: 4
        weight: 20
      shards:
        shards: 75
        material: AMETHYST_SHARD
        amount: 1
        weight: 15
  rare:
    display: '&9Rare Crate'
    icon: BARREL
    rewards:
      money:
        money: 3000
        material: GOLD_BLOCK
        amount: 1
        weight: 32
      pearls:
        material: ENDER_PEARL
        amount: 24
        weight: 25
      totems:
        material: TOTEM_OF_UNDYING
        amount: 1
        weight: 10
      shards:
        shards: 200
        material: AMETHYST_SHARD
        amount: 1
        weight: 33
  prime:
    display: '&bPrime Crate'
    icon: ENDER_CHEST
    rewards:
      cash:
        money: 10000
        material: GOLD_BLOCK
        amount: 4
        weight: 30
      netherite:
        material: NETHERITE_INGOT
        amount: 2
        weight: 12
      prime_shards:
        shards: 600
        material: AMETHYST_SHARD
        amount: 1
        weight: 28
      creeper_spawner:
        spawner-type: creeper
        material: SPAWNER
        amount: 1
        weight: 30

custom-spawners:
  price-shards: 1500
  stack-requires-sneak: true
  drop-generation-seconds: 60
  stack-scaling-exponent: 0.82
  donut-style-curve:
    enabled: true
    asymptote: 1505.35
    multiplier: 0.39567
    decay: 0.00134606
    offset: 8.24358
  types:
    pig:
      name: '&dPig Spawner'
      entity: PIG
      icon: PORKCHOP
      drops:
        PORKCHOP: 7
    cow:
      name: '&dCow Spawner'
      entity: COW
      icon: BEEF
      drops:
        BEEF: 7
    spider:
      name: '&dSpider Spawner'
      entity: SPIDER
      icon: STRING
      drops:
        STRING: 5
        SPIDER_EYE: 2
    zombie_pigman:
      name: '&dZombie Pigman Spawner'
      entity: ZOMBIFIED_PIGLIN
      icon: GOLD_NUGGET
      drops:
        GOLD_NUGGET: 9
    skeleton:
      name: '&dSkeleton Spawner'
      entity: SKELETON
      icon: BONE
      drops:
        BONE: 7
        ARROW: 3
    blaze:
      name: '&dBlaze Spawner'
      entity: BLAZE
      icon: BLAZE_POWDER
      drops:
        BLAZE_POWDER: 5
    creeper:
      name: '&dCreeper Spawner'
      entity: CREEPER
      icon: GUNPOWDER
      drops:
        GUNPOWDER: 6
    iron_golem:
      name: '&dIron Golem Spawner'
      entity: IRON_GOLEM
      icon: IRON_INGOT
      drops:
        IRON_INGOT: 4

messages:
  prefix: '&6&l%server% &8>> &f'


===== src/main/resources/presets/donut-style/preset.yml =====

format: 1
name: Classic Competitive
description: Legacy competitive SMP economy preset.
requires-plugins: []


===== src/main/resources/presets/donut-style/shops.yml =====

categories:
  blocks:
    name: '&aBlocks'
    icon: GRASS_BLOCK
    items:
      obsidian:
        material: OBSIDIAN
        amount: 16
        buy: 700
        sell: 18
      end_stone:
        material: END_STONE
        amount: 32
        buy: 420
        sell: 4
      glass:
        material: GLASS
        amount: 64
        buy: 260
        sell: 1
      oak_logs:
        material: OAK_LOG
        amount: 64
        buy: 700
        sell: 2.75
  farming:
    name: '&eFarming'
    icon: WHEAT
    items:
      wheat:
        material: WHEAT
        amount: 64
        buy: 350
        sell: 1.75
      carrots:
        material: CARROT
        amount: 64
        buy: 330
        sell: 1.60
      potatoes:
        material: POTATO
        amount: 64
        buy: 330
        sell: 1.60
      sugar_cane:
        material: SUGAR_CANE
        amount: 64
        buy: 500
        sell: 2.10
      cactus:
        material: CACTUS
        amount: 64
        buy: 410
        sell: 1.40
  combat:
    name: '&cCombat'
    icon: DIAMOND_SWORD
    items:
      pearls:
        material: ENDER_PEARL
        amount: 16
        buy: 480
        sell: 18
      golden_apples:
        material: GOLDEN_APPLE
        amount: 8
        buy: 1800
        sell: 85
      xp_bottles:
        material: EXPERIENCE_BOTTLE
        amount: 64
        buy: 3000
        sell: 15
      totem:
        material: TOTEM_OF_UNDYING
        amount: 1
        buy: 6500
        sell: 800
      arrows:
        material: ARROW
        amount: 64
        buy: 180
        sell: 1.5
  mob_drops:
    name: '&dMob Drops'
    icon: BONE
    items:
      porkchop:
        material: PORKCHOP
        amount: 64
        buy: 420
        sell: 4
      beef:
        material: BEEF
        amount: 64
        buy: 450
        sell: 4.25
      string:
        material: STRING
        amount: 64
        buy: 360
        sell: 3
      bone:
        material: BONE
        amount: 64
        buy: 360
        sell: 3
      gunpowder:
        material: GUNPOWDER
        amount: 64
        buy: 850
        sell: 7.5
      blaze_powder:
        material: BLAZE_POWDER
        amount: 32
        buy: 920
        sell: 18
  valuables:
    name: '&bValuables'
    icon: DIAMOND
    items:
      iron:
        material: IRON_INGOT
        amount: 16
        buy: 260
        sell: 10
      gold:
        material: GOLD_INGOT
        amount: 16
        buy: 420
        sell: 18
      diamond:
        material: DIAMOND
        amount: 4
        buy: 800
        sell: 125
      emerald:
        material: EMERALD
        amount: 4
        buy: 520
        sell: 70
      netherite:
        material: NETHERITE_INGOT
        amount: 1
        buy: 4500
        sell: 2250


===== src/main/resources/presets/donutsmp-style/config.yml =====

branding:
  server-name: 'Your SMP'
  display-name: '&6&l%server%'
  menu-title-prefix: '%server% | '
  tablist:
    enabled: true
    header: '&6&l%server%'
    footer: '&7/shop &8| &7/ah &8| &7/bounties &8| &7/crates'
  scoreboard:
    enabled: true
    title: '&6&l%server%'
    lines:
      - '&7%player%'
      - '&8&m------------'
      - '&fMoney: &a%money%'
      - '&fShards: &d%shards%'
      - '&fKills: &c%kills%'
      - '&fBounty: &6%bounty%'
      - '&8&m------------'
      - '&e/smp'

settings:
  starting-money: 1000.0
  starting-shards: 0
  listing-tax-percent: 2.5
  max-auction-listings: 18
  max-market-listings: 18
  order-duration-hours: 24
  order-claim-hours: 90
  default-home-limit: 2
  premium-home-bonus: 3
  kill-shards: 10
  afk-shards-per-minute: 1
  premium-online-shards-per-minute: 4
  premium-fast-buy: true
  premium-hide-command: true
  premium-listing-tax-percent: 0.5
  premium-listing-bonus: 24
  premium-sell-multiplier: 1.20
  premium-vault-rows: 4
  premium-bounty-radar: true
  premium-market-alerts: true
  premium-night-vision: true
  premium-duel-rewards: true
  premium-crate-reroll: true
  premium-shard-interest: 0.0
  premium-shard-interest-cap: 0
  premium-kit-cooldown-hours: 24
  premium-repair-cooldown-minutes: 60
  premium-feed-cooldown-minutes: 30
  premium-portable-workbench: true

premium-kit:
  DIAMOND: 6
  GOLDEN_APPLE: 12
  EXPERIENCE_BOTTLE: 48
  AMETHYST_SHARD: 32
  ENDER_PEARL: 16

dynamic-pricing:
  enabled: true
  min-multiplier: 0.55
  max-multiplier: 2.85
  buy-pressure-per-item: 0.0025
  sell-pressure-per-item: 0.0018
  decay-percent-per-hour: 10.0

duels:
  invite-timeout-seconds: 60
  allow-wagers: true
  restore-location-after-seconds: 2

drills:
  enabled: true
  tiers:
    basic:
      material: IRON_PICKAXE
      cost-shards: 500
      max-blocks: 16
      efficiency: 3
    advanced:
      material: DIAMOND_PICKAXE
      cost-shards: 1800
      max-blocks: 40
      efficiency: 5
    mythic:
      material: NETHERITE_PICKAXE
      cost-shards: 5000
      max-blocks: 80
      efficiency: 7

daily:
  money: 1000.0
  money-per-streak: 125.0
  shards: 25
  shards-per-streak: 2
  premium-multiplier: 1.5

player-warps:
  promote-cost: 5000.0

creator:
  placeable-crates: true
  protect-placed-crates: true
  default-shop-category-icon: CHEST
  ghost-preview: true
  ghost-preview-range: 6
  ghost-preview-ticks: 5

player-settings:
  public_chat: true
  private_messages: true
  payments: true
  duel_requests: true
  bounty_alerts: true
  market_alerts: true
  scoreboard: true
  night_vision: false
  coordinate_spoof: false
  mob_spawn_hints: true
  premium-hide-command: true

sell-prices:
  COBBLESTONE: 0.20
  STONE: 0.35
  DEEPSLATE: 0.35
  DIRT: 0.10
  SAND: 0.25
  GRAVEL: 0.20
  OAK_LOG: 2.75
  SPRUCE_LOG: 2.75
  BIRCH_LOG: 2.75
  JUNGLE_LOG: 2.75
  ACACIA_LOG: 2.75
  DARK_OAK_LOG: 2.75
  MANGROVE_LOG: 2.75
  CHERRY_LOG: 2.75
  WHEAT: 1.75
  CARROT: 1.60
  POTATO: 1.60
  BEETROOT: 1.20
  SUGAR_CANE: 2.10
  CACTUS: 1.40
  MELON_SLICE: 0.65
  PUMPKIN: 2.25
  PORKCHOP: 4.0
  BEEF: 4.25
  CHICKEN: 3.5
  MUTTON: 3.75
  RABBIT: 4.0
  LEATHER: 3.5
  FEATHER: 1.5
  STRING: 3.0
  SPIDER_EYE: 4.0
  BONE: 3.0
  ARROW: 1.5
  ROTTEN_FLESH: 1.25
  GOLD_NUGGET: 2.0
  BLAZE_POWDER: 18.0
  BLAZE_ROD: 32.0
  GUNPOWDER: 7.5
  ENDER_PEARL: 18.0
  SLIME_BALL: 12.0
  PRISMARINE_SHARD: 8.0
  PRISMARINE_CRYSTALS: 10.0
  IRON_INGOT: 10.0
  GOLD_INGOT: 18.0
  COPPER_INGOT: 3.0
  REDSTONE: 2.0
  LAPIS_LAZULI: 3.0
  QUARTZ: 4.0
  DIAMOND: 125.0
  EMERALD: 70.0
  NETHERITE_SCRAP: 650.0
  NETHERITE_INGOT: 2250.0
  OBSIDIAN: 18.0
  END_STONE: 4.0

shard-shop:
  pig_spawner:
    icon: PORKCHOP
    name: '&dPig Spawner'
    shards: 1500
    spawner-type: pig
    amount: 1
  cow_spawner:
    icon: BEEF
    name: '&dCow Spawner'
    shards: 1500
    spawner-type: cow
    amount: 1
  chicken_spawner:
    icon: FEATHER
    name: '&dChicken Spawner'
    shards: 1500
    spawner-type: chicken
    amount: 1
  sheep_spawner:
    icon: WHITE_WOOL
    name: '&dSheep Spawner'
    shards: 1500
    spawner-type: sheep
    amount: 1
  spider_spawner:
    icon: STRING
    name: '&dSpider Spawner'
    shards: 1500
    spawner-type: spider
    amount: 1
  zombie_spawner:
    icon: ROTTEN_FLESH
    name: '&dZombie Spawner'
    shards: 1500
    spawner-type: zombie
    amount: 1
  zombie_pigman_spawner:
    icon: GOLD_NUGGET
    name: '&dZombie Pigman Spawner'
    shards: 1500
    spawner-type: zombie_pigman
    amount: 1
  skeleton_spawner:
    icon: BONE
    name: '&dSkeleton Spawner'
    shards: 1500
    spawner-type: skeleton
    amount: 1
  blaze_spawner:
    icon: BLAZE_POWDER
    name: '&dBlaze Spawner'
    shards: 1500
    spawner-type: blaze
    amount: 1
  creeper_spawner:
    icon: GUNPOWDER
    name: '&dCreeper Spawner'
    shards: 1500
    spawner-type: creeper
    amount: 1
  enderman_spawner:
    icon: ENDER_PEARL
    name: '&dEnderman Spawner'
    shards: 1500
    spawner-type: enderman
    amount: 1
  iron_golem_spawner:
    icon: IRON_INGOT
    name: '&dIron Golem Spawner'
    shards: 1500
    spawner-type: iron_golem
    amount: 1
  guardian_spawner:
    icon: PRISMARINE_SHARD
    name: '&dGuardian Spawner'
    shards: 1500
    spawner-type: guardian
    amount: 1
  common_key:
    icon: TRIPWIRE_HOOK
    name: '&aCommon Crate Key'
    shards: 100
    key-type: common
    amount: 1
  prime_key:
    icon: TRIPWIRE_HOOK
    name: '&bPrime Crate Key'
    shards: 250
    key-type: prime
    amount: 1
  gold_key:
    icon: TRIPWIRE_HOOK
    name: '&6Gold Crate Key'
    shards: 450
    key-type: gold
    amount: 1
  amethyst_key:
    icon: TRIPWIRE_HOOK
    name: '&dAmethyst Crate Key'
    shards: 750
    key-type: amethyst
    amount: 1
  crimson_key:
    icon: TRIPWIRE_HOOK
    name: '&cCrimson Crate Key'
    shards: 1100
    key-type: crimson
    amount: 1

crates:
  common:
    display: '&aCommon Crate'
    icon: CHEST
    animation-ticks: 60
    rewards:
      food_bundle:
        material: COOKED_BEEF
        amount: 48
        weight: 28
      cash_small:
        money: 750
        material: GOLD_INGOT
        amount: 1
        weight: 30
      diamonds:
        material: DIAMOND
        amount: 4
        weight: 16
      shards:
        shards: 75
        material: AMETHYST_SHARD
        amount: 1
        weight: 16
      prime_key:
        material: TRIPWIRE_HOOK
        amount: 1
        key-type: prime
        weight: 10
  prime:
    display: '&bPrime Crate'
    icon: ENDER_CHEST
    animation-ticks: 70
    rewards:
      cash:
        money: 3000
        material: GOLD_BLOCK
        amount: 1
        weight: 28
      pearls:
        material: ENDER_PEARL
        amount: 24
        weight: 22
      totem:
        material: TOTEM_OF_UNDYING
        amount: 1
        weight: 10
      shards:
        shards: 200
        material: AMETHYST_SHARD
        amount: 1
        weight: 25
      gold_key:
        material: TRIPWIRE_HOOK
        amount: 1
        key-type: gold
        weight: 15
  gold:
    display: '&6Gold Crate'
    icon: GOLD_BLOCK
    animation-ticks: 80
    rewards:
      cash_large:
        money: 10000
        material: GOLD_BLOCK
        amount: 4
        weight: 28
      netherite:
        material: NETHERITE_INGOT
        amount: 2
        weight: 12
      creeper_spawner:
        spawner-type: creeper
        material: SPAWNER
        amount: 1
        weight: 22
      shards:
        shards: 550
        material: AMETHYST_SHARD
        amount: 1
        weight: 23
      amethyst_key:
        material: TRIPWIRE_HOOK
        amount: 1
        key-type: amethyst
        weight: 15
  amethyst:
    display: '&dAmethyst Crate'
    icon: AMETHYST_CLUSTER
    animation-ticks: 90
    rewards:
      amethyst_pickaxe:
        material: NETHERITE_PICKAXE
        amount: 1
        weight: 14
      amethyst_axe:
        material: NETHERITE_AXE
        amount: 1
        weight: 14
      amethyst_shovel:
        material: NETHERITE_SHOVEL
        amount: 1
        weight: 14
      shard_booster:
        shards: 1200
        material: AMETHYST_SHARD
        amount: 1
        weight: 24
      iron_golem_spawner:
        spawner-type: iron_golem
        material: SPAWNER
        amount: 1
        weight: 20
      crimson_key:
        material: TRIPWIRE_HOOK
        amount: 1
        key-type: crimson
        weight: 14
  crimson:
    display: '&cCrimson Crate'
    icon: NETHER_STAR
    animation-ticks: 100
    rewards:
      cash_jackpot:
        money: 50000
        material: EMERALD_BLOCK
        amount: 8
        weight: 25
      netherite_bundle:
        material: NETHERITE_INGOT
        amount: 6
        weight: 16
      golem_spawners:
        spawner-type: iron_golem
        material: SPAWNER
        amount: 3
        weight: 22
      creeper_spawners:
        spawner-type: creeper
        material: SPAWNER
        amount: 3
        weight: 22
      shard_jackpot:
        shards: 2500
        material: AMETHYST_SHARD
        amount: 1
        weight: 15

custom-spawners:
  price-shards: 1500
  stack-requires-sneak: true
  drop-generation-seconds: 60
  stack-scaling-exponent: 0.82
  donut-style-curve:
    enabled: true
    asymptote: 1505.35
    multiplier: 0.39567
    decay: 0.00134606
    offset: 8.24358
  types:
    pig:
      name: '&dPig Spawner'
      entity: PIG
      icon: PORKCHOP
      drops:
        PORKCHOP: 7
    cow:
      name: '&dCow Spawner'
      entity: COW
      icon: BEEF
      drops:
        BEEF: 7
        LEATHER: 2
    chicken:
      name: '&dChicken Spawner'
      entity: CHICKEN
      icon: FEATHER
      drops:
        CHICKEN: 6
        FEATHER: 3
    sheep:
      name: '&dSheep Spawner'
      entity: SHEEP
      icon: WHITE_WOOL
      drops:
        MUTTON: 6
        WHITE_WOOL: 3
    spider:
      name: '&dSpider Spawner'
      entity: SPIDER
      icon: STRING
      drops:
        STRING: 5
        SPIDER_EYE: 2
    zombie:
      name: '&dZombie Spawner'
      entity: ZOMBIE
      icon: ROTTEN_FLESH
      drops:
        ROTTEN_FLESH: 7
    zombie_pigman:
      name: '&dZombie Pigman Spawner'
      entity: ZOMBIFIED_PIGLIN
      icon: GOLD_NUGGET
      drops:
        GOLD_NUGGET: 9
    skeleton:
      name: '&dSkeleton Spawner'
      entity: SKELETON
      icon: BONE
      drops:
        BONE: 7
        ARROW: 3
    blaze:
      name: '&dBlaze Spawner'
      entity: BLAZE
      icon: BLAZE_POWDER
      drops:
        BLAZE_POWDER: 5
        BLAZE_ROD: 1
    creeper:
      name: '&dCreeper Spawner'
      entity: CREEPER
      icon: GUNPOWDER
      drops:
        GUNPOWDER: 6
    enderman:
      name: '&dEnderman Spawner'
      entity: ENDERMAN
      icon: ENDER_PEARL
      drops:
        ENDER_PEARL: 4
    iron_golem:
      name: '&dIron Golem Spawner'
      entity: IRON_GOLEM
      icon: IRON_INGOT
      drops:
        IRON_INGOT: 4
        POPPY: 1
    guardian:
      name: '&dGuardian Spawner'
      entity: GUARDIAN
      icon: PRISMARINE_SHARD
      drops:
        PRISMARINE_SHARD: 5
        PRISMARINE_CRYSTALS: 2

messages:
  prefix: '&6&l%server% &8>> &f'


===== src/main/resources/presets/donutsmp-style/preset.yml =====

format: 1
name: DonutSMP Style
description: Competitive economy, virtual spawners, shards, shops, and crates.
requires-plugins: []


===== src/main/resources/presets/donutsmp-style/shops.yml =====

categories:
  blocks:
    name: '&aBlocks'
    icon: GRASS_BLOCK
    items:
      obsidian:
        material: OBSIDIAN
        amount: 16
        buy: 700
        sell: 18
      end_stone:
        material: END_STONE
        amount: 32
        buy: 420
        sell: 4
      glass:
        material: GLASS
        amount: 64
        buy: 260
        sell: 1
      stone:
        material: STONE
        amount: 64
        buy: 120
        sell: 0.35
      deepslate:
        material: DEEPSLATE
        amount: 64
        buy: 120
        sell: 0.35
      oak_logs:
        material: OAK_LOG
        amount: 64
        buy: 700
        sell: 2.75
      spruce_logs:
        material: SPRUCE_LOG
        amount: 64
        buy: 700
        sell: 2.75
  farming:
    name: '&eFarming'
    icon: WHEAT
    items:
      wheat:
        material: WHEAT
        amount: 64
        buy: 350
        sell: 1.75
      carrots:
        material: CARROT
        amount: 64
        buy: 330
        sell: 1.60
      potatoes:
        material: POTATO
        amount: 64
        buy: 330
        sell: 1.60
      sugar_cane:
        material: SUGAR_CANE
        amount: 64
        buy: 500
        sell: 2.10
      cactus:
        material: CACTUS
        amount: 64
        buy: 410
        sell: 1.40
      pumpkin:
        material: PUMPKIN
        amount: 32
        buy: 220
        sell: 2.25
  combat:
    name: '&cCombat'
    icon: DIAMOND_SWORD
    items:
      pearls:
        material: ENDER_PEARL
        amount: 16
        buy: 480
        sell: 18
      golden_apples:
        material: GOLDEN_APPLE
        amount: 8
        buy: 1800
        sell: 85
      xp_bottles:
        material: EXPERIENCE_BOTTLE
        amount: 64
        buy: 3000
        sell: 15
      totem:
        material: TOTEM_OF_UNDYING
        amount: 1
        buy: 6500
        sell: 800
      arrows:
        material: ARROW
        amount: 64
        buy: 180
        sell: 1.5
      obsidian:
        material: OBSIDIAN
        amount: 64
        buy: 2600
        sell: 18
  mob_drops:
    name: '&dMob Drops'
    icon: BONE
    items:
      porkchop:
        material: PORKCHOP
        amount: 64
        buy: 420
        sell: 4
      beef:
        material: BEEF
        amount: 64
        buy: 450
        sell: 4.25
      chicken:
        material: CHICKEN
        amount: 64
        buy: 380
        sell: 3.5
      string:
        material: STRING
        amount: 64
        buy: 360
        sell: 3
      bone:
        material: BONE
        amount: 64
        buy: 360
        sell: 3
      rotten_flesh:
        material: ROTTEN_FLESH
        amount: 64
        buy: 220
        sell: 1.25
      gunpowder:
        material: GUNPOWDER
        amount: 64
        buy: 850
        sell: 7.5
      blaze_powder:
        material: BLAZE_POWDER
        amount: 32
        buy: 920
        sell: 18
      ender_pearls:
        material: ENDER_PEARL
        amount: 16
        buy: 480
        sell: 18
  valuables:
    name: '&bValuables'
    icon: DIAMOND
    items:
      iron:
        material: IRON_INGOT
        amount: 16
        buy: 260
        sell: 10
      gold:
        material: GOLD_INGOT
        amount: 16
        buy: 420
        sell: 18
      copper:
        material: COPPER_INGOT
        amount: 32
        buy: 160
        sell: 3
      diamond:
        material: DIAMOND
        amount: 4
        buy: 800
        sell: 125
      emerald:
        material: EMERALD
        amount: 4
        buy: 520
        sell: 70
      netherite_scrap:
        material: NETHERITE_SCRAP
        amount: 1
        buy: 1300
        sell: 650
      netherite:
        material: NETHERITE_INGOT
        amount: 1
        buy: 4500
        sell: 2250
  redstone:
    name: '&cRedstone'
    icon: REDSTONE
    items:
      redstone:
        material: REDSTONE
        amount: 64
        buy: 180
        sell: 2
      hopper:
        material: HOPPER
        amount: 8
        buy: 900
        sell: 25
      observer:
        material: OBSERVER
        amount: 16
        buy: 900
        sell: 18
      piston:
        material: PISTON
        amount: 16
        buy: 640
        sell: 14
      sticky_piston:
        material: STICKY_PISTON
        amount: 16
        buy: 850
        sell: 18


===== src/main/resources/presets/pvp-economy/config.yml =====

branding:
  server-name: Your SMP
  display-name: '&6&l%server%'
  menu-title-prefix: '%server% | '
  tablist:
    enabled: true
    header: '&6&l%server%'
    footer: '&7/shop &8| &7/ah &8| &7/bounties &8| &7/crates'
  scoreboard:
    enabled: true
    title: '&6&l%server%'
    lines:
    - '&7%player%'
    - '&8&m------------'
    - '&fMoney: &a%money%'
    - '&fShards: &d%shards%'
    - '&fKills: &c%kills%'
    - '&fBounty: &6%bounty%'
    - '&8&m------------'
    - '&e/smp'
settings:
  starting-money: 250.0
  starting-shards: 0
  listing-tax-percent: 4.0
  max-auction-listings: 12
  max-market-listings: 12
  order-duration-hours: 24
  order-claim-hours: 90
  default-home-limit: 1
  premium-home-bonus: 3
  kill-shards: 15
  afk-shards-per-minute: 0
  premium-online-shards-per-minute: 0
  premium-fast-buy: true
  premium-listing-tax-percent: 2.0
  premium-listing-bonus: 18
  premium-sell-multiplier: 1.25
  premium-vault-rows: 3
  premium-bounty-radar: true
  premium-market-alerts: true
  premium-night-vision: true
  premium-duel-rewards: true
  premium-crate-reroll: true
  premium-shard-interest: 0.0
  premium-shard-interest-cap: 0
  premium-kit-cooldown-hours: 24
  premium-repair-cooldown-minutes: 60
  premium-feed-cooldown-minutes: 30
  premium-portable-workbench: true
premium-kit:
  DIAMOND: 4
  GOLDEN_APPLE: 8
  EXPERIENCE_BOTTLE: 32
  AMETHYST_SHARD: 16
dynamic-pricing:
  enabled: true
  min-multiplier: 0.5
  max-multiplier: 2.0
  buy-pressure-per-item: 0.003
  sell-pressure-per-item: 0.002
  decay-percent-per-hour: 8.0
duels:
  invite-timeout-seconds: 60
  allow-wagers: true
  restore-location-after-seconds: 2
drills:
  enabled: true
  tiers:
    basic:
      material: IRON_PICKAXE
      cost-shards: 500
      max-blocks: 16
      efficiency: 3
    advanced:
      material: DIAMOND_PICKAXE
      cost-shards: 1800
      max-blocks: 36
      efficiency: 5
    mythic:
      material: NETHERITE_PICKAXE
      cost-shards: 5000
      max-blocks: 72
      efficiency: 7
daily:
  money: 200.0
  money-per-streak: 25.0
  shards: 10
  shards-per-streak: 1
  premium-multiplier: 1.5
player-warps:
  promote-cost: 2500.0
creator:
  placeable-crates: true
  protect-placed-crates: true
  default-shop-category-icon: CHEST
  ghost-preview: true
  ghost-preview-range: 6
  ghost-preview-ticks: 5
player-settings:
  public_chat: true
  private_messages: true
  payments: true
  duel_requests: true
  bounty_alerts: true
  market_alerts: true
  scoreboard: true
  night_vision: false
  coordinate_spoof: false
  mob_spawn_hints: true
  premium-hide-command: true
sell-prices:
  COBBLESTONE: 0.25
  DIRT: 0.15
  OAK_LOG: 3.0
  SPRUCE_LOG: 3.0
  WHEAT: 2.0
  CARROT: 1.8
  POTATO: 1.8
  IRON_INGOT: 12.0
  GOLD_INGOT: 18.0
  DIAMOND: 150.0
  EMERALD: 80.0
  NETHERITE_INGOT: 2500.0
  ENDER_PEARL: 20.0
  BLAZE_ROD: 35.0
  GUNPOWDER: 8.0
shard-shop:
  spawner_token:
    icon: SPAWNER
    name: '&dSkeleton Spawner'
    shards: 500
    spawner-type: skeleton
    amount: 1
  common_key:
    icon: TRIPWIRE_HOOK
    name: '&aCommon Crate Key'
    shards: 100
    key-type: common
    amount: 1
  prime_key:
    icon: TRIPWIRE_HOOK
    name: '&bPrime Crate Key'
    shards: 350
    key-type: prime
    amount: 1
crates:
  common:
    display: '&aCommon Crate'
    icon: CHEST
    rewards:
      steak:
        material: COOKED_BEEF
        amount: 32
        weight: 40
      money:
        money: 500
        material: GOLD_INGOT
        amount: 1
        weight: 35
      diamond:
        material: DIAMOND
        amount: 3
        weight: 15
      shards:
        shards: 50
        material: AMETHYST_SHARD
        amount: 1
        weight: 10
  prime:
    display: '&bPrime Crate'
    icon: ENDER_CHEST
    rewards:
      pearls:
        material: ENDER_PEARL
        amount: 16
        weight: 35
      money:
        money: 2500
        material: GOLD_BLOCK
        amount: 1
        weight: 25
      netherite:
        material: NETHERITE_INGOT
        amount: 1
        weight: 10
      shards:
        shards: 200
        material: AMETHYST_SHARD
        amount: 1
        weight: 30
custom-spawners:
  price-shards: 3000
  stack-requires-sneak: true
  drop-generation-seconds: 75
  stack-scaling-exponent: 0.82
  donut-style-curve:
    enabled: true
    asymptote: 1505.35
    multiplier: 0.39567
    decay: 0.00134606
    offset: 8.24358
  types:
    pig:
      name: '&dPig Spawner'
      entity: PIG
      icon: PORKCHOP
      drops:
        PORKCHOP: 7
    cow:
      name: '&dCow Spawner'
      entity: COW
      icon: BEEF
      drops:
        BEEF: 7
    spider:
      name: '&dSpider Spawner'
      entity: SPIDER
      icon: STRING
      drops:
        STRING: 5
        SPIDER_EYE: 2
    zombie_pigman:
      name: '&dZombie Pigman Spawner'
      entity: ZOMBIFIED_PIGLIN
      icon: GOLD_NUGGET
      drops:
        GOLD_NUGGET: 9
    skeleton:
      name: '&dSkeleton Spawner'
      entity: SKELETON
      icon: BONE
      drops:
        BONE: 7
        ARROW: 3
    blaze:
      name: '&dBlaze Spawner'
      entity: BLAZE
      icon: BLAZE_POWDER
      drops:
        BLAZE_POWDER: 5
    creeper:
      name: '&dCreeper Spawner'
      entity: CREEPER
      icon: GUNPOWDER
      drops:
        GUNPOWDER: 6
    iron_golem:
      name: '&dIron Golem Spawner'
      entity: IRON_GOLEM
      icon: IRON_INGOT
      drops:
        IRON_INGOT: 4
messages:
  prefix: '&6&l%server% &8>> &f'


===== src/main/resources/presets/pvp-economy/preset.yml =====

format: 1
name: PvP Economy
description: Competitive trading, kill rewards, and wager duels.
requires-plugins: []


===== src/main/resources/presets/pvp-economy/shops.yml =====

categories:
  essentials:
    name: '&aEssentials'
    icon: COOKED_BEEF
    items:
      steak:
        material: COOKED_BEEF
        amount: 16
        buy: 250
        sell: 5
      oak_logs:
        material: OAK_LOG
        amount: 32
        buy: 480
        sell: 3
      pearls:
        material: ENDER_PEARL
        amount: 8
        buy: 320
        sell: 20
      golden_apples:
        material: GOLDEN_APPLE
        amount: 4
        buy: 900
        sell: 75
  combat:
    name: '&cCombat'
    icon: DIAMOND_SWORD
    items:
      arrows:
        material: ARROW
        amount: 64
        buy: 220
        sell: 1
      obsidian:
        material: OBSIDIAN
        amount: 16
        buy: 700
        sell: 18
      totem:
        material: TOTEM_OF_UNDYING
        amount: 1
        buy: 6000
        sell: 800
      xp_bottle:
        material: EXPERIENCE_BOTTLE
        amount: 32
        buy: 1600
        sell: 15
  farming:
    name: '&eFarming'
    icon: WHEAT
    items:
      wheat:
        material: WHEAT
        amount: 64
        buy: 360
        sell: 2
      carrots:
        material: CARROT
        amount: 64
        buy: 320
        sell: 1.8
      potatoes:
        material: POTATO
        amount: 64
        buy: 320
        sell: 1.8
      gunpowder:
        material: GUNPOWDER
        amount: 32
        buy: 650
        sell: 8


===== src/main/resources/presets/survival-plus/config.yml =====

branding:
  server-name: Your SMP
  display-name: '&6&l%server%'
  menu-title-prefix: '%server% | '
  tablist:
    enabled: true
    header: '&6&l%server%'
    footer: '&7/shop &8| &7/ah &8| &7/bounties &8| &7/crates'
  scoreboard:
    enabled: true
    title: '&6&l%server%'
    lines:
    - '&7%player%'
    - '&8&m------------'
    - '&fMoney: &a%money%'
    - '&fShards: &d%shards%'
    - '&fKills: &c%kills%'
    - '&fBounty: &6%bounty%'
    - '&8&m------------'
    - '&e/smp'
settings:
  starting-money: 1500.0
  starting-shards: 0
  listing-tax-percent: 1.5
  max-auction-listings: 18
  max-market-listings: 18
  order-duration-hours: 24
  order-claim-hours: 90
  default-home-limit: 4
  premium-home-bonus: 3
  kill-shards: 2
  afk-shards-per-minute: 1
  premium-online-shards-per-minute: 1
  premium-fast-buy: true
  premium-listing-tax-percent: 1.0
  premium-listing-bonus: 18
  premium-sell-multiplier: 1.25
  premium-vault-rows: 3
  premium-bounty-radar: true
  premium-market-alerts: true
  premium-night-vision: true
  premium-duel-rewards: true
  premium-crate-reroll: true
  premium-shard-interest: 0.0
  premium-shard-interest-cap: 0
  premium-kit-cooldown-hours: 24
  premium-repair-cooldown-minutes: 60
  premium-feed-cooldown-minutes: 30
  premium-portable-workbench: true
premium-kit:
  DIAMOND: 4
  GOLDEN_APPLE: 8
  EXPERIENCE_BOTTLE: 32
  AMETHYST_SHARD: 16
dynamic-pricing:
  enabled: true
  min-multiplier: 0.75
  max-multiplier: 1.5
  buy-pressure-per-item: 0.003
  sell-pressure-per-item: 0.002
  decay-percent-per-hour: 8.0
duels:
  invite-timeout-seconds: 60
  allow-wagers: false
  restore-location-after-seconds: 2
drills:
  enabled: true
  tiers:
    basic:
      material: IRON_PICKAXE
      cost-shards: 500
      max-blocks: 16
      efficiency: 3
    advanced:
      material: DIAMOND_PICKAXE
      cost-shards: 1800
      max-blocks: 36
      efficiency: 5
    mythic:
      material: NETHERITE_PICKAXE
      cost-shards: 5000
      max-blocks: 72
      efficiency: 7
daily:
  money: 400.0
  money-per-streak: 50.0
  shards: 20
  shards-per-streak: 2
  premium-multiplier: 1.5
player-warps:
  promote-cost: 2500.0
creator:
  placeable-crates: true
  protect-placed-crates: true
  default-shop-category-icon: CHEST
  ghost-preview: true
  ghost-preview-range: 6
  ghost-preview-ticks: 5
player-settings:
  public_chat: true
  private_messages: true
  payments: true
  duel_requests: true
  bounty_alerts: true
  market_alerts: true
  scoreboard: true
  night_vision: false
  coordinate_spoof: false
  mob_spawn_hints: true
  premium-hide-command: true
sell-prices:
  COBBLESTONE: 0.25
  DIRT: 0.15
  OAK_LOG: 3.0
  SPRUCE_LOG: 3.0
  WHEAT: 2.0
  CARROT: 1.8
  POTATO: 1.8
  IRON_INGOT: 12.0
  GOLD_INGOT: 18.0
  DIAMOND: 150.0
  EMERALD: 80.0
  NETHERITE_INGOT: 2500.0
  ENDER_PEARL: 20.0
  BLAZE_ROD: 35.0
  GUNPOWDER: 8.0
shard-shop:
  spawner_token:
    icon: SPAWNER
    name: '&dSkeleton Spawner'
    shards: 500
    spawner-type: skeleton
    amount: 1
  common_key:
    icon: TRIPWIRE_HOOK
    name: '&aCommon Crate Key'
    shards: 100
    key-type: common
    amount: 1
  prime_key:
    icon: TRIPWIRE_HOOK
    name: '&bPrime Crate Key'
    shards: 350
    key-type: prime
    amount: 1
crates:
  common:
    display: '&aCommon Crate'
    icon: CHEST
    rewards:
      steak:
        material: COOKED_BEEF
        amount: 32
        weight: 40
      money:
        money: 500
        material: GOLD_INGOT
        amount: 1
        weight: 35
      diamond:
        material: DIAMOND
        amount: 3
        weight: 15
      shards:
        shards: 50
        material: AMETHYST_SHARD
        amount: 1
        weight: 10
  prime:
    display: '&bPrime Crate'
    icon: ENDER_CHEST
    rewards:
      pearls:
        material: ENDER_PEARL
        amount: 16
        weight: 35
      money:
        money: 2500
        material: GOLD_BLOCK
        amount: 1
        weight: 25
      netherite:
        material: NETHERITE_INGOT
        amount: 1
        weight: 10
      shards:
        shards: 200
        material: AMETHYST_SHARD
        amount: 1
        weight: 30
custom-spawners:
  price-shards: 2000
  stack-requires-sneak: true
  drop-generation-seconds: 90
  stack-scaling-exponent: 0.82
  donut-style-curve:
    enabled: true
    asymptote: 1505.35
    multiplier: 0.39567
    decay: 0.00134606
    offset: 8.24358
  types:
    pig:
      name: '&dPig Spawner'
      entity: PIG
      icon: PORKCHOP
      drops:
        PORKCHOP: 7
    cow:
      name: '&dCow Spawner'
      entity: COW
      icon: BEEF
      drops:
        BEEF: 7
    spider:
      name: '&dSpider Spawner'
      entity: SPIDER
      icon: STRING
      drops:
        STRING: 5
        SPIDER_EYE: 2
    zombie_pigman:
      name: '&dZombie Pigman Spawner'
      entity: ZOMBIFIED_PIGLIN
      icon: GOLD_NUGGET
      drops:
        GOLD_NUGGET: 9
    skeleton:
      name: '&dSkeleton Spawner'
      entity: SKELETON
      icon: BONE
      drops:
        BONE: 7
        ARROW: 3
    blaze:
      name: '&dBlaze Spawner'
      entity: BLAZE
      icon: BLAZE_POWDER
      drops:
        BLAZE_POWDER: 5
    creeper:
      name: '&dCreeper Spawner'
      entity: CREEPER
      icon: GUNPOWDER
      drops:
        GUNPOWDER: 6
    iron_golem:
      name: '&dIron Golem Spawner'
      entity: IRON_GOLEM
      icon: IRON_INGOT
      drops:
        IRON_INGOT: 4
messages:
  prefix: '&6&l%server% &8>> &f'


===== src/main/resources/presets/survival-plus/preset.yml =====

format: 1
name: Survival Plus
description: Balanced survival economy with daily rewards and gentle price changes.
requires-plugins: []


===== src/main/resources/presets/survival-plus/shops.yml =====

categories:
  essentials:
    name: '&aEssentials'
    icon: COOKED_BEEF
    items:
      steak:
        material: COOKED_BEEF
        amount: 16
        buy: 250
        sell: 5
      oak_logs:
        material: OAK_LOG
        amount: 32
        buy: 480
        sell: 3
      pearls:
        material: ENDER_PEARL
        amount: 8
        buy: 320
        sell: 20
      golden_apples:
        material: GOLDEN_APPLE
        amount: 4
        buy: 900
        sell: 75
  combat:
    name: '&cCombat'
    icon: DIAMOND_SWORD
    items:
      arrows:
        material: ARROW
        amount: 64
        buy: 220
        sell: 1
      obsidian:
        material: OBSIDIAN
        amount: 16
        buy: 700
        sell: 18
      totem:
        material: TOTEM_OF_UNDYING
        amount: 1
        buy: 6000
        sell: 800
      xp_bottle:
        material: EXPERIENCE_BOTTLE
        amount: 32
        buy: 1600
        sell: 15
  farming:
    name: '&eFarming'
    icon: WHEAT
    items:
      wheat:
        material: WHEAT
        amount: 64
        buy: 360
        sell: 2
      carrots:
        material: CARROT
        amount: 64
        buy: 320
        sell: 1.8
      potatoes:
        material: POTATO
        amount: 64
        buy: 320
        sell: 1.8
      gunpowder:
        material: GUNPOWDER
        amount: 32
        buy: 650
        sell: 8


===== src/main/resources/shops.yml =====

categories:
  essentials:
    name: '&aEssentials'
    icon: COOKED_BEEF
    items:
      steak:
        material: COOKED_BEEF
        amount: 16
        buy: 250
        sell: 5
      oak_logs:
        material: OAK_LOG
        amount: 32
        buy: 480
        sell: 3
      pearls:
        material: ENDER_PEARL
        amount: 8
        buy: 320
        sell: 20
      golden_apples:
        material: GOLDEN_APPLE
        amount: 4
        buy: 900
        sell: 75
  combat:
    name: '&cCombat'
    icon: DIAMOND_SWORD
    items:
      arrows:
        material: ARROW
        amount: 64
        buy: 220
        sell: 1
      obsidian:
        material: OBSIDIAN
        amount: 16
        buy: 700
        sell: 18
      totem:
        material: TOTEM_OF_UNDYING
        amount: 1
        buy: 6000
        sell: 800
      xp_bottle:
        material: EXPERIENCE_BOTTLE
        amount: 32
        buy: 1600
        sell: 15
  farming:
    name: '&eFarming'
    icon: WHEAT
    items:
      wheat:
        material: WHEAT
        amount: 64
        buy: 360
        sell: 2
      carrots:
        material: CARROT
        amount: 64
        buy: 320
        sell: 1.8
      potatoes:
        material: POTATO
        amount: 64
        buy: 320
        sell: 1.8
      gunpowder:
        material: GUNPOWDER
        amount: 32
        buy: 650
        sell: 8p