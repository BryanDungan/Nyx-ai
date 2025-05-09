import sqlite3

def migrate():
    conn = sqlite3.connect("nyx_memory.db")
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE memory ADD COLUMN detected_form TEXT")
        print("✅ Added 'detected_form' column to memory table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️ 'detected_form' column already exists.")
        else:
            print("❌ Unexpected error:", e)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
