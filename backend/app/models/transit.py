from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from datetime import datetime
from app.db.base_class import Base

class TransitInventory(Base):
    __tablename__ = "transit_inventory"

    id = Column(Integer, primary_key=True, index=True)
    box_no = Column(String, index=True, nullable=False)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    contract_no = Column(String, nullable=True)
    total_quantity = Column(Integer, nullable=False)
    received_quantity = Column(Integer, default=0, nullable=False)
    quantity = Column(Integer, nullable=False)  # pending quantity
    purchase_price = Column(Numeric(10, 2), nullable=True)
    sale_price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String, default="CNY")
    status = Column(String, default="in_transit") # in_transit, received
    created_at = Column(DateTime, default=datetime.utcnow)
