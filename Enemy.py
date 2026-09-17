"""
enemy.py — the Enemy class.

Handles:
- Loading enemy data from data.ENEMIES
- Current HP / Mana
- Choosing an attack each turn (respects hp_threshold, mana_cost, uses)
- Status effects (same system as Player)
- Reward payout
"""

from Data import ENEMIES, ENEMIES_BY_TIER, STATUS_EFFECTS, MANA_REGEN_PER_TURN


# ============================================================
# ENEMY CLASS
# ============================================================

class Enemy:
    def __init__(self, key):
        if key not in ENEMIES:
            raise ValueError(f"Unknown enemy: {key}")

        data = ENEMIES[key]
        self.key = key
        self.name = data["name"]
        self.tier = data["tier"]
        self.level = data["level"]

        # Max stats (frozen from data)
        self.max_hp = data["hp"]
        self.max_mana = data["mana"]

        # Current resources
        self.current_hp = self.max_hp
        self.current_mana = self.max_mana

        # Defenses
        self.pd = data["pd"]   # physical defense
        self.md = data["md"]   # magical defense

        self.initiative_bonus = data["initiative_bonus"]

        # Attacks
        self.attacks = data.get("attacks", [])

        # Specials (can be dict or list)
        special = data.get("special")
        if isinstance(special, list):
            self.specials = special
        elif isinstance(special, dict):
            self.specials = [special]
        else:
            self.specials = []

        # Weakness / resistance
        self.weak_to = data.get("weak_to", {})   # {"fire": 1.5}
        self.requires = data.get("requires")     # e.g. "expecto_patronum"

        # Rewards
        self.xp_reward = data["xp"]
        self.galleons_reward = data["galleons"]
        self.token_chance = data["token_chance"]
        self.rare_token = data.get("rare_token", False)
        self.rare_token_count = data.get("rare_token_count", 1)

        # Statuses
        self.statuses = []

        # Per-battle state (things that reset each fight)
        self.used_specials = set()   # names of one-use specials already used
        self.summons = []            # future use (Death Eater)
        self.slain = False           # set True when HP hits 0

    # --------------------------------------------------------
    # RESOURCES
    # --------------------------------------------------------

    def take_damage(self, amount):
        self.current_hp = max(0, self.current_hp - int(amount))
        if self.current_hp == 0:
            self.slain = True

    def heal(self, amount):
        self.current_hp = min(self.max_hp, self.current_hp + int(amount))

    def spend_mana(self, amount):
        if self.current_mana < amount:
            return False
        self.current_mana -= amount
        return True

    def restore_mana(self, amount):
        self.current_mana = min(self.max_mana, self.current_mana + amount)

    def is_alive(self):
        return self.current_hp > 0

    def hp_pct(self):
        return self.current_hp / self.max_hp if self.max_hp else 0.0

    # --------------------------------------------------------
    # STATUS EFFECTS
    # --------------------------------------------------------

    def add_status(self, name, duration=None, data=None):
        template = STATUS_EFFECTS.get(name, {})
        dur = duration if duration is not None else template.get("duration", 1)
        effect = {"name": name, "duration": dur}
        if data:
            effect.update(data)

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

    def should_skip_turn(self):
        """True if a skip_turn status is active."""
        for s in self.statuses:
            template = STATUS_EFFECTS.get(s["name"], {})
            if template.get("type") == "skip_turn":
                return True
        return False

    def get_attack_penalty(self):
        """Sum of debuff amounts (e.g. weakened -2)."""
        total = 0
        for s in self.statuses:
            template = STATUS_EFFECTS.get(s["name"], {})
            if template.get("type") == "debuff":
                total += s.get("amount", template.get("amount", 0))
        return total

    def tick_statuses(self):
        """
        Decrement durations, remove expired, return DoT damage taken this tick.
        Called at the END of the enemy's turn.
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

    # --------------------------------------------------------
    # DAMAGE MODIFIERS
    # --------------------------------------------------------

    def incoming_damage_multiplier(self, spell_type=None, element=None):
        """
        Apply weaknesses / resistances / specials.
        spell_type: "attack" | "control" | "defense" | "support"
        element:    "fire" | "physical" | "magical" | None
        """
        mult = 1.0

        # Weakness (e.g. Acromantula weak to fire)
        if element and element in self.weak_to:
            mult *= self.weak_to[element]

        # Special resistances
        for spec in self.specials:
            name = spec.get("name")

            if name == "thick_hide" and element == "physical":
                # Handled as flat reduction in combat, but mark it
                pass

            if name == "non_corporeal" and element == "physical":
                mult *= spec.get("physical_multiplier", 0.5)

            if name == "giant_serpent":
                if element in spec.get("resist", {}):
                    mult *= spec["resist"][element]

        return mult

    def flat_damage_reduction(self, element=None):
        """Thick Hide style flat reduction."""
        reduction = 0
        for spec in self.specials:
            if spec.get("name") == "thick_hide" and element == "physical":
                reduction += spec.get("physical_reduction", 0)
        return reduction

    def bloodthirsty_bonus(self):
        """Red Cap: +damage below 50% HP."""
        for spec in self.specials:
            if spec.get("name") == "bloodthirsty":
                if self.hp_pct() < spec["threshold"]:
                    return spec["bonus_damage"]
        return 0

    def frenzy_extra_attacks(self):
        """Werewolf: extra attacks below 30% HP."""
        for spec in self.specials:
            if spec.get("name") == "frenzy":
                if self.hp_pct() < spec["threshold"]:
                    return spec["extra_attacks"]
        return 0

    def extra_damage_taken(self):
        """Werewolf frenzy: +dmg taken while frenzied."""
        for spec in self.specials:
            if spec.get("name") == "frenzy":
                if self.hp_pct() < spec["threshold"]:
                    return spec["extra_damage_taken"]
        return 0

    # --------------------------------------------------------
    # ATTACK SELECTION (AI)
    # --------------------------------------------------------

    def choose_attack(self):
        """
        Pick an attack for this turn.
        Returns an attack dict or None if the enemy has no options.
        """
        if not self.attacks:
            return None

        # Filter by conditions
        available = []
        for atk in self.attacks:
            # hp_threshold: only usable below X% HP
            threshold = atk.get("hp_threshold")
            if threshold is not None and self.hp_pct() >= threshold:
                continue

            # mana_cost
            mana_cost = atk.get("mana_cost", 0)
            if mana_cost and self.current_mana < mana_cost:
                continue

            available.append(atk)

        if not available:
            # Fall back to the first attack that doesn't need mana (if any)
            for atk in self.attacks:
                if atk.get("mana_cost", 0) == 0:
                    threshold = atk.get("hp_threshold")
                    if threshold is None or self.hp_pct() < threshold:
                        return atk
            return None

        # Simple AI:
        # - Prefer strong attacks (higher damage) when available
        # - Otherwise first available
        # We keep it deterministic-ish for now; can add randomness later.
        available.sort(key=lambda a: a.get("damage", 0), reverse=True)
        return available[0]

    def special_available(self, name):
        """Check if a one-use special is still available."""
        for spec in self.specials:
            if spec.get("name") == name:
                if name in self.used_specials:
                    return False
                # uses check
                max_uses = spec.get("uses", 1)
                used_count = sum(1 for s in self.used_specials if s == name)
                if used_count >= max_uses:
                    return False
                return True
        return False

    def mark_special_used(self, name):
        self.used_specials.add(name)

    # --------------------------------------------------------
    # END OF TURN
    # --------------------------------------------------------

    def end_of_turn(self):
        """
        Called at end of the enemy's turn.
        Returns (mana_gained, dot_damage).
        """
        before_mana = self.current_mana
        self.restore_mana(MANA_REGEN_PER_TURN)

        dot = self.tick_statuses()
        if dot:
            self.take_damage(dot)

        return (self.current_mana - before_mana, dot)

    # --------------------------------------------------------
    # REWARDS
    # --------------------------------------------------------

    def roll_rewards(self, rng):
        """
        Roll rewards for defeating this enemy.
        `rng` is a random.Random instance.
        Returns dict: {"xp", "galleons", "tokens", "rare_tokens"}
        """
        tokens = 0
        rare_tokens = 0

        if rng.random() < self.token_chance:
            tokens = 1
        if self.rare_token:
            rare_tokens = self.rare_token_count

        return {
            "xp": self.xp_reward,
            "galleons": self.galleons_reward,
            "tokens": tokens,
            "rare_tokens": rare_tokens,
        }

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    def status_line(self):
        if not self.statuses:
            return ""
        return "  STATUS: " + ", ".join(
            f"{s['name']}({s['duration']})" for s in self.statuses
        )

    def short_sheet(self):
        lines = []
        lines.append(f"{self.name} (Lv {self.level}, {self.tier})")
        lines.append(f"  HP:   {self.current_hp} / {self.max_hp}")
        if self.max_mana:
            lines.append(f"  Mana: {self.current_mana} / {self.max_mana}")
        lines.append(f"  PD: {self.pd}   MD: {self.md}   Init: {self.initiative_bonus:+d}")
        if self.statuses:
            lines.append(self.status_line())
        return "\n".join(lines)


# ============================================================
# HELPERS
# ============================================================

def make_enemy(key):
    """Convenience constructor."""
    return Enemy(key)


def enemies_of_tier(tier):
    """Return list of enemy keys for a tier."""
    return list(ENEMIES_BY_TIER.get(tier, []))


def random_enemy_key(tier, rng):
    """Pick a random enemy key from a tier."""
    keys = enemies_of_tier(tier)
    if not keys:
        return None
    return rng.choice(keys)


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    import random
    rng = random.Random(42)

    print("=== Sample Enemies ===\n")

    for key in ["training_dummy", "cornish_pixie", "mountain_troll",
                "dementor", "basilisk"]:
        e = Enemy(key)
        print(e.short_sheet())
        print()

    print("=== Attack Selection Test ===\n")

    # Dark Wizard Apprentice — Sectumsempra only below 50% HP
    dw = Enemy("dark_wizard_apprentice")
    print(f"{dw.name} at full HP:")
    chosen = dw.choose_attack()
    print(f"  -> Chooses: {chosen['name']}")

    dw.current_hp = int(dw.max_hp * 0.4)
    print(f"\n{dw.name} at 40% HP:")
    chosen = dw.choose_attack()
    print(f"  -> Chooses: {chosen['name']}")

    print()
    print("=== Reward Roll Test ===\n")

    for key in ["cornish_pixie", "mountain_troll", "dementor"]:
        e = Enemy(key)
        # Roll 5 times to see the random token distribution
        rolls = [e.roll_rewards(rng) for _ in range(5)]
        tokens = sum(r["tokens"] for r in rolls)
        print(f"{e.name:<28} token_chance={e.token_chance:.0%}  "
              f"got {tokens}/5 tokens")

    print()
    print("=== Status Effect Test ===\n")

    rat = Enemy("giant_rat")
    rat.add_status("burn", duration=3, data={"damage": 3})
    print(rat.short_sheet())
    for turn in range(3):
        mana_gained, dot = rat.end_of_turn()
        print(f"  Turn {turn + 1}: dot={dot}, hp={rat.current_hp}, "
              f"statuses={[s['name'] for s in rat.statuses]}")