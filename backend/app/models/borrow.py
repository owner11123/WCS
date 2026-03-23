from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base


class BorrowOrder(Base):
    __tablename__ = "borrow_order"

    id = Column(Integer, primary_key=True, index=True)
    borrow_no = Column(String(50), unique=True, index=True, nullable=False)
    borrower = Column(String(100), nullable=False)
    borrower_unit = Column(String(100))
    status = Column(String(20), default="open", index=True)
    remark = Column(String(200))
    borrow_time = Column(DateTime, default=datetime.utcnow, nullable=False)

    operator_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    items = relationship("BorrowItem", back_populates="borrow_order", cascade="all, delete-orphan")


class BorrowItem(Base):
    __tablename__ = "borrow_item"

    id = Column(Integer, primary_key=True, index=True)
    borrow_order_id = Column(Integer, ForeignKey("borrow_order.id"), index=True, nullable=False)

    material_id = Column(Integer, ForeignKey("material.id"), index=True, nullable=False)
    location_id = Column(Integer, ForeignKey("location.id"), index=True, nullable=False)
    price_version_id = Column(Integer, ForeignKey("material_price_version.id"), index=True, nullable=False)

    quantity = Column(Integer, nullable=False)
    returned_quantity = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="open", index=True)

    borrow_order = relationship("BorrowOrder", back_populates="items")
