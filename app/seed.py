from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.order import Order
from app.models.user import User


def get_or_create_user(db: Session, username: str, password: str, role: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user:
        return user

    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_orders(db: Session, user1: User, user2: User):
    if db.query(Order).count() > 0:
        return

    orders = [
        Order(item_name="Laptop Dell cho phong ke toan", amount=18500000, status="paid", owner_id=user1.id),
        Order(item_name="May in Canon", amount=4200000, status="pending", owner_id=user2.id),
        Order(item_name="Goi bao tri website", amount=3000000, status="paid", owner_id=user1.id),
        Order(item_name="Router WiFi van phong", amount=2500000, status="pending", owner_id=user2.id),
    ]
    db.add_all(orders)
    db.commit()


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user1 = get_or_create_user(db, "user1", "password123", "user")
        user2 = get_or_create_user(db, "user2", "password123", "user")
        get_or_create_user(db, "admin", "admin123", "admin")
        seed_orders(db, user1, user2)
        print("Seed data completed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
