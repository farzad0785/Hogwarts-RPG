"""
player.py — the Player class.

Handles:
- Base attributes + effective attribute calculation (base + wand + temp mods)
- Derived stats (HP, Mana, defenses)
- Resources (current HP/Mana, Galleons, Spell Tokens)
- XP and leveling
- Known spells
- Wand (wood, core, bond)
- Status effects (burn, poison, disarmed, etc.)
"""

from Data import (
    ATTRIBUTES, ATTR_DISPLAY, ATTR_MIN, ATTR_MAX,
    XP_TO_NEXT, ATTR_POINTS_PER_LEVEL,
    SPELLS, MAX_LEVEL, MANA_REGEN_PER_TURN,
    STATUS_EFFECTS,
    WAND_WOOD_BONUS, WAND_CORES, WAND_BOND_LEVELS, BOND_NAMES,
    GEAR, GEAR_SLOTS, INVENTORY_LIMITS,
    WAND_UPGRADES,
    HOUSES,
    STREAK_BONUS_PER_WIN, STREAK_CAP,
)


# ============================================================
# STARTING VALUES
# ============================================================

STARTING_ATTRS = {
    "brawn": 3,
    "agility": 3,
    "intellect": 3,
    "perception": 3,
    "willpower": 3,
    "presence": 3,
    "power": 4,
    "control": 4,
}

STARTING_TOKENS = 2
STARTING_GALLEONS = 0
STARTING_SPELLS = ["flipendo"]

# ============================================================
# PLAYER CLASS
# ============================================================

class Player:
    def __init__(
            self,
            name="Student",
            wand_wood="holly",
            wand_core="phoenix_feather",
            attrs=None,
    ):
        self.name = name
        self.level = 1
        self.xp = 0
        self.attr_points = 0
        self.house = None                # set after Sorting
        self.win_streak = 0
        self.discovered_enemies = []     # list of enemy keys (Hufflepuff)

        # Attributes
        self.base_attrs = dict(attrs) if attrs else dict(STARTING_ATTRS)

        # Wand
        self.wand = {
            "wood": wand_wood,
            "core": wand_core,
            "battles_won": 0,
        }
        self.wand_upgrades = []   # list of purchased upgrade keys

        # Temporary modifiers (list of {"attr", "amount", "duration", "source"})
        self.temp_mods = []

        # Status effects (list of {"name", "duration", ...extra})
        self.statuses = []

        # Resources
        self.galleons = STARTING_GALLEONS
        self.spell_tokens = STARTING_TOKENS
        self.known_spells = list(STARTING_SPELLS)

        # Inventory (fleshed out later with items system)
        self.inventory = {
            "potions": {},   # {"healing_draught": 2, ...}
            "items": {},
            "gear": {},
        }

        # Equipped gear (one item per slot; None = empty)
        self.equipped = {slot: None for slot in GEAR_SLOTS}

        # Initialize current HP/Mana to max
        self.current_hp = self.max_hp()
        self.current_mana = self.max_mana()

    # --------------------------------------------------------
    # ATTRIBUTES
    # --------------------------------------------------------

    def get_effective_attr(self, attr):
        """Base + wand bonuses + temporary modifiers, clamped 1–10."""
        base = self.base_attrs.get(attr, 0)
        value = base + self._permanent_attr_bonus(attr) + self._temp_attr_bonus(attr)
        return max(ATTR_MIN, min(ATTR_MAX, value))

    def get_all_effective_attrs(self):
        return {a: self.get_effective_attr(a) for a in ATTRIBUTES}

    def _permanent_attr_bonus(self, attr):
        bonus = 0
        # Wand wood
        if WAND_WOOD_BONUS.get(self.wand["wood"]) == attr:
            bonus += 1
        # Wand bond
        bonus += self._bond_bonuses().get(attr, 0)
        # Wand upgrades
        bonus += self._wand_upgrade_attr(attr)
        # Gear attributes
        for gear_key in self.equipped.values():
            if gear_key is None:
                continue
            gear = GEAR.get(gear_key, {})
            bonus += gear.get("attrs", {}).get(attr, 0)
        # House attribute bonus
        if self.house and self.house in HOUSES:
            bonus += HOUSES[self.house]["attr_bonus"].get(attr, 0)
        return bonus

    def _temp_attr_bonus(self, attr):
        return sum(m["amount"] for m in self.temp_mods if m["attr"] == attr)

    # --------------------------------------------------------
    # DERIVED STATS
    # --------------------------------------------------------

    def max_hp(self):
        eff = self.get_all_effective_attrs()
        base = 20 + eff["brawn"] * 3 + eff["willpower"] * 2 + self.level * 5
        base += self._house_hp_bonus()
        return base

    def _house_hp_bonus(self):
        """Hufflepuff: +2 max HP per discovered enemy species."""
        if self.house == "hufflepuff":
            per = HOUSES["hufflepuff"]["passive_data"]["hp_per_species"]
            return per * len(self.discovered_enemies)
        return 0

    def max_mana(self):
        eff = self.get_all_effective_attrs()
        base = 20 + eff["power"] * 2 + eff["control"] * 2 + self.level * 3
        core = WAND_CORES.get(self.wand["core"], {})
        base += core.get("bonus_mana", 0)
        base += self._wand_upgrade_flat("mana")   # <-- ADD
        return base

    def physical_defense(self):
        eff = self.get_all_effective_attrs()
        base = 8 + eff["agility"] + eff["brawn"]
        return base + self._gear_flat_bonus("physical_defense")

    def magical_defense(self):
        eff = self.get_all_effective_attrs()
        return 8 + eff["willpower"] + eff["control"]

    def initiative_bonus(self):
        eff = self.get_all_effective_attrs()
        return eff["agility"] + eff["perception"]

    def spell_attack_bonus(self):
        """Added to d20 for spell attack rolls."""
        eff = self.get_all_effective_attrs()
        base = eff["control"] + eff["perception"]
        core = WAND_CORES.get(self.wand["core"], {})
        base += core.get("accuracy_modifier", 0)
        base += self._bond_bonuses().get("spell_accuracy", 0)
        base += self._wand_upgrade_flat("spell_accuracy")
        base += self.gryffindor_attack_bonus()
        return base

    def _gryffindor_clutch_active(self):
        if self.house != "gryffindor":
            return False
        threshold = HOUSES["gryffindor"]["passive_data"]["hp_threshold"]
        return (self.current_hp / self.max_hp()) < threshold

    def gryffindor_attack_bonus(self):
        if self._gryffindor_clutch_active():
            return HOUSES["gryffindor"]["passive_data"]["attack"]
        return 0

    def gryffindor_damage_bonus(self):
        if self._gryffindor_clutch_active():
            return HOUSES["gryffindor"]["passive_data"]["damage"]
        return 0

    def spell_damage_bonus(self, target_hp_pct=1.0):
        """Added to spell base + scaling."""
        core = WAND_CORES.get(self.wand["core"], {})
        bonus = core.get("damage_modifier", 0)
        bonus += self._bond_bonuses().get("spell_damage", 0)
        if core.get("name") == "Thestral Tail Hair" and target_hp_pct < 0.5:
            bonus += core.get("execute_bonus", 0)
        bonus += self.gryffindor_damage_bonus()
        return bonus

    def get_spell_mana_cost(self, spell_key):
        """Apply wand bond mana discount."""
        cost = SPELLS[spell_key]["mana"]
        cost -= self._bond_bonuses().get("mana_discount", 0)
        cost -= self._wand_upgrade_flat("mana_discount")   # <-- ADD
        return max(1, cost)

    def _gear_flat_bonus(self, flat_name):
        """Sum of flat bonuses from all equipped gear (e.g. physical_defense)."""
        total = 0
        for gear_key in self.equipped.values():
            if gear_key is None:
                continue
            gear = GEAR.get(gear_key, {})
            total += gear.get("flats", {}).get(flat_name, 0)
        return total

    # --------------------------------------------------------
    # RESOURCES
    # --------------------------------------------------------

    def take_damage(self, amount):
        self.current_hp = max(0, self.current_hp - int(amount))

    def heal(self, amount):
        self.current_hp = min(self.max_hp(), self.current_hp + int(amount))

    def spend_mana(self, amount):
        if self.current_mana < amount:
            return False
        self.current_mana -= amount
        return True

    def restore_mana(self, amount):
        self.current_mana = min(self.max_mana(), self.current_mana + amount)

    def is_alive(self):
        return self.current_hp > 0

    def _clamp_resources(self):
        self.current_hp = min(self.current_hp, self.max_hp())
        self.current_mana = min(self.current_mana, self.max_mana())

    # --------------------------------------------------------
    # XP & LEVELING
    # --------------------------------------------------------

    def gain_xp(self, amount):
        """Add XP, level up as many times as thresholds allow. Returns levels gained."""
        self.xp += amount
        levels_gained = 0
        while self.level < MAX_LEVEL:
            need = XP_TO_NEXT[self.level]
            if need is None or self.xp < need:
                break
            self.xp -= need
            self.level += 1
            levels_gained += 1
            self.attr_points += ATTR_POINTS_PER_LEVEL
        return levels_gained

    def spend_attr_point(self, attr):
        """Spend one unspent attribute point on `attr`."""
        if self.attr_points <= 0:
            return False
        if attr not in self.base_attrs:
            return False
        if self.base_attrs[attr] >= ATTR_MAX:
            return False
        self.base_attrs[attr] += 1
        self.attr_points -= 1
        self._clamp_resources()
        return True

    def full_restore(self):
        self.current_hp = self.max_hp()
        self.current_mana = self.max_mana()

    # --------------------------------------------------------
    # HOUSE PASSIVES
    # --------------------------------------------------------

    def discover_enemy(self, enemy_key):
        """
        Hufflepuff: track species. Returns True if this is a NEW species.
        Called by combat on victory.
        """
        if enemy_key in self.discovered_enemies:
            return False
        self.discovered_enemies.append(enemy_key)
        # Hufflepuff gets max HP bonus from this — clamp current HP so it doesn't shrink
        self._clamp_resources()
        return True

    # --------------------------------------------------------
    # WIN STREAK
    # --------------------------------------------------------

    def streak_multiplier(self):
        """Multiplier for XP and Galleons based on streak BEFORE this win."""
        streak = min(self.win_streak, STREAK_CAP)
        return 1.0 + streak * STREAK_BONUS_PER_WIN

    def record_win(self):
        """
        Called after a victory.
        Returns (bonus_tokens, message) where bonus_tokens is 0 for most houses.
        """
        self.win_streak += 1

        # Ravenclaw: +1 token every 4th win
        if self.house == "ravenclaw":
            interval = HOUSES["ravenclaw"]["passive_data"]["streak_interval"]
            tokens = HOUSES["ravenclaw"]["passive_data"]["tokens"]
            if self.win_streak > 0 and self.win_streak % interval == 0:
                self.spell_tokens += tokens
                return tokens, f"Ravenclaw insight: +{tokens} Spell Token!"

        return 0, None

    def reset_streak(self):
        self.win_streak = 0

    # --------------------------------------------------------
    # SPELLS
    # --------------------------------------------------------

    def knows_spell(self, spell_key):
        return spell_key in self.known_spells

    def learn_spell(self, spell_key):
        """Spend tokens and learn. Returns (success, message)."""
        if spell_key not in SPELLS:
            return False, "Unknown spell."
        if self.knows_spell(spell_key):
            return False, "Already known."
        cost = SPELLS[spell_key]["token_cost"]
        if self.spell_tokens < cost:
            return False, f"Need {cost} tokens, have {self.spell_tokens}."
        self.spell_tokens -= cost
        self.known_spells.append(spell_key)
        return True, f"Learned {SPELLS[spell_key]['name']}!"

    # --------------------------------------------------------
    # CURRENCY
    # --------------------------------------------------------

    def add_galleons(self, n):
        self.galleons += n

    def spend_galleons(self, n):
        if self.galleons < n:
            return False
        self.galleons -= n
        return True

    def add_spell_tokens(self, n):
        self.spell_tokens += n

    # --------------------------------------------------------
    # WAND
    # --------------------------------------------------------

    def _bond_bonuses(self):
        """Return the bond-level bonus dict for the current wand."""
        wins = self.wand["battles_won"]
        bonuses = {}
        for threshold, bonus in WAND_BOND_LEVELS:
            if wins >= threshold:
                bonuses = bonus
        return bonuses

    def _wand_upgrade_flat(self, key):
        """Sum flat bonus from purchased wand upgrades (e.g. spell_accuracy)."""
        total = 0
        for up_key in self.wand_upgrades:
            up = WAND_UPGRADES.get(up_key, {})
            total += up.get("effect", {}).get(key, 0)
        return total

    def _wand_upgrade_attr(self, attr):
        """Sum attribute bonus from purchased wand upgrades."""
        total = 0
        for up_key in self.wand_upgrades:
            up = WAND_UPGRADES.get(up_key, {})
            total += up.get("effect", {}).get("attr", {}).get(attr, 0)
        return total

    def bond_level(self):
        wins = self.wand["battles_won"]
        level = 1
        for i, (threshold, _) in enumerate(WAND_BOND_LEVELS):
            if wins >= threshold:
                level = i + 1
        return level

    def bond_name(self):
        return BOND_NAMES[self.bond_level() - 1]

    def record_battle_won(self):
        """Call after a battle victory. Returns True if bond leveled up."""
        old_level = self.bond_level()
        self.wand["battles_won"] += 1
        new_level = self.bond_level()
        if new_level > old_level:
            self._clamp_resources()
            return True
        return False
    
    def switch_wand(self, wood, core):
        """Swap wands. Resets bond. Old wand is lost (for now)."""
        if wood not in WAND_WOOD_BONUS:
            return False, "Unknown wood."
        if core not in WAND_CORES:
            return False, "Unknown core."
        self.wand = {"wood": wood, "core": core, "battles_won": 0}
        self.wand_upgrades = []   # <-- ADD (upgrades are tied to the wand)
        self._clamp_resources()
        return True, f"Now wielding {wood.title()} + {WAND_CORES[core]['name']}."

    # --------------------------------------------------------
    # STATUS EFFECTS
    # --------------------------------------------------------

    def add_status(self, name, duration=None, data=None):
        """Add or refresh a status effect."""
        template = STATUS_EFFECTS.get(name, {})
        dur = duration if duration is not None else template.get("duration", 1)
        effect = {"name": name, "duration": dur}
        if data:
            effect.update(data)
        # If already present, refresh duration
        existing = self.get_status(name)
        if existing:
            existing["duration"] = max(existing["duration"], dur)
            if data:
                existing.update(data)
        else:
            self.statuses.append(effect)

    def get_status(self, name):
        for s in self.statuses:
            if s["name"] == name:
                return s
        return None

    def has_status(self, name):
        return self.get_status(name) is not None

    def remove_status(self, name):
        self.statuses = [s for s in self.statuses if s["name"] != name]

    def tick_statuses(self):
        """
        Decrement durations, remove expired, return total DoT damage taken this tick.
        Call this at the END of the player's turn.
        """
        dot = 0
        remaining = []
        for s in self.statuses:
            template = STATUS_EFFECTS.get(s["name"], {})
            if template.get("type") == "dot":
                dot += s.get("damage", template.get("damage", 0))
            s["duration"] -= 1
            if s["duration"] > 0:
                remaining.append(s)
        self.statuses = remaining
        return dot
    def tick_temp_mods(self):
        """Decrement temp mods and remove expired ones."""
        remaining = []
        for m in self.temp_mods:
            m["duration"] -= 1
            if m["duration"] > 0:
                remaining.append(m)
        self.temp_mods = remaining

    # --------------------------------------------------------
    # END-OF-TURN EFFECTS
    # --------------------------------------------------------

    def end_of_turn(self):
        core = WAND_CORES.get(self.wand["core"], {})
        hp_regen = core.get("hp_regen", 0)

        before_hp = self.current_hp
        before_mana = self.current_mana

        if hp_regen:
            self.heal(hp_regen)
        self.restore_mana(MANA_REGEN_PER_TURN)

        dot = self.tick_statuses()
        if dot:
            self.take_damage(dot)

        self.tick_temp_mods()   # <-- ADD THIS LINE

        return (
            self.current_hp - before_hp,
            self.current_mana - before_mana,
            dot,
        )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    def sheet(self):
        """Return a multi-line character sheet string."""
        eff = self.get_all_effective_attrs()
        lines = []
        lines.append("━" * 50)
        house_str = f"  •  {HOUSES[self.house]['name']}" if self.house else ""
        lines.append(f"  {self.name} — Level {self.level}{house_str}")
        lines.append("━" * 50)
        lines.append(f"  HP:   {self.current_hp} / {self.max_hp()}")
        lines.append(f"  Mana: {self.current_mana} / {self.max_mana()}")
        xp_needed = XP_TO_NEXT.get(self.level)
        xp_display = f"{self.xp} / {xp_needed}" if xp_needed else f"{self.xp} (MAX)"
        lines.append(f"  XP:   {xp_display}")

        if self.attr_points:
            lines.append(f"  Unspent Attribute Points: {self.attr_points}")
        lines.append("")
        lines.append("  ATTRIBUTES          BASE   EFF")

        for attr in ATTRIBUTES:
            base = self.base_attrs[attr]
            e = eff[attr]
            marker = "" if base == e else f"  ({base}→{e})"
            lines.append(f"    {ATTR_DISPLAY[attr]:<14}  {base:>3}    {e:>3}{marker}")

        lines.append("")
        wood = self.wand["wood"].title()
        core = WAND_CORES[self.wand["core"]]["name"]
        bond = self.bond_name()
        lines.append(f"  WAND: {wood} + {core}  (Bond: {bond}, {self.wand['battles_won']} wins)")
        lines.append("")
        spells = ", ".join(SPELLS[s]["name"] for s in self.known_spells)
        lines.append(f"  SPELLS: {spells}")

        if self.win_streak > 0:
            mult = self.streak_multiplier()
            lines.append(f"  WIN STREAK: {self.win_streak}   (XP/Galleon multiplier: ×{mult:.2f})")
        lines.append(f"  TOKENS: {self.spell_tokens}    GALLEONS: {self.galleons}")

        if self.house and self.house in HOUSES:
            passive = HOUSES[self.house]["passive_data"]
            if self.house == "hufflepuff":
                bonus_hp = passive["hp_per_species"] * len(self.discovered_enemies)
                lines.append(f"  DISCOVERED: {len(self.discovered_enemies)} species   (+{bonus_hp} max HP)")

        if self.statuses:
            status_str = ", ".join(f"{s['name']}({s['duration']})" for s in self.statuses)
            lines.append(f"  STATUS: {status_str}")

        lines.append("━" * 50)
        return "\n".join(lines)


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    p = Player(name="Test Student", wand_wood="holly", wand_core="phoenix_feather")
    print(p.sheet())
    print()

    print("--- Gain 100 XP ---")
    levels = p.gain_xp(100)
    print(f"Leveled up {levels} time(s). Now level {p.level}, {p.attr_points} unspent points.")
    p.spend_attr_point("control")
    print("Spent point on Control.")
    print(p.sheet())
    print()

    print("--- Learn Expelliarmus ---")
    ok, msg = p.learn_spell("expelliarmus")
    print(msg)
    print(f"Tokens left: {p.spell_tokens}")

    print()
    print("--- Simulate battle win (5x to trigger bond 2) ---")
    for _ in range(5):
        leveled = p.record_battle_won()
        if leveled:
            print(f"Bond up! Now Bond {p.bond_level()} ({p.bond_name()})")
    print(f"Spell attack bonus: {p.spell_attack_bonus()}")