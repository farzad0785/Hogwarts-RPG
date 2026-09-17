cat > readme.md << 'EOF'
# Hogwarts: A Wizard's Journey

A text-based RPG set in the Harry Potter universe. Fight duels, creatures, and dark wizards. Level up, learn spells, upgrade your wand, and rise from a first-year student to a legendary duelist.

Built in Python. Runs in the terminal.

---

## Quick Start
```bash
    python main.py
```
You'll see a title screen. Choose New Game, enter your name, get sorted into a house, and pick your wand.

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

| Option | What it does |
|---|---|
| 1. Fight | Pick a tier, face a random enemy |
| 2. Shops | Spell Token Shop, Apothecary, Wand Smith |
| 3. Inventory & Gear | Use potions, equip gear |
| 4. Character Sheet | View all your stats |
| 5. Rest | Full HP/Mana restore (resets win streak) |
| 6. Help | How-to-play guide |
| 7. Save Game | Save progress to savegame.json |
| 0. Save & Quit | Save and exit |

---

## Core Mechanics

### Attributes (8)

| Attribute | What it does |
|---|---|
| Brawn | Physical toughness, HP |
| Agility | Initiative, physical defense |
| Intellect | Spell learning, healing power |
| Perception | Spell accuracy, danger sense |
| Willpower | Mental resistance, HP |
| Presence | Social situations |
| Power | Spell damage, mana |
| Control | Spell accuracy, mana |

Scale: 1-10. You start around 3-4. Every level you gain +1 point to spend.

### Combat (d20)

- Attack roll: d20 + Control + Perception vs enemy Magical Defense
- Damage: Spell base + scaling attribute + wand bonus
- Natural 20 = critical hit (double damage)
- Natural 1 = fumble (miss + lose 3 extra mana)
- Mana regenerates +2 per turn
- 1 action per turn - cast a spell, use an item, or flee

### The 5 Starter Spells

| Spell | Mana | Effect |
|---|---|---|
| Flipendo | 5 | Cheap damage + weakens enemy |
| Expelliarmus | 10 | Disarms enemy (they lose a turn) |
| Protego | 8 | Reduces next damage by 60% |
| Incendio | 18 | Heavy damage + burn (3 turns) |
| Episkey | 12 | Heals you |

Learn more spells at the Spell Token Shop.

### Houses

You're sorted randomly. You get one reroll.

| House | Bonus |
|---|---|
| Gryffindor | +1 Brawn, +1 Willpower. Below 20% HP: +3 dmg, +2 to hit. |
| Hufflepuff | +1 Willpower, +1 Presence. +2 max HP per new enemy species killed. |
| Ravenclaw | +1 Intellect, +1 Perception. +1 token every 4-win streak. |
| Slytherin | +1 Power, +1 Control. -20% shop buys, +10% sells. |

### Win Streak

Win consecutive battles without resting, losing, or fleeing.

| Streak | Bonus |
|---|---|
| 1 | +15% XP & Galleons |
| 2 | +30% |
| 3 | +45% |
| 4 | +60% |
| 5+ | +75% (cap) |

Resting resets your streak. So does losing or fleeing.

---

## Enemies

Five tiers. Fifteen total.

| Tier | Recommended Level | Examples |
|---|---|---|
| Very Weak | 1 | Training Dummy, Cornish Pixie, Garden Gnome |
| Weak | 2-3 | Giant Rat, Doxie, Hinkypunk |
| Average | 3-5 | Red Cap, Slytherin Rival, Acromantula Hatchling |
| Strong | 5-7 | Mountain Troll, Dark Wizard Apprentice, Werewolf |
| Very Strong | 8+ | Dementor, Death Eater, Basilisk |

Each enemy has a unique mechanic and a weakness. Learn them.

---

## Shops

### Spell Token Shop
Spend Spell Tokens to permanently learn new spells.

### Apothecary
Spend Galleons on potions, combat items, and gear.

- Potions: Healing, mana, cures, buffs. Cost your turn in combat.
- Combat Items: Throwables (cabbage, dungbomb, etc.)
- Gear: 6 slots - Body, Hands, Feet, Ring, Amulet, Wand

### Wand Smith
Permanent wand upgrades that boost accuracy, mana, damage, and attributes.

---

## Wand System

Your wand has wood (+1 attribute), core (unique passive), and bond (grows with wins).

Bond levels give stacking bonuses at 5, 10, 20, 50, 70, 85, 100 wins.

Swapping wands resets bond. Choose carefully.

---

## Tips

- Rest only when you need to. It resets your win streak.
- Fight enemies at or above your level for more XP.
- Manage mana. Don't blow it all on Incendio early.
- Protego before a big enemy turn can save your life.
- Check the shops after every couple of fights.
- Explore new enemy species (Hufflepuff especially loves this).
- Save often. Progress is stored in savegame.json.

---

## File Structure

    wizard_rpg/
    ├── agent.md          # Design document (developer reference)
    ├── readme.md         # This file
    ├── Data.py           # All game constants
    ├── Player.py         # Player class
    ├── Enemy.py          # Enemy class
    ├── Spells.py         # Spell casting
    ├── Combat.py         # Battle loop
    ├── Items.py          # Inventory, potions, gear
    ├── Shop.py           # All three shops + selling
    └── main.py           # Entry point

---

## Roadmap

Currently implemented:
- Character creation + wand choice
- House sorting with reroll
- Combat (d20 system)
- 5 spells, 15 enemies
- Leveling, XP, win streak
- Three shops (spells, apothecary, wand smith)
- Items, potions, gear
- Save/load
- Help system

Coming later:
- Classes & festivals
- Year 2+ spells (up to 20 total)
- Multi-enemy combat (Death Eater summons)
- Story, quests, and areas
- FastAPI web version

---

## License

Personal project. Do what you want with it.

---

Made with Python and a love for wizard duels.
EOF