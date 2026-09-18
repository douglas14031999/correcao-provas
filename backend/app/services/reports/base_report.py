import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class ReportMetadata:
    prefeitura: str = "Prefeitura Municipal de Lagoa da Canoa"
    secretaria: str = "Secretaria Municipal de Educação - SEMED"
    state: str = "Estado de Alagoas"
    school_name: str = ""
    inep_code: str = ""
    classroom_name: str = ""
    grade_year: str = ""
    shift: str = ""
    exam_title: str = ""
    teacher_name: str = ""
    school_year: str = ""
    issue_date: str = field(default_factory=lambda: datetime.now().strftime("%d/%m/%Y às %H:%M"))
    logo_path: Optional[str] = None

@dataclass
class ReportTableColumn:
    key: str
    header: str
    width_ratio: float = 1.0  # Relative width weight
    align: str = "left"       # 'left', 'center', 'right'
    is_numeric: bool = False
    format_type: Optional[str] = None # 'decimal', 'percent', 'integer', 'status', 'badge'

@dataclass
class ReportData:
    title: str
    metadata: ReportMetadata
    columns: List[ReportTableColumn]
    rows: List[Dict[str, Any]]
    subtitle: str = ""
    summary_cards: List[Dict[str, Any]] = field(default_factory=list)
    signatures: List[str] = field(default_factory=lambda: [
        "Professor(a) / Aplicador(a)",
        "Coordenação Pedagógica / Direção"
    ])
    notes: List[str] = field(default_factory=list)
