from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class StockMovement(Base):
    __tablename__ = "stock_movement"

    id = Column(Integer, primary_key=True, index=True)
    movement_no = Column(String, unique=True, index=True, nullable=False)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    price_version_id = Column(Integer, ForeignKey("material_price_version.id"), nullable=False)
    source_location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    target_location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    operator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    movement_time = Column(DateTime, default=datetime.utcnow)

    # Relationships can be added here if needed, e.g., to material, location, user

class InventoryCheck(Base):
    __tablename__ = "inventory_check"

    id = Column(Integer, primary_key=True, index=True)
    check_no = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="pending") # pending, completed
    operator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    remarks = Column(String, nullable=True)

    items = relationship("InventoryCheckItem", back_populates="check_order", cascade="all, delete-orphan")

class InventoryCheckItem(Base):
    __tablename__ = "inventory_check_item"

    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(Integer, ForeignKey("inventory_check.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    price_version_id = Column(Integer, ForeignKey("material_price_version.id"), nullable=False)
    system_quantity = Column(Integer, nullable=False)
    actual_quantity = Column(Integer, nullable=True) # Nullable until counted
    difference = Column(Integer, nullable=True) # actual - system
    reason = Column(String, nullable=True)

    check_order = relationship("InventoryCheck", back_populates="items")
