from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field
from datetime import timedelta, datetime
import uuid
from jose import jwt, JWTError

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    settings,
)
from app.models.user import User

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=255)
    institution: str | None = Field(None, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ProfileUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(None, max_length=255)
    institution: str | None = Field(None, max_length=255)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PreferencesRequest(BaseModel):
    preferences: dict


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    institution: str | None
    is_active: bool
    created_at: datetime | None = None
    last_login: datetime | None = None
    
    class Config:
        from_attributes = True


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role="user",
        institution=user_in.institution,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    user.last_login = datetime.utcnow()
    await db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_active_user),
):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/profile", response_model=UserResponse)
async def read_profile(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    profile_in: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    changes = profile_in.model_dump(exclude_unset=True)
    if "email" in changes and changes["email"] is None:
        raise HTTPException(status_code=422, detail="Email cannot be empty")
    if "email" in changes and changes["email"] != current_user.email:
        existing = await db.scalar(select(User).where(User.email == changes["email"]))
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
    for field, value in changes.items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.put("/password")
async def change_password(
    request: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = get_password_hash(request.new_password)
    await db.commit()
    return {"message": "Password updated successfully"}


@router.get("/preferences")
async def get_preferences(current_user: User = Depends(get_current_active_user)):
    return {"preferences": (current_user.meta_data or {}).get("preferences", {})}


@router.put("/preferences")
async def save_preferences(
    request: PreferencesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    meta_data = dict(current_user.meta_data or {})
    meta_data["preferences"] = request.preferences
    current_user.meta_data = meta_data
    await db.commit()
    return {"preferences": request.preferences}


@router.delete("/preferences")
async def reset_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    meta_data = dict(current_user.meta_data or {})
    meta_data.pop("preferences", None)
    current_user.meta_data = meta_data or None
    await db.commit()
    return {"preferences": {}}


@router.delete("/preferences/{preference_key}")
async def delete_preference(
    preference_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    meta_data = dict(current_user.meta_data or {})
    preferences = dict(meta_data.get("preferences", {}))
    preferences.pop(preference_key, None)
    if preferences:
        meta_data["preferences"] = preferences
    else:
        meta_data.pop("preferences", None)
    current_user.meta_data = meta_data or None
    await db.commit()
    return {"preferences": preferences}
