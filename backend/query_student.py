import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "storage", "exams.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

student_id = '377e901e-4eb9-41c2-b676-d00d8a6defc0'
c.execute("SELECT * FROM students WHERE id = ?", (student_id,))
st = dict(c.fetchone())
print("Student:", st)

classroom_id = st['classroom_id']
c.execute("SELECT * FROM classrooms WHERE id = ?", (classroom_id,))
cl = dict(c.fetchone())
print("\nClassroom:", cl)

school_id = cl.get('school_id')
c.execute("SELECT * FROM schools WHERE id = ?", (school_id,))
sc = dict(c.fetchone())
print("\nSchool:", sc)

print("\n--- EXAMS AVAILABLE ---")
c.execute("SELECT id, title, total_questions, answer_key FROM exams WHERE title LIKE '%CANOA%' OR title LIKE '%MATEM%' OR title LIKE '%8%'")
for r in c.fetchall():
    print(dict(r))
