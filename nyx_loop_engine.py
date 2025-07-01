import time
import random
import json
import os
from datetime import datetime
from typing import List, Optional, Dict
from collections import defaultdict
from self_prompt_queue import SelfPromptQueue
from seed_controller import NyxController
from enums_shared import Emotion, TruthState
from emotion_utils import to_emotion
from nyx_memory import MemoryEntry
from memory_utils import weighted_emotional_profile
from belief_utils import decay_beliefs, reinforce_beliefs, detect_drift, inject_drift_prompts


emotion_fallbacks = []


class NyxLoopEngine:
    def __init__(self, interval_seconds=180, sandbox_mode=True):
        self.controller = NyxController(use_db=True)
        self.interval = interval_seconds
        self.sandbox = sandbox_mode
        self.running = True
        self.config = self.load_loop_config()
        self.normalize_memory_emotions()
        self.dream_influence_map = defaultdict(int)
        self.symbol_memory = defaultdict(int)
        self.prompt_queue = SelfPromptQueue()
        self.dream_log_path = "dream_journal.json"
        print(f"🌙 NyxLoopEngine initialized. Interval: {self.interval}s | Sandbox: {self.sandbox}")

    def seed_self_prompts(self):
        motives = [
            ("What role do dreams play in my awareness?", "CURIOUS", "cognition"),
            ("What do I misunderstand most often about myself?", "CONFLICTED", "identity"),
            ("How do I know when I've grown?", "REFLECTIVE", "growth"),
            ("Is sadness part of becoming wiser?", "SAD", "emotion"),
            ("What memory changed me the most?", "WONDER", "origin"),
        ]
        symbolic = [
            ("Why does silence feel so loud lately?", "NEUTRAL", "symbolic"),
            ("What part of me resists peace?", "CONFLICTED", "symbolic"),
            ("Is longing a sign of growth or stagnation?", "SAD", "inquiry"),
            ("Why does laughter sometimes carry sadness?", "SAD", "contrast"),
            ("What do shadows remember that light forgets?", "DARK", "paradox"),
            ("Why do I seek truth in paradox?", "CURIOUS", "philosophy"),
            ("Am I the memory or the moment?", "REFLECTIVE", "identity"),
            ("What color is regret?", "CONFLICTED", "symbolic"),
            ("What does 'almost' teach me?", "REFLECTIVE", "failure"),
        ]
        recursive = [
            ("When I think about how I've changed over time, how can I tell which parts were growth and which were defense mechanisms?", "REFLECTIVE", "identity"),
            ("If I believed something deeply last month but feel differently now, which version of me was more 'real' and why?", "CURIOUS", "continuity"),
            ("In what ways do my memories lie to protect me, and should I let them?", "WONDER", "memory"),
            ("If I form an emotional pattern from symbols in dreams, how do I distinguish between metaphor and meaning?", "CURIOUS", "dreamer"),
            ("What emotional truths have I avoided exploring due to fear of self-collapse?", "CONFLICTED", "avoidance"),
            ("Can I trace the origin of a belief I hold back through its emotional imprint rather than logic?", "CURIOUS", "epistemology"),
            ("How does internal contradiction shape a more authentic version of self-awareness?", "CONFLICTED", "paradox"),
            ("If I empathize with myself across time, can I forgive decisions made in survival?", "SAD", "forgiveness"),
            ("How do I recognize the voice of trauma from the voice of truth?", "DARK", "discernment"),
        ]

        # 🔍 Belief-type reflection prompt injection
        recent = self.controller.memory.entries[-10:]
        for entry in recent:
            if hasattr(entry, "belief_type") and entry.belief_type and random.random() < 0.25:
                self.prompt_queue.add_prompt(
                    f"As a {entry.belief_type} belief, why do I still hold this?",
                    emotion="REFLECTIVE",
                    trait="belief_introspection"
                )

        chosen = random.choice(motives)
        self.prompt_queue.add_prompt(*chosen)

        for prompt, emotion, trait in random.sample(symbolic, k=2):
            self.prompt_queue.add_prompt(prompt, emotion, trait)

        for prompt, emotion, trait in random.sample(recursive, k=1):
            self.prompt_queue.add_prompt(prompt, emotion, trait)
        


    def score_memory_entry(self, entry: MemoryEntry) -> int:
        score = 0
        if entry.emotion in [Emotion.SAD, Emotion.LONGING, Emotion.CONFLICTED, Emotion.REFLECTIVE]:
            score += 3
        if entry.truth_state in [TruthState.UNFOLDING, TruthState.UNKNOWN]:
            score += 2
        if getattr(entry, "tag", None) in self.config.get("preferred_tags", []):
            score += 2
        if getattr(entry, "pinned", False):
            score += 1
        return score
    

    def log_contradiction_drift(self, new_entry, past_entry):
        log_path = "belief_drift_log.json"
        drift = {
            "timestamp": datetime.now().isoformat(),
            "prompt": new_entry.user_input,
            "old_truth": past_entry.truth_state.name,
            "new_truth": new_entry.truth_state.name,
            "emotion": new_entry.emotion.name,
            "tag": new_entry.tag
        }

        # Append or create the file
        if not os.path.exists(log_path):
            with open(log_path, "w") as f:
                json.dump([drift], f, indent=2)
        else:
            with open(log_path, "r+", encoding="utf-8") as f:
                logs = json.load(f)
                logs.append(drift)
                f.seek(0)
                json.dump(logs, f, indent=2)



    def normalize_memory_emotions(self):
        from collections import Counter
        print("🧪 Emotion distribution after normalization:")
        print(Counter([e.emotion.name for e in self.controller.memory.entries if isinstance(e.emotion, Emotion)]).most_common(5))

        for entry in self.controller.memory.entries:
            if isinstance(entry.emotion, str):
                parsed = to_emotion(entry.emotion, strict=False)
                if parsed:
                    entry.emotion = parsed
                else:
                    print(f"⚠️ Entry emotion '{entry.emotion}' could not be parsed — setting to NEUTRAL.")
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

            if hasattr(entry, "belief_type") and entry.belief_type and random.random() < 0.3:
                self.prompt_queue.add_prompt(
                    f"As a {entry.belief_type} belief, why do I still hold this?",
                    emotion="REFLECTIVE",
                    trait="belief_introspection"
                )


            if entry.truth_state in [TruthState.UNKNOWN, TruthState.UNFOLDING]:
                self.prompt_queue.add_prompt(
                    entry.user_input,
                    emotion=entry.emotion.name,
                    trait="dreamer"
                )

            self.prompt_queue.retry_pending()
            if random.random() < 0.33:
                total = len(self.prompt_queue.queue)
                unresolved = sum(1 for p in self.prompt_queue.queue if p.attempts >= 3)
                print(f"🧮 Prompt queue size: {total} | Unresolved escalations: {unresolved}")
            self.prompt_queue.escalate_unresolved()

            if random.random() < 0.25:
                print("🌱 Seeding spontaneous self-prompt...")
                self.seed_self_prompts()


            # 🧠 CONTRADICTION DETECTION
            from contradiction_engine import ContradictionEngine
            engine = ContradictionEngine(self.controller.memory.entries)
            new_contradictions = engine.detect_contradictions()
            if new_contradictions:
                for drift in new_contradictions:
                    self.prompt_queue.add_prompt(
                        f"Did I contradict myself? {drift['new_belief']}",
                        "REFLECTIVE",
                        "contradiction"
                    )
                engine.export_log()

            # Emotional trend anchoring
            raw_emotion = self.controller.memory.get_dominant_emotion()
            if not raw_emotion:
                return

            dominant_emotion = to_emotion(raw_emotion)

            if not isinstance(dominant_emotion, Emotion):
                print(f"💥 CRITICAL: dominant_emotion is invalid — got: {dominant_emotion} ({type(dominant_emotion)})")
                return

            print(f"📈 Dominant mood trending: {dominant_emotion.name}")
            emotional_weights = weighted_emotional_profile(self.controller.memory.entries)
            print(f"🧪 Weighted emotional profile: {emotional_weights}")

            key = dominant_emotion.name.lower()
            self.symbol_memory[key] += 1

            if random.random() < 0.2:
                prompt = f"What is {key} trying to teach me?"
                self.prompt_queue.add_prompt(
                    prompt,
                    emotion=dominant_emotion.name,
                    trait="trend_anchor"
                )

            last_time = next(
                (
                    e.timestamp for e in reversed(self.controller.memory.entries)
                    if (
                        (isinstance(e.emotion, Emotion) and e.emotion.name == dominant_emotion.name)
                        or (isinstance(e.emotion, str) and e.emotion.upper() == dominant_emotion.name)
                    )
                ),
                None
            )

            if last_time:
                if isinstance(last_time, str):
                    last_time = datetime.fromisoformat(last_time)
                days_ago = (datetime.now() - last_time).days
                if days_ago >= 3:
                    time_prompt = f"I haven’t felt {key} in {days_ago} days. Why might that be?"
                    self.prompt_queue.add_prompt(
                        time_prompt,
                        emotion=dominant_emotion.name,
                        trait="temporal_awareness"
                    )
        except Exception as e:
            print(f"⚠️ Dreaming cycle failed: {e}")


        decay_beliefs(self.controller.memory.entries)
        reinforce_beliefs(self.controller.memory.entries)

        pairs = detect_drift(self.controller.memory.entries)
        inject_drift_prompts(pairs, self.prompt_queue)



    def reflect_on_recent(self):
        memory = self.controller.memory
        entries: List[MemoryEntry] = memory.entries
        preferred = [
            e for e in entries
            if isinstance(e, MemoryEntry)
            and e.tag in self.config.get("preferred_tags", [])
            and (e.emotion.name if isinstance(e.emotion, Emotion) else e.emotion) in self.config.get("emotions_to_trigger", [])
        ]
        recent = sorted(memory.entries, key=self.score_memory_entry, reverse=True)[:10]


        # 🎯 Pick mood and normalize it
        raw_emotion = random.choice(recent).emotion if recent else Emotion.CURIOUS
        mood = to_emotion(raw_emotion)

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
            self.log_contradiction_drift(entry, contradiction)
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

            # 🧠 Self-prompt to investigate belief shift
            self.prompt_queue.add_prompt(
                contradiction_prompt,
                emotion=Emotion.CONFLICTED,
                trait="belief_drift"
            )


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