# 📁 self_prompt_queue.py (FINALIZED RECURSION-SAFE)
import json
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional
from emotion_utils import to_emotion

PERSIST_PATH = "pending_prompts.json"

def normalize_text(text: str) -> str:
    return text.lower().replace("“", '"').replace("”", '"').strip()

@dataclass
class SelfPrompt:
    prompt: str
    emotion: str
    trait: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    attempts: int = 0
    reword_level: int = 0

    def to_dict(self):
        return {
            "prompt": self.prompt,
            "emotion": self.emotion,
            "trait": self.trait,
            "timestamp": self.timestamp.isoformat(),
            "attempts": self.attempts,
            "reword_level": self.reword_level
        }

    @staticmethod
    def from_dict(d):
        return SelfPrompt(
            prompt=d["prompt"],
            emotion=to_emotion(d["emotion"]).name,
            trait=d.get("trait"),
            timestamp=datetime.fromisoformat(d["timestamp"]),
            attempts=d.get("attempts", 0),
            reword_level=d.get("reword_level", 0)
        )

class SelfPromptQueue:
    def __init__(self, path="pending_prompts.json"):
        self.path = path
        self.queue: List[SelfPrompt] = []
        self.load()

    def reword_prompt(self, original_prompt: str, level: int = 0) -> str:
        if level == 0:
            return f"What’s another way to explore: “{original_prompt}”?"
        else:
            return f"What’s another *deeper* angle to explore (level {level + 1}): “{original_prompt}”?"

    def exists(self, prompt: str) -> bool:
        normalized = normalize_text(prompt)
        return any(normalize_text(p.prompt) == normalized for p in self.queue)


    def add_prompt(self, prompt, emotion="NEUTRAL", trait=None, reword_level=0):
        if self.exists(prompt):
            print(f"⚠️ Prompt already exists in queue: '{prompt}'")
            return

        self.queue.append(
            SelfPrompt(prompt=prompt, emotion=emotion, trait=trait, reword_level=reword_level)
        )
    def escalate_unresolved(self, max_depth=3):
        for p in self.queue:
            if p.attempts >= 3 and p.reword_level < max_depth:
                recent = [
                    x for x in self.queue
                    if normalize_text(p.prompt) in normalize_text(x.prompt)
                ]
                if any(r.reword_level > p.reword_level for r in recent):
                    continue

                print(f"⚠️ Escalating unresolved prompt: '{p.prompt}'")
                new_prompt = self.reword_prompt(p.prompt, p.reword_level)
                self.add_prompt(
                    prompt=new_prompt,
                    emotion=p.emotion,
                    trait="reworded",
                    reword_level=p.reword_level + 1
                )

    def prioritize(self):
        trait_priority = {
            "temporal_awareness": 3,
            "dreamer": 2,
            "reworded": 1,
            "casual": 0,
            None: 0
        }
        self.queue.sort(key=lambda p: trait_priority.get(p.trait, 0), reverse=True)

    def get_pending(self):
        self.load()
        return self.queue

    def retry_pending(self):
        now = datetime.now()
        MAX_ATTEMPTS = 20
        fresh_queue = []

        for p in self.get_pending():
            if p.attempts >= MAX_ATTEMPTS:
                print(f"🗑 Dropping stale prompt (max attempts): '{p.prompt}'")
                continue
            if (now - p.timestamp).total_seconds() < 300:
                continue
            print(f"🔁 Retrying prompt: '{p.prompt}'")
            p.attempts += 1
            p.timestamp = now
            fresh_queue.append(p)

        self.prioritize()
        self.queue = fresh_queue
        self.save()

    def save(self):
        with open(PERSIST_PATH, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in self.queue], f, indent=2)

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.queue = [SelfPrompt.from_dict(d) for d in json.load(f)]
