"""
Data.py — Central data for the wizard RPG.

Everything here comes from agent.md.
Edit this file to tweak balance; the rest of the code reads from here.
"""

# ============================================================
# ATTRIBUTES
# ============================================================

ATTRIBUTES = [
    "brawn",
    "agility",
    "intellect",
    "perception",
    "willpower",
    "presence",
    "power",
    "control",
]

ATTR_DISPLAY = {
    "brawn": "Brawn",
    "agility": "Agility",
    "intellect": "Intellect",
    "perception": "Perception",
    "willpower": "Willpower",
    "presence": "Presence",
    "power": "Power",
    "control": "Control",
}

ATTR_MIN = 1
ATTR_MAX = 10


# ============================================================
# COMBAT CONSTANTS
# ============================================================

MANA_REGEN_PER_TURN = 2
FUMBLE_MANA_LOSS = 3          # extra mana lost on natural 1
CRIT_MULTIPLIER = 2           # natural 20 = double damage

MAX_LEVEL = 10


# ============================================================
# LEVELING
# ============================================================

# XP needed to go from this level to the next.
XP_TO_NEXT = {
    1: 100,
    2: 200,
    3: 300,
    4: 400,
    5: 500,
    6: 600,
    7: 700,
    8: 800,
    9: 900,
    10: None,   # max level
}

ATTR_POINTS_PER_LEVEL = 1
HP_PER_LEVEL = 5
MANA_PER_LEVEL = 3

# ============================================================
# ITEMS
# ============================================================

POTIONS = {
    "healing_draught": {
        "name": "Healing Draught",
        "effect": {"heal": 25},
        "cost": 10,
        "description": "Restore 25 HP.",
    },
    "wiggenweld": {
        "name": "Wiggenweld Potion",
        "effect": {"heal": 50},
        "cost": 25,
        "description": "Restore 50 HP.",
    },
    "mana_elixir": {
        "name": "Mana Elixir",
        "effect": {"restore_mana": 20},
        "cost": 15,
        "description": "Restore 20 Mana.",
    },
    "antidote": {
        "name": "Antidote",
        "effect": {"cure": ["poison", "infected"]},
        "cost": 10,
        "description": "Remove poison or infection.",
    },
    "burn_salve": {
        "name": "Burn Salve",
        "effect": {"cure": ["burn"]},
        "cost": 8,
        "description": "Remove burn.",
    },
    "invigoration_draught": {
        "name": "Invigoration Draught",
        "effect": {"buff": {"attr": "power", "amount": 2, "duration": 3}},
        "cost": 20,
        "description": "+2 Power for 3 turns.",
    },
    "focusing_potion": {
        "name": "Focusing Potion",
        "effect": {"buff": {"attr": "control", "amount": 2, "duration": 3}},
        "cost": 20,
        "description": "+2 Control for 3 turns.",
    },
    "draught_of_peace": {
        "name": "Draught of Peace",
        "effect": {"buff": {"attr": "willpower", "amount": 2, "duration": 3}},
        "cost": 20,
        "description": "+2 Willpower for 3 turns.",
    },
    "fire_protection": {
        "name": "Fire Protection Potion",
        "effect": {"resistance": {"element": "fire", "multiplier": 0.5, "duration": 3}},
        "cost": 18,
        "description": "-50% fire damage for 3 turns.",
    },
}

COMBAT_ITEMS = {
    "chinese_cabbage": {
        "name": "Chinese Chomping Cabbage",
        "effect": {"damage": 12, "ignores_defense": True},
        "cost": 15,
        "description": "12 damage, ignores defense.",
    },
    "dungbomb": {
        "name": "Dungbomb",
        "effect": {"skip_turn_chance": 0.5},
        "cost": 10,
        "description": "50% chance enemy loses next turn.",
    },
    "darkness_powder": {
        "name": "Instant Darkness Powder",
        "effect": {"debuff": {"attr": "attack", "amount": -4, "duration": 1}},
        "cost": 12,
        "description": "Enemy -4 to next attack.",
    },
    "fanged_flyer": {
        "name": "Fanged Flyer",
        "effect": {"damage": 8, "guaranteed_hit": True},
        "cost": 18,
        "description": "8 damage, guaranteed hit.",
    },
    "stink_pellet": {
        "name": "Stink Pellet",
        "effect": {"flee_below_pct": 0.25},
        "cost": 8,
        "description": "Enemy flees if below 25% HP.",
    },
}

GEAR = {
    "student_robes": {
        "name": "Student Robes",
        "slot": "body",
        "flats": {"physical_defense": 1},
        "cost": 20,
        "description": "+1 Physical Defense.",
    },
    "dueling_robes": {
        "name": "Dueling Robes",
        "slot": "body",
        "flats": {"physical_defense": 2},
        "cost": 50,
        "description": "+2 Physical Defense.",
    },
    "dragonhide_gloves": {
        "name": "Dragonhide Gloves",
        "slot": "hands",
        "attrs": {"power": 1},
        "cost": 60,
        "description": "+1 Power.",
    },
    "quickstep_boots": {
        "name": "Quickstep Boots",
        "slot": "feet",
        "attrs": {"agility": 1},
        "cost": 40,
        "description": "+1 Agility.",
    },
    "focusing_ring": {
        "name": "Focusing Ring",
        "slot": "ring",
        "attrs": {"control": 1},
        "cost": 80,
        "description": "+1 Control.",
    },
    "lucky_charm": {
        "name": "Lucky Charm",
        "slot": "amulet",
        "special": {"name": "reroll_nat_1", "uses_per_battle": 1},
        "cost": 100,
        "description": "Reroll one natural 1 per battle.",
    },
}

GEAR_SLOTS = ["body", "hands", "feet", "ring", "amulet"]

INVENTORY_LIMITS = {
    "potion_stack": 5,
    "item_stack": 10,
}

# ============================================================
# SPELLS
# ============================================================

# type : "attack" | "control" | "defense" | "support"
# scaling: list of attributes added to base damage / heal
# effect: special effect dict (optional)

SPELLS = {
    "flipendo": {
        "name": "Flipendo",
        "type": "attack",
        "mana": 5,
        "base": 6,
        "scaling": ["power"],
        "effect": {"name": "weakened", "amount": -2, "duration": 1},
        "token_cost": 1,
        "description": "Knockback jinx. Cheap damage, weakens enemy's next attack.",
    },
    "expelliarmus": {
        "name": "Expelliarmus",
        "type": "control",
        "mana": 10,
        "base": 3,
        "scaling": ["control"],
        "effect": {"name": "disarmed", "duration": 1},
        "token_cost": 3,
        "description": "Disarming charm. Low damage, but enemy loses their next turn.",
    },
    "protego": {
        "name": "Protego",
        "type": "defense",
        "mana": 8,
        "base": 0,
        "scaling": [],
        "effect": {"name": "shield", "reduce": 0.60, "duration": 1},
        "token_cost": 4,
        "description": "Shield charm. Blocks the next spell, or reduces damage by 60% this turn.",
    },
    "incendio": {
        "name": "Incendio",
        "type": "attack",
        "mana": 18,
        "base": 16,
        "scaling": ["power"],
        "effect": {"name": "burn", "damage": 3, "duration": 3},
        "token_cost": 5,
        "description": "Fire-making spell. Heavy damage plus burn over 3 turns.",
    },
    "episkey": {
        "name": "Episkey",
        "type": "support",
        "mana": 12,
        "base": 10,
        "scaling": ["intellect", "willpower"],
        "effect": None,
        "token_cost": 3,
        "description": "Healing charm. Restores HP to yourself.",
    },
}


# ============================================================
# STATUS EFFECTS
# ============================================================

STATUS_EFFECTS = {
    "burn":      {"damage": 3,  "duration": 3, "type": "dot"},
    "poison":    {"damage": 2,  "duration": 3, "type": "dot"},
    "infected":  {"damage": 2,  "duration": 2, "type": "dot"},
    "disarmed":  {"duration": 1, "type": "skip_turn"},
    "stunned":   {"duration": 1, "type": "skip_turn"},
    "petrified": {"duration": 2, "type": "skip_turn"},
    "weakened":  {"amount": -2, "duration": 1, "type": "debuff"},
    "shield":    {"reduce": 0.60, "duration": 1, "type": "buff"},
}


# ============================================================
# ENEMIES
# ============================================================
# tier: "very_weak" | "weak" | "average" | "strong" | "very_strong"
# attacks: list of dicts — name, to_hit_bonus, damage, vs ("md" | "pd"), effect (optional)

ENEMIES = {
    # --- VERY WEAK ---
    "training_dummy": {
        "name": "Training Dummy",
        "tier": "very_weak",
        "level": 1, "hp": 12, "mana": 0,
        "pd": 8, "md": 8, "initiative_bonus": 0,
        "attacks": [],
        "special": None,
        "xp": 5, "galleons": 1, "token_chance": 0.05,
    },
    "cornish_pixie": {
        "name": "Cornish Pixie",
        "tier": "very_weak",
        "level": 1, "hp": 18, "mana": 10,
        "pd": 12, "md": 10, "initiative_bonus": 5,
        "attacks": [
            {"name": "Nip", "to_hit_bonus": 4, "damage": 4, "vs": "pd"},
        ],
        "special": {"name": "erratic", "dodge_chance": 0.25},
        "xp": 10, "galleons": 2, "token_chance": 0.10,
    },
    "garden_gnome": {
        "name": "Garden Gnome",
        "tier": "very_weak",
        "level": 1, "hp": 20, "mana": 0,
        "pd": 10, "md": 9, "initiative_bonus": 1,
        "attacks": [
            {"name": "Headbutt", "to_hit_bonus": 3, "damage": 5, "vs": "pd"},
        ],
        "special": {"name": "stubborn", "resist_spell": "flipendo", "multiplier": 0.5},
        "xp": 8, "galleons": 1, "token_chance": 0.08,
    },

    # --- WEAK ---
    "giant_rat": {
        "name": "Giant Rat",
        "tier": "weak",
        "level": 2, "hp": 30, "mana": 0,
        "pd": 12, "md": 11, "initiative_bonus": 3,
        "attacks": [
            {"name": "Bite", "to_hit_bonus": 5, "damage": 8, "vs": "pd",
             "effect": {"name": "infected", "chance": 0.25}},
        ],
        "special": None,
        "xp": 22, "galleons": 5, "token_chance": 0.20,
    },
    "doxie": {
        "name": "Doxie",
        "tier": "weak",
        "level": 2, "hp": 24, "mana": 12,
        "pd": 14, "md": 12, "initiative_bonus": 4,
        "attacks": [
            {"name": "Venomous Bite", "to_hit_bonus": 5, "damage": 6, "vs": "pd",
             "effect": {"name": "poison", "chance": 1.0}},
        ],
        "special": {"name": "tiny", "to_hit_penalty": -2},
        "xp": 25, "galleons": 6, "token_chance": 0.20,
    },
    "hinkypunk": {
        "name": "Hinkypunk",
        "tier": "weak",
        "level": 2, "hp": 28, "mana": 20,
        "pd": 11, "md": 13, "initiative_bonus": 2,
        "attacks": [
            {"name": "Flame Burst", "to_hit_bonus": 5, "damage": 9, "vs": "md"},
        ],
        "special": {"name": "lure", "dc": 13, "uses": 1},
        "xp": 25, "galleons": 6, "token_chance": 0.20,
    },

    # --- AVERAGE ---
    "red_cap": {
        "name": "Red Cap",
        "tier": "average",
        "level": 3, "hp": 50, "mana": 15,
        "pd": 14, "md": 13, "initiative_bonus": 4,
        "attacks": [
            {"name": "Club Smash", "to_hit_bonus": 6, "damage": 12, "vs": "pd"},
            {"name": "Headbutt", "to_hit_bonus": 6, "damage": 8, "vs": "pd",
             "effect": {"name": "stunned", "chance": 0.15}},
        ],
        "special": {"name": "bloodthirsty", "threshold": 0.5, "bonus_damage": 3},
        "xp": 45, "galleons": 12, "token_chance": 0.35,
    },
    "slytherin_rival": {
        "name": "Slytherin Dueling Rival",
        "tier": "average",
        "level": 3, "hp": 45, "mana": 35,
        "pd": 13, "md": 15, "initiative_bonus": 5,
        "attacks": [
            {"name": "Flipendo", "to_hit_bonus": 7, "damage": 10, "vs": "md"},
            {"name": "Expelliarmus", "to_hit_bonus": 7, "damage": 5, "vs": "md",
             "effect": {"name": "disarmed", "chance": 1.0}},
        ],
        "special": {"name": "tactical"},
        "xp": 50, "galleons": 15, "token_chance": 0.40,
    },
    "acromantula_hatchling": {
        "name": "Acromantula Hatchling",
        "tier": "average",
        "level": 3, "hp": 55, "mana": 10,
        "pd": 15, "md": 12, "initiative_bonus": 3,
        "attacks": [
            {"name": "Venomous Bite", "to_hit_bonus": 6, "damage": 10, "vs": "pd",
             "effect": {"name": "poison", "chance": 1.0, "damage": 4}},
        ],
        "special": {"name": "web_shot", "uses": 1, "agility_penalty": -2, "duration": 2},
        "weak_to": {"fire": 1.5},
        "xp": 48, "galleons": 14, "token_chance": 0.35,
    },

    # --- STRONG ---
    "mountain_troll": {
        "name": "Mountain Troll",
        "tier": "strong",
        "level": 5, "hp": 100, "mana": 0,
        "pd": 16, "md": 12, "initiative_bonus": -1,
        "attacks": [
            {"name": "Club Smash", "to_hit_bonus": 8, "damage": 20, "vs": "pd"},
            {"name": "Boulder Throw", "to_hit_bonus": 6, "damage": 15, "vs": "pd"},
        ],
        "special": {"name": "thick_hide", "physical_reduction": 3},
        "xp": 100, "galleons": 30, "token_chance": 0.50,
    },
    "dark_wizard_apprentice": {
        "name": "Dark Wizard Apprentice",
        "tier": "strong",
        "level": 5, "hp": 80, "mana": 60,
        "pd": 14, "md": 17, "initiative_bonus": 6,
        "attacks": [
            {"name": "Incendio", "to_hit_bonus": 9, "damage": 20, "vs": "md",
             "effect": {"name": "burn", "chance": 1.0}},
            {"name": "Expelliarmus", "to_hit_bonus": 9, "damage": 6, "vs": "md",
             "effect": {"name": "disarmed", "chance": 1.0}},
            {"name": "Sectumsempra", "to_hit_bonus": 9, "damage": 18, "vs": "md",
             "hp_threshold": 0.5, "mana_cost": 20},
        ],
        "special": {"name": "dark_resilience", "resist_spell": "expelliarmus", "chance": 0.5},
        "xp": 120, "galleons": 40, "token_chance": 0.55,
    },
    "werewolf": {
        "name": "Werewolf (Untamed)",
        "tier": "strong",
        "level": 5, "hp": 95, "mana": 0,
        "pd": 17, "md": 14, "initiative_bonus": 7,
        "attacks": [
            {"name": "Claw Swipe", "to_hit_bonus": 9, "damage": 16, "vs": "pd"},
            {"name": "Savage Bite", "to_hit_bonus": 9, "damage": 20, "vs": "pd",
             "hp_threshold": 0.5},
        ],
        "special": {"name": "frenzy", "threshold": 0.30, "extra_attacks": 1, "extra_damage_taken": 5},
        "xp": 110, "galleons": 35, "token_chance": 0.50,
    },

    # --- VERY STRONG ---
    "dementor": {
        "name": "Dementor",
        "tier": "very_strong",
        "level": 8, "hp": 150, "mana": 100,
        "pd": 18, "md": 20, "initiative_bonus": 4,
        "attacks": [
            {"name": "Soul Drain", "to_hit_bonus": 10, "damage": 15, "vs": "md",
             "lifesteal": 10},
            {"name": "Kiss", "to_hit_bonus": 10, "damage": 999, "vs": "md",
             "hp_threshold": 0.20},
        ],
        "special": [
            {"name": "fear_aura", "dc": 16, "mana_drain": 5, "penalty": -2},
            {"name": "non_corporeal", "physical_multiplier": 0.5},
        ],
        "requires": "expecto_patronum",
        "xp": 300, "galleons": 80, "token_chance": 1.0, "rare_token": True,
    },
    "death_eater": {
        "name": "Death Eater",
        "tier": "very_strong",
        "level": 8, "hp": 140, "mana": 120,
        "pd": 16, "md": 19, "initiative_bonus": 7,
        "attacks": [
            {"name": "Avada Kedavra", "to_hit_bonus": 11, "damage": 25, "vs": "md",
             "mana_cost": 40, "execute_threshold": 0.30, "hp_threshold": 0.5},
            {"name": "Crucio", "to_hit_bonus": 11, "damage": 18, "vs": "md",
             "mana_cost": 20, "effect": {"name": "stunned", "chance": 1.0}},
            {"name": "Incendio", "to_hit_bonus": 11, "damage": 22, "vs": "md",
             "mana_cost": 18, "effect": {"name": "burn", "chance": 1.0}},
        ],
        "special": {"name": "dark_mark", "summon": "dark_wizard_apprentice",
                    "summon_hp_pct": 0.5, "threshold": 0.5, "uses": 1},
        "xp": 350, "galleons": 100, "token_chance": 1.0, "rare_token": True,
    },
    "basilisk": {
        "name": "Basilisk",
        "tier": "very_strong",
        "level": 10, "hp": 200, "mana": 50,
        "pd": 19, "md": 18, "initiative_bonus": 5,
        "attacks": [
            {"name": "Bite", "to_hit_bonus": 12, "damage": 30, "vs": "pd",
             "effect": {"name": "poison", "chance": 1.0, "damage": 8}},
            {"name": "Tail Swipe", "to_hit_bonus": 10, "damage": 20, "vs": "pd",
             "effect": {"name": "stunned", "chance": 1.0}},
            {"name": "Petrifying Gaze", "to_hit_bonus": 12, "damage": 0, "vs": "md",
             "save": {"attr": "brawn", "dc": 18},
             "effect": {"name": "petrified", "chance": 1.0}},
        ],
        "special": {"name": "giant_serpent", "immune": ["poison"], "resist": {"fire": 0.5}},
        "xp": 400, "galleons": 120, "token_chance": 1.0, "rare_token": True, "rare_token_count": 2,
    },
}

# ============================================================
# WAND TABLES
# ============================================================

WAND_WOOD_BONUS = {
    "holly":   "control",
    "oak":     "brawn",
    "willow":  "willpower",
    "vine":    "perception",
    "hazel":   "intellect",
    "ash":     "agility",
    "birch":   "presence",
    "redwood": "power",
}

WAND_CORES = {
    "phoenix_feather": {
        "name": "Phoenix Feather",
        "bonus_mana": 3,
        "hp_regen": 1,
    },
    "dragon_heartstring": {
        "name": "Dragon Heartstring",
        "damage_modifier": 2,
        "fumble_self_damage": 3,
    },
    "unicorn_hair": {
        "name": "Unicorn Hair",
        "accuracy_modifier": 2,
        "damage_modifier": -1,
    },
    "thestral_tail_hair": {
        "name": "Thestral Tail Hair",
        "execute_bonus": 2,
    },
}

WAND_BOND_LEVELS = [
    (0,   {}),
    (5,   {"spell_accuracy": 1}),
    (10,  {"spell_damage": 1}),
    (20,  {"control": 1}),
    (50,  {"mana_discount": 1}),
    (70,  {"power": 1}),
    (85,  {"spell_accuracy": 1, "spell_damage": 1}),
    (100, {"control": 1, "power": 1}),
]

BOND_NAMES = [
    "New", "Familiar", "Attuned", "Bonded",
    "Loyal", "Devoted", "Inseparable", "Legendary",
]

# ============================================================
# WAND UPGRADES  (permanent, bought with Galleons)
# ============================================================

WAND_UPGRADES = {
    "wand_polish": {
        "name": "Wand Polish",
        "effect": {"spell_accuracy": 1},
        "cost": 30,
        "description": "+1 Spell Accuracy.",
    },
    "core_reinforcement": {
        "name": "Core Reinforcement",
        "effect": {"mana": 2},
        "cost": 40,
        "description": "+2 Mana.",
    },
    "grip_charm": {
        "name": "Grip Charm",
        "effect": {"mana_discount": 1},
        "cost": 80,
        "description": "-1 Mana cost on all spells (min 1).",
    },
    "wand_mastery_1": {
        "name": "Wand Mastery I",
        "effect": {"attr": {"control": 1}},
        "cost": 120,
        "description": "+1 Control.",
    },
    "wand_mastery_2": {
        "name": "Wand Mastery II",
        "effect": {"attr": {"power": 1}},
        "cost": 200,
        "description": "+1 Power.",
    },
}

# ============================================================
# HOUSES
# ============================================================

HOUSES = {
    "gryffindor": {
        "name": "Gryffindor",
        "colors": "Scarlet and Gold",
        "motto": "Their daring, nerve, and chivalry set Gryffindors apart.",
        "attr_bonus": {"brawn": 1, "willpower": 1},
        "passive": "clutch",
        # clutch: below 20% HP → +3 spell damage, +2 attack rolls
        "passive_data": {"hp_threshold": 0.20, "damage": 3, "attack": 2},
    },
    "hufflepuff": {
        "name": "Hufflepuff",
        "colors": "Yellow and Black",
        "motto": "Those patient Hufflepuffs are true and unafraid of toil.",
        "attr_bonus": {"willpower": 1, "presence": 1},
        "passive": "discovery_hp",
        # +2 max HP per new enemy species defeated
        "passive_data": {"hp_per_species": 2},
    },
    "ravenclaw": {
        "name": "Ravenclaw",
        "colors": "Blue and Bronze",
        "motto": "Wit beyond measure is man's greatest treasure.",
        "attr_bonus": {"intellect": 1, "perception": 1},
        "passive": "streak_token",
        # +1 token every 4th consecutive win
        "passive_data": {"streak_interval": 4, "tokens": 1},
    },
    "slytherin": {
        "name": "Slytherin",
        "colors": "Green and Silver",
        "motto": "Those cunning folk use any means to achieve their ends.",
        "attr_bonus": {"power": 1, "control": 1},
        "passive": "trader",
        # -20% buy, +10% sell
        "passive_data": {"buy_multiplier": 0.80, "sell_multiplier": 1.10},
    },
}

HOUSE_KEYS = list(HOUSES.keys())


# ============================================================
# WIN STREAK
# ============================================================

STREAK_BONUS_PER_WIN = 0.15
STREAK_CAP = 5

# ============================================================
# ENEMY TIER -> LIST  (for picking random enemies)
# ============================================================

ENEMIES_BY_TIER = {}
for _key, _enemy in ENEMIES.items():
    _tier = _enemy["tier"]
    ENEMIES_BY_TIER.setdefault(_tier, []).append(_key)

if __name__ == "__main__":
    print(f"Spells: {len(SPELLS)}")
    print(f"Enemies: {len(ENEMIES)}")
    print(f"Tiers: {list(ENEMIES_BY_TIER.keys())}")
    for tier, keys in ENEMIES_BY_TIER.items():
        print(f"  {tier}: {len(keys)} enemies")