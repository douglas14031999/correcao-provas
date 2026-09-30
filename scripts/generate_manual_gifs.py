import os
import math
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "assets", "gifs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Fonts
FONT_PATH = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD_PATH = "C:/Windows/Fonts/segoeuib.ttf"

def get_font(size, bold=False):
    try:
        path = FONT_BOLD_PATH if bold else FONT_PATH
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_cursor(draw, x, y, clicking=False):
    # Draw arrow cursor
    pts = [(x, y), (x, y + 18), (x + 5, y + 14), (x + 9, y + 22), (x + 12, y + 21), (x + 8, y + 13), (x + 14, y + 13)]
    draw.polygon(pts, fill="#0f172a", outline="#ffffff")
    if clicking:
        draw.ellipse([x - 8, y - 8, x + 8, y + 8], outline="#38bdf8", width=2)

def draw_window_frame(draw, w, h, title="Prova Canoa — SEMED"):
    # Window background
    draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=10, fill="#f8fafc", outline="#cbd5e1", width=1)
    # Header bar
    draw.rounded_rectangle([0, 0, w - 1, 40], radius=10, fill="#ffffff")
    draw.rectangle([0, 30, w - 1, 40], fill="#ffffff")
    draw.line([0, 40, w - 1, 40], fill="#e2e8f0", width=1)
    
    # Window control dots
    draw.ellipse([14, 15, 24, 25], fill="#ef4444")
    draw.ellipse([30, 15, 40, 25], fill="#f59e0b")
    draw.ellipse([46, 15, 56, 25], fill="#10b981")
    
    # Title
    f_title = get_font(12, bold=True)
    draw.text((70, 13), title, fill="#475569", font=f_title)
    
    # SEMED badge
    f_badge = get_font(10, bold=True)
    draw.rounded_rectangle([w - 140, 10, w - 16, 30], radius=10, fill="#e0f2fe")
    draw.text((w - 132, 13), "LAGOA DA CANOA • AL", fill="#0369a1", font=f_badge)

# -------------------------------------------------------------
# GIF 1: LOGIN & ACESSO
# -------------------------------------------------------------
def make_gif_login():
    w, h = 760, 440
    frames = []
    total_frames = 45

    for i in range(total_frames):
        im = Image.new("RGB", (w, h), "#0b1528")
        draw = ImageDraw.Draw(im)
        draw_window_frame(draw, w, h, "Portal de Avaliações — Acesso Seguro")

        # Background subtle gradient/glow
        draw.ellipse([w//2 - 200, h//2 - 150, w//2 + 200, h//2 + 150], fill="#0f2347")

        # Center Card
        card_w, card_h = 320, 320
        cx = (w - card_w) // 2
        cy = 60
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=12, fill="#ffffff", outline="#e2e8f0", width=1)

        # Card Logo Badge
        draw.rounded_rectangle([cx + card_w//2 - 24, cy + 20, cx + card_w//2 + 24, cy + 68], radius=8, fill="#eff6ff", outline="#bfdbfe")
        draw.text((cx + card_w//2 - 14, cy + 32), "SEMED", fill="#0284c7", font=get_font(10, bold=True))

        # Title
        draw.text((cx + 70, cy + 80), "Portal de Avaliações", fill="#0f172a", font=get_font(16, bold=True))
        draw.text((cx + 80, cy + 104), "Secretaria de EDUCAÇÃO", fill="#64748b", font=get_font(11))

        # Inputs
        user_text = ""
        pwd_text = ""
        cursor_x = cx + 40
        cursor_y = cy + 160
        clicking = False

        if i >= 6:
            user_text = "admin"[:min(5, (i - 6) // 2)]
        if i >= 18:
            pwd_text = "••••••••"[:min(8, (i - 18) // 2)]

        # Cursor animation
        if i < 10:
            cursor_x = cx + 40 + i * 5
            cursor_y = cy + 150
        elif i < 22:
            cursor_x = cx + 40 + (i - 10) * 4
            cursor_y = cy + 205
        elif i < 35:
            # Move to submit button
            t = (i - 22) / 13
            cursor_x = int(cx + 80 + t * 80)
            cursor_y = int(cy + 205 + t * 65)
        else:
            cursor_x = cx + 160
            cursor_y = cy + 270
            if 35 <= i <= 38:
                clicking = True

        # Input 1: Usuario
        draw.rounded_rectangle([cx + 25, cy + 135, cx + card_w - 25, cy + 175], radius=6, outline="#0284c7" if i < 18 else "#cbd5e1", width=2 if i < 18 else 1)
        draw.text((cx + 36, cy + 146), user_text if user_text else "Usuário ou Matrícula", fill="#0f172a" if user_text else "#94a3b8", font=get_font(12))

        # Input 2: Senha
        draw.rounded_rectangle([cx + 25, cy + 190, cx + card_w - 25, cy + 230], radius=6, outline="#0284c7" if 18 <= i < 35 else "#cbd5e1", width=2 if 18 <= i < 35 else 1)
        draw.text((cx + 36, cy + 201), pwd_text if pwd_text else "Sua Senha", fill="#0f172a" if pwd_text else "#94a3b8", font=get_font(12))

        # Button Entrar
        btn_fill = "#1d4ed8" if clicking else "#0284c7"
        if i >= 38:
            btn_fill = "#059669" # Success green
        draw.rounded_rectangle([cx + 25, cy + 250, cx + card_w - 25, cy + 290], radius=6, fill=btn_fill)
        btn_label = "Conectando..." if i >= 38 else "Entrar na Plataforma"
        draw.text((cx + 85, cy + 262), btn_label, fill="#ffffff", font=get_font(12, bold=True))

        # Link manual at bottom
        draw.text((cx + 75, cy + 300), "📖 Manual de Uso & Documentação", fill="#0284c7", font=get_font(10, bold=True))

        # Step overlay callout
        draw.rounded_rectangle([20, h - 45, w - 20, h - 12], radius=6, fill="#0f172a", outline="#334155")
        step_msg = "Passo 1: Insira usuário e senha institucional e clique em 'Entrar'" if i < 36 else "Sucesso: Sessão autenticada via token criptográfico JWT!"
        draw.text((36, h - 35), step_msg, fill="#38bdf8" if i >= 36 else "#f8fafc", font=get_font(12, bold=True))

        draw_cursor(draw, cursor_x, cursor_y, clicking)
        frames.append(im)

    gif_path = os.path.join(OUTPUT_DIR, "gif_1_login.gif")
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=120, loop=0)
    print(f">> Gerado: {gif_path}")

# -------------------------------------------------------------
# GIF 2: SCANNER OMR (CÂMERA E LEITURA)
# -------------------------------------------------------------
def make_gif_scanner():
    w, h = 760, 440
    frames = []
    total_frames = 50

    for i in range(total_frames):
        im = Image.new("RGB", (w, h), "#f1f5f9")
        draw = ImageDraw.Draw(im)
        draw_window_frame(draw, w, h, "Correção de Provas — Leitor OMR de Alta Precisão")

        # Top Bar in App
        draw.rectangle([0, 40, w, 85], fill="#ffffff")
        draw.line([0, 85, w, 85], fill="#e2e8f0")
        draw.text((25, 55), "Simulado: MATEMÁTICA - 9º ANO", fill="#0f172a", font=get_font(12, bold=True))
        draw.text((320, 55), "Turma: 9º ANO A (MATUTINO)", fill="#475569", font=get_font(12))
        draw.rounded_rectangle([w - 180, 50, w - 25, 76], radius=6, fill="#10b981")
        draw.text((w - 165, 56), "● CÂMERA PRONTA", fill="#ffffff", font=get_font(10, bold=True))

        # Viewport Left: Camera Feed Simulator
        cam_x, cam_y, cam_w, cam_h = 25, 100, 450, 310
        draw.rounded_rectangle([cam_x, cam_y, cam_x + cam_w, cam_y + cam_h], radius=8, fill="#020617")

        # ArUco Markers
        marker_color = "#10b981" if i >= 12 else "#0284c7"
        m_size = 32
        # 4 corners
        draw.rectangle([cam_x + 20, cam_y + 20, cam_x + 20 + m_size, cam_y + 20 + m_size], fill=marker_color)
        draw.text((cam_x + 30, cam_y + 28), "0", fill="#fff", font=get_font(14, bold=True))

        draw.rectangle([cam_x + cam_w - 20 - m_size, cam_y + 20, cam_x + cam_w - 20, cam_y + 20 + m_size], fill=marker_color)
        draw.text((cam_x + cam_w - 15 - m_size, cam_y + 28), "1", fill="#fff", font=get_font(14, bold=True))

        draw.rectangle([cam_x + 20, cam_y + cam_h - 20 - m_size, cam_x + 20 + m_size, cam_y + cam_h - 20], fill=marker_color)
        draw.text((cam_x + 30, cam_y + cam_h - 15 - m_size), "3", fill="#fff", font=get_font(14, bold=True))

        draw.rectangle([cam_x + cam_w - 20 - m_size, cam_y + cam_h - 20 - m_size, cam_x + cam_w - 20, cam_y + cam_h - 20], fill=marker_color)
        draw.text((cam_x + cam_w - 15 - m_size, cam_y + cam_h - 15 - m_size), "2", fill="#fff", font=get_font(14, bold=True))

        # Sheet in center
        paper_x = cam_x + 65
        paper_y = cam_y + 30
        paper_w = cam_w - 130
        paper_h = cam_h - 60
        draw.rounded_rectangle([paper_x, paper_y, paper_x + paper_w, paper_y + paper_h], radius=4, fill="#ffffff")

        # Sheet header
        draw.rounded_rectangle([paper_x + 10, paper_y + 10, paper_x + paper_w - 10, paper_y + 35], radius=3, fill="#244061")
        draw.text((paper_x + 20, paper_y + 16), "PROVA CANOA 2026 • MATEMÁTICA", fill="#ffffff", font=get_font(8, bold=True))

        # Instructions banner in sheet
        draw.rounded_rectangle([paper_x + 10, paper_y + 40, paper_x + paper_w - 10, paper_y + 54], radius=3, fill="#e0f2fe", outline="#bae6fd")
        draw.text((paper_x + 14, paper_y + 43), "ORIENTAÇÕES: Preencha totalmente a bolha.", fill="#0369a1", font=get_font(6, bold=True))
        draw.text((paper_x + paper_w - 95, paper_y + 43), "CORRETO: [ ⬤ ]", fill="#0369a1", font=get_font(6, bold=True))

        # Bubbles table
        for r in range(8):
            row_y = paper_y + 65 + r * 18
            draw.text((paper_x + 15, row_y), f"{r+1:02d}", fill="#0f172a", font=get_font(8, bold=True))
            for opt_idx, opt_char in enumerate(["A", "B", "C", "D"]):
                dot_x = paper_x + 40 + opt_idx * 16
                is_filled = (opt_idx == (r % 4))
                is_scanned = (i >= 25 and is_filled)
                dot_fill = "#10b981" if is_scanned else ("#0f172a" if is_filled else "#ffffff")
                draw.ellipse([dot_x, row_y, dot_x + 12, row_y + 12], fill=dot_fill, outline="#0f172a")

        # Laser Scan Line
        laser_y = cam_y + 40 + int(((i % 25) / 25) * (cam_h - 80))
        draw.line([cam_x + 10, laser_y, cam_x + cam_w - 10, laser_y], fill="#38bdf8", width=3)

        # Right Panel: Recognition Results
        res_x = 490
        res_w = w - res_x - 25
        draw.rounded_rectangle([res_x, cam_y, res_x + res_w, cam_y + cam_h], radius=8, fill="#ffffff", outline="#e2e8f0")
        draw.text((res_x + 16, cam_y + 16), "Resultado da Leitura", fill="#0f172a", font=get_font(14, bold=True))

        if i < 28:
            draw.text((res_x + 16, cam_y + 50), "Aguardando alinhamento...", fill="#94a3b8", font=get_font(12))
            draw.ellipse([res_x + 80, cam_y + 120, res_x + 140, cam_y + 180], outline="#cbd5e1", width=4)
        else:
            # Score detected
            draw.rounded_rectangle([res_x + 16, cam_y + 48, res_x + res_w - 16, cam_y + 115], radius=8, fill="#d1fae5", outline="#6ee7b7")
            draw.text((res_x + 28, cam_y + 56), "ALUNO RECONHECIDO", fill="#065f46", font=get_font(9, bold=True))
            draw.text((res_x + 28, cam_y + 72), "DOUGLAS CAVALCANTE", fill="#0f172a", font=get_font(13, bold=True))
            draw.text((res_x + 28, cam_y + 92), "Nota: 10.0 / 10.0 (100% de Acerto)", fill="#059669", font=get_font(11, bold=True))

            # Breakdown
            draw.text((res_x + 16, cam_y + 130), "Respostas Auditadas:", fill="#475569", font=get_font(11, bold=True))
            for q in range(6):
                qy = cam_y + 155 + q * 22
                draw.text((res_x + 20, qy), f"Item {q+1:02d}:", fill="#64748b", font=get_font(10))
                draw.rounded_rectangle([res_x + 75, qy - 2, res_x + 120, qy + 16], radius=4, fill="#f0fdf4")
                draw.text((res_x + 82, qy), "CERTO ✓", fill="#16a34a", font=get_font(9, bold=True))

            draw.rounded_rectangle([res_x + 16, cam_y + cam_h - 45, res_x + res_w - 16, cam_y + cam_h - 12], radius=6, fill="#0284c7")
            draw.text((res_x + 40, cam_y + cam_h - 34), "Salvo Automaticamente ✓", fill="#ffffff", font=get_font(11, bold=True))

        frames.append(im)

    gif_path = os.path.join(OUTPUT_DIR, "gif_2_scanner.gif")
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=110, loop=0)
    print(f">> Gerado: {gif_path}")

# -------------------------------------------------------------
# GIF 3: NOVA PROVA & GABARITO
# -------------------------------------------------------------
def make_gif_nova_prova():
    w, h = 760, 440
    frames = []
    total_frames = 45

    for i in range(total_frames):
        im = Image.new("RGB", (w, h), "#f8fafc")
        draw = ImageDraw.Draw(im)
        draw_window_frame(draw, w, h, "Nova Prova — Cadastrar Avaliação & Capa Integrada")

        # Left Form (Cards 1 to 4)
        fx, fy, fw = 25, 55, 430
        draw.rounded_rectangle([fx, fy, fx + fw, fy + 80], radius=8, fill="#ffffff", outline="#e2e8f0")
        draw.text((fx + 16, fy + 12), "1  CABEÇALHO DA PROVA", fill="#0f172a", font=get_font(11, bold=True))

        # Title typed
        title_val = "PROVA CANOA 2026 – LÍNGUA PORTUGUESA"[:min(38, i * 2)]
        draw.rounded_rectangle([fx + 16, fy + 35, fx + fw - 16, fy + 65], radius=6, outline="#0284c7" if i < 15 else "#cbd5e1")
        draw.text((fx + 26, fy + 43), title_val if title_val else "Ex: PROVA CANOA 2026", fill="#0f172a" if title_val else "#94a3b8", font=get_font(11))

        # Card 2: Cores
        fy2 = fy + 95
        draw.rounded_rectangle([fx, fy2, fx + fw, fy2 + 75], radius=8, fill="#ffffff", outline="#e2e8f0")
        draw.text((fx + 16, fy2 + 10), "2  COR DO GABARITO & FOLHA", fill="#0f172a", font=get_font(11, bold=True))
        colors = ["#244061", "#1e3a8a", "#0f766e", "#15803d", "#c2410c", "#831843"]
        active_color_idx = 1 if i >= 18 else 0
        for c_idx, col in enumerate(colors):
            cx_btn = fx + 16 + c_idx * 64
            draw.rounded_rectangle([cx_btn, fy2 + 35, cx_btn + 56, fy2 + 62], radius=6, outline=col if c_idx == active_color_idx else "#cbd5e1", width=2 if c_idx == active_color_idx else 1)
            draw.ellipse([cx_btn + 8, fy2 + 43, cx_btn + 20, fy2 + 55], fill=col)
            draw.text((cx_btn + 24, fy2 + 43), f"C{c_idx+1}", fill="#475569", font=get_font(9, bold=True))

        # Card 4: Parâmetros
        fy3 = fy2 + 90
        draw.rounded_rectangle([fx, fy3, fx + fw, fy3 + 75], radius=8, fill="#ffffff", outline="#e2e8f0")
        draw.text((fx + 16, fy3 + 10), "4  PARÂMETROS DA AVALIAÇÃO", fill="#0f172a", font=get_font(11, bold=True))
        
        # Items quick pills
        pills = ["10 itens", "15 itens", "20 itens", "25 itens"]
        active_pill = 2 if i >= 25 else -1
        for p_idx, pl in enumerate(pills):
            px_btn = fx + 16 + p_idx * 75
            is_p_active = (p_idx == active_pill)
            draw.rounded_rectangle([px_btn, fy3 + 35, px_btn + 68, fy3 + 62], radius=12, fill="#0284c7" if is_p_active else "#f1f5f9", outline="#0284c7" if is_p_active else "#cbd5e1")
            draw.text((px_btn + 14, fy3 + 43), pl, fill="#ffffff" if is_p_active else "#475569", font=get_font(10, bold=is_p_active))

        # Action Button: Salvar
        btn_y = fy3 + 90
        draw.rounded_rectangle([fx, btn_y, fx + fw, btn_y + 40], radius=8, fill="#0284c7" if i < 35 else "#059669")
        draw.text((fx + 150, btn_y + 12), "Salvar Prova & Gerar PDF" if i < 35 else "✓ Prova Salva com Sucesso!", fill="#ffffff", font=get_font(12, bold=True))

        # Right View: Live Mockup Preview
        rx = 475
        rw = w - rx - 25
        rh = 360
        draw.rounded_rectangle([rx, fy, rx + rw, fy + rh], radius=8, fill="#ffffff", outline="#cbd5e1", width=1)
        
        # Banner in mockup
        banner_col = colors[active_color_idx]
        draw.rounded_rectangle([rx + 12, fy + 12, rx + rw - 12, fy + 48], radius=4, fill=banner_col)
        mock_title = title_val if title_val else "PROVA CANOA 2026 – LÍNGUA PORTUGUESA"
        draw.text((rx + 20, fy + 18), mock_title[:32], fill="#ffffff", font=get_font(9, bold=True))
        draw.text((rx + 20, fy + 32), "5º ANO DO ENSINO FUNDAMENTAL", fill="#bae6fd", font=get_font(7))

        # Instructions banner in preview
        draw.rounded_rectangle([rx + 12, fy + 54, rx + rw - 12, fy + 72], radius=4, fill="#e0f2fe", outline="#bae6fd")
        draw.text((rx + 16, fy + 58), "ORIENTAÇÕES: Preencha totalmente a bolha.", fill="#0369a1", font=get_font(6, bold=True))
        draw.text((rx + rw - 85, fy + 58), "CORRETO: [ ⬤ ]", fill="#0369a1", font=get_font(6, bold=True))

        # Questions matrix in mockup
        q_count = 20 if i >= 25 else 10
        for row_i in range(min(q_count, 12)):
            qy = fy + 80 + row_i * 20
            draw.text((rx + 20, qy), f"{row_i+1:02d}", fill="#0f172a", font=get_font(8, bold=True))
            for opt_j in range(4):
                dx = rx + 45 + opt_j * 20
                is_key_filled = (opt_j == (row_i % 4)) and (i >= 30)
                draw.ellipse([dx, qy, dx + 13, qy + 13], fill=banner_col if is_key_filled else "#ffffff", outline=banner_col)

        frames.append(im)

    gif_path = os.path.join(OUTPUT_DIR, "gif_3_nova_prova.gif")
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=120, loop=0)
    print(f">> Gerado: {gif_path}")

# -------------------------------------------------------------
# GIF 4: ELABORADOR DE PROVAS & BNCC
# -------------------------------------------------------------
def make_gif_elaborador():
    w, h = 760, 440
    frames = []
    total_frames = 40

    for i in range(total_frames):
        im = Image.new("RGB", (w, h), "#0f172a")
        draw = ImageDraw.Draw(im)
        draw_window_frame(draw, w, h, "Elaborador Pedagógico — Alinhamento à Matriz BNCC")

        # Search Bar
        draw.rounded_rectangle([25, 55, 450, 92], radius=6, fill="#1e293b", outline="#334155")
        search_query = "EF05MA08"[:min(8, i // 2)]
        draw.text((40, 66), f"🔍 Buscar Código BNCC: {search_query}", fill="#38bdf8" if search_query else "#94a3b8", font=get_font(12, bold=True))

        # Grade filter pill
        draw.rounded_rectangle([470, 55, 600, 92], radius=6, fill="#0284c7")
        draw.text((485, 66), "5º Ano Fundamental", fill="#ffffff", font=get_font(11, bold=True))

        # Items List
        card_y = 110
        draw.rounded_rectangle([25, card_y, 450, card_y + 130], radius=8, fill="#1e293b", outline="#38bdf8" if i >= 16 else "#334155", width=2 if i >= 16 else 1)
        draw.rounded_rectangle([35, card_y + 12, 130, card_y + 32], radius=4, fill="#0284c7")
        draw.text((42, card_y + 16), "BNCC: EF05MA08", fill="#ffffff", font=get_font(9, bold=True))
        draw.text((35, card_y + 40), "Calcular a fração de uma quantidade...", fill="#f8fafc", font=get_font(11, bold=True))
        draw.text((35, card_y + 60), "Em uma caixa há 24 lápis. 1/4 deles são azuis.", fill="#94a3b8", font=get_font(10))
        draw.text((35, card_y + 78), "(A) 4 lápis   (B) 6 lápis   (C) 8 lápis   (D) 12 lápis", fill="#64748b", font=get_font(10))

        btn_add_fill = "#10b981" if i >= 20 else "#0284c7"
        draw.rounded_rectangle([35, card_y + 98, 160, card_y + 122], radius=4, fill=btn_add_fill)
        draw.text((45, card_y + 104), "✓ Item Adicionado" if i >= 20 else "+ Inserir na Prova", fill="#ffffff", font=get_font(10, bold=True))

        # Right Preview: Exam Sheet rendering
        px = 480
        pw = w - px - 25
        draw.rounded_rectangle([px, card_y, px + pw, card_y + 300], radius=8, fill="#ffffff")
        draw.rounded_rectangle([px + 12, card_y + 12, px + pw - 12, card_y + 45], radius=4, fill="#0f172a")
        draw.text((px + 20, card_y + 20), "CADERNO DE MATEMÁTICA", fill="#ffffff", font=get_font(10, bold=True))

        if i >= 20:
            draw.text((px + 16, card_y + 60), "Questão 01 [EF05MA08]", fill="#0284c7", font=get_font(10, bold=True))
            draw.text((px + 16, card_y + 78), "Em uma caixa há 24 lápis...", fill="#0f172a", font=get_font(9))
            draw.text((px + 16, card_y + 95), "(A) 4    (B) 6    (C) 8    (D) 12", fill="#475569", font=get_font(9))

        frames.append(im)

    gif_path = os.path.join(OUTPUT_DIR, "gif_4_elaborador.gif")
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=120, loop=0)
    print(f">> Gerado: {gif_path}")

# -------------------------------------------------------------
# GIF 5: TURMAS E IMPORTAÇÃO
# -------------------------------------------------------------
def make_gif_turmas():
    w, h = 760, 440
    frames = []
    total_frames = 40

    for i in range(total_frames):
        im = Image.new("RGB", (w, h), "#f8fafc")
        draw = ImageDraw.Draw(im)
        draw_window_frame(draw, w, h, "Gestão Escolar — Cadastro de Turmas & Enturmação")

        # Header bar
        draw.rectangle([0, 40, w, 80], fill="#ffffff")
        draw.line([0, 80, w, 80], fill="#e2e8f0")
        draw.text((25, 52), "Escola: E.M.E.F. MONSENHOR CLÓVIS DUARTE", fill="#0f172a", font=get_font(12, bold=True))

        # Modal
        mx, my, mw, mh = 140, 100, 480, 310
        draw.rounded_rectangle([mx, my, mx + mw, my + mh], radius=10, fill="#ffffff", outline="#cbd5e1", width=2)
        draw.text((mx + 20, my + 16), "Cadastrar Nova Turma", fill="#0f172a", font=get_font(14, bold=True))

        # Field 1: Nome da Turma
        t_name = "5º ANO B"[:min(8, i // 2)]
        draw.text((mx + 20, my + 50), "Nome da Turma:", fill="#475569", font=get_font(11, bold=True))
        draw.rounded_rectangle([mx + 20, my + 70, mx + 220, my + 100], radius=6, outline="#0284c7" if i < 15 else "#cbd5e1")
        draw.text((mx + 30, my + 78), t_name if t_name else "Ex: 5º ANO A", fill="#0f172a" if t_name else "#94a3b8", font=get_font(11))

        # Field 2: Turno
        draw.text((mx + 240, my + 50), "Turno:", fill="#475569", font=get_font(11, bold=True))
        draw.rounded_rectangle([mx + 240, my + 70, mx + mw - 20, my + 100], radius=6, fill="#f1f5f9", outline="#cbd5e1")
        draw.text((mx + 250, my + 78), "MANHÃ (MATUTINO)", fill="#0f172a", font=get_font(11))

        # Textarea: Alunos
        draw.text((mx + 20, my + 115), "Estudantes da Turma (Colar Lista Nominal):", fill="#475569", font=get_font(11, bold=True))
        draw.rounded_rectangle([mx + 20, my + 135, mx + mw - 20, my + 240], radius=6, fill="#f8fafc", outline="#0284c7" if i >= 15 else "#cbd5e1")
        
        students = [
            "1. ADRIEL SILVA DE SOUZA",
            "2. BEATRIZ CARVALHO SANTOS",
            "3. CARLOS EDUARDO LIMA",
            "4. DOUGLAS CAVALCANTE SILVA",
            "5. EMANUELE FERREIRA COSTA"
        ]
        num_students_visible = min(5, max(0, (i - 15) // 2))
        for s_idx in range(num_students_visible):
            draw.text((mx + 30, my + 145 + s_idx * 18), students[s_idx], fill="#0f172a", font=get_font(10, bold=True))

        # Submit button
        btn_col = "#059669" if i >= 30 else "#0284c7"
        draw.rounded_rectangle([mx + mw - 160, my + 260, mx + mw - 20, my + 295], radius=6, fill=btn_col)
        draw.text((mx + mw - 145, my + 270), "✓ Turma Criada" if i >= 30 else "Salvar Turma", fill="#ffffff", font=get_font(11, bold=True))

        frames.append(im)

    gif_path = os.path.join(OUTPUT_DIR, "gif_5_turmas.gif")
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=120, loop=0)
    print(f">> Gerado: {gif_path}")

# -------------------------------------------------------------
# GIF 6: RELATÓRIOS E RENDIMENTO
# -------------------------------------------------------------
def make_gif_relatorios():
    w, h = 760, 440
    frames = []
    total_frames = 40

    for i in range(total_frames):
        im = Image.new("RGB", (w, h), "#f8fafc")
        draw = ImageDraw.Draw(im)
        draw_window_frame(draw, w, h, "Relatórios Pedagógicos & Rendimento — SEMED Canoa")

        # Top Selector
        draw.rounded_rectangle([25, 55, w - 25, 95], radius=8, fill="#ffffff", outline="#e2e8f0")
        draw.text((40, 68), "Relatório Analítico por Turma: 5º ANO A • MATEMÁTICA", fill="#0f172a", font=get_font(12, bold=True))
        
        # Export Excel Button
        btn_ex_fill = "#059669" if i >= 20 else "#10b981"
        draw.rounded_rectangle([w - 180, 62, w - 40, 88], radius=6, fill=btn_ex_fill)
        draw.text((w - 170, 68), "⬇ Baixar Excel (.xlsx)" if i < 25 else "✓ Arquivo Gerado!", fill="#ffffff", font=get_font(10, bold=True))

        # Charts / Performance Cards
        card_w = (w - 70) // 3
        draw.rounded_rectangle([25, 110, 25 + card_w, 185], radius=8, fill="#ffffff", outline="#e2e8f0")
        draw.text((38, 122), "MÉDIA DA TURMA", fill="#64748b", font=get_font(9, bold=True))
        draw.text((38, 142), "8.6", fill="#0284c7", font=get_font(24, bold=True))
        draw.text((85, 154), "/ 10.0", fill="#94a3b8", font=get_font(11))

        draw.rounded_rectangle([35 + card_w, 110, 35 + 2 * card_w, 185], radius=8, fill="#ffffff", outline="#e2e8f0")
        draw.text((48 + card_w, 122), "TAXA DE PARTICIPAÇÃO", fill="#64748b", font=get_font(9, bold=True))
        draw.text((48 + card_w, 142), "96.4%", fill="#059669", font=get_font(24, bold=True))

        draw.rounded_rectangle([45 + 2 * card_w, 110, 45 + 3 * card_w, 185], radius=8, fill="#ffffff", outline="#e2e8f0")
        draw.text((58 + 2 * card_w, 122), "PROFICIÊNCIA BNCC", fill="#64748b", font=get_font(9, bold=True))
        draw.text((58 + 2 * card_w, 142), "NÍVEL ADEQUADO", fill="#d97706", font=get_font(14, bold=True))

        # Table of Skills
        ty = 200
        draw.rounded_rectangle([25, ty, w - 25, ty + 190], radius=8, fill="#ffffff", outline="#e2e8f0")
        draw.text((40, ty + 12), "Matriz de Habilidades Diagnosticadas (BNCC)", fill="#0f172a", font=get_font(11, bold=True))

        headers = ["CÓDIGO", "HABILIDADE", "ACERTOS", "STATUS"]
        draw.line([25, ty + 35, w - 25, ty + 35], fill="#e2e8f0")
        
        rows = [
            ("EF05MA08", "Resolver problemas de multiplicação e divisão com números naturais", "91.6%", "DOMINADO"),
            ("EF05MA15", "Reconhecer figuras geométricas espaciais e suas planificações", "84.2%", "ADEQUADO"),
            ("EF05MA19", "Medir grandezas de tempo, temperatura e capacidade", "78.0%", "ADEQUADO"),
            ("EF05MA22", "Interpretar dados estatísticos em tabelas e gráficos de colunas", "95.0%", "DOMINADO"),
        ]

        for r_idx, (code, desc, pct, st) in enumerate(rows):
            ry = ty + 48 + r_idx * 32
            draw.text((40, ry), code, fill="#0284c7", font=get_font(10, bold=True))
            draw.text((120, ry), desc[:52] + "...", fill="#475569", font=get_font(10))
            draw.text((540, ry), pct, fill="#0f172a", font=get_font(10, bold=True))
            draw.rounded_rectangle([610, ry - 3, 690, ry + 16], radius=4, fill="#d1fae5" if st == "DOMINADO" else "#fef3c7")
            draw.text((620, ry), st, fill="#065f46" if st == "DOMINADO" else "#92400e", font=get_font(8, bold=True))

        frames.append(im)

    gif_path = os.path.join(OUTPUT_DIR, "gif_6_relatorios.gif")
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=120, loop=0)
    print(f">> Gerado: {gif_path}")

if __name__ == "__main__":
    print(">> Gerando os 6 GIFs animados do sistema...")
    make_gif_login()
    make_gif_scanner()
    make_gif_nova_prova()
    make_gif_elaborador()
    make_gif_turmas()
    make_gif_relatorios()
    print(">> Todos os 6 GIFs foram criados com sucesso em:", OUTPUT_DIR)
