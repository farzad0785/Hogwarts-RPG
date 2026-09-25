"""Tkinter interface for Hogwarts: A Wizard's Journey.

This module deliberately sits beside the terminal client in Main.py.  Both
front ends use the same Player, Enemy, spell, item, shop, and reward logic.
Run it with::

    python GUI.py
"""

from __future__ import annotations

import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from Combat import (
    MAX_TURNS,
    _all_dead,
    _draw,
    _enemies_turn,
    _flee,
    _handle_enemy_death,
    _label_enemies,
    _lose,
    _player_end_of_turn,
    _win,
)
from Data import (
    ATTRIBUTES,
    ATTR_DISPLAY,
    BOND_FOCI,
    BOND_FOCUS_KEYS,
    BOSS_GAUNTLET_BY_YEAR,
    COMBAT_ITEMS,
    ENEMIES,
    ENEMIES_BY_TIER,
    GEAR,
    GEAR_SLOTS,
    HOUSES,
    POTIONS,
    SPELLS,
    WAND_CORES,
    WAND_CORE_FEE,
    WAND_FOCUS_FEE,
    WAND_UPGRADES,
    WAND_WOOD_BONUS,
    WAND_WOOD_FEE,
    XP_TO_NEXT,
)
from Enemy import Enemy, random_enemy_key, enemies_of_tier
from Items import equip_gear, inventory_count, unequip_gear, use_combat_item, use_potion
from Main import SAVE_FILE, boss_gate_available, current_boss_gauntlet, save_game, try_load
from Player import Player
from Shop import _buy_multiplier, buy_item, buy_wand_upgrade, learn_spell, sell_item
from Spells import cast_spell


COLORS = {
    "bg": "#090d18",
    "panel": "#111827",
    "panel_alt": "#172033",
    "raised": "#202a40",
    "gold": "#d8ad55",
    "gold_hover": "#ecc66f",
    "text": "#f5f1e8",
    "muted": "#9aa6bb",
    "border": "#2b3852",
    "red": "#c95757",
    "green": "#58a67d",
    "blue": "#648bd8",
    "purple": "#9d75d6",
}

HOUSE_COLORS = {
    "gryffindor": "#9f3138",
    "hufflepuff": "#c99d38",
    "ravenclaw": "#3765a3",
    "slytherin": "#39735a",
}

TIER_INFO = {
    "very_weak": ("Very Weak", 1, "Practice and small creatures"),
    "weak": ("Weak", 2, "Early duels and pests"),
    "average": ("Average", 3, "Rivals and dangerous creatures"),
    "strong": ("Strong", 5, "Serious magical threats"),
    "very_strong": ("Very Strong", 8, "Elite and deadly opponents"),
}


def clear_children(widget):
    for child in widget.winfo_children():
        child.destroy()


class ScrollFrame(tk.Frame):
    """A themed vertically scrollable frame."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self.canvas = tk.Canvas(
            self, bg=COLORS["bg"], highlightthickness=0, bd=0
        )
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = tk.Frame(self.canvas, bg=COLORS["bg"])
        self.window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.body.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.window, width=e.width),
        )
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)

    def _on_wheel(self, event):
        if self.winfo_exists() and self.winfo_containing(event.x_root, event.y_root):
            self.canvas.yview_scroll(int(-event.delta / 120), "units")


class HogwartsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hogwarts: A Wizard's Journey")
        self.geometry("1220x780")
        self.minsize(1000, 680)
        self.configure(bg=COLORS["bg"])
        self.player: Player | None = None
        self.content = None
        self.header_title = None
        self.header_meta = None
        self.nav_buttons = {}
        self.current_page = "home"
        self.creation_house = None
        self.creation_rerolled = False
        self._configure_styles()
        self.house_images = self._load_house_images()
        self.show_landing()

    def _load_house_images(self):
        """Load generated house emblems at three UI-friendly sizes."""
        asset_dir = Path(__file__).resolve().parent / "assets" / "houses"
        images = {}
        for house_key in HOUSES:
            path = asset_dir / f"{house_key}.png"
            try:
                original = tk.PhotoImage(file=str(path))
            except tk.TclError:
                continue
            images[house_key] = {
                "original": original,
                "medium": original.subsample(2),
                "small": original.subsample(4),
            }
        return images

    def house_image(self, house_key, size="small"):
        return self.house_images.get(house_key, {}).get(size)

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["raised"],
            background=COLORS["raised"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["gold"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            padding=7,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["raised"])],
            selectbackground=[("readonly", COLORS["raised"])],
            selectforeground=[("readonly", COLORS["text"])],
        )
        style.configure(
            "Gold.Horizontal.TProgressbar",
            troughcolor=COLORS["raised"],
            background=COLORS["gold"],
            bordercolor=COLORS["raised"],
            lightcolor=COLORS["gold"],
            darkcolor=COLORS["gold"],
        )
        style.configure(
            "Health.Horizontal.TProgressbar",
            troughcolor=COLORS["raised"],
            background=COLORS["red"],
            bordercolor=COLORS["raised"],
        )
        style.configure(
            "Mana.Horizontal.TProgressbar",
            troughcolor=COLORS["raised"],
            background=COLORS["blue"],
            bordercolor=COLORS["raised"],
        )
        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=COLORS["panel"],
            foreground=COLORS["muted"],
            padding=(18, 10),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS["gold"])],
            foreground=[("selected", COLORS["bg"])],
        )

    def primary_button(self, parent, text, command, width=None, state="normal"):
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            state=state,
            bg=COLORS["gold"],
            fg=COLORS["bg"],
            activebackground=COLORS["gold_hover"],
            activeforeground=COLORS["bg"],
            disabledforeground="#6d6658",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2" if state == "normal" else "arrow",
            padx=16,
            pady=9,
        )

    def secondary_button(self, parent, text, command, width=None, state="normal"):
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            state=state,
            bg=COLORS["raised"],
            fg=COLORS["text"],
            activebackground=COLORS["border"],
            activeforeground=COLORS["text"],
            disabledforeground="#596273",
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            cursor="hand2" if state == "normal" else "arrow",
            padx=14,
            pady=8,
        )

    @staticmethod
    def label(parent, text, size=10, color=None, weight="normal", **kwargs):
        return tk.Label(
            parent,
            text=text,
            bg=kwargs.pop("bg", parent.cget("bg")),
            fg=color or COLORS["text"],
            font=("Segoe UI", size, weight),
            **kwargs,
        )

    def card(self, parent, **kwargs):
        return tk.Frame(
            parent,
            bg=COLORS["panel"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            bd=0,
            **kwargs,
        )

    def show_landing(self):
        clear_children(self)
        self.player = None
        shell = tk.Frame(self, bg=COLORS["bg"])
        shell.pack(fill="both", expand=True)

        left = tk.Frame(shell, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(70, 30), pady=55)
        right = tk.Frame(shell, bg=COLORS["panel"], width=390)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        crest = tk.Canvas(left, width=92, height=92, bg=COLORS["bg"], highlightthickness=0)
        crest.create_oval(5, 5, 87, 87, outline=COLORS["gold"], width=2)
        crest.create_text(46, 46, text="H", fill=COLORS["gold"], font=("Georgia", 34, "bold"))
        crest.pack(anchor="w", pady=(30, 28))

        self.label(left, "HOGWARTS", 34, COLORS["gold"], "bold").pack(anchor="w")
        self.label(left, "A WIZARD'S JOURNEY", 14, COLORS["muted"], "bold").pack(
            anchor="w", pady=(4, 24)
        )
        self.label(
            left,
            "Shape your magic. Master your wand.\nWrite your own story at Hogwarts.",
            17,
            COLORS["text"],
            wraplength=550,
            justify="left",
        ).pack(anchor="w")

        features = tk.Frame(left, bg=COLORS["bg"])
        features.pack(anchor="w", pady=(38, 0))
        for title, detail in (
            ("TURN-BASED DUELS", "Tactical spells, items, and magical creatures"),
            ("YOUR WAND, YOUR PATH", "Woods, cores, upgrades, and growing bonds"),
            ("SEVEN YEARS", "Level up, face bosses, and build your legend"),
        ):
            row = tk.Frame(features, bg=COLORS["bg"])
            row.pack(fill="x", pady=8)
            tk.Label(row, text="◆", bg=COLORS["bg"], fg=COLORS["gold"], font=("Segoe UI", 10)).pack(
                side="left", padx=(0, 12)
            )
            copy = tk.Frame(row, bg=COLORS["bg"])
            copy.pack(side="left")
            self.label(copy, title, 10, COLORS["text"], "bold").pack(anchor="w")
            self.label(copy, detail, 9, COLORS["muted"]).pack(anchor="w")

        action = tk.Frame(right, bg=COLORS["panel"])
        action.pack(fill="x", padx=45, pady=(190, 0))
        self.label(action, "ENTER THE CASTLE", 12, COLORS["gold"], "bold").pack(anchor="w")
        self.label(action, "Begin a new journey or continue your saved game.", 10, COLORS["muted"], wraplength=290, justify="left").pack(
            anchor="w", pady=(8, 28)
        )
        self.primary_button(action, "New Journey", self.show_creation).pack(fill="x", pady=5)
        self.secondary_button(action, "Continue", self.load_existing).pack(fill="x", pady=5)
        self.label(action, "No external packages required", 9, COLORS["muted"]).pack(
            pady=(25, 0)
        )

    def show_creation(self):
        clear_children(self)
        self.creation_house = None
        self.creation_rerolled = False

        outer = tk.Frame(self, bg=COLORS["bg"])
        outer.pack(fill="both", expand=True, padx=55, pady=35)
        top = tk.Frame(outer, bg=COLORS["bg"])
        top.pack(fill="x")
        self.secondary_button(top, "Back", self.show_landing).pack(side="left")
        self.label(top, "CREATE YOUR WIZARD", 18, COLORS["gold"], "bold").pack(side="left", padx=25)

        body = tk.Frame(outer, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, pady=(25, 0))
        form = self.card(body)
        form.pack(side="left", fill="both", expand=True, padx=(0, 12))
        sorting = self.card(body, width=390)
        sorting.pack(side="right", fill="y", padx=(12, 0))
        sorting.pack_propagate(False)

        fields = tk.Frame(form, bg=COLORS["panel"])
        fields.pack(fill="both", expand=True, padx=35, pady=30)
        self.label(fields, "Student details", 15, COLORS["text"], "bold").pack(anchor="w")
        self.label(fields, "Choose the magical identity you will carry through the school years.", 9, COLORS["muted"]).pack(
            anchor="w", pady=(5, 24)
        )

        self.label(fields, "NAME", 9, COLORS["gold"], "bold").pack(anchor="w")
        self.name_entry = tk.Entry(
            fields,
            bg=COLORS["raised"], fg=COLORS["text"], insertbackground=COLORS["gold"],
            relief="flat", font=("Segoe UI", 12), bd=0,
        )
        self.name_entry.pack(fill="x", ipady=10, pady=(5, 18))
        self.name_entry.insert(0, "Student")

        self.wood_values = {f"{key.title()}  (+1 {attr.title()})": key for key, attr in WAND_WOOD_BONUS.items()}
        self.core_values = {info["name"]: key for key, info in WAND_CORES.items()}
        self.focus_values = {info["name"]: key for key, info in BOND_FOCI.items()}

        self.wood_combo = self._creation_combo(fields, "WAND WOOD", self.wood_values)
        self.core_combo = self._creation_combo(fields, "WAND CORE", self.core_values)
        self.focus_combo = self._creation_combo(fields, "BOND FOCUS", self.focus_values)

        sort_inner = tk.Frame(sorting, bg=COLORS["panel"])
        sort_inner.pack(fill="both", expand=True, padx=32, pady=35)
        self.label(sort_inner, "THE SORTING HAT", 15, COLORS["gold"], "bold").pack()
        self.label(sort_inner, "Your house is chosen by fate. You may ask the Hat once more.", 10, COLORS["muted"], wraplength=300, justify="center").pack(
            pady=(10, 28)
        )
        badge_frame = tk.Frame(sort_inner, width=154, height=154, bg=COLORS["raised"])
        badge_frame.pack(pady=12)
        badge_frame.pack_propagate(False)
        self.house_badge = tk.Label(
            badge_frame, text="?", bg=COLORS["raised"], fg=COLORS["gold"],
            font=("Georgia", 28, "bold"), relief="flat",
        )
        self.house_badge.pack(fill="both", expand=True)
        self.house_name = self.label(sort_inner, "Not sorted yet", 14, COLORS["text"], "bold")
        self.house_name.pack(pady=(8, 3))
        self.house_detail = self.label(sort_inner, "", 9, COLORS["muted"], wraplength=300, justify="center")
        self.house_detail.pack()
        self.sort_button = self.primary_button(sort_inner, "Place on the Sorting Hat", self.sort_house)
        self.sort_button.pack(fill="x", pady=(28, 8))
        self.begin_button = self.secondary_button(sort_inner, "Begin Year One", self.begin_new_game, state="disabled")
        self.begin_button.pack(fill="x", pady=8)

    def _creation_combo(self, parent, title, mapping):
        self.label(parent, title, 9, COLORS["gold"], "bold").pack(anchor="w")
        combo = ttk.Combobox(parent, values=list(mapping), state="readonly", font=("Segoe UI", 10))
        combo.current(0)
        combo.pack(fill="x", pady=(5, 16))
        return combo

    def sort_house(self):
        options = list(HOUSES)
        if self.creation_house:
            options.remove(self.creation_house)
            self.creation_rerolled = True
        self.creation_house = random.choice(options)
        house = HOUSES[self.creation_house]
        crest = self.house_image(self.creation_house, "medium")
        if crest:
            self.house_badge.configure(image=crest, text="", bg=COLORS["panel"])
        else:
            self.house_badge.configure(
                image="", text=house["name"][0], bg=HOUSE_COLORS[self.creation_house], fg="#fff7da"
            )
        self.house_name.configure(text=house["name"])
        bonuses = ", ".join(f"+1 {a.title()}" for a in house["attr_bonus"])
        self.house_detail.configure(text=f"{house['colors']}\n{bonuses}\n\n{house['motto']}")
        if self.creation_rerolled:
            self.sort_button.configure(text="Reroll used", state="disabled")
        else:
            self.sort_button.configure(text="Ask the Hat Again")
        self.begin_button.configure(
            state="normal", bg=COLORS["gold"], fg=COLORS["bg"], cursor="hand2"
        )

    def begin_new_game(self):
        if not self.creation_house:
            return
        name = self.name_entry.get().strip() or "Student"
        wood = self.wood_values[self.wood_combo.get()]
        core = self.core_values[self.core_combo.get()]
        focus = self.focus_values[self.focus_combo.get()]
        self.player = Player(name=name, wand_wood=wood, wand_core=core, wand_focus=focus)
        self.player.house = self.creation_house
        from Items import add_to_inventory

        add_to_inventory(self.player, "potions", "healing_draught", 1)
        self.show_shell()

    def load_existing(self):
        player = try_load(SAVE_FILE)
        if player is None:
            messagebox.showinfo("No saved journey", "No usable savegame.json was found.")
            return
        self.player = player
        self.show_shell()

    def show_shell(self):
        clear_children(self)
        shell = tk.Frame(self, bg=COLORS["bg"])
        shell.pack(fill="both", expand=True)
        sidebar = tk.Frame(shell, bg="#0d1322", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        main = tk.Frame(shell, bg=COLORS["bg"])
        main.pack(side="left", fill="both", expand=True)

        brand = tk.Frame(sidebar, bg="#0d1322")
        brand.pack(fill="x", padx=22, pady=(25, 30))
        self.label(brand, "H", 23, COLORS["gold"], "bold", bg="#0d1322").pack(side="left")
        self.label(brand, "  HOGWARTS", 12, COLORS["text"], "bold", bg="#0d1322").pack(side="left")

        nav = (
            ("home", "Overview"),
            ("battle", "Battle Arena"),
            ("spells", "Spellbook"),
            ("inventory", "Inventory & Gear"),
            ("shops", "Diagon Alley"),
            ("character", "Character"),
        )
        self.nav_buttons = {}
        for key, text in nav:
            button = tk.Button(
                sidebar, text=text, anchor="w", command=lambda k=key: self.switch_page(k),
                bg="#0d1322", fg=COLORS["muted"], activebackground=COLORS["panel_alt"],
                activeforeground=COLORS["text"], relief="flat", bd=0,
                font=("Segoe UI", 10), padx=24, pady=12, cursor="hand2",
            )
            button.pack(fill="x", pady=1)
            self.nav_buttons[key] = button

        bottom = tk.Frame(sidebar, bg="#0d1322")
        bottom.pack(side="bottom", fill="x", padx=18, pady=20)
        self.secondary_button(bottom, "Save Journey", self.save_current).pack(fill="x", pady=4)
        self.secondary_button(bottom, "Title Screen", self.return_to_title).pack(fill="x", pady=4)

        header = tk.Frame(main, bg=COLORS["bg"], height=88)
        header.pack(fill="x", padx=30)
        header.pack_propagate(False)
        title_wrap = tk.Frame(header, bg=COLORS["bg"])
        title_wrap.pack(side="left", pady=18)
        self.header_title = self.label(title_wrap, "", 19, COLORS["text"], "bold")
        self.header_title.pack(anchor="w")
        self.header_meta = self.label(title_wrap, "", 9, COLORS["muted"])
        self.header_meta.pack(anchor="w", pady=(3, 0))
        resources = tk.Frame(header, bg=COLORS["bg"])
        resources.pack(side="right", pady=22)
        self.resource_label = self.label(resources, "", 10, COLORS["gold"], "bold")
        self.resource_label.pack()

        self.content = tk.Frame(main, bg=COLORS["bg"])
        self.content.pack(fill="both", expand=True, padx=30, pady=(0, 28))
        self.switch_page("home")

    def update_header(self, title=None):
        if not self.player or not self.header_title:
            return
        if title:
            self.header_title.configure(text=title)
        house = HOUSES.get(self.player.house, {}).get("name", "Unsorted")
        self.header_meta.configure(
            text=f"{self.player.name}  •  {house}  •  Year {self.player.year}  •  Level {self.player.level}"
        )
        self.resource_label.configure(
            text=f"{self.player.galleons} Galleons     {self.player.spell_tokens} Tokens"
        )

    def switch_page(self, key):
        self.current_page = key
        for name, button in self.nav_buttons.items():
            active = name == key
            button.configure(
                bg=COLORS["panel_alt"] if active else "#0d1322",
                fg=COLORS["gold"] if active else COLORS["muted"],
                font=("Segoe UI", 10, "bold" if active else "normal"),
            )
        renderers = {
            "home": ("Overview", self.render_home),
            "battle": ("Battle Arena", self.render_battle_select),
            "spells": ("Spellbook", self.render_spellbook),
            "inventory": ("Inventory & Gear", self.render_inventory),
            "shops": ("Diagon Alley", self.render_shops),
            "character": ("Character", self.render_character),
        }
        title, renderer = renderers[key]
        self.update_header(title)
        clear_children(self.content)
        renderer()

    def save_current(self, quiet=False):
        if not self.player:
            return
        try:
            save_game(self.player)
            if not quiet:
                messagebox.showinfo("Journey saved", "Your progress has been saved.")
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc))

    def return_to_title(self):
        if self.player and messagebox.askyesno("Return to title", "Save before returning to the title screen?"):
            self.save_current(quiet=True)
        self.show_landing()

    def section_heading(self, parent, title, subtitle=None):
        row = tk.Frame(parent, bg=parent.cget("bg"))
        row.pack(fill="x", pady=(0, 14))
        self.label(row, title, 14, COLORS["text"], "bold").pack(anchor="w")
        if subtitle:
            self.label(row, subtitle, 9, COLORS["muted"]).pack(anchor="w", pady=(3, 0))
        return row

    def stat_card(self, parent, title, value, detail, accent):
        card = self.card(parent)
        self.label(card, title.upper(), 8, COLORS["muted"], "bold").pack(anchor="w", padx=18, pady=(15, 5))
        self.label(card, str(value), 20, accent, "bold").pack(anchor="w", padx=18)
        self.label(card, detail, 8, COLORS["muted"]).pack(anchor="w", padx=18, pady=(3, 15))
        return card

    def render_home(self):
        p = self.player
        hero = self.card(self.content)
        hero.pack(fill="x", pady=(0, 16))
        accent = tk.Frame(hero, bg=HOUSE_COLORS.get(p.house, COLORS["gold"]), width=7)
        accent.pack(side="left", fill="y")
        crest = self.house_image(p.house, "small")
        if crest:
            tk.Label(hero, image=crest, bg=COLORS["panel"], bd=0).pack(
                side="left", padx=(18, 0), pady=14
            )
        copy = tk.Frame(hero, bg=COLORS["panel"])
        copy.pack(side="left", fill="both", expand=True, padx=24, pady=22)
        self.label(copy, f"Welcome back, {p.name}", 18, COLORS["text"], "bold").pack(anchor="w")
        self.label(
            copy,
            f"Your {p.bond_name()} wand is ready. A new challenge waits in the Battle Arena.",
            10, COLORS["muted"],
        ).pack(anchor="w", pady=(5, 0))
        hero_actions = tk.Frame(hero, bg=COLORS["panel"])
        hero_actions.pack(side="right", padx=25)
        self.primary_button(hero_actions, "Enter Battle Arena", lambda: self.switch_page("battle")).pack(
            fill="x", pady=3
        )
        self.secondary_button(hero_actions, "Rest at Hogwarts", self.rest_player).pack(
            fill="x", pady=3
        )

        stats = tk.Frame(self.content, bg=COLORS["bg"])
        stats.pack(fill="x", pady=(0, 16))
        cards = (
            ("Health", f"{p.current_hp}/{p.max_hp()}", "Current vitality", COLORS["red"]),
            ("Mana", f"{p.current_mana}/{p.max_mana()}", "Spell energy", COLORS["blue"]),
            ("Win streak", p.win_streak, f"Reward x{p.streak_multiplier():.2f}", COLORS["green"]),
            ("Wand bond", p.bond_name(), f"{p.bond_wins_total()} victories", COLORS["purple"]),
        )
        for i, args in enumerate(cards):
            stats.grid_columnconfigure(i, weight=1)
            card = self.stat_card(stats, *args)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 6, 0 if i == 3 else 6))

        lower = tk.Frame(self.content, bg=COLORS["bg"])
        lower.pack(fill="both", expand=True)
        progress = self.card(lower)
        progress.pack(side="left", fill="both", expand=True, padx=(0, 8))
        recent = self.card(lower)
        recent.pack(side="right", fill="both", expand=True, padx=(8, 0))

        self.label(progress, "YEAR PROGRESS", 10, COLORS["gold"], "bold").pack(anchor="w", padx=20, pady=(18, 12))
        need = XP_TO_NEXT.get(p.level)
        if need:
            ttk.Progressbar(progress, maximum=need, value=p.xp, style="Gold.Horizontal.TProgressbar").pack(fill="x", padx=20)
            self.label(progress, f"{p.xp} / {need} XP to Level {p.level + 1}", 9, COLORS["muted"]).pack(anchor="w", padx=20, pady=(7, 13))
        else:
            self.label(progress, "Maximum level reached", 10, COLORS["gold"]).pack(anchor="w", padx=20)
        if p.attr_points:
            self.label(progress, f"{p.attr_points} unspent attribute point(s)", 10, COLORS["gold"], "bold").pack(anchor="w", padx=20, pady=5)
            self.secondary_button(progress, "Spend points", lambda: self.switch_page("character")).pack(anchor="w", padx=20, pady=(5, 15))

        self.label(recent, "RECENT BATTLES", 10, COLORS["gold"], "bold").pack(anchor="w", padx=20, pady=(18, 10))
        if not p.battle_log:
            self.label(recent, "No battles yet. Your story starts here.", 9, COLORS["muted"]).pack(anchor="w", padx=20)
        else:
            for entry in reversed(p.battle_log[-5:]):
                row = tk.Frame(recent, bg=COLORS["panel"])
                row.pack(fill="x", padx=20, pady=4)
                result_color = COLORS["green"] if entry["result"] == "win" else COLORS["red"]
                self.label(row, entry["result"].upper(), 8, result_color, "bold").pack(side="left")
                self.label(row, entry["enemy"], 9, COLORS["text"]).pack(side="left", padx=12)
                self.label(row, f"{entry['turns']} turns", 8, COLORS["muted"]).pack(side="right")

    def rest_player(self):
        if not messagebox.askyesno(
            "Rest at Hogwarts",
            "Restore all HP and Mana? Your current win streak will reset.",
        ):
            return
        self.player.full_restore()
        self.player.reset_streak()
        self.render_again()

    def render_battle_select(self):
        self.section_heading(self.content, "Choose your challenge", "Higher tiers unlock as your level grows.")
        grid = tk.Frame(self.content, bg=COLORS["bg"])
        grid.pack(fill="both", expand=True)
        for col in range(2):
            grid.grid_columnconfigure(col, weight=1)
        for index, (key, (name, level, detail)) in enumerate(TIER_INFO.items()):
            card = self.card(grid)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=7, pady=7)
            available = self.player.level >= level
            self.label(card, name, 14, COLORS["text"] if available else COLORS["muted"], "bold").pack(anchor="w", padx=20, pady=(17, 3))
            count = len(enemies_of_tier(key, self.player.year))
            self.label(card, f"{detail}  •  {count} opponents", 9, COLORS["muted"]).pack(anchor="w", padx=20)
            state = "normal" if available else "disabled"
            text = "Find an opponent" if available else f"Requires Level {level}"
            self.secondary_button(card, text, lambda tier=key: self.prepare_encounter(tier), state=state).pack(anchor="w", padx=20, pady=16)

        if boss_gate_available(self.player):
            boss = self.card(grid)
            boss.grid(row=3, column=0, columnspan=2, sticky="ew", padx=7, pady=12)
            self.label(boss, "THE YEAR'S FINAL TRIAL", 14, COLORS["gold"], "bold").pack(anchor="w", padx=20, pady=(16, 3))
            remaining = [ENEMIES[k]["name"] for k in current_boss_gauntlet(self.player) if k not in self.player.bosses_defeated]
            self.label(boss, "Remaining: " + ", ".join(remaining), 9, COLORS["muted"]).pack(anchor="w", padx=20)
            self.primary_button(boss, "Face your destiny", self.prepare_boss).pack(anchor="w", padx=20, pady=16)

    def prepare_encounter(self, tier):
        key = random_enemy_key(tier, random.Random(), self.player.year)
        if key:
            self.render_encounter(key)

    def prepare_boss(self):
        key = next((k for k in current_boss_gauntlet(self.player) if k not in self.player.bosses_defeated), None)
        if key:
            self.render_encounter(key, boss=True)

    def render_encounter(self, enemy_key, boss=False):
        clear_children(self.content)
        self.update_header("Encounter")
        data = ENEMIES[enemy_key]
        wrap = tk.Frame(self.content, bg=COLORS["bg"])
        wrap.pack(expand=True)
        card = self.card(wrap, width=650, height=430)
        card.pack()
        card.pack_propagate(False)
        self.label(card, "BOSS ENCOUNTER" if boss else "A NEW OPPONENT APPEARS", 10, COLORS["red"] if boss else COLORS["gold"], "bold").pack(pady=(38, 12))
        self.label(card, data["name"], 25, COLORS["text"], "bold").pack()
        self.label(card, f"Level {data['level']}   •   {data['tier'].replace('_', ' ').title()}", 10, COLORS["muted"]).pack(pady=(5, 24))
        stats = tk.Frame(card, bg=COLORS["panel"])
        stats.pack()
        for title, value in (("HP", data["hp"]), ("PD", data["pd"]), ("MD", data["md"]), ("MANA", data["mana"])):
            block = tk.Frame(stats, bg=COLORS["raised"], width=105, height=62)
            block.pack(side="left", padx=5)
            block.pack_propagate(False)
            self.label(block, title, 8, COLORS["muted"], "bold").pack(pady=(9, 1))
            self.label(block, str(value), 14, COLORS["text"], "bold").pack()
        hint = data.get("hint", "No information is available.")
        self.label(card, hint, 10, COLORS["muted"], wraplength=550, justify="center").pack(pady=24)
        actions = tk.Frame(card, bg=COLORS["panel"])
        actions.pack()
        self.primary_button(actions, "Begin Duel", lambda: self.start_battle(enemy_key, boss)).pack(side="left", padx=6)
        self.secondary_button(actions, "Back Away", lambda: self.switch_page("battle")).pack(side="left", padx=6)

    def start_battle(self, enemy_key, boss=False):
        clear_children(self.content)
        self.update_header("Duel in Progress")
        BattleView(self, self.content, enemy_key, boss=boss).pack(fill="both", expand=True)

    def render_spellbook(self):
        scroll = ScrollFrame(self.content)
        scroll.pack(fill="both", expand=True)
        self.section_heading(scroll.body, "Known spells", f"{len(self.player.known_spells)} of {self.player.spell_cap()} spell slots used")
        for key, spell in SPELLS.items():
            known = key in self.player.known_spells
            card = self.card(scroll.body)
            card.pack(fill="x", pady=5)
            badge = tk.Label(
                card, text=spell["type"].upper(), width=10,
                bg=COLORS["gold"] if known else COLORS["raised"],
                fg=COLORS["bg"] if known else COLORS["muted"],
                font=("Segoe UI", 8, "bold"), pady=7,
            )
            badge.pack(side="left", padx=15, pady=15)
            copy = tk.Frame(card, bg=COLORS["panel"])
            copy.pack(side="left", fill="both", expand=True, pady=12)
            self.label(copy, spell["name"], 11, COLORS["text"] if known else COLORS["muted"], "bold").pack(anchor="w")
            self.label(copy, spell["description"], 9, COLORS["muted"]).pack(anchor="w", pady=(3, 0))
            status = f"{self.player.get_spell_mana_cost(key)} mana" if known else f"Locked • {spell['token_cost']} tokens"
            self.label(card, status, 9, COLORS["gold"] if known else COLORS["muted"], "bold").pack(side="right", padx=20)

    def render_inventory(self):
        p = self.player
        scroll = ScrollFrame(self.content)
        scroll.pack(fill="both", expand=True)
        body = scroll.body
        self.section_heading(body, "Carried items", "Use potions, equip gear, or sell items you no longer need.")
        tables = (("Potions", "potions", POTIONS), ("Combat items", "items", COMBAT_ITEMS), ("Unequipped gear", "gear", GEAR))
        for title, category, table in tables:
            self.label(body, title.upper(), 9, COLORS["gold"], "bold").pack(anchor="w", pady=(14, 5))
            entries = p.inventory.get(category, {})
            if not entries:
                self.label(body, "Nothing here yet.", 9, COLORS["muted"]).pack(anchor="w", pady=(2, 8))
                continue
            for key, count in list(entries.items()):
                info = table[key]
                row = self.card(body)
                row.pack(fill="x", pady=3)
                self.label(row, f"{info['name']}  x{count}", 10, COLORS["text"], "bold").pack(side="left", padx=15, pady=13)
                self.label(row, info["description"], 9, COLORS["muted"]).pack(side="left", padx=10)
                if category == "potions":
                    self.secondary_button(row, "Use", lambda k=key: self.use_inventory_potion(k)).pack(side="right", padx=5, pady=7)
                if category == "gear":
                    self.secondary_button(row, "Equip", lambda k=key: self.equip_inventory_gear(k)).pack(side="right", padx=5, pady=7)
                self.secondary_button(row, "Sell", lambda c=category, k=key: self.sell_inventory_item(c, k)).pack(side="right", padx=(5, 12), pady=7)

        self.label(body, "EQUIPPED", 9, COLORS["gold"], "bold").pack(anchor="w", pady=(20, 5))
        equipped = self.card(body)
        equipped.pack(fill="x", pady=(0, 20))
        for slot in GEAR_SLOTS:
            key = p.equipped.get(slot)
            row = tk.Frame(equipped, bg=COLORS["panel"])
            row.pack(fill="x", padx=15, pady=6)
            self.label(row, slot.title(), 9, COLORS["muted"], "bold", width=12, anchor="w").pack(side="left")
            self.label(row, GEAR[key]["name"] if key else "Empty", 10, COLORS["text"]).pack(side="left")
            if key:
                self.secondary_button(row, "Unequip", lambda s=slot: self.unequip_slot(s)).pack(side="right")

    def use_inventory_potion(self, key):
        ok, messages = use_potion(self.player, key)
        messagebox.showinfo("Potion" if ok else "Cannot use", "\n".join(messages))
        self.update_header()
        self.render_again()

    def equip_inventory_gear(self, key):
        ok, msg = equip_gear(self.player, key)
        messagebox.showinfo("Gear" if ok else "Cannot equip", msg)
        self.render_again()

    def unequip_slot(self, slot):
        ok, msg = unequip_gear(self.player, slot)
        messagebox.showinfo("Gear" if ok else "Cannot unequip", msg)
        self.render_again()

    def sell_inventory_item(self, category, key):
        ok, msg = sell_item(self.player, category, key)
        messagebox.showinfo("Sale" if ok else "Cannot sell", msg)
        self.update_header()
        self.render_again()

    def render_shops(self):
        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True)
        spell_tab = tk.Frame(notebook, bg=COLORS["bg"])
        supply_tab = tk.Frame(notebook, bg=COLORS["bg"])
        wand_tab = tk.Frame(notebook, bg=COLORS["bg"])
        notebook.add(spell_tab, text="Spell Shop")
        notebook.add(supply_tab, text="Apothecary")
        notebook.add(wand_tab, text="Wand Smith")
        self._render_shop_list(spell_tab, "spells", SPELLS)
        all_supplies = [("potions", k, v) for k, v in POTIONS.items()]
        all_supplies += [("items", k, v) for k, v in COMBAT_ITEMS.items()]
        all_supplies += [("gear", k, v) for k, v in GEAR.items()]
        self._render_supply_shop(supply_tab, all_supplies)
        self._render_shop_list(wand_tab, "upgrades", WAND_UPGRADES)

    def _render_shop_list(self, parent, kind, table):
        scroll = ScrollFrame(parent)
        scroll.pack(fill="both", expand=True, padx=3, pady=10)
        title = "Learn permanent magic" if kind == "spells" else "Permanent wand improvements"
        self.section_heading(scroll.body, title)
        for key, info in table.items():
            row = self.card(scroll.body)
            row.pack(fill="x", pady=4)
            copy = tk.Frame(row, bg=COLORS["panel"])
            copy.pack(side="left", fill="both", expand=True, padx=16, pady=12)
            self.label(copy, info["name"], 10, COLORS["text"], "bold").pack(anchor="w")
            self.label(copy, info["description"], 9, COLORS["muted"]).pack(anchor="w", pady=(3, 0))
            if kind == "spells":
                owned = key in self.player.known_spells
                cost = info["token_cost"]
                action = lambda k=key: self.shop_learn(k)
                text = "Known" if owned else f"Learn • {cost} T"
            else:
                owned = key in self.player.wand_upgrades
                cost = int(info["cost"] * _buy_multiplier(self.player))
                action = lambda k=key: self.shop_upgrade(k)
                text = "Owned" if owned else f"Install • {cost} G"
            self.secondary_button(row, text, action, state="disabled" if owned else "normal").pack(side="right", padx=16)

    def _render_supply_shop(self, parent, entries):
        scroll = ScrollFrame(parent)
        scroll.pack(fill="both", expand=True, padx=3, pady=10)
        self.section_heading(scroll.body, "Potions, combat items, and gear")
        for category, key, info in entries:
            row = self.card(scroll.body)
            row.pack(fill="x", pady=4)
            copy = tk.Frame(row, bg=COLORS["panel"])
            copy.pack(side="left", fill="both", expand=True, padx=16, pady=12)
            self.label(copy, info["name"], 10, COLORS["text"], "bold").pack(anchor="w")
            self.label(copy, f"{category[:-1].title()} • {info['description']}", 9, COLORS["muted"]).pack(anchor="w", pady=(3, 0))
            price = int(info["cost"] * _buy_multiplier(self.player))
            self.secondary_button(row, f"Buy • {price} G", lambda c=category, k=key: self.shop_buy(c, k)).pack(side="right", padx=16)

    def shop_buy(self, category, key):
        ok, msg = buy_item(self.player, category, key)
        messagebox.showinfo("Purchase" if ok else "Cannot buy", msg)
        self.update_header()

    def shop_learn(self, key):
        ok, msg = learn_spell(self.player, key)
        messagebox.showinfo("Spell learned" if ok else "Cannot learn", msg)
        self.update_header()
        self.render_again()

    def shop_upgrade(self, key):
        ok, msg = buy_wand_upgrade(self.player, key)
        messagebox.showinfo("Wand upgraded" if ok else "Cannot upgrade", msg)
        self.update_header()
        self.render_again()

    def render_character(self):
        scroll = ScrollFrame(self.content)
        scroll.pack(fill="both", expand=True)
        body = scroll.body
        left = tk.Frame(body, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(body, bg=COLORS["bg"])
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        self.section_heading(left, "Attributes", f"{self.player.attr_points} points available • cap {self.player.attribute_cap()}")
        attrs = self.card(left)
        attrs.pack(fill="x")
        for attr in ATTRIBUTES:
            row = tk.Frame(attrs, bg=COLORS["panel"])
            row.pack(fill="x", padx=16, pady=6)
            self.label(row, ATTR_DISPLAY[attr], 9, COLORS["muted"], "bold", width=14, anchor="w").pack(side="left")
            base = self.player.base_attrs[attr]
            effective = self.player.get_effective_attr(attr)
            self.label(row, f"{base} base  /  {effective} effective", 10, COLORS["text"]).pack(side="left")
            enabled = self.player.attr_points > 0 and base < self.player.attribute_cap()
            self.secondary_button(row, "+", lambda a=attr: self.spend_point(a), width=2, state="normal" if enabled else "disabled").pack(side="right")

        derived = self.card(left)
        derived.pack(fill="x", pady=15)
        self.label(derived, "DERIVED STATS", 9, COLORS["gold"], "bold").pack(anchor="w", padx=16, pady=(15, 8))
        values = (
            ("Physical Defense", self.player.physical_defense()),
            ("Magical Defense", self.player.magical_defense()),
            ("Initiative", f"+{self.player.initiative_bonus()}"),
            ("Spell Accuracy", f"+{self.player.spell_attack_bonus()}"),
        )
        for name, value in values:
            row = tk.Frame(derived, bg=COLORS["panel"])
            row.pack(fill="x", padx=16, pady=4)
            self.label(row, name, 9, COLORS["muted"]).pack(side="left")
            self.label(row, str(value), 10, COLORS["text"], "bold").pack(side="right")
        tk.Frame(derived, bg=COLORS["panel"], height=10).pack()

        house_key = self.player.house
        house_info = HOUSES.get(house_key)
        if house_info:
            self.section_heading(right, "House")
            house_card = self.card(right)
            house_card.pack(fill="x", pady=(0, 15))
            crest = self.house_image(house_key, "small")
            if crest:
                tk.Label(house_card, image=crest, bg=COLORS["panel"], bd=0).pack(
                    side="left", padx=14, pady=12
                )
            house_copy = tk.Frame(house_card, bg=COLORS["panel"])
            house_copy.pack(side="left", fill="both", expand=True, pady=15)
            self.label(house_copy, house_info["name"], 12, COLORS["text"], "bold").pack(anchor="w")
            self.label(
                house_copy, house_info["motto"], 8, COLORS["muted"],
                wraplength=290, justify="left",
            ).pack(anchor="w", pady=(4, 0))

        self.section_heading(right, "Wand", f"Bond: {self.player.bond_name()} • {self.player.bond_wins_total()} wins")
        wand = self.card(right)
        wand.pack(fill="x")
        self._wand_row(wand, "Wood", self.player.wand["wood"].title(), f"Change • {WAND_WOOD_FEE} G", self.change_wood_dialog)
        self._wand_row(wand, "Core", WAND_CORES[self.player.wand["core"]]["name"], f"Change • {WAND_CORE_FEE} G", self.change_core_dialog)
        self._wand_row(wand, "Focus", BOND_FOCI[self.player.wand["focus"]]["name"], f"Change • {WAND_FOCUS_FEE} G", self.change_focus_dialog)

        if self.player.pending_focus_unlock and self.player.locked_foci():
            unlock = self.card(right)
            unlock.pack(fill="x", pady=15)
            self.label(unlock, "NEW BOND FOCUS AVAILABLE", 10, COLORS["gold"], "bold").pack(anchor="w", padx=16, pady=(15, 5))
            self.label(unlock, "Choose a new focus to unlock at no cost.", 9, COLORS["muted"]).pack(anchor="w", padx=16)
            for focus in self.player.locked_foci():
                self.secondary_button(unlock, BOND_FOCI[focus]["name"], lambda f=focus: self.unlock_focus(f)).pack(fill="x", padx=16, pady=4)
            tk.Frame(unlock, bg=COLORS["panel"], height=10).pack()

    def _wand_row(self, parent, title, value, action_text, command):
        row = tk.Frame(parent, bg=COLORS["panel"])
        row.pack(fill="x", padx=16, pady=9)
        copy = tk.Frame(row, bg=COLORS["panel"])
        copy.pack(side="left")
        self.label(copy, title.upper(), 8, COLORS["muted"], "bold").pack(anchor="w")
        self.label(copy, value, 10, COLORS["text"], "bold").pack(anchor="w")
        self.secondary_button(row, action_text, command).pack(side="right")

    def spend_point(self, attr):
        if self.player.spend_attr_point(attr):
            self.render_again()

    def unlock_focus(self, focus):
        ok, msg = self.player.unlock_focus(focus)
        if ok:
            self.player.pending_focus_unlock = False
        messagebox.showinfo("Bond focus" if ok else "Cannot unlock", msg)
        self.render_again()

    def _choice_dialog(self, title, mapping, current, callback):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.configure(bg=COLORS["panel"])
        dialog.geometry("430x210")
        dialog.transient(self)
        dialog.grab_set()
        self.label(dialog, title, 14, COLORS["gold"], "bold", bg=COLORS["panel"]).pack(pady=(25, 12))
        combo = ttk.Combobox(dialog, values=list(mapping), state="readonly", width=38)
        combo.pack(pady=8)
        for index, (_, key) in enumerate(mapping.items()):
            if key == current:
                combo.current(index)
                break

        def apply_choice():
            if not combo.get():
                return
            ok, msg = callback(mapping[combo.get()])
            messagebox.showinfo(title if ok else "Cannot change", msg, parent=dialog)
            if ok:
                dialog.destroy()
                self.update_header()
                self.render_again()

        self.primary_button(dialog, "Confirm", apply_choice).pack(pady=14)

    def change_wood_dialog(self):
        mapping = {f"{k.title()} (+1 {v.title()})": k for k, v in WAND_WOOD_BONUS.items()}
        self._choice_dialog("Change wand wood", mapping, self.player.wand["wood"], self.player.change_wand_wood)

    def change_core_dialog(self):
        mapping = {v["name"]: k for k, v in WAND_CORES.items()}
        self._choice_dialog("Change wand core", mapping, self.player.wand["core"], self.player.change_wand_core)

    def change_focus_dialog(self):
        mapping = {BOND_FOCI[k]["name"]: k for k in self.player.wand["unlocked_foci"]}
        self._choice_dialog("Change bond focus", mapping, self.player.wand["focus"], self.player.change_wand_focus)

    def render_again(self):
        key = self.current_page
        self.switch_page(key)


class BattleSession:
    """Event-driven adapter around the existing combat rules."""

    def __init__(self, view, player, enemy, rng=None):
        self.view = view
        self.player = player
        self.enemies = [enemy]
        self.rng = rng or random.Random()
        self.turns = 0
        self.active = True
        self.waiting = False
        self.result = None
        _label_enemies(self.enemies)
        player_init = self.rng.randint(1, 20) + player.initiative_bonus()
        enemy_init = max(self.rng.randint(1, 20) + e.initiative_bonus for e in self.enemies)
        self.player_first = player_init >= enemy_init
        self.log(f"{player.name}: initiative {player_init}  |  Enemy: {enemy_init}")
        self.log(f"{'You' if self.player_first else 'The enemy'} act first.")

    def log(self, text):
        self.view.add_log(text)

    def start(self):
        self.begin_round()

    def begin_round(self):
        if not self.active:
            return
        if self.turns >= MAX_TURNS:
            self.finish(_draw(self.player, self.enemies, self.turns, self.log))
            return
        self.turns += 1
        self.log("")
        self.log(f"TURN {self.turns}")
        if self.player_first:
            self.prepare_player()
        else:
            self.view.after(250, self.enemy_then_player)

    def prepare_player(self):
        if not self.active:
            return
        skip = next((name for name in ("disarmed", "stunned", "petrified") if self.player.has_status(name)), None)
        if skip:
            self.log(f"{self.player.name} is {skip} and loses the turn.")
            self.player.remove_status(skip)
            _player_end_of_turn(self.player, self.log)
            self.after_player_action()
            return
        self.waiting = True
        self.view.refresh()
        self.log("Choose a spell, item, or action.")

    def cast(self, spell_key, target):
        if not self.active or not self.waiting:
            return
        cost = self.player.get_spell_mana_cost(spell_key)
        if self.player.current_mana < cost:
            self.log(f"Not enough mana for {SPELLS[spell_key]['name']}.")
            return
        self.waiting = False
        spell = SPELLS[spell_key]
        actual_target = self.player if spell["type"] in ("support", "defense") else target
        result = cast_spell(self.player, spell_key, actual_target, rng=self.rng)
        for line in result["messages"]:
            self.log(line)
        self.handle_enemy_deaths()
        _player_end_of_turn(self.player, self.log)
        self.after_player_action()

    def use_potion(self, key):
        if not self.active or not self.waiting:
            return False
        ok, messages = use_potion(self.player, key)
        for line in messages:
            self.log(line)
        if not ok:
            return False
        self.waiting = False
        _player_end_of_turn(self.player, self.log)
        self.after_player_action()
        return True

    def use_item(self, key, target):
        if not self.active or not self.waiting:
            return False
        ok, messages = use_combat_item(self.player, key, target, self.rng)
        for line in messages:
            self.log(line)
        if not ok:
            return False
        self.waiting = False
        self.handle_enemy_deaths()
        _player_end_of_turn(self.player, self.log)
        self.after_player_action()
        return True

    def pass_turn(self):
        if not self.active or not self.waiting:
            return
        self.waiting = False
        self.log(f"{self.player.name} holds position.")
        _player_end_of_turn(self.player, self.log)
        self.after_player_action()

    def flee(self):
        if not self.active or not self.waiting:
            return
        if any(e.is_boss for e in self.enemies):
            self.log("There is no retreat from this battle.")
            return
        self.waiting = False
        self.finish(_flee(self.player, self.enemies, self.turns, self.log))

    def handle_enemy_deaths(self):
        for enemy in self.enemies:
            if not enemy.is_alive() and not enemy._death_handled:
                enemy._death_handled = True
                _handle_enemy_death(self.player, enemy, self.log)

    def after_player_action(self):
        self.view.refresh()
        if not self.player.is_alive():
            self.finish(_lose(self.player, self.enemies, self.turns, self.log))
        elif _all_dead(self.enemies):
            self.finish(_win(self.player, self.enemies, self.turns, self.rng, self.log))
        elif self.player_first:
            self.view.after(300, self.enemy_then_next)
        else:
            self.view.after(300, self.begin_round)

    def _enemy_phase(self):
        result = _enemies_turn(self.player, self.enemies, self.rng, self.log)
        self.view.refresh()
        if result == "player_dead" or not self.player.is_alive():
            self.finish(_lose(self.player, self.enemies, self.turns, self.log))
            return False
        if result == "all_dead" or _all_dead(self.enemies):
            self.finish(_win(self.player, self.enemies, self.turns, self.rng, self.log))
            return False
        return True

    def enemy_then_player(self):
        if self.active and self._enemy_phase():
            self.prepare_player()

    def enemy_then_next(self):
        if self.active and self._enemy_phase():
            self.begin_round()

    def finish(self, result):
        if not self.active:
            return
        self.active = False
        self.waiting = False
        self.result = result
        self.view.on_finish(result)


class BattleView(tk.Frame):
    def __init__(self, app, parent, enemy_key, boss=False):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.player = app.player
        self.enemy_key = enemy_key
        self.is_boss = boss
        self.enemy = Enemy(enemy_key)
        self.target_map = {}
        self.result = None
        self._build()
        self.session = BattleSession(self, self.player, self.enemy)
        self.after(100, self.session.start)

    def _build(self):
        battlefield = tk.Frame(self, bg=COLORS["bg"])
        battlefield.pack(side="left", fill="both", expand=True, padx=(0, 10))
        sidebar = tk.Frame(self, bg=COLORS["panel"], width=300, highlightbackground=COLORS["border"], highlightthickness=1)
        sidebar.pack(side="right", fill="y", padx=(10, 0))
        sidebar.pack_propagate(False)

        self.combatants = tk.Frame(battlefield, bg=COLORS["bg"])
        self.combatants.pack(fill="x")
        self.log_text = tk.Text(
            battlefield, bg="#0c1220", fg=COLORS["text"], insertbackground=COLORS["gold"],
            selectbackground=COLORS["border"], relief="flat", bd=0,
            font=("Consolas", 9), wrap="word", padx=14, pady=12, height=14, state="disabled",
        )
        self.log_text.pack(fill="both", expand=True, pady=12)
        self.actions = tk.Frame(battlefield, bg=COLORS["panel"], highlightbackground=COLORS["border"], highlightthickness=1)
        self.actions.pack(fill="x")

        self.app.label(sidebar, "DUEL STATUS", 10, COLORS["gold"], "bold").pack(anchor="w", padx=20, pady=(20, 15))
        self.player_status = tk.Frame(sidebar, bg=COLORS["panel"])
        self.player_status.pack(fill="x", padx=20)
        self.status_text = self.app.label(sidebar, "", 9, COLORS["muted"], wraplength=250, justify="left")
        self.status_text.pack(anchor="w", padx=20, pady=14)
        self.app.label(sidebar, "TARGET", 8, COLORS["muted"], "bold").pack(anchor="w", padx=20, pady=(10, 5))
        self.target_combo = ttk.Combobox(sidebar, state="readonly", width=27)
        self.target_combo.pack(fill="x", padx=20)
        self.app.secondary_button(sidebar, "Use Item", self.open_items).pack(fill="x", padx=20, pady=(20, 5))
        self.pass_button = self.app.secondary_button(sidebar, "Pass Turn", self.pass_turn)
        self.pass_button.pack(fill="x", padx=20, pady=5)
        self.flee_button = self.app.secondary_button(sidebar, "Flee", self.flee)
        self.flee_button.pack(fill="x", padx=20, pady=5)
        self.return_button = self.app.primary_button(sidebar, "Return to Arena", self.leave_battle, state="disabled")
        self.return_button.pack(side="bottom", fill="x", padx=20, pady=20)

    def add_log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update_idletasks()

    def refresh(self):
        if not hasattr(self, "session"):
            return
        clear_children(self.combatants)
        player_card = self.app.card(self.combatants)
        player_card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self._combatant_card(player_card, self.player.name, self.player.current_hp, self.player.max_hp(), self.player.current_mana, self.player.max_mana(), True)
        living = [e for e in self.session.enemies if e.is_alive()]
        for enemy in living:
            card = self.app.card(self.combatants)
            card.pack(side="left", fill="both", expand=True, padx=6)
            self._combatant_card(card, enemy.label, enemy.current_hp, enemy.max_hp, enemy.current_mana, enemy.max_mana, False)

        clear_children(self.player_status)
        self.app.label(self.player_status, f"HP  {self.player.current_hp}/{self.player.max_hp()}", 10, COLORS["text"], "bold").pack(anchor="w")
        ttk.Progressbar(self.player_status, maximum=max(1, self.player.max_hp()), value=self.player.current_hp, style="Health.Horizontal.TProgressbar").pack(fill="x", pady=(4, 9))
        self.app.label(self.player_status, f"MANA  {self.player.current_mana}/{self.player.max_mana()}", 10, COLORS["text"], "bold").pack(anchor="w")
        ttk.Progressbar(self.player_status, maximum=max(1, self.player.max_mana()), value=self.player.current_mana, style="Mana.Horizontal.TProgressbar").pack(fill="x", pady=(4, 9))
        statuses = ", ".join(s["name"].title() for s in self.player.statuses) or "No active effects"
        self.status_text.configure(text=statuses)

        self.target_map = {e.label: e for e in living}
        values = list(self.target_map)
        self.target_combo.configure(values=values)
        if values:
            self.target_combo.current(0)

        clear_children(self.actions)
        self.app.label(self.actions, "SPELLS", 8, COLORS["muted"], "bold").grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(10, 4))
        waiting = self.session.active and self.session.waiting
        for index, key in enumerate(self.player.known_spells):
            spell = SPELLS[key]
            cost = self.player.get_spell_mana_cost(key)
            enabled = waiting and self.player.current_mana >= cost
            button = self.app.secondary_button(
                self.actions,
                f"{spell['name']}\n{cost} mana",
                lambda k=key: self.cast_spell(k),
                state="normal" if enabled else "disabled",
            )
            button.grid(row=1 + index // 3, column=index % 3, sticky="ew", padx=6, pady=6)
        for col in range(3):
            self.actions.grid_columnconfigure(col, weight=1)
        state = "normal" if waiting else "disabled"
        self.pass_button.configure(state=state)
        self.flee_button.configure(state=state if not self.is_boss else "disabled")

    def _combatant_card(self, card, name, hp, max_hp, mana, max_mana, player):
        color = COLORS["gold"] if player else COLORS["red"]
        self.app.label(card, name, 11, color, "bold").pack(anchor="w", padx=14, pady=(12, 6))
        self.app.label(card, f"HP {hp}/{max_hp}", 9, COLORS["text"]).pack(anchor="w", padx=14)
        ttk.Progressbar(card, maximum=max(1, max_hp), value=hp, style="Health.Horizontal.TProgressbar").pack(fill="x", padx=14, pady=(4, 6))
        if max_mana:
            self.app.label(card, f"Mana {mana}/{max_mana}", 8, COLORS["muted"]).pack(anchor="w", padx=14, pady=(0, 10))
        else:
            tk.Frame(card, bg=COLORS["panel"], height=15).pack()

    def selected_target(self):
        target = self.target_map.get(self.target_combo.get())
        if target:
            return target
        return next((e for e in self.session.enemies if e.is_alive()), None)

    def cast_spell(self, key):
        target = self.selected_target()
        if target or SPELLS[key]["type"] in ("support", "defense"):
            self.session.cast(key, target)

    def pass_turn(self):
        self.session.pass_turn()

    def flee(self):
        self.session.flee()

    def open_items(self):
        if not self.session.waiting:
            return
        dialog = tk.Toplevel(self)
        dialog.title("Battle items")
        dialog.geometry("520x460")
        dialog.configure(bg=COLORS["panel"])
        dialog.transient(self)
        dialog.grab_set()
        self.app.label(dialog, "USE AN ITEM", 14, COLORS["gold"], "bold", bg=COLORS["panel"]).pack(pady=(20, 10))
        list_frame = tk.Frame(dialog, bg=COLORS["panel"])
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)
        any_items = False
        for category, table in (("potions", POTIONS), ("items", COMBAT_ITEMS)):
            for key, count in self.player.inventory.get(category, {}).items():
                if count < 1:
                    continue
                any_items = True
                info = table[key]
                row = tk.Frame(list_frame, bg=COLORS["raised"])
                row.pack(fill="x", pady=4)
                self.app.label(row, f"{info['name']}  x{count}", 9, COLORS["text"], "bold", bg=COLORS["raised"]).pack(side="left", padx=12, pady=11)

                def use(cat=category, item_key=key):
                    if cat == "potions":
                        ok = self.session.use_potion(item_key)
                    else:
                        target = self.selected_target()
                        ok = bool(target) and self.session.use_item(item_key, target)
                    if ok:
                        dialog.destroy()

                self.app.secondary_button(row, "Use", use).pack(side="right", padx=8, pady=5)
        if not any_items:
            self.app.label(list_frame, "Your bag has no usable battle items.", 10, COLORS["muted"], bg=COLORS["panel"]).pack(pady=35)
        self.app.secondary_button(dialog, "Cancel", dialog.destroy).pack(pady=12)

    def on_finish(self, result):
        self.result = result
        if result["result"] == "win" and self.is_boss:
            if self.enemy_key not in self.player.bosses_defeated:
                self.player.bosses_defeated.append(self.enemy_key)
            self.app.save_current(quiet=True)
        self.refresh()
        title = {
            "win": "Victory!",
            "lose": "Defeat",
            "flee": "You escaped",
            "draw": "Draw",
        }[result["result"]]
        self.add_log("")
        self.add_log(title.upper())
        self.return_button.configure(state="normal", bg=COLORS["gold"], fg=COLORS["bg"], cursor="hand2")
        self.app.update_header("Duel Complete")

    def leave_battle(self):
        if not self.result:
            return
        if self.result["result"] == "lose":
            self.player.full_restore()
            messagebox.showinfo("Hospital Wing", "You wake in the hospital wing, fully restored.")
        if self.is_boss and self.result["result"] == "win":
            remaining = [k for k in current_boss_gauntlet(self.player) if k not in self.player.bosses_defeated]
            if remaining:
                self.player.full_restore()
                messagebox.showinfo("Final Trial", "You catch your breath. One final opponent remains.")
            else:
                summary = self.player.advance_year()
                self.player.full_restore()
                self.app.save_current(quiet=True)
                if "new_year" in summary:
                    messagebox.showinfo(
                        "Year Complete",
                        f"Year {summary['old_year']} complete!\n\nYear {summary['new_year']} begins.\n"
                        f"+{summary['attr_points_gained']} attribute points\n"
                        f"Attribute cap: {summary['new_attr_cap']}",
                    )
                else:
                    messagebox.showinfo(
                        "Hogwarts Complete",
                        "Seven years, countless duels. Your story here is complete.",
                    )
        self.app.switch_page("battle")


if __name__ == "__main__":
    HogwartsApp().mainloop()
