from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
import os

def init_db(db: Session) -> None:
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        password = os.getenv("ADMIN_PASSWORD", "123456")
        user = User(
            username="admin",
            password_hash=get_password_hash(password),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")

if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)
    db.close()
