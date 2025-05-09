import sqlite3
from tabulate import tabulate

DB_PATH = "nyx_memory.db"

def fetch_recent_entries(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, user_input, response, emotion, truth_state
        FROM memory
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    results = cursor.fetchall()
    conn.close()
    return results

if __name__ == "__main__":
    entries = fetch_recent_entries()
    headers = ["ID", "Timestamp", "Input", "Response", "Emotion", "Truth"]
    print(tabulate(entries, headers=headers, tablefmt="fancy_grid"))
