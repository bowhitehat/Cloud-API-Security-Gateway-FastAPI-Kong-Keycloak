from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# Cấu hình Swagger UI tích hợp với Keycloak OIDC
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="http://localhost:8081/realms/capstone/protocol/openid-connect/auth",
    tokenUrl="http://localhost:8081/realms/capstone/protocol/openid-connect/token",
)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        username = payload.get("preferred_username")
        if username is None:
            raise credentials_exception
        
        # Lấy roles từ token
        roles = payload.get("realm_access", {}).get("roles", [])
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        # Nếu user chưa có trong DB thì tự động tạo (như cơ chế JIT provisioning)
        user = User(
            username=username,
            hashed_password="idp_managed",
            role="admin" if "admin" in roles else "user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Cập nhật role theo IdP
        expected_role = "admin" if "admin" in roles else "user"
        if user.role != expected_role:
            user.role = expected_role
            db.commit()
            
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required",
        )
    return current_user
