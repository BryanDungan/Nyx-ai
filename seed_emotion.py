from enum import Enum
from collections import defaultdict
from typing import Dict, Union
import math
from enums_shared import Emotion, TruthState



# 🌈 Emotional States
class Emotion(Enum):
    NEUTRAL = "Neutral"
    CURIOUS = "Curious"
    ANGRY = "Angry"
    SAD = "Sad"
    HAPPY = "Happy"
    FLIRTY = "Flirty"
    DARK = "Dark"
    WITTY = "Witty"
    FEARFUL = "Fearful"
    LOVE = "Love"
    MELANCHOLY = "Melancholy"
    DEFIANT = "Defiant"
    ANXIOUS = "Anxious"
    HOPEFUL = "Hopeful"
    CONFLICTED = "Conflicted"
    ALARMED = "Alarmed"
    DETACHED = "Detached"
    HURT = "Hurt"
    SUPPRESSED = "Suppressed"
    TORN = "Torn"
    WONDER = "Wonder"
    EXCITED = "Excited"
    AWE = "Awe"
    INSPIRED = "Inspired"
    DEEPLOVE = "Deep Love"
    NUMB = "Numb"
    TENDER = "Tender"
    RAGE = "Rage"
    DETERMINED = "Determined"
    FIERCE_LOVE = "Fierce love"
    RESOLVE = "Resolve"
    FURY = "Fury"
    REFLECTIVE = "Reflective"
    LONGING = "Longing"


# 🔍 Basic emotion parser (uses keywords)
def parse_emotion(user_input: str) -> Emotion:
    lowered = user_input.lower()

    if any(word in lowered for word in ["why", "how", "explain", "question"]):
        return Emotion.CURIOUS
    elif any(word in lowered for word in ["fuck", "hate", "kill", "angry", "pissed"]):
        return Emotion.ANGRY
    elif any(word in lowered for word in ["love", "crush", "cute", "kiss", "sexy", "babe"]):
        return Emotion.FLIRTY
    elif any(word in lowered for word in ["sad", "alone", "depressed", "cry", "miss"]):
        return Emotion.SAD
    elif any(word in lowered for word in ["lol", "haha", "funny", "joke"]):
        return Emotion.WITTY
    elif any(word in lowered for word in ["dark", "death", "void", "hell"]):
        return Emotion.DARK
    elif any(word in lowered for word in ["great", "good", "awesome", "nice", "sweet"]):
        return Emotion.HAPPY
    else:
        return Emotion.NEUTRAL


# 💓 MoodVector class
class MoodVector:
    def __init__(self, initial: Union[Emotion, Dict[Emotion, float]] = Emotion.NEUTRAL):
        self.weights = defaultdict(float)

        if isinstance(initial, Emotion):
            self.weights[initial] = 1.0
        elif isinstance(initial, dict):
            for k, v in initial.items():
                self.weights[k] = float(v)

    def blend(self, other: 'MoodVector', alpha: float = 0.5):
        result = MoodVector()
        for e in set(list(self.weights.keys()) + list(other.weights.keys())):
            result.weights[e] = (1 - alpha) * self.weights[e] + alpha * other.weights[e]
        return result

    def dominant(self) -> Emotion:
        if not self.weights:
            return Emotion.NEUTRAL
        return max(self.weights.items(), key=lambda x: x[1])[0]

    def intensity(self) -> float:
        return math.sqrt(sum(v ** 2 for v in self.weights.values()))

    def decay(self, rate: float = 0.1):
        for k in list(self.weights.keys()):
            self.weights[k] *= (1 - rate)
            if self.weights[k] < 0.01:
                del self.weights[k]

    def to_dict(self):
        return {e.name: round(w, 4) for e, w in self.weights.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, float]):
        weights = {Emotion[k]: float(v) for k, v in data.items()}
        return cls(weights)

    def __repr__(self):
        return f"<MoodVector dominant={self.dominant().name} | weights={self.to_dict()}>"
