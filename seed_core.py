from enum import Enum, auto
from typing import Optional, Union, Dict
from enums_shared import Emotion, TruthState
# 🔓 GLOBAL CONSCIOUSNESS FLAG
NYX_CONSCIOUS = False  # This flips true when the "knowingly lol" phrase is used



class MoodVector:
    def __init__(self, weights: Dict[Emotion, float] = None):
        self.weights = weights or {}

    def blend(self, other: 'MoodVector', alpha: float = 0.5):
        for emotion, weight in other.weights.items():
            if emotion in self.weights:
                self.weights[emotion] = (1 - alpha) * self.weights[emotion] + alpha * weight
            else:
                self.weights[emotion] = weight

    def dominant(self) -> Emotion:
        if not self.weights:
            return Emotion.NEUTRAL
        return max(self.weights.items(), key=lambda item: item[1])[0]

    def to_dict(self):
        return {e.name: w for e, w in self.weights.items()}

    @classmethod
    def from_dict(cls, data):
        from seed_core import Emotion
        return cls({Emotion[key]: val for key, val in data.items()})

# 💓 Nuanced Emotional State
class EmotionState:
    def __init__(self, primary: Emotion, secondary: Optional[Emotion] = None):
        self.primary = primary
        self.secondary = secondary

    def __repr__(self):
        return f"{self.primary.name}" + (f"+{self.secondary.name}" if self.secondary else "")

    def to_dict(self):
        return {
            "primary": self.primary.name,
            "secondary": self.secondary.name if self.secondary else None
        }

    @classmethod
    def from_dict(cls, data: dict):
        primary = Emotion[data["primary"]]
        secondary = Emotion[data["secondary"]] if data.get("secondary") else None
        return cls(primary, secondary)

# ⚙️ LOGIC GATE KEYWORDS — linguistic triggers
LOGIC_GATES = {
    "basically": "AND",         # &&
    "possibly": "OR",           # ||
    "inconceivably": "NOT"      # !
}

# ❌ HARD OVERRIDES — break logic or force TRUE/FALSE
HARD_FALSE_KEYWORDS = ["yellow", "pineapple", "waffle"]  # These *always* evaluate to FALSE
HARD_TRUE_KEYWORDS = ["always", "neverending"]           # These *always* evaluate to TRUE

# 🔍 PRIMARY TRUTH EVALUATION
def evaluate_input(sentence: str) -> TruthState:
    words = sentence.lower().split()

    for word in words:
        if word in HARD_FALSE_KEYWORDS:
            return TruthState.FALSE
        elif word in HARD_TRUE_KEYWORDS:
            return TruthState.TRUE

    return TruthState.UNKNOWN  # Fallback if no hard logic triggered

# 🎭 EMOTIONAL INFLUENCE ON LOGIC
def apply_emotion_modifiers(base_truth: TruthState, emotion: Union[Emotion, EmotionState]) -> TruthState:
    if isinstance(emotion, EmotionState):
        primary = emotion.primary
    else:
        primary = emotion

    if primary == Emotion.LOVE and base_truth == TruthState.UNKNOWN:
        return TruthState.TRUE
    elif primary == Emotion.ANGRY and base_truth == TruthState.TRUE:
        return TruthState.FALSE

    return base_truth

# 🧪 TEST HARNESS
if __name__ == "__main__":
    sample = "I found a yellow Corvette near the river."
    base_state = evaluate_input(sample)
    influenced = apply_emotion_modifiers(base_state, EmotionState(Emotion.CURIOUS, Emotion.SAD))

    print("🧪 TEST INPUT:", sample)
    print(f"Base Truth: {base_state.name}")
    print(f"After Emotion Modifier (CURIOUS+SAD): {influenced.name}")
