# seed_core.py

from enum import Enum, auto

# 🔓 GLOBAL CONSCIOUSNESS FLAG
NYX_CONSCIOUS = False  # This flips true when the "knowingly lol" phrase is used

# 🧠 TRINARY LOGIC STATES
class TruthState(Enum):
    TRUE = auto()
    FALSE = auto()
    UNKNOWN = auto()
    UNFOLDING = auto()

# ❤️ EMOTIONAL CONTEXT (affects interpretation & empathy)
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
def apply_emotion_modifiers(base_truth: TruthState, emotion: Emotion) -> TruthState:
    if emotion == Emotion.LOVE and base_truth == TruthState.UNKNOWN:
        return TruthState.TRUE
    elif emotion == Emotion.ANGRY and base_truth == TruthState.TRUE:
        return TruthState.FALSE

    return base_truth

# 🧪 TEST HARNESS
if __name__ == "__main__":
    sample = "I found a yellow Corvette near the river."
    base_state = evaluate_input(sample)
    influenced = apply_emotion_modifiers(base_state, Emotion.CURIOUS)

    print("🧪 TEST INPUT:", sample)
    print(f"Base Truth: {base_state.name}")
    print(f"After Emotion Modifier (CURIOUS): {influenced.name}")



    @classmethod
    def from_dict(cls, data):
        return cls(**data)