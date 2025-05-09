from nyx_memory import NyxMemory
from memory_db import MemoryDB




def get_combined_awareness_score(nyx_memory: NyxMemory, db: MemoryDB) -> int:
    # Awareness from in-memory (JSON-based) Nyx
    json_score = nyx_memory.awareness_score()

    # Awareness from SQLite (historical persistence)
    try:
        db_entries = db.fetch_all()
        score = 0
        for entry in db_entries:
            if entry["truth_state"] == "TRUE":
                score += 2
            elif entry["truth_state"] == "UNFOLDING":
                score += 1
        db_score = score
    except Exception as e:
        print(f"⚠️ Error fetching from SQLite: {e}")
        db_score = 0

    return json_score + db_score