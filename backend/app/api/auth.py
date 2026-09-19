import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header, Depends

from app.services.database import (
    get_system_settings,
    update_system_settings,
    get_user_by_username,
    get_user_by_id,
    update_user_last_login
)

router = APIRouter(prefix="/auth", tags=["Autenticação & Segurança"])

SALT = "semed_canoa_salt_2026"
DEFAULT_USER = "admin"
DEFAULT_PASS = "semed2026"

def hash_password(password: str) -> str:
    """Computes SHA-256 hash of password with fixed salt."""
    return hashlib.sha256((password + SALT).encode("utf-8")).hexdigest()

def get_auth_settings():
    settings = get_system_settings()
    stored_user = settings.get("admin_username") or DEFAULT_USER
    stored_hash = settings.get("admin_password_hash")
    if not stored_hash:
        stored_hash = hash_password(DEFAULT_PASS)
        update_system_settings({
            "admin_username": stored_user,
            "admin_password_hash": stored_hash
        })
    return stored_user, stored_hash, settings

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: Optional[bool] = True

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    new_username: Optional[str] = None

def get_authenticated_user(authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)) -> dict:
    token = None
    if isinstance(authorization, str) and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
    elif isinstance(x_auth_token, str) and x_auth_token.strip():
        token = x_auth_token.strip()

    if not token:
        raise HTTPException(status_code=401, detail="Token de autenticação não fornecido.")

    settings = get_system_settings()
    stored_token = settings.get("admin_session_token")
    expires_str = settings.get("admin_session_expires")

    if not stored_token or stored_token != token:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")

    if expires_str:
        try:
            exp_date = datetime.fromisoformat(expires_str)
            if datetime.utcnow() > exp_date:
                raise HTTPException(status_code=401, detail="Sessão expirada. Faça login novamente.")
        except Exception:
            raise HTTPException(status_code=401, detail="Sessão inválida.")

    user_id = settings.get("admin_session_user_id")
    user_info = None
    if user_id:
        user_info = get_user_by_id(user_id)

    if not user_info:
        stored_user, _, _ = get_auth_settings()
        user_info = {
            "id": "admin-default",
            "username": stored_user,
            "name": "Administrador SEMED",
            "role": "admin",
            "email": "educacao@lagoadacanoa.al.gov.br"
        }

    return user_info

def require_roles(allowed_roles: list, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)) -> dict:
    user = get_authenticated_user(authorization, x_auth_token)
    role = user.get("role", "professor")
    if role not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"Acesso negado. Ação restrita a usuários com perfil: {', '.join(allowed_roles)}.")
    return user

def verify_token_from_header(authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)) -> bool:
    try:
        get_authenticated_user(authorization, x_auth_token)
        return True
    except HTTPException:
        return False

@router.post("/login")
def login(req: LoginRequest):
    input_user = (req.username or "").strip().lower()
    input_pass = req.password or ""
    hashed_pass = hash_password(input_pass)

    matched_user = None

    # 1. Search in `users` table
    db_user = get_user_by_username(input_user)
    if db_user:
        if db_user.get("is_active") == 0:
            raise HTTPException(status_code=403, detail="Conta desativada. Solicite liberação junto à Secretaria Municipal de Educação.")
        if db_user.get("password_hash") == hashed_pass or (input_pass == DEFAULT_PASS and db_user.get("password_hash") == hash_password(DEFAULT_PASS)):
            matched_user = db_user
            update_user_last_login(db_user["id"])

    # 2. Fallback to system_settings default admin
    if not matched_user:
        stored_user, stored_hash, _ = get_auth_settings()
        is_user_match = input_user in [stored_user.lower(), "admin", "semed"]
        is_pass_match = (hashed_pass == stored_hash) or (input_pass == DEFAULT_PASS and stored_hash == hash_password(DEFAULT_PASS))
        if is_user_match and is_pass_match:
            matched_user = {
                "id": "admin-default",
                "username": stored_user,
                "name": "Administrador SEMED",
                "role": "admin",
                "email": "educacao@lagoadacanoa.al.gov.br"
            }

    if not matched_user:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")

    # Generate session token
    token = secrets.token_hex(24)
    days = 30 if req.remember_me else 1
    expires_at = datetime.utcnow() + timedelta(days=days)

    update_system_settings({
        "admin_session_token": token,
        "admin_session_expires": expires_at.isoformat(),
        "admin_session_user_id": matched_user["id"]
    })

    return {
        "success": True,
        "token": token,
        "expires_at": expires_at.isoformat(),
        "user": {
            "id": matched_user["id"],
            "username": matched_user["username"],
            "name": matched_user["name"],
            "role": matched_user["role"],
            "email": matched_user.get("email", "")
        }
    }

@router.get("/me")
def get_current_user(authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    is_valid = verify_token_from_header(authorization, x_auth_token)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")

    settings = get_system_settings()
    user_id = settings.get("admin_session_user_id")

    user_info = None
    if user_id:
        user_info = get_user_by_id(user_id)

    if not user_info:
        stored_user, _, _ = get_auth_settings()
        user_info = {
            "id": "admin-default",
            "username": stored_user,
            "name": "Administrador SEMED",
            "role": "admin",
            "email": "educacao@lagoadacanoa.al.gov.br"
        }

    return {
        "authenticated": True,
        "user": {
            "id": user_info["id"],
            "username": user_info["username"],
            "name": user_info["name"],
            "role": user_info["role"],
            "email": user_info.get("email", "")
        },
        "institution": {
            "prefeitura": settings.get("prefeitura_name", "Prefeitura Municipal de Lagoa da Canoa"),
            "secretaria": settings.get("secretaria_name", "Secretaria Municipal de Educação - SEMED"),
            "state": settings.get("state_name", "Estado de Alagoas")
        }
    }

@router.post("/logout")
def logout():
    update_system_settings({
        "admin_session_token": "",
        "admin_session_expires": ""
    })
    return {"success": True, "message": "Sessão encerrada com sucesso."}

@router.post("/change-password")
def change_password(req: ChangePasswordRequest, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    if not verify_token_from_header(authorization, x_auth_token):
        raise HTTPException(status_code=401, detail="Acesso não autorizado.")

    stored_user, stored_hash, _ = get_auth_settings()
    if hash_password(req.current_password) != stored_hash:
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")

    if not req.new_password or len(req.new_password.strip()) < 4:
        raise HTTPException(status_code=400, detail="A nova senha deve ter pelo menos 4 caracteres.")

    updates = {
        "admin_password_hash": hash_password(req.new_password.strip())
    }
    if req.new_username and len(req.new_username.strip()) >= 3:
        updates["admin_username"] = req.new_username.strip()

    update_system_settings(updates)
    return {"success": True, "message": "Credenciais atualizadas com sucesso."}
