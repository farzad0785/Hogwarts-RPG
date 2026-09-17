"""
shop.py — the three shops + selling.

Shops:
1. Spell Token Shop — spend Spell Tokens to learn spells
2. Apothecary       — spend Galleons on potions, combat items, gear
3. Wand Smith       — spend Galleons on permanent wand upgrades

Selling:
- Sell potions / items / gear for 50% of buy price.
- Wand upgrades cannot be sold.
"""

from Data import (
    SPELLS, POTIONS, COMBAT_ITEMS, GEAR, WAND_UPGRADES,
    GEAR_SLOTS,
    HOUSES,
)
from Items import add_to_inventory, remove_from_inventory, inventory_count


SELL_RATE = 0.5

def _buy_multiplier(player):
    """Slytherin: -20% buy prices."""
    if player.house == "slytherin":
        return HOUSES["slytherin"]["passive_data"]["buy_multiplier"]
    return 1.0


def _sell_multiplier(player):
    """Slytherin: +10% sell prices."""
    if player.house == "slytherin":
        return HOUSES["slytherin"]["passive_data"]["sell_multiplier"]
    return 1.0

# ============================================================
# CORE TRANSACTIONS (no menus)
# ============================================================

def buy_item(player, category, key):
    """
    Buy a potion, combat item, or gear with Galleons.
    Returns (success, message).
    """
    table = _table_for(category)
    if table is None:
        return False, f"Unknown category: {category}"
    if key not in table:
        return False, f"Unknown item: {key}"

    item = table[key]
    cost = int(item["cost"] * _buy_multiplier(player))

    if player.galleons < cost:
        return False, f"Not enough Galleons (need {cost}, have {player.galleons})."

    # Try to add to inventory first (stack limits)
    ok, add_msg = add_to_inventory(player, category, key, 1)
    if not ok:
        return False, add_msg

    player.galleons -= cost
    return True, f"Bought {item['name']} for {cost} Galleons."


def sell_item(player, category, key, amount=1):
    """
    Sell potions / items / gear for 50% of buy price.
    Returns (success, message).
    """
    table = _table_for(category)
    if table is None:
        return False, f"Unknown category: {category}"
    if key not in table:
        return False, f"Unknown item: {key}"

    have = inventory_count(player, category, key)
    if have < amount:
        return False, f"You only have {have} {table[key]['name']}."

    item = table[key]
    unit_price = int(item["cost"] * SELL_RATE * _sell_multiplier(player))
    total = unit_price * amount

    remove_from_inventory(player, category, key, amount)
    player.galleons += total
    return True, f"Sold {amount}x {item['name']} for {total} Galleons."


def learn_spell(player, spell_key):
    """
    Spend Spell Tokens to learn a spell.
    Returns (success, message).
    """
    if spell_key not in SPELLS:
        return False, f"Unknown spell: {spell_key}"
    return player.learn_spell(spell_key)


def buy_wand_upgrade(player, upgrade_key):
    """
    Buy a permanent wand upgrade with Galleons.
    Returns (success, message).
    """
    if upgrade_key not in WAND_UPGRADES:
        return False, f"Unknown wand upgrade: {upgrade_key}"

    if upgrade_key in player.wand_upgrades:
        return False, f"{WAND_UPGRADES[upgrade_key]['name']} already owned."

    up = WAND_UPGRADES[upgrade_key]
    cost = int(up["cost"] * _buy_multiplier(player))

    if player.galleons < cost:
        return False, f"Not enough Galleons (need {cost}, have {player.galleons})."

    player.galleons -= cost
    player.wand_upgrades.append(upgrade_key)
    player._clamp_resources()
    return True, f"Installed {up['name']} for {cost} Galleons."


# ============================================================
# HELPERS
# ============================================================

def _table_for(category):
    return {
        "potions": POTIONS,
        "items": COMBAT_ITEMS,
        "gear": GEAR,
    }.get(category)


def _sellable_items(player):
    """Return list of (category, key, count) for everything sellable."""
    rows = []
    for cat in ("potions", "items", "gear"):
        for key, count in player.inventory.get(cat, {}).items():
            rows.append((cat, key, count))
    return rows


def _find_category(key):
    if key in POTIONS:
        return "potions"
    if key in COMBAT_ITEMS:
        return "items"
    if key in GEAR:
        return "gear"
    return None


# ============================================================
# INTERACTIVE MENUS
# ============================================================

def menu_spell_shop(player, input_func=input):
    """Spell Token Shop."""
    while True:
        print()
        print("━" * 50)
        print(f"  SPELL TOKEN SHOP              Tokens: {player.spell_tokens}")
        print("━" * 50)

        # Build list of learnable (not yet known) spells
        learnable = []
        for key, spell in SPELLS.items():
            if player.knows_spell(key):
                continue
            learnable.append(key)

        if not learnable:
            print("  You have learned every available spell.")
            print("━" * 50)
            input_func("  Press Enter to leave. ")
            return

        for i, key in enumerate(learnable, start=1):
            spell = SPELLS[key]
            cost = spell["token_cost"]
            tag = "" if player.spell_tokens >= cost else "  (not enough tokens)"
            print(f"  {i}. {spell['name']:<16} {cost} tokens{tag}")
        print("  0. Leave")
        print("━" * 50)

        choice = input_func("  > ").strip()

        if choice == "0":
            return
        if not choice.isdigit():
            continue
        idx = int(choice) - 1
        if not (0 <= idx < len(learnable)):
            continue

        key = learnable[idx]
        ok, msg = learn_spell(player, key)
        print(f"  {msg}")


def menu_apothecary(player, input_func=input):
    """Apothecary — buy potions, items, gear; sell anything."""
    while True:
        print()
        print("━" * 50)
        if player.house == "slytherin":
            print("  (Slytherin: -20% buy, +10% sell)")
        print(f"  APOTHECARY                    Galleons: {player.galleons}")
        print("━" * 50)
        print("  1. Buy Potions")
        print("  2. Buy Combat Items")
        print("  3. Buy Gear")
        print("  4. Sell Items")
        print("  0. Leave")
        print("━" * 50)

        choice = input_func("  > ").strip()

        if choice == "0":
            return
        if choice == "1":
            _buy_menu(player, "potions", input_func)
        elif choice == "2":
            _buy_menu(player, "items", input_func)
        elif choice == "3":
            _buy_menu(player, "gear", input_func)
        elif choice == "4":
            _sell_menu(player, input_func)


def menu_wand_shop(player, input_func=input):
    """Wand Smith — permanent upgrades."""
    while True:
        print()
        print("━" * 50)
        if player.house == "slytherin":
            print("  (Slytherin: -20% buy, +10% sell)")
        print(f"  WAND SMITH                    Galleons: {player.galleons}")
        print("━" * 50)

        available = []
        for key, up in WAND_UPGRADES.items():
            if key in player.wand_upgrades:
                continue
            available.append(key)

        if not available:
            print("  Your wand is fully upgraded.")
            print("━" * 50)
            input_func("  Press Enter to leave. ")
            return

        for i, key in enumerate(available, start=1):
            up = WAND_UPGRADES[key]
            tag = "" if player.galleons >= up["cost"] else "  (need more gold)"
            print(f"  {i}. {up['name']:<22} {up['cost']:>4} G  — {up['description']}{tag}")
        print("  0. Leave")
        print("━" * 50)

        choice = input_func("  > ").strip()

        if choice == "0":
            return
        if not choice.isdigit():
            continue
        idx = int(choice) - 1
        if not (0 <= idx < len(available)):
            continue

        key = available[idx]
        ok, msg = buy_wand_upgrade(player, key)
        print(f"  {msg}")


# ============================================================
# SUB-MENUS
# ============================================================

def _buy_menu(player, category, input_func):
    table = _table_for(category)
    keys = list(table.keys())

    while True:
        print()
        print("━" * 50)
        if player.house == "slytherin":
            print("  (Slytherin: -20% buy, +10% sell)")
        label = {"potions": "POTIONS", "items": "COMBAT ITEMS", "gear": "GEAR"}[category]
        print(f"  BUY {label}                   Galleons: {player.galleons}")
        print("━" * 50)
        for i, key in enumerate(keys, start=1):
            item = table[key]
            tag = "" if player.galleons >= item["cost"] else "  (need more gold)"
            print(f"  {i}. {item['name']:<26} {item['cost']:>4} G  — {item['description']}{tag}")
        print("  0. Back")
        print("━" * 50)

        choice = input_func("  > ").strip()
        if choice == "0":
            return
        if not choice.isdigit():
            continue
        idx = int(choice) - 1
        if not (0 <= idx < len(keys)):
            continue

        key = keys[idx]
        ok, msg = buy_item(player, category, key)
        print(f"  {msg}")


def _sell_menu(player, input_func):
    while True:
        rows = _sellable_items(player)
        print()
        print("━" * 50)
        if player.house == "slytherin":
            print("  (Slytherin: -20% buy, +10% sell)")
        print(f"  SELL                          Galleons: {player.galleons}")
        print("━" * 50)

        if not rows:
            print("  You have nothing to sell.")
            print("━" * 50)
            input_func("  Press Enter to go back. ")
            return

        for i, (cat, key, count) in enumerate(rows, start=1):
            item = _table_for(cat)[key]
            unit = int(item["cost"] * SELL_RATE * _sell_multiplier(player))
            print(f"  {i}. {item['name']:<26} x{count}  ({unit} G each)")
        print("  0. Back")
        print("━" * 50)

        choice = input_func("  > ").strip()
        if choice == "0":
            return
        if not choice.isdigit():
            continue
        idx = int(choice) - 1
        if not (0 <= idx < len(rows)):
            continue

        cat, key, count = rows[idx]
        ok, msg = sell_item(player, cat, key, amount=1)
        print(f"  {msg}")


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    from Player import Player

    print("=== Shop Self-Test ===\n")

    p = Player(name="Harry", wand_wood="holly", wand_core="phoenix_feather")

    # ---- Learn spells ----
    print("--- Learning spells ---")
    p.spell_tokens = 20
    for key in ["expelliarmus", "episkey", "protego", "incendio"]:
        ok, msg = learn_spell(p, key)
        print(f"  {msg}")
    print(f"  Tokens left: {p.spell_tokens}, Known: {p.known_spells}")

    # ---- Buy items ----
    print("\n--- Buying items ---")
    p.galleons = 100
    purchases = [
        ("potions", "healing_draught"),
        ("potions", "mana_elixir"),
        ("items", "chinese_cabbage"),
        ("gear", "student_robes"),
    ]
    for cat, key in purchases:
        ok, msg = buy_item(p, cat, key)
        print(f"  {msg}")
    print(f"  Galleons left: {p.galleons}")
    print(f"  Inventory: {p.inventory}")

    # ---- Buy wand upgrades ----
    print("\n--- Buying wand upgrades ---")
    for key in ["wand_polish", "core_reinforcement"]:
        ok, msg = buy_wand_upgrade(p, key)
        print(f"  {msg}")
    print(f"  Galleons left: {p.galleons}")
    print(f"  Spell Accuracy bonus: {p.spell_attack_bonus()}")
    print(f"  Max Mana: {p.max_mana()}")

    # ---- Sell ----
    print("\n--- Selling ---")
    ok, msg = sell_item(p, "potions", "healing_draught")
    print(f"  {msg}")
    print(f"  Galleons after sale: {p.galleons}")

    # ---- Not enough gold ----
    print("\n--- Testing edge cases ---")
    p.galleons = 5
    ok, msg = buy_item(p, "gear", "lucky_charm")
    print(f"  {msg}")

    ok, msg = buy_wand_upgrade(p, "wand_mastery_1")
    print(f"  {msg}")

    ok, msg = buy_wand_upgrade(p, "wand_polish")   # already owned
    print(f"  {msg}")

    ok, msg = sell_item(p, "potions", "healing_draught", amount=10)
    print(f"  {msg}")