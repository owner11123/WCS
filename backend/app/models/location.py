from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Location(Base):
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    warehouse_code = Column(String(50), index=True)
    zone_code = Column(String(50), index=True)
    location_code = Column(String(50), index=True)
    area_code = Column(String(50), index=True)
    row_no = Column(Integer, index=True)
    layer_no = Column(Integer, index=True)
    col_no = Column(Integer, index=True)
    is_active = Column(Boolean, default=True)

    stocks = relationship("Stock", back_populates="location")
