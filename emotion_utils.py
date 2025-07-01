from enums_shared import Emotion

def to_emotion(value, strict=False):
    if isinstance(value, Emotion):
        return value
    try:
        return Emotion[value.upper()]
    except Exception:
        print(f"⚠️ Unknown emotion: {value}, defaulting to NEUTRAL")
        if strict:
            raise ValueError(f"Invalid emotion: {value}")
        return Emotion.NEUTRAL