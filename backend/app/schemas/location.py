from pydantic import BaseModel
from typing import Optional

class LocationBase(BaseModel):
    code: Optional[str] = None
    warehouse_code: Optional[str] = None
    zone_code: Optional[str] = None
    location_code: Optional[str] = None
    area_code: Optional[str] = None
    row_no: Optional[int] = None
    layer_no: Optional[int] = None
    col_no: Optional[int] = None
    is_active: Optional[bool] = True

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    id: int

    class Config:
        from_attributes = True

class LocationGenerateRequest(BaseModel):
    warehouse_code: str
    area_code: str
    row_start: int
    row_end: int
    layer_start: int
    layer_end: int
    col_start: int
    col_end: int
    reactivate_existing: Optional[bool] = True
