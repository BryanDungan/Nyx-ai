import sqlite3

def migrate():
    conn = sqlite3.connect("nyx_memory.db")
    cursor = conn.cursor()

    # Add the new column, if it doesn't already exist
    try:
        cursor.execute("ALTER TABLE memory ADD COLUMN fallback_tone TEXT")
        print("✅ Added 'fallback_tone' column to memory table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ 'fallback_tone' column already exists.")
        else:
            print("❌ Unexpected error:", e)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
