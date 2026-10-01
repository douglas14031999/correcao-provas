import os
import re
import uuid
import json
import base64
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.services.database import get_connection, is_postgres

logger = logging.getLogger("uvicorn")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILDER_IMAGES_DIR = os.path.join(BASE_DIR, "storage", "builder_images")
os.makedirs(BUILDER_IMAGES_DIR, exist_ok=True)

def ensure_image_saved_as_webp(url_or_b64: str) -> str:
    """
    Se a imagem for uma string Base64 (data:image/...), decodifica, converte para WebP
    e salva em disco em storage/builder_images/, retornando o caminho relativo /storage/builder_images/qimg_xxx.webp.
    Isso impede que o banco de dados infle com megabytes de dados Base64 inline.
    """
    if not url_or_b64 or not isinstance(url_or_b64, str):
        return ""
    s = url_or_b64.strip()
    if not s.startswith("data:image/"):
        return s
    try:
        header, b64_str = s.split(",", 1)
        raw_bytes = base64.b64decode(b64_str)
        from PIL import Image, ImageOps
        import io
        img = Image.open(io.BytesIO(raw_bytes))
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
        elif img.mode != "RGB":
            img = img.convert("RGB")
        max_dim = 2048
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        unique_name = f"qimg_{uuid.uuid4().hex[:12]}.webp"
        dest_path = os.path.join(BUILDER_IMAGES_DIR, unique_name)
        img.save(dest_path, format="WEBP", quality=85, method=6)
        return f"/storage/builder_images/{unique_name}"
    except Exception as e:
        logger.warning(f"Erro ao converter imagem Base64 para WebP no salvamento do banco: {e}")
        return s

def init_builder_db():
    """Initializes isolated tables for the exam builder module."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if is_postgres():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS builder_exams (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                institution TEXT DEFAULT 'PREFEITURA MUNICIPAL DE LAGOA DA CANOA - SEMED',
                school_name TEXT DEFAULT 'SEMED - LAGOA DA CANOA',
                discipline TEXT DEFAULT 'MATEMÁTICA',
                teacher_name TEXT DEFAULT '',
                grade_year TEXT DEFAULT '9º ANO',
                classroom TEXT DEFAULT 'TURMA A',
                shift TEXT DEFAULT 'MATUTINO',
                exam_date TEXT DEFAULT '',
                max_score REAL DEFAULT 10.0,
                columns_layout INTEGER DEFAULT 2,
                font_size TEXT DEFAULT 'medium',
                header_style TEXT DEFAULT 'standard',
                footer_text TEXT DEFAULT 'Boa Prova!',
                include_answer_sheet INTEGER DEFAULT 1,
                linked_exam_id TEXT DEFAULT '',
                margin_top REAL DEFAULT 3.0,
                margin_bottom REAL DEFAULT 2.0,
                margin_left REAL DEFAULT 3.0,
                margin_right REAL DEFAULT 2.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS builder_questions (
                id TEXT PRIMARY KEY,
                exam_id TEXT NOT NULL,
                question_number INTEGER NOT NULL,
                statement TEXT NOT NULL,
                points REAL DEFAULT 1.0,
                image_url TEXT DEFAULT '',
                image_position TEXT DEFAULT 'after_statement',
                image_width TEXT DEFAULT '50%',
                image_caption TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (exam_id) REFERENCES builder_exams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS builder_alternatives (
                id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                letter TEXT NOT NULL,
                text TEXT NOT NULL,
                is_correct INTEGER DEFAULT 0,
                order_index INTEGER NOT NULL,
                FOREIGN KEY (question_id) REFERENCES builder_questions(id) ON DELETE CASCADE
            );
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS builder_exams (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                institution TEXT DEFAULT 'PREFEITURA MUNICIPAL DE LAGOA DA CANOA - SEMED',
                school_name TEXT DEFAULT 'SEMED - LAGOA DA CANOA',
                discipline TEXT DEFAULT 'MATEMÁTICA',
                teacher_name TEXT DEFAULT '',
                grade_year TEXT DEFAULT '9º ANO',
                classroom TEXT DEFAULT 'TURMA A',
                shift TEXT DEFAULT 'MATUTINO',
                exam_date TEXT DEFAULT '',
                max_score REAL DEFAULT 10.0,
                columns_layout INTEGER DEFAULT 2,
                font_size TEXT DEFAULT 'medium',
                header_style TEXT DEFAULT 'standard',
                footer_text TEXT DEFAULT 'Boa Prova!',
                include_answer_sheet INTEGER DEFAULT 1,
                linked_exam_id TEXT DEFAULT '',
                margin_top REAL DEFAULT 3.0,
                margin_bottom REAL DEFAULT 2.0,
                margin_left REAL DEFAULT 3.0,
                margin_right REAL DEFAULT 2.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS builder_questions (
                id TEXT PRIMARY KEY,
                exam_id TEXT NOT NULL,
                question_number INTEGER NOT NULL,
                statement TEXT NOT NULL,
                points REAL DEFAULT 1.0,
                image_url TEXT DEFAULT '',
                image_position TEXT DEFAULT 'after_statement',
                image_width TEXT DEFAULT '50%',
                image_caption TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (exam_id) REFERENCES builder_exams(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS builder_alternatives (
                id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                letter TEXT NOT NULL,
                text TEXT NOT NULL,
                is_correct INTEGER DEFAULT 0,
                order_index INTEGER NOT NULL,
                FOREIGN KEY (question_id) REFERENCES builder_questions(id) ON DELETE CASCADE
            );
        """)

    if_ne = "IF NOT EXISTS " if is_postgres() else ""

    # Migração segura de colunas de margem caso tabela já exista
    for col, def_val in [("margin_top", 3.0), ("margin_bottom", 2.0), ("margin_left", 3.0), ("margin_right", 2.0)]:
        try:
            cursor.execute(f"ALTER TABLE builder_exams ADD COLUMN {if_ne}{col} REAL DEFAULT {def_val}")
            conn.commit()
        except Exception:
            if is_postgres():
                try: conn.rollback()
                except Exception: pass

    # Migração segura de sincronismo OMR e contagem de páginas
    for col, def_sql in [
        ("gabarito_synced_at", "TEXT DEFAULT ''"),
        ("page_count", "INTEGER DEFAULT 1")
    ]:
        try:
            cursor.execute(f"ALTER TABLE builder_exams ADD COLUMN {if_ne}{col} {def_sql}")
            conn.commit()
        except Exception:
            if is_postgres():
                try: conn.rollback()
                except Exception: pass
    
    # Migração segura de colunas de imagem em alternativas
    for col, def_sql in [("image_url", "TEXT DEFAULT ''"), ("image_width", "TEXT DEFAULT '180px'"), ("image_align", "TEXT DEFAULT 'center'")]:
        try:
            cursor.execute(f"ALTER TABLE builder_alternatives ADD COLUMN {if_ne}{col} {def_sql}")
            conn.commit()
        except Exception:
            if is_postgres():
                try: conn.rollback()
                except Exception: pass

    # Migração segura de colunas BNCC e metadados em questões
    for col, def_sql in [
        ("bncc_code", "TEXT DEFAULT ''"),
        ("discipline", "TEXT DEFAULT ''"),
        ("grade_year", "TEXT DEFAULT ''"),
        ("source_exam_title", "TEXT DEFAULT ''"),
        ("explanation", "TEXT DEFAULT ''")
    ]:
        try:
            cursor.execute(f"ALTER TABLE builder_questions ADD COLUMN {if_ne}{col} {def_sql}")
            conn.commit()
        except Exception:
            if is_postgres():
                try: conn.rollback()
                except Exception: pass

    # Garante existência do registro de sistema para questões preservadas no banco
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT OR IGNORE INTO builder_exams (
            id, title, institution, school_name, discipline, teacher_name,
            grade_year, classroom, shift, exam_date, max_score, columns_layout,
            font_size, header_style, footer_text, include_answer_sheet, created_at, updated_at
        ) VALUES (
            'banco_questoes_geral', 'Banco de Questões', '', '', '', '', '', '', '', '', 0, 1, 'medium', 'standard', '', 0, ?, ?
        )
    """, (now, now))

    # Deduplicação e limpeza de questões duplicadas dentro do banco geral
    try:
        # 1. Remove questões vazias ou sem enunciado do banco geral
        cursor.execute("DELETE FROM builder_alternatives WHERE question_id IN (SELECT id FROM builder_questions WHERE exam_id = 'banco_questoes_geral' AND TRIM(statement) = '')")
        cursor.execute("DELETE FROM builder_questions WHERE exam_id = 'banco_questoes_geral' AND TRIM(statement) = ''")
        
        # 2. Remove duplicatas internas dentro de banco_questoes_geral (mantendo 1 cópia única de cada enunciado)
        cursor.execute("""
            SELECT id, LOWER(TRIM(statement)) FROM builder_questions
            WHERE exam_id = 'banco_questoes_geral' AND TRIM(statement) != ''
            ORDER BY created_at DESC
        """)
        bank_rows = cursor.fetchall()
        seen_bank = set()
        to_del = []
        for r in bank_rows:
            qid, s = r[0], r[1]
            if s in seen_bank:
                to_del.append(qid)
            else:
                seen_bank.add(s)
                
        if to_del:
            for i in range(0, len(to_del), 100):
                batch = to_del[i:i+100]
                ph = ",".join("?" for _ in batch)
                cursor.execute(f"DELETE FROM builder_alternatives WHERE question_id IN ({ph})", tuple(batch))
                cursor.execute(f"DELETE FROM builder_questions WHERE id IN ({ph})", tuple(batch))
        conn.commit()
    except Exception as e:
        logger.warning(f"Aviso ao deduplicar questoes do banco geral: {e}")

    conn.commit()
    conn.close()

    # Se o banco de questões estiver vazio, popula automaticamente com o acervo oficial da BNCC
    try:
        c_check = get_connection()
        cur_check = c_check.cursor()
        cur_check.execute("SELECT COUNT(*) FROM builder_questions WHERE exam_id = 'banco_questoes_geral'")
        total_bank_q = cur_check.fetchone()[0]
        c_check.close()
        if total_bank_q == 0:
            logger.info("Banco de questões vazio. Inicializando auto-seeder BNCC...")
            try:
                from scripts.seed_question_bank import seed_questions
                seed_questions()
            except ImportError:
                import sys
                script_path = os.path.join(BASE_DIR, "scripts")
                if script_path not in sys.path:
                    sys.path.insert(0, script_path)
                from seed_question_bank import seed_questions
                seed_questions()
    except Exception as e_seed:
        logger.warning(f"Aviso ao verificar ou popular banco de questoes inicial: {e_seed}")

def _normalize_margin_cm(val: Any, default: float) -> float:
    try:
        f = float(val) if val is not None else default
        return round(f / 10.0, 2) if f > 5.0 else round(f, 2)
    except Exception:
        return default

def list_builder_exams() -> List[Dict[str, Any]]:
    """Lists all created exams with question count."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, 
               (SELECT COUNT(*) FROM builder_questions q WHERE q.exam_id = e.id) as question_count
        FROM builder_exams e
        WHERE e.id != 'banco_questoes_geral'
        ORDER BY e.updated_at DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT id FROM exams")
    valid_exam_ids = {r[0] for r in cursor.fetchall()}
    conn.close()

    stale_to_clean = []
    for e in rows:
        e["margin_top"] = _normalize_margin_cm(e.get("margin_top"), 3.0)
        e["margin_bottom"] = _normalize_margin_cm(e.get("margin_bottom"), 2.0)
        e["margin_left"] = _normalize_margin_cm(e.get("margin_left"), 3.0)
        e["margin_right"] = _normalize_margin_cm(e.get("margin_right"), 2.0)
        linked_id = (e.get("linked_exam_id") or "").strip()
        synced_at = (e.get("gabarito_synced_at") or "").strip()
        updated_at = (e.get("updated_at") or "").strip()
        is_outdated = False
        if linked_id:
            if linked_id not in valid_exam_ids:
                # O gabarito vinculado foi excluído no sistema de correção: desvincula automaticamente
                stale_to_clean.append(e["id"])
                linked_id = ""
                e["linked_exam_id"] = None
                e["gabarito_synced_at"] = None
            else:
                if not synced_at:
                    is_outdated = True
                elif updated_at and updated_at > synced_at:
                    is_outdated = True
        e["has_linked_exam"] = bool(linked_id)
        e["is_gabarito_outdated"] = is_outdated

    if stale_to_clean:
        try:
            c_fix = get_connection()
            cur_fix = c_fix.cursor()
            ph = ",".join("?" for _ in stale_to_clean)
            cur_fix.execute(f"UPDATE builder_exams SET linked_exam_id = NULL, gabarito_synced_at = NULL WHERE id IN ({ph})", tuple(stale_to_clean))
            c_fix.commit()
            c_fix.close()
        except Exception as err:
            logger.warning(f"Erro ao limpar vínculos órfãos de builder_exams: {err}")

    return rows

def get_builder_exam(exam_id: str) -> Optional[Dict[str, Any]]:
    """Gets full exam structure with questions and alternatives."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM builder_exams WHERE id = ?", (exam_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    exam = dict(row)
    exam["margin_top"] = _normalize_margin_cm(exam.get("margin_top"), 3.0)
    exam["margin_bottom"] = _normalize_margin_cm(exam.get("margin_bottom"), 2.0)
    exam["margin_left"] = _normalize_margin_cm(exam.get("margin_left"), 3.0)
    exam["margin_right"] = _normalize_margin_cm(exam.get("margin_right"), 2.0)
    
    linked_id = (exam.get("linked_exam_id") or "").strip()
    synced_at = (exam.get("gabarito_synced_at") or "").strip()
    updated_at = (exam.get("updated_at") or "").strip()
    is_outdated = False
    has_linked = False

    if linked_id:
        cursor.execute("SELECT id FROM exams WHERE id = ?", (linked_id,))
        if cursor.fetchone():
            has_linked = True
            if not synced_at:
                is_outdated = True
            elif updated_at and updated_at > synced_at:
                is_outdated = True
        else:
            # O gabarito foi excluído no sistema de correção: limpa o vínculo órfão
            try:
                cursor.execute("UPDATE builder_exams SET linked_exam_id = NULL, gabarito_synced_at = NULL WHERE id = ?", (exam_id,))
                conn.commit()
            except Exception as err:
                logger.warning(f"Erro ao limpar vínculo órfão no get_builder_exam: {err}")
            linked_id = ""
            exam["linked_exam_id"] = None
            exam["gabarito_synced_at"] = None

    exam["has_linked_exam"] = has_linked
    exam["is_gabarito_outdated"] = is_outdated
    
    cursor.execute("""
        SELECT * FROM builder_questions 
        WHERE exam_id = ? 
        ORDER BY question_number ASC
    """, (exam_id,))
    questions = [dict(q) for q in cursor.fetchall()]
    
    for q in questions:
        q["bncc_code"] = q.get("bncc_code") or ""
        q["skill"] = q["bncc_code"]
        cursor.execute("""
            SELECT * FROM builder_alternatives 
            WHERE question_id = ? 
            ORDER BY order_index ASC
        """, (q["id"],))
        alts = []
        for a in cursor.fetchall():
            d = dict(a)
            if d.get("image_url"):
                d["image"] = {
                    "url": d.get("image_url", ""),
                    "width": d.get("image_width", "180px"),
                    "align": d.get("image_align", "center")
                }
            alts.append(d)
        q["alternatives"] = alts
    
    exam["questions"] = questions
    conn.close()
    return exam

def create_builder_exam(data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new exam in builder tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    exam_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    questions = data.get("questions", [])
    calc_score = sum(float(q.get("points") or 1.0) for q in questions) if questions else 0.0
    final_max_score = calc_score if calc_score > 0 else float(data.get("max_score") or 10.0)
    
    cursor.execute("""
        INSERT INTO builder_exams (
            id, title, institution, school_name, discipline, teacher_name,
            grade_year, classroom, shift, exam_date, max_score, columns_layout,
            font_size, header_style, footer_text, include_answer_sheet, linked_exam_id,
            margin_top, margin_bottom, margin_left, margin_right,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        exam_id,
        data.get("title") or "NOVA AVALIAÇÃO",
        data.get("institution") or "PREFEITURA MUNICIPAL DE LAGOA DA CANOA - SEMED",
        data.get("school_name") or "SEMED - LAGOA DA CANOA",
        data.get("discipline") or "MATEMÁTICA",
        data.get("teacher_name") or "",
        data.get("grade_year") or "9º ANO",
        data.get("classroom") or "TURMA A",
        data.get("shift") or "MATUTINO",
        data.get("exam_date") or datetime.now().strftime("%d/%m/%Y"),
        final_max_score,
        int(data.get("columns_layout") or 2),
        data.get("font_size") or "medium",
        data.get("header_style") or "standard",
        data.get("footer_text") or "Boa Prova!",
        int(data.get("include_answer_sheet", 1)),
        data.get("linked_exam_id") or "",
        _normalize_margin_cm(data.get("margin_top"), 3.0),
        _normalize_margin_cm(data.get("margin_bottom"), 2.0),
        _normalize_margin_cm(data.get("margin_left"), 3.0),
        _normalize_margin_cm(data.get("margin_right"), 2.0),
        now,
        now
    ))
    
    # Save initial questions if provided (preserva todas as questões criadas pelo professor)
    questions = data.get("questions", [])
    for idx, q_data in enumerate(questions):
        q_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO builder_questions (
                id, exam_id, question_number, statement, points,
                image_url, image_position, image_width, image_caption,
                bncc_code, discipline, grade_year, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            q_id,
            exam_id,
            idx + 1,
            q_data.get("statement") or "",
            float(q_data.get("points") or 1.0),
            ensure_image_saved_as_webp(q_data.get("image_url") or ""),
            q_data.get("image_position") or "after_statement",
            q_data.get("image_width") or "50%",
            q_data.get("image_caption") or "",
            (q_data.get("bncc_code") or q_data.get("skill") or "").strip(),
            q_data.get("discipline") or data.get("discipline") or "",
            q_data.get("grade_year") or data.get("grade_year") or "",
            now
        ))
        
        alternatives = q_data.get("alternatives", [])
        for a_idx, a_data in enumerate(alternatives):
            img_data = a_data.get("image") or {}
            raw_url = a_data.get("image_url") or img_data.get("url") or ""
            img_url = ensure_image_saved_as_webp(raw_url)
            img_width = a_data.get("image_width") or img_data.get("width") or "180px"
            img_align = a_data.get("image_align") or img_data.get("align") or "center"
            cursor.execute("""
                INSERT INTO builder_alternatives (
                    id, question_id, letter, text, is_correct, order_index, image_url, image_width, image_align
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                q_id,
                a_data.get("letter", chr(65 + a_idx)),
                a_data.get("text", ""),
                1 if a_data.get("is_correct") else 0,
                a_idx,
                img_url,
                img_width,
                img_align
            ))
            
    conn.commit()
    conn.close()
    
    return get_builder_exam(exam_id)

def update_builder_exam(exam_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates an existing exam and its questions in builder tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    questions = data.get("questions", [])
    calc_score = sum(float(q.get("points") or 1.0) for q in questions) if questions else 0.0
    final_max_score = calc_score if calc_score > 0 else float(data.get("max_score") or 10.0)

    cursor.execute("""
        UPDATE builder_exams SET
            title = ?, institution = ?, school_name = ?, discipline = ?,
            teacher_name = ?, grade_year = ?, classroom = ?, shift = ?,
            exam_date = ?, max_score = ?, columns_layout = ?, font_size = ?,
            header_style = ?, footer_text = ?, include_answer_sheet = ?,
            margin_top = ?, margin_bottom = ?, margin_left = ?, margin_right = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        data.get("title") or "AVALIAÇÃO",
        data.get("institution") or "PREFEITURA MUNICIPAL DE LAGOA DA CANOA - SEMED",
        data.get("school_name") or "SEMED - LAGOA DA CANOA",
        data.get("discipline") or "MATEMÁTICA",
        data.get("teacher_name") or "",
        data.get("grade_year") or "9º ANO",
        data.get("classroom") or "TURMA A",
        data.get("shift") or "MATUTINO",
        data.get("exam_date") or "",
        final_max_score,
        int(data.get("columns_layout") or 2),
        data.get("font_size") or "medium",
        data.get("header_style") or "standard",
        data.get("footer_text") or "Boa Prova!",
        int(data.get("include_answer_sheet", 1)),
        _normalize_margin_cm(data.get("margin_top"), 3.0),
        _normalize_margin_cm(data.get("margin_bottom"), 2.0),
        _normalize_margin_cm(data.get("margin_left"), 3.0),
        _normalize_margin_cm(data.get("margin_right"), 2.0),
        now,
        exam_id
    ))
    
    # Replace questions cleanly
    if "questions" in data:
        # Delete existing alternatives and questions for this exam
        cursor.execute("""
            DELETE FROM builder_alternatives 
            WHERE question_id IN (SELECT id FROM builder_questions WHERE exam_id = ?)
        """, (exam_id,))
        cursor.execute("DELETE FROM builder_questions WHERE exam_id = ?", (exam_id,))
        
        questions = data.get("questions") or []
        for idx, q_data in enumerate(questions):
            q_id = str(uuid.uuid4())
            q_img_url = ensure_image_saved_as_webp(q_data.get("image_url") or "")
            cursor.execute("""
                INSERT INTO builder_questions (
                    id, exam_id, question_number, statement, points,
                    image_url, image_position, image_width, image_caption,
                    bncc_code, discipline, grade_year, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                q_id,
                exam_id,
                idx + 1,
                q_data.get("statement") or "",
                float(q_data.get("points") or 1.0),
                q_img_url,
                q_data.get("image_position") or "after_statement",
                q_data.get("image_width") or "50%",
                q_data.get("image_caption") or "",
                (q_data.get("bncc_code") or q_data.get("skill") or "").strip(),
                q_data.get("discipline") or data.get("discipline") or "",
                q_data.get("grade_year") or data.get("grade_year") or "",
                now
            ))
            
            for a_idx, a_data in enumerate(q_data.get("alternatives", [])):
                img_data = a_data.get("image") or {}
                raw_img_url = a_data.get("image_url") or img_data.get("url") or ""
                img_url = ensure_image_saved_as_webp(raw_img_url)
                img_width = a_data.get("image_width") or img_data.get("width") or "180px"
                img_align = a_data.get("image_align") or img_data.get("align") or "center"
                cursor.execute("""
                    INSERT INTO builder_alternatives (
                        id, question_id, letter, text, is_correct, order_index, image_url, image_width, image_align
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    q_id,
                    a_data.get("letter", chr(65 + a_idx)),
                    a_data.get("text", ""),
                    1 if a_data.get("is_correct") else 0,
                    a_idx,
                    img_url,
                    img_width,
                    img_align
                ))
                
    conn.commit()
    conn.close()
    return get_builder_exam(exam_id)

def delete_builder_exams_batch(exam_ids: List[str]) -> int:
    """
    Exclui avaliações em lote mantendo todas as questões e alternativas salvas no Banco de Questões.
    As questões são desvinculadas das provas removidas, com seus metadados preservados.
    """
    if not exam_ids:
        return 0
    init_builder_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    deleted_count = 0
    for e_id in exam_ids:
        cursor.execute("SELECT id, title, discipline, grade_year FROM builder_exams WHERE id = ?", (e_id,))
        exam = cursor.fetchone()
        if not exam:
            continue
        
        exam_dict = dict(exam) if hasattr(exam, "keys") else {
            "id": exam[0], "title": exam[1], "discipline": exam[2], "grade_year": exam[3]
        }
        
        # Obtém todas as questões da avaliação sendo excluída
        cursor.execute("""
            SELECT id, statement, discipline, grade_year, source_exam_title
            FROM builder_questions
            WHERE exam_id = ?
        """, (e_id,))
        exam_questions = cursor.fetchall()

        for q_row in exam_questions:
            q_id = q_row[0]
            stmt = (q_row[1] or "").strip()

            if not stmt:
                # Questão sem texto de enunciado: exclui para não poluir o banco
                cursor.execute("DELETE FROM builder_alternatives WHERE question_id = ?", (q_id,))
                cursor.execute("DELETE FROM builder_questions WHERE id = ?", (q_id,))
                continue

            norm_stmt = stmt.lower()

            # Checa se este enunciado já existe em outra questão salva no banco de dados
            cursor.execute("""
                SELECT id FROM builder_questions
                WHERE exam_id != ? AND LOWER(TRIM(statement)) = ?
                LIMIT 1
            """, (e_id, norm_stmt))
            already_exists = cursor.fetchone()

            if already_exists:
                # NÃO SALVA DUPLICATA! Questão idêntica já existe no banco de dados.
                cursor.execute("DELETE FROM builder_alternatives WHERE question_id = ?", (q_id,))
                cursor.execute("DELETE FROM builder_questions WHERE id = ?", (q_id,))
            else:
                # Questão inédita: preserva no acervo geral (banco_questoes_geral)
                cursor.execute("""
                    UPDATE builder_questions
                    SET source_exam_title = COALESCE(NULLIF(source_exam_title, ''), ?),
                        discipline = COALESCE(NULLIF(discipline, ''), ?),
                        grade_year = COALESCE(NULLIF(grade_year, ''), ?),
                        exam_id = 'banco_questoes_geral'
                    WHERE id = ?
                """, (
                    exam_dict.get("title") or "Avaliação",
                    exam_dict.get("discipline") or "",
                    exam_dict.get("grade_year") or "",
                    q_id
                ))

        cursor.execute("DELETE FROM builder_exams WHERE id = ? AND id != 'banco_questoes_geral'", (e_id,))
        deleted_count += 1

    conn.commit()
    conn.close()
    return deleted_count

def delete_builder_exam(exam_id: str) -> bool:
    """Exclui uma avaliação preservando suas questões no banco de questões."""
    return delete_builder_exams_batch([exam_id]) > 0

def delete_question_from_bank(question_id: str) -> bool:
    """Exclui uma questão e suas alternativas diretamente do Banco de Questões."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM builder_alternatives WHERE question_id = ?", (question_id,))
    cursor.execute("DELETE FROM builder_questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()
    return True

def duplicate_builder_exam(exam_id: str) -> Optional[Dict[str, Any]]:
    """Duplicates an existing exam with all its questions."""
    original = get_builder_exam(exam_id)
    if not original:
        return None
    
    copy_data = dict(original)
    copy_data["title"] = f"{original['title']} (Cópia)"
    copy_data["linked_exam_id"] = ""
    return create_builder_exam(copy_data)

def sync_builder_exam_to_main_exams(exam_id: str, custom_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Sincroniza a chave de respostas e metadados da prova com o sistema principal de correção por câmera.
    Cria ou atualiza o exame na tabela `exams` oficial com o gabarito das alternativas marcadas como corretas.
    Valida obrigatoriamente se todas as questões possuem alternativas corretas marcadas (Edge Case 1).
    Gera automaticamente a folha OMR em PDF com os dados e modelo de capa selecionados.
    """
    builder_exam = get_builder_exam(exam_id)
    if not builder_exam:
        raise ValueError("Avaliação não encontrada no elaborador.")
    
    questions = builder_exam.get("questions", [])
    if not questions:
        raise ValueError("A avaliação precisa ter ao menos uma questão para gerar o gabarito OMR.")
    
    # Validação Edge Case 1: todas as questões precisam ter alternativa correta
    missing_correct = []
    for q in questions:
        q_num = q.get("question_number", 1)
        alts = q.get("alternatives", [])
        if not any(a.get("is_correct") for a in alts):
            missing_correct.append(q_num)
            
    if missing_correct:
        missing_str = ", ".join(str(n) for n in sorted(missing_correct))
        raise ValueError(
            f"As seguintes questões estão sem alternativa correta definida: Questão {missing_str}. "
            f"Marque a resposta correta no elaborador antes de gerar o gabarito."
        )
    
    answer_key_dict = {}
    weights_dict = {}
    max_alt_count = 4
    
    for q in questions:
        q_num = str(q["question_number"])
        weights_dict[q_num] = float(q.get("points", 1.0))
        alts = q.get("alternatives", [])
        if len(alts) > max_alt_count:
            max_alt_count = len(alts)
        correct_letter = "A"
        for a in alts:
            if a.get("is_correct"):
                correct_letter = a.get("letter", "A").upper()
                break
        answer_key_dict[q_num] = correct_letter
        
    num_questions = len(questions)
    num_alternatives = min(5, max(4, max_alt_count))
    points_per_q = float(builder_exam.get("max_score", 10.0)) / max(1, num_questions)
    
    target_exam_id = builder_exam.get("linked_exam_id")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    existing_main = None
    existing_school = ""
    if target_exam_id:
        cursor.execute("SELECT id, school_name FROM exams WHERE id = ?", (target_exam_id,))
        existing_main = cursor.fetchone()
        if existing_main:
            try:
                existing_school = existing_main["school_name"] or ""
            except Exception:
                existing_school = existing_main[1] or ""
        
    custom = custom_params or {}
    title = (custom.get("title") or builder_exam.get("title") or "PROVA ELABORADA").strip()
    subtitle = (custom.get("subtitle") or builder_exam.get("grade_year") or "ENSINO FUNDAMENTAL").strip()
    school_name = (custom.get("school_name") or existing_school or builder_exam.get("school_name") or "").strip()
    classroom = (custom.get("classroom") or builder_exam.get("classroom") or "").strip()
    shift = normalize_builder_shift((custom.get("shift") or builder_exam.get("shift") or "MANHÃ").strip())
    
    req_page_count = custom.get("page_count")
    if req_page_count is not None and str(req_page_count).isdigit() and int(req_page_count) > 0:
        page_count = int(req_page_count)
    else:
        page_count = calculate_builder_exam_page_count(builder_exam)

    header_color = (custom.get("header_color") or "#244061").strip()
    cover_model = (custom.get("cover_model") or "opcao_4_azul_nautico_lagoa").strip()
    cover_title = (custom.get("cover_title") or "PROVA CANOA").strip()
    cover_subtitle = (custom.get("cover_subtitle") or builder_exam.get("discipline") or "AVALIAÇÃO DIAGNÓSTICA MUNICIPAL").strip()
    cover_instructions = (custom.get("cover_instructions") or "1. Preencha completamente o círculo da resposta correta.\n2. Utilize caneta esferográfica azul ou preta.\n3. Não dobre, rasure ou molhe esta folha de respostas.").strip()
    
    from app.services.database import get_submissions_by_exam
    from app.services.pdf_generator import generate_answer_sheet_pdf, DEFAULT_LOGO_PATH
    
    submissions = get_submissions_by_exam(target_exam_id) if existing_main else []
    has_submissions = len(submissions) > 0
    is_update = existing_main is not None
    
    if not is_update:
        target_exam_id = str(uuid.uuid4())
        
    # Gera a folha de respostas OMR oficial em PDF e extrai o mapa canonical de bolhas
    sheets_dir = os.path.join(BASE_DIR, "storage", "sheets")
    os.makedirs(sheets_dir, exist_ok=True)
    pdf_path = os.path.join(sheets_dir, f"exam_{target_exam_id}.pdf")
    
    pdf_bytes, template_data = generate_answer_sheet_pdf(
        exam_id=target_exam_id,
        title=title,
        subtitle=subtitle,
        school_name=school_name,
        student_name="",
        classroom=classroom,
        shift=shift,
        num_questions=num_questions,
        num_alternatives=num_alternatives,
        logo_path=DEFAULT_LOGO_PATH,
        output_path=pdf_path,
        header_color=header_color
    )
    
    template_json = json.dumps(template_data) if isinstance(template_data, dict) else (template_data or "{}")
    now = datetime.now().isoformat()
    
    skills_matrix_dict = {}
    for q in questions:
        q_num = str(q.get("question_number", 1))
        bncc = (q.get("bncc_code") or "").strip()
        skills_matrix_dict[q_num] = bncc
    skills_matrix_json = json.dumps(skills_matrix_dict)

    if not is_update:
        cursor.execute("""
            INSERT INTO exams (
                id, title, institution, num_questions, num_alternatives,
                points_per_question, answer_key, weights, subtitle, school_name,
                classroom, shift, logo_path, created_at, header_color,
                cover_model, cover_title, cover_subtitle, cover_instructions,
                sheet_template, page_count, skills_matrix
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            target_exam_id,
            title,
            builder_exam.get("institution", "PREFEITURA MUNICIPAL DE LAGOA DA CANOA - SEMED"),
            num_questions,
            num_alternatives,
            points_per_q,
            json.dumps(answer_key_dict),
            json.dumps(weights_dict),
            subtitle,
            school_name,
            classroom,
            shift,
            DEFAULT_LOGO_PATH,
            now,
            header_color,
            cover_model,
            cover_title,
            cover_subtitle,
            cover_instructions,
            template_json,
            page_count,
            skills_matrix_json
        ))
    else:
        cursor.execute("""
            UPDATE exams SET
                title = ?, subtitle = ?, school_name = ?, classroom = ?, shift = ?,
                num_questions = ?, num_alternatives = ?, points_per_question = ?,
                answer_key = ?, weights = ?, header_color = ?, cover_model = ?,
                cover_title = ?, cover_subtitle = ?, cover_instructions = ?,
                sheet_template = ?, page_count = ?, skills_matrix = ?
            WHERE id = ?
        """, (
            title, subtitle, school_name, classroom, shift,
            num_questions, num_alternatives, points_per_q,
            json.dumps(answer_key_dict), json.dumps(weights_dict), header_color,
            cover_model, cover_title, cover_subtitle, cover_instructions,
            template_json, page_count, skills_matrix_json,
            target_exam_id
        ))

    # Vincula o ID do gabarito e marca como sincronizado no elaborador
    cursor.execute("""
        UPDATE builder_exams
        SET linked_exam_id = ?, gabarito_synced_at = ?, updated_at = ?
        WHERE id = ?
    """, (target_exam_id, now, now, exam_id))
        
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "exam_id": target_exam_id,
        "title": title,
        "is_update": is_update,
        "has_submissions": has_submissions,
        "submissions_count": len(submissions),
        "num_questions": num_questions,
        "num_alternatives": num_alternatives,
        "page_count": page_count,
        "answer_key": answer_key_dict,
        "cover_model": cover_model,
        "pdf_url": f"/storage/sheets/exam_{target_exam_id}.pdf",
        "message": f"Gabarito {'atualizado' if is_update else 'criado'} com sucesso no sistema de correção!"
    }

def calculate_builder_exam_page_count(builder_exam: Dict[str, Any]) -> int:
    """
    Calcula instantaneamente (< 2ms) o número real de páginas que o caderno de prova ocupará no PDF.
    Utiliza simulação analítica de alta fidelidade das dimensões reais A4, colunas e margens.
    """
    if not builder_exam:
        return 1
        
    questions = builder_exam.get("questions", [])
    if not questions:
        return 1

    try:
        import math
        raw_top = float(builder_exam.get("margin_top") if builder_exam.get("margin_top") is not None else 3.0)
        raw_bottom = float(builder_exam.get("margin_bottom") if builder_exam.get("margin_bottom") is not None else 2.0)
        raw_left = float(builder_exam.get("margin_left") if builder_exam.get("margin_left") is not None else 3.0)
        raw_right = float(builder_exam.get("margin_right") if builder_exam.get("margin_right") is not None else 2.0)

        margin_top = (raw_top / 10.0 if raw_top > 5.0 else raw_top) * 10.0  # mm
        margin_bottom = (raw_bottom / 10.0 if raw_bottom > 5.0 else raw_bottom) * 10.0  # mm
        margin_left = (raw_left / 10.0 if raw_left > 5.0 else raw_left) * 10.0  # mm
        margin_right = (raw_right / 10.0 if raw_right > 5.0 else raw_right) * 10.0  # mm

        cols = int(builder_exam.get("columns_layout") or builder_exam.get("columns") or 2)
        header_style = builder_exam.get("header_style") or "title_only"
        include_header = builder_exam.get("include_header")
        if include_header is None:
            include_header = (header_style == "standard")
        else:
            include_header = bool(include_header)

        page_h = 297.0
        page_w = 210.0
        footer_h = 9.0
        col_gap = 8.0 if cols == 2 else 0.0

        content_w = page_w - margin_left - margin_right
        col_w = (content_w - col_gap) / 2.0 if cols == 2 else content_w
        chars_per_line = max(28, int(col_w / 1.7))

        h_header_p1 = 48.0 if include_header else 20.0
        h_header_p_sub = 8.0

        cur_page = 1
        avail_h = page_h - margin_top - margin_bottom - footer_h - h_header_p1
        col_idx = 0
        cur_col_used = 0.0

        for q in questions:
            stmt = q.get("statement", "") or ""
            stmt_lines = max(1, math.ceil(len(stmt) / chars_per_line))
            # Envelope do cartão (padding 5mm) + Header (7mm) + Enunciado (linhas * 4.6mm) + Margem (3.5mm)
            q_h = 12.0 + (stmt_lines * 4.6) + 3.5
            
            if q.get("image_url"):
                q_h += 48.0
                
            alts = q.get("alternatives", [])
            for a in alts:
                alt_text = a.get("text", "") or ""
                alt_lines = max(1, math.ceil(len(alt_text) / (chars_per_line - 10)))
                # alt-row min height 6.0mm + 1.5mm gap
                q_h += max(6.0, alt_lines * 4.4) + 1.5
                if a.get("image_url") or (a.get("image") and a.get("image").get("url")):
                    q_h += 25.0
                    
            if cur_col_used + q_h > avail_h and cur_col_used > 0:
                if col_idx < cols - 1:
                    col_idx += 1
                    cur_col_used = q_h
                else:
                    cur_page += 1
                    col_idx = 0
                    avail_h = page_h - margin_top - margin_bottom - footer_h - h_header_p_sub
                    cur_col_used = q_h
            else:
                cur_col_used += q_h

        return max(1, cur_page)
    except Exception as e:
        logger.warning(f"Erro no cálculo analítico de páginas: {e}")
        import math
        return max(1, math.ceil(len(questions) / 6.0))

def normalize_builder_shift(shift_raw: Optional[str]) -> str:
    """Normaliza nomes de turnos para coincidir exatamente com os valores do select OMR."""
    if not shift_raw:
        return "MANHÃ"
    s = str(shift_raw).strip().upper()
    if any(k in s for k in ("MAT", "MANH")):
        return "MANHÃ"
    elif any(k in s for k in ("VESP", "TARD")):
        return "TARDE"
    elif any(k in s for k in ("NOT", "NOIT")):
        return "NOITE"
    elif "INTEG" in s:
        return "INTEGRAL"
    return "MANHÃ"

def get_builder_exam_grading_status(exam_id: str) -> Dict[str, Any]:
    """
    Verifica o status do gabarito de uma avaliação do elaborador:
    - Retorna dados pré-preenchidos da prova ou do gabarito vinculado já salvo
    - Identifica se há gabarito vinculado (`linked_exam_id`) e se existem correções salvas
    - Valida Edge Case 1: lista questões sem alternativa correta marcada
    """
    builder_exam = get_builder_exam(exam_id)
    if not builder_exam:
        raise ValueError("Avaliação não encontrada no elaborador.")
        
    questions = builder_exam.get("questions", [])
    num_questions = len(questions)
    
    missing_correct = []
    answer_key_preview = {}
    for q in questions:
        q_num = q.get("question_number", 1)
        alts = q.get("alternatives", [])
        correct_alts = [a.get("letter", "A").upper() for a in alts if a.get("is_correct")]
        if not correct_alts:
            missing_correct.append(q_num)
        else:
            answer_key_preview[str(q_num)] = correct_alts[0]
            
    linked_id = builder_exam.get("linked_exam_id") or ""
    has_linked = False
    submissions_count = 0
    linked_data = None
    
    if linked_id:
        from app.services.database import get_exam, get_submissions_by_exam
        ex = get_exam(linked_id)
        if ex:
            has_linked = True
            linked_data = dict(ex) if hasattr(ex, "keys") else ex
            subs = get_submissions_by_exam(linked_id)
            submissions_count = len(subs)

    # Prioriza dados já configurados e salvos no gabarito vinculado (se existir)
    saved_title = (linked_data.get("title") if linked_data else None) or builder_exam.get("title") or "Avaliação"
    saved_subtitle = (linked_data.get("subtitle") if linked_data else None) or builder_exam.get("grade_year") or "ENSINO FUNDAMENTAL"
    saved_school = (linked_data.get("school_name") if linked_data else None) or builder_exam.get("school_name") or ""
    saved_classroom = (linked_data.get("classroom") if linked_data else None) or builder_exam.get("classroom") or ""
    raw_shift = (linked_data.get("shift") if linked_data else None) or builder_exam.get("shift") or "MANHÃ"
    saved_shift = normalize_builder_shift(raw_shift)
    
    calc_page_count = calculate_builder_exam_page_count(builder_exam)
    saved_page_count = calc_page_count or int((linked_data.get("page_count") if linked_data else None) or 1)

    synced_at = (builder_exam.get("gabarito_synced_at") or "").strip()
    updated_at = (builder_exam.get("updated_at") or "").strip()
    is_outdated = False
    if has_linked:
        if not synced_at:
            is_outdated = True
        elif updated_at and updated_at > synced_at:
            is_outdated = True
            
    return {
        "exam_id": exam_id,
        "title": saved_title,
        "subtitle": saved_subtitle,
        "discipline": builder_exam.get("discipline") or "",
        "grade_year": builder_exam.get("grade_year") or "",
        "school_name": saved_school,
        "classroom": saved_classroom,
        "shift": saved_shift,
        "page_count": saved_page_count,
        "num_questions": num_questions,
        "missing_correct_questions": sorted(missing_correct),
        "can_generate": len(missing_correct) == 0 and num_questions > 0,
        "has_linked_exam": has_linked,
        "linked_exam_id": linked_id if has_linked else "",
        "is_gabarito_outdated": is_outdated,
        "gabarito_synced_at": synced_at,
        "updated_at": updated_at,
        "submissions_count": submissions_count,
        "cover_model": (linked_data.get("cover_model") if linked_data else None) or "opcao_4_azul_nautico_lagoa",
        "cover_title": (linked_data.get("cover_title") if linked_data else None) or "PROVA CANOA",
        "cover_subtitle": (linked_data.get("cover_subtitle") if linked_data else None) or (builder_exam.get("discipline") or "AVALIAÇÃO DIAGNÓSTICA MUNICIPAL"),
        "cover_instructions": (linked_data.get("cover_instructions") if linked_data else None) or "1. Preencha completamente o círculo da resposta correta.\n2. Utilize caneta esferográfica azul ou preta.\n3. Não dobre, rasure ou molhe esta folha de respostas.",
        "header_color": (linked_data.get("header_color") if linked_data else None) or "#244061",
        "answer_key_preview": answer_key_preview
    }

def get_question_bank(
    query: str = "",
    discipline: str = "",
    grade_year: str = "",
    bncc_code: str = "",
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Retorna questões cadastradas de todas as provas para o Banco de Questões."""
    init_builder_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = ["1=1", "TRIM(q.statement) != ''"]
    params = []

    # Deduplica questões no acervo para retornar sempre uma única ocorrência de cada enunciado
    conditions.append("""
        q.id IN (
            SELECT MAX(id)
            FROM builder_questions
            WHERE TRIM(statement) != ''
            GROUP BY LOWER(TRIM(statement))
        )
    """)
    
    if query and query.strip():
        conditions.append("LOWER(q.statement) LIKE ?")
        params.append(f"%{query.strip().lower()}%")
        
    if discipline and discipline.strip() and discipline.strip().lower() != "todas":
        conditions.append("(LOWER(COALESCE(NULLIF(q.discipline, ''), e.discipline, '')) = ?)")
        params.append(discipline.strip().lower())
        
    if grade_year and grade_year.strip() and grade_year.strip().lower() != "todos":
        conditions.append("(LOWER(COALESCE(NULLIF(q.grade_year, ''), e.grade_year, '')) = ?)")
        params.append(grade_year.strip().lower())
        
    if bncc_code and bncc_code.strip():
        conditions.append("LOWER(q.bncc_code) LIKE ?")
        params.append(f"%{bncc_code.strip().lower()}%")
        
    where_clause = " AND ".join(conditions)
    
    # Total count
    count_sql = f"""
        SELECT COUNT(*) FROM builder_questions q
        LEFT JOIN builder_exams e ON q.exam_id = e.id
        WHERE {where_clause}
    """
    cursor.execute(count_sql, tuple(params))
    total_count = cursor.fetchone()[0]
    
    # Query items
    query_sql = f"""
        SELECT q.*, 
               COALESCE(NULLIF(q.discipline, ''), e.discipline, '') as exam_discipline,
               COALESCE(NULLIF(q.grade_year, ''), e.grade_year, '') as exam_grade_year,
               COALESCE(NULLIF(q.source_exam_title, ''), e.title, 'Banco Geral') as source_exam_title
        FROM builder_questions q
        LEFT JOIN builder_exams e ON q.exam_id = e.id
        WHERE {where_clause}
        ORDER BY q.created_at DESC
        LIMIT ? OFFSET ?
    """
    p_query = list(params)
    p_query.extend([limit, offset])
    cursor.execute(query_sql, tuple(p_query))
    questions = [dict(r) for r in cursor.fetchall()]
    
    # Fetch alternatives for each question
    for q in questions:
        cursor.execute("""
            SELECT * FROM builder_alternatives
            WHERE question_id = ?
            ORDER BY order_index ASC
        """, (q["id"],))
        alts = []
        for a in cursor.fetchall():
            d = dict(a)
            if d.get("image_url"):
                d["image"] = {
                    "url": d.get("image_url", ""),
                    "width": d.get("image_width", "180px"),
                    "align": d.get("image_align", "center")
                }
            alts.append(d)
        q["alternatives"] = alts
        
    conn.close()
    return {
        "items": questions,
        "questions": questions,
        "total": total_count,
        "limit": limit,
        "offset": offset
    }

def get_question_bank_filters() -> Dict[str, Any]:
    """Retorna disciplinas, anos e códigos BNCC existentes para popular filtros."""
    init_builder_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT COALESCE(NULLIF(q.discipline, ''), e.discipline, '') as disc
        FROM builder_questions q
        LEFT JOIN builder_exams e ON q.exam_id = e.id
        WHERE COALESCE(NULLIF(q.discipline, ''), e.discipline, '') != ''
        ORDER BY disc ASC
    """)
    disciplines = [r[0] for r in cursor.fetchall() if r[0]]
    
    cursor.execute("""
        SELECT DISTINCT COALESCE(NULLIF(q.grade_year, ''), e.grade_year, '') as gr
        FROM builder_questions q
        LEFT JOIN builder_exams e ON q.exam_id = e.id
        WHERE COALESCE(NULLIF(q.grade_year, ''), e.grade_year, '') != ''
        ORDER BY gr ASC
    """)
    grades = [r[0] for r in cursor.fetchall() if r[0]]
    
    cursor.execute("""
        SELECT DISTINCT q.bncc_code
        FROM builder_questions q
        WHERE q.bncc_code IS NOT NULL AND q.bncc_code != ''
        ORDER BY q.bncc_code ASC
    """)
    bncc_codes = [r[0] for r in cursor.fetchall() if r[0]]
    
    cursor.execute("""
        SELECT COUNT(*) FROM builder_questions
        WHERE id IN (
            SELECT MAX(id) FROM builder_questions
            WHERE TRIM(statement) != ''
            GROUP BY LOWER(TRIM(statement))
        )
    """)
    total_q = cursor.fetchone()[0]
    
    conn.close()
    return {
        "disciplines": disciplines,
        "grades": grades,
        "bncc_codes": bncc_codes,
        "total_questions": total_q
    }

def insert_question_into_bank(q_data: Dict[str, Any]) -> Dict[str, Any]:
    """Insere uma nova questão com alternativas diretamente no banco de questões geral."""
    conn = get_connection()
    cursor = conn.cursor()
    qid = q_data.get("id") or str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    # Próximo número sequencial de questão para o banco geral
    cursor.execute("SELECT COALESCE(MAX(question_number), 0) + 1 FROM builder_questions WHERE exam_id = 'banco_questoes_geral'")
    row = cursor.fetchone()
    next_num = row[0] if row else 1
    
    cursor.execute("""
        INSERT INTO builder_questions (
            id, exam_id, question_number, statement, points,
            image_url, image_position, image_width, image_caption,
            created_at, bncc_code, discipline, grade_year, source_exam_title, explanation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        qid,
        "banco_questoes_geral",
        next_num,
        q_data.get("statement", "").strip(),
        float(q_data.get("points") or 1.0),
        q_data.get("image_url", ""),
        q_data.get("image_position", "after_statement"),
        q_data.get("image_width", "50%"),
        q_data.get("image_caption", ""),
        now,
        (q_data.get("bncc_code") or "").strip().upper(),
        (q_data.get("discipline") or "").strip(),
        (q_data.get("grade_year") or "").strip(),
        q_data.get("source_exam_title") or "Gerador IA (Groq - Llama 3.1 8B)",
        (q_data.get("explanation") or "").strip()
    ))
    
    alternatives = q_data.get("alternatives", [])
    for idx, alt in enumerate(alternatives):
        aid = alt.get("id") or str(uuid.uuid4())
        is_corr = 1 if alt.get("is_correct") else 0
        cursor.execute("""
            INSERT INTO builder_alternatives (
                id, question_id, letter, text, is_correct, order_index,
                image_url, image_width, image_align
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            aid,
            qid,
            alt.get("letter", chr(65 + idx)),
            (alt.get("text") or "").strip(),
            is_corr,
            idx,
            alt.get("image_url", ""),
            alt.get("image_width", "180px"),
            alt.get("image_align", "center")
        ))
        
    conn.commit()
    conn.close()
    
    return {
        "id": qid,
        "success": True,
        "message": "Questão inserida no Banco de Questões com sucesso!"
    }


def normalize_statement(text: str) -> str:
    """Normaliza o enunciado convertendo para minúsculas e colapsando múltiplos espaços em branco."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', str(text).strip().lower())


def export_question_bank_data() -> Dict[str, Any]:
    """Retorna todo o acervo do Banco de Questões estruturado em formato JSON exportável."""
    init_builder_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Seleciona todas as questões únicas no banco de questões
    cursor.execute("""
        SELECT q.*,
               COALESCE(NULLIF(q.discipline, ''), e.discipline, '') as exam_discipline,
               COALESCE(NULLIF(q.grade_year, ''), e.grade_year, '') as exam_grade_year,
               COALESCE(NULLIF(q.source_exam_title, ''), e.title, 'Banco de Questões') as effective_source_title
        FROM builder_questions q
        LEFT JOIN builder_exams e ON q.exam_id = e.id
        WHERE TRIM(q.statement) != ''
          AND q.id IN (
              SELECT MAX(id)
              FROM builder_questions
              WHERE TRIM(statement) != ''
              GROUP BY LOWER(TRIM(statement))
          )
        ORDER BY q.created_at ASC
    """)
    raw_questions = [dict(r) for r in cursor.fetchall()]

    questions = []
    for q in raw_questions:
        qid = q["id"]
        cursor.execute("""
            SELECT letter, text, is_correct, order_index, image_url, image_width, image_align
            FROM builder_alternatives
            WHERE question_id = ?
            ORDER BY order_index ASC
        """, (qid,))
        alts = []
        for a in cursor.fetchall():
            d = dict(a)
            alts.append({
                "letter": d.get("letter", ""),
                "text": d.get("text") or "",
                "is_correct": bool(d.get("is_correct")),
                "order_index": d.get("order_index", 0),
                "image_url": d.get("image_url") or "",
                "image_width": d.get("image_width") or "180px",
                "image_align": d.get("image_align") or "center"
            })

        questions.append({
            "statement": (q.get("statement") or "").strip(),
            "points": float(q.get("points") or 1.0),
            "discipline": q.get("discipline") or q.get("exam_discipline") or "",
            "grade_year": q.get("grade_year") or q.get("exam_grade_year") or "",
            "bncc_code": (q.get("bncc_code") or "").strip().upper(),
            "explanation": (q.get("explanation") or "").strip(),
            "source_exam_title": q.get("source_exam_title") or q.get("effective_source_title") or "Banco de Questões",
            "image_url": q.get("image_url") or "",
            "image_position": q.get("image_position") or "after_statement",
            "image_width": q.get("image_width") or "50%",
            "image_caption": q.get("image_caption") or "",
            "alternatives": alts
        })

    conn.close()

    return {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "system": "Prova Canoa - Sistema Municipal de Avaliações",
        "total_questions": len(questions),
        "questions": questions
    }


def import_question_bank_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Importa um lote de questões de um dicionário/JSON para o Banco de Questões com desduplicação rigorosa."""
    init_builder_db()
    conn = get_connection()
    cursor = conn.cursor()

    raw_questions = data.get("questions")
    if raw_questions is None:
        if isinstance(data, list):
            raw_questions = data
        else:
            raw_questions = []

    if not isinstance(raw_questions, list):
        conn.close()
        raise ValueError("O formato do arquivo JSON é inválido. A chave 'questions' deve ser uma lista.")

    # 1. Carrega todos os enunciados já existentes no banco de dados para verificação de duplicidade
    cursor.execute("SELECT statement FROM builder_questions WHERE TRIM(statement) != ''")
    existing_rows = cursor.fetchall()
    existing_statements = {normalize_statement(r[0]) for r in existing_rows if r[0]}

    # Pega o próximo número sequencial para o banco geral
    cursor.execute("SELECT COALESCE(MAX(question_number), 0) FROM builder_questions WHERE exam_id = 'banco_questoes_geral'")
    row = cursor.fetchone()
    current_num = row[0] if row else 0

    total_in_file = len(raw_questions)
    imported_count = 0
    skipped_duplicates = 0
    skipped_empty = 0

    now = datetime.now().isoformat()

    for item in raw_questions:
        if not isinstance(item, dict):
            continue

        raw_stmt = (item.get("statement") or "").strip()
        if not raw_stmt:
            skipped_empty += 1
            continue

        norm_stmt = normalize_statement(raw_stmt)

        # Se já existe no banco (ou já foi importado nesta mesma execução), pula para evitar duplicata
        if norm_stmt in existing_statements:
            skipped_duplicates += 1
            continue

        # Registra no conjunto de enunciados existentes para evitar duplicatas dentro do próprio arquivo importado
        existing_statements.add(norm_stmt)
        current_num += 1

        qid = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO builder_questions (
                id, exam_id, question_number, statement, points,
                image_url, image_position, image_width, image_caption,
                created_at, bncc_code, discipline, grade_year, source_exam_title, explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            qid,
            "banco_questoes_geral",
            current_num,
            raw_stmt,
            float(item.get("points") or 1.0),
            item.get("image_url", ""),
            item.get("image_position", "after_statement"),
            item.get("image_width", "50%"),
            item.get("image_caption", ""),
            now,
            (item.get("bncc_code") or "").strip().upper(),
            (item.get("discipline") or "").strip(),
            (item.get("grade_year") or "").strip(),
            (item.get("source_exam_title") or "Importação de Backup").strip(),
            (item.get("explanation") or "").strip()
        ))

        alternatives = item.get("alternatives") or []
        for idx, alt in enumerate(alternatives):
            if not isinstance(alt, dict):
                continue
            aid = str(uuid.uuid4())
            is_corr = 1 if alt.get("is_correct") else 0
            cursor.execute("""
                INSERT INTO builder_alternatives (
                    id, question_id, letter, text, is_correct, order_index,
                    image_url, image_width, image_align
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                aid,
                qid,
                alt.get("letter", chr(65 + idx)),
                (alt.get("text") or "").strip(),
                is_corr,
                idx,
                alt.get("image_url", ""),
                alt.get("image_width", "180px"),
                alt.get("image_align", "center")
            ))

        imported_count += 1

    conn.commit()
    conn.close()

    return {
        "success": True,
        "total_in_file": total_in_file,
        "imported_count": imported_count,
        "skipped_duplicates": skipped_duplicates,
        "skipped_empty": skipped_empty,
        "message": (
            f"Importação concluída com sucesso! {imported_count} novas questões adicionadas. "
            f"{skipped_duplicates} questões duplicadas foram ignoradas."
            if skipped_duplicates > 0 else
            f"Importação concluída com sucesso! {imported_count} novas questões adicionadas."
        )
    }


