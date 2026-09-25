# HARRY POTTER WIZARD RPG — DESIGN BLUEPRINT

> Single source of truth. Mechanics and structure only.
> No full tables, no per-item numbers — those live in `Data.py`.

---

## 1. CORE CONCEPT

Turn-based wizard RPG set in Hogwarts. Fight duels, creatures, and dark
wizards. Level up, learn spells, upgrade your wand, and progress through
seven school years.

**Loop:**
Fight → earn XP / Galleons / Spell Tokens → level up and shop →
fight stronger enemies → boss gate → next year.

**Rules:**
- Non-lethal for students (defeat = hospital wing, no permadeath).
- Replayable, dramatic, d20-driven.
- Two front ends: Tkinter GUI (`GUI.py`) and terminal (`main.py`).
- Same game logic for both. Front ends are cosmetic only.

---

## 2. ATTRIBUTES (8)

| Attribute  | Covers                              |
|------------|-------------------------------------|
| Brawn      | Strength, endurance, HP             |
| Agility    | Speed, reflexes, initiative, PD     |
| Intellect  | Memory, logic, spell learning, mana |
| Perception | Awareness, aim, accuracy            |
| Willpower  | Focus, courage, mental defense, HP  |
| Presence   | Charm, leadership, persuasion       |
| Power      | Raw magical force, spell damage     |
| Control    | Precision, spell accuracy, mana     |

**Scale:** 1–10 in Year 1. Cap grows per year (+2 per year).
**Layers:** Effective = Base + Permanent mods + Temporary mods.
Permanent mods: wand wood, wand core, bond bonuses, wand upgrades, gear, house.

---

## 3. DERIVED STATS

| Stat             | Formula                                                    |
|------------------|------------------------------------------------------------|
| HP               | 20 + (Brawn×3) + (Willpower×2) + (Level×5) + house/bond    |
| Mana             | 20 + (Power×2) + (Control×2) + Intellect + (Level×3) + wand |
| Physical Defense | 8 + Agility + Brawn + gear + bond                          |
| Magical Defense  | 8 + Willpower + Control + bond                             |
| Initiative       | d20 + Agility + Perception + bond                          |
| Spell Accuracy   | Control + Perception + wand + bond + upgrades + house      |
| Spell Damage     | Spell base + scaling attr + wand + bond + house            |

---

## 4. COMBAT (d20 SYSTEM)

**Attack:** d20 + Spell Accuracy vs enemy Magical Defense
**Damage:** spell base + scaling attribute + wand bonus
**Mana regen:** +2 per turn
**Actions per turn:** 1 (spell / item / flee)

| Roll       | Result                   |
|------------|--------------------------|
| Natural 20 | Double damage            |
| Natural 1  | Miss + lose 3 extra mana |

**Multi-enemy:** supports 1+ enemies. Player picks target when 2+ alive.
Summons (Death Eater, Aragog) join at end of enemy phase.

**Status effects:** burn, poison, infected, disarmed, stunned, petrified,
weakened, shield. Sources live in `Data.py`.

---

## 5. SPELLS

- **5 starter spells:** Flipendo, Expelliarmus, Protego, Incendio, Episkey.
- Each spell has: mana cost, base damage/heal, scaling attribute, effect.
- Exact values live in `Data.py → SPELLS`.
- **Spell cap grows per year:** 5 → 7 → 9 → ... (Year 1 → 7).
- **Learning is permanent.** No respec. No refunds.
- Roadmap: +5 spells per year (up to 20 total).

---

## 6. LEVELING & XP

- **XP curve:** 100 × current level (continues across years).
- **On level up:** +1 Attribute Point, +5 HP, +3 Mana, full restore.
- **Attribute cap per year:** 10 / 12 / 14 / 16 / 18 / 20 / 22.
- **Level range per year:** 1–10, 11–20, 21–30, ... 61–70.
- **Level gates enemies.** Trying a tier above your level will wreck you.

**Post-battle prompts (in order):**
1. Spend attribute points (or save for later)
2. Unlock a new Bond Focus (at Level 3/5/7)
3. Boss gate (when at finale level + not yet beaten)

---

## 7. HOUSES

Player is sorted randomly (with one reroll). Houses give a fixed
attribute bonus and a unique passive. House bonuses **stack each year**.

| House      | Attribute Bonus             | Passive                                |
|------------|-----------------------------|----------------------------------------|
| Gryffindor | +1 Brawn, +1 Willpower      | Below 30% HP: +3 dmg, +2 to hit        |
| Hufflepuff | +1 Willpower, +1 Presence   | +2 max HP per new enemy species        |
| Ravenclaw  | +1 Intellect, +1 Perception | +1 token every 4 consecutive wins      |
| Slytherin  | +1 Power, +1 Control        | −20% shop buy prices, +10% sell prices |

Exact values live in `Data.py → HOUSES`.

---

## 8. WIN STREAK

Consecutive wins without resting, losing, or fleeing.
Applies to **both XP and Galleons** from each victory.

- +15% per win, cap +75% at 5+ wins.
- Resets on: rest, loss, flee.
- Does NOT reset on: shopping, gear changes, saving.

**Training Dummy and similar practice enemies** don't count toward streak
or bond, and drop no tokens.

---

## 9. ENEMIES

**6 tiers:** Very Weak → Weak → Average → Strong → Very Strong → Boss.

- Each tier has 3–7 enemies.
- Every enemy has a unique mechanic and a weakness.
- Stronger enemies have more options (not just more HP).
- **Every enemy has a `hint`** shown before the fight.

**Boss tier** is excluded from random encounters. Triggered at the year's
finale level (Level 11 for Year 1). Bosses cannot be fled.

Full roster and stats: `Data.py → ENEMIES`. (dynamically maps to `ENEMIES_BY_TIER`).

---

## 10. WAND SYSTEM

The wand has **three parts**:

| Part       | Effect                                  | Options |
|------------|-----------------------------------------|---------|
| Wood       | +1 to one attribute                     | 8       |
| Core       | Unique passive effect                   | 4       |
| Bond Focus | Determines the bond buff curve          | 4       |

**Bond Foci:** Warrior / Scholar / Warden / Trickster.
Same level curve (5 / 10 / 20 / 50 / 70 / 85 / 100 wins) but different
bonuses. Each focus tracks wins **separately**.

- Player picks 1 focus at start.
- New foci unlock at Level 3, 5, 7 (player picks order).
- Switching focus preserves old progress.
- Bond bonuses from all reached tiers **stack**.

**Changing parts (fees):** Wood 25 G / Core 25 G / Focus 40 G.
**Wand upgrades are permanent** — never lost on swap.

Details: `Data.py → BOND_FOCI`, `WAND_CORES`, `WAND_WOOD_BONUS`.

---

## 11. ITEMS, POTIONS, GEAR

**Two currencies:**
- **Spell Tokens** → learn spells (permanent)
- **Galleons** → potions, items, gear, wand upgrades (consumable + upgrades)

**Categories:**
- **Potions** — heal, restore mana, cure statuses, temporary buffs.
  Using any item costs your turn in combat.
- **Combat items** — throwables that damage, debuff, or crowd-control.
- **Gear** — 6 slots (Body, Hands, Feet, Ring, Amulet, Wand).
  Small bonuses only (+1 or +2 to one stat).
- **Wand upgrades** — permanent, one-time purchases from the Wand Smith.

**Inventory:** potions stack to 5, items to 10, gear unlimited.
Selling returns 50% of buy price.

Full catalog: `Data.py → POTIONS`, `COMBAT_ITEMS`, `GEAR`, `WAND_UPGRADES`.

---

## 12. SHOPS

Three shops in Diagon Alley:

1. **Spell Token Shop** — spend tokens to learn spells.
2. **Apothecary** — buy potions, items, gear.
3. **Wand Smith** — permanent wand upgrades.

Unlocked at Level 2. Full stock in `Data.py`.

---

## 13. YEAR PROGRESSION

| Year | Levels | Attr Cap | Spell Cap | Boss Gate        |
|------|--------|----------|-----------|------------------|
| 1    | 1–10   | 10       | 5         | Aragog, Voldemort |
| 2    | 11–20  | 12       | 7         | TBD              |
| 3    | 21–30  | 14       | 9         | TBD              |
| 4+   | …      | …        | …         | TBD              |

**Year transition (after bosses):**
- +5 Attribute Points
- +1 to each of the house's two attributes
- New house buff stacks on top of the old
- New content unlocks (enemies, spells, areas)
- Streak resets
- **Everything else carries over:** spells, wand, gear, money, tokens,
  battle log, discovered species

**Boss trigger:** player reaches the year's finale level (Level 11 for
Year 1) and hasn't beaten the boss pair yet. Gauntlet runs both bosses
in sequence. No retreat. Loss = 50% gold penalty + hospital wing.

---

## 14. UI / FRONT ENDS

**Terminal client (`main.py`)** — hub menu with:
Battle Arena · Diagon Alley · Status · Rest · Help · Save · Exit.
Submenus handle fight, shops, wand/gear, inventory, character sheet,
recent actions, and attribute/focus prompts.

**GUI client (`GUI.py`)** — Tkinter. Same game rules, richer UI:
dashboard, interactive combat view, spellbook, shops, wand panel,
character sheet, save/load. Launched via `run_gui.bat` (Windows).

Both front ends share Player, Enemy, Spells, Items, Shop, Combat.
No game logic lives in either front end.

---

## 15. HELP SYSTEM

"How to Play" screen (hub option or first-time prompt) explaining:
core loop, attributes, derived stats, combat, spells, houses, win streak,
wand & bond foci, enemy hints, tips.

Single function in `main.py → show_help()`.

---

## 16. FILE STRUCTURE
wizard_rpg/
├── agent.md # this blueprint
├── readme.md # player-facing readme
├── GUI.py # Tkinter front end
├── run_gui.bat # Windows GUI launcher
├── assets/houses/ # house crest artwork
├── Data.py # all constants (attrs, spells, enemies, items, houses)
├── Player.py # Player class
├── Enemy.py # Enemy class
├── Spells.py # spell casting & resolution
├── Combat.py # battle loop
├── Items.py # inventory, potions, gear
├── Shop.py # shops + selling
├── main.py # terminal entry point
└── savegame.json # player save (gitignored)

---

## 17. SAVE SYSTEM

- JSON save file (`savegame.json`) with a `.bak` fallback.
- Save format is **versioned** (`"version": 1`).
- Corrupt main save → auto-recovers from `.bak`.
- Save from newer version → refuses to load.

---

## 18. DEFERRED / ROADMAP

- Classes & festivals (XP events + temp modifiers)
- Year 2+ content (spells, enemies, areas)
- Story, quests, and areas
- Multi-slot saves
- First-clear XP bonus + diminishing returns
- Lucky Charm reroll wiring
- Fire Protection potion resistance wiring
- FastAPI web port

---

## 19. DESIGN RULES (LOCKED)

1. Combat uses d20 + stats.
2. 8 attributes, small numbers, growth per year.
3. Spells are permanent once learned.
4. Wand parts and Bond Foci are swappable for a small fee.
5. Wand upgrades are never lost.
6. Streak rewards risk; resting costs it.
7. Every enemy has a mechanic and a weakness.
8. Bosses gate year transitions and cannot be fled.
9. Non-lethal for students; no permadeath.
10. Two front ends, one game engine.

---

*End. Keep this document lean. Details live in code.*