import json

try:
    with open("seed_journal.json", "r", encoding="utf-8") as f:
        content = f.read()

    # Try extracting only the valid JSON array
    array_end = content.rindex(']')
    cleaned_json = content[:array_end + 1]
    data = json.loads(cleaned_json)

    print(f"✅ Successfully parsed {len(data)} entries.")

    # Overwrite the file with clean JSON
    with open("seed_journal.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

except Exception as e:
    print("❌ Couldn't auto-repair:", e)