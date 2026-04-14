from datetime import timedelta
from typing import Any
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import security
from app.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate
from app.schemas.token import Token

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation failed",
                "fields": {"email": "already registered"},
            },
        )

    if not user_in.name or not user_in.name.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation failed",
                "fields": {"name": "is required"},
            },
        )

    new_user = User(
        name=user_in.name.strip(),
        email=user_in.email,
        password=security.get_password_hash(user_in.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Return token + user per the spec
    access_token = security.create_access_token(
        subject=str(new_user.id),
        extra_claims={"email": new_user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "token": access_token,
        "user": {
            "id": str(new_user.id),
            "name": new_user.name,
            "email": new_user.email,
        },
    }


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> Any:
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not security.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized"},
        )

    access_token = security.create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "token": access_token,
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
        },
    }
