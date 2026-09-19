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

    # Contar mídias institucionais e provas
    media_counts = {"assets": 0, "overlays": 0, "scans": 0}

    now_iso = datetime.utcnow().isoformat()
    manifest = {
        "version": "1.0.0",
        "app_title": "OMR Provas & Simulados - SEMED Lagoa da Canoa",
        "created_at": now_iso,
        "database_type": "postgresql" if is_postgres() else "sqlite",
        "table_counts": counts,
        "total_records": sum(counts.values()),
        "media_counts": media_counts
    }

    # Gerar arquivo ZIP em memória
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Arquivo do banco de dados em JSON
        zf.writestr(
            "database.json",
            json.dumps(database_dump, ensure_ascii=False, indent=2)
        )

        # 2. Arquivos de armazenamento: assets, brasão, overlays (Raio-X) e scans originais
        media_folders = ["assets", "overlays", "scans"]
        for folder in media_folders:
            folder_path = os.path.join(STORAGE_DIR, folder)
            if os.path.exists(folder_path):
                for root, _, files in os.walk(folder_path):
                    for f in files:
                        full_p = os.path.join(root, f)
                        rel_p = os.path.relpath(full_p, STORAGE_DIR)
                        zf.write(full_p, arcname=os.path.join("storage", rel_p))
                        media_counts[folder] = media_counts.get(folder, 0) + 1

        # Brasão oficial na raiz de storage se existir
        logo_muni = os.path.join(STORAGE_DIR, "logo_municipal.jpg")
        if os.path.exists(logo_muni):
            zf.write(logo_muni, arcname="storage/logo_municipal.jpg")
            media_counts["assets"] = media_counts.get("assets", 0) + 1

        # 3. Manifesto com informações consolidadas
        manifest["media_counts"] = media_counts
        manifest["total_media_files"] = sum(media_counts.values())
        zf.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2)
        )

    zip_bytes = zip_buffer.getvalue()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_omr_canoa_{timestamp_str}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Backup-Records": str(manifest["total_records"]),
            "X-Backup-Media": str(manifest["total_media_files"])
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

    def rebase_storage_path(val: Any) -> Any:
        if not val or not isinstance(val, str):
            return val
        norm_val = val.replace("\\", "/")
        if "storage/" in norm_val:
            sub_rel = norm_val.split("storage/", 1)[1]
            return os.path.join(STORAGE_DIR, sub_rel.replace("/", os.sep))
        return val

    try:
        # Desativar chaves estrangeiras temporariamente se SQLite para limpeza sem conflitos
        if not is_postgres():
            try:
                cursor.execute("PRAGMA foreign_keys = OFF;")
            except Exception:
                pass

        # 1. Limpeza em cascata respeitando Foreign Keys
        for tbl in TABLE_ORDER_CLEAR:
            try:
                cursor.execute(f"DELETE FROM {tbl}")
            except Exception as e:
                print(f"[Backup] Aviso ao limpar tabela {tbl}: {e}")

        # Obter colunas reais existentes na tabela de destino
        def get_table_columns(table_name: str) -> set:
            if is_postgres():
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = %s
                """, (table_name,))
                return {row[0].lower() for row in cursor.fetchall()}
            else:
                cursor.execute(f"PRAGMA table_info({table_name})")
                return {row["name"].lower() for row in cursor.fetchall()}

        # 2. Inserção dos registros por tabela
        for tbl in TABLE_ORDER_RESTORE:
            records = database_dump.get(tbl, [])
            count = 0
            if records:
                db_cols = get_table_columns(tbl)
                if not db_cols:
                    continue

                for r in records:
                    # Mapeamento de compatibilidade de campos legados
                    if tbl == "exams":
                        if "primary_color" in r and ("header_color" not in r or not r["header_color"]):
                            r["header_color"] = r["primary_color"]
                        elif "header_color" in r and ("primary_color" not in r or not r["primary_color"]):
                            r["primary_color"] = r["header_color"]

                        if "logo_path" in r:
                            r["logo_path"] = rebase_storage_path(r["logo_path"])

                    elif tbl == "system_settings" and r.get("key") == "logo_path":
                        r["value"] = rebase_storage_path(r.get("value"))

                    # Filtrar apenas colunas que realmente existem na tabela de destino
                    valid_cols = [c for c in r.keys() if c.lower() in db_cols]
                    if not valid_cols:
                        continue

                    col_names = ", ".join(valid_cols)
                    placeholders = ", ".join(["?"] * len(valid_cols))
                    sql = f"INSERT INTO {tbl} ({col_names}) VALUES ({placeholders})"
                    values = [r.get(c) for c in valid_cols]
                    cursor.execute(sql, values)
                    count += 1

            restored_stats[tbl] = count

        # Reativar chaves estrangeiras se SQLite
        if not is_postgres():
            try:
                cursor.execute("PRAGMA foreign_keys = ON;")
            except Exception:
                pass

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

@router.post("/system-update")
def execute_system_update(
    authorization: Optional[str] = Header(None),
    x_auth_token: Optional[str] = Header(None)
):
    """
    Executa a atualização remota do código a partir do GitHub e reinicia o serviço Systemd:
    1. git fetch origin
    2. git reset --hard origin/main
    3. sudo systemctl restart correcao-provas (em background)
    """
    require_roles(["admin"], authorization, x_auth_token)

    import subprocess
    import threading
    import time

    root_dir = os.path.dirname(BACKEND_DIR)
    git_output = []

    try:
        # Executar git fetch origin
        fetch_res = subprocess.run(
            ["git", "-c", "safe.directory=*", "fetch", "origin"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        if fetch_res.stdout:
            git_output.append(fetch_res.stdout.strip())
        if fetch_res.stderr:
            git_output.append(fetch_res.stderr.strip())

        # Executar git reset --hard origin/main
        reset_res = subprocess.run(
            ["git", "-c", "safe.directory=*", "reset", "--hard", "origin/main"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        if reset_res.stdout:
            git_output.append(reset_res.stdout.strip())
        if reset_res.stderr:
            git_output.append(reset_res.stderr.strip())

        if reset_res.returncode != 0:
            err_msg = reset_res.stderr or reset_res.stdout or "Código de retorno diferente de zero"
            raise Exception(f"Erro ao executar git reset: {err_msg}")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao sincronizar com o repositório GitHub: {str(e)}"
        )

    # Agenda reinicialização assíncrona após responder HTTP 200
    def delayed_restart():
        time.sleep(1.5)
        # 1. Tenta reiniciar o serviço Systemd via sudo
        try:
            res = subprocess.run(["sudo", "systemctl", "restart", "correcao-provas"], timeout=15)
            if res.returncode == 0:
                return
        except Exception:
            pass

        # 2. Tenta systemctl direto
        try:
            res = subprocess.run(["systemctl", "restart", "correcao-provas"], timeout=15)
            if res.returncode == 0:
                return
        except Exception:
            pass

        # 3. Fallback: envia SIGTERM para o próprio processo para que o Systemd (Restart=always) recrie
        try:
            os.kill(os.getpid(), 15)
        except Exception:
            pass

    threading.Thread(target=delayed_restart, daemon=True).start()

    return {
        "success": True,
        "message": "Sistema sincronizado com sucesso! Reiniciando serviço correcao-provas em instantes...",
        "output": "\n".join([line for line in git_output if line.strip()])
    }

