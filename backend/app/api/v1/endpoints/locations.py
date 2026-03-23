from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import SessionLocal
from app.models.location import Location
from app.schemas.location import Location as LocationSchema, LocationCreate, LocationGenerateRequest

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=LocationSchema)
def create_location(location_in: LocationCreate, db: Session = Depends(get_db)):
    code = (location_in.code or "").strip()
    warehouse_code = (location_in.warehouse_code or "").strip() or None
    zone_code = (location_in.zone_code or "").strip() or None
    location_code = (location_in.location_code or "").strip() or None
    area_code = (location_in.area_code or "").strip() or None
    row_no = int(location_in.row_no) if location_in.row_no is not None else None
    layer_no = int(location_in.layer_no) if location_in.layer_no is not None else None
    col_no = int(location_in.col_no) if location_in.col_no is not None else None

    if not code:
        if warehouse_code and area_code and row_no and layer_no and col_no:
            code = f"{warehouse_code}-{area_code}-{row_no}-{layer_no}-{col_no}"
        elif row_no and layer_no and col_no:
            code = f"{row_no}-{layer_no}-{col_no}"
        elif warehouse_code and zone_code and location_code:
            code = f"{warehouse_code}-{zone_code}-{location_code}"
        else:
            raise HTTPException(status_code=400, detail="Either code or required segment fields must be provided")

    parts = code.split("-")
    if len(parts) == 5:
        warehouse_code = warehouse_code or parts[0]
        area_code = area_code or parts[1]
        row_no = row_no or int(parts[2])
        layer_no = layer_no or int(parts[3])
        col_no = col_no or int(parts[4])
    elif len(parts) == 3:
        try:
            r, l, c = int(parts[0]), int(parts[1]), int(parts[2])
            row_no = row_no or r
            layer_no = layer_no or l
            col_no = col_no or c
        except ValueError:
            if not (warehouse_code and zone_code and location_code):
                warehouse_code, zone_code, location_code = parts[0], parts[1], parts[2]

    db_location = db.query(Location).filter(Location.code == code).first()
    if db_location:
        raise HTTPException(status_code=400, detail="Location code already exists")
    
    location = Location(
        code=code,
        warehouse_code=warehouse_code,
        zone_code=zone_code,
        location_code=location_code,
        area_code=area_code,
        row_no=row_no,
        layer_no=layer_no,
        col_no=col_no,
        is_active=location_in.is_active if location_in.is_active is not None else True
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return location

@router.get("/")
def read_locations(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    query = db.query(Location).filter(Location.is_active == True)
    total = query.count()
    locations = query.offset(skip).limit(limit).all()
    
    items = []
    for l in locations:
        items.append({
            "id": l.id,
            "code": l.code,
            "warehouse_code": l.warehouse_code,
            "zone_code": l.zone_code,
            "location_code": l.location_code,
            "area_code": l.area_code,
            "row_no": l.row_no,
            "layer_no": l.layer_no,
            "col_no": l.col_no,
            "is_active": l.is_active
        })
        
    return {
        "total": total,
        "items": items
    }

@router.delete("/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Soft delete
    location.is_active = False
    db.commit()
    return {"message": "Location deleted successfully"}

@router.post("/generate")
def generate_locations(req: LocationGenerateRequest, db: Session = Depends(get_db)):
    warehouse_code = (req.warehouse_code or "").strip()
    area_code = (req.area_code or "").strip()
    if not warehouse_code or not area_code:
        raise HTTPException(status_code=400, detail="warehouse_code and area_code are required")

    row_start = int(req.row_start)
    row_end = int(req.row_end)
    layer_start = int(req.layer_start)
    layer_end = int(req.layer_end)
    col_start = int(req.col_start)
    col_end = int(req.col_end)

    if row_start <= 0 or layer_start <= 0 or col_start <= 0:
        raise HTTPException(status_code=400, detail="Start values must be >= 1")
    if row_end < row_start or layer_end < layer_start or col_end < col_start:
        raise HTTPException(status_code=400, detail="End values must be >= start values")

    codes = []
    for r in range(row_start, row_end + 1):
        for l in range(layer_start, layer_end + 1):
            for c in range(col_start, col_end + 1):
                codes.append(f"{warehouse_code}-{area_code}-{r}-{l}-{c}")

    existing = db.query(Location).filter(Location.code.in_(codes)).all()
    existing_by_code = {x.code: x for x in existing}

    created = 0
    reactivated = 0
    for code in codes:
        ex = existing_by_code.get(code)
        if ex:
            if req.reactivate_existing and not ex.is_active:
                ex.is_active = True
                reactivated += 1
            if ex.warehouse_code is None or ex.zone_code is None or ex.location_code is None:
                parts = code.split("-")
                if len(parts) == 3:
                    ex.warehouse_code = ex.warehouse_code or parts[0]
                    ex.zone_code = ex.zone_code or parts[1]
                    ex.location_code = ex.location_code or parts[2]
            continue

        parts = code.split("-")
        location = Location(
            code=code,
            warehouse_code=warehouse_code,
            area_code=area_code,
            row_no=int(parts[2]),
            layer_no=int(parts[3]),
            col_no=int(parts[4]),
            is_active=True
        )
        db.add(location)
        created += 1

    db.commit()
    return {
        "message": "Locations generated successfully",
        "created": created,
        "existing": len(existing),
        "reactivated": reactivated,
        "total": len(codes)
    }
