cat > readme.md << 'EOF'
# Hogwarts: A Wizard's Journey

A turn-based RPG set in the Harry Potter universe. Fight duels, creatures,
and dark wizards. Level up, learn spells, upgrade your wand, and rise from a
first-year student to a legendary duelist.

Built in Python. Play through the graphical interface or in the terminal.

---

## Quick Start

### Graphical interface (recommended)

    python GUI.py

On Windows you can also double-click `run_gui.bat`.

The Tkinter interface includes character creation, house sorting, interactive
combat, shops, inventory and gear management, character progression, and
save/load. It uses only the Python standard library.

### Terminal interface

    python main.py

You'll see a title screen. Choose New Game, enter your name, get sorted into a
house, and pick your wand.

That's it. You're a wizard now.

---

## Requirements

- Python 3.8+
- No external libraries. Standard library only.

---

## How to Play

### The Loop

1. Fight enemies to earn XP, Galleons, and Spell Tokens.
2. Level up to gain Attribute Points.
3. Spend tokens at the Spell Shop to learn new spells.
4. Spend Galleons at the Apothecary for potions and gear.
5. Fight stronger enemies and repeat.

### Main Hub

The hub is organized by purpose:

| Option                 | What's inside                                    |
|------------------------|--------------------------------------------------|
| 1. Battle Arena        | Fight enemies, view recent battles, boss gauntlet |
| 2. Diagon Alley        | Shops, wand & gear management                    |
| 3. Status              | Character sheet, inventory, spend points         |
| 4. Rest                | Full HP/Mana restore (resets win streak)         |
| 5. Help                | How-to-play guide                                |
| 6. Save                | Save progress                                    |
| 0. Exit                | Save & quit                                      |

### Attributes (8)

| Attribute   | What it does                  |
|-------------|-------------------------------|
| Brawn       | Physical toughness, HP        |
| Agility     | Initiative, physical defense  |
| Intellect   | Spell learning, mana, healing |
| Perception  | Spell accuracy, danger sense  |
| Willpower   | Mental resistance, HP         |
| Presence    | Social situations             |
| Power       | Spell damage, mana            |
| Control     | Spell accuracy, mana          |

Scale: 1–10 (cap grows each year). You start around 3–4. Every level grants
+1 point to spend.

### Combat (d20)

- Attack roll: d20 + Control + Perception vs enemy Magical Defense.
- Damage: Spell base + scaling attribute + wand bonus.
- Natural 20 = critical hit (double damage).
- Natural 1 = fumble (miss + lose 3 extra mana).
- Mana regenerates +2 per turn.
- 1 action per turn — cast a spell, use an item, or flee.
- In combat: press **I** for items, **?** for spell details, **F** to flee.
- Using an item costs your turn.

**Multi-enemy combat:** some fights feature multiple enemies (summons, groups).
When 2+ enemies are alive, you pick a target before casting.

### The 5 Starter Spells

| Spell        | Mana | Effect                           |
|--------------|------|----------------------------------|
| Flipendo     | 5    | Cheap damage + weakens enemy     |
| Expelliarmus | 10   | Disarms enemy (they lose a turn) |
| Protego      | 8    | Reduces next damage by 60%       |
| Incendio     | 18   | Heavy damage + burn (3 turns)    |
| Episkey      | 12   | Heals you                        |

Learn more spells at the Spell Token Shop.

### Houses

You're sorted randomly. You get one reroll.

| House      | Bonus                                                              |
|------------|--------------------------------------------------------------------|
| Gryffindor | +1 Brawn, +1 Willpower. Below 20% HP: +3 dmg, +2 to hit.           |
| Hufflepuff | +1 Willpower, +1 Presence. +2 max HP per new enemy species killed. |
| Ravenclaw  | +1 Intellect, +1 Perception. +1 token every 4-win streak.          |
| Slytherin  | +1 Power, +1 Control. −20% shop buys, +10% sells.                  |

### Win Streak

Win consecutive battles without resting, losing, or fleeing.

| Streak | Bonus              |
|--------|--------------------|
| 1      | +15% XP & Galleons |
| 2      | +30%               |
| 3      | +45%               |
| 4      | +60%               |
| 5+     | +75% (cap)         |

Resting, losing, or fleeing resets your streak.

---

## Enemies

Six tiers. Thirty-two total.

| Tier        | Recommended Level | Examples                                           |
|-------------|-------------------|----------------------------------------------------|
| Very Weak   | 1                 | Training Dummy, Cornish Pixie, Puffskein, Bundimun |
| Weak        | 2–3               | Giant Rat, Niffler, Mandrake, Fire Crab            |
| Average     | 3–5               | Red Cap, House Rivals, Grindylow                   |
| Strong      | 5–7               | Mountain Troll, Werewolf, Inferi, Boggart          |
| Very Strong | 8+                | Dementor, Death Eater, Bellatrix                   |
| Boss        | 11                | Aragog, Lord Voldemort                             |

**Enemy Hints** — before every fight, you see a one-line warning about the
enemy's special mechanic. Pay attention:

    You encounter: Niffler
      Level 2   HP 25   MD 11   PD 14

      ⚠ Steals 3 Galleons every time it hits you.

    1. Fight
    2. Back away

Each enemy has a unique mechanic and a weakness. Learn them.

### Bosses (Year Finale)

Two bosses guard the end of Year 1 — **Aragog** and **Lord Voldemort**. They
do not appear in random fights. Once you reach **Level 11**, the "Face Your
Destiny" option unlocks in the Battle Arena.

- **Aragog** — summons Acromantula Hatchlings, weak to fire.
- **Voldemort** — draws on dark power below 50% HP, executes low-HP players.

**No retreat from a boss fight.** Defeat costs 50% of your Galleons.

---

## Shops

### Spell Token Shop
Spend Spell Tokens to permanently learn new spells.

### Apothecary
Spend Galleons on potions, combat items, and gear.

- **Potions** — healing, mana, cures, buffs. Cost your turn in combat.
- **Combat Items** — throwables (cabbage, dungbomb, etc.).
- **Gear** — 6 slots (Body, Hands, Feet, Ring, Amulet, Wand).

### Wand Smith
Permanent wand upgrades that boost accuracy, mana, damage, and attributes.

---

## Wand System

Your wand has **three parts**, plus growing **bond progress**:

| Part           | What it does                    | Options |
|----------------|---------------------------------|---------|
| **Wood**       | +1 to one attribute             | 8 types |
| **Core**       | Unique passive effect           | 4 types |
| **Bond Focus** | Determines your bond buff curve | 4 types |

### Bond Focus

Each focus has its own bonus curve. Pick 1 at start. More unlock at
**Level 3, 5, 7**.

| Focus                 | Theme                        |
|-----------------------|------------------------------|
| **Warrior's Focus**   | Damage and attack rolls      |
| **Scholar's Focus**   | Accuracy and mana efficiency |
| **Warden's Focus**    | HP and defense               |
| **Trickster's Focus** | Agility and initiative       |

Bond levels unlock at **5 / 10 / 20 / 50 / 70 / 85 / 100** wins. Bonuses from
all reached tiers **stack**.

**Switching focus keeps the old one's progress.** Switch back anytime.

### Wand & Gear Menu

From Diagon Alley, option **2. Wand & Gear**:

- View your wand's full details (all foci progress).
- View equipped gear and its bonuses.
- Change wood (25 G), core (25 G), or focus (40 G).

Wand upgrades from the Wand Smith are **permanent** — they never go away.

---

## Year Progression

The game is designed for **seven years** of content.

| Year | Levels | Attribute Cap | Spell Cap |
|------|--------|---------------|-----------|
| 1    | 1–10   | 10            | 5         |
| 2    | 11–20  | 12            | 7         |
| 3    | 21–30  | 14            | 9         |
| 4–7  | …      | …             | …         |

After defeating the year's bosses, you advance to the next year. You keep
everything — spells, wand, gear, money, and bond progress. You gain bonus
attribute points and stronger house bonuses.

---

## Recent Actions

View your last **5 battles** from the Battle Arena menu. Each entry shows:

- Enemy name
- Result (WIN / LOSS / FLEE / DRAW)
- Turns taken
- Rewards earned (XP, Galleons, Tokens)

---

## Saving

Progress is saved to `savegame.json`. The game keeps a `.bak` backup
automatically — if the main save gets corrupted, the backup is used.

---

## Tips

- Rest only when you need to — it resets your win streak.
- Fight enemies at or above your level for more XP.
- Manage mana. Don't blow it all on Incendio early.
- Protego before a big enemy turn can save your life.
- Check the shops after every couple of fights.
- Explore new enemy species — Hufflepuff especially loves this.
- Experiment with different Bond Foci. Swapping is cheap.

---

## File Structure

    wizard_rpg/
    ├── agent.md          # Developer blueprint
    ├── readme.md         # This file
    ├── GUI.py            # Tkinter graphical interface
    ├── run_gui.bat       # Windows GUI launcher
    ├── assets/houses/    # House crest artwork
    ├── Data.py           # All game constants
    ├── Player.py         # Player class
    ├── Enemy.py          # Enemy class
    ├── Spells.py         # Spell casting
    ├── Combat.py         # Battle loop
    ├── Items.py          # Inventory, potions, gear
    ├── Shop.py           # All three shops + selling
    └── main.py           # Terminal entry point

---

## Roadmap

**Implemented:**
- Character creation, Sorting Hat with reroll, wand choice
- GUI and terminal front ends (same rules)
- Combat (d20 system, multi-enemy, summons)
- 5 starter spells, 32 enemies, 2 bosses
- Leveling, XP, win streak
- Three shops (spells, apothecary, wand smith)
- Items, potions, gear, mid-battle item usage
- Wand system: wood / core / 4 Bond Foci
- Enemy hints (pre-battle warnings)
- Recent Actions log
- Save with versioning and backup
- Help system

**Coming later:**
- Boss gauntlet + year transition
- Classes & festivals
- Year 2+ content (spells, enemies, areas)
- Story, quests, and locations
- FastAPI web version

---

## License

Personal project. Free to use and download.

---

Made with Python and a love for wizard duels.
EOF