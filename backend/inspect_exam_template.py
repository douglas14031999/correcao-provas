import sqlite3
import json
import os

db_path = os.path.join(os.path.dirname(__file__), "storage", "exams.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, title, sheet_template FROM exams WHERE id = 'a7556746-7e39-4526-b752-bf0477a0e461'")
row = c.fetchone()
print("Exam ID:", row[0])
print("Exam Title:", row[1])
tmpl = json.loads(row[2]) if row[2] else None
if tmpl:
    print("Template keys:", list(tmpl.keys()))
    print("Canonical size:", tmpl.get("canonical_width"), tmpl.get("canonical_height"))
    print("is_compact:", tmpl.get("is_compact"))
    print("Marker centers:", tmpl.get("marker_centers"))
    print("Bubbles count:", len(tmpl.get("bubbles", {})))
    print("Bubble 1:", tmpl.get("bubbles", {}).get("1"))
    print("Bubble 22:", tmpl.get("bubbles", {}).get("22"))
else:
    print("No template found!")
