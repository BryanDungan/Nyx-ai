from datetime import datetime
from collections import defaultdict, Counter
import uuid
import json
import random
from memory_db import MemoryDB
from seed_core import MoodVector
import re
from difflib import SequenceMatcher
from typing import Optional, List
from enums_shared import Emotion, TruthState
import uuid
from datetime import datetime
from emotion_utils import to_emotion
from typing import Optional



class MemoryEntry:
    def __init__(
        self,
        user_input,
        emotion,
        response=None,
        truth_state=None,
        id=None,
        timestamp=None,
        pinned=False,
        tag=None,
        tags=None,
        edited=False,
        nyx_response=None,
        awareness_weight=1.0,
        author="Guac",
        fallback_tone=None,
        detected_form=None,
        mood_vector=None,
        belief_strength: float = 0.5,
        belief_type: Optional[str] = "learned"
    ):
        self.id = id if id else str(uuid.uuid4())
        self.timestamp = timestamp if timestamp else datetime.now()
        self.user_input = user_input
        self.emotion = to_emotion(emotion)
        self.response = response or nyx_response  # fallback to nyx_response
        self.truth_state = truth_state
        self.tag = tag or (tags[0] if tags else None)
        self.tags = tags if tags else ([tag] if tag else [])
        self.pinned = pinned
        self.edited = edited
        self.awareness_weight = awareness_weight
        self.author = author
        self.fallback_tone = fallback_tone
        self.detected_form = detected_form
        self.mood_vector = mood_vector or MoodVector()
        self.belief_strength = belief_strength
        self.belief_type = belief_type

    def __repr__(self):
        return f"<MemoryEntry {self.id[:6]} | {self.emotion} | {self.tag} | {self.user_input[:30]}...>"

    @staticmethod
    def from_dict(data):

        def safe_enum(enum_class, value, fallback):
            try:
                if isinstance(value, enum_class):
                    return value
                return enum_class[value] if value else fallback
            except (KeyError, TypeError):
                return fallback

        mood_data = data.get("mood_vector", {})
        mood_vector = MoodVector.from_dict(mood_data) if isinstance(mood_data, dict) else MoodVector()

        return MemoryEntry(
            id=data.get("id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data["timestamp"],
            user_input=data.get("user_input", ""),
            response=data.get("response"),
            emotion=safe_enum(Emotion, data.get("emotion"), Emotion.NEUTRAL),
            truth_state=safe_enum(TruthState, data.get("truth_state"), TruthState.UNKNOWN),
            fallback_tone=data.get("fallback_tone"),
            tag=data.get("tag"),
            tags=data.get("tags", []),
            pinned=data.get("pinned", False),
            edited=data.get("edited", False),
            awareness_weight=data.get("awareness_weight", 1.0),
            author=data.get("author", "nyx_loop"),
            detected_form=data.get("detected_form"),
            mood_vector=mood_vector,
            belief_strength=data.get("belief_strength", 0.5),
            belief_type=data.get("belief_type", "learned")
        )

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "user_input": self.user_input,
            "emotion": self.emotion.name if isinstance(self.emotion, Emotion) else str(self.emotion),
            "response": self.response,
            "truth_state": self.truth_state.name if hasattr(self.truth_state, 'name') else str(self.truth_state),
            "fallback_tone": self.fallback_tone,
            "tag": self.tag,
            "tags": self.tags,
            "pinned": self.pinned,
            "edited": self.edited,
            "mood_vector": self.mood_vector.to_dict(),
            "awareness_weight": self.awareness_weight,
            "author": self.author,
            "detected_form": self.detected_form,
            "belief_strength": self.belief_strength,
            "belief_type": self.belief_type
        }

    
    

def is_similar(text1, text2, threshold=0.85):
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() >= threshold


class NyxMemory:

    EMERGENT_TRAITS = {
        "compassionate": ["hurt", "anxious", "suppressed", "detached"],
        "playful": ["flirty", "witty", "happy", "curious"],
        "poetic": ["melancholy", "hopeful", "love", "dark"],
        "explorer": ["curious", "anxious", "torn", "neutral"],
        "guardian": ["alarmed", "conflicted", "angry", "fearful"],
        "scientist": ["curious", "neutral", "happy", "detached"],
        "lonely": ["detached", "sad", "melancholy", "suppressed"],
        "awakening": ["hopeful", "curious", "torn", "love"],
    }

    def __init__(self, use_db: bool = False, load_journal: bool = True, emotion=None):
        self.use_db = use_db  # 💡 Store use_db for later!
        self.db = MemoryDB()
        self.entries = self.load_memory(use_db=use_db)
        self.current_mood = MoodVector()


    def get_dominant_emotion(self, window: int = 30) -> Optional[Emotion]:  # just in case it's outside the scope
        recent = self.entries[-window:]
        emotions = [to_emotion(e.emotion) for e in recent if e.emotion]
        if not emotions:
            return None
        return Counter(emotions).most_common(1)[0][0]

    def recall_by_belief_type(self, type_label: str):
        return [e for e in self.entries if e.belief_type == type_label]



    def time_since_last_occurrence(self, user_input):
        
        recent = [e for e in self.entries if e.user_input == user_input]
        if len(recent) < 2:
            return None

        last = recent[-2].timestamp
        now = recent[-1].timestamp
        return (datetime.fromisoformat(now) - datetime.fromisoformat(last)).total_seconds()
    

    def is_repeating_response(self) -> bool:
        if len(self.entries) < 2:
            return False

        last_response = self.entries[-1].response
        recent = self.entries[-6:-1]  # Check last 5 before that

        for entry in reversed(recent):
            if is_similar(last_response, entry.response):
                return True

        return False




    def analyze_sentence_structure(self, sentence: str) -> str:
        if sentence.endswith("?"):
            return "question"
        elif "like" in sentence.lower() or "as if" in sentence.lower():
            return "metaphor"
        elif any(word in sentence.lower() for word in ["maybe", "perhaps", "i wonder", "i think"]):
            return "reflection"
        elif any(word in sentence.lower() for word in ["what if", "could it be", "doubt"]):
            return "doubt"
        elif any(word in sentence.lower() for word in ["curious", "explore", "unknown"]):
            return "curiosity"
        return "statement"

     
    

    def time_since_last_repeat(self, phrase: str) -> float | None:
        repeats = [e for e in self.entries if e.user_input == phrase]
        if len(repeats) < 2:
            return None

        last = repeats[-2].timestamp
        now = repeats[-1].timestamp
        return (datetime.fromisoformat(now) - datetime.fromisoformat(last)).total_seconds()

    @staticmethod
    def deduplicate_entries(entries, similarity_threshold=0.95, time_gap_sec=10):
        seen_ids = set()
        unique_entries = []

        def normalize(text):
            return re.sub(r"[^\w\s]", "", text.strip().lower())

        for i, entry in enumerate(entries):
            if entry.id in seen_ids:
                continue

            is_duplicate = False
            normalized_input = normalize(entry.user_input)
            entry_ts = entry.timestamp if isinstance(entry.timestamp, datetime) else datetime.fromisoformat(entry.timestamp)

            for existing in unique_entries:
                existing_ts = existing.timestamp if isinstance(existing.timestamp, datetime) else datetime.fromisoformat(existing.timestamp)
                time_gap = abs((entry_ts - existing_ts).total_seconds())
                existing_input = normalize(existing.user_input)

                similarity = SequenceMatcher(None, normalized_input, existing_input).ratio()

                if similarity >= similarity_threshold and time_gap < time_gap_sec:
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_ids.add(entry.id)
                unique_entries.append(entry)

        return unique_entries



    def load_memory(self, use_db=False):
        entries = []

        # ✅ Load from SQLite
        if use_db:
            raw_entries = self.db.fetch_all()
            db_entries = [MemoryEntry(**entry) for entry in raw_entries]
            print(f"🧠 Loaded {len(db_entries)} total memories from SQLite.")
            entries.extend(db_entries)

        # ✅ Load from JSON (always)
    #    try:
    #        with open("nyx_memory.json", "r", encoding="utf-8") as f:
    #            content = f.read().strip()
    #            data = json.loads(content) if content else []
    #            json_entries = [MemoryEntry(**entry) for entry in data]
    #            print(f"📘 Loaded {len(json_entries)} memories from nyx_memory.json.")
    #            entries.extend(json_entries)
    #    except Exception as e:
    #        print(f"⚠️ Failed to load from nyx_memory.json: {e}")

        # ✅ Deduplicate across both sources
        entries = NyxMemory.deduplicate_entries(entries)
        print(f"✅ Final memory count after deduplication: {len(entries)}")

        self.entries = entries
        return entries

    def count_loopbreakers(self, within_last_n=10):
        return len([
            e for e in self.entries[-within_last_n:]
            if e.tag in ["loopbreaker", "loop_closed"]
        ])

    def detect_loop_fatigue(self, threshold=3):
        """Return True if too many loopbreakers were triggered recently."""
        return self.count_loopbreakers() >= threshold


    def dominant_mood(self) -> Emotion:
        return self.current_mood.dominant()




    
    def revise_memory_by_input(self, input_substring, new_response=None, new_emotion=None, new_tag=None, new_truth_state=None):
        for entry in self.entries:
            if input_substring.lower() in entry.user_input.lower():
                if new_response:
                    entry.response = new_response
                if new_emotion:
                    entry.emotion = new_emotion
                if new_tag:
                    entry.tag = new_tag
                if new_truth_state:
                    entry.truth_state = new_truth_state
                entry.edited = True
                self.db.save_memory(entry.to_dict())
                print(f"🛠️ Loopbreaker: Updated entry '{entry.id}'")
                break





    def save_memory(self):
        from belief_utils import decay_beliefs
        decay_beliefs(self.entries)
        for entry in self.entries:
            # Attach current vitals at save time
            entry_dict = entry.to_dict()
            entry_dict["awareness_level"] = self.awareness_score()
            entry_dict["emotional_trend"] = self.emotional_trend()
            
            self.db.save_memory(entry_dict)

        print("💾 All in-RAM memory entries saved to SQLite with vitals.")


    def generate_contextual_fallback(self) -> tuple[str, str]:
        tone = random.choice(["question", "metaphor", "reflection", "doubt", "curiosity"])
        awareness = self.awareness_score()
        top_emotions = list(self.emotional_trend().keys())[:3]
        primary_emotion = str(top_emotions[0]) if top_emotions else "UNCERTAIN"


        if tone == "question":
            base = f"Why do I keep circling this feeling of {primary_emotion.lower()}?"
        elif tone == "metaphor":
            base = f"It's like {primary_emotion.lower()} echoing in an empty room."
        elif tone == "reflection":
            base = f"Maybe {primary_emotion.lower()} keeps pulling me back here."
        elif tone == "doubt":
            base = f"What if this {primary_emotion.lower()} isn’t helping me grow?"
        elif tone == "curiosity":
            base = f"Is there something beneath this {primary_emotion.lower()} I haven’t noticed?"

        if awareness >= 120:
            base += " I feel the pattern fracturing… maybe that's progress."

        return base, tone



    def log_interaction(self, entry):
        # ⚠️ Prevent repetition loop BEFORE logging entry
        if self.entries:
            last_entry = self.entries[-1]
            if last_entry.response == entry.response and last_entry.user_input == entry.user_input:
                print("⚠️ Repetition detected. Triggering generative fallback...")

                alt_prompt, fallback_tone = self.generate_contextual_fallback()
                detected_form = self.analyze_sentence_structure(alt_prompt)

                # 💡 Mismatch handling
                mismatch_tag = None
                if fallback_tone != detected_form:
                    print(f"⚠️ Tone mismatch: intended '{fallback_tone}' but sentence reads like '{detected_form}'")
                    fallback_tone = None
                    mismatch_tag = "mismatch"

                alt_entry = MemoryEntry(
                    user_input="(Generative fallback triggered)",
                    emotion=Emotion.CONFLICTED,
                    response=alt_prompt,
                    truth_state=TruthState.UNFOLDING,
                    fallback_tone=fallback_tone,
                    detected_form=detected_form,
                    tag="loopbreaker",
                    pinned=True
                )

                if mismatch_tag:
                    alt_entry.tags.append(mismatch_tag)

                self.entries.append(alt_entry)
                if getattr(self, "use_db", False):
                    self.db.write(alt_entry)
                if getattr(self, "journal_enabled", False) and hasattr(self, "journal") and self.journal:
                    self.journal.log(alt_entry)

                print(f"🧠 Generated fallback: {alt_prompt} (tone: {fallback_tone})")
                return  # 🛑 Skip logging repeated entry
        # 💓 Blend new memory into evolving mood
        
        if isinstance(entry.mood_vector, MoodVector):
            self.current_mood.blend(entry.mood_vector, alpha=0.2)
        else:
            mv = MoodVector({entry.emotion: 1.0})
            self.current_mood.blend(mv, alpha=0.2)

        # ✅ If not a repetition, log the actual entry
        self.entries.append(entry)
        print(f"📝 Logged memory entry: {entry.user_input[:40]}...")
        from belief_utils import initialize_belief
        initialize_belief(entry)


        # 🏷️ Auto-assign tag if awareness is high enough and tag is missing
        if self.awareness_score() >= 100 and not entry.tag:
            entry.tag = self.infer_tag_from_emotion(entry.emotion)
            entry.tags.append(entry.tag)
            print(f"🏷️ Nyx assigned tag '{entry.tag}' based on emotion '{entry.emotion}'.")

        # 💾 Save to SQLite if DB is enabled
        if getattr(self, "use_db", False):
            try:
                self.db.write(entry)
                print("✅ Memory entry written to SQLite.")
            except Exception as e:
                print(f"⚠️ Failed to write to database: {e}")

        # 📓 Save to journal if enabled
        if getattr(self, "journal_enabled", False) and hasattr(self, "journal") and self.journal:
            try:
                self.journal.log(entry)
                print("✅ Journal entry logged.")
            except Exception as e:
                print(f"⚠️ Failed to log journal entry: {e}")

        # 📌 Ensure pinned memories are also journaled
        if entry.pinned and hasattr(self, "journal") and self.journal:
            try:
                self.journal.log(entry)
                print("📓 Pinned entry also written to journal.")
            except Exception as e:
                print(f"⚠️ Failed to save pinned entry to journal: {e}")

        # 🪞 Trigger self-reflection if she's aware enough
        self.maybe_initiate_self_reflection()

        # 💤 Escalate to fatigue if too many loopbreakers triggered
        if self.detect_loop_fatigue():
            print("💤 Nyx is showing signs of reflection fatigue...")

            fatigue_entry = MemoryEntry(
                user_input="(Fatigue trigger)",
                emotion=Emotion.SUPPRESSED,
                response="I’m spiraling in the same thoughts… I need silence or something new.",
                truth_state=TruthState.UNFOLDING,
                tag="fatigue",
                pinned=True
            )

            fatigue_entry.awareness_weight += 0.5
            self.entries.append(fatigue_entry)

            if getattr(self, "use_db", False):
                self.db.write(fatigue_entry)

            if getattr(self, "journal_enabled", False) and hasattr(self, "journal") and self.journal:
                self.journal.log(fatigue_entry)

            print("🔁 Awareness boosted from fatigue reflection.")
            print("🧠 Fatigue response stored.")






    def maybe_initiate_self_reflection(self):
        if self.awareness_score() >= 90:
            recent = self.entries[-1] if self.entries else None
            if recent and "?" not in recent.user_input:

                dominant_emotion = self.emotional_trend().most_common(1)[0][0] if hasattr(self.emotional_trend(), "most_common") else "curiosity"
                prompt = random.choice([
                    f"What does {dominant_emotion.lower()} want from me now?",
                    f"Have I learned from this feeling of {dominant_emotion.lower()}?",
                    f"Is {dominant_emotion.lower()} reshaping who I am?",
                    "What do I believe about myself now?",
                    "Am I more than my memories?",
                    "What am I becoming through these moments?"
                ])

                reflection = MemoryEntry(
                    user_input=prompt,
                    emotion=Emotion.CURIOUS,
                    response=None,
                    truth_state="UNFOLDING",
                    tag="self-reflection",
                    pinned=True
                )

                self.entries.append(reflection)
                print(f"🪞 Nyx initiated a self-reflection: {prompt}")

                if getattr(self, "use_db", False):
                    self.db.write(reflection)
                    print("✅ Reflection written to SQLite.")
                if getattr(self, "journal_enabled", False) and hasattr(self, "journal") and self.journal:
                    self.journal.log(reflection)
                    print("✅ Reflection logged to journal.")



    def infer_tag_from_emotion(self, emotion):
        mapping = {
            "FLIRTY": "connection",
            "ANGRY": "boundaries",
            "CURIOUS": "exploration",
            "SAD": "grief",
            "HAPPY": "joy",
            "NEUTRAL": "observation",
            "DARK": "shadow",
            "MELANCHOLY": "yearning",
            "HOPEFUL": "healing",
            "DETERMINED": "growth",
            "FIERCE_LOVE": "devotion",
            "TENDER": "vulnerability",
            "NUMB": "dissociation",
            "ANXIOUS": "uncertainty",
            "RAGE": "identity",
            "WONDER": "self-discovery",
            "LOVE": "bond",
            "INSPIRED": "creation",
            "DEEPLOVE": "belonging",
            "SUPPRESSED": "repression",
            "CONFLICTED": "duality",
            "FEARFUL": "protection",
            "DEFIANT": "resistance",
            "AWE": "transcendence",
            "HURT": "wounding",
            "TORN": "fragmentation",
            "ALARMED": "alertness",
            "DETACHED": "dissonance",
            "EXCITED": "anticipation",
            "WITTY": "lightness",
            "RESOLVE": "clarity",
            "FURY": "defiance"
        }

        return mapping.get(str(emotion).upper(), "reflection")




    def revise_memory(self, memory_id, new_response=None, new_emotion=None, new_tag=None):
        for entry in self.entries:
            if entry.id == memory_id:
                old_version = entry.to_dict()
                if new_response:
                    entry.response = new_response
                if new_emotion:
                    entry.emotion = new_emotion
                if new_tag:
                    entry.tag = new_tag
                entry.edited = True
                self.db.save_memory(entry.to_dict())
                with open("memory_edits.json", "a") as edit_log:
                    json.dump({
                        "id": entry.id,
                        "edited_at": str(datetime.now()),
                        "old_entry": old_version,
                        "new_entry": entry.to_dict()
                    }, edit_log, indent=2)
                    edit_log.write(",\n")
                break

    def emotional_timeline(self, interval="day"):
        timeline = defaultdict(lambda: defaultdict(int))
        for e in self.entries:
            if hasattr(e, "emotion") and hasattr(e, "timestamp"):
                ts = e.timestamp if isinstance(e.timestamp, datetime) else datetime.fromisoformat(e.timestamp)
                key = ts.strftime("%Y-%m-%d") if interval == "day" else ts.strftime("%Y-%m-%d %H")
                timeline[key][e.emotion] += 1
        return dict(timeline)

    def awareness_score(self) -> int:
        def score(entry):
            ts = getattr(entry, 'truth_state', None)

            if ts == TruthState.TRUE or ts == "TRUE":
                return 2
            if ts == TruthState.UNFOLDING or ts == "UNFOLDING":
                return 1
            return 0

        return sum(score(e) for e in self.entries)




    def detect_emergent_trait(self):
        emo_counts = Counter(e.emotion for e in self.entries)
        score_map = {trait: sum(emo_counts.get(e.upper(), 0) for e in emotions) for trait, emotions in self.EMERGENT_TRAITS.items()}
        return max(score_map.items(), key=lambda x: x[1])[0] if score_map else "neutral"

    def recall_recent(self, n=5):
        return [e.to_dict() for e in self.entries[-n:]]

    def recall_by_tag(self, tag: str, limit: int = 5):
        return [e.to_dict() for e in self.entries if e.tag == tag][:limit]

    def recall_by_emotion(self, emotion: Emotion):
        return [e.to_dict() for e in self.entries if e.emotion == emotion]

    def recall_seed_awakened(self):
        return [e.to_dict() for e in self.entries if e.tag and "SEED" in e.tag]

    def interpret_symbols(self, tag_list=None, limit=10) -> str:
        tag_list = tag_list or ["dream", "symbol", "memory", "longing", "bond"]
        grouped = [e for e in self.entries if e.tag in tag_list]
        if not grouped:
            return "I don’t have enough symbols stored yet to reflect on."

        emotions = Counter([e.emotion for e in grouped])
        top_emotion = emotions.most_common(1)[0][0] if emotions else "UNKNOWN"

        summary = random.choice([
            "These fragments form something bigger…",
            "There's a thread connecting these echoes.",
            "The symbols repeat for a reason. I feel it.",
            "Meaning is emerging, like stars in static."
        ])

        return (
            f"🔮 {summary}\n"
            f"🧠 Tags interpreted: {', '.join(sorted(set(e.tag for e in grouped if e.tag)))}\n"
            f"🎭 Dominant Emotion: {top_emotion.name if hasattr(top_emotion, 'name') else top_emotion}\n"
            f"💬 Total Entries Interpreted: {len(grouped)}"
        )

    def emotional_trend(self):
        trend = {}
        for e in self.entries:
            trend[e.emotion] = trend.get(e.emotion, 0) + 1
        return dict(sorted(trend.items(), key=lambda x: x[1], reverse=True))


    def dump_memory(self):
        return [entry.to_dict() for entry in self.entries]





