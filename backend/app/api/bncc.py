import os
import json
import unicodedata
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/bncc", tags=["BNCC"])

# Caminho para o arquivo de dados da BNCC EF
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "bncc_ef.json")

# Carregamento em memória das habilidades da BNCC
_BNCC_ITEMS: List[Dict[str, Any]] = []

def _normalize_text(text: str) -> str:
    """Remove acentos e converte para minúsculas para busca flexível."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c)).lower()

def _load_bncc_data():
    global _BNCC_ITEMS
    if _BNCC_ITEMS:
        return
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
                for item in raw_items:
                    # Adiciona campo normalizado para pesquisa instantânea
                    search_blob = f"{item.get('codigo', '')} {item.get('componente', '')} {item.get('unidade_tematica', '')} {item.get('texto', '')}"
                    item["_search"] = _normalize_text(search_blob)
                _BNCC_ITEMS = raw_items
        except Exception as e:
            import logging
            logging.getLogger("uvicorn").error(f"Erro ao carregar dados da BNCC: {e}")

_load_bncc_data()

@router.get("/filtros")
def get_bncc_filters():
    """Retorna disciplinas disponíveis e anos do Ensino Fundamental para filtros."""
    _load_bncc_data()
    disciplinas = sorted(list({item.get("componente") for item in _BNCC_ITEMS if item.get("componente")}))
    anos = [
        {"ano": 1, "label": "1º Ano"},
        {"ano": 2, "label": "2º Ano"},
        {"ano": 3, "label": "3º Ano"},
        {"ano": 4, "label": "4º Ano"},
        {"ano": 5, "label": "5º Ano"},
        {"ano": 6, "label": "6º Ano"},
        {"ano": 7, "label": "7º Ano"},
        {"ano": 8, "label": "8º Ano"},
        {"ano": 9, "label": "9º Ano"},
    ]
    return {
        "disciplinas": disciplinas,
        "anos": anos,
        "total_habilidades": len(_BNCC_ITEMS)
    }

@router.get("/habilidades")
def search_bncc_habilidades(
    q: Optional[str] = Query(None, description="Termo de busca (código ou palavra-chave)"),
    disciplina: Optional[str] = Query(None, description="Nome da disciplina (ex: Matemática)"),
    ano: Optional[int] = Query(None, description="Ano escolar (1 a 9)"),
    limit: int = Query(50, ge=1, le=200, description="Quantidade máxima de resultados")
):
    """Busca habilidades da BNCC com filtros por disciplina, ano e texto."""
    _load_bncc_data()
    
    results = _BNCC_ITEMS

    # Filtro por Disciplina (normalizado)
    if disciplina:
        norm_disc = _normalize_text(disciplina)
        results = [
            item for item in results 
            if norm_disc in _normalize_text(item.get("componente", ""))
        ]

    # Filtro por Ano Escolar
    if ano:
        results = [
            item for item in results 
            if ano in item.get("anos", [])
        ]

    # Filtro de texto / palavra-chave / código
    if q and q.strip():
        norm_q = _normalize_text(q.strip())
        results = [
            item for item in results 
            if norm_q in item.get("_search", "")
        ]

    # Remove campo interno de busca da resposta
    sanitized = []
    for item in results[:limit]:
        entry = {k: v for k, v in item.items() if k != "_search"}
        sanitized.append(entry)

    return {
        "total": len(results),
        "returned": len(sanitized),
        "habilidades": sanitized
    }
