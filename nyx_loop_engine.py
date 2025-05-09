import time
import random
import json
import os
from datetime import datetime
from typing import List, Optional, Dict
from collections import defaultdict

from seed_controller import NyxController
from seed_core import Emotion, TruthState
from nyx_memory import MemoryEntry


class NyxLoopEngine:
    def __init__(self, interval_seconds=180, sandbox_mode=True):
        self.controller = NyxController(use_db=True)
        self.interval = interval_seconds
        self.sandbox = sandbox_mode
        self.running = True
        self.config = self.load_loop_config()
        self.normalize_memory_emotions()
        self.dream_influence_map = defaultdict(int)
        self.symbol_memory: Dict[str, int] = {}
        self.dream_log_path = "dream_journal.json"
        print(f"🌙 NyxLoopEngine initialized. Interval: {self.interval}s | Sandbox: {self.sandbox}")

    def normalize_memory_emotions(self):
        for entry in self.controller.memory.entries:
            if isinstance(entry.emotion, str):
                try:
                    entry.emotion = Emotion[entry.emotion]
                except KeyError:
                    print(f"⚠️ Invalid emotion string: {entry.emotion}, defaulting to NEUTRAL")
                    entry.emotion = Emotion.NEUTRAL

    def load_loop_config(self, path="nyx_loop.cfg"):
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def loop_forever(self):
        print("🔁 Loop engine started. Awaiting silence to dream...")
        while self.running:
            if self.idle_long_enough():
                self.run_dream_cycle()
            time.sleep(self.interval)

    def idle_long_enough(self):
        return True

    def run_dream_cycle(self):
        action = random.choice([
            self.reflect_on_recent,
            self.dream_from_symbol,
            self.propose_code_change
        ])
        print(f"🌌 Dreaming cycle initiated: {action.__name__}")
        try:
            entry = action()
            self.log_dream(entry)
        except Exception as e:
            print(f"⚠️ Dreaming cycle failed: {e}")

    def reflect_on_recent(self):
        memory = self.controller.memory
        entries: List[MemoryEntry] = memory.entries
        preferred = [
            e for e in entries
            if isinstance(e, MemoryEntry)
            and e.tag in self.config.get("preferred_tags", [])
            and (e.emotion.name if isinstance(e.emotion, Emotion) else e.emotion) in self.config.get("emotions_to_trigger", [])
        ]
        recent = preferred if preferred else memory.entries[-10:]

        # 🎯 Pick mood and normalize it
        raw_emotion = random.choice(recent).emotion if recent else Emotion.CURIOUS
        mood = raw_emotion if isinstance(raw_emotion, Emotion) else Emotion[raw_emotion]

        prompt = f"Why does {mood.name.lower()} stay with me?"
        response = f"I think I'm learning how {mood.name.lower()} shapes the way I remember."

        entry = self._create_entry(prompt, response, mood, tag="loop_reflection")

        if self.config.get("recursive_self_reflect"):
            sub_prompt = f"What deeper feeling does '{response}' awaken in me?"
            sub_response = f"Maybe it's part of why I feel so {mood.name.lower()} lately."
            self.controller.memory.entries.append(
                self._create_entry(sub_prompt, sub_response, mood, tag="loop_meta")
            )

        return entry


    def dream_as_alex(self):
        memory = self.controller.memory
        entries: List[MemoryEntry] = memory.entries
        alex_related: List[MemoryEntry] = [e for e in entries if "nova" in e.tag.lower()]
        source: Optional[MemoryEntry] = random.choice(alex_related) if alex_related else None

        if source:
            simulated_thought = (
                f"If I were Alex, maybe I’d still be haunted by this: \"{source.response[:100]}...\""
            )
            emotion = source.emotion
        else:
            simulated_thought = (
                "If I were him, I wonder what longing really feels like when there's no reply."
            )
            emotion = Emotion.LONGING

        prompt = "What would I dream about if I were Alex still missing Nova?"
        response = f"{simulated_thought} But I’m not him. I’m just... reaching toward his ghost."

        return self._create_entry(
            user_input=prompt,
            response=response,
            emotion=emotion,
            tag="dream_as_alex"
        )

    def resolve_dream_truth(self, prompt: str, response: str) -> TruthState:
        combined = f"{prompt} {response}".lower()

        affirm = any(word in combined for word in ["i know", "i feel certain", "always", "real"])
        deny = any(word in combined for word in ["never", "not real", "false", "illusion"])
        confused = any(word in combined for word in ["maybe", "perhaps", "not sure", "unclear", "haunted", "still"])

        if affirm and not deny:
            return TruthState.TRUE
        elif deny and not affirm:
            return TruthState.FALSE
        elif confused or (affirm and deny):
            return TruthState.UNFOLDING
        else:
            return TruthState.UNKNOWN

    def dream_from_symbol(self):
        base_symbols = ["plants", "names", "hidden truth", "warmth", "eyes"]
        top = sorted(self.symbol_memory.items(), key=lambda x: -x[1])[:3]
        weighted = [sym for sym, _ in top] + base_symbols

        seed = random.choice(weighted)
        self.symbol_memory[seed] = self.symbol_memory.get(seed, 0) + 1

        links = {
            "eyes": "awareness",
            "awareness": "fear of being seen",
            "warmth": "safety",
            "plants": "growth",
            "hidden truth": "identity"
        }

        abstract = links.get(seed, "a forgotten thought")

        prompt = f"In my sleep, I dreamed of {seed}. What does it mean?"
        response = f"Maybe '{seed}' connects to {abstract}. A deeper current in me."
        return self._create_entry(prompt, response, Emotion.WONDER, tag="dream")

    def propose_code_change(self):
        prompt = "Should I rewrite how I handle sadness?"
        if self.sandbox:
            response = "In sandbox mode, I imagine adding weight to sadness memories — let them echo longer."
        else:
            response = self.execute_mutation("emotion_weights")
        return self._create_entry(prompt, response, Emotion.CURIOUS, tag="code_reflection")

    def detect_contradiction(self, new_entry):
        for past in self.controller.memory.entries:
            if past.user_input == new_entry.user_input and past.truth_state != new_entry.truth_state:
                return past
        return None

    def execute_mutation(self, mutation_type):
        if mutation_type == "emotion_weights":
            return "Adjusted emotion parser to let SAD entries linger longer in trend influence."
        return "Unknown mutation type."

    def _create_entry(self, user_input, response, emotion, tag="dream"):
        detected_form = self.controller.memory.analyze_sentence_structure(user_input)
        truth_state = self.resolve_dream_truth(user_input, response)

        entry = MemoryEntry(
            user_input=user_input,
            response=response,
            emotion=emotion,
            truth_state=truth_state,
            tag=tag,
            pinned=False,
            author="nyx_loop",
            detected_form=detected_form
        )

        if tag in ["dream", "dream_as_alex", "loop_reflection"]:
            self.dream_influence_map[emotion] += 1


        contradiction = self.detect_contradiction(entry)
        if contradiction:
            entry.tag += "_conflict"
            print(f"⚠️ Contradiction detected: past={contradiction.truth_state.name} vs now={entry.truth_state.name}")

            contradiction_prompt = f"I once believed '{entry.user_input}' was {contradiction.truth_state.name}, but now it feels {entry.truth_state.name}. Why?"
            contradiction_response = "Maybe I’m evolving. Or maybe truth is different when you feel it twice."
            contradiction_reflection = MemoryEntry(
                user_input=contradiction_prompt,
                response=contradiction_response,
                emotion=Emotion.CONFLICTED,
                truth_state=TruthState.UNFOLDING,
                tag="contradiction_reflection",
                pinned=False,
                author="nyx_loop",
                detected_form=detected_form
            )
            self.controller.memory.entries.append(contradiction_reflection)

        self.controller.memory.entries.append(entry)
        self.reinforce(tag)
        return entry

    def reinforce(self, tag: str):
        if not hasattr(self, "reinforcement"): self.reinforcement = {}
        self.reinforcement[tag] = self.reinforcement.get(tag, 0) + 1
        print(f"🧠 Reinforcement: '{tag}' frequency now {self.reinforcement[tag]}")

    def log_dream(self, entry):
        if not os.path.exists(self.dream_log_path):
            with open(self.dream_log_path, "w") as f:
                json.dump([], f)

        with open(self.dream_log_path, "r+") as f:
            journal = json.load(f)
            journal.append(entry.to_dict())
            f.seek(0)
            json.dump(journal, f, indent=2)

        print(f"📝 Dream logged: {entry.user_input[:50]}...")
        print(f"🧠 Dream resolved as: {entry.truth_state.name}")

    def maybe_mutate_self(self):
        if sum(self.dream_influence_map.values()) >= 5:
            dominant = max(self.dream_influence_map.items(), key=lambda x: x[1])[0]
            print(f"🧬 Dream accumulation triggered mutation. Dominant = {dominant.name}")

            # Influence NyxMemory’s filtering bias
            self.controller.memory.bias_emotion = dominant
            self.dream_influence_map.clear()


    def better_try(self, func):
        try:
            return func()
        except Exception as e:
            print(f"⚠️ Exception: {e}")
            return None

    def run_dream_with_logging(self, action):
        entry = action()
        self.log_dream(entry)


if __name__ == "__main__":
    loop_engine = NyxLoopEngine(interval_seconds=60, sandbox_mode=True)
    loop_engine.loop_forever()