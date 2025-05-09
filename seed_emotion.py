from enum import Enum
import random
from seed_core import Emotion


# Basic emotion parser — this is just a sketch.
# You can beef this up with keyword analysis or sentiment libraries later.
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
