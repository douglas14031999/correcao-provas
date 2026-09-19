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
    try:
        sync_pwa_icons(target_path)
    except Exception as e:
        print(f"[PWA Icon Sync] Erro ao sincronizar ícones estáticos: {e}")

    return {
        "status": "success",
        "message": "Brasão municipal atualizado com sucesso!",
        "logo_url": "/api/settings/logo"
    }

from fastapi.responses import FileResponse, Response
from PIL import Image
import io

def sync_pwa_icons(logo_path: Optional[str] = None):
    """Gera os arquivos estáticos frontend/pwa-icon-192.png e frontend/pwa-icon-512.png."""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
    if not os.path.exists(frontend_dir):
        return

    if not logo_path or not os.path.exists(logo_path):
        settings = get_system_settings()
        logo_path = settings.get("logo_path", "")
        if not logo_path or not os.path.exists(logo_path):
            default_asset = os.path.join(STORAGE_DIR, "assets", "logo_lagoa_da_canoa.png")
            if os.path.exists(default_asset):
                logo_path = default_asset

    if not logo_path or not os.path.exists(logo_path):
        return

    with Image.open(logo_path) as img:
        img = img.convert("RGBA")
        for size in [192, 512]:
            canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
            padding = int(size * 0.10)
            fit_w = size - (padding * 2)
            fit_h = size - (padding * 2)
            thumb = img.copy()
            thumb.thumbnail((fit_w, fit_h), Image.Resampling.LANCZOS)
            paste_x = (size - thumb.width) // 2
            paste_y = (size - thumb.height) // 2
            canvas.paste(thumb, (paste_x, paste_y), thumb)
            target = os.path.join(frontend_dir, f"pwa-icon-{size}.png")
            canvas.save(target, format="PNG", optimize=True)



@router.get("/logo")
def get_logo():
    settings = get_system_settings()
    logo_path = settings.get("logo_path", "")
    if logo_path and os.path.exists(logo_path):
        return FileResponse(logo_path)
    raise HTTPException(status_code=404, detail="Nenhum brasão cadastrado.")

@router.get("/pwa-icon")
def get_pwa_icon(size: int = 192):
    """
    Retorna o logo cadastrado na plataforma formatado e quadrado para ícone de PWA (192x192, 512x512).
    """
    settings = get_system_settings()
    logo_path = settings.get("logo_path", "")

    # Fallback para logo padrão da prefeitura em assets se não configurado
    if not logo_path or not os.path.exists(logo_path):
        default_asset = os.path.join(STORAGE_DIR, "assets", "logo_lagoa_da_canoa.png")
        if os.path.exists(default_asset):
            logo_path = default_asset

    target_size = min(max(size, 48), 1024)

    if logo_path and os.path.exists(logo_path):
        try:
            with Image.open(logo_path) as img:
                img = img.convert("RGBA")
                # Fundo branco suave com cantos limpos
                canvas = Image.new("RGBA", (target_size, target_size), (255, 255, 255, 255))
                
                # Margem/Padding de 10% para não cortar bordas em ícones maskable
                padding = int(target_size * 0.10)
                fit_w = target_size - (padding * 2)
                fit_h = target_size - (padding * 2)

                img.thumbnail((fit_w, fit_h), Image.Resampling.LANCZOS)
                paste_x = (target_size - img.width) // 2
                paste_y = (target_size - img.height) // 2
                canvas.paste(img, (paste_x, paste_y), img)

                buf = io.BytesIO()
                canvas.save(buf, format="PNG", optimize=True)
                return Response(
                    content=buf.getvalue(),
                    media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"}
                )
        except Exception as e:
            print(f"[PWA Icon] Erro ao renderizar ícone: {e}")

    # Fallback elegante caso a imagem não possa ser aberta
    canvas = Image.new("RGBA", (target_size, target_size), (36, 64, 97, 255))
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return Response(
        content=buf.getvalue(),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}
    )
