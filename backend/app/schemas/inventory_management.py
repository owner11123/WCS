from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- Stock Movement Schemas ---
class StockMovementBase(BaseModel):
    material_id: int
    price_version_id: int
    source_location_id: int
    target_location_id: int
    quantity: int

class StockMovementCreate(StockMovementBase):
    operator_id: int

class StockMovementSchema(StockMovementBase):
    id: int
    movement_no: str
    operator_id: int
    movement_time: datetime
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    source_location_code: Optional[str] = None
    target_location_code: Optional[str] = None
    batch_no: Optional[str] = None

    class Config:
        from_attributes = True

# --- Inventory Check Schemas ---
class InventoryCheckItemBase(BaseModel):
    material_id: int
    location_id: int
    price_version_id: int
    system_quantity: int
    actual_quantity: Optional[int] = None
    difference: Optional[int] = None
    reason: Optional[str] = None

class InventoryCheckItemUpdate(BaseModel):
    id: int
    actual_quantity: int
    reason: Optional[str] = None

class InventoryCheckItemSchema(InventoryCheckItemBase):
    id: int
    check_id: int
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    location_code: Optional[str] = None
    batch_no: Optional[str] = None

    class Config:
        from_attributes = True

class InventoryCheckCreate(BaseModel):
    operator_id: int
    location_ids: Optional[List[int]] = None # Empty means full check
    remarks: Optional[str] = None

class InventoryCheckUpdate(BaseModel):
    items: List[InventoryCheckItemUpdate]

class InventoryCheckSchema(BaseModel):
    id: int
    check_no: str
    status: str
    operator_id: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    remarks: Optional[str] = None
    items: Optional[List[InventoryCheckItemSchema]] = []

    class Config:
        from_attributes = True
