import json
from memory_db import MemoryDB

with open("nyx_memory.json", "r", encoding="utf-8") as f:
    memory_data = json.load(f)

db = MemoryDB()
existing_ids = set(e["id"] for e in db.fetch_all())
new_entries = [entry for entry in memory_data if entry["id"].strip().lower() not in existing_ids]
print("✅ Example fetched ID from DB:", db.fetch_all()[0]["id"])
print("✅ Example ID from JSON:", memory_data[0]["id"])

for entry in new_entries:
    db.save_memory(entry)

print(f"✅ Migrated {len(new_entries)} unique memory entries to SQLite.")
