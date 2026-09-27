from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserRead
from app.services.deps import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/", response_model=list[UserRead])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/exposure/vulnerable", tags=["Excessive Data Exposure Demo"])
def get_all_users_vulnerable(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Endpoint bị lỗi Excessive Data Exposure.
    Lấy danh sách user và trả về trực tiếp Object/Dict từ Database mà không filter (không dùng response_model).
    Attacker sẽ thấy cả password hash, thông tin nhạy cảm.
    """
    users = db.query(User).all()
    # Chuyển object sang dict thủ công để mô phỏng lỗi (vì SQLAlchemy object không tự serialize thành JSON)
    return [{"id": u.id, "username": u.username, "role": u.role, "hashed_password": u.hashed_password} for u in users]


@router.get("/exposure/secure", response_model=list[UserRead], tags=["Excessive Data Exposure Demo"])
def get_all_users_secure(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Endpoint an toàn.
    Sử dụng response_model=list[UserRead] để FastAPI tự động loại bỏ các trường không có trong Schema (như hashed_password).
    """
    return db.query(User).all()
