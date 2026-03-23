from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StockBase(BaseModel):
    material_id: int
    location_id: int
    price_version_id: int
    quantity: int

class StockCreate(StockBase):
    pass

class Stock(StockBase):
    id: int

    class Config:
        from_attributes = True

class StockDetail(Stock):
    material_code: str
    material_description: str
    location_code: str
    location_name: str
    purchase_price: float
    sale_price: float
    currency: str
    batch_no: str
    total_inbound: Optional[int] = 0
    total_outbound: Optional[int] = 0

class StockTransactionBase(BaseModel):
    material_id: int
    location_id: int
    price_version_id: int
    transaction_type: str
    quantity_change: int
    balance: int
    reference_order: Optional[str] = None
    operator_id: Optional[int] = None

class StockTransactionCreate(StockTransactionBase):
    pass

class StockTransaction(StockTransactionBase):
    id: int

    class Config:
        from_attributes = True