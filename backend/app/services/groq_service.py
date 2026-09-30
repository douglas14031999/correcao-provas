import os
import json
import logging
from typing import Optional, Dict, Any, List
import httpx

from app.services.database import get_system_settings

logger = logging.getLogger("uvicorn")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"

def get_configured_groq_api_key() -> str:
    """
    Retorna a chave da API da Groq configurada no sistema.
    Prioridade:
    1. Tabela system_settings (banco de dados)
    2. Variável de ambiente GROQ_API_KEY (.env)
    """
    try:
        settings = get_system_settings()
        key = (settings.get("groq_api_key") or "").strip()
        if key:
            return key
    except Exception as e:
        logger.warning(f"Erro ao buscar chave Groq no banco: {e}")

    return os.environ.get("GROQ_API_KEY", "").strip()

def mask_api_key(key: str) -> str:
    """Mascara a chave da API para exibição segura na interface."""
    if not key:
        return ""
    if len(key) <= 8:
        return "********"
    return f"{key[:4]}...{key[-4:]}"

async def test_groq_api_key(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Testa se uma chave da API da Groq é válida fazendo uma requisição rápida de validação.
    """
    key = (api_key or "").strip() or get_configured_groq_api_key()
    if not key:
        return {
            "success": False,
            "message": "Nenhuma chave da Groq foi informada ou configurada no sistema."
        }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": DEFAULT_GROQ_MODEL,
        "messages": [
            {"role": "user", "content": "Responda apenas: OK"}
        ],
        "max_tokens": 5,
        "temperature": 0.1
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                return {
                    "success": True,
                    "message": f"Conexão com a Groq (Llama 3.1 8B) bem-sucedida! Resposta do modelo: '{content}'",
                    "model": DEFAULT_GROQ_MODEL
                }
            elif resp.status_code == 401:
                return {
                    "success": False,
                    "message": "Chave da Groq inválida ou não autorizada (Erro 401)."
                }
            elif resp.status_code == 429:
                return {
                    "success": False,
                    "message": "Limite de requisições da Groq excedido temporariamente (Erro 429 - Rate Limit)."
                }
            else:
                return {
                    "success": False,
                    "message": f"Erro na API da Groq ({resp.status_code}): {resp.text}"
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Falha na comunicação com os servidores da Groq: {str(e)}"
        }

def _get_bncc_skill_details(bncc_code: str) -> Optional[Dict[str, str]]:
    """Busca detalhes oficiais da habilidade BNCC pelo código."""
    if not bncc_code:
        return None
    try:
        from app.api.bncc import _BNCC_ITEMS, _load_bncc_data
        _load_bncc_data()
        clean_code = bncc_code.strip().upper()
        for item in _BNCC_ITEMS:
            if item.get("codigo", "").strip().upper() == clean_code:
                return {
                    "codigo": item.get("codigo", ""),
                    "componente": item.get("componente", ""),
                    "ano": item.get("ano", ""),
                    "unidade_tematica": item.get("unidade_tematica", ""),
                    "objeto_conhecimento": item.get("objeto_conhecimento", ""),
                    "texto": item.get("texto", "")
                }
    except Exception as e:
        logger.warning(f"Erro ao buscar detalhes da BNCC para IA: {e}")
    return None

async def generate_ai_question_groq(
    discipline: str,
    grade_year: str,
    bncc_code: Optional[str] = None,
    difficulty: Optional[str] = "Médio",
    num_alternatives: Optional[int] = 4,
    local_theme: Optional[str] = None,
    custom_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Gera uma questão inédita com alternativas e gabarito utilizando a Groq Cloud (Llama 3.1 8B Instant).
    Retorna dicionário pronto para uso e edição no sistema.
    """
    key = get_configured_groq_api_key()
    if not key:
        raise ValueError(
            "A Chave de API da Groq (Llama 3.1 8B) não está configurada no sistema. "
            "Acesse o menu Configurações ou defina a variável GROQ_API_KEY no arquivo .env."
        )

    # Detalhes da BNCC
    bncc_info = _get_bncc_skill_details(bncc_code) if bncc_code else None
    num_alts = 5 if num_alternatives == 5 else 4
    letters = ["A", "B", "C", "D", "E"][:num_alts]

    # Prompt do Sistema Especialista
    system_prompt = (
        "Você é um especialista sênior em elaboração de itens de avaliação educacional e matrizes de referência "
        "(SAEB, Prova Brasil e BNCC - Base Nacional Comum Curricular do Brasil).\n"
        "Sua missão é gerar UMA questão inédita, com rigor pedagógico impecável, linguagem clara e adequada à faixa etária dos alunos.\n\n"
        "REGRAS DE CONSTRUÇÃO DO ITEM:\n"
        "1. ENUNCIADO: Contextualizado, claro e direto. Se for matemática ou ciências, inclua uma situação-problema cotidiana. Se for língua portuguesa, forneça um texto-base rico ou contexto interpretativo.\n"
        "2. FÓRMULAS E SÍMBOLOS: Use notação limpa e acessível. Se usar LaTeX, use delimitadores simples como $x^2$ ou escreva claramente.\n"
        f"3. ALTERNATIVAS: Exatamente {num_alts} alternativas ({', '.join(letters)}).\n"
        "4. DISTRATORES PLAUSÍVEIS (SAEB): Os distratores (opções incorretas) devem ser erros comuns de raciocínio, não opções absurdas ou fáceis demais. Deve haver apenas UMA resposta correta inequívoca.\n"
        "5. NADA DE TEXTO FORA DO JSON: Você DEVE responder ESTRITAMENTE em formato JSON válido, sem markdown envolvente e sem explicações externas.\n"
    )

    # Construção da Instrução do Usuário
    user_prompt_parts = [
        f"Componente Curricular / Disciplina: {discipline or 'Geral'}",
        f"Ano / Série: {grade_year or 'Ensino Fundamental'}",
        f"Nível de Dificuldade: {difficulty or 'Médio'}",
        f"Número de Alternativas: {num_alts} ({', '.join(letters)})"
    ]

    if bncc_info:
        user_prompt_parts.append(
            f"Habilidade Oficial BNCC: {bncc_info['codigo']} - {bncc_info['texto']} "
            f"(Unidade Temática: {bncc_info.get('unidade_tematica', '')}, Objeto de Conhecimento: {bncc_info.get('objeto_conhecimento', '')})"
        )
    elif bncc_code:
        user_prompt_parts.append(f"Código BNCC Solicitado: {bncc_code.strip().upper()}")

    if local_theme and local_theme.strip():
        user_prompt_parts.append(
            f"Contextualização / Tema Local Sugerido: {local_theme.strip()} "
            "(Dê preferência a contextos reais, cultura regional de Alagoas/Lagoa da Canoa, patrimônio, natureza ou dia a dia escolar, tornando a questão engajadora e significativa)."
        )

    if custom_prompt and custom_prompt.strip():
        user_prompt_parts.append(f"Instruções Pedagógicas Adicionais do Professor: {custom_prompt.strip()}")

    user_prompt_parts.append(
        "\nRetorne o JSON estritamente com este formato:\n"
        "{\n"
        '  "statement": "Texto completo e claro do enunciado da questão (incluindo o texto-base se houver)",\n'
        '  "bncc_code": "Código da habilidade BNCC trabalhada",\n'
        f'  "correct_answer": "Letra da alternativa correta (uma entre {", ".join(letters)})",\n'
        '  "alternatives": [\n'
        + ",\n".join([f'    {{"letter": "{lt}", "text": "Texto da alternativa {lt}"}}' for lt in letters]) +
        "\n  ],\n"
        '  "explanation": "Breve justificativa pedagógica explicando a resolução e o porquê da alternativa correta."\n'
        "}"
    )

    user_message = "\n".join(user_prompt_parts)

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    request_body = {
        "model": DEFAULT_GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.6,
        "max_tokens": 1500
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GROQ_API_URL, headers=headers, json=request_body)

        if response.status_code == 401:
            raise ValueError("Chave da Groq inválida ou expirada. Verifique as configurações do sistema.")
        elif response.status_code == 429:
            raise ValueError("Limite de requisições da Groq atingido temporariamente. Aguarde alguns instantes e tente novamente.")
        elif response.status_code != 200:
            raise ValueError(f"Erro na Groq API ({response.status_code}): {response.text}")

        data = response.json()
        raw_content = data["choices"][0]["message"]["content"]
        parsed = json.loads(raw_content)

        statement = (parsed.get("statement") or "").strip()
        if not statement:
            raise ValueError("O modelo não gerou um enunciado válido.")

        raw_alts = parsed.get("alternatives") or []
        correct_letter = (parsed.get("correct_answer") or "A").strip().upper()

        clean_alts = []
        for idx, alt in enumerate(raw_alts[:num_alts]):
            let = alt.get("letter", letters[idx] if idx < len(letters) else f"Alt {idx+1}").strip().upper()
            txt = (alt.get("text") or "").strip()
            is_corr = (let == correct_letter)
            clean_alts.append({
                "letter": let,
                "text": txt,
                "is_correct": is_corr,
                "order_index": idx
            })

        # Garante que ao menos uma esteja marcada como correta
        if not any(a["is_correct"] for a in clean_alts) and clean_alts:
            clean_alts[0]["is_correct"] = True
            correct_letter = clean_alts[0]["letter"]

        return {
            "statement": statement,
            "discipline": discipline,
            "grade_year": grade_year,
            "bncc_code": (parsed.get("bncc_code") or bncc_code or "").strip().upper(),
            "difficulty": difficulty,
            "correct_answer": correct_letter,
            "alternatives": clean_alts,
            "explanation": (parsed.get("explanation") or "").strip(),
            "model_used": DEFAULT_GROQ_MODEL
        }

    except json.JSONDecodeError as jde:
        logger.error(f"Erro ao decodificar JSON da Groq: {jde}")
        raise ValueError("A IA respondeu em formato inválido. Tente gerar novamente.")
    except httpx.TimeoutException:
        raise ValueError("Tempo limite esgotado ao conectar com a Groq. Verifique sua conexão à internet.")
    except Exception as e:
        logger.error(f"Erro inesperado ao gerar questão na Groq: {e}")
        raise
