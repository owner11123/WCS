from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Material(Base):
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    model = Column(String(100))
    description = Column(Text)
    category_major = Column(String(100), index=True)
    category_minor = Column(String(100), index=True)
    substitute_code = Column(String(50))
    vehicle_model = Column(String(100))
    is_deleted = Column(Boolean, default=False)

    price_versions = relationship("MaterialPriceVersion", back_populates="material")
    stocks = relationship("Stock", back_populates="material")

class MaterialPriceVersion(Base):
    __tablename__ = "material_price_version"
    
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    batch_no = Column(String(50), index=True)
    purchase_price = Column(Numeric(10, 2))
    sale_price = Column(Numeric(10, 2))
    currency = Column(String(3), default="CNY")
    contract_no = Column(String(50))
    effective_date = Column(Date)
    expire_date = Column(Date)

    material = relationship("Material", back_populates="price_versions")
    stocks = relationship("Stock", back_populates="price_version")
