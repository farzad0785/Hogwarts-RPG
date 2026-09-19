"""
combat.py — turn-based battle loop (multi-enemy).

Supports 1 or more enemies in a single battle.

Combatants act in initiative order:
    - Player has one initiative roll.
    - Each enemy has its own initiative roll.
    - Player goes before the enemies if player_init >= highest enemy init.
    - Otherwise, all enemies act first, then the player.
    - Summoned enemies join at the end of the enemy phase (act next round).

Targeting:
    - Offensive spells prompt the player to pick a target (auto-picks if only 1 enemy).
    - Support/defense spells auto-target self.
    - Combat items auto-target (pick enemy).

Summons:
    - Death Eater's Dark Mark spawns a Dark Wizard Apprentice at 50% HP.
    - Aragog's Brood Mother spawns Hatchlings at 50% and 25% HP.
    - Summoned enemies are appended to the enemy list.
"""

import random

from Data import SPELLS, ENEMIES, HOUSES
from Spells import cast_spell, apply_incoming_damage
from Enemy import Enemy


# ============================================================
# CONSTANTS
# ============================================================

MAX_TURNS = 50


# ============================================================
# PUBLIC ENTRY
# ============================================================

def run_battle(player, enemies, rng=None, auto=False, verbose=True):
    """
    Run one full battle against one or more enemies.

    player  : Player instance
    enemies : Enemy instance OR list of Enemy instances
    rng     : random.Random (optional)
    auto    : if True, player auto-casts (for testing)
    verbose : print turn-by-turn log

    Returns dict: {
        "result": "win" | "lose" | "flee" | "draw",
        "turns": int,
        "rewards": {...} or None,
    }
    """
    if rng is None:
        rng = random.Random()

    # ---- Normalize to list ----
    if not isinstance(enemies, list):
        enemies = [enemies]

    # ---- Assign labels for duplicates ----
    _label_enemies(enemies)

    log = _make_logger(verbose)

    # ---- Initiative ----
    player_init = rng.randint(1, 20) + player.initiative_bonus()
    enemy_inits = [rng.randint(1, 20) + e.initiative_bonus for e in enemies]
    top_enemy_init = max(enemy_inits) if enemy_inits else 0
    player_first = player_init >= top_enemy_init

    log("")
    if len(enemies) == 1:
        log(f"═══ BATTLE: {player.name} vs {enemies[0].label} ═══")
    else:
        log(f"═══ BATTLE: {player.name} vs {len(enemies)} enemies ═══")
        for e in enemies:
            log(f"    {e.label:<28} Lv {e.level}  HP {e.max_hp}")
    log(f"  Initiative — {player.name}: {player_init}  |  Top enemy: {top_enemy_init}")
    if player_first:
        log(f"  {player.name} goes first.")
    else:
        log(f"  Enemies go first.")
    log("")

    turns = 0
    while turns < MAX_TURNS:
        turns += 1
        log(f"───── Turn {turns} ─────")

        if player_first:
            # Player acts
            result = _player_turn(player, enemies, rng, log, auto=auto)
            if result == "flee":
                return _flee(player, enemies, turns, log)
            if result == "player_dead":
                return _lose(player, enemies, turns, log)
            if _all_dead(enemies):
                return _win(player, enemies, turns, rng, log)

            # Enemies act
            result = _enemies_turn(player, enemies, rng, log)
            if result == "player_dead":
                return _lose(player, enemies, turns, log)
            if result == "all_dead" or _all_dead(enemies):
                return _win(player, enemies, turns, rng, log)
        else:
            # Enemies act
            result = _enemies_turn(player, enemies, rng, log)
            if result == "player_dead":
                return _lose(player, enemies, turns, log)
            if result == "all_dead" or _all_dead(enemies):
                return _win(player, enemies, turns, rng, log)

            # Player acts
            result = _player_turn(player, enemies, rng, log, auto=auto)
            if result == "flee":
                return _flee(player, enemies, turns, log)
            if result == "player_dead":
                return _lose(player, enemies, turns, log)
            if _all_dead(enemies):
                return _win(player, enemies, turns, rng, log)

    return _draw(player, enemies, turns, log)


# ============================================================
# LABELS
# ============================================================

def _label_enemies(enemies):
    """Assign readable labels. Duplicates get #1, #2, etc."""
    counts = {}
    for e in enemies:
        counts[e.name] = counts.get(e.name, 0) + 1
    seen = {}
    for e in enemies:
        if counts[e.name] > 1:
            seen[e.name] = seen.get(e.name, 0) + 1
            e.label = f"{e.name} #{seen[e.name]}"
        else:
            e.label = e.name

# ============================================================
# HELPERS
# ============================================================

def _living(enemies):
    return [e for e in enemies if e.is_alive()]


def _all_dead(enemies):
    return all(not e.is_alive() for e in enemies)


# ============================================================
# PLAYER TURN
# ============================================================

def _player_turn(player, enemies, rng, log, auto=False):
    """Returns: 'ok', 'flee', 'player_dead'."""

    # ---- Skip turn ----
    if (player.has_status("disarmed")
            or player.has_status("stunned")
            or player.has_status("petrified")):
        skip_name = (
            "disarmed" if player.has_status("disarmed")
            else "stunned" if player.has_status("stunned")
            else "petrified"
        )
        log(f"  {player.name} is {skip_name} — loses the turn!")
        player.remove_status(skip_name)
        _player_end_of_turn(player, log)
        return "ok"

    # ---- Choose action ----
    if auto:
        spell_key = _auto_pick_spell(player, enemies)
        target = _auto_pick_target(enemies)
        if spell_key is None or target is None:
            log(f"  {player.name} hesitates.")
            _player_end_of_turn(player, log)
            return "ok"
    else:
        action = _prompt_player_action(player, enemies, rng, log)

        if action == "flee":
            if any(getattr(e, "is_boss", False) for e in enemies):
                log("  You cannot flee from this fight!")
                _player_end_of_turn(player, log)
                return "ok"
            return "flee"
        if action is None:
            _player_end_of_turn(player, log)
            return "ok"
        if action == "item_used":
            _player_end_of_turn(player, log)
            if not player.is_alive():
                return "player_dead"
            return "ok"

        # action is either a spell_key (single) or (spell_key, target) tuple
        if isinstance(action, tuple):
            spell_key, target = action
        else:
            # Fallback: pick first living enemy
            spell_key = action
            living = _living(enemies)
            target = living[0] if living else None
            if target is None:
                _player_end_of_turn(player, log)
                return "ok"

    # ---- Cast ----
    spell = SPELLS[spell_key]

    # Support / defense auto-target self
    if spell["type"] in ("support", "defense"):
        target = player

    result = cast_spell(player, spell_key, target, rng=rng)
    for line in result["messages"]:
        log("  " + line)

    # Check enemy deaths (could be multiple from AoE in future; single-target now)
    for enemy in enemies:
        if not enemy.is_alive() and not getattr(enemy, "_death_handled", False):
            enemy._death_handled = True
            _handle_enemy_death(player, enemy, log)

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
# ENEMIES TURN
# ============================================================

def _enemies_turn(player, enemies, rng, log):
    """Returns: 'ok', 'all_dead', 'player_dead'."""

    initial_count = len(enemies)
    for i in range(initial_count):
        if i >= len(enemies):
            break
        enemy = enemies[i]
        if not enemy.is_alive():
            continue

        _single_enemy_turn(player, enemy, enemies, rng, log)

        # DoT or self-damage may have killed the enemy during its turn
        if not enemy.is_alive() and not getattr(enemy, "_death_handled", False):
            enemy._death_handled = True
            _handle_enemy_death(player, enemy, log)

        if not player.is_alive():
            return "player_dead"
        if _all_dead(enemies):
            return "all_dead"

    return "ok"


def _single_enemy_turn(player, enemy, enemies, rng, log):
    # ---- Skip turn ----
    if enemy.should_skip_turn():
        skip_name = next(
            (s["name"] for s in enemy.statuses
             if s["name"] in ("disarmed", "stunned", "petrified")),
            "stunned",
        )
        log(f"  {enemy.label} is {skip_name} — loses the turn!")
        enemy.remove_status(skip_name)
        _enemy_end_of_turn(enemy, log)
        return

    # ---- Lazy skip (Flobberworm) ----
    for spec in enemy.specials:
        if spec.get("name") == "lazy":
            if rng.random() < spec.get("skip_chance", 0.5):
                log(f"  {enemy.label} dozes off and skips the turn.")
                _enemy_end_of_turn(enemy, log)
                return

    # ---- Specials (may summon) ----
    if _try_enemy_special(player, enemy, enemies, rng, log):
        _enemy_end_of_turn(enemy, log)
        return

    # ---- Normal attack ----
    attack = enemy.choose_attack()
    if attack is None:
        log(f"  {enemy.label} hesitates...")
        _enemy_end_of_turn(enemy, log)
        return

    _resolve_enemy_attack(player, enemy, attack, rng, log)
    _enemy_end_of_turn(enemy, log)


def _enemy_end_of_turn(enemy, log):
    mana_gained, dot = enemy.end_of_turn()
    notes = []
    if mana_gained > 0:
        notes.append(f"+{mana_gained} mana")
    if dot > 0:
        notes.append(f"-{dot} HP (status)")
    if notes:
        log(f"  [{enemy.label} end of turn] {', '.join(notes)}")
    if not enemy.is_alive():
        log(f"  ★ {enemy.label} succumbs to their wounds!")


# ============================================================
# ENEMY ATTACK RESOLUTION
# ============================================================

def _resolve_enemy_attack(player, enemy, attack, rng, log):
    attack_name = attack.get("name", "?")

    enemy.mark_attack_used(attack_name)

    # ---- Self-heal ----
    if attack.get("vs") == "self":
        mana_cost = attack.get("mana_cost", 0)
        if mana_cost and not enemy.spend_mana(mana_cost):
            log(f"  {enemy.label} lacks mana for {attack_name} — skips.")
            return
        before = enemy.current_hp
        enemy.heal(attack.get("heal", 0))
        gained = enemy.current_hp - before
        log(f"  {enemy.label} casts {attack_name} and heals {gained} HP.")
        return

    # ---- Mana cost ----
    mana_cost = attack.get("mana_cost", 0)
    if mana_cost:
        if not enemy.spend_mana(mana_cost):
            log(f"  {enemy.label} lacks mana for {attack_name} — skips.")
            return

    # ---- Roll ----
    nat = rng.randint(1, 20)
    penalty = enemy.get_attack_penalty()
    bonus = attack.get("to_hit_bonus", 0) + penalty

    vs = attack.get("vs", "pd")
    defense = player.physical_defense() if vs == "pd" else player.magical_defense()
    attack_total = nat + bonus

    if nat == 1:
        log(f"  {enemy.label} attacks with {attack_name} — NATURAL 1! Misses badly.")
        return
    if nat != 20 and attack_total < defense:
        log(f"  {enemy.label} attacks with {attack_name} — "
            f"d20({nat}) + {bonus} = {attack_total} vs {defense} → MISS")
        return

    # ---- Save-or-suck ----
    save = attack.get("save")
    if save:
        dc = save["dc"]
        attr = save["attr"]
        attr_val = player.get_effective_attr(attr)
        save_roll = rng.randint(1, 20) + attr_val
        if save_roll >= dc:
            log(f"  {enemy.label} uses {attack_name} — "
                f"{player.name} saves! (d20 + {attr_val} = {save_roll} vs {dc})")
            return
        else:
            log(f"  {enemy.label} uses {attack_name} — "
                f"{player.name} fails to save! (d20 + {attr_val} = {save_roll} vs {dc})")

    # ---- Damage ----
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
        log(f"  {enemy.label} hits with {attack_name} — "
            f"d20({nat}) + {bonus} = {attack_total} vs {defense} → "
            f"{final_damage} damage{crit_tag}")
    else:
        log(f"  {enemy.label} uses {attack_name}.")

    # ---- Steal gold ----
    if "steal_gold" in attack:
        amount = min(attack["steal_gold"], player.galleons)
        if amount > 0:
            player.galleons -= amount
            log(f"  → {enemy.label} snatches {amount} Galleons!")
        else:
            log(f"  → {enemy.label} finds nothing to steal.")

    # ---- Mana drain ----
    if "mana_drain" in attack:
        amount = min(attack["mana_drain"], player.current_mana)
        if amount > 0:
            player.current_mana -= amount
            log(f"  → {enemy.label} drains {amount} mana!")

    # ---- Effect ----
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

    # ---- Execute ----
    execute_threshold = attack.get("execute_threshold")
    if execute_threshold and player.current_hp > 0:
        if player.current_hp / player.max_hp() < execute_threshold:
            player.current_hp = 0
            log(f"  ★ {enemy.label}'s {attack_name} EXECUTES {player.name}!")


# ============================================================
# ENEMY SPECIALS + SUMMONS
# ============================================================

def _try_enemy_special(player, enemy, enemies, rng, log):
    """Returns True if a special consumed the enemy's turn."""

    # ---- Lure (Hinkypunk) ----
    if enemy.special_available("lure"):
        spec = next(s for s in enemy.specials if s["name"] == "lure")
        enemy.mark_special_used("lure")
        dc = spec["dc"]
        will = player.get_effective_attr("willpower")
        save = rng.randint(1, 20) + will
        if save >= dc:
            log(f"  {enemy.label} tries to lure {player.name} — "
                f"saved! (d20 + {will} = {save} vs {dc})")
        else:
            player.add_status("stunned", duration=1)
            log(f"  {enemy.label} LURES {player.name}! "
                f"d20 + {will} = {save} vs {dc} → stunned!")
        return True

    # ---- Web Shot (Acromantula) ----
    if enemy.special_available("web_shot"):
        spec = next(s for s in enemy.specials if s["name"] == "web_shot")
        enemy.mark_special_used("web_shot")
        penalty = spec.get("agility_penalty", -2)
        dur = spec.get("duration", 2)
        player.add_status("weakened", data={"amount": penalty}, duration=dur)
        log(f"  {enemy.label} shoots webbing! {player.name} is slowed ({penalty} for {dur}).")
        return True

    # ---- Steadfast (Hufflepuff Rival) ----
    if enemy.special_available("steadfast") and enemy.hp_pct() < 0.30:
        spec = next(s for s in enemy.specials if s["name"] == "steadfast")
        enemy.mark_special_used("steadfast")
        heal = spec.get("heal", 0)
        enemy.heal(heal)
        log(f"  ★ {enemy.label} rallies! (+{heal} HP)")
        return True

    # ---- Dark Lord's Will (Voldemort) ----
    if enemy.special_available("dark_lords_will") and enemy.hp_pct() < 0.5:
        spec = next(s for s in enemy.specials if s["name"] == "dark_lords_will")
        enemy.mark_special_used("dark_lords_will")
        heal = spec.get("heal", 0)
        enemy.heal(heal)
        log(f"  ★ {enemy.label} draws on dark power! (+{heal} HP)")
        return True

    # ---- Dark Mark (Death Eater) ----
    if enemy.special_available("dark_mark") and enemy.hp_pct() < 0.5:
        spec = next(s for s in enemy.specials if s["name"] == "dark_mark")
        enemy.mark_special_used("dark_mark")
        summon_key = spec.get("summon")
        hp_pct = spec.get("summon_hp_pct", 1.0)
        new_enemy = _summon_enemy(enemies, summon_key, hp_pct, log)
        if new_enemy:
            log(f"  ★ {enemy.label} summons {new_enemy.label} with the Dark Mark!")
        return True

    # ---- Brood Mother (Aragog) ----
    for spec in enemy.specials:
        if spec.get("name") != "brood_mother":
            continue
        for thresh in spec.get("thresholds", []):
            key = f"brood_mother_{int(thresh * 100)}"
            if enemy.hp_pct() < thresh and key not in enemy.used_specials:
                enemy.mark_special_used(key)
                summon_key = spec.get("summon")
                hp_pct = spec.get("summon_hp_pct", 1.0)
                new_enemy = _summon_enemy(enemies, summon_key, hp_pct, log)
                if new_enemy:
                    log(f"  ★ {enemy.label} spawns {new_enemy.label}!")
                return True

    # ---- Fear Aura (Dementor) — passive, doesn't consume turn ----
    if any(s.get("name") == "fear_aura" for s in enemy.specials):
        spec = next(s for s in enemy.specials if s["name"] == "fear_aura")
        dc = spec["dc"]
        will = player.get_effective_attr("willpower")
        save = rng.randint(1, 20) + will
        if save < dc:
            player.current_mana = max(0, player.current_mana - spec["mana_drain"])
            player.add_status("weakened",
                              data={"amount": spec["penalty"]}, duration=1)
            log(f"  {enemy.label}'s Fear Aura grips {player.name}! "
                f"(-{spec['mana_drain']} mana, {spec['penalty']} to rolls)")
        else:
            log(f"  {enemy.label}'s Fear Aura washes over {player.name} — resisted.")
        return False

    return False


def _summon_enemy(enemies, summon_key, hp_pct, log):
    def _summon_enemy(enemies, summon_key, hp_pct, log):
        """Create an Enemy, label it, and append it. Returns the new Enemy or None."""
    if summon_key not in ENEMIES:
        log(f"  (Unknown summon: {summon_key})")
        return None

    new_enemy = Enemy(summon_key)
    if hp_pct < 1.0:
        new_enemy.current_hp = max(1, int(new_enemy.max_hp * hp_pct))

    # ---- Assign a stable label ----
    same_name = [e for e in enemies if e.name == new_enemy.name]

    if not same_name:
        new_enemy.label = new_enemy.name
    else:
        # Renumber existing un-numbered duplicates
        n = 0
        for e in same_name:
            label = getattr(e, "label", e.name)
            if " #" not in label:
                n += 1
                e.label = f"{e.name} #{n}"
            else:
                try:
                    existing_n = int(label.rsplit(" #", 1)[1])
                    n = max(n, existing_n)
                except (ValueError, IndexError):
                    pass
        n += 1
        new_enemy.label = f"{new_enemy.name} #{n}"

    enemies.append(new_enemy)
    return new_enemy


# ============================================================
# PLAYER TARGETING
# ============================================================

def _auto_pick_target(enemies):
    """Pick the lowest-HP living enemy."""
    living = _living(enemies)
    if not living:
        return None
    return min(living, key=lambda e: e.current_hp)


def _prompt_target_selection(enemies, log):
    """Prompt for an enemy target. Returns Enemy or None (back out)."""
    living = _living(enemies)
    if not living:
        return None
    if len(living) == 1:
        return living[0]

    log("")
    log("  Which enemy?")
    for i, e in enumerate(living, start=1):
        log(f"    {i}. {e.label:<28} HP {e.current_hp}/{e.max_hp}")
    log("    0. Back")

    try:
        choice = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if choice == "0" or not choice.isdigit():
        return None
    n = int(choice) - 1
    if 0 <= n < len(living):
        return living[n]
    return None


# ============================================================
# ENEMY DEATH HANDLING
# ============================================================

def _handle_enemy_death(player, enemy, log):
    """On-death specials (Erumpent explosion)."""
    for spec in getattr(enemy, "specials", []):
        if spec.get("name") == "explosive_death":
            dmg = spec.get("damage", 0)
            if dmg > 0:
                player.take_damage(dmg)
                log(f"  ★ {enemy.label} explodes! {player.name} takes {dmg} damage.")


# ============================================================
# OUTCOMES
# ============================================================

def _win(player, enemies, turns, rng, log):
    # Aggregate rewards from every enemy in the fight
    total_xp = 0
    total_gold = 0
    total_tokens = 0
    total_rare_tokens = 0
    has_new_species = False
    total_streak_mult = player.streak_multiplier()

    # Any enemy with `no_streak` doesn't count toward bond/streak
    any_real_enemy = any(not e.no_streak for e in enemies)

    log("")
    log(f"═══ VICTORY ═══")
    if len(enemies) == 1:
        log(f"  {enemies[0].label} defeated in {turns} turns.")
    else:
        log(f"  All {len(enemies)} enemies defeated in {turns} turns.")

    for e in enemies:
        rewards = e.roll_rewards(rng)
        total_xp += rewards["xp"]
        total_gold += rewards["galleons"]
        total_tokens += rewards["tokens"]
        total_rare_tokens += rewards["rare_tokens"]

        # Species discovery (Hufflepuff)
        if player.discover_enemy(e.key):
            has_new_species = True

    # Apply streak multiplier (once on aggregate)
    xp_gain = int(total_xp * total_streak_mult)
    gold_gain = int(total_gold * total_streak_mult)

    if total_streak_mult > 1.0 and any_real_enemy:
        log(f"  Win streak bonus: ×{total_streak_mult:.2f}")

    player.gain_xp(xp_gain)
    player.add_galleons(gold_gain)
    player.add_spell_tokens(total_tokens + total_rare_tokens)

    bond_up = False
    if any_real_enemy:
        bond_up = player.record_battle_won()

    log(f"  +{xp_gain} XP")
    log(f"  +{gold_gain} Galleons")
    if total_tokens:
        log(f"  +{total_tokens} Spell Token(s)")
    if total_rare_tokens:
        log(f"  +{total_rare_tokens} RARE Token(s)")
    if bond_up:
        log(f"  ★ WAND BOND UP! Now Bond {player.bond_level()} ({player.bond_name()})")

    if has_new_species and player.house == "hufflepuff":
        hp_bonus = HOUSES["hufflepuff"]["passive_data"]["hp_per_species"]
        log(f"  ★ Hufflepuff: new species discovered! +{hp_bonus} max HP.")
        player.heal(hp_bonus)

    # Ravenclaw streak
    bonus_tokens = 0
    if any_real_enemy:
        bonus_tokens, msg = player.record_win()
        if msg:
            log(f"  ★ {msg}")

    # Battle log — record once for the fight
    if len(enemies) == 1:
        label = enemies[0].name
    else:
        label = f"{len(enemies)} enemies"

    player.record_battle(
        enemy_name=label,
        result="win",
        turns=turns,
        xp=xp_gain,
        gold=gold_gain,
        tokens=total_tokens + total_rare_tokens + bonus_tokens,
    )

    return {
        "result": "win",
        "turns": turns,
        "rewards": {
            "xp": xp_gain,
            "galleons": gold_gain,
            "tokens": total_tokens,
            "rare_tokens": total_rare_tokens,
        },
        "bond_up": bond_up,
    }


def _lose(player, enemies, turns, log):
    log("")
    log(f"═══ DEFEAT ═══")
    log(f"  {player.name} falls after {turns} turns.")

    is_boss = any(getattr(e, "is_boss", False) for e in enemies)

    if is_boss:
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

    if len(enemies) == 1:
        label = enemies[0].name
    else:
        label = f"{len(enemies)} enemies"

    player.record_battle(
        enemy_name=label,
        result="lose",
        turns=turns,
    )

    return {
        "result": "lose",
        "turns": turns,
        "rewards": None,
    }


def _flee(player, enemies, turns, log):
    log(f"  {player.name} flees the battle. Win streak reset.")
    player.reset_streak()

    if len(enemies) == 1:
        label = enemies[0].name
    else:
        label = f"{len(enemies)} enemies"

    player.record_battle(
        enemy_name=label,
        result="flee",
        turns=turns,
    )

    return {
        "result": "flee",
        "turns": turns,
        "rewards": None,
    }


def _draw(player, enemies, turns, log):
    log(f"  Battle drags on — both sides retreat. (Draw after {turns} turns)")

    if len(enemies) == 1:
        label = enemies[0].name
    else:
        label = f"{len(enemies)} enemies"

    player.record_battle(
        enemy_name=label,
        result="draw",
        turns=turns,
    )

    return {
        "result": "draw",
        "turns": turns,
        "rewards": None,
    }


# ============================================================
# PLAYER ACTION PROMPT
# ============================================================

def _prompt_player_action(player, enemies, rng, log):
    """
    Show menu, read input.
    Returns: spell_key | (spell_key, target) | "flee" | "item_used" | None
    """
    living = _living(enemies)

    while True:
        log("")
        log(f"  {player.name}: HP {player.current_hp}/{player.max_hp()}  "
            f"Mana {player.current_mana}/{player.max_mana()}")
        log("  Enemies:")
        for i, e in enumerate(living, start=1):
            statuses = ""
            if e.statuses:
                statuses = "  [" + ",".join(s["name"] for s in e.statuses) + "]"
            log(f"    {i}. {e.label:<28} HP {e.current_hp}/{e.max_hp}{statuses}")
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
            result = _item_menu(player, enemies, rng, log)
            if result == "item_used":
                return "item_used"
            continue

        if choice in ("f", "flee"):
            return "flee"

        if choice == "0":
            return None

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                spell_key = options[idx]
                spell = SPELLS[spell_key]

                # Self-target spells skip target selection
                if spell["type"] in ("support", "defense"):
                    return spell_key

                # Offensive — prompt for target
                target = _prompt_target_selection(enemies, log)
                if target is None:
                    continue  # back to menu
                return (spell_key, target)


# ============================================================
# HELPERS FOR MENUS
# ============================================================

def _total_consumables(player):
    p = sum(player.inventory.get("potions", {}).values())
    i = sum(player.inventory.get("items", {}).values())
    return p + i


def _item_menu(player, enemies, rng, log):
    """Show items. Returns 'item_used' or None."""
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
    entries = []

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
        # Combat items need a target
        target = _prompt_target_selection(enemies, log)
        if target is None:
            return None
        ok, msgs = use_combat_item(player, key, target, rng)

    for m in msgs:
        log("  " + m)

    if not ok:
        return None
    return "item_used"


def _show_spell_help(player, log):
    log("")
    log("  ═══ SPELL DETAILS ═══")
    for key in player.known_spells:
        spell = SPELLS[key]
        cost = player.get_spell_mana_cost(key)

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
# AUTO-MODE HELPERS
# ============================================================

def _auto_pick_spell(player, enemies):
    """For auto-mode testing. Picks strongest affordable spell.
    `enemies` is unused for now but kept for future smart targeting."""
    best = None
    best_score = -1
    for key in player.known_spells:
        cost = player.get_spell_mana_cost(key)
        if player.current_mana < cost:
            continue
        spell = SPELLS[key]
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

