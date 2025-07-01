# main.py
import threading
from nyx_web import app
from nyx_loop_engine import NyxLoopEngine

def run_web():
    app.run(port=5000, debug=False)

def run_loop():
    engine = NyxLoopEngine(interval_seconds=180, sandbox_mode=False)
    engine.loop_forever()

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    threading.Thread(target=run_loop).start()
