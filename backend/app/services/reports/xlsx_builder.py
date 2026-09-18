import io
import os
from typing import Optional
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from .base_report import ReportData

from openpyxl.drawing.image import Image as OpenPyXLImage

def build_xlsx_report(data: ReportData) -> bytes:
    """Builds a formatted, styled executive Excel spreadsheet report (.xlsx)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório Oficial"
    ws.views.sheetView[0].showGridLines = True

    # Palettes
    color_navy = "1E293B"
    color_slate_header = "334155"
    color_light_gray = "F8FAFC"
    color_border = "CBD5E1"
    color_meta_bg = "F8FAFC"

    thin_border = Border(
        left=Side(style="thin", color=color_border),
        right=Side(style="thin", color=color_border),
        top=Side(style="thin", color=color_border),
        bottom=Side(style="thin", color=color_border)
    )

    font_title_entity = Font(name="Segoe UI", size=11, bold=True, color="0F172A")
    font_sub_entity = Font(name="Segoe UI", size=9.5, color="334155")
    font_school = Font(name="Segoe UI", size=10, bold=True, color="0F172A")
    font_doc_title = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    font_meta_label = Font(name="Segoe UI", size=8.5, bold=True, color="0F172A")
    font_meta_val = Font(name="Segoe UI", size=8.5, color="1E293B")
    font_th = Font(name="Segoe UI", size=9, bold=True, color="FFFFFF")
    font_td = Font(name="Segoe UI", size=9, color="0F172A")
    font_td_bold = Font(name="Segoe UI", size=9, bold=True, color="0F172A")
    font_footer = Font(name="Segoe UI", size=8, italic=True, color="64748B")

    num_cols = max(5, len(data.columns))

    # 1. INSTITUTIONAL HEADER WITH LOGO
    has_logo = False
    if data.metadata.logo_path and os.path.exists(data.metadata.logo_path):
        try:
            img = OpenPyXLImage(data.metadata.logo_path)
            img.width = 52
            img.height = 52
            ws.merge_cells(start_row=1, start_column=1, end_row=3, end_column=1)
            ws.add_image(img, "A1")
            has_logo = True
            ws.column_dimensions["A"].width = 12
        except Exception as e:
            has_logo = False

    start_col = 2 if has_logo else 1
    ws.row_dimensions[1].height = 19
    ws.row_dimensions[2].height = 16
    ws.row_dimensions[3].height = 18

    # Merge entity lines across remaining columns for seamless presentation
    ws.merge_cells(start_row=1, start_column=start_col, end_row=1, end_column=num_cols)
    c_pref = ws.cell(row=1, column=start_col, value=data.metadata.prefeitura.upper())
    c_pref.font = font_title_entity
    c_pref.alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells(start_row=2, start_column=start_col, end_row=2, end_column=num_cols)
    c_sec = ws.cell(row=2, column=start_col, value=data.metadata.secretaria.upper())
    c_sec.font = font_sub_entity
    c_sec.alignment = Alignment(horizontal="left", vertical="center")

    school_name_display = data.metadata.school_name.upper() if data.metadata.school_name else ""
    if data.metadata.inep_code:
        school_name_display += f" — INEP: {data.metadata.inep_code}"
    ws.merge_cells(start_row=3, start_column=start_col, end_row=3, end_column=num_cols)
    c_esc = ws.cell(row=3, column=start_col, value=school_name_display)
    c_esc.font = font_school
    c_esc.alignment = Alignment(horizontal="left", vertical="center")

    # Spacer
    ws.row_dimensions[4].height = 6

    # 2. DOCUMENT TITLE BANNER
    ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=num_cols)
    cell_t = ws.cell(row=5, column=1, value=data.title.upper())
    cell_t.font = font_doc_title
    cell_t.fill = PatternFill(start_color=color_navy, end_color=color_navy, fill_type="solid")
    cell_t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[5].height = 24

    # Spacer
    ws.row_dimensions[6].height = 4

    # 3. METADATA GRID (2 rows x 3 columns matching reference design)
    m = data.metadata
    ws.row_dimensions[7].height = 20
    ws.row_dimensions[8].height = 20

    # Determine balanced column splits for the 3 metadata columns
    c1_end = max(2, round(num_cols * 0.44))
    c2_end = max(c1_end + 1, c1_end + round(num_cols * 0.32))
    if c2_end >= num_cols:
        c2_end = num_cols - 1

    # Style all background and borders in metadata block first
    for r in range(7, 9):
        for c in range(1, num_cols + 1):
            cell_m = ws.cell(row=r, column=c)
            cell_m.fill = PatternFill(start_color=color_meta_bg, end_color=color_meta_bg, fill_type="solid")
            cell_m.border = thin_border
            if not cell_m.value:
                cell_m.value = ""

    # Row 7: Turma | Turno | Ano Letivo
    ws.merge_cells(start_row=7, start_column=1, end_row=7, end_column=c1_end)
    c_turma = ws.cell(row=7, column=1, value=f"Turma: {m.classroom_name or '-'}")
    c_turma.font = font_meta_label
    c_turma.alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells(start_row=7, start_column=c1_end + 1, end_row=7, end_column=c2_end)
    c_turno = ws.cell(row=7, column=c1_end + 1, value=f"Turno: {m.shift or '( ) MANHÃ       ( ) TARDE'}")
    c_turno.font = font_meta_label
    c_turno.alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells(start_row=7, start_column=c2_end + 1, end_row=7, end_column=num_cols)
    c_ano = ws.cell(row=7, column=c2_end + 1, value=f"Ano Letivo: {m.school_year or '2026'}")
    c_ano.font = font_meta_label
    c_ano.alignment = Alignment(horizontal="left", vertical="center")

    # Row 8: Avaliação | Série/Ano | Total Alunos
    ws.merge_cells(start_row=8, start_column=1, end_row=8, end_column=c1_end)
    c_aval = ws.cell(row=8, column=1, value=f"Avaliação: {m.exam_title or 'Geral'}")
    c_aval.font = font_meta_label
    c_aval.alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells(start_row=8, start_column=c1_end + 1, end_row=8, end_column=c2_end)
    c_serie = ws.cell(row=8, column=c1_end + 1, value=f"Série/Ano: {m.grade_year or '-'}")
    c_serie.font = font_meta_label
    c_serie.alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells(start_row=8, start_column=c2_end + 1, end_row=8, end_column=num_cols)
    c_total = ws.cell(row=8, column=c2_end + 1, value=f"Total Alunos: {len(data.rows)}")
    c_total.font = font_meta_label
    c_total.alignment = Alignment(horizontal="left", vertical="center")

    # Spacer
    ws.row_dimensions[9].height = 6

    # 4. SUMMARY CARDS (KPIs)
    current_row = 10
    if data.summary_cards:
        ws.row_dimensions[current_row].height = 26
        for idx, card in enumerate(data.summary_cards[:num_cols], start=1):
            cell_k = ws.cell(row=current_row, column=idx, value=f"{card.get('label')}: {card.get('value')}")
            cell_k.font = font_meta_label
            cell_k.fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
            cell_k.border = thin_border
            cell_k.alignment = Alignment(horizontal="center", vertical="center")
        current_row += 2

    # 5. DATA TABLE
    table_header_row = current_row
    ws.row_dimensions[table_header_row].height = 22

    for c_idx, col in enumerate(data.columns, start=1):
        c = ws.cell(row=table_header_row, column=c_idx, value=col.header)
        c.font = font_th
        c.fill = PatternFill(start_color=color_slate_header, end_color=color_slate_header, fill_type="solid")
        c.alignment = Alignment(horizontal=col.align, vertical="center")
        c.border = thin_border

    data_start_row = table_header_row + 1
    for r_idx, row_dict in enumerate(data.rows, start=data_start_row):
        ws.row_dimensions[r_idx].height = 19
        is_even = (r_idx % 2 == 0)
        row_fill = PatternFill(start_color=color_light_gray, end_color=color_light_gray, fill_type="solid") if is_even else PatternFill(fill_type=None)

        for c_idx, col in enumerate(data.columns, start=1):
            val = row_dict.get(col.key)
            cell_d = ws.cell(row=r_idx, column=c_idx, value=val)
            cell_d.font = font_td
            cell_d.alignment = Alignment(horizontal=col.align, vertical="center")
            cell_d.border = thin_border
            if is_even:
                cell_d.fill = row_fill

            # Numeric formatting
            if col.format_type == "decimal" and isinstance(val, (int, float)):
                cell_d.number_format = "0.0"
            elif col.format_type == "percent" and isinstance(val, (int, float)):
                cell_d.number_format = "0.0%"
            elif col.is_numeric and isinstance(val, (int, float)):
                cell_d.number_format = "#,##0.0"

    # Auto-fit column widths
    for col_idx in range(1, len(data.columns) + 1):
        col_letter = get_column_letter(col_idx)
        max_len = 0
        for r in range(table_header_row, table_header_row + len(data.rows) + 1):
            val = ws.cell(row=r, column=col_idx).value
            if val is not None:
                max_len = max(max_len, len(str(val)))
        ws.column_dimensions[col_letter].width = max(12, min(max_len + 4, 45))

    # FOOTER SIGNATURES
    sig_row = data_start_row + len(data.rows) + 3
    ws.cell(row=sig_row, column=1, value="_________________________________________").font = font_td_bold
    ws.cell(row=sig_row + 1, column=1, value=data.signatures[0] if data.signatures else "Responsável").font = font_footer

    if num_cols >= 4 and len(data.signatures) > 1:
        ws.cell(row=sig_row, column=num_cols - 1, value="_________________________________________").font = font_td_bold
        ws.cell(row=sig_row + 1, column=num_cols - 1, value=data.signatures[1]).font = font_footer

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
