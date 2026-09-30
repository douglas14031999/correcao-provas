"""
Script para publicação de Release oficial no GitHub
Cria o Release v1.0.0 com changelog estruturado e notas de lançamento.
"""

import sys
import os
import json
import subprocess
import urllib.request
import urllib.error

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_github_token():
    # 1. Tentar ler do git credential helper
    try:
        p = subprocess.Popen(
            ['git', 'credential', 'fill'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        out, _ = p.communicate('protocol=https\nhost=github.com\n')
        for line in out.splitlines():
            if line.startswith('password='):
                return line.split('password=', 1)[1].strip()
    except Exception as e:
        print(f"Aviso ao consultar git credential: {e}")

    # 2. Tentar variável de ambiente
    return os.environ.get('GITHUB_TOKEN')

def create_release():
    token = get_github_token()
    if not token:
        print("✗ Erro: Não foi possível obter o token de autenticação do GitHub.")
        return False

    url = "https://api.github.com/repos/douglas14031999/correcao-provas/releases"

    release_body = """# Prova Canoa v1.0.0 — Versão Oficial Homologada 🚀
**Secretaria Municipal de Educação (SEMED) • Lagoa da Canoa / AL**

Temos a satisfação de anunciar a **primeira versão oficial (v1.0.0)** da plataforma **Prova Canoa**, solução completa de correção inteligente de avaliações, leitor óptico por Visão Computacional (OMR) e diagnóstico pedagógico alinhado à BNCC.

---

### ✨ Destaques & Funcionalidades da Versão 1.0.0

#### 1. 📷 Scanner OMR de Alta Precisão (Visão Computacional)
- **Auto-Alinhamento ArUco:** Correção automática de perspectiva e enquadramento utilizando 4 marcadores fiduciais nos vértices da folha.
- **Leitura em < 1 segundo:** Identificação das bolhas marcadas e atribuição imediata da pontuação.
- **Suporte a Celulares (HTTPS):** Acesso móvel seguro com suporte nativo à câmera traseira em smartphones de professores e aplicadores.
- **Detecção Anti-Fraude & Anulação Dupla:** Anulação transparente em caso de múltiplas respostas na mesma questão.

#### 2. 📝 Criador de Provas & Capas Homologadas (Nova Prova)
- **Padrão Gráfico Oficial:** 8 paletas temáticas da identidade visual municipal e 5 opções de capa integrada.
- **Atalhos Rápidos de Série & Questões:** Botões para 2º, 5º e 9º Ano, além de pílulas rápidas para 10, 15, 20 e 25 itens.
- **Impressão Milimétrica (100%):** Geração de PDFs em alta resolução calibrados para papel comum A4 75g.

#### 3. 📚 Elaborador Pedagógico BNCC (`/provas` e `/elaborador`)
- **Catálogo Curricular Completo:** Filtros por disciplina (Língua Portuguesa, Matemática, etc.) e ano de escolaridade.
- **Busca por Código BNCC:** Pesquisa de habilidades (ex: `EF05MA08`) e objetos de conhecimento.
- **Montagem de Cadernos:** Diagramação em duas colunas com capa e folha de respostas anexada.

#### 4. 👥 Gestão de Escolas, Turmas e Estudantes
- **Enturmação em Lote:** Importação de listas de chamada inteiras via copiar e colar de planilhas.
- **Classificação por Turnos:** Separação entre turmas matutinas, vespertinas e integrais.

#### 5. 📊 Relatórios Pedagógicos & Rendimento da Rede
- **Matriz de Habilidades:** Diagnóstico visual por faixas de domínio (Consolidado, Em Desenvolvimento, Crítico).
- **Atas de Resultados:** Notas nominais e mapas de acertos/erros para análise de distratores.
- **Exportação em Excel (.xlsx):** Planilhas formatadas prontas para conselhos de classe e reuniões pedagógicas.

#### 6. 💾 Governança, Segurança & Backup
- **Autenticação Segura JWT:** Controle granular por papéis (Administrador SEMED, Coordenador, Professor).
- **Backup Completo em .ZIP:** Exportação e restauração total de dados e históricos.
- **Operação Offline (PWA):** Funcionamento garantido em escolas sem internet graças ao Service Worker local.

#### 7. 📖 Manual do Usuário Integrado (`/manual`)
- **Passo a Passo Visual Detalhado:** Instruções operacionais para todos os módulos.
- **GIFs Animados das Telas Reais:** Demonstrações animadas gravadas diretamente na interface real do sistema.
- **Visualizador Lightbox:** Clique para ampliar imagens e animações em tela cheia.

---

### 🛠️ Inicialização Rápida

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Iniciar servidores HTTP e HTTPS
python backend/run_server.py
```
- Acesso Web Local: `http://localhost:8080`
- Câmera Mobile Segura: `https://SEU_IP:8443`
- Manual do Sistema: `http://localhost:8080/static/manual.html`

---
*Homologado pela equipe técnica e pedagógica • Lagoa da Canoa / AL • 2026*
"""

    payload = {
        "tag_name": "v1.0.0",
        "target_commitish": "main",
        "name": "Prova Canoa v1.0.0 — Versão Oficial Homologada (SEMED)",
        "body": release_body.strip(),
        "draft": False,
        "prerelease": False
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "Antigravity-Release-Publisher"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            html_url = data.get("html_url")
            print("=" * 60)
            print(f"✓ RELEASE CRIADO COM SUCESSO NO GITHUB!")
            print(f"Tag: {data.get('tag_name')}")
            print(f"Título: {data.get('name')}")
            print(f"URL Pública: {html_url}")
            print("=" * 60)
            return True
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"✗ Erro ao criar release no GitHub (HTTP {e.code}): {err_msg}")
        return False
    except Exception as e:
        print(f"✗ Erro de conexão: {e}")
        return False

if __name__ == "__main__":
    success = create_release()
    sys.exit(0 if success else 1)
