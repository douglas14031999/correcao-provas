import sqlite3
import json
import os
import re
from typing import Optional, List, Dict, Any
from datetime import datetime

# Database Configuration (PostgreSQL in production VPS or SQLite local fallback)
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage", "exams.db"
)

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

def is_postgres() -> bool:
    url = get_database_url()
    return url.startswith("postgresql://")

class PostgresCursorWrapper:
    """Wrapper around psycopg2 DictCursor that adapts SQLite '?' placeholders to PostgreSQL '%s'."""
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql: str, params=None):
        if params is not None:
            sql_pg = sql.replace("?", "%s")
            return self._cursor.execute(sql_pg, params)
        return self._cursor.execute(sql)

    def executemany(self, sql: str, seq_of_params):
        sql_pg = sql.replace("?", "%s")
        return self._cursor.executemany(sql_pg, seq_of_params)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size: Optional[int] = None):
        return self._cursor.fetchmany(size) if size is not None else self._cursor.fetchmany()

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cursor.close()

class PostgresConnectionWrapper:
    """Wrapper around psycopg2 connection providing SQLite-like behavior and DictCursor factory."""
    def __init__(self, conn):
        self._conn = conn
        self._row_factory = None

    @property
    def row_factory(self):
        return self._row_factory

    @row_factory.setter
    def row_factory(self, val):
        self._row_factory = val

    def cursor(self):
        import psycopg2.extras
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return PostgresCursorWrapper(cur)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._conn.rollback()
        else:
            self._conn.commit()
        self._conn.close()

def get_connection():
    if is_postgres():
        import psycopg2
        url = get_database_url()
        raw_conn = psycopg2.connect(url)
        return PostgresConnectionWrapper(raw_conn)
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    if is_postgres():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                institution TEXT,
                num_questions INTEGER NOT NULL,
                num_alternatives INTEGER NOT NULL DEFAULT 4,
                points_per_question REAL DEFAULT 1.0,
                answer_key TEXT NOT NULL,
                weights TEXT,
                sheet_template TEXT,
                subtitle TEXT DEFAULT '2º ANO DO ENSINO FUNDAMENTAL',
                school_name TEXT DEFAULT '',
                classroom TEXT DEFAULT '',
                student_name TEXT DEFAULT '',
                shift TEXT DEFAULT '(  ) MANHÃ       (  ) TARDE',
                logo_path TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                exam_id TEXT NOT NULL,
                student_name TEXT,
                student_id TEXT,
                classroom_id TEXT DEFAULT '',
                school_id TEXT DEFAULT '',
                score REAL NOT NULL,
                max_score REAL NOT NULL,
                detected_answers TEXT NOT NULL,
                results_detail TEXT NOT NULL,
                scanned_image_url TEXT,
                overlay_image_url TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS schools (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                inep_code TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS classrooms (
                id TEXT PRIMARY KEY,
                school_id TEXT NOT NULL,
                name TEXT NOT NULL,
                grade_year TEXT DEFAULT '',
                shift TEXT DEFAULT 'MANHÃ',
                created_at TEXT NOT NULL,
                FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
                UNIQUE(school_id, name, grade_year)
            );

            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                school_id TEXT NOT NULL,
                classroom_id TEXT NOT NULL,
                registration TEXT DEFAULT '',
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
                FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS classroom_exams (
                classroom_id TEXT NOT NULL,
                exam_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (classroom_id, exam_id),
                FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE,
                FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT DEFAULT '',
                role TEXT NOT NULL DEFAULT 'admin',
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login TEXT DEFAULT ''
            );
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                institution TEXT,
                num_questions INTEGER NOT NULL,
                num_alternatives INTEGER NOT NULL DEFAULT 4,
                points_per_question REAL DEFAULT 1.0,
                answer_key TEXT NOT NULL,
                weights TEXT,
                sheet_template TEXT,
                subtitle TEXT,
                school_name TEXT,
                classroom TEXT,
                student_name TEXT,
                shift TEXT,
                logo_path TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Run migrations for existing DBs if columns do not exist
        cursor.execute("PRAGMA table_info(exams)")
        existing_cols = [r["name"] for r in cursor.fetchall()]
        new_cols = [
            ("subtitle", "TEXT DEFAULT '2º ANO DO ENSINO FUNDAMENTAL'"),
            ("school_name", "TEXT DEFAULT ''"),
            ("classroom", "TEXT DEFAULT ''"),
            ("student_name", "TEXT DEFAULT ''"),
            ("shift", "TEXT DEFAULT '(  ) MANHÃ       (  ) TARDE'"),
            ("logo_path", "TEXT DEFAULT ''")
        ]
        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE exams ADD COLUMN {col_name} {col_type}")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                exam_id TEXT NOT NULL,
                student_name TEXT,
                student_id TEXT,
                classroom_id TEXT,
                school_id TEXT,
                score REAL NOT NULL,
                max_score REAL NOT NULL,
                detected_answers TEXT NOT NULL,
                results_detail TEXT NOT NULL,
                scanned_image_url TEXT,
                overlay_image_url TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE CASCADE
            )
        """)

        # Migrations for submissions
        cursor.execute("PRAGMA table_info(submissions)")
        sub_cols = [r["name"] for r in cursor.fetchall()]
        if "classroom_id" not in sub_cols:
            cursor.execute("ALTER TABLE submissions ADD COLUMN classroom_id TEXT DEFAULT ''")
        if "school_id" not in sub_cols:
            cursor.execute("ALTER TABLE submissions ADD COLUMN school_id TEXT DEFAULT ''")

        # Gestão Escolar: Escolas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schools (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                inep_code TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

        # Gestão Escolar: Turmas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classrooms (
                id TEXT PRIMARY KEY,
                school_id TEXT NOT NULL,
                name TEXT NOT NULL,
                grade_year TEXT DEFAULT '',
                shift TEXT DEFAULT 'MANHÃ',
                created_at TEXT NOT NULL,
                FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
                UNIQUE(school_id, name, grade_year)
            )
        """)

        # Migration for classrooms table if old UNIQUE(school_id, name) exists
        try:
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='classrooms'")
            tbl_row = cursor.fetchone()
            if tbl_row and "UNIQUE(school_id, name)" in tbl_row[0]:
                cursor.execute("PRAGMA foreign_keys=OFF")
                cursor.execute("""
                    CREATE TABLE classrooms_v2 (
                        id TEXT PRIMARY KEY,
                        school_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        grade_year TEXT DEFAULT '',
                        shift TEXT DEFAULT 'MANHÃ',
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
                        UNIQUE(school_id, name, grade_year)
                    )
                """)
                cursor.execute("INSERT INTO classrooms_v2 SELECT * FROM classrooms")
                cursor.execute("DROP TABLE classrooms")
                cursor.execute("ALTER TABLE classrooms_v2 RENAME TO classrooms")
                cursor.execute("PRAGMA foreign_keys=ON")
        except Exception as e:
            print(f"Migration notice: {e}")

        # Gestão Escolar: Alunos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                school_id TEXT NOT NULL,
                classroom_id TEXT NOT NULL,
                registration TEXT DEFAULT '',
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
                FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE
            )
        """)

        # Gestão Escolar: Múltiplos Gabaritos por Turma
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classroom_exams (
                classroom_id TEXT NOT NULL,
                exam_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (classroom_id, exam_id),
                FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE,
                FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
            )
        """)

        # Configurações Institucionais do Sistema (Brasão, Prefeitura, Secretaria)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Gestão de Usuários e Controle de Acesso Multi-Operador
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT DEFAULT '',
                role TEXT NOT NULL DEFAULT 'admin',
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login TEXT DEFAULT ''
            )
        """)

    # Seed inicial do administrador mestre caso a tabela esteja vazia (tanto no SQLite quanto no PostgreSQL)
    cursor.execute("SELECT COUNT(*) FROM users")
    first_row = cursor.fetchone()
    user_count = first_row[0] if first_row else 0
    if user_count == 0:
        import hashlib
        import uuid
        salt = "semed_canoa_salt_2026"
        admin_hash = hashlib.sha256(("semed2026" + salt).encode("utf-8")).hexdigest()
        cursor.execute("""
            INSERT INTO users (id, username, name, email, role, password_hash, is_active, created_at, last_login)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, '')
        """, (
            str(uuid.uuid4()),
            "admin",
            "Administrador SEMED",
            "educacao@lagoadacanoa.al.gov.br",
            "admin",
            admin_hash,
            datetime.utcnow().isoformat()
        ))
    
    conn.commit()
    conn.close()

# Database operations for Exams
def save_exam(exam_data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO exams (
            id, title, institution, num_questions, num_alternatives, points_per_question,
            answer_key, weights, sheet_template, subtitle, school_name, classroom,
            student_name, shift, logo_path, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        exam_data["id"],
        exam_data["title"],
        exam_data.get("institution", "Prefeitura Municipal de Lagoa da Canoa"),
        exam_data["num_questions"],
        exam_data.get("num_alternatives", 4),
        exam_data.get("points_per_question", 1.0),
        json.dumps(exam_data.get("answer_key", {})),
        json.dumps(exam_data.get("weights", {})),
        json.dumps(exam_data.get("sheet_template", {})),
        exam_data.get("subtitle", "2º ANO DO ENSINO FUNDAMENTAL"),
        exam_data.get("school_name", ""),
        exam_data.get("classroom", ""),
        exam_data.get("student_name", ""),
        exam_data.get("shift", "(  ) MANHÃ       (  ) TARDE"),
        exam_data.get("logo_path", ""),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    return exam_data

def get_exam(exam_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exams WHERE id = ? OR id LIKE ? ORDER BY created_at DESC LIMIT 1", (exam_id, f"{exam_id}%"))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["answer_key"] = json.loads(data["answer_key"] or "{}")
    data["weights"] = json.loads(data["weights"] or "{}")
    data["sheet_template"] = json.loads(data["sheet_template"] or "{}")
    return data

def list_exams() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exams ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        item = dict(r)
        item["answer_key"] = json.loads(item["answer_key"] or "{}")
        item["weights"] = json.loads(item["weights"] or "{}")
        item["sheet_template"] = json.loads(item["sheet_template"] or "{}")
        result.append(item)
    return result

def update_exam(exam_id: str, exam_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE exams
        SET title = ?, subtitle = ?, school_name = ?, classroom = ?, student_name = ?,
            shift = ?, logo_path = ?, num_questions = ?, num_alternatives = ?,
            points_per_question = ?, answer_key = ?, weights = ?, sheet_template = ?
        WHERE id = ?
    """, (
        exam_data["title"],
        exam_data.get("subtitle", "2º ANO DO ENSINO FUNDAMENTAL"),
        exam_data.get("school_name", ""),
        exam_data.get("classroom", ""),
        exam_data.get("student_name", ""),
        exam_data.get("shift", "(  ) MANHÃ       (  ) TARDE"),
        exam_data.get("logo_path", ""),
        exam_data["num_questions"],
        exam_data.get("num_alternatives", 4),
        exam_data.get("points_per_question", 1.0),
        json.dumps(exam_data.get("answer_key", {})),
        json.dumps(exam_data.get("weights", {})),
        json.dumps(exam_data.get("sheet_template", {})),
        exam_id
    ))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    if not updated:
        return None
    return get_exam(exam_id)

def update_exam_template(exam_id: str, sheet_template: Dict[str, Any]) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE exams
        SET sheet_template = ?
        WHERE id = ?
    """, (json.dumps(sheet_template), exam_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def delete_exam(exam_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM submissions WHERE exam_id = ?", (exam_id,))
    cursor.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Database operations for Submissions
def save_submission(sub_data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO submissions (
            id, exam_id, student_name, student_id, classroom_id, school_id, score, max_score,
            detected_answers, results_detail, scanned_image_url, overlay_image_url, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sub_data["id"],
        sub_data["exam_id"],
        sub_data.get("student_name", "Aluno Não Identificado"),
        sub_data.get("student_id", ""),
        sub_data.get("classroom_id", ""),
        sub_data.get("school_id", ""),
        sub_data["score"],
        sub_data["max_score"],
        json.dumps(sub_data["detected_answers"]),
        json.dumps(sub_data["results_detail"]),
        sub_data.get("scanned_image_url", ""),
        sub_data.get("overlay_image_url", ""),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    return sub_data

def get_submission(submission_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    item["detected_answers"] = json.loads(item["detected_answers"] or "{}")
    item["results_detail"] = json.loads(item["results_detail"] or "[]")
    return item

def delete_submission(submission_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM submissions WHERE id = ?", (submission_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def delete_submissions_by_exam(exam_id: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM submissions WHERE exam_id = ?", (exam_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def get_submissions_by_exam(exam_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM submissions WHERE exam_id = ? ORDER BY created_at DESC", (exam_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        item = dict(r)
        item["detected_answers"] = json.loads(item["detected_answers"] or "{}")
        item["results_detail"] = json.loads(item["results_detail"] or "[]")
        result.append(item)
    return result


# --- GESTÃO ESCOLAR: ESCOLAS, TURMAS E ALUNOS ---

import uuid

def get_or_create_school(name: str, inep_code: str = "") -> Dict[str, Any]:
    name_clean = name.strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schools WHERE LOWER(name) = LOWER(?)", (name_clean,))
    row = cursor.fetchone()
    if row:
        school = dict(row)
        conn.close()
        return school
        
    school_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO schools (id, name, inep_code, created_at) VALUES (?, ?, ?, ?)",
        (school_id, name_clean, inep_code.strip(), now)
    )
    conn.commit()
    conn.close()
    return {"id": school_id, "name": name_clean, "inep_code": inep_code.strip(), "created_at": now}

def get_school(school_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schools WHERE id = ?", (school_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_school(school_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schools WHERE id = ?", (school_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def delete_classroom(classroom_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM submissions WHERE classroom_id = ?", (classroom_id,))
    cursor.execute("DELETE FROM classroom_exams WHERE classroom_id = ?", (classroom_id,))
    cursor.execute("DELETE FROM students WHERE classroom_id = ?", (classroom_id,))
    cursor.execute("DELETE FROM classrooms WHERE id = ?", (classroom_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def update_classroom(
    classroom_id: str,
    name: Optional[str] = None,
    shift: Optional[str] = None,
    grade_year: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Updates classroom details such as name, shift, and grade_year."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classrooms WHERE id = ?", (classroom_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    current = dict(row)
    new_name = name.strip() if (name and name.strip()) else current["name"]
    new_shift = shift.strip().upper() if (shift and shift.strip()) else current.get("shift", "MANHÃ")
    new_grade = grade_year.strip() if (grade_year is not None and grade_year.strip()) else current.get("grade_year", "")

    cursor.execute(
        "UPDATE classrooms SET name = ?, shift = ?, grade_year = ? WHERE id = ?",
        (new_name, new_shift, new_grade, classroom_id)
    )
    conn.commit()

    cursor.execute("SELECT * FROM classrooms WHERE id = ?", (classroom_id,))
    updated = cursor.fetchone()
    conn.close()
    return dict(updated) if updated else None

def get_or_create_classroom(school_id: str, name: str, grade_year: str = "", shift: str = "MANHÃ") -> Dict[str, Any]:
    name_clean = name.strip()
    grade_clean = grade_year.strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM classrooms WHERE school_id = ? AND LOWER(name) = LOWER(?) AND LOWER(grade_year) = LOWER(?)",
        (school_id, name_clean, grade_clean)
    )
    row = cursor.fetchone()
    if row:
        classroom = dict(row)
        conn.close()
        return classroom
        
    class_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO classrooms (id, school_id, name, grade_year, shift, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (class_id, school_id, name_clean, grade_clean, shift.strip().upper(), now)
    )
    conn.commit()
    conn.close()
    return {"id": class_id, "school_id": school_id, "name": name_clean, "grade_year": grade_clean, "shift": shift.strip().upper(), "created_at": now}

def link_exams_to_classroom(classroom_id: str, exam_ids: List[str]) -> List[str]:
    """Links multiple exams to a classroom, replacing previous links."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM classroom_exams WHERE classroom_id = ?", (classroom_id,))
    now = datetime.utcnow().isoformat()
    for eid in exam_ids:
        if eid and str(eid).strip():
            cursor.execute(
                "INSERT OR IGNORE INTO classroom_exams (classroom_id, exam_id, created_at) VALUES (?, ?, ?)",
                (classroom_id, str(eid).strip(), now)
            )
    conn.commit()
    conn.close()
    return exam_ids

def get_classroom_exams(classroom_id: str) -> List[Dict[str, Any]]:
    """Returns all exams linked to a classroom."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.title, e.num_questions, e.subtitle, ce.created_at as linked_at
        FROM classroom_exams ce
        JOIN exams e ON ce.exam_id = e.id
        WHERE ce.classroom_id = ?
        ORDER BY ce.created_at ASC
    """, (classroom_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_or_create_student(classroom_id: str, name: str, registration: str = "", school_id: Optional[str] = None) -> Dict[str, Any]:
    name_clean = name.strip()
    conn = get_connection()
    cursor = conn.cursor()
    
    if not school_id:
        cursor.execute("SELECT school_id FROM classrooms WHERE id = ?", (classroom_id,))
        c_row = cursor.fetchone()
        school_id = c_row["school_id"] if c_row else ""
        
    # Find existing student in this class by name
    cursor.execute(
        "SELECT * FROM students WHERE classroom_id = ? AND LOWER(name) = LOWER(?)",
        (classroom_id, name_clean)
    )
    row = cursor.fetchone()
    if row:
        student = dict(row)
        conn.close()
        return student
        
    student_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO students (id, school_id, classroom_id, registration, name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (student_id, school_id, classroom_id, registration.strip(), name_clean, now)
    )
    conn.commit()
    conn.close()
    return {"id": student_id, "school_id": school_id, "classroom_id": classroom_id, "registration": registration.strip(), "name": name_clean, "created_at": now}


def list_schools_tree() -> List[Dict[str, Any]]:
    """Returns schools with nested classrooms, linked exams, and student counts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schools ORDER BY name ASC")
    schools = [dict(r) for r in cursor.fetchall()]
    
    for sch in schools:
        cursor.execute("SELECT * FROM classrooms WHERE school_id = ? ORDER BY name ASC", (sch["id"],))
        classes = [dict(c) for c in cursor.fetchall()]
        for cl in classes:
            cursor.execute("SELECT COUNT(*) as total FROM students WHERE classroom_id = ?", (cl["id"],))
            cl["student_count"] = cursor.fetchone()["total"]
            cursor.execute("""
                SELECT e.id, e.title, e.num_questions
                FROM classroom_exams ce
                JOIN exams e ON ce.exam_id = e.id
                WHERE ce.classroom_id = ?
                ORDER BY ce.created_at ASC
            """, (cl["id"],))
            cl["linked_exams"] = [dict(r) for r in cursor.fetchall()]

        sch["classrooms"] = classes
        sch["classroom_count"] = len(classes)
        cursor.execute("SELECT COUNT(*) as total FROM students WHERE school_id = ?", (sch["id"],))
        sch["student_count"] = cursor.fetchone()["total"]
        
    conn.close()
    return schools

def get_classroom_with_details(classroom_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, s.name as school_name 
        FROM classrooms c 
        JOIN schools s ON c.school_id = s.id 
        WHERE c.id = ?
    """, (classroom_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    data = dict(row)
    cursor.execute("SELECT * FROM students WHERE classroom_id = ? ORDER BY name ASC", (classroom_id,))
    data["students"] = [dict(r) for r in cursor.fetchall()]
    cursor.execute("""
        SELECT e.id, e.title, e.num_questions
        FROM classroom_exams ce
        JOIN exams e ON ce.exam_id = e.id
        WHERE ce.classroom_id = ?
        ORDER BY ce.created_at ASC
    """, (classroom_id,))
    data["linked_exams"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return data

def get_classroom_linked_exams(classroom_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.title, e.num_questions, e.points_per_question
        FROM classroom_exams ce
        JOIN exams e ON ce.exam_id = e.id
        WHERE ce.classroom_id = ?
        ORDER BY ce.created_at ASC
    """, (classroom_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_student_by_id(student_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT st.*, cl.name as classroom_name, cl.shift as classroom_shift, sch.name as school_name
        FROM students st
        LEFT JOIN classrooms cl ON st.classroom_id = cl.id
        LEFT JOIN schools sch ON (st.school_id = sch.id OR cl.school_id = sch.id)
        WHERE st.id = ? OR st.id LIKE ?
        ORDER BY st.created_at DESC LIMIT 1
    """, (student_id, f"{student_id}%"))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_classroom_report(classroom_id: str, exam_id: str) -> Optional[Dict[str, Any]]:
    """Calculates comprehensive analytics for a classroom and exam."""
    cl = get_classroom_with_details(classroom_id)
    if not cl:
        return None
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exams WHERE id = ?", (exam_id,))
    exam_row = cursor.fetchone()
    if not exam_row:
        conn.close()
        return None
        
    exam = dict(exam_row)
    exam["answer_key"] = json.loads(exam["answer_key"] or "{}")
    
    # Get submissions for this exam that belong to students in this classroom
    student_ids = [s["id"] for s in cl["students"]]
    submissions = []
    
    for st in cl["students"]:
        cursor.execute("""
            SELECT * FROM submissions 
            WHERE exam_id = ? AND (student_id = ? OR LOWER(student_name) = LOWER(?))
            ORDER BY score DESC LIMIT 1
        """, (exam_id, st["id"], st["name"]))
        sub_row = cursor.fetchone()
        if sub_row:
            sub = dict(sub_row)
            sub["detected_answers"] = json.loads(sub["detected_answers"] or "{}")
            sub["results_detail"] = json.loads(sub["results_detail"] or "[]")
            
            correct_c = sum(1 for r in sub["results_detail"] if r.get("is_correct"))
            wrong_c = sum(1 for r in sub["results_detail"] if not r.get("is_correct") and not r.get("is_blank") and not r.get("is_double"))
            blank_c = sum(1 for r in sub["results_detail"] if r.get("is_blank"))
            double_c = sum(1 for r in sub["results_detail"] if r.get("is_double"))
            
            sub["correct_count"] = correct_c
            sub["wrong_count"] = wrong_c
            sub["blank_count"] = blank_c
            sub["double_count"] = double_c
            
            st["submission"] = sub
            st["status"] = "CORRIGIDO"
            st["score"] = sub["score"]
            st["correct_count"] = correct_c
            st["percentage"] = round((sub["score"] / max(1.0, sub["max_score"])) * 100, 1)
            submissions.append(sub)
        else:
            st["submission"] = None
            st["status"] = "PENDENTE"
            st["score"] = None
            st["correct_count"] = 0
            st["percentage"] = None
            
    conn.close()
    
    # Calculate statistics
    total_students = len(cl["students"])
    graded_count = len(submissions)
    avg_score = round(sum(s["score"] for s in submissions) / max(1, graded_count), 2) if graded_count else 0.0
    avg_percentage = round(sum((s["score"] / max(1.0, s["max_score"])) * 100 for s in submissions) / max(1, graded_count), 1) if graded_count else 0.0
    
    # Grade distribution on 0-10 scale
    grade_distribution = {
        "insufficient": 0, # < 5.0
        "regular": 0,      # 5.0 - 6.9
        "good": 0,         # 7.0 - 8.9
        "excellent": 0     # 9.0 - 10.0
    }
    for s in submissions:
        score_10 = (s["score"] / max(1.0, s["max_score"])) * 10.0
        if score_10 < 5.0:
            grade_distribution["insufficient"] += 1
        elif score_10 < 7.0:
            grade_distribution["regular"] += 1
        elif score_10 < 9.0:
            grade_distribution["good"] += 1
        else:
            grade_distribution["excellent"] += 1

    # Question accuracy rates across the class
    questions_stats = {}
    num_questions = exam["num_questions"]
    for q_idx in range(1, num_questions + 1):
        q_str = str(q_idx)
        correct_ans = exam["answer_key"].get(q_str, "")
        correct_count = sum(1 for s in submissions if s["detected_answers"].get(q_str) == correct_ans and correct_ans != "")
        accuracy = round((correct_count / max(1, graded_count)) * 100, 1) if graded_count else 0.0
        questions_stats[q_str] = {
            "question": q_idx,
            "correct_answer": correct_ans,
            "correct_count": correct_count,
            "accuracy_percentage": accuracy
        }

    # Sort students by score descending for ranking
    sorted_students = sorted(
        cl["students"],
        key=lambda x: (0 if x["status"] == "CORRIGIDO" else 1, -(x["score"] or 0), x["name"])
    )
        
    return {
        "classroom": {
            "id": cl["id"],
            "name": cl["name"],
            "school_name": cl["school_name"],
            "grade_year": cl.get("grade_year", ""),
            "shift": cl["shift"]
        },
        "exam": {
            "id": exam["id"],
            "title": exam["title"],
            "num_questions": exam["num_questions"],
            "points_per_question": exam["points_per_question"],
            "max_score": round(float(exam["num_questions"]) * float(exam.get("points_per_question", 1.0)), 2)
        },
        "total_students": total_students,
        "graded_students": graded_count,
        "corrected_count": graded_count,
        "pending_students": total_students - graded_count,
        "average_score": avg_score,
        "class_average": avg_score,
        "average_percentage": avg_percentage,
        "students": sorted_students,
        "student_results": sorted_students,
        "questions_stats": questions_stats,
        "grade_distribution": grade_distribution
    }


def compare_classroom_exams(classroom_id: str, exam1_id: str, exam2_id: str) -> Optional[Dict[str, Any]]:
    """Calculates side-by-side comparison analytics between two exams for the same classroom."""
    rep1 = get_classroom_report(classroom_id, exam1_id)
    rep2 = get_classroom_report(classroom_id, exam2_id)
    if not rep1 or not rep2:
        return None

    ex1 = rep1["exam"]
    ex2 = rep2["exam"]
    cl = rep1["classroom"]

    # Student-by-student comparison
    st2_map = {s["id"]: s for s in rep2["students"]}
    comparison_students = []

    for s1 in rep1["students"]:
        s2 = st2_map.get(s1["id"], {})
        
        is_graded1 = s1.get("status") == "CORRIGIDO" and s1.get("score") is not None
        is_graded2 = s2.get("status") == "CORRIGIDO" and s2.get("score") is not None
        
        score1 = round(s1.get("score"), 1) if is_graded1 else None
        score2 = round(s2.get("score"), 1) if is_graded2 else None
        
        correct1 = s1.get("correct_count", 0) if is_graded1 else 0
        correct2 = s2.get("correct_count", 0) if is_graded2 else 0

        # Delta & Combined Average
        if is_graded1 and is_graded2:
            delta = round(score1 - score2, 1)
            combined_avg = round((score1 + score2) / 2.0, 1)
            if score1 > score2:
                best_exam = ex1["title"]
            elif score2 > score1:
                best_exam = ex2["title"]
            else:
                best_exam = "Empate"
        elif is_graded1:
            delta = None
            combined_avg = score1
            best_exam = ex1["title"]
        elif is_graded2:
            delta = None
            combined_avg = score2
            best_exam = ex2["title"]
        else:
            delta = None
            combined_avg = None
            best_exam = "-"

        sub1 = s1.get("submission") or {}
        sub2 = s2.get("submission") or {}
        results1 = sub1.get("results_detail", []) if is_graded1 else []
        results2 = sub2.get("results_detail", []) if is_graded2 else []

        comparison_students.append({
            "id": s1["id"],
            "name": s1["name"],
            "registration": s1.get("registration", ""),
            "score1": score1,
            "correct1": correct1,
            "status1": s1.get("status", "PENDENTE"),
            "results1": results1,
            "score2": score2,
            "correct2": correct2,
            "status2": s2.get("status", "PENDENTE"),
            "results2": results2,
            "combined_avg": combined_avg,
            "delta": delta,
            "best_exam": best_exam
        })

    # Sort students: both graded first (by combined_avg DESC), then single graded, then pending
    comparison_students.sort(
        key=lambda s: (
            0 if (s["score1"] is not None and s["score2"] is not None) else (1 if (s["score1"] is not None or s["score2"] is not None) else 2),
            -(s["combined_avg"] or 0),
            s["name"]
        )
    )

    # Questions side-by-side
    max_q = max(ex1["num_questions"], ex2["num_questions"])
    questions_comparison = []
    for q_idx in range(1, max_q + 1):
        q_str = str(q_idx)
        q1 = rep1["questions_stats"].get(q_str, {})
        q2 = rep2["questions_stats"].get(q_str, {})
        
        acc1 = q1.get("accuracy_percentage", 0.0)
        acc2 = q2.get("accuracy_percentage", 0.0)
        
        questions_comparison.append({
            "question": q_idx,
            "accuracy1": acc1,
            "correct_ans1": q1.get("correct_answer", "-"),
            "hits1": q1.get("correct_count", 0),
            "accuracy2": acc2,
            "correct_ans2": q2.get("correct_answer", "-"),
            "hits2": q2.get("correct_count", 0),
            "delta": round(acc1 - acc2, 1)
        })

    avg_diff = round(rep1["average_score"] - rep2["average_score"], 2)
    if avg_diff > 0:
        highlight_summary = f"A turma obteve melhor média em {ex1['title']} (+{avg_diff} pts)."
    elif avg_diff < 0:
        highlight_summary = f"A turma obteve melhor média em {ex2['title']} (+{abs(avg_diff)} pts)."
    else:
        highlight_summary = "A média geral da turma foi exatamente igual em ambos os simulados."

    return {
        "classroom": cl,
        "exam1": ex1,
        "exam2": ex2,
        "summary": {
            "avg_score1": rep1["average_score"],
            "avg_score2": rep2["average_score"],
            "avg_pct1": rep1["average_percentage"],
            "avg_pct2": rep2["average_percentage"],
            "graded_students1": rep1["graded_students"],
            "graded_students2": rep2["graded_students"],
            "total_students": rep1["total_students"],
            "avg_diff": avg_diff,
            "highlight_summary": highlight_summary
        },
        "students": comparison_students,
        "questions_comparison": questions_comparison
    }

def get_students_report_by_year(grade_year: str, school_id: Optional[str] = None, exam_id: Optional[str] = None) -> Dict[str, Any]:
    """Generates ranking and performance report of all students for a specific school year/grade (e.g. 2º Ano, 5º Ano)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Find matching classrooms with smart grade/year matching
    params_cl = []
    clean_gy = (grade_year or "").strip()
    if not clean_gy or clean_gy.lower() in ("todos", "todos os anos", "rede"):
        cl_where = "1=1"
    else:
        digits = re.findall(r'\d+', clean_gy)
        if digits:
            d = digits[0]
            cl_where = """(
                c.grade_year LIKE ? OR c.grade_year LIKE ? OR c.grade_year LIKE ? OR
                c.grade_year LIKE ? OR c.grade_year LIKE ? OR
                c.name LIKE ? OR c.name LIKE ?
            )"""
            params_cl.extend([f"%- {d}º%", f"%- {d}°%", f"%- {d} ano%", f"{d}º%", f"{d}°%", f"%{d}º%", f"%{d}°%"])
        else:
            cl_where = "(c.grade_year LIKE ? OR c.name LIKE ?)"
            params_cl.extend([f"%{clean_gy}%", f"%{clean_gy}%"])

    query_cl = f"SELECT c.*, s.name as school_name, s.inep_code as school_inep FROM classrooms c JOIN schools s ON c.school_id = s.id WHERE {cl_where}"
    if school_id:
        query_cl += " AND c.school_id = ?"
        params_cl.append(school_id)

    cursor.execute(query_cl, params_cl)
    cl_rows = cursor.fetchall()

    classroom_map = {r["id"]: dict(r) for r in cl_rows}
    cl_ids = list(classroom_map.keys())

    if not cl_ids:
        conn.close()
        return {
            "grade_year": grade_year,
            "total_students": 0,
            "graded_students": 0,
            "average_score": 0.0,
            "average_percentage": 0.0,
            "highest_score": 0.0,
            "students": [],
            "classrooms_count": 0,
            "exam": None
        }

    # Fetch exam if specified
    exam_info = None
    if exam_id:
        cursor.execute("SELECT id, title, num_questions, points_per_question FROM exams WHERE id = ?", (exam_id,))
        ex_row = cursor.fetchone()
        if ex_row:
            exam_info = dict(ex_row)
            exam_info["max_score"] = round(float(ex_row["num_questions"]) * float(ex_row["points_per_question"]), 2)

    # Fetch students
    placeholders = ",".join(["?"] * len(cl_ids))
    cursor.execute(f"SELECT * FROM students WHERE classroom_id IN ({placeholders}) ORDER BY name ASC", cl_ids)
    st_rows = cursor.fetchall()

    students_list = []
    total_graded = 0
    scores_sum = 0.0
    pcts_sum = 0.0

    for st in st_rows:
        st_dict = dict(st)
        cl_info = classroom_map.get(st["classroom_id"], {})
        st_dict["classroom_name"] = cl_info.get("name", "")
        st_dict["school_name"] = cl_info.get("school_name", "")
        st_dict["shift"] = cl_info.get("shift", "")

        # Look up submission
        if exam_id:
            cursor.execute("""
                SELECT * FROM submissions 
                WHERE exam_id = ? AND (student_id = ? OR (classroom_id = ? AND LOWER(student_name) = LOWER(?)))
                ORDER BY score DESC LIMIT 1
            """, (exam_id, st["id"], st["classroom_id"], st["name"]))
            sub = cursor.fetchone()
            if sub:
                max_sc = max(1.0, sub["max_score"])
                sc = round(sub["score"], 1)
                pct = round((sc / max_sc) * 100, 1)
                st_dict["status"] = "CORRIGIDO"
                st_dict["score"] = sc
                st_dict["max_score"] = sub["max_score"]
                st_dict["percentage"] = pct
                st_dict["results_detail"] = json.loads(sub["results_detail"] or "[]")
                st_dict["correct_count"] = sum(1 for r in st_dict["results_detail"] if r.get("is_correct"))
                total_graded += 1
                scores_sum += sc
                pcts_sum += pct
            else:
                st_dict["status"] = "PENDENTE"
                st_dict["score"] = None
                st_dict["percentage"] = None
                st_dict["correct_count"] = 0
                st_dict["results_detail"] = []
        else:
            # Average across all submissions of this student
            cursor.execute("""
                SELECT score, max_score, results_detail FROM submissions 
                WHERE student_id = ? OR (classroom_id = ? AND LOWER(student_name) = LOWER(?))
            """, (st["id"], st["classroom_id"], st["name"]))
            subs = cursor.fetchall()
            if subs:
                scores = [s["score"] for s in subs]
                pcts = [(s["score"] / max(1.0, s["max_score"])) * 100 for s in subs]
                avg_sc = round(sum(scores) / len(scores), 1)
                avg_pct = round(sum(pcts) / len(pcts), 1)
                st_dict["status"] = "CORRIGIDO"
                st_dict["score"] = avg_sc
                st_dict["max_score"] = 10.0
                st_dict["percentage"] = avg_pct
                st_dict["submissions_count"] = len(subs)
                st_dict["correct_count"] = 0
                st_dict["results_detail"] = []
                total_graded += 1
                scores_sum += avg_sc
                pcts_sum += avg_pct
            else:
                st_dict["status"] = "PENDENTE"
                st_dict["score"] = None
                st_dict["percentage"] = None
                st_dict["correct_count"] = 0
                st_dict["submissions_count"] = 0
                st_dict["results_detail"] = []

        students_list.append(st_dict)

    conn.close()

    # Sort from highest score to lowest score (melhor desempenho para o pior), then by name
    students_list.sort(
        key=lambda s: (0 if s["status"] == "CORRIGIDO" else 1, -(s["score"] or 0), s["name"])
    )

    # Assign position rank
    for idx, s in enumerate(students_list, start=1):
        s["rank"] = idx if s["status"] == "CORRIGIDO" else "-"

    avg_score = round(scores_sum / max(1, total_graded), 2) if total_graded else 0.0
    avg_percentage = round(pcts_sum / max(1, total_graded), 1) if total_graded else 0.0
    highest_score = max((s["score"] for s in students_list if s["score"] is not None), default=0.0)

    return {
        "grade_year": grade_year,
        "school_id": school_id,
        "exam": exam_info,
        "total_students": len(students_list),
        "graded_students": total_graded,
        "classrooms_count": len(cl_ids),
        "average_score": avg_score,
        "average_percentage": avg_percentage,
        "highest_score": highest_score,
        "students": students_list
    }

def get_schools_overview_report() -> Dict[str, Any]:
    """Overview statistics for all schools and classrooms in the network."""
    tree = list_schools_tree()
    conn = get_connection()
    cursor = conn.cursor()

    overview = []
    total_network_students = 0
    total_network_graded = 0
    scores_accum = []

    for school in tree:
        sch_students_count = sum(c.get("students_count", 0) for c in school.get("classrooms", []))
        cursor.execute("SELECT score FROM submissions WHERE school_id = ?", (school["id"],))
        subs = cursor.fetchall()
        sch_graded_count = len(subs)
        sch_avg = round(sum(s["score"] for s in subs) / max(1, sch_graded_count), 2) if sch_graded_count else 0.0

        for s in subs:
            scores_accum.append(s["score"])

        total_network_students += sch_students_count
        total_network_graded += sch_graded_count

        overview.append({
            "school_id": school["id"],
            "school_name": school["name"],
            "inep_code": school.get("inep_code", ""),
            "classrooms_count": len(school.get("classrooms", [])),
            "students_count": sch_students_count,
            "graded_count": sch_graded_count,
            "average_score": sch_avg
        })

    conn.close()

    network_avg = round(sum(scores_accum) / max(1, len(scores_accum)), 2) if scores_accum else 0.0

    return {
        "total_schools": len(tree),
        "total_students": total_network_students,
        "total_graded": total_network_graded,
        "network_average": network_avg,
        "schools": overview
    }

def get_system_settings() -> Dict[str, str]:
    """Retrieves current municipal institutional settings (names and logo path)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM system_settings")
    rows = cursor.fetchall()
    conn.close()

    defaults = {
        "prefeitura_name": "PREFEITURA MUNICIPAL DE LAGOA DA CANOA",
        "secretaria_name": "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "state_name": "Estado de Alagoas",
        "logo_path": ""
    }
    settings = dict(defaults)
    for r in rows:
        settings[r["key"]] = r["value"]
    return settings

def update_system_settings(settings_dict: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, str]:
    """Updates municipal institutional settings (supports dict or kwargs)."""
    items = dict(settings_dict or {})
    items.update(kwargs)

    conn = get_connection()
    cursor = conn.cursor()
    for k, v in items.items():
        if v is not None:
            cursor.execute("""
                INSERT INTO system_settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (k, str(v)))
    conn.commit()
    conn.close()
    return get_system_settings()


def get_exams_by_grade_year(grade_year: str, school_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns exams linked to classrooms of the given grade_year (and optionally school_id)."""
    conn = get_connection()
    cursor = conn.cursor()

    clean_gy = (grade_year or "").strip()
    
    if not clean_gy or clean_gy.lower() in ("todos", "todos os anos", "rede"):
        cl_where = "1=1"
        cl_params = []
    else:
        digits = re.findall(r'\d+', clean_gy)
        if digits:
            d = digits[0]
            cl_where = """(
                cl.grade_year LIKE ? OR cl.grade_year LIKE ? OR cl.grade_year LIKE ? OR
                cl.grade_year LIKE ? OR cl.grade_year LIKE ? OR
                cl.name LIKE ? OR cl.name LIKE ?
            )"""
            cl_params = [f"%- {d}º%", f"%- {d}°%", f"%- {d} ano%", f"{d}º%", f"{d}°%", f"%{d}º%", f"%{d}°%"]
        else:
            cl_where = "(cl.grade_year LIKE ? OR cl.name LIKE ?)"
            cl_params = [f"%{clean_gy}%", f"%{clean_gy}%"]

    school_filter = ""
    school_params = []
    if school_id:
        school_filter = " AND cl.school_id = ?"
        school_params = [school_id]

    query = f"""
        SELECT DISTINCT e.id, e.title, e.num_questions, e.points_per_question, e.created_at
        FROM exams e
        WHERE e.id IN (
            SELECT ce.exam_id 
            FROM classroom_exams ce 
            JOIN classrooms cl ON ce.classroom_id = cl.id 
            WHERE {cl_where}{school_filter}
        )
        OR e.id IN (
            SELECT s.exam_id 
            FROM submissions s 
            JOIN classrooms cl ON s.classroom_id = cl.id 
            WHERE {cl_where}{school_filter}
        )
        ORDER BY e.title ASC
    """
    all_params = (cl_params + school_params) * 2
    cursor.execute(query, all_params)
    exams = [dict(r) for r in cursor.fetchall()]

    # Fallback: if no exams found via classroom links, check if exam itself has grade in classroom or title
    if not exams and clean_gy and clean_gy.lower() not in ("todos", "todos os anos", "rede"):
        digits = re.findall(r'\d+', clean_gy)
        if digits:
            d = digits[0]
            cursor.execute("""
                SELECT id, title, num_questions, points_per_question, created_at
                FROM exams
                WHERE classroom LIKE ? OR classroom LIKE ? OR title LIKE ? OR title LIKE ?
                ORDER BY title ASC
            """, (f"%{d}º%", f"%{d}%ano%", f"%{d}º%", f"%{d}%ano%"))
            exams = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return exams


def get_macro_dashboard_data(exam_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes aggregated municipal metrics for the executive dashboard:
    - KPIs: Total Students, Graded Tests, City Average %, Participation Rate %
    - Schools Comparison: average % and submissions per school
    - Grade Years Comparison: 1º to 9º Ano performance
    - Executive School Table with performance badges
    - Alert Classrooms: classes with avg score < 50%
    - Available exams list for filtering
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Total counts in system
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM schools")
    total_schools = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM classrooms")
    total_classrooms = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM exams")
    total_exams = cursor.fetchone()[0] or 0

    # Submissions KPI filter
    sub_where = "WHERE s.max_score > 0"
    sub_params = []
    if exam_id and exam_id.strip() and exam_id.strip().lower() not in ("all", "todos"):
        sub_where += " AND s.exam_id = ?"
        sub_params.append(exam_id.strip())

    cursor.execute(f"""
        SELECT COUNT(*), AVG((s.score * 100.0) / s.max_score)
        FROM submissions s
        {sub_where}
    """, sub_params)
    sub_row = cursor.fetchone()
    total_graded = sub_row[0] or 0
    overall_avg = round(float(sub_row[1] or 0.0), 1)

    participation_rate = round((total_graded / total_students * 100.0), 1) if total_students > 0 else 0.0

    # Available exams for dropdown
    cursor.execute("SELECT id, title, subtitle, num_questions FROM exams ORDER BY title ASC")
    exams_list = [dict(r) for r in cursor.fetchall()]

    # Performance by School
    cursor.execute("SELECT id, name, inep_code FROM schools ORDER BY name ASC")
    all_schools = [dict(r) for r in cursor.fetchall()]

    schools_table = []
    for sc in all_schools:
        sid = sc["id"]
        cursor.execute("SELECT COUNT(*) FROM classrooms WHERE school_id = ?", (sid,))
        cls_count = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM students WHERE school_id = ?", (sid,))
        std_count = cursor.fetchone()[0] or 0

        sc_where = "WHERE s.max_score > 0 AND (s.school_id = ? OR cl.school_id = ?)"
        sc_params = [sid, sid]
        if exam_id and exam_id.strip() and exam_id.strip().lower() not in ("all", "todos"):
            sc_where += " AND s.exam_id = ?"
            sc_params.append(exam_id.strip())

        cursor.execute(f"""
            SELECT COUNT(DISTINCT s.id), AVG((s.score * 100.0) / s.max_score)
            FROM submissions s
            LEFT JOIN classrooms cl ON s.classroom_id = cl.id
            {sc_where}
        """, sc_params)
        sc_sub_row = cursor.fetchone()
        sc_graded = sc_sub_row[0] or 0
        sc_avg = round(float(sc_sub_row[1] or 0.0), 1) if sc_graded > 0 else 0.0

        if sc_graded == 0:
            status = "Sem Dados"
            status_level = "neutral"
        elif sc_avg >= 70.0:
            status = "Alto Desempenho"
            status_level = "success"
        elif sc_avg >= 50.0:
            status = "Na Média"
            status_level = "warning"
        else:
            status = "Atenção"
            status_level = "danger"

        sc_rate = round((sc_graded / std_count * 100.0), 1) if std_count > 0 else 0.0

        schools_table.append({
            "school_id": sid,
            "school_name": sc["name"],
            "name": sc["name"],
            "inep_code": sc["inep_code"] or "-",
            "classrooms_count": cls_count,
            "students_count": std_count,
            "total_students": std_count,
            "graded_count": sc_graded,
            "average_pct": sc_avg,
            "avg_score_percent": sc_avg,
            "participation_rate": sc_rate,
            "status": status,
            "status_level": status_level
        })

    # Sort schools by average desc
    schools_table.sort(key=lambda x: (x["graded_count"] > 0, x["average_pct"]), reverse=True)

    # Performance by Grade Year (1º ao 9º Ano)
    canonical_years = ["1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano"]
    years_data = []

    for idx, yr in enumerate(canonical_years, 1):
        gy_patterns = [f"%{idx}º%", f"%{idx}°%", f"%{idx} ano%", f"%{idx}ª%"]
        pattern_where = " OR ".join(["cl.grade_year LIKE ? OR cl.name LIKE ?" for _ in gy_patterns])
        flat_params = []
        for p in gy_patterns:
            flat_params.extend([p, p])

        yr_where = f"WHERE s.max_score > 0 AND ({pattern_where})"
        yr_params = list(flat_params)
        if exam_id and exam_id.strip() and exam_id.strip().lower() not in ("all", "todos"):
            yr_where += " AND s.exam_id = ?"
            yr_params.append(exam_id.strip())

        cursor.execute(f"""
            SELECT COUNT(DISTINCT s.id), AVG((s.score * 100.0) / s.max_score)
            FROM submissions s
            LEFT JOIN classrooms cl ON s.classroom_id = cl.id
            {yr_where}
        """, yr_params)
        yr_row = cursor.fetchone()
        yr_graded = yr_row[0] or 0
        yr_avg = round(float(yr_row[1] or 0.0), 1) if yr_graded > 0 else 0.0

        years_data.append({
            "grade_year": yr,
            "grade_name": yr,
            "graded_count": yr_graded,
            "average_pct": yr_avg,
            "avg_score_percent": yr_avg
        })

    # Alert Classrooms (classes with average < 50% and at least 1 submission)
    alert_where = "WHERE s.max_score > 0"
    alert_params = []
    if exam_id and exam_id.strip() and exam_id.strip().lower() not in ("all", "todos"):
        alert_where += " AND s.exam_id = ?"
        alert_params.append(exam_id.strip())

    cursor.execute(f"""
        SELECT cl.id, cl.name, sc.name as school_name, cl.grade_year, cl.shift,
               COUNT(s.id) as graded_count,
               AVG((s.score * 100.0) / s.max_score) as avg_pct
        FROM classrooms cl
        JOIN schools sc ON cl.school_id = sc.id
        JOIN submissions s ON s.classroom_id = cl.id
        {alert_where}
        GROUP BY cl.id, cl.name, sc.name, cl.grade_year, cl.shift
        HAVING avg_pct < 50.0 AND graded_count > 0
        ORDER BY avg_pct ASC
        LIMIT 10
    """, alert_params)
    alert_rows = cursor.fetchall()
    alerts = []
    for r in alert_rows:
        alerts.append({
            "classroom_id": r["id"],
            "classroom_name": r["name"],
            "school_name": r["school_name"],
            "grade_year": r["grade_year"] or "-",
            "shift": r["shift"] or "-",
            "graded_count": r["graded_count"],
            "average_pct": round(float(r["avg_pct"]), 1),
            "avg_percent": round(float(r["avg_pct"]), 1)
        })

    conn.close()

    return {
        "kpis": {
            "total_students": total_students,
            "total_schools": total_schools,
            "total_classrooms": total_classrooms,
            "total_exams": total_exams,
            "total_graded": total_graded,
            "overall_avg_pct": overall_avg,
            "overall_avg_percent": overall_avg,
            "participation_rate": participation_rate
        },
        "schools_table": schools_table,
        "schools_comparison": schools_table,
        "years_data": years_data,
        "grade_years_comparison": years_data,
        "alerts": alerts,
        "alert_classrooms": alerts,
        "exams_list": exams_list
    }

# =========================================================================
# GESTÃO DE USUÁRIOS E PERFIS DE ACESSO
# =========================================================================

def get_all_users() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, name, email, role, is_active, created_at, last_login
        FROM users
        ORDER BY role ASC, name ASC
    """)
    rows = cursor.fetchall()
    users = [dict(r) for r in rows]
    conn.close()
    return users

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(name: str, username: str, email: str, role: str, password_hash: str, is_active: int = 1) -> Dict[str, Any]:
    import uuid
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (id, username, name, email, role, password_hash, is_active, created_at, last_login)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, '')
    """, (user_id, username.strip().lower(), name.strip(), (email or "").strip(), role.strip(), password_hash, is_active, now))
    conn.commit()
    conn.close()
    return {
        "id": user_id,
        "username": username.strip().lower(),
        "name": name.strip(),
        "email": (email or "").strip(),
        "role": role.strip(),
        "is_active": is_active,
        "created_at": now,
        "last_login": ""
    }

def update_user(user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    values = []
    allowed_keys = ["name", "email", "role", "is_active", "password_hash"]
    for k in allowed_keys:
        if k in updates:
            fields.append(f"{k} = ?")
            values.append(updates[k])
    
    if not fields:
        conn.close()
        return get_user_by_id(user_id)

    values.append(user_id)
    cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return get_user_by_id(user_id)

def delete_user(user_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def update_user_last_login(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.utcnow().isoformat(), user_id))
    conn.commit()
    conn.close()

def count_active_admins() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count




