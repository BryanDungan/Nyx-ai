import sqlite3


class MemoryDB:
    def __init__(self, path="nyx_memory.db", use_db=False):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # ← Add this line
        self.use_db = use_db  # ✅ Now this is defined!
        self.ensure_schema()


    def ensure_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                user_input TEXT,
                emotion TEXT,
                response TEXT,
                truth_state TEXT,
                fallback_tone TEXT,
                detected_form TEXT,
                tag TEXT,
                pinned BOOLEAN,
                edited BOOLEAN
            )
        """)
        self.conn.commit()


    def write(self, entry): 
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO memory (
                id, timestamp, user_input, emotion, response, truth_state, fallback_tone, detected_form, tag, pinned, edited
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  -- 🔥 11 placeholders
            """,
            (
                entry.id,
                entry.timestamp.isoformat(),
                entry.user_input,
                entry.emotion if isinstance(entry.emotion, str) else entry.emotion.name,
                entry.response,
                entry.truth_state if isinstance(entry.truth_state, str) else entry.truth_state.name,
                entry.fallback_tone if hasattr(entry, "fallback_tone") else None,
                entry.tag,
                entry.detected_form if hasattr(entry, "detected_form") else None,
                int(entry.pinned),
                int(entry.edited)
            )
        )
        self.conn.commit()


    def fetch_all(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memory")
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


    def _create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    user_input TEXT,
                    emotion TEXT,
                    response TEXT,
                    truth_state TEXT,
                    fallback_tone TEXT,
                    detected_form TEXT,
                    tag TEXT,
                    pinned BOOLEAN,
                    edited BOOLEAN
                )
            """)
            self.conn.commit()

    def save_memory(self, memory):
        self.conn.execute("""
            INSERT OR REPLACE INTO memory
            (id, timestamp, user_input, emotion, response, truth_state, fallback_tone, tag, pinned, detected_form, edited)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory["id"],
            memory["timestamp"],
            memory["user_input"],
            memory["emotion"],
            memory["response"],
            memory["truth_state"],
            memory.get("fallback_tone", None),
            memory.get("detected_form", None),
            memory.get("tag", None),
            int(memory.get("pinned", False)),
            int(memory.get("edited", False))
        ))


    def fetch_recent(self, limit=100):
        cur = self.conn.execute("""
            SELECT * FROM memory ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        return [dict(zip([column[0] for column in cur.description], row)) for row in cur.fetchall()]

    def count_memories(self):
        with self.conn:
            result = self.conn.execute("SELECT COUNT(*) FROM memory").fetchone()
            return result[0]


