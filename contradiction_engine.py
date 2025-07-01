# contradiction_engine.py (new file)
from datetime import datetime
from typing import List
from nyx_memory import MemoryEntry

class ContradictionEngine:
    def __init__(self, memory_entries: List[MemoryEntry]):
        self.memories = memory_entries
        self.belief_drift_log = []

    def detect_contradictions(self):
        seen = {}
        contradictions = []

        for mem in self.memories:
            user_input = (mem.user_input or "").strip().lower()
            prompt = (mem.prompt or "").strip().lower() if hasattr(mem, "prompt") else ""

            # 🚫 Skip introspective loops
            if user_input.startswith("did i contradict myself?") or prompt.startswith("did i contradict myself?"):
                continue

            tag = getattr(mem, "tag", None)
            emotion = str(getattr(mem, "emotion", ""))
            key = (tag, emotion)

            if key in seen and seen[key] != user_input:
                contradictions.append({
                    "timestamp": datetime.now().isoformat(),
                    "tag": tag,
                    "emotion": emotion,
                    "old_belief": seen[key],
                    "new_belief": user_input,
                    "source": prompt or user_input
                })

            seen[key] = user_input

        self.belief_drift_log.extend(contradictions)
        return contradictions



    def export_log(self, path="belief_drift_log.json"):
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.belief_drift_log, f, indent=2, default=str)
