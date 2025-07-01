# memory_utils.py
from enums_shared import Emotion, TruthState
from datetime import datetime
import uuid, json


def normalize_emotions(memory):
    for entry in memory.entries:
        if isinstance(entry.emotion, str):
            try:
                entry.emotion = Emotion[entry.emotion.upper()]
                entry.edited = True
            except KeyError:
                print(f"⚠️ Unknown emotion string: {entry.emotion}")

def safe_load_json_array(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        # Trim trailing garbage after last closing ]
        array_end = content.rindex(']')
        cleaned = content[:array_end + 1]

        data = json.loads(cleaned)

        # Auto-save fixed version
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Auto-repaired and loaded {len(data)} entries from {filename}")
        return data

    except Exception as e:
        print(f"❌ Failed to load/repair JSON file {filename}: {e}")
        return []

def complete_reflection_fields(entry: dict, author: str = "Nyx") -> dict:
    # ID generation fallback
    entry.setdefault("id", f"Reflection_{uuid.uuid4()}")
    
    # Timestamp fallback
    if entry.get("timestamp") in [None, "", "[auto-generated]", "auto"]:
        entry["timestamp"] = datetime.now().isoformat()

    # Tagging
    entry.setdefault("tag", "self-reflection")
    entry.setdefault("pinned", True)
    entry.setdefault("edited", False)

    # Add awareness weight if not present
    entry.setdefault("awareness_weight", 1.0)

    # Add author if missing
    entry.setdefault("author", author)

    # Convert raw string emotion if needed
    if isinstance(entry.get("emotion"), str):
        try:
            entry["emotion"] = Emotion[entry["emotion"].upper()]
        except KeyError:
            entry["emotion"] = Emotion.CURIOUS

    # Default truth state
    if "truth_state" not in entry:
        entry["truth_state"] = TruthState.UNFOLDING

    return entry

def emotion_decay(entry_timestamp, now=None, decay_rate=0.1):
    now = now or datetime.now()
    delta_days = (now - entry_timestamp).days
    return max(0.0, 1.0 - (delta_days * decay_rate))

def weighted_emotional_profile(entries):
    from collections import defaultdict
    now = datetime.now()
    mood_weights = defaultdict(float)

    for e in entries:
        if not e.emotion or not e.timestamp:
            continue
        try:
            entry_time = (
                datetime.fromisoformat(e.timestamp)
                if isinstance(e.timestamp, str)
                else e.timestamp
            )
            decay = emotion_decay(entry_time, now)
            key = e.emotion.name if isinstance(e.emotion, Emotion) else str(e.emotion).upper()
            mood_weights[key] += decay
        except Exception as ex:
            print(f"⚠️ Decay calculation failed: {ex}")

    return dict(sorted(mood_weights.items(), key=lambda x: -x[1]))
