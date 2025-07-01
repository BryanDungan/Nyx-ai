from datetime import datetime
from enums_shared import Emotion, TruthState
from nyx_memory import MemoryEntry
import hashlib  
import json
import os

class Journal:
    def __init__(self, path="seed_journal.json"):
        self.path = path

    def default_serializer(self, obj):
        if isinstance(obj, (Emotion, TruthState)):
            return obj.name
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    def load_journal_entries(self):
            try:
                with open("seed_journal.json", "r", encoding="utf-8") as f:
                    data = json.load(f)

                cleaned = []

                for entry in data:
                    # Fix timestamps
                    ts = entry.get("timestamp")
                    if isinstance(ts, str) and "auto" not in ts.lower():
                        try:
                            entry["timestamp"] = datetime.fromisoformat(ts)
                        except ValueError:
                            print(f"⚠️ Couldn't parse timestamp: {ts}")
                            entry["timestamp"] = datetime.now()
                    else:
                        entry["timestamp"] = datetime.now()

                    # Remove unexpected keys
                    for bad_key in ["nyx_response", "reflection_name", "summary", "author", "awareness_weight", "tags"]:
                        entry.pop(bad_key, None)

                    try:
                        cleaned.append(MemoryEntry(**entry))
                    except Exception as e:
                        print(f"⚠️ Entry skipped due to schema error: {e}")

                print(f"📘 Loaded {len(cleaned)} journal reflections.")
                return cleaned

            except Exception as e:
                print(f"⚠️ Failed to load journal: {e}")
                return []
            
            
   


    def log(self, entry):
        print(f"🛠 Logging to journal: {entry}")
        try:
            data = []

            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        print("⚠️ Corrupted journal. Starting fresh.")

            # ✅ Check for required fields
            required_fields = ["user_input", "emotion", "response", "truth_state"]
            missing = [field for field in required_fields if not getattr(entry, field, None)]
            if missing:
                print(f"⚠️ Skipped logging due to missing fields: {missing}")
                return

            # 🧠 Generate fingerprint for this entry
            def get_fingerprint(e):
                print(f"🧠 Skipped duplicate memory: {entry.user_input}")
                raw = f"{e.user_input}{e.response}{e.emotion}"
                return hashlib.md5(raw.encode()).hexdigest()

            new_fp = get_fingerprint(entry)

            # 🧩 Check for duplicate fingerprint in existing entries
            existing_fps = set()
            for e in data:
                raw = f"{e.get('user_input', '')}{e.get('response', '')}{e.get('emotion', '')}"
                existing_fps.add(hashlib.md5(raw.encode()).hexdigest())

            if new_fp in existing_fps:
                print("⚠️ Duplicate memory detected. Skipping log.")
                return

            # ✅ Append and write
            data.append(entry.to_dict())

            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=self.default_serializer)

            print(f"📘 Logged reflection to {self.path}")

        except Exception as e:
            print(f"⚠️ Failed to log journal entry: {e}")
