import os
import io
import json
import zipfile
import shutil
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Header, HTTPException, UploadFile, File
from fastapi.responses import Response

from app.api.auth import require_roles
from app.services.database import get_connection, is_postgres

router = APIRouter(prefix="/backup", tags=["Backup e Restauração"])

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORAGE_DIR = os.path.join(BACKEND_DIR, "storage")
ASSETS_DIR = os.path.join(STORAGE_DIR, "assets")

TABLE_ORDER_CLEAR = [
    "submissions",
    "classroom_exams",
    "students",
    "classrooms",
    "schools",
    "exams",
    "users",
    "system_settings"
]

TABLE_ORDER_RESTORE = [
    "system_settings",
    "users",
    "schools",
    "classrooms",
    "students",
    "exams",
    "classroom_exams",
    "submissions"
]

@router.get("/stats")
def get_backup_stats(
    authorization: Optional[str] = Header(None),
    x_auth_token: Optional[str] = Header(None)
):
    """Retorna estatísticas detalhadas de registros no banco para exibição na tela de Backup."""
    require_roles(["admin"], authorization, x_auth_token)
    conn = get_connection()
    cursor = conn.cursor()

    stats = {}
    for tbl in TABLE_ORDER_RESTORE:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
            r = cursor.fetchone()
            stats[tbl] = r[0] if r else 0
        except Exception:
            stats[tbl] = 0

    conn.close()
    return {
        "schools": stats.get("schools", 0),
        "classrooms": stats.get("classrooms", 0),
        "students": stats.get("students", 0),
        "exams": stats.get("exams", 0),
        "submissions": stats.get("submissions", 0),
        "users": stats.get("users", 0),
        "system_settings": stats.get("system_settings", 0)
    }

@router.get("/export")
def export_backup(
    authorization: Optional[str] = Header(None),
    x_auth_token: Optional[str] = Header(None)
):
    """Exporta todo o banco de dados e arquivos de mídia/brasão em um arquivo ZIP seguro."""
    require_roles(["admin"], authorization, x_auth_token)

    conn = get_connection()
    cursor = conn.cursor()

    database_dump: Dict[str, Any] = {}
    counts: Dict[str, int] = {}

    for tbl in TABLE_ORDER_RESTORE:
        try:
            cursor.execute(f"SELECT * FROM {tbl}")
            rows = cursor.fetchall()
            database_dump[tbl] = [dict(r) for r in rows]
            counts[tbl] = len(rows)
        except Exception as e:
            database_dump[tbl] = []
            counts[tbl] = 0

    conn.close()

    now_iso = datetime.utcnow().isoformat()
    manifest = {
        "version": "1.0.0",
        "app_title": "OMR Provas & Simulados - SEMED Lagoa da Canoa",
        "created_at": now_iso,
        "database_type": "postgresql" if is_postgres() else "sqlite",
        "table_counts": counts,
        "total_records": sum(counts.values())
    }

    # Gerar arquivo ZIP em memória
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Arquivo do banco de dados em JSON
        zf.writestr(
            "database.json",
            json.dumps(database_dump, ensure_ascii=False, indent=2)
        )

        # 2. Manifesto com informações e hash
        zf.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2)
        )

        # 3. Arquivos de ativos institucionais (brasão, logos municipais)
        if os.path.exists(ASSETS_DIR):
            for root, _, files in os.walk(ASSETS_DIR):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, STORAGE_DIR)
                    zf.write(full_p, arcname=os.path.join("storage", rel_p))

        # Brasão oficial na raiz de storage se existir
        logo_muni = os.path.join(STORAGE_DIR, "logo_municipal.jpg")
        if os.path.exists(logo_muni):
            zf.write(logo_muni, arcname="storage/logo_municipal.jpg")

    zip_bytes = zip_buffer.getvalue()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_omr_canoa_{timestamp_str}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Backup-Records": str(manifest["total_records"])
        }
    )

@router.post("/import")
async def import_backup(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
    x_auth_token: Optional[str] = Header(None)
):
    """Importa um arquivo ZIP de backup com substituição total segura e restaurando integridade referencial."""
    require_roles(["admin"], authorization, x_auth_token)

    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. O arquivo de backup deve ter extensão .zip"
        )

    content = await file.read()
    try:
        zip_buffer = io.BytesIO(content)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            namelist = zf.namelist()
            if "database.json" not in namelist:
                raise HTTPException(
                    status_code=400,
                    detail="Arquivo de backup inválido: 'database.json' não foi encontrado no arquivo ZIP."
                )

            db_json_bytes = zf.read("database.json")
            database_dump = json.loads(db_json_bytes.decode("utf-8"))

            manifest_data = {}
            if "manifest.json" in namelist:
                try:
                    manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                except Exception:
                    pass

            # Extrair ativos institucionais
            for member in namelist:
                if member.startswith("storage/") and not member.endswith("/"):
                    rel_path = member[len("storage/"):]
                    target_path = os.path.join(STORAGE_DIR, rel_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "wb") as out_f:
                        out_f.write(zf.read(member))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao processar o arquivo de backup: {str(e)}"
        )

    # Iniciar Restauração no Banco de Dados
    conn = get_connection()
    cursor = conn.cursor()

    restored_stats = {}

    try:
        # 1. Limpeza em cascata respeitando Foreign Keys
        for tbl in TABLE_ORDER_CLEAR:
            try:
                cursor.execute(f"DELETE FROM {tbl}")
            except Exception as e:
                print(f"[Backup] Aviso ao limpar tabela {tbl}: {e}")

        # 2. Inserção dos registros por tabela
        for tbl in TABLE_ORDER_RESTORE:
            records = database_dump.get(tbl, [])
            count = 0
            if records:
                # Obter colunas a partir do primeiro registro
                first_rec = records[0]
                cols = list(first_rec.keys())
                col_names = ", ".join(cols)
                placeholders = ", ".join(["?"] * len(cols))

                sql = f"INSERT INTO {tbl} ({col_names}) VALUES ({placeholders})"
                for r in records:
                    values = [r.get(c) for c in cols]
                    cursor.execute(sql, values)
                    count += 1

            restored_stats[tbl] = count

        # 3. Salvaguarda de Segurança: garantir que existe pelo menos 1 administrador ativo
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1")
        active_admin_row = cursor.fetchone()
        active_admin_count = active_admin_row[0] if active_admin_row else 0

        if active_admin_count == 0:
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
            restored_stats["users"] = restored_stats.get("users", 0) + 1

        conn.commit()

    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao restaurar banco de dados: {str(e)}"
        )

    conn.close()

    total_restored = sum(restored_stats.values())
    return {
        "success": True,
        "message": f"Backup restaurado com sucesso! Total de {total_restored} registros restaurados.",
        "stats": restored_stats,
        "manifest": manifest_data
    }
