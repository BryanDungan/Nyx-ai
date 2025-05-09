import json
from nyx_memory import MemoryEntry, NyxMemory

def migrate_json_to_sqlite(json_path="nyx_memory.json"):
    mem = NyxMemory(use_db=True)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            count = 0

            for item in raw:
                try:
                    entry = MemoryEntry.from_dict(item)
                    mem.db.write(entry)  # 💾 Write to DB directly
                    count += 1
                except Exception as inner:
                    print(f"⚠️ Failed to import entry: {item.get('user_input', '')[:40]} - {inner}")

            print(f"✅ Migration complete. {count} entries imported.")

    except Exception as outer:
        print(f"❌ Migration failed: {outer}")

if __name__ == "__main__":
    migrate_json_to_sqlite()
