import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.order import Order
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead
from app.services.deps import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])
security_logger = logging.getLogger("api.security")


@router.get("/", response_model=list[OrderRead])
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "admin":
        return db.query(Order).order_by(Order.id).all()

    return (
        db.query(Order)
        .filter(Order.owner_id == current_user.id)
        .order_by(Order.id)
        .all()
    )


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = Order(
        item_name=payload.item_name,
        amount=payload.amount,
        status=payload.status,
        owner_id=current_user.id,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/vulnerable/{order_id}", response_model=OrderRead)
def vulnerable_get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint co tinh bi loi BOLA de demo.
    Bat ky user da dang nhap nao cung xem duoc order cua user khac neu biet order_id.
    KHONG dung endpoint nay cho ban da bao ve.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    security_logger.warning(
        "bola_vulnerable_access_allowed",
        extra={
            "event": "bola_vulnerable_access_allowed",
            "username": current_user.username,
            "order_id": order_id,
        },
    )
    return order


@router.get("/{order_id}", response_model=OrderRead)
def secure_get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint da fix BOLA.
    User chi xem duoc order cua minh. Admin xem duoc tat ca.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role != "admin" and order.owner_id != current_user.id:
        security_logger.warning(
            "bola_blocked",
            extra={
                "event": "bola_blocked",
                "username": current_user.username,
                "order_id": order_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this order",
        )

    return order
