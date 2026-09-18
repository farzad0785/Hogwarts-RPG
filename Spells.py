"""
spells.py — spell casting and resolution.

Responsibilities:
- Roll attack (d20 + player.spell_attack_bonus vs target MD)
- Compute damage (base + scaling + wand bonus, crit, weakness, resistances)
- Apply status effects (burn, disarmed, weakened, shield)
- Handle support (Episkey heals self) and defense (Protego shields self)
- Handle nat 20 (double damage) and nat 1 (miss + 3 extra mana)

Combat.py calls `cast_spell()` and displays the result.
"""

import random

from Data import SPELLS


# ============================================================
# SPELL ELEMENTS
# ============================================================
# Used to apply enemy weaknesses / resistances.

SPELL_ELEMENTS = {
    "flipendo": "physical",
    "expelliarmus": "magical",
    "incendio": "fire",
    "protego": None,
    "episkey": None,
}


# ============================================================
# RESULT BUILDER
# ============================================================

def _new_result(spell_key):
    spell = SPELLS[spell_key]
    return {
        "spell_key": spell_key,
        "spell_name": spell["name"],
        "spell_type": spell["type"],
        "mana_spent": 0,
        "roll": None,               # natural d20
        "attack_total": None,       # d20 + bonus
        "target_defense": None,
        "hit": False,
        "crit": False,
        "fumble": False,
        "damage": 0,
        "healing": 0,
        "effects": [],              # list of status names applied
        "messages": [],             # display lines
        "extra": {},                # spell-specific stuff
    }


# ============================================================
# HELPERS
# ============================================================

def _scaling_bonus(caster, spell):
    """Sum effective attribute values named in spell['scaling']."""
    total = 0
    for attr in spell.get("scaling", []):
        total += caster.get_effective_attr(attr)
    return total


def _is_player(caster):
    """Duck-typing: Player has `spell_attack_bonus`, Enemy does not."""
    return hasattr(caster, "spell_attack_bonus")


def _get_attack_bonus(caster):
    """Player has richer spell bonus logic. Enemies use attack's to_hit_bonus."""
    if _is_player(caster):
        return caster.spell_attack_bonus()
    return 0  # not used for player-style spells cast by enemies


def _target_defense(target, spell):
    """Which defense does this spell target?"""
    if spell["type"] in ("attack", "control"):
        return target.md  # magical defense
    return None


def _apply_status(target, status_name, data=None, duration=None):
    """Apply a status effect to player or enemy."""
    if hasattr(target, "add_status"):
        target.add_status(status_name, duration=duration, data=data)


# ============================================================
# MAIN ENTRY
# ============================================================

def cast_spell(caster, spell_key, target, rng=None):
    """
    Cast a spell.

    caster : Player (or Enemy casting its own defined attacks — not supported here)
    spell_key : one of data.SPELLS keys
    target : Enemy (or Player, if it's Episkey/Protego — target = caster)
    rng : random.Random instance (optional)

    Returns a result dict (see _new_result).
    """
    if rng is None:
        rng = random

    if spell_key not in SPELLS:
        raise ValueError(f"Unknown spell: {spell_key}")

    spell = SPELLS[spell_key]
    result = _new_result(spell_key)
    result["spell_type"] = spell["type"]

    # ---------------------------------------------------------
    # MANA CHECK
    # ---------------------------------------------------------
    if _is_player(caster):
        cost = caster.get_spell_mana_cost(spell_key)
    else:
        cost = spell["mana"]

    # Support / defense spells target self; check before target's defense
    if spell["type"] in ("support", "defense"):
        target = caster

    if hasattr(caster, "current_mana"):
        if caster.current_mana < cost:
            result["messages"].append(
                f"Not enough mana to cast {spell['name']} (need {cost})."
            )
            return result
        caster.current_mana -= cost
        result["mana_spent"] = cost

    # ---------------------------------------------------------
    # DISPATCH BY TYPE
    # ---------------------------------------------------------
    if spell["type"] == "support":
        _resolve_support(caster, spell, result)
    elif spell["type"] == "defense":
        _resolve_defense(caster, spell, result)
    else:
        _resolve_offensive(caster, spell, spell_key, target, rng, result)

    return result


# ============================================================
# SUPPORT  (Episkey)
# ============================================================

def _resolve_support(caster, spell, result):
    base = spell["base"]
    scaling = _scaling_bonus(caster, spell)
    heal_amount = base + scaling

    before = caster.current_hp
    if hasattr(caster, "heal"):
        caster.heal(heal_amount)
    after = caster.current_hp
    actual = after - before

    result["healing"] = actual
    result["hit"] = True
    result["messages"].append(f"{caster.name} casts {spell['name']} and heals {actual} HP.")


# ============================================================
# DEFENSE  (Protego)
# ============================================================

def _resolve_defense(caster, spell, result):
    effect = spell.get("effect") or {}
    reduce_pct = effect.get("reduce", 0.60)
    duration = effect.get("duration", 1)

    _apply_status(caster, "shield", data={"reduce": reduce_pct}, duration=duration)

    result["hit"] = True
    result["effects"].append("shield")
    result["extra"]["reduce"] = reduce_pct
    result["messages"].append(
        f"{caster.name} casts {spell['name']} — incoming damage reduced by "
        f"{int(reduce_pct * 100)}% this turn."
    )


# ============================================================
# OFFENSIVE  (Flipendo, Expelliarmus, Incendio)
# ============================================================

def _resolve_offensive(caster, spell, spell_key, target, rng, result):
    # ---------------------------------------------------------
    # ATTACK ROLL
    # ---------------------------------------------------------
    nat = rng.randint(1, 20)
    attack_bonus = _get_attack_bonus(caster)
    attack_total = nat + attack_bonus
    defense = _target_defense(target, spell)

    result["roll"] = nat
    result["attack_total"] = attack_total
    result["target_defense"] = defense

    # Natural 1 — fumble
    if nat == 1:
        result["fumble"] = True
        if hasattr(caster, "current_mana"):
            caster.current_mana = max(0, caster.current_mana - 3)
        result["messages"].append(
            f"{caster.name} casts {spell['name']} — NATURAL 1! "
            f"The spell fizzles. (-3 extra mana)"
        )
        return

    # Natural 20 — crit
    is_crit = (nat == 20)

    # Hit or miss
    if not is_crit and attack_total < defense:
        result["messages"].append(
            f"{caster.name} casts {spell['name']} — "
            f"d20({nat}) + {attack_bonus} = {attack_total} vs {defense} → MISS"
        )
        return

    result["hit"] = True
    result["crit"] = is_crit

    # ---------------------------------------------------------
    # BASE DAMAGE
    # ---------------------------------------------------------
    base = spell["base"]
    scaling = _scaling_bonus(caster, spell)
    damage = base + scaling

    # Wand damage bonus (player only)
    target_hp_pct = 1.0
    if hasattr(target, "hp_pct"):
        target_hp_pct = target.hp_pct()

    if _is_player(caster) and hasattr(caster, "spell_damage_bonus"):
        damage += caster.spell_damage_bonus(target_hp_pct=target_hp_pct)

    # Crit doubles base + scaling (not the wand bonus; small design choice)
    if is_crit:
        damage = (base + scaling) * 2 + (
            caster.spell_damage_bonus(target_hp_pct=target_hp_pct)
            if _is_player(caster) and hasattr(caster, "spell_damage_bonus")
            else 0
        )

    # ---------------------------------------------------------
    # ENEMY RESISTANCES / WEAKNESSES
    # ---------------------------------------------------------
    element = SPELL_ELEMENTS.get(spell_key)
    multiplier = 1.0
    flat_reduction = 0

    if hasattr(target, "incoming_damage_multiplier"):
        multiplier = target.incoming_damage_multiplier(
            spell_type=spell["type"], element=element
        )
    if hasattr(target, "flat_damage_reduction"):
        flat_reduction = target.flat_damage_reduction(element=element)

    # Stubborn (Garden Gnome): half damage from a specific spell
    for spec in getattr(target, "specials", []):
        if spec.get("name") == "stubborn" and spec.get("resist_spell") == spell_key:
            multiplier *= spec.get("multiplier", 0.5)

    damage = int(damage * multiplier)
    damage -= flat_reduction
    damage = max(0, damage)

    # Extra dmg taken (Werewolf frenzy)
    if hasattr(target, "extra_damage_taken"):
        damage += target.extra_damage_taken()

    # ---------------------------------------------------------
    # APPLY DAMAGE
    # ---------------------------------------------------------
    before_hp = target.current_hp
    if hasattr(target, "take_damage"):
        target.take_damage(damage)
    after_hp = target.current_hp
    actual_damage = before_hp - after_hp

    result["damage"] = actual_damage

    # --- Reflect damage (Fire Crab's hot shell) ---
    if hasattr(target, "reflect_damage_amount"):
        reflect = target.reflect_damage_amount()
        if reflect > 0 and hasattr(caster, "take_damage"):
            caster.take_damage(reflect)
            result["messages"].append(
                f"  → {target.name}'s hot shell burns {caster.name} for {reflect} damage!"
            )
    # ---------------------------------------------------------
    # DISPLAY MESSAGE
    # ---------------------------------------------------------
    crit_tag = "  ★ CRITICAL HIT!" if is_crit else ""
    result["messages"].append(
        f"{caster.name} casts {spell['name']} — "
        f"d20({nat}) + {attack_bonus} = {attack_total} vs {defense} → "
        f"HIT for {actual_damage} damage{crit_tag}"
    )
    if multiplier != 1.0:
        result["messages"].append(
            f"  ({target.name} takes {int(multiplier * 100)}% damage from this spell)"
        )
    if flat_reduction:
        result["messages"].append(
            f"  ({target.name} shrugs off {flat_reduction} damage — thick hide)"
        )

    # ---------------------------------------------------------
    # APPLY SPELL EFFECT (burn, disarmed, weakened)
    # ---------------------------------------------------------
    effect = spell.get("effect")
    if effect:
        _apply_spell_effect(spell_key, effect, target, result)

    # ---------------------------------------------------------
    # LIFESTEAL (used by enemy spells, not player)
    # ---------------------------------------------------------
    lifesteal = spell.get("lifesteal")
    if lifesteal and hasattr(caster, "heal"):
        caster.heal(lifesteal)
        result["messages"].append(f"  (Drained {lifesteal} HP)")


# ============================================================
# SPELL EFFECT APPLICATION
# ============================================================

def _apply_spell_effect(spell_key, effect, target, result):
    name = effect.get("name")
    if not name:
        return

    if name == "burn":
        damage = effect.get("damage", 3)
        duration = effect.get("duration", 3)
        _apply_status(target, "burn", data={"damage": damage}, duration=duration)
        result["effects"].append("burn")
        result["messages"].append(f"  → {target.name} is burning! ({damage}/turn for {duration})")

    elif name == "disarmed":
        duration = effect.get("duration", 1)
        _apply_status(target, "disarmed", duration=duration)
        result["effects"].append("disarmed")
        result["messages"].append(f"  → {target.name} is disarmed — loses next turn!")

    elif name == "weakened":
        amount = effect.get("amount", -2)
        duration = effect.get("duration", 1)
        _apply_status(target, "weakened", data={"amount": amount}, duration=duration)
        result["effects"].append("weakened")
        result["messages"].append(f"  → {target.name} is weakened ({amount} to next attack)")


# ============================================================
# DAMAGE MITIGATION ON INCOMING HITS
# ============================================================

def apply_incoming_damage(target, raw_damage):
    """
    Called by combat when the PLAYER is about to take damage.
    Applies shield status if active.
    Returns (final_damage, note).
    """
    if not hasattr(target, "get_status"):
        return raw_damage, None

    shield = target.get_status("shield")
    if shield:
        reduce = shield.get("reduce", 0.60)
        final = int(raw_damage * (1 - reduce))
        note = f"  Protego absorbs {int(reduce * 100)}% — takes {final} instead of {raw_damage}"
        # Shield lasts one hit, then expires
        target.remove_status("shield")
        return final, note

    return raw_damage, None


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    import random
    from Player import Player
    from Enemy import Enemy

    rng = random.Random(7)

    print("=== Player vs Slytherin Rival (full example) ===\n")

    p = Player(name="Harry", wand_wood="holly", wand_core="phoenix_feather")
    e = Enemy("slytherin_rival")

    print(p.short_sheet() if hasattr(p, "short_sheet") else p.sheet())
    print()
    print(e.short_sheet())
    print()

    print("--- Cast Expelliarmus ---")
    result = cast_spell(p, "expelliarmus", e, rng=rng)
    for line in result["messages"]:
        print(line)
    print(f"  Enemy HP: {e.current_hp}/{e.max_hp}")
    print(f"  Player Mana: {p.current_mana}/{p.max_mana}")
    print()

    print("--- Cast Incendio ---")
    result = cast_spell(p, "incendio", e, rng=rng)
    for line in result["messages"]:
        print(line)
    print(f"  Enemy HP: {e.current_hp}/{e.max_hp}")
    print()

    print("--- Enemy takes burn tick (end of its turn) ---")
    mana, dot = e.end_of_turn()
    print(f"  Burn damage: {dot}, Enemy HP: {e.current_hp}")

    print()
    print("--- Cast Episkey on self ---")
    p.current_hp = 20
    result = cast_spell(p, "episkey", p, rng=rng)
    for line in result["messages"]:
        print(line)
    print(f"  Player HP: {p.current_hp}/{p.max_hp}")

    print()
    print("--- Cast Protego (shield) ---")
    result = cast_spell(p, "protego", p, rng=rng)
    for line in result["messages"]:
        print(line)

    print()
    print("--- Enemy hits player for 20, shield absorbs ---")
    final, note = apply_incoming_damage(p, 20)
    print(f"  Raw: 20  Final: {final}")
    if note:
        print(note)

    print()
    print("--- Natural 1 fumble test (reroll until nat 1) ---")
    e2 = Enemy("cornish_pixie")
    for seed in range(200):
        test_rng = random.Random(seed)
        r = cast_spell(p, "flipendo", e2, rng=test_rng)
        if r["fumble"]:
            print(f"  Seed {seed}: {r['messages'][0]}")
            break

    print()
    print("--- Natural 20 crit test ---")
    e3 = Enemy("mountain_troll")
    for seed in range(500):
        test_rng = random.Random(seed)
        r = cast_spell(p, "incendio", e3, rng=test_rng)
        if r["crit"]:
            print(f"  Seed {seed}: {r['messages'][0]}")
            break

