from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Date
from app.db.base_class import Base

class InboundOrder(Base):
    __tablename__ = "inbound_order"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, index=True, nullable=False)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    price_version_id = Column(Integer, ForeignKey("material_price_version.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    contract_no = Column(String(50)) # 采购合同号
    inbound_time = Column(DateTime)
    status = Column(String(20), default="draft") # draft, completed, cancelled
    operator_id = Column(Integer, ForeignKey("user.id"))

class OutboundOrder(Base):
    __tablename__ = "outbound_order"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, index=True, nullable=False)
    group_no = Column(String(50), index=True)  # same for all lines in one outbound order
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    price_version_id = Column(Integer, ForeignKey("material_price_version.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    customer = Column(String(100))
    receiver = Column(String(50))
    outbound_time = Column(DateTime)
    status = Column(String(20), default="draft") # draft, completed, cancelled
    operator_id = Column(Integer, ForeignKey("user.id"))

class PendingInbound(Base):
    __tablename__ = "pending_inbound"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    price_version_id = Column(Integer, ForeignKey("material_price_version.id"))
    quantity = Column(Integer, nullable=False)
    received_quantity = Column(Integer, default=0)
    expected_date = Column(Date)
    contract_no = Column(String(50))
    remark = Column(Text)
    status = Column(String(20), default="pending") # pending, partial, completed
