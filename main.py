#!/usr/bin/env python3
"""
Simple Quizlet-like terminal app.

Requirements:
    pip install rich questionary pyyaml

Directory structure:

quiz.py
decks/
    networking.yaml
    linux.yaml
    temperature.yaml

Example YAML:

title: Temperature Sensors

cards:
  - q: Which states disable temperature sensors?
    a:
      - Waiting
      - Idle
      - Running

  - q: Which state enables DMA?
    a: Running
"""

from pathlib import Path
import random
import sys

import questionary
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress


console = Console()


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def check_answer(user_answer, expected):
    """Returns (correct, expected_string)."""

    if isinstance(expected, list):
        submitted = {
            normalize(x)
            for x in user_answer.split(",")
            if x.strip()
        }

        answers = {
            normalize(x)
            for x in expected
        }

        return submitted == answers, ", ".join(expected)

    return normalize(user_answer) == normalize(str(expected)), str(expected)


# ------------------------------------------------------------
# Deck loading
# ------------------------------------------------------------

DECK_DIR = Path("decks")


if not DECK_DIR.exists():
    console.print("[red]Missing 'decks' folder.[/]")
    sys.exit(1)

files = sorted(DECK_DIR.glob("*.yaml"))

if not files:
    console.print("[red]No YAML decks found.[/]")
    sys.exit(1)

choices = [f.stem.replace("_", " ").title() for f in files]
choices.append("Quit")

selection = questionary.select(
    "Choose a deck",
    choices=choices,
).ask()

if selection == "Quit" or selection is None:
    raise SystemExit

selected_file = files[choices.index(selection)]

with open(selected_file, "r") as f:
    deck = yaml.safe_load(f)

title = deck.get("title", selected_file.stem.title())
cards = deck["cards"]

random.shuffle(cards)

console.clear()

console.print(
    Panel.fit(
        f"[bold cyan]{title}[/]\n"
        f"{len(cards)} cards",
        border_style="cyan",
    )
)

console.print()

# ------------------------------------------------------------
# Quiz
# ------------------------------------------------------------

correct = 0
incorrect = 0
skipped = 0

queue = list(cards)

with Progress() as progress:

    task = progress.add_task(
        "Studying...",
        total=len(queue),
    )

    while queue:

        card = queue.pop(0)

        progress.stop()

        console.rule("[bold blue]Question")

        console.print(card["q"], style="bold")

        action = questionary.select(
            "",
            choices=[
                "Answer",
                "Show Answer",
                "Skip",
                "Quit",
            ],
        ).ask()

        if action == "Quit":
            break

        if action == "Skip":
            skipped += 1
            progress.update(task, advance=1)
            progress.start()
            continue

        if action == "Show Answer":
            console.print()

            answer = card["a"]

            if isinstance(answer, list):
                console.print("[bold green]Answer:[/]")
                for item in answer:
                    console.print(f" • {item}")
            else:
                console.print(f"[bold green]Answer:[/] {answer}")

            console.input("\nPress Enter to continue...")

            progress.update(task, advance=1)
            progress.start()
            continue

        guess = console.input("\n[bold cyan]> [/]").strip()

        ok, expected = check_answer(
            guess,
            card["a"],
        )

        console.print()

        if ok:
            console.print("[bold green]✓ Correct[/]")
            correct += 1

        else:
            console.print("[bold red]✗ Incorrect[/]")
            console.print(f"[yellow]Expected:[/] {expected}")
            incorrect += 1

            # Put missed card back into the queue a few questions later.
            if queue:
                insert_at = min(
                    random.randint(2, 5),
                    len(queue),
                )
                queue.insert(insert_at, card)

                # Progress total increases because card returns later.
                progress.update(task, total=progress.tasks[0].total + 1)

        console.input("\nPress Enter...")

        progress.update(task, advance=1)
        progress.start()

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

console.clear()

table = Table(title=f"{title} Results")

table.add_column("Metric")
table.add_column("Value", justify="right")

table.add_row("Correct", str(correct))
table.add_row("Incorrect", str(incorrect))
table.add_row("Skipped", str(skipped))

attempted = correct + incorrect

if attempted:
    score = correct / attempted * 100
else:
    score = 0

table.add_row("Score", f"{score:.1f}%")

console.print(table)

console.print()

if score == 100:
    console.print("[bold green]Perfect score! 🎉[/]")
elif score >= 80:
    console.print("[green]Great job![/]")
elif score >= 60:
    console.print("[yellow]Keep practicing![/]")
else:
    console.print("[red]Time for another round![/]")