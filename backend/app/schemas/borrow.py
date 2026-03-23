from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BorrowItemCreate(BaseModel):
    material_id: int
    location_id: int
    price_version_id: int
    quantity: int


class BorrowOrderCreate(BaseModel):
    borrower: str
    borrower_unit: Optional[str] = None
    remark: Optional[str] = None
    items: List[BorrowItemCreate]


class BorrowItemReturn(BaseModel):
    borrow_item_id: int
    return_quantity: int
    location_id: Optional[int] = None


class BorrowReturnRequest(BaseModel):
    items: List[BorrowItemReturn]


class BorrowItem(BaseModel):
    id: int
    material_id: int
    location_id: int
    price_version_id: int
    quantity: int
    returned_quantity: int
    status: str

    class Config:
        from_attributes = True


class BorrowOrder(BaseModel):
    id: int
    borrow_no: str
    borrower: str
    borrower_unit: Optional[str] = None
    status: str
    remark: Optional[str] = None
    borrow_time: datetime
    operator_id: int
    items: List[BorrowItem] = []

    class Config:
        from_attributes = True

