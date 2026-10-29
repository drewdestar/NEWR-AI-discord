"""SQLite persistence for conversation history, preferences and feedback."""
import sqlite3, time
from pathlib import Path

def init_db(path="data.db"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, role TEXT,
        content TEXT, created_at REAL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS prefs(
        user_id TEXT PRIMARY KEY, model TEXT, language TEXT, style TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, kind TEXT,
        text TEXT, created_at REAL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, text TEXT, created_at REAL)""")
    con.commit(); con.close()

def _con(path):
    con = sqlite3.connect(path); con.row_factory = sqlite3.Row; return con

def add_message(path, user_id, role, content):
    con = _con(path); con.execute("INSERT INTO history(user_id,role,content,created_at) VALUES(?,?,?,?)",
        (str(user_id), role, content, time.time())); con.commit(); con.close()

def get_history(path, user_id, limit=12):
    con = _con(path)
    rows = con.execute("SELECT role,content FROM history WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (str(user_id), limit)).fetchall(); con.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

def clear_history(path, user_id):
    con = _con(path); cur = con.execute("DELETE FROM history WHERE user_id=?", (str(user_id),)); con.commit(); n = cur.rowcount; con.close(); return n

def history_count(path, user_id):
    con = _con(path); n = con.execute("SELECT COUNT(*) c FROM history WHERE user_id=?", (str(user_id),)).fetchone()["c"]; con.close(); return n

def set_pref(path, user_id, **kw):
    con = _con(path)
    cur = con.execute("SELECT * FROM prefs WHERE user_id=?", (str(user_id),)).fetchone()
    vals = {"model": None, "language": None, "style": None}
    if cur:
        for k in vals: vals[k] = cur[k]
    vals.update({k: v for k, v in kw.items() if v is not None})
    con.execute("INSERT OR REPLACE INTO prefs(user_id,model,language,style) VALUES(?,?,?,?)",
        (str(user_id), vals["model"], vals["language"], vals["style"])); con.commit(); con.close()

def get_pref(path, user_id):
    con = _con(path); r = con.execute("SELECT * FROM prefs WHERE user_id=?", (str(user_id),)).fetchone(); con.close()
    return dict(r) if r else {"model": None, "language": None, "style": None}

def add_feedback(path, user_id, kind, text):
    con = _con(path); con.execute("INSERT INTO feedback(user_id,kind,text,created_at) VALUES(?,?,?,?)",
        (str(user_id), kind, text, time.time())); con.commit(); con.close()

def add_note(path, user_id, text):
    con = _con(path); con.execute("INSERT INTO notes(user_id,text,created_at) VALUES(?,?,?)",
        (str(user_id), text, time.time())); con.commit(); con.close()

def list_notes(path, user_id):
    con = _con(path); rows = con.execute("SELECT id,text FROM notes WHERE user_id=? ORDER BY id DESC LIMIT 20", (str(user_id),)).fetchall(); con.close()
    return [(r["id"], r["text"]) for r in rows]
