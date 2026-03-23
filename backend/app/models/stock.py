from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Stock(Base):
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    price_version_id = Column(Integer, ForeignKey("material_price_version.id"), nullable=False)
    quantity = Column(Integer, default=0)
    total_inbound = Column(Integer, default=0)
    total_outbound = Column(Integer, default=0)

    material = relationship("Material", back_populates="stocks")
    location = relationship("Location", back_populates="stocks")
    price_version = relationship("MaterialPriceVersion", back_populates="stocks")

class StockTransaction(Base):
    __tablename__ = "stock_transaction"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    price_version_id = Column(Integer, ForeignKey("material_price_version.id"), nullable=False)
    transaction_type = Column(String(20)) # inbound, outbound, adjust, return_in, return_out
    quantity_change = Column(Integer)
    balance = Column(Integer)
    reference_order = Column(String(50))
    operator_id = Column(Integer, ForeignKey("user.id"))