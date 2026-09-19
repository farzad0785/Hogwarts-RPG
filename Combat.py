"""
combat.py — the battle loop.

Ties Player + Enemy + Spells together into a full turn-based fight.

Flow:
1. Roll initiative
2. Loop:
   a. Whoever is faster acts first
   b. Player turn: choose spell / item / flee, resolve, tick end-of-turn
   c. Enemy turn: check skip, choose attack, resolve, tick end-of-turn
   d. Check win/lose
3. Award rewards on victory
"""

import random

from Data import SPELLS, ENEMIES, HOUSES
from Spells import cast_spell, apply_incoming_damage
from Player import Player


# ============================================================
# CONSTANTS
# ============================================================

MAX_TURNS = 50   # safety valve — draws end here


# ============================================================
# PUBLIC ENTRY
# ============================================================

def run_battle(player, enemy, rng=None, auto=False, verbose=True):
    """
    Run one full battle.

    player : Player instance
    enemy  : Enemy instance
    rng    : random.Random (optional)
    auto   : if True, player auto-casts the first affordable spell (for testing)
    verbose: print turn-by-turn log

    Returns dict: {
        "result": "win" | "lose" | "flee" | "draw",
        "turns": int,
        "rewards": {...} or None,
    }
    """
    if rng is None:
        rng = random.Random()

    log = _make_logger(verbose)

    # ---------------------------------------------------------
    # INITIATIVE
    # ---------------------------------------------------------
    player_init = rng.randint(1, 20) + player.initiative_bonus()
    enemy_init = rng.randint(1, 20) + enemy.initiative_bonus

    player_first = player_init >= enemy_init

    log("")
    log(f"═══ BATTLE: {player.name} vs {enemy.name} ═══")
    log(f"  Initiative — {player.name}: {player_init}  |  {enemy.name}: {enemy_init}")
    log(f"  {player.name} goes first." if player_first else f"  {enemy.name} goes first.")
    log("")

    turns = 0
    while turns < MAX_TURNS:
        turns += 1
        log(f"───── Turn {turns} ─────")

        # ---- Player turn ----
        if not player_first:
            # Enemy goes first this round
            result = _enemy_turn(player, enemy, rng, log)
            if result == "player_dead":
                return _lose(player, enemy, turns, log)
            if result == "enemy_dead":
                return _win(player, enemy, turns, rng, log)

        result = _player_turn(player, enemy, rng, log, auto=auto)
        if result == "flee":
            return _flee(player, enemy, turns, log)
        if result == "enemy_dead":
            return _win(player, enemy, turns, rng, log)
        if result == "player_dead":
            return _lose(player, enemy, turns, log)

        # ---- Enemy turn ----
        if player_first:
            result = _enemy_turn(player, enemy, rng, log)
            if result == "player_dead":
                return _lose(player, enemy, turns, log)
            if result == "enemy_dead":
                return _win(player, enemy, turns, rng, log)

        # Flip who goes first next round (based on initiative each round, simple version)
        # Actually: keep the same order. Remove this if you want alternating. For now, keep.
        # player_first stays the same.

    return _draw(player, enemy, turns, log)


# ============================================================
# PLAYER TURN
# ============================================================

def _player_turn(player, enemy, rng, log, auto=False):
    """Returns one of: 'ok', 'flee', 'enemy_dead', 'player_dead', 'item_used'"""

    if player.has_status("disarmed") or player.has_status("stunned") or player.has_status("petrified"):
        skip_name = (
            "disarmed" if player.has_status("disarmed")
            else "stunned" if player.has_status("stunned")
            else "petrified"
        )
        log(f"  {player.name} is {skip_name} — loses the turn!")
        player.remove_status(skip_name)
        _player_end_of_turn(player, log)
        return "ok"

    if auto:
        spell_key = _auto_pick_spell(player, enemy)
        if spell_key is None:
            log(f"  {player.name} has no castable spell — skips.")
            _player_end_of_turn(player, log)
            return "ok"
    else:
        action = _prompt_player_action(player, enemy, rng, log)

        if action == "flee":
            if getattr(enemy, "is_boss", False):
                log("  You cannot flee from this fight!")
                _player_end_of_turn(player, log)
                return "ok"
            return "flee"

        if action is None:
            _player_end_of_turn(player, log)
            return "ok"

        if action == "item_used":
            # An item was used inside the prompt — consumes the turn
            if not enemy.is_alive():
                _handle_enemy_death(player, enemy, log)
                log(f"  ★ {enemy.name} is defeated!")
                return "enemy_dead"
            _player_end_of_turn(player, log)
            if not player.is_alive():
                return "player_dead"
            return "ok"

        spell_key = action

    # ---- Cast spell ----
    result = cast_spell(player, spell_key, enemy, rng=rng)
    for line in result["messages"]:
        log("  " + line)

    if not enemy.is_alive():
        _handle_enemy_death(player, enemy, log)
        log(f"  ★ {enemy.name} is defeated!")
        return "enemy_dead"

    _player_end_of_turn(player, log)

    if not player.is_alive():
        return "player_dead"

    return "ok"


def _player_end_of_turn(player, log):
    hp_gained, mana_gained, dot = player.end_of_turn()
    notes = []
    if hp_gained > 0:
        notes.append(f"+{hp_gained} HP")
    if mana_gained > 0:
        notes.append(f"+{mana_gained} mana")
    if dot > 0:
        notes.append(f"-{dot} HP (status)")
    if notes:
        log(f"  [end of turn] {', '.join(notes)}")
    if not player.is_alive():
        log(f"  ★ {player.name} has fallen!")


# ============================================================
# ENEMY TURN
# ============================================================

def _enemy_turn(player, enemy, rng, log):
    """Returns one of: 'ok', 'enemy_dead', 'player_dead'"""

    if not enemy.is_alive():
        return "enemy_dead"

    # ---- Lazy skip (Flobberworm) ----
    for spec in enemy.specials:
        if spec.get("name") == "lazy":
            if rng.random() < spec.get("skip_chance", 0.5):
                log(f"  {enemy.name} dozes off and skips the turn.")
                _enemy_end_of_turn(enemy, log)
                return "ok"

    # ---- Skip turn ----
    if enemy.should_skip_turn():
        skip_name = next(
            (s["name"] for s in enemy.statuses
             if s["name"] in ("disarmed", "stunned", "petrified")),
            "stunned",
        )
        log(f"  {enemy.name} is {skip_name} — loses the turn!")
        enemy.remove_status(skip_name)
        _enemy_end_of_turn(enemy, log)
        return "ok"

    # ---- Specials ----
    action_taken = _try_enemy_special(player, enemy, rng, log)
    if action_taken:
        _enemy_end_of_turn(enemy, log)
        if not player.is_alive():
            return "player_dead"
        return "ok"

    # ---- Pick attack ----
    attack = enemy.choose_attack()
    if attack is None:
        log(f"  {enemy.name} hesitates...")
        _enemy_end_of_turn(enemy, log)
        return "ok"

    # ---- Resolve ----
    _resolve_enemy_attack(player, enemy, attack, rng, log)

    _enemy_end_of_turn(enemy, log)

    if not player.is_alive():
        return "player_dead"
    if not enemy.is_alive():
        return "enemy_dead"

    return "ok"


def _enemy_end_of_turn(enemy, log):
    mana_gained, dot = enemy.end_of_turn()
    notes = []
    if mana_gained > 0:
        notes.append(f"+{mana_gained} mana")
    if dot > 0:
        notes.append(f"-{dot} HP (status)")
    if notes:
        log(f"  [{enemy.name} end of turn] {', '.join(notes)}")
    if not enemy.is_alive():
        log(f"  ★ {enemy.name} succumbs to their wounds!")


# ============================================================
# ENEMY ATTACK RESOLUTION
# ============================================================

def _resolve_enemy_attack(player, enemy, attack, rng, log):
    attack_name = attack.get("name", "?")

    # Track uses
    enemy.mark_attack_used(attack_name)

    # --- Self-heal attack (Hufflepuff Rival's Episkey) ---
    if attack.get("vs") == "self":
        mana_cost = attack.get("mana_cost", 0)
        if mana_cost and not enemy.spend_mana(mana_cost):
            log(f"  {enemy.name} lacks mana for {attack_name} — skips.")
            return
        before = enemy.current_hp
        enemy.heal(attack.get("heal", 0))
        gained = enemy.current_hp - before
        log(f"  {enemy.name} casts {attack_name} and heals {gained} HP.")
        return

    # --- Spend mana ---
    mana_cost = attack.get("mana_cost", 0)
    if mana_cost:
        if not enemy.spend_mana(mana_cost):
            log(f"  {enemy.name} lacks mana for {attack_name} — skips.")
            return

    # --- Attack roll ---
    nat = rng.randint(1, 20)
    penalty = enemy.get_attack_penalty()
    bonus = attack.get("to_hit_bonus", 0) + penalty

    vs = attack.get("vs", "pd")
    defense = player.physical_defense() if vs == "pd" else player.magical_defense()
    attack_total = nat + bonus

    if nat == 1:
        log(f"  {enemy.name} attacks with {attack_name} — NATURAL 1! Misses badly.")
        return
    if nat != 20 and attack_total < defense:
        log(f"  {enemy.name} attacks with {attack_name} — "
            f"d20({nat}) + {bonus} = {attack_total} vs {defense} → MISS")
        return

    # --- Save-or-suck (Basilisk gaze, Mandrake scream) ---
    save = attack.get("save")
    if save:
        dc = save["dc"]
        attr = save["attr"]
        attr_val = player.get_effective_attr(attr)
        save_roll = rng.randint(1, 20) + attr_val
        if save_roll >= dc:
            log(f"  {enemy.name} uses {attack_name} — "
                f"{player.name} saves! (d20 + {attr_val} = {save_roll} vs {dc})")
            return
        else:
            log(f"  {enemy.name} uses {attack_name} — "
                f"{player.name} fails to save! (d20 + {attr_val} = {save_roll} vs {dc})")

    # --- Damage ---
    damage = attack.get("damage", 0)
    damage += enemy.threshold_damage_bonus()

    crit = (nat == 20)
    if crit:
        damage *= 2

    final_damage, note = apply_incoming_damage(player, damage)
    if note:
        log("  " + note)

    player.take_damage(final_damage)

    crit_tag = "  ★ CRIT!" if crit else ""
    if final_damage > 0:
        log(f"  {enemy.name} hits with {attack_name} — "
            f"d20({nat}) + {bonus} = {attack_total} vs {defense} → "
            f"{final_damage} damage{crit_tag}")
    else:
        log(f"  {enemy.name} uses {attack_name}.")

    # --- Steal gold (Niffler) ---
    if "steal_gold" in attack:
        amount = min(attack["steal_gold"], player.galleons)
        if amount > 0:
            player.galleons -= amount
            log(f"  → {enemy.name} snatches {amount} Galleons!")
        else:
            log(f"  → {enemy.name} finds nothing to steal.")

    # --- Mana drain (Chizpurfle) ---
    if "mana_drain" in attack:
        amount = min(attack["mana_drain"], player.current_mana)
        if amount > 0:
            player.current_mana -= amount
            log(f"  → {enemy.name} drains {amount} mana!")

    # --- Apply effect ---
    effect = attack.get("effect")
    if effect:
        name = effect.get("name")
        chance = effect.get("chance", 1.0)
        if rng.random() < chance:
            data = {}
            if "damage" in effect:
                data["damage"] = effect["damage"]
            if "amount" in effect:
                data["amount"] = effect["amount"]
            duration = effect.get("duration")
            player.add_status(name, data=data, duration=duration)
            log(f"  → {player.name} is {name}!")

    # --- Execute (Avada Kedavra) ---
    execute_threshold = attack.get("execute_threshold")
    if execute_threshold and player.current_hp > 0:
        if player.current_hp / player.max_hp() < execute_threshold:
            player.current_hp = 0
            log(f"  ★ {enemy.name}'s {attack_name} EXECUTES {player.name}!")


# ============================================================
# ENEMY SPECIALS
# ============================================================

def _try_enemy_special(player, enemy, rng, log):
    """Returns True if a special was used (skipping the normal attack)."""

    # ---- Hinkypunk: Lure ----
    if enemy.special_available("lure"):
        spec = next(s for s in enemy.specials if s["name"] == "lure")
        enemy.mark_special_used("lure")
        dc = spec["dc"]
        will = player.get_effective_attr("willpower")
        save = rng.randint(1, 20) + will
        if save >= dc:
            log(f"  {enemy.name} tries to lure {player.name} — "
                f"saved! (d20 + {will} = {save} vs {dc})")
        else:
            player.add_status("stunned", duration=1)
            log(f"  {enemy.name} LURES {player.name}! "
                f"d20 + {will} = {save} vs {dc} → stunned!")
        return True

    # ---- Acromantula: Web Shot ----
    if enemy.special_available("web_shot"):
        spec = next(s for s in enemy.specials if s["name"] == "web_shot")
        enemy.mark_special_used("web_shot")
        penalty = spec.get("agility_penalty", -2)
        dur = spec.get("duration", 2)
        player.add_status("weakened", data={"amount": penalty}, duration=dur)
        log(f"  {enemy.name} shoots webbing! {player.name} is slowed ({penalty} Agility for {dur}).")
        return True

    # ---- Steadfast (Hufflepuff Rival) ----
    if enemy.special_available("steadfast") and enemy.hp_pct() < 0.30:
        spec = next(s for s in enemy.specials if s["name"] == "steadfast")
        enemy.mark_special_used("steadfast")
        heal = spec.get("heal", 0)
        enemy.heal(heal)
        log(f"  ★ {enemy.name} rallies! (+{heal} HP)")
        return True

    # ---- Dark Lord's Will (Voldemort) ----
    if enemy.special_available("dark_lords_will") and enemy.hp_pct() < 0.5:
        spec = next(s for s in enemy.specials if s["name"] == "dark_lords_will")
        enemy.mark_special_used("dark_lords_will")
        heal = spec.get("heal", 0)
        enemy.heal(heal)
        log(f"  ★ {enemy.name} draws on dark power! (+{heal} HP)")
        return True

    # ---- Brood Mother (Aragog) — placeholder until multi-enemy combat ----
    for spec in enemy.specials:
        if spec.get("name") != "brood_mother":
            continue
        for thresh in spec.get("thresholds", []):
            key = f"brood_mother_{thresh}"
            if enemy.hp_pct() < thresh and key not in enemy.used_specials:
                enemy.mark_special_used(key)
                log(f"  ★ {enemy.name} spawns a Hatchling! (full summon coming later)")
                return True

    # ---- Death Eater: Dark Mark ----
    if enemy.special_available("dark_mark") and enemy.hp_pct() < 0.5:
        spec = next(s for s in enemy.specials if s["name"] == "dark_mark")
        enemy.mark_special_used("dark_mark")
        log(f"  ★ {enemy.name} summons an ally with the Dark Mark!")
        # NOTE: summoning not fully implemented yet.
        # For now: heal enemy to 50% as a stand-in. Real summon comes later.
        enemy.heal(int(enemy.max_hp * 0.25))
        log(f"  (Summon placeholder: {enemy.name} recovers some HP)")
        return True

    # ---- Dementor: Fear Aura (passive, every turn) ----
    if any(s.get("name") == "fear_aura" for s in enemy.specials):
        spec = next(s for s in enemy.specials if s["name"] == "fear_aura")
        dc = spec["dc"]
        will = player.get_effective_attr("willpower")
        save = rng.randint(1, 20) + will
        if save < dc:
            player.current_mana = max(0, player.current_mana - spec["mana_drain"])
            player.add_status("weakened", data={"amount": spec["penalty"]}, duration=1)
            log(f"  {enemy.name}'s Fear Aura grips {player.name}! "
                f"(-{spec['mana_drain']} mana, {spec['penalty']} to rolls)")
        else:
            log(f"  {enemy.name}'s Fear Aura washes over {player.name} — resisted.")
        # Fear aura does not skip the attack; return False
        return False

    return False


# ============================================================
# OUTCOMES
# ============================================================

def _handle_enemy_death(player, enemy, log):
    """Trigger on-death specials (Erumpent explosion)."""
    for spec in getattr(enemy, "specials", []):
        if spec.get("name") == "explosive_death":
            dmg = spec.get("damage", 0)
            if dmg > 0:
                player.take_damage(dmg)
                log(f"  ★ {enemy.name} explodes! {player.name} takes {dmg} damage.")

def _win(player, enemy, turns, rng, log):
    rewards = enemy.roll_rewards(rng)

    # ---- Win streak multiplier ----
    mult = player.streak_multiplier()
    xp_gain = int(rewards["xp"] * mult)
    gold_gain = int(rewards["galleons"] * mult)

    log("")
    log(f"═══ VICTORY ═══")
    log(f"  {enemy.name} defeated in {turns} turns.")

    if mult > 1.0 and not enemy.no_streak:
        log(f"  Win streak bonus: ×{mult:.2f}")

    # ---- Apply rewards ----
    player.gain_xp(xp_gain)
    player.add_galleons(gold_gain)
    player.add_spell_tokens(rewards["tokens"] + rewards["rare_tokens"])

    # Training Dummy and similar "practice" enemies don't count toward bond
    if enemy.no_streak:
        bond_up = False
    else:
        bond_up = player.record_battle_won()

    log(f"  +{xp_gain} XP")
    log(f"  +{gold_gain} Galleons")
    if rewards["tokens"]:
        log(f"  +{rewards['tokens']} Spell Token(s)")
    if rewards["rare_tokens"]:
        log(f"  +{rewards['rare_tokens']} RARE Token(s)")
    if bond_up:
        log(f"  ★ WAND BOND UP! Now Bond {player.bond_level()} ({player.bond_name()})")

    # ---- Hufflepuff: new species discovery ----
    is_new_species = player.discover_enemy(enemy.key)
    if is_new_species and player.house == "hufflepuff":
        hp_bonus = HOUSES["hufflepuff"]["passive_data"]["hp_per_species"]
        log(f"  ★ Hufflepuff: new species discovered! +{hp_bonus} max HP.")
        player.heal(hp_bonus)

    # ---- Record streak (skip for Training Dummy and similar) ----
    bonus_tokens = 0
    if not enemy.no_streak:
        bonus_tokens, msg = player.record_win()
        if msg:
            log(f"  ★ {msg}")

    # ---- Log the battle ----
    player.record_battle(
        enemy_name=enemy.name,
        result="win",
        turns=turns,
        xp=xp_gain,
        gold=gold_gain,
        tokens=rewards["tokens"] + rewards["rare_tokens"] + bonus_tokens,
    )

    return {
        "result": "win",
        "turns": turns,
        "rewards": {
            "xp": xp_gain,
            "galleons": gold_gain,
            "tokens": rewards["tokens"],
            "rare_tokens": rewards["rare_tokens"],
        },
        "bond_up": bond_up,
    }


def _lose(player, enemy, turns, log):
    log("")
    log(f"═══ DEFEAT ═══")
    log(f"  {player.name} falls after {turns} turns.")

    is_boss = getattr(enemy, "is_boss", False)
    if is_boss:
        # Harsher penalty for boss fights
        lost = int(player.galleons * 0.50)
        player.galleons -= lost
        player.reset_streak()
        log(f"  BOSS DEFEAT — harsher penalty!")
        log(f"  Lose {lost} Galleons (50%) and your win streak.")
        log(f"  You wake in the hospital wing. The boss awaits another attempt.")
    else:
        lost = int(player.galleons * 0.25)
        player.galleons -= lost
        player.reset_streak()
        log(f"  Lose {lost} Galleons and your win streak. Wake up in the hospital wing.")

    player.record_battle(
        enemy_name=enemy.name,
        result="lose",
        turns=turns,
    )

    return {
        "result": "lose",
        "turns": turns,
        "rewards": None,
    }


def _flee(player, enemy, turns, log):
    log(f"  {player.name} flees the battle. Win streak reset.")
    player.reset_streak()

    player.record_battle(
        enemy_name=enemy.name,
        result="flee",
        turns=turns,
    )

    return {
        "result": "flee",
        "turns": turns,
        "rewards": None,
    }


def _draw(player, enemy, turns, log):
    log(f"  Battle drags on — both sides retreat. (Draw after {turns} turns)")

    player.record_battle(
        enemy_name=enemy.name,
        result="draw",
        turns=turns,
    )

    return {
        "result": "draw",
        "turns": turns,
        "rewards": None,
    }


# ============================================================
# AI HELPERS
# ============================================================

def _auto_pick_spell(player, enemy):
    """For auto-mode testing: pick the strongest affordable known spell."""
    best = None
    best_score = -1
    for key in player.known_spells:
        cost = player.get_spell_mana_cost(key)
        if player.current_mana < cost:
            continue
        spell = SPELLS[key]
        # Simple preference: Episkey when hurt, else highest base damage
        if key == "episkey" and player.current_hp < player.max_hp() * 0.4:
            return "episkey"
        score = spell["base"]
        if score > best_score:
            best_score = score
            best = key
    if best is None and "flipendo" in player.known_spells:
        return "flipendo"
    return best


# ============================================================
# INTERACTIVE INPUT (used when auto=False)
# ============================================================

def _prompt_player_action(player, enemy, rng, log):
    """
    Show menu, read input.
    Returns: spell_key (str) | "flee" | "item_used" | None
    """
    while True:
        log("")
        log(f"  {player.name}: HP {player.current_hp}/{player.max_hp()}  "
            f"Mana {player.current_mana}/{player.max_mana()}")
        log(f"  {enemy.name}: HP {enemy.current_hp}/{enemy.max_hp}")
        if enemy.statuses:
            log(f"  {enemy.status_line()}")
        log("")
        log("  Choose an action:")

        options = []
        for i, key in enumerate(player.known_spells, start=1):
            spell = SPELLS[key]
            cost = player.get_spell_mana_cost(key)
            affordable = "" if player.current_mana >= cost else "  (not enough mana)"
            log(f"    {i}. {spell['name']:<14} ({cost} mana){affordable}")
            options.append(key)

        item_count = _total_consumables(player)
        item_label = f"Items ({item_count})" if item_count else "Items (empty)"

        log(f"    I. {item_label}")
        log(f"    F. Flee")
        log(f"    ?. Spell details")
        log(f"    0. Pass")

        try:
            choice = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None

        if choice == "?":
            _show_spell_help(player, log)
            continue

        if choice == "i":
            result = _item_menu(player, enemy, rng, log)
            if result == "item_used":
                return "item_used"
            # otherwise, loop back
            continue

        if choice in ("f", "flee"):
            return "flee"

        if choice == "0":
            return None

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]

def _total_consumables(player):
    p = sum(player.inventory.get("potions", {}).values())
    i = sum(player.inventory.get("items", {}).values())
    return p + i


def _item_menu(player, enemy, rng, log):
    """
    Show potions + combat items. If player picks one, use it and return "item_used".
    Otherwise return None (loop back to main menu).
    """
    from Items import use_potion, use_combat_item
    from Data import POTIONS, COMBAT_ITEMS

    potions = player.inventory.get("potions", {})
    items = player.inventory.get("items", {})

    if not potions and not items:
        log("  You have no items.")
        input("  Press Enter to return. ")
        return None

    log("")
    log("  ═══ USE AN ITEM ═══")
    entries = []  # (category, key, label)

    if potions:
        log("  Potions:")
        for k, count in potions.items():
            name = POTIONS[k]["name"]
            desc = POTIONS[k]["description"]
            log(f"    {len(entries) + 1}. {name:<26} x{count}  — {desc}")
            entries.append(("potions", k))

    if items:
        log("  Combat Items:")
        for k, count in items.items():
            name = COMBAT_ITEMS[k]["name"]
            desc = COMBAT_ITEMS[k]["description"]
            log(f"    {len(entries) + 1}. {name:<26} x{count}  — {desc}")
            entries.append(("items", k))

    log("    0. Back")

    try:
        choice = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if choice == "0" or not choice.isdigit():
        return None

    idx = int(choice) - 1
    if not (0 <= idx < len(entries)):
        return None

    category, key = entries[idx]

    if category == "potions":
        ok, msgs = use_potion(player, key)
    else:
        ok, msgs = use_combat_item(player, key, enemy, rng)

    for m in msgs:
        log("  " + m)

    if not ok:
        return None

    # Turn consumed
    return "item_used"

def _show_spell_help(player, log):
    """Display details for each known spell."""
    log("")
    log("  ═══ SPELL DETAILS ═══")
    for key in player.known_spells:
        spell = SPELLS[key]
        cost = player.get_spell_mana_cost(key)

        # Compute current damage / heal preview
        scaling = 0
        for attr in spell.get("scaling", []):
            scaling += player.get_effective_attr(attr)

        if spell["type"] == "support":
            preview = f"heals ~{spell['base'] + scaling} HP"
        elif spell["type"] == "defense":
            preview = "blocks/reduces damage"
        else:
            dmg = spell["base"] + scaling
            if hasattr(player, "spell_damage_bonus"):
                dmg += player.spell_damage_bonus()
            preview = f"~{dmg} damage"

        log("")
        log(f"  {spell['name']}  ({cost} mana)")
        log(f"    {spell['description']}")
        log(f"    Effect:  {preview}")

        # Additional effect
        effect = spell.get("effect")
        if effect:
            name = effect.get("name")
            if name == "burn":
                log(f"    On hit:  Burn {effect['damage']}/turn for {effect['duration']} turns")
            elif name == "disarmed":
                log(f"    On hit:  Enemy loses next turn")
            elif name == "weakened":
                log(f"    On hit:  Enemy {effect['amount']} to next attack")
            elif name == "shield":
                log(f"    Self:    Reduce incoming damage by {int(effect['reduce'] * 100)}%")

    log("")
    log("  ═════════════════════")
    input("  Press Enter to return to menu. ")
# ============================================================
# LOGGER
# ============================================================

def _make_logger(verbose):
    if verbose:
        def log(msg=""):
            print(msg)
        return log
    else:
        def log(msg=""):
            pass
        return log


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    import random
    from Player import Player
    from Enemy import Enemy

    print("=== AUTO BATTLE: Harry vs Slytherin Rival ===\n")
    p = Player(name="Harry", wand_wood="holly", wand_core="phoenix_feather")
    p.spell_tokens = 20
    p.learn_spell("expelliarmus")
    p.learn_spell("episkey")
    p.learn_spell("protego")
    p.learn_spell("incendio")

    e = Enemy("slytherin_rival")

    rng = random.Random(42)
    result = run_battle(p, e, rng=rng, auto=True, verbose=True)
    print(f"\nResult: {result['result']} in {result['turns']} turns.")

    print()
    print("=== AUTO BATTLE: Harry vs Mountain Troll (should lose at Lv1) ===\n")
    p2 = Player(name="Harry", wand_wood="holly", wand_core="phoenix_feather")
    p2.spell_tokens = 20
    p2.learn_spell("expelliarmus")
    p2.learn_spell("episkey")
    p2.learn_spell("protego")
    p2.learn_spell("incendio")

    e2 = Enemy("mountain_troll")
    rng2 = random.Random(7)
    result2 = run_battle(p2, e2, rng=rng2, auto=True, verbose=True)
    print(f"\nResult: {result2['result']} in {result2['turns']} turns.")