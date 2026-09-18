import hashlib
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, HTTPException, Header, Depends

from app.services.database import (
    get_all_users,
    get_user_by_id,
    get_user_by_username,
    create_user,
    update_user,
    delete_user,
    count_active_admins
)
from app.api.auth import require_roles, SALT

router = APIRouter(prefix="/users", tags=["Gestão de Usuários"])

def hash_password(password: str) -> str:
    return hashlib.sha256((password + SALT).encode("utf-8")).hexdigest()

class UserCreateRequest(BaseModel):
    name: str
    username: str
    email: Optional[str] = ""
    role: str = "professor" # "admin", "coordenador", "professor"
    password: str
    is_active: Optional[bool] = True

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    new_password: Optional[str] = None

class UserStatusRequest(BaseModel):
    is_active: bool

@router.get("")
def list_users(authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin", "coordenador"], authorization, x_auth_token)
    return get_all_users()

@router.post("")
def add_user(req: UserCreateRequest, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin", "coordenador"], authorization, x_auth_token)

    clean_user = req.username.strip().lower()
    if len(clean_user) < 3:
        raise HTTPException(status_code=400, detail="O nome de usuário deve ter pelo menos 3 caracteres.")
    
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="O nome completo é obrigatório.")

    if not req.password or len(req.password) < 4:
        raise HTTPException(status_code=400, detail="A senha deve ter no mínimo 4 caracteres.")

    valid_roles = ["admin", "coordenador", "professor"]
    clean_role = req.role.strip().lower()
    if clean_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Perfil inválido. Opções: {', '.join(valid_roles)}")

    existing = get_user_by_username(clean_user)
    if existing:
        raise HTTPException(status_code=400, detail=f"O usuário '{clean_user}' já está cadastrado no sistema.")

    pwd_hash = hash_password(req.password)
    user = create_user(
        name=req.name,
        username=clean_user,
        email=req.email or "",
        role=clean_role,
        password_hash=pwd_hash,
        is_active=1 if req.is_active else 0
    )
    return {"success": True, "message": "Usuário cadastrado com sucesso!", "user": user}

@router.put("/{user_id}")
def edit_user(user_id: str, req: UserUpdateRequest, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin", "coordenador"], authorization, x_auth_token)

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    updates = {}
    if req.name is not None and req.name.strip():
        updates["name"] = req.name.strip()
    if req.email is not None:
        updates["email"] = req.email.strip()
    if req.role is not None:
        valid_roles = ["admin", "coordenador", "professor"]
        clean_role = req.role.strip().lower()
        if clean_role not in valid_roles:
            raise HTTPException(status_code=400, detail="Perfil de acesso inválido.")
        # If demoting this user from admin, ensure at least one other active admin remains
        if user["role"] == "admin" and clean_role != "admin" and count_active_admins() <= 1:
            raise HTTPException(status_code=400, detail="Não é possível alterar o perfil do único administrador ativo da rede.")
        updates["role"] = clean_role
    if req.is_active is not None:
        new_active = 1 if req.is_active else 0
        if user["role"] == "admin" and new_active == 0 and count_active_admins() <= 1:
            raise HTTPException(status_code=400, detail="Não é possível desativar o único administrador do sistema.")
        updates["is_active"] = new_active
    if req.new_password and len(req.new_password.strip()) >= 4:
        updates["password_hash"] = hash_password(req.new_password.strip())

    updated = update_user(user_id, updates)
    return {"success": True, "message": "Dados do usuário atualizados com sucesso!", "user": updated}

@router.patch("/{user_id}/status")
def toggle_status(user_id: str, req: UserStatusRequest, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin", "coordenador"], authorization, x_auth_token)

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    new_active = 1 if req.is_active else 0
    if user["role"] == "admin" and new_active == 0 and count_active_admins() <= 1:
        raise HTTPException(status_code=400, detail="Não é possível desativar o único administrador do sistema.")

    update_user(user_id, {"is_active": new_active})
    return {"success": True, "message": "Status atualizado com sucesso!"}

@router.delete("/{user_id}")
def remove_user(user_id: str, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin"], authorization, x_auth_token)

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if user["role"] == "admin" and count_active_admins() <= 1:
        raise HTTPException(status_code=400, detail="Operação negada: não é permitido excluir o único administrador ativo do sistema.")

    success = delete_user(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao excluir usuário.")

    return {"success": True, "message": f"Usuário '{user['username']}' excluído com sucesso."}
