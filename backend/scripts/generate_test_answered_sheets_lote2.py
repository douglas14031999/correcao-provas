import os
import sys
import json
import sqlite3
import shutil
import pymupdf as fitz
from reportlab.lib import pagesizes, colors
from reportlab.pdfgen import canvas

# Configure paths
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

from app.services.pdf_generator import render_sheet_unit, DEFAULT_LOGO_PATH
from app.services.omr_engine import grade_submission

OUTPUT_DIR = os.path.join(BACKEND_DIR, "storage", "gabaritos_teste")
STATIC_OUTPUT_DIR = os.path.join(ROOT_DIR, "frontend", "assets", "gabaritos_teste")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STATIC_OUTPUT_DIR, exist_ok=True)

DB_PATH = os.path.join(BACKEND_DIR, "storage", "exams.db")

def main():
    print("Iniciando geração do LOTE 2 de gabaritos teste com novos alunos...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 6 Configurações com Turmas diferentes (Vespertino e 9º B) e Alunos diferentes
    test_configs = [
        {
            "class_filter": "%8%A%VESP%",
            "subject_filter": "PORTUGUES",
            "student_offset": 0,
            "desc": "Nota 10.0 - Gabaritou (22 Acertos, 0 Erros)",
            "wrong_indices": [],
            "blank_indices": [],
            "double_indices": []
        },
        {
            "class_filter": "%8%A%VESP%",
            "subject_filter": "MATEMAT",
            "student_offset": 1,
            "desc": "Nota 9.1 (20 Acertos, 2 Erros)",
            "wrong_indices": [5, 17],
            "blank_indices": [],
            "double_indices": []
        },
        {
            "class_filter": "%8%B%VESP%",
            "subject_filter": "PORTUGUES",
            "student_offset": 0,
            "desc": "Nota 8.2 (18 Acertos, 4 Erros)",
            "wrong_indices": [3, 9, 14, 21],
            "blank_indices": [],
            "double_indices": []
        },
        {
            "class_filter": "%8%B%VESP%",
            "subject_filter": "MATEMAT",
            "student_offset": 1,
            "desc": "Nota 6.8 (15 Acertos, 5 Erros, 2 Em Branco)",
            "wrong_indices": [4, 8, 11, 16, 20],
            "blank_indices": [12, 22],
            "double_indices": []
        },
        {
            "class_filter": "%9%B%MATUT%",
            "subject_filter": "PORTUGUES",
            "student_offset": 0,
            "desc": "Nota 5.5 (12 Acertos, 9 Erros, 1 Dupla Marcação)",
            "wrong_indices": [2, 6, 7, 10, 13, 15, 18, 19, 21],
            "blank_indices": [],
            "double_indices": [8]
        },
        {
            "class_filter": "%9%B%MATUT%",
            "subject_filter": "MATEMAT",
            "student_offset": 1,
            "desc": "Nota 8.6 (19 Acertos, 3 Erros)",
            "wrong_indices": [4, 11, 19],
            "blank_indices": [],
            "double_indices": []
        }
    ]

    selected_data = []

    for idx, cfg in enumerate(test_configs):
        c.execute("""
            SELECT ce.classroom_id, c.name as class_name, c.shift, s.name as school_name,
                   e.id as exam_id, e.title as exam_title, e.num_questions, e.num_alternatives,
                   e.answer_key, e.points_per_question, e.header_color, e.subtitle
            FROM classroom_exams ce
            JOIN classrooms c ON ce.classroom_id = c.id
            JOIN schools s ON c.school_id = s.id
            JOIN exams e ON ce.exam_id = e.id
            WHERE c.name LIKE ?
            ORDER BY c.name
        """, (cfg["class_filter"],))
        rows = c.fetchall()

        target_row = None
        for r in rows:
            clean_title = r["exam_title"].upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O")
            if cfg["subject_filter"] in clean_title:
                target_row = r
                break
        if not target_row and rows:
            target_row = rows[0]

        # Get student
        c.execute("""
            SELECT s.id, s.name, s.registration
            FROM students s
            WHERE s.classroom_id = ?
            ORDER BY s.name
            LIMIT 1 OFFSET ?
        """, (target_row["classroom_id"], cfg["student_offset"]))
        student_row = c.fetchone()
        student = dict(student_row)

        target_dict = dict(target_row)

        ans_key = json.loads(target_dict["answer_key"]) if isinstance(target_dict["answer_key"], str) else target_dict["answer_key"]

        num_q = target_dict["num_questions"] or 20
        student_answers = {}

        for q_num in range(1, num_q + 1):
            q_str = str(q_num)
            correct_opt = ans_key.get(q_str, "A")

            if q_num in cfg["blank_indices"]:
                student_answers[q_str] = "BLANK"
            elif q_num in cfg["double_indices"]:
                student_answers[q_str] = f"{correct_opt},B" if correct_opt != "B" else "A,B"
            elif q_num in cfg["wrong_indices"]:
                opts = ["A", "B", "C", "D"]
                wrong_opt = [o for o in opts if o != correct_opt][0]
                student_answers[q_str] = wrong_opt
            else:
                student_answers[q_str] = correct_opt

        selected_data.append({
            "config": cfg,
            "exam": target_dict,
            "student": student,
            "answers": student_answers
        })

    conn.close()

    # Generate Unified Multi-Page PDF (2 per page) in memory
    import io
    pdf_buffer = io.BytesIO()
    page_w, page_h = pagesizes.A4
    half_h = page_h / 2.0
    pdf_canvas = canvas.Canvas(pdf_buffer, pagesize=pagesizes.A4)

    page_images_info = []

    # Render in pairs of 2 per page
    num_pairs = (len(selected_data) + 1) // 2
    for page_idx in range(num_pairs):
        top_idx = page_idx * 2
        bot_idx = top_idx + 1

        top_item = selected_data[top_idx]
        bot_item = selected_data[bot_idx] if bot_idx < len(selected_data) else None

        # Render Top Sheet
        ex_top = top_item["exam"]
        st_top = top_item["student"]
        cfg_top = top_item["config"]
        ans_top = top_item["answers"]

        print(f"Renderizando Página {page_idx + 1} - Superior: {st_top['name']} ({ex_top['class_name']}) - {cfg_top['desc']}...")
        render_sheet_unit(
            c=pdf_canvas,
            x0=0,
            y0=half_h,
            width=page_w,
            height=half_h,
            exam_id=ex_top["exam_id"],
            title=ex_top["exam_title"],
            subtitle=ex_top["subtitle"] or "ENSINO FUNDAMENTAL",
            school_name=ex_top["school_name"],
            student_name=st_top["name"],
            student_id=st_top["id"],
            classroom=ex_top["class_name"],
            shift=ex_top["shift"] or "VESPERTINO",
            num_questions=ex_top["num_questions"],
            num_alternatives=ex_top["num_alternatives"] or 4,
            logo_path=DEFAULT_LOGO_PATH,
            is_compact=True,
            header_color=ex_top["header_color"] or "#244061",
            filled_answers=ans_top
        )

        # Scissor Cut Line in middle
        pdf_canvas.setStrokeColor(colors.HexColor("#94a3b8"))
        pdf_canvas.setLineWidth(0.8)
        pdf_canvas.setDash([4, 4])
        pdf_canvas.line(16, half_h, page_w - 16, half_h)
        pdf_canvas.setDash([])

        pdf_canvas.setFont("Helvetica-Bold", 6.5)
        pdf_canvas.setFillColor(colors.HexColor("#64748b"))
        pdf_canvas.drawCentredString(page_w / 2.0, half_h - 2.5, "✂ - - - - - - - - CORTE AQUI PARA DESTACAR AS DUAS FOLHAS - - - - - - - - ✂")

        # Render Bottom Sheet
        if bot_item:
            ex_bot = bot_item["exam"]
            st_bot = bot_item["student"]
            cfg_bot = bot_item["config"]
            ans_bot = bot_item["answers"]

            print(f"Renderizando Página {page_idx + 1} - Inferior: {st_bot['name']} ({ex_bot['class_name']}) - {cfg_bot['desc']}...")
            render_sheet_unit(
                c=pdf_canvas,
                x0=0,
                y0=0,
                width=page_w,
                height=half_h,
                exam_id=ex_bot["exam_id"],
                title=ex_bot["exam_title"],
                subtitle=ex_bot["subtitle"] or "ENSINO FUNDAMENTAL",
                school_name=ex_bot["school_name"],
                student_name=st_bot["name"],
                student_id=st_bot["id"],
                classroom=ex_bot["class_name"],
                shift=ex_bot["shift"] or "VESPERTINO",
                num_questions=ex_bot["num_questions"],
                num_alternatives=ex_bot["num_alternatives"] or 4,
                logo_path=DEFAULT_LOGO_PATH,
                is_compact=True,
                header_color=ex_bot["header_color"] or "#244061",
                filled_answers=ans_bot
            )

        pdf_canvas.showPage()

    pdf_canvas.save()
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()

    def safe_write(path: str, data: bytes):
        try:
            with open(path, "wb") as f:
                f.write(data)
            print(f"[OK] Arquivo salvo em: {path}")
            return True
        except PermissionError:
            print(f"[AVISO] Arquivo bloqueado por outro aplicativo: {path}")
            return False

    pdf_path_lote2 = os.path.join(OUTPUT_DIR, "GABARITOS_TESTE_LOTE_2.pdf")
    safe_write(pdf_path_lote2, pdf_bytes)
    root_pdf_path_lote2 = os.path.join(ROOT_DIR, "GABARITOS_TESTE_LOTE_2.pdf")
    safe_write(root_pdf_path_lote2, pdf_bytes)

    # Render each page and each half-sheet into high-resolution JPG images (250 DPI)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    sheet_counter = 1

    for page_idx, page in enumerate(doc):
        pw = page.rect.width
        ph = page.rect.height
        mid_y = ph / 2.0

        # Save full page preview
        full_page_pix = page.get_pixmap(dpi=200)
        full_page_name = f"Lote2_Pagina_{page_idx + 1:02d}_Completa_2_por_folha.jpg"
        full_page_pix.save(os.path.join(OUTPUT_DIR, full_page_name))
        full_page_pix.save(os.path.join(STATIC_OUTPUT_DIR, full_page_name))

        rect_top = fitz.Rect(0, 0, pw, mid_y)
        rect_bot = fitz.Rect(0, mid_y, pw, ph)

        halves = [(rect_top, selected_data[page_idx * 2])]
        if page_idx * 2 + 1 < len(selected_data):
            halves.append((rect_bot, selected_data[page_idx * 2 + 1]))

        for rect_clip, item in halves:
            st = item["student"]
            ex = item["exam"]
            cfg = item["config"]

            pix = page.get_pixmap(clip=rect_clip, dpi=250)

            clean_student = "".join([c for c in st["name"].split()[0] if c.isalnum()]).upper()
            clean_class = ex["class_name"].replace("º", "").replace(" ", "_").replace("-", "").replace("__", "_")
            clean_subject = "PORTUGUES" if "PORTUGUESA" in ex["exam_title"].upper() else "MATEMATICA"

            file_name = f"Lote2_Folha_{sheet_counter:02d}_{clean_class}_{clean_subject}_{clean_student}.jpg"
            img_path = os.path.join(OUTPUT_DIR, file_name)
            pix.save(img_path)

            static_img_path = os.path.join(STATIC_OUTPUT_DIR, file_name)
            shutil.copyfile(img_path, static_img_path)

            # Test OMR Engine with this image
            with open(img_path, "rb") as img_f:
                img_bytes = img_f.read()

            omr_result = grade_submission(img_bytes, ex["exam_id"], st["name"])
            score = omr_result.get("score", 0.0)
            max_score = omr_result.get("max_score", 10.0)
            correct_cnt = omr_result.get("correct_count", 0)
            wrong_cnt = omr_result.get("wrong_count", 0)
            blank_cnt = omr_result.get("blank_count", 0)
            detected_student = omr_result.get("student_name", "N/A")

            page_images_info.append({
                "sheet_num": sheet_counter,
                "page": page_idx + 1,
                "position": "Superior (Topo)" if rect_clip == rect_top else "Inferior (Base)",
                "filename": file_name,
                "student_name": st["name"],
                "classroom": ex["class_name"],
                "school": ex["school_name"],
                "subject": ex["exam_title"],
                "expected_profile": cfg["desc"],
                "omr_score": f"{score:.1f} / {max_score:.1f}",
                "omr_correct": correct_cnt,
                "omr_wrong": wrong_cnt,
                "omr_blank": blank_cnt,
                "detected_student": detected_student,
                "local_path": img_path,
                "web_url": f"/static/assets/gabaritos_teste/{file_name}"
            })
            sheet_counter += 1

    manifest_path = os.path.join(OUTPUT_DIR, "manifest_lote2.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(page_images_info, mf, ensure_ascii=False, indent=2)

    print("\n" + "="*70)
    print("RESUMO DO LOTE 2 DE GABARITOS TESTE GERADOS E TESTADOS COM SUCESSO:")
    print("="*70)
    for info in page_images_info:
        print(f"Folha #{info['sheet_num']} (Pág {info['page']} - {info['position']}): {info['student_name']} ({info['classroom']})")
        print(f"  Disciplina: {info['subject']}")
        print(f"  Perfil:     {info['expected_profile']}")
        print(f"  Resultado:  Nota {info['omr_score']} ({info['omr_correct']} Acertos, {info['omr_wrong']} Erros, {info['omr_blank']} Em Branco)")
        print(f"  Arquivo:    {info['filename']}")
        print("-"*70)

    print(f"\nPDF Completo: {root_pdf_path_lote2}")
    print(f"Pasta de Imagens: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
