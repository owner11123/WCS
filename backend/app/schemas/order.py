from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

class OrderItemBase(BaseModel):
    material_id: int
    actual_material_id: Optional[int] = None
    price_version_id: Optional[int] = None
    location_id: int
    quantity: int
    contract_no: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    sale_price: Optional[Decimal] = None
    currency: Optional[str] = "CNY"

class InboundOrderBase(BaseModel):
    order_no: str
    inbound_time: Optional[datetime] = None
    status: Optional[str] = "draft"

class InboundOrderCreate(InboundOrderBase):
    operator_id: int
    items: List[OrderItemBase]

class InboundOrder(InboundOrderBase):
    id: int
    operator_id: int
    material_id: int
    location_id: int
    quantity: int
    contract_no: Optional[str] = None
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    location_code: Optional[str] = None
    location_name: Optional[str] = None

    class Config:
        from_attributes = True

class OutboundOrderBase(BaseModel):
    order_no: Optional[str] = None
    customer: Optional[str] = None
    receiver: Optional[str] = None
    outbound_time: Optional[datetime] = None
    status: Optional[str] = "draft"

class OutboundOrderCreate(OutboundOrderBase):
    operator_id: int
    items: List[OrderItemBase]

class OutboundOrder(OutboundOrderBase):
    id: int
    operator_id: int
    material_id: int
    location_id: int
    quantity: int
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    location_code: Optional[str] = None
    location_name: Optional[str] = None
    sale_price: Optional[Decimal] = None
    currency: Optional[str] = None
    contract_no: Optional[str] = None

    class Config:
        from_attributes = True

class PendingInboundBase(BaseModel):
    material_id: int
    price_version_id: Optional[int] = None
    quantity: int
    received_quantity: Optional[int] = 0
    expected_date: Optional[date] = None
    contract_no: Optional[str] = None
    remark: Optional[str] = None
    status: Optional[str] = "pending"

class PendingInboundCreate(PendingInboundBase):
    pass

class PendingInbound(PendingInboundBase):
    id: int

    class Config:
        from_attributes = True
