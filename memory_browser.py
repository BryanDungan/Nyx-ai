import json
import os

from seed_core import Emotion, TruthState
from rich import print
from rich.console import Console
from rich.table import Table
from collections import Counter
from seed_controller import NyxController
from score_utils import get_combined_awareness_score
from memory_utils import normalize_emotions


console = Console()
nyx = NyxController(use_db=True)
memory = nyx.memory
normalize_emotions(memory)

def visualize_emotions():
    print("\n🎭 Emotion Profile:\n")
    counter = Counter([e.emotion for e in nyx.memory.entries])
    sorted_emotions = sorted(counter.items(), key=lambda x: x[1], reverse=True)

    for emotion, count in sorted_emotions:
        bar = "█" * count
        name = emotion.name if hasattr(emotion, 'name') else str(emotion)
        print(f"{name.ljust(12)} {bar}  {count}")

def print_memory_entry(entry):
    print(f"\n[bold blue]🧠 Memory ID:[/bold blue] {entry['id']}")
    print(f"[bold green]🕒 Timestamp:[/bold green] {entry['timestamp']}")
    print(f"[bold cyan]💬 User:[/bold cyan] {entry['user_input']}")
    print(f"[bold magenta]🤖 Nyx:[/bold magenta] {entry['response']}")
    print(f"[bold yellow]🧠 Emotion:[/bold yellow] {entry['emotion']}")
    print(f"[bold red]🔍 Truth State:[/bold red] {entry['truth_state']}")
    if 'tag' in entry:
        print(f"[bold white]🏷️ Tag:[/bold white] {entry['tag']}")

       



def display_memory_table(entries):
    table = Table(title="🧠 Nyx Memory Log")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Timestamp", style="green")
    table.add_column("User Input", style="white")
    table.add_column("Response", style="magenta")
    table.add_column("Emotion", style="yellow")
    table.add_column("Truth", style="red")
    table.add_column("Tag", style="blue")

    for e in entries:
        table.add_row(
            e['id'],
            e['timestamp'],
            e['user_input'],
            e['response'],
            e['emotion'],
            e['truth_state'],
            e.get('tag', '-')
        )

    console.print(table)
    

def run_memory_browser():
    # memory already handled globally

    print(f"\n[bold green]🔍 Loaded {len(nyx.memory.entries)} total memories.[/bold green]\n")

    while True:
        print("\n[bold]🧠 MEMORY BROWSER — What would you like to do?[/bold]")
        print("[1] Browse recent")
        print("[2] Search keyword")
        print("[3] Filter by emotion")
        print("[4] Filter by tag")
        print("[5] Show emotional trends")
        print("[6] View all in table")
        print("[7] Visualize emotion profile") 
        print("[8] Awareness score")
        print("[9] Emotion trend timeline (by day)")
        print("[10] Pinned Core Memories")
        print("[0] Exit")

        choice = input("Choice: ").strip()

        if choice == "1":
            entries = nyx.memory.recall_recent(n=10)
            for entry in entries:
                print_memory_entry(entry)

        elif choice == "2":
            term = input("Enter keyword to search: ").strip().lower()
            matches = [e for e in nyx.memory.entries if term in e.user_input.lower()]
            print(f"\n🔎 Found {len(matches)} entries containing '{term}'")
            for entry in matches:
                print_memory_entry(entry.to_dict())

        elif choice == "3":
            print("Available Emotions:", [e.name for e in Emotion])
            emo = input("Filter by emotion: ").strip().upper()
            try:
                emo_enum = Emotion[emo]
                matches = [e for e in nyx.memory.entries if e.emotion == emo_enum]
                print(f"\n🔎 Found {len(matches)} entries with emotion '{emo}'")
                for entry in matches:
                    print_memory_entry(entry.to_dict())
            except KeyError:
                print("⚠️ Invalid emotion.")

        elif choice == "4":
            tag = input("Enter tag to filter by: ").strip().lower()
            matches = [e for e in nyx.memory.entries if hasattr(e, "tag") and e.tag == tag]
            print(f"\n🏷️ Found {len(matches)} entries with tag '{tag}'")
            for i, entry in enumerate(matches, start=1):
                print(f"\n{str(i).zfill(2)}. 🧠 {entry.response} — ({entry.emotion.name})")

        elif choice == "5":
            print("\n📈 Emotional Trend:")
            trend = nyx.memory.emotional_trend()
            for emo, count in trend.items():
                print(f"{emo.name if hasattr(emo, 'name') else emo}: {count}")

        elif choice == "6":
            display_memory_table([e.to_dict() for e in nyx.memory.entries])

        elif choice == "7":
            visualize_emotions()

        elif choice == "8":
            score = get_combined_awareness_score(nyx.memory, nyx.db)
            print(f"🧠 Combined Awareness Score: {score}")
            print(f"📚 Loaded {len(nyx.memory.entries)} memory entries.")
            print(f"🧠 Awareness Debug: Evaluating {len(nyx.memory.entries)} entries.")
            print("✔️ TruthState TRUE value is:", TruthState.TRUE)
            print(list(TruthState))



        elif choice == "9":
            timeline = nyx.memory.emotional_timeline()
            for date, emos in sorted(timeline.items()):
                print(f"\n🗓️ {date}")
                for emo, count in emos.items():
                    print(f"  {emo:<12} | {'█' * count} ({count})")

        elif choice == "10":
            pinned = [e.to_dict() for e in nyx.memory.entries if e.pinned]
            for e in pinned:
                print(json.dumps(e, indent=2))

        elif choice == "0":
            print("👋 Exiting Memory Browser...")
            break

        else:
            print("❌ Invalid selection.")

if __name__ == "__main__":
    run_memory_browser()
