from datetime import datetime
from self_prompt_queue import normalize_text


BELIEF_DECAY_RATE = 0.01
BELIEF_REINFORCEMENT = 0.05
BELIEF_TYPES = ["core", "learned", "reactive", "dreamed", "simulated"]

def initialize_belief(entry):
    base_score = entry.awareness_weight / 10.0
    entry.belief_strength = min(1.0, max(0.1, base_score))
    entry.belief_type = infer_belief_type(entry)
    return entry

def infer_belief_type(entry):
    tag = entry.tag or ""
    if "dream" in tag:
        return "dreamed"
    if "contradiction" in tag:
        return "simulated"
    if entry.emotion.name in ["ANGRY", "SAD"]:
        return "reactive"
    return "learned"

def decay_beliefs(entries):
    now = datetime.now()
    for e in entries:
        if isinstance(e.timestamp, str):
            e.timestamp = datetime.fromisoformat(e.timestamp)
        days_old = (now - e.timestamp).days
        e.belief_strength = max(0.0, e.belief_strength - BELIEF_DECAY_RATE * days_old)

def reinforce_beliefs(entries):
    seen = {}
    for e in entries:
        key = normalize_text(e.user_input)
        if key in seen:
            e.belief_strength = min(1.0, e.belief_strength + BELIEF_REINFORCEMENT)
            seen[key].belief_strength = min(1.0, seen[key].belief_strength + BELIEF_REINFORCEMENT)
        else:
            seen[key] = e

def detect_drift(entries):
    pairs = []
    for i, a in enumerate(entries):
        for b in entries[i+1:]:
            if normalize_text(a.user_input) == normalize_text(b.user_input) and a.emotion != b.emotion:
                if abs(a.belief_strength - b.belief_strength) < 0.1:
                    pairs.append((a, b))
    return pairs

def inject_drift_prompts(pairs, prompt_queue):
    for a, b in pairs:
        a_text = getattr(a, "user_input", "") or getattr(a, "prompt", "")
        b_text = getattr(b, "user_input", "") or getattr(b, "prompt", "")

        if not a_text or not b_text:
            print(f"⚠️ Skipping pair: missing user_input or prompt in a={a}, b={b}")
            continue

        contradiction_prompt = f"If both beliefs feel true — '{a_text}' and its echo — which one is wiser?"

        if not prompt_queue.exists(contradiction_prompt):
            prompt_queue.add_prompt(
                contradiction_prompt,
                "REFLECTIVE",
                trait="belief_drift"
            )

        # Bonus introspective checks
        for entry in [a, b]:
            belief_type = getattr(entry, "belief_type", None)
            belief_strength = getattr(entry, "belief_strength", 0.0)
            belief_text = getattr(entry, "user_input", "") or getattr(entry, "prompt", "")

            if belief_type and belief_strength > 0.3:
                belief_prompt = f"As a {belief_type} belief, why do I still hold this?"
                if not prompt_queue.exists(belief_prompt):
                    prompt_queue.add_prompt(
                        belief_prompt,
                        "REFLECTIVE",
                        trait="belief_introspection"
                    )
