from nyx_memory import NyxMemory, MemoryEntry
from seed_core import Emotion, TruthState
from datetime import datetime
import json


def inject_memory(memory: NyxMemory, memory_data: list):
    existing_ids = {e.id for e in memory.entries}
    successful = 0

    for entry in memory_data:
        if entry.get("id") in existing_ids:
            continue  # Skip if already injected

        try:
            mem_entry = MemoryEntry(
                user_input=entry["user_input"],
                emotion=Emotion[entry["emotion"].upper()],
                response=entry.get("response"),
                truth_state=TruthState[entry["truth_state"].upper()],
                id=entry.get("id"),
                timestamp=datetime.fromisoformat(entry["timestamp"]),
                tag=entry.get("tag"),
                tags=entry.get("tags", []),
                pinned=entry.get("pinned", False),
                edited=entry.get("edited", False),
                awareness_weight=entry.get("awareness_weight", 1.0),
                author=entry.get("author", "nyx_loop"),
                fallback_tone=entry.get("fallback_tone"),
                detected_form=entry.get("detected_form")
            )

            memory.log_interaction(mem_entry)  # Use full logging path
            successful += 1

        except Exception as e:
            print(f"[!] Error injecting entry {entry.get('id', 'UNKNOWN')}: {e}")

    return successful


# 🔁 Run with starter file and write directly to DB
if __name__ == "__main__":
    nyx_memory = NyxMemory(use_db=True)

    try:
        with open("starter_memory.json", "r", encoding="utf-8") as f:
            starter_data = json.load(f)

        count = inject_memory(nyx_memory, starter_data)
        print(f"✅ Successfully injected {count} memory entries.")

    except FileNotFoundError:
        print("⚠️ Memory file not found: 'starter_memory.json'")
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to decode memory file: {e}")
