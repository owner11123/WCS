from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from app.db.session import SessionLocal
from app.models.transit import TransitInventory
from app.models.material import Material
from pydantic import BaseModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_transit_inventory(skip: int = 0, limit: int = 20, status: str = None, q: str = None, box_no: str = None, db: Session = Depends(get_db)):
    query = db.query(
        TransitInventory.id,
        TransitInventory.box_no,
        TransitInventory.material_id,
        TransitInventory.contract_no,
        TransitInventory.quantity,
        TransitInventory.total_quantity,
        TransitInventory.received_quantity,
        TransitInventory.purchase_price,
        TransitInventory.sale_price,
        TransitInventory.currency,
        TransitInventory.status,
        TransitInventory.created_at,
        Material.code.label('material_code'),
        Material.description.label('material_description'),
        Material.vehicle_model.label('vehicle_model')
    ).join(Material, TransitInventory.material_id == Material.id)
    
    if status:
        query = query.filter(TransitInventory.status == status)
    keyword = q or box_no
    if keyword:
        query = query.filter(
            TransitInventory.box_no.ilike(f"%{keyword}%") |
            Material.code.ilike(f"%{keyword}%")
        )
        
    total = query.count()
    records = query.order_by(desc(TransitInventory.created_at)).offset(skip).limit(limit).all()
    
    items = []
    for r in records:
        items.append({
            "id": r.id,
            "box_no": r.box_no,
            "material_id": r.material_id,
            "contract_no": r.contract_no,
            "quantity": r.quantity,
            "total_quantity": r.total_quantity,
            "received_quantity": r.received_quantity,
            "purchase_price": float(r.purchase_price) if r.purchase_price else None,
            "sale_price": float(r.sale_price) if r.sale_price else None,
            "currency": r.currency,
            "status": r.status,
            "created_at": r.created_at,
            "material_code": r.material_code,
            "material_description": r.material_description,
            "vehicle_model": r.vehicle_model
        })
        
    return {"total": total, "items": items}

@router.get("/available-boxes")
def get_available_boxes(db: Session = Depends(get_db)):
    query = db.query(
        TransitInventory.id,
        TransitInventory.box_no,
        TransitInventory.quantity,
        TransitInventory.total_quantity,
        TransitInventory.received_quantity,
        TransitInventory.contract_no,
        Material.code.label('material_code'),
        Material.description.label('material_description')
    ).join(Material, TransitInventory.material_id == Material.id)\
     .filter(TransitInventory.status == 'in_transit', TransitInventory.quantity > 0)
     
    records = query.order_by(desc(TransitInventory.created_at)).all()
    
    # Group by box_no
    grouped_boxes = {}
    for r in records:
        if r.box_no not in grouped_boxes:
            grouped_boxes[r.box_no] = {
                "box_no": r.box_no,
                "items": []
            }
            
        grouped_boxes[r.box_no]["items"].append({
            "id": r.id,
            "quantity": r.quantity,
            "total_quantity": r.total_quantity,
            "received_quantity": r.received_quantity,
            "contract_no": r.contract_no,
            "material_code": r.material_code,
            "material_description": r.material_description
        })
        
    return list(grouped_boxes.values())
