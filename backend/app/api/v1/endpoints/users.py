from datetime import datetime
from typing import Literal, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import ROLE_PERMISSIONS, get_password_hash, require_roles
from app.models.user import User

router = APIRouter()
RoleName = Literal["user", "auditor", "admin"]


class AccountCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    institution: Optional[str] = Field(None, max_length=255)
    role: RoleName = "user"


class AccountUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    institution: Optional[str] = Field(None, max_length=255)
    role: Optional[RoleName] = None
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    institution: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/roles")
async def list_roles(_admin: User = Depends(require_roles("admin"))):
    labels = {"user": "Pengguna", "auditor": "Auditor", "admin": "Administrator"}
    return [
        {"name": name, "label": labels[name], "permissions": permissions}
        for name, permissions in ROLE_PERMISSIONS.items()
    ]


@router.get("/", response_model=list[AccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_in: AccountCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    existing = await db.scalar(select(User).where(User.email == account_in.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    account = User(
        email=account_in.email,
        hashed_password=get_password_hash(account_in.password),
        full_name=account_in.full_name,
        institution=account_in.institution,
        role=account_in.role,
        is_active=True,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: uuid.UUID,
    account_in: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    account = await db.get(User, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    changes = account_in.model_dump(exclude_unset=True)
    if "email" in changes and changes["email"] != account.email:
        if changes["email"] is None:
            raise HTTPException(status_code=422, detail="Email cannot be empty")
        duplicate = await db.scalar(select(User).where(User.email == changes["email"]))
        if duplicate:
            raise HTTPException(status_code=409, detail="Email already registered")
    if account.id == admin.id and (
        changes.get("is_active") is False or changes.get("role", account.role) != "admin"
    ):
        raise HTTPException(status_code=400, detail="You cannot remove your own administrator access")
    if "role" in changes and changes["role"] is None:
        raise HTTPException(status_code=422, detail="Role cannot be empty")
    if "is_active" in changes and changes["is_active"] is None:
        raise HTTPException(status_code=422, detail="Account status cannot be empty")
    new_password = changes.pop("password", None)
    if new_password:
        account.hashed_password = get_password_hash(new_password)
    if account.role == "admin" and (
        changes.get("role", "admin") != "admin" or changes.get("is_active") is False
    ):
        active_admins = await db.scalar(
            select(func.count(User.id)).where(User.role == "admin", User.is_active.is_(True))
        )
        if (active_admins or 0) <= 1:
            raise HTTPException(status_code=400, detail="At least one active administrator must remain")
    for field, value in changes.items():
        setattr(account, field, value)
    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}", response_model=AccountResponse)
async def deactivate_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    account = await db.get(User, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    if account.role == "admin" and account.is_active:
        active_admins = await db.scalar(
            select(func.count(User.id)).where(User.role == "admin", User.is_active.is_(True))
        )
        if (active_admins or 0) <= 1:
            raise HTTPException(status_code=400, detail="At least one active administrator must remain")
    account.is_active = False
    await db.commit()
    await db.refresh(account)
    return account


@router.post("/{account_id}/activate", response_model=AccountResponse)
async def activate_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    account = await db.get(User, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account.is_active = True
    await db.commit()
    await db.refresh(account)
    return account
