"""
main.py — Harry Potter Wizard RPG entry point.

Run:
    python main.py

Adjust imports at the top if your filenames differ in capitalization.
"""

import json
import random
from pathlib import Path

from Data import (
    ENEMIES, ENEMIES_BY_TIER,
    POTIONS, GEAR, GEAR_SLOTS,
    ATTRIBUTES, ATTR_DISPLAY,
    YEAR_LEVEL_RANGE, ATTRIBUTE_CAP_BY_YEAR, SPELL_CAP_BY_YEAR,
    HOUSES, HOUSE_KEYS,
)
from Player import Player, WAND_WOOD_BONUS, WAND_CORES
from Enemy import Enemy, random_enemy_key
from Combat import run_battle
from Items import (
    add_to_inventory, use_potion, equip_gear, unequip_gear,
    show_inventory, show_equipped,
)
from Shop import menu_spell_shop, menu_apothecary, menu_wand_shop


# ============================================================
# CONFIG
# ============================================================

SAVE_FILE = "savegame.json"

TIER_MIN_LEVEL = {
    "very_weak":   1,
    "weak":        2,
    "average":     3,
    "strong":      5,
    "very_strong": 8,
}

TIER_DISPLAY = {
    "very_weak":   "Very Weak",
    "weak":        "Weak",
    "average":     "Average",
    "strong":      "Strong",
    "very_strong": "Very Strong",
}

TIER_ORDER = ["very_weak", "weak", "average", "strong", "very_strong"]


# ============================================================
# INPUT HELPERS
# ============================================================

def prompt(text="  > "):
    try:
        return input(text).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def pause(text="  Press Enter to continue..."):
    try:
        input(text)
    except (EOFError, KeyboardInterrupt):
        print()


# ============================================================
# TITLE
# ============================================================
def show_help():
    """Beginner-friendly explanation of game mechanics."""
    sections = [
        ("HOW TO PLAY", [
            "Fight enemies to earn XP, Galleons, and Spell Tokens.",
            "Level up to gain Attribute Points and raise your stats.",
            "Spend Spell Tokens to learn new spells.",
            "Spend Galleons on potions, gear, and wand upgrades.",
            "The main hub lets you fight, shop, rest, or manage gear.",
        ]),
        ("ATTRIBUTES", [
            "Brawn      — strength, endurance, physical toughness",
            "Agility    — speed, reflexes, initiative, dodging",
            "Intellect  — memory, logic, spell learning, potions",
            "Perception — awareness, aim, spotting danger",
            "Willpower  — focus, courage, resisting mind magic",
            "Presence   — charm, leadership, persuasion",
            "Power      — raw magical force, spell damage, mana",
            "Control    — precision, spell accuracy, finesse",
            "",
            "Scale: 1-10. Students are 2-4. Prodigies are 6-8.",
            "Every level you get +1 point to spend on any attribute.",
        ]),
        ("DERIVED STATS", [
            "HP        — how much damage you can take",
            "Mana      — fuel for casting spells",
            "Phys Def  — Agility + Brawn + 8     (vs physical attacks)",
            "Mag Def   — Willpower + Control + 8 (vs spells)",
            "Initiative— Agility + Perception     (who goes first)",
            "Accuracy  — Control + Perception     (spell hit chance)",
        ]),
        ("COMBAT", [
            "Attack roll: d20 + Control + Perception vs enemy Magical Defense.",
            "Natural 20 = critical hit (double damage).",
            "Natural 1  = fumble (miss + lose 3 extra mana).",
            "Mana regenerates +2 per turn.",
            "You get 1 action per turn: cast a spell, use an item, or flee.",
            "Using a potion in combat costs your turn.",
        ]),
        ("SPELLS", [
            "Flipendo    (5 mana)  — cheap damage + weakens enemy",
            "Expelliarmus(10 mana) — disarms enemy (they lose a turn)",
            "Protego     (8 mana)  — reduces next incoming damage by 60%",
            "Incendio    (18 mana) — heavy damage + burn over 3 turns",
            "Episkey     (12 mana) — heals you",
            "",
            "More spells unlock in future years.",
        ]),
        ("WIN STREAK", [
            "Consecutive wins (without resting, losing, or fleeing) boost XP and Galleons.",
            "Each win adds +15%, up to +75% at 5+ wins.",
            "Resting or losing resets your streak.",
        ]),
        ("HOUSES", [
            "Gryffindor — +1 Brawn, +1 Willpower. Below 20% HP: +3 dmg, +2 to hit.",
            "Hufflepuff — +1 Willpower, +1 Presence. +2 max HP per new species killed.",
            "Ravenclaw  — +1 Intellect, +1 Perception. +1 token every 4-win streak.",
            "Slytherin  — +1 Power, +1 Control. -20% shop buys, +10% sells.",
        ]),
        ("TIPS", [
            "Rest only when you need to — it resets your win streak.",
            "Fight enemies at or above your level for more XP.",
            "Manage mana: don't blow it all on Incendio early.",
            "Protego before a big enemy turn can save your life.",
            "Check the shops after every couple of fights.",
        ]),
    ]

    print()
    print("═" * 60)
    print("  HOW TO PLAY — A WIZARD'S GUIDE")
    print("═" * 60)
    for title, lines in sections:
        print()
        print(f"  ── {title} ──")
        for line in lines:
            print(f"    {line}")
    print()
    print("═" * 60)
    pause()

def show_recent_actions(player):
    """Show the last 5 battles."""
    print()
    print("═" * 60)
    print("  RECENT BATTLES")
    print("═" * 60)

    if not player.battle_log:
        print("  No battles fought yet.")
        print("═" * 60)
        pause()
        return

    # Show the last 5 (most recent first)
    recent = list(reversed(player.battle_log[-5:]))

    for i, entry in enumerate(recent, start=1):
        enemy   = entry["enemy"]
        result  = entry["result"].upper()
        turns   = entry["turns"]
        xp      = entry.get("xp", 0)
        gold    = entry.get("gold", 0)
        tokens  = entry.get("tokens", 0)

        turn_str = f"{turns} turn" + ("s" if turns != 1 else "")
        rewards = "—"
        if result == "WIN":
            parts = []
            if xp:
                parts.append(f"+{xp} XP")
            if gold:
                parts.append(f"+{gold} G")
            if tokens:
                parts.append(f"+{tokens} T")
            rewards = "  ".join(parts) if parts else "—"

        print(f"  {i}. {enemy:<24} {result:<6} {turn_str:<10} {rewards}")

    print("═" * 60)
    pause()

BOSS_GAUNTLET = ["aragog", "voldemort"]

def boss_gate_available(player):
    """True if the player is at Year 1 boss trigger and hasn't beaten them."""
    if player.year != 1:
        return False
    if not player.at_year_finale_level():
        return False
    for boss_key in BOSS_GAUNTLET:
        if boss_key not in player.bosses_defeated:
            return True
    return False


def boss_gauntlet_flow(player):
    """Fight both bosses in sequence. No retreat."""
    print()
    print("═" * 60)
    print("  ⚠  THE YEAR'S FINAL TRIAL")
    print("═" * 60)
    print()
    print("  The school year has ended. Two dark forces await you.")
    print("  There is no retreat. Defeat means starting over.")
    print()
    print("  Boss 1: Aragog (Forbidden Forest)")
    print("  Boss 2: Lord Voldemort (Chamber of Secrets)")
    print()
    choice = prompt("  Face your destiny? (y/n) > ").lower()
    if choice not in ("y", "yes"):
        print("  You step back. But the darkness will wait.")
        return

    rng = random.Random()
    for boss_key in BOSS_GAUNTLET:
        if boss_key in player.bosses_defeated:
            continue

        # ---- Heal between bosses (except first) ----
        if player.bosses_defeated:
            print()
            print("  You catch your breath before the next fight...")
            player.full_restore()

        boss = Enemy(boss_key)
        boss_data = ENEMIES[boss_key]
        print()
        print("═" * 60)
        print(f"  ⚠  BOSS BATTLE: {boss_data['name']}")
        print("═" * 60)
        print(f"    Level {boss.level}   HP {boss.max_hp}   "
              f"MD {boss.md}   PD {boss.pd}")
        if boss_data.get("hint"):
            print()
            print(f"    ⚠ {boss_data['hint']}")
        print()

        result = run_battle(player, boss, rng=rng, auto=False, verbose=True)

        if result["result"] == "lose":
            print()
            print("  You have been defeated. Return when you are stronger.")
            pause()
            return

        # Boss beaten
        player.bosses_defeated.append(boss_key)
        save_game(player)
        print()
        print(f"  ★ {boss_data['name']} has fallen!")
        pause()

    # All bosses done
    year_complete(player)


def year_complete(player):
    """Celebration + year transition."""
    print()
    print("═" * 60)
    print("  ★  YEAR 1 COMPLETE  ★")
    print("═" * 60)
    print()
    print(f"  Congratulations, {player.name} of {HOUSES[player.house]['name']}.")
    print()
    print(f"  Kills recorded:    {len(player.discovered_enemies)} species")
    print(f"  Gold earned:       {player.galleons} G")
    print(f"  Spells known:      {len(player.known_spells)}")
    print(f"  Wand bond:         {player.bond_name()}")
    print()
    pause("  Press Enter to begin Year 2. ")

    summary = player.advance_year()

    print()
    print("═" * 60)
    print(f"  ★  YEAR {summary['new_year']} BEGINS  ★")
    print("═" * 60)
    print()
    print(f"  +{summary['attr_points_gained']} Attribute Points")
    for attr, val in summary["house_attrs"].items():
        print(f"  +1 {attr.title()} (house blessing) — now {val}")
    print(f"  New attribute cap: {summary['new_attr_cap']}")
    print(f"  New spell cap:     {summary['new_spell_cap']}")
    print()
    print("  New areas unlocked. New challenges await.")
    print()
    pause()

def print_banner():
    print()
    print("═" * 60)
    print("   HOGWARTS: A WIZARD'S JOURNEY")
    print("   A text-based RPG of magic, duels, and dark creatures.")
    print("═" * 60)
    print()


def title_flow():
    while True:
        print("  1. New Game")
        print("  2. Load Game")
        print("  0. Quit")
        print()
        choice = prompt()
        if choice == "0":
            print("\n  Goodbye, wizard.")
            return None
        if choice == "1":
            return create_character()
        if choice == "2":
            p = try_load()
            if p is not None:
                return p


# ============================================================
# CHARACTER CREATION
# ============================================================

def create_character():
    print()
    name = prompt("  What is your name? > ") or "Student"
    print()

    # ---- Sorting ----
    house_key = sorting_hat()

    # ---- Wand wood ----
    wood_keys = list(WAND_WOOD_BONUS.keys())
    print("  Choose your wand wood:")
    for i, wood in enumerate(wood_keys, start=1):
        attr = WAND_WOOD_BONUS[wood]
        print(f"    {i}. {wood.title():<10}  (+1 {attr.title()})")
    print()
    wood = choose_from(wood_keys, "wood")

    # ---- Wand core ----
    print()
    print("  Choose your wand core:")
    core_keys = list(WAND_CORES.keys())
    for i, core in enumerate(core_keys, start=1):
        info = WAND_CORES[core]
        print(f"    {i}. {info['name']:<22}  {describe_core(info)}")
    print()
    core = choose_from(core_keys, "core")

    # ---- Build player ----
    p = Player(name=name, wand_wood=wood, wand_core=core)
    p.house = house_key
    add_to_inventory(p, "potions", "healing_draught", 1)

    print()
    print(f"  Welcome, {name} of {HOUSES[house_key]['name']}.")
    print(f"  Your wand: {wood.title()} + {WAND_CORES[core]['name']}")
    print(f"  You start with Flipendo and 2 Spell Tokens.")
    print()
    choice = prompt("  Would you like a quick guide? (y/n) > ").lower()
    if choice in ("y", "yes"):
        show_help()
    else:
        pause()
    return p


def sorting_hat():
    """Random house, with one reroll."""
    rng = random.Random()
    house_key = rng.choice(HOUSE_KEYS)
    _display_sorting(house_key)

    choice = prompt("  Accept? (y/n) > ").lower()
    if choice in ("y", "yes", ""):
        return house_key

    # Reroll
    print()
    print("  The Sorting Hat grumbles... and tries again.")
    print()
    house_key = rng.choice(HOUSE_KEYS)
    _display_sorting(house_key)
    pause("  Press Enter to accept. ")
    return house_key


def _display_sorting(house_key):
    h = HOUSES[house_key]
    print("  The Sorting Hat is placed on your head...")
    print()
    print(f"  ═══ {h['name'].upper()} ═══")
    print(f"  {h['colors']}")
    print(f"  \"{h['motto']}\"")
    print()
    attr_bonus = h["attr_bonus"]
    bonus_str = ", ".join(f"+1 {a.title()}" for a in attr_bonus)
    print(f"  Attributes: {bonus_str}")
    print(f"  Passive: {_describe_passive(house_key)}")
    print()


def _describe_passive(house_key):
    return {
        "gryffindor": "Below 20% HP: +3 spell damage, +2 attack rolls",
        "hufflepuff": "+2 max HP for each new enemy species defeated",
        "ravenclaw": "+1 Spell Token every 4th consecutive win",
        "slytherin": "-20% shop buy prices, +10% sell prices",
    }[house_key]


def describe_core(info):
    parts = []
    if info.get("bonus_mana"):
        parts.append(f"+{info['bonus_mana']} Mana")
    if info.get("hp_regen"):
        parts.append(f"+{info['hp_regen']} HP/turn")
    if info.get("damage_modifier"):
        parts.append(f"{info['damage_modifier']:+d} Damage")
    if info.get("accuracy_modifier"):
        parts.append(f"{info['accuracy_modifier']:+d} Accuracy")
    if info.get("execute_bonus"):
        parts.append(f"+{info['execute_bonus']} dmg vs wounded")
    return ", ".join(parts)


def choose_from(keys, label):
    while True:
        c = prompt()
        if c.isdigit():
            idx = int(c) - 1
            if 0 <= idx < len(keys):
                return keys[idx]
        print(f"  Invalid {label}. Try again.")


# ============================================================
# SAVE / LOAD
# ============================================================

def save_game(player, path=SAVE_FILE):
    data = {
        "name":           player.name,
        "level":          player.level,
        "xp":             player.xp,
        "attr_points":    player.attr_points,
        "base_attrs":     player.base_attrs,
        "wand":           player.wand,
        "wand_upgrades":  player.wand_upgrades,
        "galleons":       player.galleons,
        "spell_tokens":   player.spell_tokens,
        "known_spells":   player.known_spells,
        "inventory":      player.inventory,
        "equipped":       player.equipped,
        "current_hp":     player.current_hp,
        "current_mana":   player.current_mana,
        "house":          player.house,
        "win_streak":     player.win_streak,
        "discovered_enemies": player.discovered_enemies,
        "battle_log":     player.battle_log,
        "year":             player.year,
        "bosses_defeated":  player.bosses_defeated,
        "year_bonuses":     player.year_bonuses,
    }
    Path(path).write_text(json.dumps(data, indent=2))


def try_load(path=SAVE_FILE):
    if not Path(path).exists():
        print("\n  No save file found.")
        return None
    try:
        data = json.loads(Path(path).read_text())
    except Exception as e:
        print(f"\n  Failed to load save: {e}")
        return None

    p = Player(
        name=data.get("name", "Student"),
        wand_wood=data.get("wand", {}).get("wood", "holly"),
        wand_core=data.get("wand", {}).get("core", "phoenix_feather"),
    )
    p.level         = data.get("level", 1)
    p.xp            = data.get("xp", 0)
    p.attr_points   = data.get("attr_points", 0)
    p.base_attrs    = data.get("base_attrs", p.base_attrs)
    p.wand          = data.get("wand", p.wand)
    p.wand_upgrades = data.get("wand_upgrades", [])
    p.galleons      = data.get("galleons", 0)
    p.spell_tokens  = data.get("spell_tokens", 0)
    p.known_spells  = data.get("known_spells", ["flipendo"])
    p.inventory     = data.get("inventory", {"potions": {}, "items": {}, "gear": {}})
    p.equipped      = data.get("equipped", {slot: None for slot in GEAR_SLOTS})
    p.current_hp    = data.get("current_hp", p.max_hp())
    p.current_mana  = data.get("current_mana", p.max_mana())
    p.house              = data.get("house")
    p.win_streak         = data.get("win_streak", 0)
    p.discovered_enemies = data.get("discovered_enemies", [])
    p.battle_log = data.get("battle_log", [])
    p.year             = data.get("year", 1)
    p.bosses_defeated  = data.get("bosses_defeated", [])
    p.year_bonuses     = data.get("year_bonuses", {})

    print(f"\n  Loaded {p.name} (Level {p.level}).")
    return p


# ============================================================
# MAIN HUB
# ============================================================

def main_hub(player):
    while True:
        print()
        print("═" * 56)
        house_str = f" of {HOUSES[player.house]['name']}" if player.house else ""
        print(f"  HUB — {player.name}{house_str}, Year {player.year}, Level {player.level}")
        print(f"  HP {player.current_hp}/{player.max_hp()}   "
              f"Mana {player.current_mana}/{player.max_mana()}   "
              f"Galleons {player.galleons}   Tokens {player.spell_tokens}")
        if player.win_streak > 0:
            mult = player.streak_multiplier()
            print(f"  Win Streak: {player.win_streak}   (XP/Gold ×{mult:.2f})")

        if player.attr_points:
            print(f"  ⚠ {player.attr_points} unspent Attribute Point(s)")
        boss_ready = boss_gate_available(player)

        print("  1. Fight")
        print("  2. Shops")
        print("  3. Inventory & Gear")
        print("  4. Character Sheet")
        print("  5. Rest (full restore)")
        print("  6. Help / How to Play")
        print("  7. Recent Actions")
        print("  8. Save Game")
        if boss_ready:
            print("  ⚠  9. FACE YOUR DESTINY")
        print("  0. Save & Quit")
        print("═" * 56)

        if boss_ready:
            print("  The final trial awaits. Type 9 when ready.")

        choice = prompt("  > ")
        if choice == "0":
            save_game(player)
            print("\n  Saved. Goodbye, wizard.")
            return
        elif choice == "1":
            fight_flow(player)
        elif choice == "2":
            shops_flow(player)
        elif choice == "3":
            inventory_flow(player)
        elif choice == "4":
            print()
            print(player.sheet())
            pause()
        elif choice == "5":
            rest(player)
        elif choice == "6":
            show_help()
        elif choice == "7":
            show_recent_actions(player)
        elif choice == "8":
            save_game(player)
            print("  Game saved.")
        elif choice == "9" and boss_ready:
            boss_gauntlet_flow(player)


# ============================================================
# FIGHT
# ============================================================

def fight_flow(player):
    while True:
        print()
        print("═" * 56)
        print("  CHOOSE A TIER")
        print("═" * 56)

        available = []
        for tier in TIER_ORDER:
            need = TIER_MIN_LEVEL[tier]
            count = len(ENEMIES_BY_TIER.get(tier, []))
            if player.level < need:
                print(f"    -   {TIER_DISPLAY[tier]:<12}  (need Level {need})")
            else:
                available.append(tier)
                idx = len(available)
                print(f"    {idx}.  {TIER_DISPLAY[tier]:<12}  ({count} enemies)")
        print("    0.  Back")
        print("═" * 56)

        choice = prompt("  > ")
        if choice == "0":
            return
        if not choice.isdigit():
            continue
        idx = int(choice) - 1
        if not (0 <= idx < len(available)):
            continue

        tier = available[idx]
        encounter(player, tier)

        # Post-battle: check for unspent points, death, etc.
        if player.attr_points > 0:
            prompt_spend_points(player)
        if not player.is_alive():
            print()
            print("  You wake up in the hospital wing, sore but alive.")
            player.current_hp = player.max_hp()
            player.current_mana = player.max_mana()
            pause()


def encounter(player, tier):
    rng = random.Random()
    key = random_enemy_key(tier, rng)
    if key is None:
        print("  No enemies in this tier.")
        return

    enemy = Enemy(key)
    print()
    print(f"  You encounter: {enemy.name}")
    print(f"    Level {enemy.level}   HP {enemy.max_hp}   "
          f"MD {enemy.md}   PD {enemy.pd}")
    hint = ENEMIES.get(key, {}).get("hint")
    if hint:
        print()
        print(f"    ⚠ {hint}")
    print()
    print("    1. Fight")
    print("    2. Back away")

    choice = prompt("  > ")
    if choice != "1":
        print("  You back away.")
        return

    run_battle(player, enemy, rng=rng, auto=False, verbose=True)
    pause()


# ============================================================
# SPEND ATTRIBUTE POINTS
# ============================================================

def prompt_spend_points(player):
    while player.attr_points > 0:
        print()
        print(f"  You have {player.attr_points} unspent Attribute Point(s).")
        print("  Spend on which attribute?")
        for i, attr in enumerate(ATTRIBUTES, start=1):
            cur = player.base_attrs[attr]
            print(f"    {i}. {ATTR_DISPLAY[attr]:<12} (current {cur})")
        print("    0. Save for later")

        choice = prompt("  > ")
        if choice == "0":
            return
        if not choice.isdigit():
            continue
        idx = int(choice) - 1
        if not (0 <= idx < len(ATTRIBUTES)):
            continue
        attr = ATTRIBUTES[idx]
        if player.spend_attr_point(attr):
            print(f"  {ATTR_DISPLAY[attr]} increased.")


# ============================================================
# SHOPS
# ============================================================

def shops_flow(player):
    while True:
        print()
        print("═" * 56)
        print(f"  SHOPS   (Galleons {player.galleons}   Tokens {player.spell_tokens})")
        print("═" * 56)
        print("  1. Spell Token Shop")
        print("  2. Apothecary")
        print("  3. Wand Smith")
        print("  0. Back")

        choice = prompt("  > ")
        if choice == "0":
            return
        elif choice == "1":
            menu_spell_shop(player)
        elif choice == "2":
            menu_apothecary(player)
        elif choice == "3":
            menu_wand_shop(player)


# ============================================================
# INVENTORY & GEAR
# ============================================================

def inventory_flow(player):
    while True:
        print()
        print(show_equipped(player))
        print(show_inventory(player))
        print("  1. Use Potion")
        print("  2. Equip Gear")
        print("  3. Unequip Gear")
        print("  0. Back")

        choice = prompt("  > ")
        if choice == "0":
            return
        elif choice == "1":
            use_potion_menu(player)
        elif choice == "2":
            equip_menu(player)
        elif choice == "3":
            unequip_menu(player)


def use_potion_menu(player):
    potions = player.inventory.get("potions", {})
    if not potions:
        print("  You have no potions.")
        return
    keys = list(potions.keys())
    print()
    print("  Which potion?")
    for i, k in enumerate(keys, start=1):
        p = POTIONS[k]
        print(f"    {i}. {p['name']:<26} x{potions[k]}")
    print("    0. Back")

    choice = prompt("  > ")
    if choice == "0" or not choice.isdigit():
        return
    idx = int(choice) - 1
    if not (0 <= idx < len(keys)):
        return

    ok, msgs = use_potion(player, keys[idx])
    for m in msgs:
        print("  " + m)


def equip_menu(player):
    gear = player.inventory.get("gear", {})
    if not gear:
        print("  You have no gear in your bag.")
        return
    keys = list(gear.keys())
    print()
    print("  Which gear to equip?")
    for i, k in enumerate(keys, start=1):
        g = GEAR[k]
        print(f"    {i}. {g['name']:<24} ({g['slot']})  — {g['description']}")
    print("    0. Back")

    choice = prompt("  > ")
    if choice == "0" or not choice.isdigit():
        return
    idx = int(choice) - 1
    if not (0 <= idx < len(keys)):
        return

    ok, msg = equip_gear(player, keys[idx])
    print("  " + msg)


def unequip_menu(player):
    equipped = [(slot, player.equipped[slot])
                for slot in GEAR_SLOTS
                if player.equipped.get(slot)]
    if not equipped:
        print("  Nothing is equipped.")
        return

    print()
    print("  Which slot to empty?")
    for i, (slot, k) in enumerate(equipped, start=1):
        print(f"    {i}. {slot:<8} — {GEAR[k]['name']}")
    print("    0. Back")

    choice = prompt("  > ")
    if choice == "0" or not choice.isdigit():
        return
    idx = int(choice) - 1
    if not (0 <= idx < len(equipped)):
        return

    slot, _ = equipped[idx]
    ok, msg = unequip_gear(player, slot)
    print("  " + msg)


# ============================================================
# REST
# ============================================================

def rest(player):
    if (player.current_hp == player.max_hp()
            and player.current_mana == player.max_mana()):
        print("  You are already at full strength.")
        return

    if player.win_streak > 0:
        print(f"  Resting will reset your {player.win_streak}-win streak.")
        choice = prompt("  Rest anyway? (y/n) > ").lower()
        if choice not in ("y", "yes", ""):
            print("  You push on.")
            return

    player.full_restore()
    player.reset_streak()
    print("  You rest by the fire and recover fully. Win streak reset.")


# ============================================================
# MAIN
# ============================================================

def main():
    print_banner()
    player = title_flow()
    if player is None:
        return
    main_hub(player)


if __name__ == "__main__":
    main()

main_hub()