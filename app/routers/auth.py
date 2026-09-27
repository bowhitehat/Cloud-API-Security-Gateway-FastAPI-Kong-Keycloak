import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])
security_logger = logging.getLogger("api.security")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if payload.role not in {"user", "admin"}:
        raise HTTPException(status_code=400, detail="Role must be user or admin")

    existed_user = db.query(User).filter(User.username == payload.username).first()
    if existed_user:
        raise HTTPException(status_code=409, detail="Username already exists")

    user = User(
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    security_logger.info(
        "user_registered",
        extra={"event": "user_registered", "username": user.username},
    )
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        security_logger.warning(
            "login_failed",
            extra={"event": "login_failed", "username": form_data.username},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.username,
        extra_claims={"role": user.role, "user_id": user.id},
    )
    security_logger.info(
        "login_success",
        extra={"event": "login_success", "username": user.username},
    )
    return Token(access_token=access_token)
