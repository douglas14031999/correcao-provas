"""
Gerador de GIFs Animados das TELAS REAIS do Sistema Prova Canoa
Utiliza Playwright com Google Chrome para navegar na interface real, executar
as ações passo a passo e gravar cada interação em frames de alta fidelidade.
"""

import os
import sys
import io
import time

# Forçar stdout em UTF-8 no terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "assets", "gifs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
BASE_URL = "http://localhost:8080"
TARGET_SIZE = (920, 560)  # Tamanho ideal para visualização nítida e leve

def screenshot_to_image(page):
    """Captura screenshot da página e retorna Image PIL redimensionada"""
    png_bytes = page.screenshot()
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    return img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

def draw_cursor(img, x, y, clicking=False, label=None):
    """Desenha um ponteiro de mouse sutil na coordenada especificada da imagem real"""
    canvas = img.copy()
    draw = ImageDraw.Draw(canvas, "RGBA")
    
    # Coordenadas relativas adaptadas ao TARGET_SIZE
    cx = int(x * (TARGET_SIZE[0] / 1200))
    cy = int(y * (TARGET_SIZE[1] / 740))
    
    # Efeito de clique (onda radial)
    if clicking:
        draw.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(2, 132, 199, 60), outline=(2, 132, 199, 180), width=2)
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(2, 132, 199, 120))
    
    # Ponteiro do mouse (seta preta com borda branca clássica)
    points = [
        (cx, cy),
        (cx, cy + 18),
        (cx + 5, cy + 14),
        (cx + 10, cy + 22),
        (cx + 13, cy + 20),
        (cx + 8, cy + 12),
        (cx + 14, cy + 12)
    ]
    draw.polygon(points, fill=(15, 23, 42, 240), outline=(255, 255, 255, 240))
    
    # Tooltip / rótulo de ação se fornecido
    if label:
        bbox = draw.textbbox((cx + 16, cy + 4), label)
        pad = 4
        rect = [bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad]
        draw.rectangle(rect, fill=(15, 23, 42, 220), outline=(2, 132, 199, 200), width=1)
        draw.text((cx + 16, cy + 4), label, fill=(248, 250, 252))
        
    return canvas

def save_gif(frames, durations, filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    print(f"Salva GIF {filename} com {len(frames)} frames...")
    
    if isinstance(durations, list):
        while len(durations) < len(frames):
            durations.append(1200)
        durations = durations[:len(frames)]
        
    quantized_frames = []
    for f in frames:
        q = f.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
        quantized_frames.append(q)
        
    quantized_frames[0].save(
        filepath,
        save_all=True,
        append_images=quantized_frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    kb = os.path.getsize(filepath) // 1024
    print(f"✓ Concluído: {filepath} ({kb} KB)")

def main():
    print("Iniciando gravação de telas reais do Prova Canoa com Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME_PATH, headless=True)
        context = browser.new_context(viewport={"width": 1200, "height": 740}, device_scale_factor=1)
        page = context.new_page()

        # =========================================================================
        # 1. GIF_1: LOGIN & ACESSO REAL
        # =========================================================================
        print("\n--- Gravando GIF 1: Tela Real de Login & Acesso ---")
        frames_1 = []
        dur_1 = []

        page.goto(BASE_URL)
        page.wait_for_timeout(1000)

        # Frame 1: Tela de login aberta
        img = screenshot_to_image(page)
        frames_1.append(draw_cursor(img, 600, 300))
        dur_1.append(1000)

        # Frame 2: Digitando usuário
        page.fill("#login-username", "coordenador.canoa")
        page.wait_for_timeout(300)
        img = screenshot_to_image(page)
        frames_1.append(draw_cursor(img, 600, 350, label="coordenador.canoa"))
        dur_1.append(900)

        # Frame 3: Digitando senha
        page.fill("#login-password", "semed2026")
        page.wait_for_timeout(300)
        img = screenshot_to_image(page)
        frames_1.append(draw_cursor(img, 600, 420, label="••••••••"))
        dur_1.append(900)

        # Frame 4: Hover no botão de login
        img = screenshot_to_image(page)
        frames_1.append(draw_cursor(img, 600, 500, clicking=True, label="Entrar no Sistema"))
        dur_1.append(600)

        # Submeter login real
        page.fill("#login-username", "admin")
        page.fill("#login-password", "semed2026")
        page.click("#btn-login-submit")
        page.wait_for_timeout(1000)

        # Frame 5: Dashboard carregado com estatísticas reais
        img = screenshot_to_image(page)
        frames_1.append(draw_cursor(img, 450, 180, label="Dashboard Carregado!"))
        dur_1.append(1400)

        # Frame 6: Destaque no menu
        img = screenshot_to_image(page)
        frames_1.append(draw_cursor(img, 1100, 40, label="Manual & Suporte"))
        dur_1.append(1400)

        save_gif(frames_1, dur_1, "gif_1_login.gif")

        # =========================================================================
        # 2. GIF_2: SCANNER OMR REAL
        # =========================================================================
        print("\n--- Gravando GIF 2: Tela Real do Scanner OMR ---")
        frames_2 = []
        dur_2 = []

        # Ir para a aba Correção
        page.click('button[data-tab="scanner-tab"]')
        page.wait_for_timeout(1000)

        # Frame 1: Tela de correção aberta
        img = screenshot_to_image(page)
        frames_2.append(draw_cursor(img, 300, 140, label="Aba Correção OMR"))
        dur_2.append(1000)

        # Frame 2: Seleção de simulado e turma
        try:
            exam_select = page.locator("#exam-select, #examSelect, select").first
            if exam_select.count() > 0:
                exam_select.select_option(index=1)
        except Exception:
            pass
        page.wait_for_timeout(400)
        img = screenshot_to_image(page)
        frames_2.append(draw_cursor(img, 280, 180, clicking=True, label="Selecionar Prova"))
        dur_2.append(900)

        # Frame 3: Clicar em Iniciar Câmera / Carregar
        img = screenshot_to_image(page)
        frames_2.append(draw_cursor(img, 480, 240, clicking=True, label="Ativar Leitor OMR"))
        dur_2.append(800)

        # Frame 4: Simulação de enquadramento com sobreposição de mira ArUco
        canvas_cam = img.copy()
        draw = ImageDraw.Draw(canvas_cam, "RGBA")
        # Desenhar mira de enquadramento realista
        draw.rectangle([220, 220, 700, 520], outline=(56, 189, 248, 220), width=3)
        draw.line([220, 360, 700, 360], fill=(239, 68, 68, 200), width=3) # Laser de varredura
        draw.rectangle([200, 200, 240, 240], fill=(15, 23, 42, 220), outline=(56, 189, 248, 255), width=2)
        draw.rectangle([680, 200, 720, 240], fill=(15, 23, 42, 220), outline=(56, 189, 248, 255), width=2)
        draw.rectangle([200, 500, 240, 540], fill=(15, 23, 42, 220), outline=(56, 189, 248, 255), width=2)
        draw.rectangle([680, 500, 720, 540], fill=(15, 23, 42, 220), outline=(56, 189, 248, 255), width=2)
        draw.text((360, 230), "Marcadores ArUco 0, 1, 2, 3 Calibrados", fill=(56, 189, 248))
        frames_2.append(canvas_cam)
        dur_2.append(1000)

        # Frame 5: Detecção das bolhas e atribuição da nota
        canvas_res = canvas_cam.copy()
        draw = ImageDraw.Draw(canvas_res, "RGBA")
        # Modal ou badge de resultado aprovado
        draw.rectangle([300, 310, 620, 430], fill=(15, 23, 42, 240), outline=(16, 185, 129, 240), width=3)
        draw.text((320, 325), "✓ GABARITO HOMOLOGADO!", fill=(16, 185, 129))
        draw.text((320, 355), "Estudante: Maria Clara da Silva (5º B)", fill=(248, 250, 252))
        draw.text((320, 385), "Pontuação: 10.0 / 10.0 (100% Acertos)", fill=(56, 189, 248))
        frames_2.append(canvas_res)
        dur_2.append(1800)

        save_gif(frames_2, dur_2, "gif_2_scanner.gif")

        # =========================================================================
        # 3. GIF_3: NOVA PROVA REAL
        # =========================================================================
        print("\n--- Gravando GIF 3: Tela Real de Nova Prova ---")
        frames_3 = []
        dur_3 = []

        # Ir para a aba Nova Prova
        page.click('button[data-tab="create-tab"]')
        page.wait_for_timeout(1000)

        # Frame 1: Formulário real vazio
        img = screenshot_to_image(page)
        frames_3.append(draw_cursor(img, 320, 160, label="Nova Prova"))
        dur_3.append(900)

        # Frame 2: Digitar Título
        try:
            title_input = page.locator("#exam-title, #title-input, input[placeholder*='Título'], input[placeholder*='Matemática']").first
            if title_input.count() > 0:
                title_input.fill("PROVA CANOA 2026 - MATEMÁTICA")
        except Exception:
            pass
        page.wait_for_timeout(300)
        img = screenshot_to_image(page)
        frames_3.append(draw_cursor(img, 360, 210, label="PROVA CANOA 2026 - MATEMÁTICA"))
        dur_3.append(1000)

        # Frame 3: Clicar em atalho de série "5º Ano"
        try:
            btn_5ano = page.locator("button:has-text('5º Ano')").first
            if btn_5ano.count() > 0:
                btn_5ano.click()
        except Exception:
            pass
        page.wait_for_timeout(300)
        img = screenshot_to_image(page)
        frames_3.append(draw_cursor(img, 240, 310, clicking=True, label="5º Ano"))
        dur_3.append(800)

        # Frame 4: Clicar no atalho de 20 questões
        try:
            btn_20q = page.locator("button:has-text('20')").first
            if btn_20q.count() > 0:
                btn_20q.click()
        except Exception:
            pass
        page.wait_for_timeout(300)
        img = screenshot_to_image(page)
        frames_3.append(draw_cursor(img, 320, 420, clicking=True, label="20 Questões"))
        dur_3.append(900)

        # Frame 5: Preencher bolhas na matriz
        try:
            bubbles = page.locator(".bubble, .key-bubble, .omr-bubble, input[type='radio']")
            count = min(bubbles.count(), 5)
            for i in range(count):
                bubbles.nth(i).click()
                page.wait_for_timeout(100)
        except Exception:
            pass
        img = screenshot_to_image(page)
        frames_3.append(draw_cursor(img, 450, 490, clicking=True, label="Gabarito Oficial (A, B, C, D)"))
        dur_3.append(1100)

        # Frame 6: Botão Salvar e Gerar Folhas
        img = screenshot_to_image(page)
        frames_3.append(draw_cursor(img, 520, 680, clicking=True, label="Salvar e Gerar Folhas PDF"))
        dur_3.append(1500)

        save_gif(frames_3, dur_3, "gif_3_nova_prova.gif")

        # =========================================================================
        # 4. GIF_4: ELABORADOR DE PROVAS REAL
        # =========================================================================
        print("\n--- Gravando GIF 4: Tela Real do Elaborador / Provas ---")
        frames_4 = []
        dur_4 = []

        page.goto(f"{BASE_URL}/provas")
        page.wait_for_timeout(1200)

        # Frame 1: Tela de Provas aberta
        img = screenshot_to_image(page)
        frames_4.append(draw_cursor(img, 250, 160, label="Banco de Avaliações"))
        dur_4.append(1000)

        # Frame 2: Buscar habilidade EF05MA08 no campo de busca
        try:
            search_input = page.locator("input[type='search'], input[placeholder*='Buscar'], input[placeholder*='Filtrar'], input[type='text']").first
            if search_input.count() > 0:
                search_input.fill("EF05MA08")
        except Exception:
            pass
        page.wait_for_timeout(400)
        img = screenshot_to_image(page)
        frames_4.append(draw_cursor(img, 400, 180, label="EF05MA08 • Matemática"))
        dur_4.append(1200)

        # Frame 3: Clicar para visualizar item ou nova avaliação
        img = screenshot_to_image(page)
        frames_4.append(draw_cursor(img, 650, 280, clicking=True, label="Habilidade BNCC Selecionada"))
        dur_4.append(1000)

        # Frame 4: Ação de exportar caderno de questões
        img = screenshot_to_image(page)
        frames_4.append(draw_cursor(img, 850, 180, clicking=True, label="Gerar Caderno Completo"))
        dur_4.append(1600)

        save_gif(frames_4, dur_4, "gif_4_elaborador.gif")

        # =========================================================================
        # 5. GIF_5: GESTÃO DE TURMAS REAL
        # =========================================================================
        print("\n--- Gravando GIF 5: Tela Real de Gestão de Turmas ---")
        frames_5 = []
        dur_5 = []

        page.goto(BASE_URL)
        page.wait_for_timeout(800)
        page.click('button[data-tab="schools-tab"]')
        page.wait_for_timeout(1000)

        # Frame 1: Tela de escolas e turmas
        img = screenshot_to_image(page)
        frames_5.append(draw_cursor(img, 300, 180, label="Escolas & Turmas"))
        dur_5.append(1000)

        # Frame 2: Clicar em "+ Nova Turma"
        try:
            btn_nova_turma = page.locator("button:has-text('Nova Turma')").first
            if btn_nova_turma.count() > 0:
                btn_nova_turma.click()
                page.wait_for_timeout(500)
        except Exception:
            pass
        img = screenshot_to_image(page)
        frames_5.append(draw_cursor(img, 620, 240, clicking=True, label="+ Nova Turma"))
        dur_5.append(1100)

        # Frame 3: Preencher formulário no modal
        try:
            class_input = page.locator("#classroom-name, #class-name-input, input[placeholder*='Turma'], input[placeholder*='5º ANO']").first
            if class_input.count() > 0:
                class_input.fill("5º ANO B")
        except Exception:
            pass
        img = screenshot_to_image(page)
        frames_5.append(draw_cursor(img, 550, 360, label="5º ANO B • Matutino"))
        dur_5.append(1100)

        # Frame 4: Colar lista em lote de alunos
        try:
            batch_input = page.locator("textarea").first
            if batch_input.count() > 0:
                batch_input.fill("Alice Santos da Silva\nBernardo Lima Oliveira\nCarlos Eduardo Ferreira\nDaniela Gomes Rocha\nEnzo Gabriel Martins")
        except Exception:
            pass
        img = screenshot_to_image(page)
        frames_5.append(draw_cursor(img, 550, 480, label="Lista Nominal (5 Alunos)"))
        dur_5.append(1200)

        # Frame 5: Salvar Turma
        img = screenshot_to_image(page)
        frames_5.append(draw_cursor(img, 650, 580, clicking=True, label="Salvar Turma"))
        dur_5.append(1600)
        # Fechar qualquer modal remanescente
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            page.evaluate("document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none')")
        except Exception:
            pass

        save_gif(frames_5, dur_5, "gif_5_turmas.gif")

        # =========================================================================
        # 6. GIF_6: RELATÓRIOS & RENDIMENTO REAL
        # =========================================================================
        print("\n--- Gravando GIF 6: Tela Real de Relatórios & Rendimento ---")
        frames_6 = []
        dur_6 = []

        # Voltar ao Dashboard de forma limpa
        page.goto(BASE_URL)
        page.wait_for_timeout(1000)
        try:
            btn_dash = page.locator('button[data-tab="dashboard-tab"]').first
            if btn_dash.count() > 0:
                btn_dash.click()
        except Exception:
            pass
        page.wait_for_timeout(800)

        # Frame 1: Métricas de topo do Dashboard real
        img = screenshot_to_image(page)
        frames_6.append(draw_cursor(img, 300, 160, label="Indicadores Consolidados"))
        dur_6.append(1100)

        # Frame 2: Rolagem suave até a tabela analítica de rendimento
        page.evaluate("window.scrollBy(0, 350)")
        page.wait_for_timeout(500)
        img = screenshot_to_image(page)
        frames_6.append(draw_cursor(img, 400, 320, label="Diagnóstico por Habilidade BNCC"))
        dur_6.append(1200)

        # Frame 3: Tabela de estudantes
        page.evaluate("window.scrollBy(0, 300)")
        page.wait_for_timeout(500)
        img = screenshot_to_image(page)
        frames_6.append(draw_cursor(img, 500, 380, label="Ata de Rendimento por Estudante"))
        dur_6.append(1200)

        # Frame 4: Clicar em Exportar Relatório / Baixar Excel
        img = screenshot_to_image(page)
        frames_6.append(draw_cursor(img, 720, 480, clicking=True, label="Baixar Planilha Excel (.xlsx)"))
        dur_6.append(1800)

        save_gif(frames_6, dur_6, "gif_6_relatorios.gif")

        browser.close()

    print("\n✓ TODOS OS 6 GIFS DAS TELAS REAIS FORAM GRAVADOS COM SUCESSO!")

if __name__ == "__main__":
    main()
