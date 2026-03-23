from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import SessionLocal
from app.models.material import Material, MaterialPriceVersion
from app.schemas.material import Material as MaterialSchema, MaterialCreate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=MaterialSchema)
def create_material(material_in: MaterialCreate, db: Session = Depends(get_db)):
    db_material = db.query(Material).filter(Material.code == material_in.code).first()
    if db_material:
        raise HTTPException(status_code=400, detail="Material code already exists")
    
    material = Material(
        code=material_in.code,
        model=material_in.model,
        description=material_in.description,
        category_major=material_in.category_major,
        category_minor=material_in.category_minor,
        substitute_code=material_in.substitute_code,
        vehicle_model=material_in.vehicle_model,
        is_deleted=material_in.is_deleted
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    for pv in material_in.price_versions:
        price_version = MaterialPriceVersion(
            material_id=material.id,
            **pv.dict()
        )
        db.add(price_version)
    
    if material_in.price_versions:
        db.commit()
        db.refresh(material)
        
    return material

@router.get("/")
def read_materials(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    query = db.query(Material).filter(Material.is_deleted == False)
    total = query.count()
    materials = query.offset(skip).limit(limit).all()
    
    # Format to match schema
    items = []
    for m in materials:
        items.append({
            "id": m.id,
            "code": m.code,
            "model": m.model,
            "description": m.description,
            "category_major": m.category_major,
            "category_minor": m.category_minor,
            "substitute_code": m.substitute_code,
            "vehicle_model": m.vehicle_model,
            "is_deleted": m.is_deleted
        })
        
    return {
        "total": total,
        "items": items
    }

@router.put("/{material_id}", response_model=MaterialSchema)
def update_material(material_id: int, material_in: MaterialCreate, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    material.model = material_in.model
    material.description = material_in.description
    material.category_major = material_in.category_major
    material.category_minor = material_in.category_minor
    material.substitute_code = material_in.substitute_code
    material.vehicle_model = material_in.vehicle_model
    
    db.commit()
    db.refresh(material)
    return material
