import os
import shutil
from typing import Optional, Dict
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from fastapi.responses import FileResponse

from app.services.database import get_system_settings, update_system_settings
from app.api.auth import require_roles

router = APIRouter(prefix="/settings", tags=["Configurações Institucionais"])

class SettingsUpdateRequest(BaseModel):
    prefeitura_name: Optional[str] = None
    secretaria_name: Optional[str] = None
    state_name: Optional[str] = None

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage")

@router.get("")
def get_settings():
    settings = get_system_settings()
    logo_path = settings.get("logo_path", "")
    has_logo = bool(logo_path and os.path.exists(logo_path))
    return {
        "prefeitura_name": settings.get("prefeitura_name", "Prefeitura Municipal de Lagoa da Canoa"),
        "secretaria_name": settings.get("secretaria_name", "Secretaria Municipal de Educação - SEMED"),
        "state_name": settings.get("state_name", "Estado de Alagoas"),
        "has_logo": has_logo,
        "logo_url": "/api/settings/logo" if has_logo else None
    }

@router.post("")
def save_settings(req: SettingsUpdateRequest, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin", "coordenador"], authorization, x_auth_token)
    updates = {}
    if req.prefeitura_name is not None:
        updates["prefeitura_name"] = req.prefeitura_name.strip()
    if req.secretaria_name is not None:
        updates["secretaria_name"] = req.secretaria_name.strip()
    if req.state_name is not None:
        updates["state_name"] = req.state_name.strip()

    updated = update_system_settings(updates)
    return {
        "status": "success",
        "settings": updated
    }

@router.post("/logo")
async def upload_logo(file: UploadFile = File(...), authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin", "coordenador"], authorization, x_auth_token)
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo enviado deve ser uma imagem (PNG ou JPG).")

    os.makedirs(STORAGE_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1] or ".png"
    target_path = os.path.join(STORAGE_DIR, f"logo_municipal{ext}")

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    update_system_settings({"logo_path": target_path})

    return {
        "status": "success",
        "message": "Brasão municipal atualizado com sucesso!",
        "logo_url": "/api/settings/logo"
    }

@router.get("/logo")
def get_logo():
    settings = get_system_settings()
    logo_path = settings.get("logo_path", "")
    if logo_path and os.path.exists(logo_path):
        return FileResponse(logo_path)
    raise HTTPException(status_code=404, detail="Nenhum brasão cadastrado.")
