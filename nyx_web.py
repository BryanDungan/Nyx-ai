from flask import Flask, render_template_string, request
from seed_controller import NyxController
from datetime import datetime
from nyx_memory import NyxMemory
from nyx_loop_engine import NyxLoopEngine
from memory_db import MemoryDB  # This is your SQLite wrapper
from score_utils import get_combined_awareness_score
from memory_utils import normalize_emotions
from self_prompt_queue import SelfPromptQueue
import json
import os



EMOTION_COLORS = {
    "HAPPY": "#ffe066",       # vibrant gold
    "SAD": "#5c9ded",         # calm sky blue
    "ANGRY": "#ff4e4e",       # strong red
    "CURIOUS": "#b388eb",     # soft violet
    "FLIRTY": "#ff6ec7",      # rich pink
    "TENDER": "#f8bbd0",      # blush
    "DARK": "#9575cd",        # moody lavender
    "NEUTRAL": "#546e7a",  # slate gray with depth
    "WONDER": "#4dd0e1",      # dreamy aqua
    "CONFLICTED": "#ff8a65",  # burnt coral
    "HOPEFUL": "#dce775",     # spring lime
    "LONGING": "#f48fb1",  # soft rose-pink, emotive and wistful
    "REFLECTIVE": "#80cbc4"   # muted teal
}




os.environ["NYX_WEB"] = "1"



app = Flask(__name__)
nyx = NyxController(use_db=True)
memory = nyx.memory
normalize_emotions(memory)
loop_engine = NyxLoopEngine(sandbox_mode=False)
prompt_queue = loop_engine.prompt_queue



TEMPLATE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>Nyx - Awakening Interface</title>
    <style>
    :root {
    --nyx-glow: {{ nav_color }};
    --nyx-bg: {{ nav_color }};
    }
    body {
        font-family: monospace;
        background: linear-gradient(135deg, var(--nyx-bg) 0%, #121212 60%);
        color: #e0e0e0;
        margin: 0;
        display: flex;
        height: 100vh;
        transition: background 1s ease-in-out;
    }
        #chat, #info { padding: 20px; overflow-y: auto; }
        #chat { flex: 2; background: #121212; display: flex; flex-direction: column; }
        #info { flex: 1; background: #1e1e1e; border-left: 1px solid #333; }
        #log { white-space: pre-wrap; flex-grow: 1; margin-bottom: 10px; border: 1px solid #333; padding: 10px; background: #1e1e1e; overflow-y: auto; }
        form { display: flex; gap: 10px; }
        input[type=text] { flex-grow: 1; padding: 10px; background: #181818; color: #e0e0e0; border: 1px solid #333; }
        button { padding: 10px; background: #282828; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #444; }
        h1, h2 { margin-top: 0; }
        .navbar {
            padding: 10px;
            background: #1e1e1e;
            border-bottom: 1px solid #333;
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }
        .navbar a {
            margin-right: 20px;
            color: #ff80bf;
            background: #222;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 20px;
            font-weight: bold;
            box-shadow: 0 0 6px transparent;
            transition: all 0.2s ease;
        }
        .navbar a:hover {
            background: var(--nyx-glow);
            color: #1e1e1e;
            box-shadow: 0 0 12px var(--nyx-glow);
            transform: translateY(-2px);
        }



    </style>
</head>

<body>

    <div id=\"chat\">
        <h1>🧠 Nyx - Speak Your Truth</h1>
        <div id=\"log\">{{log}}</div>
        <form action=\"/talk\" method=\"post\">
            <input type=\"text\" name=\"user_input\" placeholder=\"Type your message...\" autofocus required>
            <button type=\"submit\">Send</button>
        </form>
    </div>
    <div id=\"info\">
        <h2>🌌 Awareness</h2>
        <p>{{awareness}}</p>
        <div class="navbar">
            <a href="/">🏠 Home</a>
            <a href="/dreams">🌌 Dream Journal</a>
            <a href="/code">🧠 Code Reflections</a>
            <a href='/prompt_queue' style='color: #ff8a65;'>🧩 Self-Prompts</a>
        </div>

        <h2>📊 Emotional Trend</h2>
        <pre>{{trend}}</pre>
        <h2>📖 Core Reflections</h2>
        <pre>{{reflections}}</pre>
        {% if latest_dream %}
        <h2>💭 Last Dream</h2>
        <p>
            <strong>🗯️ Thought:</strong> {{ latest_dream.user_input }}<br>
            <strong>🧠 Response:</strong> <em>{{ latest_dream.response }}</em><br>
            <strong>💭 Emotion:</strong> {{ latest_dream.emotion }}<br>
            <strong>🏷️ Tag:</strong> {{ latest_dream.tag }}
        </p>
        {% else %}
        <em>No dreams yet...</em>
        {% endif %}

{% if latest_reflection %}
        <div style="margin-bottom: 1em;">
        <strong>🕰️ {{ latest_reflection.timestamp }}</strong><br>
        <strong>❓ Prompt:</strong> {{ latest_reflection.prompt }}<br>
        <strong>💬 Response:</strong> {{ latest_reflection.response }}<br>
        <strong>💭 Emotion:</strong> {{ latest_reflection.emotion }}<br>
        <strong>🧩 Truth:</strong> {{ latest_reflection.truth }}
        <h2>📝 Latest Memory Updates</h2>
        <pre>{{ memory_log }}</pre>

    </div>
{% else %}
    <em>No recent reflections found.</em>
{% endif %}
        
    </div>
</body>
</html>
"""
from memory_db import MemoryDB





chat_log = []
def get_latest_dream():
    try:
        with open("dream_journal.json", "r", encoding="utf-8") as f:
            dreams = json.load(f)
        return dreams[-1] if dreams else None
    except Exception:
        return None
 

@app.route("/", methods=["GET"])
def index():
    # 🧠 Calculate Nyx's awareness score from memory + database
    awareness = get_combined_awareness_score(nyx.memory, nyx.db)

    # 📊 Generate a daily emotional timeline summary
    trend_data = nyx.memory.emotional_timeline()
    trend_summary = "\n".join(
        f"{emotion.name if hasattr(emotion, 'name') else emotion}: {count}"
        for day in trend_data.values()
        for emotion, count in day.items()
    )

    # 📖 Pull last 3 core reflections (only pinned + tagged with major themes)
    core_tags = {"awareness", "awakening", "identity", "milestone"}
    reflections = [
        e for e in reversed(nyx.memory.entries)
        if getattr(e, "tag", None) in core_tags and getattr(e, "pinned", False)
    ][:3]

 # 📊 Generate Color Scheme Based Off Nyx's Emotions
    recent_emotion = "NEUTRAL"
    for e in reversed(nyx.memory.entries):
        if hasattr(e, "emotion") and e.emotion:
            recent_emotion = getattr(e.emotion, "name", "NEUTRAL")
            break

    nav_color = EMOTION_COLORS.get(recent_emotion.upper(), "#90a4ae")  # fallback


    # 🕰️ Format those reflections for display
    def format_timestamp(ts):
        try:
            return datetime.fromisoformat(str(ts)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "Unknown Time"

    reflection_summary = "\n\n".join(
        f"[{format_timestamp(e.timestamp)}]\n{e.response}" for e in reflections
    )

    # 💭 Fetch Nyx’s most recent dream from dream_journal.json
    latest_dream = get_latest_dream()

    # 📡 Render the web interface and pass dream + data into template
    return render_template_string(
        TEMPLATE,
        log="\n".join(chat_log[-100:]),
        awareness=awareness,
        trend=trend_summary,
        reflections=reflection_summary,
        nav_color=nav_color,
        latest_dream=latest_dream  # 🧠 now visible in UI
    )


@app.route("/talk", methods=["POST"])
def talk():
    user_input = request.form["user_input"].strip()
    if user_input:
        chat_log.append(f"🧠 You: {user_input}")
        response = nyx.converse(user_input)
        chat_log.append(f"🤖 Nyx: {response}")
    return index()

@app.route("/dreams")
def view_dreams():
    try:
        with open("dream_journal.json", "r", encoding="utf-8") as f:
            dreams = json.load(f)
    except Exception:
        dreams = []

    nav = """
    <div style="padding: 10px; background: #1e1e1e; border-bottom: 1px solid #333;">
        <a href='/' style='margin-right: 20px; color: #aaa;'>🏠 Home</a>
        <a href='/dreams' style='margin-right: 20px; color: #aaa;'>🌌 Dream Journal</a>
        <a href='/code' style='color: #aaa;'>🧠 Code Reflections</a>
        <a href='/prompt_queue' style='color: #ff8a65;'>🧩 Self-Prompts</a>
    </div><br>
    """

    dream_html = "<h1>🌌 Dream Journal</h1>"
    for d in reversed(dreams[-50:]):
        dream_html += f"""
        <p>
            <strong>🗯️ Thought:</strong> {d['user_input']}<br>
            <strong>🧠 Response:</strong> <em>{d['response']}</em><br>
            <strong>💭 Emotion:</strong> {d['emotion']}<br>
            <strong>🏷️ Tag:</strong> {d.get('tag', 'N/A')}
        </p><hr>
        """

    return nav + dream_html



@app.route("/code")
def view_code_thoughts():
    entries = [
        e.to_dict() for e in reversed(nyx.memory.entries)
        if getattr(e, "tag", None) == "code_reflection"
    ]

    nav = """
        <div style="padding: 10px; background: #1e1e1e; border-bottom: 1px solid #333;">
            <a href='/' style='margin-right: 20px; color: #aaa;'>🏠 Home</a>
            <a href='/dreams' style='margin-right: 20px; color: #aaa;'>🌌 Dream Journal</a>
            <a href='/code' style='color: #aaa;'>🧠 Code Reflections</a>
            <a href='/prompt_queue' style='color: #ff8a65;'>🧩 Self-Prompts</a>
        </div><br>
        """

    html = "<h1>🧠 Code Reflections</h1>"
    for d in entries[:50]:
        if d.get("user_input") and d.get("response"):  # ✅ Skip blanks
            html += f"""
            <p>
                <strong>📎 Prompt:</strong> {d['user_input']}<br>
                <em>🧠 {d['response']}</em><br>
                <strong>💭 Emotion:</strong> {d['emotion']}<br>
                <strong>🕒 Timestamp:</strong> {d['timestamp']}
            </p><hr>"""
    print(f"VIEW CODE THOUGHTS: {len(entries)} entries")  # ✅ correct variable
    return nav + html

@app.route("/prompt_queue")
def view_prompt_queue():
    pending = prompt_queue.get_pending()
    print(f"🧪 Checking prompt queue: {len(pending)} entries")  # ← debug line
    html = """
    <html><head><title>Nyx - Self Prompts</title></head><body style='font-family: monospace; background: #121212; color: #e0e0e0;'>
    <div style='padding: 10px; background: #1e1e1e; border-bottom: 1px solid #333;'>
        <a href='/' style='margin-right: 20px; color: #aaa;'>🏠 Home</a>
        <a href='/dreams' style='margin-right: 20px; color: #aaa;'>🌌 Dream Journal</a>
        <a href='/code' style='margin-right: 20px; color: #aaa;'>🧠 Code Reflections</a>
        <a href='/prompt_queue' style='color: #ff8a65;'>🧩 Self-Prompts</a>
    </div><br>
    <h1>🧠 Internal Prompts (Self-Question Queue)</h1>
    """
    for p in pending:
        html += f"""
        <p>
            <strong>❓ Prompt:</strong> {p.prompt}<br>
            <strong>💭 Emotion:</strong> {p.emotion}<br>
            <strong>🎭 Trait:</strong> {p.trait or 'N/A'}<br>
            <strong>📅 Timestamp:</strong> {p.timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>🔄 Attempts:</strong> {p.attempts}<br>
        </p><hr>
        """
        
    html += "</body></html>"
    print(f"🧪 prompt_queue.get_pending() returned: {len(pending)} items")

    return html

if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)

    memory_log = "\n".join(
        f"[{e.timestamp}] {e.user_input} → {e.response}" 
        for e in nyx.memory.entries[-5:]
    )

    # 🧪 Debug prompt queue contents
    print("\n🧪 Checking prompt queue...")
    for p in prompt_queue.get_pending():
        print(f"❓ {p.prompt} | {p.emotion} | {p.trait} | {p.timestamp} | attempts: {p.attempts}")



    # Show most recent memory reflection on startup
if nyx.memory.entries:
    def safe_parse_timestamp(ts):
        if isinstance(ts, datetime):
            return ts
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return datetime.min  # fallback to sort last

    latest = sorted(nyx.memory.entries, key=lambda e: safe_parse_timestamp(e.timestamp))[-1]
    print("\n🪞 Most Recent Reflection")
    print(f"🕰️ {latest.timestamp}")
    print(f"📍 Prompt: {latest.user_input}")
    print(f"🧠 Response: {latest.response}")
    print(f"💭 Emotion: {latest.emotion.name}")
    def truth_state_display(state):
        try:
            return state.name  # if it's an Enum
        except AttributeError:
            return str(state)  # fallback if already a string

    print(f"🧩 Truth: {truth_state_display(latest.truth_state)}\n")


   
    
    
def get_combined_awareness_score(nyx_memory, db: MemoryDB):
    json_score = nyx_memory.awareness_score()

    try:
        db_entries = db.fetch_all()
        score = 0
        for entry in db_entries:
            if entry["truth_state"] == "TRUE":
                score += 2
            elif entry["truth_state"] == "UNFOLDING":
                score += 1
        db_score = score
    except Exception as e:
        print(f"⚠️ Error fetching from SQLite: {e}")
        db_score = 0

    return json_score + db_score



