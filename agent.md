# HARRY POTTER WIZARD RPG — DESIGN DOC

> Single source of truth. Update after every design session.

---

## 1. CORE CONCEPT

Wizard-school RPG. Loop:
Fight → earn XP, Galleons, Spell Tokens
→ level up, buy gear, learn spells
→ fight stronger enemies

- Tone: dramatic, swingy, replayable
- Non-lethal duels for students
- No permanent death (lose = hospital wing)
- Terminal-based (Python); FastAPI port possible later

---

## 2. ATTRIBUTES (8)

| Attribute  | Covers                           |
|------------|----------------------------------|
| Brawn      | Strength, endurance              |
| Agility    | Speed, reflexes                  |
| Intellect  | Memory, logic, theory            |
| Perception | Awareness, aim, insight          |
| Willpower  | Focus, courage, mental fortitude |
| Presence   | Charm, command, deception        |
| Power      | Raw magical force, mana          |
| Control    | Precision, spell shaping         |

**Scale:** 1–10. Student = 2–4, talented = 5, prodigy = 6–8.

**Layers:** Effective = Base + Permanent mods + Temporary mods

Permanent mods include: wand wood, wand bond, wand upgrades, gear, house bonus.

---

## 3. DERIVED STATS

| Stat             | Formula                                                       |
|------------------|---------------------------------------------------------------|
| HP               | 20 + (Brawn×3) + (Willpower×2) + (Level×5) + House bonus      |
| Mana             | 20 + (Power×2) + (Control×2) + (Level×3) + Wand/upgrade bonus |
| Physical Defense | 8 + Agility + Brawn + Gear                                    |
| Magical Defense  | 8 + Willpower + Control                                       |
| Initiative       | d20 + Agility + Perception                                    |
| Spell Accuracy   | Control + Perception + Wand + Bond + Upgrades                 |
| Spell Potency    | Power + Intellect                                             |

---

## 4. COMBAT (LOCKED — d20)

**Attack:** `d20 + Control + Perception (+ house bonus)` vs enemy Magical Defense
**Damage:** Spell Base + Scaling Attribute + Wand bonus + House bonus
**Mana regen:** +2 per turn
**Actions per turn:** 1 (spell / item / flee)

| Roll       | Result                   |
|------------|--------------------------|
| Natural 20 | Double damage            |
| Natural 1  | Miss + lose 3 extra mana |

---

## 5. STARTER SPELLS (5)

| Spell        | Mana | Effect                                    | Scaling    | Token Cost |
|--------------|------|-------------------------------------------|------------|------------|
| Flipendo     | 5    | 6 dmg + enemy -2 next attack              | Power      | 1          |
| Expelliarmus | 10   | 3 dmg + enemy loses next turn             | Control    | 3          |
| Protego      | 8    | Block next spell OR -60% damage this turn | —          | 4          |
| Incendio     | 18   | 16 dmg + burn 3/turn (3 turns)            | Power      | 5          |
| Episkey      | 12   | Heal 10                                   | Int + Will | 3          |

**Total to learn all 5:** 16 tokens

**Roadmap:** +5 spells per "year" (Year 2 → 10 total, Year 3 → 15, Year 4–5 → 20).

---

## 6. REWARDS & LEVELING

| Reward       | Use                        |
|--------------|----------------------------|
| XP           | Level up                   |
| Galleons     | Shop (potions, gear, wand) |
| Spell Tokens | Learn spells               |

**XP needed = 100 × current level**
**On level up:** +1 Attribute Point, +5 HP, +3 Mana, full restore

### Leveling Table

| Level  | XP to Next | Total XP | Total Attr Pts | HP Bonus | Mana Bonus |
|--------|------------|----------|----------------|----------|------------|
| **1**  | 100        | 0        | 0              | +5       | +3         |
| **2**  | 200        | 100      | 1              | +10      | +6         |
| **3**  | 300        | 300      | 2              | +15      | +9         |
| **4**  | 400        | 600      | 3              | +20      | +12        |
| **5**  | 500        | 1000     | 4              | +25      | +15        |
| **6**  | 600        | 1500     | 5              | +30      | +18        |
| **7**  | 700        | 2100     | 6              | +35      | +21        |
| **8**  | 800        | 2800     | 7              | +40      | +24        |
| **9**  | 900        | 3600     | 8              | +45      | +27        |
| **10** | —          | 4500     | 9              | +50      | +30        |

**Max level = 10** for now. Extend later.

### Level Milestones

| Level | Unlock                                |
|-------|---------------------------------------|
| 1     | Start. Know Flipendo. 2 Spell Tokens. |
| 2     | Shop unlocks (spells + apothecary)    |
| 3     | Weak-tier enemies available           |
| 4     | —                                     |
| 5     | Average-tier enemies. Wand upgrades.  |
| 6     | —                                     |
| 7     | Strong-tier enemies                   |
| 8     | Very Strong-tier enemies              |
| 9     | —                                     |
| 10    | Max level. Endgame.                   |

### Leveling Rules (Locked)

1. **No respec.** Attribute Points are permanent.
2. **+1 Attribute Point per level** (not multiple).
3. **Max level 10** for now.
4. **No dead levels.** Every level gives attr point + HP + Mana.
5. **Level gates enemies.** Can try early, will get wrecked.

### Starting Loadout (Level 1)

| Item         | Amount            |
|--------------|-------------------|
| Flipendo     | Known (free)      |
| Spell Tokens | 2                 |
| Galleons     | 0                 |
| Potions      | 1 Healing Draught |

### Reward Balance Rules

- First kill of enemy type: double XP / guaranteed token
- Repeat weak enemies: diminishing XP
- Level gates for strong areas
- Losing = lose 25% Galleons, wake in hospital wing

---

## 6.5 HOUSES & WIN STREAK

### House Selection

- After name entry, player is sorted into a **random house**.
- Player gets **1 reroll** — one chance to reject and take the new random house.
- Reroll is final.

### House Bonuses

| House          | Attribute Bonus             | Passive Bonus                                      |
|----------------|-----------------------------|----------------------------------------------------|
| **Gryffindor** | +1 Brawn, +1 Willpower      | Below 20% HP: +3 spell damage, +2 attack rolls     |
| **Hufflepuff** | +1 Willpower, +1 Presence   | +2 permanent max HP per new enemy species defeated |
| **Ravenclaw**  | +1 Intellect, +1 Perception | +1 Spell Token every 4th consecutive win           |
| **Slytherin**  | +1 Power, +1 Control        | -20% shop buy prices, +10% sell prices             |

### Win Streak

- Consecutive wins **without resting, losing, or fleeing**.
- Applies to **both XP and Galleons** from that victory.
- Multiplier based on streak **before** the current win:

| Wins Before | Multiplier  |
|-------------|-------------|
| 0           | ×1.00       |
| 1           | ×1.15       |
| 2           | ×1.30       |
| 3           | ×1.45       |
| 4           | ×1.60       |
| 5+          | ×1.75 (cap) |

**Streak resets on:** rest, loss, flee.
**Streak does NOT reset on:** shopping, equipping gear, using items, saving.

---

## 7. ENEMIES — 5 TIERS, 15 TOTAL

| Tier        | Enemy                  | Lvl | HP  | MD | PD | XP  | Gal | Token% |
|-------------|------------------------|-----|-----|----|----|-----|-----|--------|
| Very Weak   | Training Dummy         | 1   | 12  | 8  | 8  | 5   | 1   | 5%     |
|             | Cornish Pixie          | 1   | 18  | 10 | 12 | 10  | 2   | 10%    |
|             | Garden Gnome           | 1   | 20  | 9  | 10 | 8   | 1   | 8%     |
| Weak        | Giant Rat              | 2   | 30  | 11 | 12 | 22  | 5   | 20%    |
|             | Doxie                  | 2   | 24  | 12 | 14 | 25  | 6   | 20%    |
|             | Hinkypunk              | 2   | 28  | 13 | 11 | 25  | 6   | 20%    |
| Average     | Red Cap                | 3   | 50  | 13 | 14 | 45  | 12  | 35%    |
|             | Slytherin Rival        | 3   | 45  | 15 | 13 | 50  | 15  | 40%    |
|             | Acromantula Hatchling  | 3   | 55  | 12 | 15 | 48  | 14  | 35%    |
| Strong      | Mountain Troll         | 5   | 100 | 12 | 16 | 100 | 30  | 50%    |
|             | Dark Wizard Apprentice | 5   | 80  | 17 | 14 | 120 | 40  | 55%    |
|             | Werewolf               | 5   | 95  | 14 | 17 | 110 | 35  | 50%    |
| Very Strong | Dementor               | 8   | 150 | 20 | 18 | 300 | 80  | 100%   |
|             | Death Eater            | 8   | 140 | 19 | 16 | 350 | 100 | 100%   |
|             | Basilisk               | 10  | 200 | 18 | 19 | 400 | 120 | 100%   |

**Key enemy mechanics:**
- **Cornish Pixie** — 25% auto-dodge
- **Garden Gnome** — half damage from Flipendo
- **Giant Rat** — Infected (-2 HP/turn, 2 turns)
- **Doxie** — Tiny (-2 to hit it)
- **Hinkypunk** — Lure (Willpower check or lose turn)
- **Red Cap** — +3 dmg below 50% HP
- **Slytherin Rival** — uses player spells, tactical
- **Acromantula** — Web Shot (-2 Agility), weak to fire (+50%)
- **Mountain Troll** — Thick Hide (-3 physical dmg)
- **Dark Wizard** — resists Expelliarmus 50%
- **Werewolf** — Frenzy below 30% (2 attacks, +5 dmg taken)
- **Dementor** — non-corporeal (physical = half dmg), needs Patronus
- **Death Eater** — Dark Mark summons ally at 50% HP
- **Basilisk** — Petrifying Gaze, immune poison, fire-resistant

**Design rules:**
1. Every enemy has a unique mechanic
2. Every enemy has a weakness
3. Stronger enemies have more options (not just more HP)
4. Student duels end in surrender, not death
5. Bosses gate progress (Dementor needs Patronus)

---

## 8. STATUS EFFECTS

| Status             | Effect               | Duration  |
|--------------------|----------------------|-----------|
| Burn               | 3 dmg/turn           | 3 turns   |
| Poison             | 2–8 dmg/turn         | 2–3 turns |
| Infected           | -2 HP/turn           | 2 turns   |
| Disarmed / Stunned | Lose next turn       | 1 turn    |
| Petrified          | Cannot act           | 2 turns   |
| Weakened           | -2 attack rolls      | 1 turn    |
| Shield             | -60% incoming damage | 1 hit     |

---

## 9. SPELL TOKEN SHOP

- **Currency:** Spell Tokens (from battles)
- **Unlocks at:** Level 2
- **Learning is permanent.** No respec, no refunds.
- Once learned, spell is always available in combat.
- Future Year 2+ spells appear as `???` greyed out.

| Spell        | Type    | Cost |
|--------------|---------|------|
| Flipendo     | Attack  | 1    |
| Expelliarmus | Control | 3    |
| Episkey      | Support | 3    |
| Protego      | Defense | 4    |
| Incendio     | Attack  | 5    |

**Total to learn all 5:** 16 tokens

---

## 10. ITEMS & POTIONS

### Two Currencies

| Currency     | Shop                    | Buys                                |
|--------------|-------------------------|-------------------------------------|
| Spell Tokens | Spell Shop              | New spells (permanent)              |
| Galleons     | Apothecary / Wand Smith | Potions, items, gear, wand upgrades |

### Potions (consumed — costs a turn in combat)

| Potion                 | Effect                       | Cost |
|------------------------|------------------------------|------|
| Healing Draught        | Restore 25 HP                | 10 G |
| Wiggenweld Potion      | Restore 50 HP                | 25 G |
| Mana Elixir            | Restore 20 Mana              | 15 G |
| Antidote               | Remove poison/infected       | 10 G |
| Burn Salve             | Remove burn                  | 8 G  |
| Invigoration Draught   | +2 Power for 3 turns         | 20 G |
| Focusing Potion        | +2 Control for 3 turns       | 20 G |
| Draught of Peace       | +2 Willpower for 3 turns     | 20 G |
| Fire Protection Potion | -50% fire damage for 3 turns | 18 G |

### Combat Items (consumed)

| Item                     | Effect                      | Cost |
|--------------------------|-----------------------------|------|
| Chinese Chomping Cabbage | 12 dmg, ignores defense     | 15 G |
| Dungbomb                 | Enemy loses next turn (50%) | 10 G |
| Instant Darkness Powder  | Enemy -4 next attack        | 12 G |
| Fanged Flyer             | 8 dmg, guaranteed hit       | 18 G |
| Stink Pellet             | Enemy flees if below 25% HP | 8 G  |

### Gear (equipped, 6 slots)

Slots: **Body, Hands, Feet, Ring, Amulet, Wand**

| Gear              | Slot   | Effect                          | Cost  |
|-------------------|--------|---------------------------------|-------|
| Student Robes     | Body   | +1 Physical Defense             | 20 G  |
| Dueling Robes     | Body   | +2 Physical Defense             | 50 G  |
| Dragonhide Gloves | Hands  | +1 Power                        | 60 G  |
| Quickstep Boots   | Feet   | +1 Agility                      | 40 G  |
| Focusing Ring     | Ring   | +1 Control                      | 80 G  |
| Lucky Charm       | Amulet | Reroll one natural 1 per battle | 100 G |

### Wand Upgrades (permanent, one-time)

| Upgrade            | Effect                             | Cost  |
|--------------------|------------------------------------|-------|
| Wand Polish        | +1 Spell Accuracy                  | 30 G  |
| Core Reinforcement | +2 Mana                            | 40 G  |
| Grip Charm         | -1 Mana cost on all spells (min 1) | 80 G  |
| Wand Mastery I     | +1 Control                         | 120 G |
| Wand Mastery II    | +1 Power                           | 200 G |

### Inventory Rules

| Rule               | Detail                                    |
|--------------------|-------------------------------------------|
| Potions stack      | Up to 5 of each type                      |
| Combat items stack | Up to 10 of each                          |
| Gear slots         | 6 (Body, Hands, Feet, Ring, Amulet, Wand) |
| Selling            | 50% of buy price (Slytherin: +10%)        |
| Weight limit       | None                                      |
| Shop unlock        | Level 2                                   |

### Economy Check

| Purchase        | Cost  | Kills (Average tier) |
|-----------------|-------|----------------------|
| Healing Draught | 10 G  | ~1                   |
| Student Robes   | 20 G  | ~2                   |
| Wand Polish     | 30 G  | ~2–3                 |
| Wand Mastery I  | 120 G | ~8–10                |

---

## 11. WAND SYSTEM

### Overview

Three parts:
1. **Wood** → +1 attribute
2. **Core** → unique passive effect
3. **Bond** → grows with use

### Wood (Pick One)

| Wood    | Bonus         |
|---------|---------------|
| Holly   | +1 Control    |
| Oak     | +1 Brawn      |
| Willow  | +1 Willpower  |
| Vine    | +1 Perception |
| Hazel   | +1 Intellect  |
| Ash     | +1 Agility    |
| Birch   | +1 Presence   |
| Redwood | +1 Power      |

### Core (Pick One)

| Core               | Effect                                          |
|--------------------|-------------------------------------------------|
| Phoenix Feather    | +3 Mana, +1 HP regen per turn                   |
| Dragon Heartstring | +2 Spell Damage, natural 1 causes 3 self-damage |
| Unicorn Hair       | +2 Spell Accuracy, -1 Spell Damage              |
| Thestral Tail Hair | +2 Damage vs enemies below 50% HP               |

### Bond Levels (grows with battles won)

| Bond            | Wins | Bonus                              |
|-----------------|------|------------------------------------|
| 1 (New)         | 0    | —                                  |
| 2 (Familiar)    | 5    | +1 Spell Accuracy                  |
| 3 (Attuned)     | 10   | +1 Spell Damage                    |
| 4 (Bonded)      | 20   | +1 Control                         |
| 5 (Loyal)       | 50   | -1 Mana cost (min 1)               |
| 6 (Devoted)     | 70   | +1 Power                           |
| 7 (Inseparable) | 85   | +1 Spell Accuracy, +1 Spell Damage |
| 8 (Legendary)   | 100  | +1 Control, +1 Power               |

**Bond is tied to that wand.** Swapping resets bond to 1.

### Player Picks Their Own Wand

At Ollivander's, player chooses from 8 combinations of wood + core.

### Swapping Wands

| Rule      | Detail                      |
|-----------|-----------------------------|
| Slot      | Wand is 1 of 6 gear slots   |
| Swapping  | Free, outside of combat     |
| Bond      | Resets to 1 on the new wand |
| Old wand  | Lost (for now)              |
| Best wand | Depends on build            |

### Design Rules

1. Wood = +1 attribute.
2. Core = special passive.
3. Bond grows with use.
4. Swapping resets bond.
5. Length/flexibility = flavor only.
6. No objectively the best wand.

---

## 12. HELP SYSTEM

A "How to Play" screen accessible from:
- Main hub menu (option 6)
- First-time prompt after character creation

Explains:
- Core loop
- Attributes
- Derived stats
- Combat rules
- Spells
- Win streak
- Houses
- Tips

Single function in `main.py` → `show_help()`.

---

## 13. DEFERRED FOR LATER

- Classes & festivals (XP + temp modifiers + story)
- Full 20-spell list (Year 2+)
- Multi-enemy combat (Death Eater summons, group fights)
- Story / quests / areas
- FastAPI web version
- Save/load multiple slots
- Lucky Charm reroll wiring
- Fire Protection potion resistance wiring
- First-clear XP bonus + diminishing returns wiring

---

## 14. DESIGN DECISIONS LOG

| Decision             | Choice                               | Why                                  |
|----------------------|--------------------------------------|--------------------------------------|
| Randomness           | d20 + stats                          | Swingy, exciting, replayable         |
| 8 attributes         | Physical / mental / social / magical | Covers all playstyles                |
| Cap at 10            | Small numbers                        | Meaningful, easy to balance          |
| Mana regen +2/turn   | —                                    | Prevents spell spam                  |
| 1 action/turn        | —                                    | Simple, tactical                     |
| 5 starter spells     | Complete toolkit                     | Room to grow                         |
| Generic spell tokens | Any token = any spell                | Simple, flexible                     |
| Classes/festivals    | Deferred                             | Keep scope small                     |
| Starting tokens      | 2                                    | Medium pace                          |
| HP/Mana per level    | +5 / +3                              | Keeps combat tense                   |
| No respec            | Permanent choices                    | Weight to decisions                  |
| Potions cost a turn  | Yes                                  | Real tradeoff in combat              |
| Gear slots           | 6                                    | Enough depth, not overwhelming       |
| Selling items        | 50% of buy                           | Inventory management                 |
| Shop unlock          | Level 2                              | Let player gather money first        |
| Wand wood bonus      | +1 attribute                         | Simple, clear                        |
| Wand core            | Unique passive                       | Wand personality                     |
| Wand bond            | 8 levels                             | Slow, meaningful progression         |
| House selection      | Random + 1 reroll                    | Magic-hat feel, some agency          |
| Gryffindor bonus     | Clutch (below 20% HP)                | Rewards risky, brave play            |
| Hufflepuff bonus     | +2 HP per species                    | Rewards exploration                  |
| Ravenclaw bonus      | +1 token per 4-streak                | Rewards consistency                  |
| Slytherin bonus      | -20% buy / +10% sell                 | Cunning trader                       |
| Win streak bonus     | +15% per win, cap +75%               | Rewards risk, scales with difficulty |
| Streak resets        | Rest / loss / flee                   | Rest becomes a real cost             |
| Help system          | Hub menu + first-time prompt         | Accessibility                        |

---

## 15. FILE STRUCTURE
wizard_rpg/
├── agent.md # this design doc
├── readme.md # player-facing readme
├── Data.py # all constants (attributes, spells, enemies, items, houses)
├── Player.py # Player class
├── Enemy.py # Enemy class
├── Spells.py # Spell casting & resolution
├── Combat.py # Battle loop
├── Items.py # Inventory, potions, gear
├── Shop.py # Spell shop, apothecary, wand smith
└── main.py # Entry point — title, hub, character creation


---

## 16. NEXT STEPS

1. Playtest the current build end-to-end
2. Add first-clear XP bonus + diminishing returns
3. Add classes & festivals system
4. Add Year 2 spells
5. Multi-enemy combat for Death Eater
6. Story / quests / areas

---

## 17. GLOSSARY

- **MD** = Magical Defense
- **PD** = Physical Defense
- **Effective Attr** = Base + Permanent + Temporary
- **Tier** = Enemy difficulty (Very Weak → Very Strong)
- **Bond Level** = Wand's growth stage (1–8)
- **Streak** = Consecutive wins without resting/losing/fleeing
- **Clutch** = Gryffindor's below-20%-HP combat bonus

---

*End. Update after each design session.*