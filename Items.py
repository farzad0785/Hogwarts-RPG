"""
items.py — inventory, potions, combat items, and gear.

Responsibilities:
- Add / remove items from the player's inventory
- Use potions (heal, restore mana, cure, buff, resist)
- Use combat items (cabbage, dungbomb, etc.)
- Equip / unequip gear into 6 slots
- Display inventory and gear

Items are consumable. Gear is permanent until replaced.
"""

from Data import (
    POTIONS, COMBAT_ITEMS, GEAR, GEAR_SLOTS, INVENTORY_LIMITS,
)


# ============================================================
# INVENTORY MANAGEMENT
# ============================================================

def add_to_inventory(player, category, key, amount=1):
    """
    category: 'potions' | 'items' | 'gear'
    Returns (success, message).
    """
    if category not in ("potions", "items", "gear"):
        return False, f"Unknown category: {category}"

    table = _table_for(category)
    if key not in table:
        return False, f"Unknown {category[:-1]}: {key}"

    limit = _stack_limit(category)
    current = player.inventory[category].get(key, 0)
    new_total = current + amount

    if limit is not None and new_total > limit:
        can_add = max(0, limit - current)
        if can_add == 0:
            return False, f"{table[key]['name']} is at max stack ({limit})."
        player.inventory[category][key] = limit
        return True, f"Added {can_add} {table[key]['name']} (capped at {limit})."

    player.inventory[category][key] = new_total
    return True, f"Added {amount} {table[key]['name']}."


def remove_from_inventory(player, category, key, amount=1):
    """Returns (success, message)."""
    if category not in player.inventory:
        return False, f"Unknown category: {category}"

    current = player.inventory[category].get(key, 0)
    if current < amount:
        return False, f"Not enough {key} in inventory."

    remaining = current - amount
    if remaining == 0:
        del player.inventory[category][key]
    else:
        player.inventory[category][key] = remaining
    return True, f"Removed {amount}."


def inventory_count(player, category, key):
    return player.inventory.get(category, {}).get(key, 0)


def _table_for(category):
    return {
        "potions": POTIONS,
        "items": COMBAT_ITEMS,
        "gear": GEAR,
    }[category]


def _stack_limit(category):
    if category == "potions":
        return INVENTORY_LIMITS["potion_stack"]
    if category == "items":
        return INVENTORY_LIMITS["item_stack"]
    return None  # gear stacks are unlimited


# ============================================================
# POTIONS
# ============================================================

def use_potion(player, key, log=None):
    """
    Use a potion. Costs the player a turn in combat (caller handles that).

    Returns (success, list_of_message_lines).
    """
    if key not in POTIONS:
        return False, [f"Unknown potion: {key}"]

    if inventory_count(player, "potions", key) < 1:
        return False, [f"No {POTIONS[key]['name']} in inventory."]

    potion = POTIONS[key]
    effect = potion["effect"]
    messages = []

    # Consume it
    remove_from_inventory(player, "potions", key, 1)

    # Heal
    if "heal" in effect:
        before = player.current_hp
        player.heal(effect["heal"])
        gained = player.current_hp - before
        messages.append(f"{player.name} drinks {potion['name']} and heals {gained} HP.")

    # Restore mana
    if "restore_mana" in effect:
        before = player.current_mana
        player.restore_mana(effect["restore_mana"])
        gained = player.current_mana - before
        messages.append(f"{player.name} drinks {potion['name']} and restores {gained} mana.")

    # Cure statuses
    if "cure" in effect:
        removed = []
        for status in effect["cure"]:
            if player.has_status(status):
                player.remove_status(status)
                removed.append(status)
        if removed:
            messages.append(f"{player.name} is cured of: {', '.join(removed)}.")
        else:
            messages.append(f"{player.name} had nothing to cure.")

    # Buff (temp modifier)
    if "buff" in effect:
        b = effect["buff"]
        player.temp_mods.append({
            "attr": b["attr"],
            "amount": b["amount"],
            "duration": b["duration"],
            "source": potion["name"],
        })
        messages.append(
            f"{player.name} gains +{b['amount']} {b['attr'].title()} "
            f"for {b['duration']} turns."
        )

    # Resistance (as a status effect)
    if "resistance" in effect:
        r = effect["resistance"]
        player.add_status(
            "fire_resist",
            data={"element": r["element"], "multiplier": r["multiplier"]},
            duration=r["duration"],
        )
        messages.append(
            f"{player.name} is protected against {r['element']} "
            f"for {r['duration']} turns."
        )

    if log:
        for m in messages:
            log("  " + m)

    return True, messages


# ============================================================
# COMBAT ITEMS
# ============================================================

def use_combat_item(player, key, enemy, rng, log=None):
    """
    Use a combat item against an enemy. Costs the player a turn.

    Returns (success, list_of_message_lines).
    """
    if key not in COMBAT_ITEMS:
        return False, [f"Unknown item: {key}"]

    if inventory_count(player, "items", key) < 1:
        return False, [f"No {COMBAT_ITEMS[key]['name']} in inventory."]

    item = COMBAT_ITEMS[key]
    effect = item["effect"]
    messages = []

    # Consume it
    remove_from_inventory(player, "items", key, 1)

    # Damage
    if "damage" in effect:
        if effect.get("guaranteed_hit"):
            damage = effect["damage"]
            enemy.take_damage(damage)
            messages.append(
                f"{player.name} uses {item['name']} — {damage} damage (guaranteed hit)."
            )
        elif effect.get("ignores_defense"):
            damage = effect["damage"]
            enemy.take_damage(damage)
            messages.append(
                f"{player.name} uses {item['name']} — {damage} damage (ignores defense)."
            )
        else:
            damage = effect["damage"]
            enemy.take_damage(damage)
            messages.append(f"{player.name} uses {item['name']} — {damage} damage.")

    # Skip turn (chance-based)
    if "skip_turn_chance" in effect:
        if rng.random() < effect["skip_turn_chance"]:
            enemy.add_status("stunned", duration=1)
            messages.append(f"{enemy.name} is stunned!")
        else:
            messages.append(f"{item['name']} had no effect.")

    # Debuff
    if "debuff" in effect:
        d = effect["debuff"]
        enemy.add_status("weakened", data={"amount": d["amount"]}, duration=d["duration"])
        messages.append(
            f"{enemy.name} suffers {d['amount']} to next attack "
            f"for {d['duration']} turn(s)."
        )

    # Flee condition
    if "flee_below_pct" in effect:
        threshold = effect["flee_below_pct"]
        if enemy.hp_pct() < threshold:
            enemy.current_hp = 0
            enemy.slain = True
            messages.append(f"{enemy.name} flees the battle!")
        else:
            messages.append(f"{enemy.name} stands their ground.")

    if log:
        for m in messages:
            log("  " + m)

    return True, messages


# ============================================================
# GEAR
# ============================================================

def equip_gear(player, key):
    """
    Equip a piece of gear from inventory. Returns (success, message).
    """
    if key not in GEAR:
        return False, f"Unknown gear: {key}"

    if inventory_count(player, "gear", key) < 1:
        return False, f"No {GEAR[key]['name']} in inventory."

    gear = GEAR[key]
    slot = gear["slot"]

    # Unequip whatever is in that slot first (return to inventory)
    current = player.equipped.get(slot)
    if current is not None:
        add_to_inventory(player, "gear", current, 1)

    # Move from inventory to slot
    remove_from_inventory(player, "gear", key, 1)
    player.equipped[slot] = key

    # Recalculate HP/Mana since attributes may have changed
    player._clamp_resources()

    return True, f"Equipped {gear['name']} ({slot})."


def unequip_gear(player, slot):
    """
    Unequip gear from a slot. Returns (success, message).
    """
    if slot not in GEAR_SLOTS:
        return False, f"Unknown slot: {slot}"

    key = player.equipped.get(slot)
    if key is None:
        return False, f"Nothing equipped in {slot}."

    add_to_inventory(player, "gear", key, 1)
    player.equipped[slot] = None

    player._clamp_resources()

    return True, f"Unequipped {GEAR[key]['name']}."


# ============================================================
# DISPLAY
# ============================================================

def show_inventory(player):
    """Return a multi-line string of the player's inventory."""
    lines = []
    lines.append("━" * 50)
    lines.append("  INVENTORY")
    lines.append("━" * 50)

    lines.append("  POTIONS")
    if not player.inventory["potions"]:
        lines.append("    (empty)")
    else:
        for key, count in player.inventory["potions"].items():
            lines.append(f"    {POTIONS[key]['name']:<24} x{count}")

    lines.append("  COMBAT ITEMS")
    if not player.inventory["items"]:
        lines.append("    (empty)")
    else:
        for key, count in player.inventory["items"].items():
            lines.append(f"    {COMBAT_ITEMS[key]['name']:<24} x{count}")

    lines.append("  GEAR (unequipped)")
    if not player.inventory["gear"]:
        lines.append("    (empty)")
    else:
        for key, count in player.inventory["gear"].items():
            lines.append(f"    {GEAR[key]['name']:<24} x{count}")

    lines.append("━" * 50)
    return "\n".join(lines)


def show_equipped(player):
    """Return a multi-line string of the player's equipped gear."""
    lines = []
    lines.append("━" * 50)
    lines.append("  EQUIPPED GEAR")
    lines.append("━" * 50)

    # Wand is separate
    wood = player.wand["wood"].title()
    core = player.wand["core"].replace("_", " ").title()
    lines.append(f"    wand      : {wood} + {core}")

    for slot in GEAR_SLOTS:
        key = player.equipped.get(slot)
        if key is None:
            lines.append(f"    {slot:<10}: —")
        else:
            lines.append(f"    {slot:<10}: {GEAR[key]['name']}")

    lines.append("━" * 50)
    return "\n".join(lines)


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    from Player import Player
    from Enemy import Enemy
    import random

    print("=== Items Self-Test ===\n")

    p = Player(name="Harry", wand_wood="holly", wand_core="phoenix_feather")

    # Give some starting inventory
    add_to_inventory(p, "potions", "healing_draught", 3)
    add_to_inventory(p, "potions", "mana_elixir", 2)
    add_to_inventory(p, "items", "chinese_cabbage", 2)
    add_to_inventory(p, "gear", "student_robes", 1)
    add_to_inventory(p, "gear", "focusing_ring", 1)

    print(show_inventory(p))
    print()

    # Take damage and heal
    print("--- Take 20 damage, then use Healing Draught ---")
    p.take_damage(20)
    print(f"  HP before: {p.current_hp}")
    use_potion(p, "healing_draught")
    print(f"  HP after:  {p.current_hp}")
    print()

    # Equip gear
    print("--- Equip Student Robes ---")
    ok, msg = equip_gear(p, "student_robes")
    print(f"  {msg}")
    print(f"  Physical Defense: {p.physical_defense()}")
    print()

    print("--- Equip Focusing Ring ---")
    ok, msg = equip_gear(p, "focusing_ring")
    print(f"  {msg}")
    print(f"  Control (effective): {p.get_effective_attr('control')}")
    print()

    print(show_equipped(p))
    print()

    # Combat item
    print("--- Use Chinese Chomping Cabbage on a troll ---")

    e = Enemy("mountain_troll")
    rng = random.Random(1)
    print(f"  Troll HP before: {e.current_hp}")
    use_combat_item(p, "chinese_cabbage", e, rng)
    print(f"  Troll HP after:  {e.current_hp}")