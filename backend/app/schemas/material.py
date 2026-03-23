from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal

class MaterialPriceVersionBase(BaseModel):
    batch_no: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    sale_price: Optional[Decimal] = None
    currency: Optional[str] = "CNY"
    contract_no: Optional[str] = None
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None

class MaterialPriceVersionCreate(MaterialPriceVersionBase):
    pass

class MaterialPriceVersion(MaterialPriceVersionBase):
    id: int
    material_id: int

    class Config:
        from_attributes = True

class MaterialBase(BaseModel):
    code: str
    model: Optional[str] = None
    description: Optional[str] = None
    category_major: Optional[str] = None
    category_minor: Optional[str] = None
    substitute_code: Optional[str] = None
    vehicle_model: Optional[str] = None
    is_deleted: Optional[bool] = False

class MaterialCreate(MaterialBase):
    price_versions: Optional[List[MaterialPriceVersionCreate]] = []

class Material(MaterialBase):
    id: int
    price_versions: List[MaterialPriceVersion] = []

    class Config:
        from_attributes = True
