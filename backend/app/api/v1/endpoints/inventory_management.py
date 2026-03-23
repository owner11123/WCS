from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, aliased
from sqlalchemy import desc
from typing import List
from datetime import datetime

from app.db.session import SessionLocal
from app.models.inventory_management import StockMovement, InventoryCheck, InventoryCheckItem
from app.models.stock import Stock, StockTransaction
from app.models.material import Material, MaterialPriceVersion
from app.models.location import Location
from app.schemas.inventory_management import (
    StockMovementCreate, StockMovementSchema,
    InventoryCheckCreate, InventoryCheckSchema, InventoryCheckUpdate
)

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Stock Movement ---

@router.get("/movements")
def get_movements(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    SourceLocation = aliased(Location)
    TargetLocation = aliased(Location)
    
    query = db.query(
        StockMovement.id,
        StockMovement.movement_no,
        StockMovement.material_id,
        StockMovement.price_version_id,
        StockMovement.source_location_id,
        StockMovement.target_location_id,
        StockMovement.quantity,
        StockMovement.operator_id,
        StockMovement.movement_time,
        Material.code.label('material_code'),
        Material.description.label('material_description'),
        SourceLocation.code.label('source_location_code'),
        TargetLocation.code.label('target_location_code'),
        MaterialPriceVersion.batch_no.label('batch_no')
    ).join(Material, StockMovement.material_id == Material.id)\
     .join(SourceLocation, StockMovement.source_location_id == SourceLocation.id)\
     .join(TargetLocation, StockMovement.target_location_id == TargetLocation.id)\
     .join(MaterialPriceVersion, StockMovement.price_version_id == MaterialPriceVersion.id)
     
    total = query.count()
    movements = query.order_by(desc(StockMovement.movement_time)).offset(skip).limit(limit).all()
    
    items = []
    for m in movements:
        items.append(dict(m._mapping))
        
    return {"total": total, "items": items}

@router.post("/movements")
def create_movement(movement_in: StockMovementCreate, db: Session = Depends(get_db)):
    if movement_in.source_location_id == movement_in.target_location_id:
        raise HTTPException(status_code=400, detail="Source and target locations must be different")
        
    # 1. Check Source Stock
    source_stock = db.query(Stock).filter(
        Stock.material_id == movement_in.material_id,
        Stock.location_id == movement_in.source_location_id,
        Stock.price_version_id == movement_in.price_version_id
    ).with_for_update().first()
    
    if not source_stock or source_stock.quantity < movement_in.quantity:
        db.rollback()
        raise HTTPException(status_code=400, detail="Insufficient stock in source location")
        
    # 2. Update Source Stock
    source_stock.quantity -= movement_in.quantity
    
    # 3. Update Target Stock
    target_stock = db.query(Stock).filter(
        Stock.material_id == movement_in.material_id,
        Stock.location_id == movement_in.target_location_id,
        Stock.price_version_id == movement_in.price_version_id
    ).with_for_update().first()
    
    if target_stock:
        target_stock.quantity += movement_in.quantity
    else:
        target_stock = Stock(
            material_id=movement_in.material_id,
            location_id=movement_in.target_location_id,
            price_version_id=movement_in.price_version_id,
            quantity=movement_in.quantity,
            total_inbound=0,
            total_outbound=0
        )
        db.add(target_stock)
        
    # 4. Create Movement Record
    movement_no = f"MV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    movement = StockMovement(
        movement_no=movement_no,
        material_id=movement_in.material_id,
        price_version_id=movement_in.price_version_id,
        source_location_id=movement_in.source_location_id,
        target_location_id=movement_in.target_location_id,
        quantity=movement_in.quantity,
        operator_id=movement_in.operator_id
    )
    db.add(movement)
    
    # 5. Create Transactions
    db.add(StockTransaction(
        material_id=movement_in.material_id,
        location_id=movement_in.source_location_id,
        price_version_id=movement_in.price_version_id,
        transaction_type="movement_out",
        quantity_change=-movement_in.quantity,
        balance=source_stock.quantity,
        reference_order=movement_no,
        operator_id=movement_in.operator_id
    ))
    db.flush()
    db.add(StockTransaction(
        material_id=movement_in.material_id,
        location_id=movement_in.target_location_id,
        price_version_id=movement_in.price_version_id,
        transaction_type="movement_in",
        quantity_change=movement_in.quantity,
        balance=target_stock.quantity,
        reference_order=movement_no,
        operator_id=movement_in.operator_id
    ))
    
    db.commit()
    return {"message": "Stock movement completed successfully"}

# --- Inventory Check ---

@router.get("/checks")
def get_checks(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    query = db.query(InventoryCheck)
    total = query.count()
    checks = query.order_by(desc(InventoryCheck.created_at)).offset(skip).limit(limit).all()
    return {"total": total, "items": checks}

@router.get("/checks/{check_id}")
def get_check_detail(check_id: int, db: Session = Depends(get_db)):
    check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
        
    items_query = db.query(
        InventoryCheckItem.id,
        InventoryCheckItem.check_id,
        InventoryCheckItem.material_id,
        InventoryCheckItem.location_id,
        InventoryCheckItem.price_version_id,
        InventoryCheckItem.system_quantity,
        InventoryCheckItem.actual_quantity,
        InventoryCheckItem.difference,
        InventoryCheckItem.reason,
        Material.code.label('material_code'),
        Material.description.label('material_description'),
        Location.code.label('location_code'),
        MaterialPriceVersion.batch_no.label('batch_no')
    ).join(Material, InventoryCheckItem.material_id == Material.id)\
     .join(Location, InventoryCheckItem.location_id == Location.id)\
     .join(MaterialPriceVersion, InventoryCheckItem.price_version_id == MaterialPriceVersion.id)\
     .filter(InventoryCheckItem.check_id == check_id).all()
     
    return {
        "check": check,
        "items": [dict(i._mapping) for i in items_query]
    }

@router.post("/checks")
def create_check(check_in: InventoryCheckCreate, db: Session = Depends(get_db)):
    check_no = f"IC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    check = InventoryCheck(
        check_no=check_no,
        operator_id=check_in.operator_id,
        remarks=check_in.remarks
    )
    db.add(check)
    db.flush()
    
    # Snapshot current stock
    stock_query = db.query(Stock).filter(Stock.quantity > 0)
    if check_in.location_ids:
        stock_query = stock_query.filter(Stock.location_id.in_(check_in.location_ids))
        
    stocks = stock_query.all()
    for stock in stocks:
        item = InventoryCheckItem(
            check_id=check.id,
            material_id=stock.material_id,
            location_id=stock.location_id,
            price_version_id=stock.price_version_id,
            system_quantity=stock.quantity
        )
        db.add(item)
        
    db.commit()
    return {"message": "Inventory check created", "check_id": check.id}

@router.put("/checks/{check_id}")
def update_check_items(check_id: int, data: InventoryCheckUpdate, db: Session = Depends(get_db)):
    check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not check or check.status == 'completed':
        raise HTTPException(status_code=400, detail="Invalid check or already completed")
        
    for item_data in data.items:
        db_item = db.query(InventoryCheckItem).filter(
            InventoryCheckItem.id == item_data.id,
            InventoryCheckItem.check_id == check_id
        ).first()
        if db_item:
            db_item.actual_quantity = item_data.actual_quantity
            db_item.difference = item_data.actual_quantity - db_item.system_quantity
            db_item.reason = item_data.reason
            
    db.commit()
    return {"message": "Check items updated"}

@router.post("/checks/{check_id}/complete")
def complete_check(check_id: int, db: Session = Depends(get_db)):
    check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not check or check.status == 'completed':
        raise HTTPException(status_code=400, detail="Invalid check or already completed")
        
    items = db.query(InventoryCheckItem).filter(
        InventoryCheckItem.check_id == check_id,
        InventoryCheckItem.actual_quantity.isnot(None),
        InventoryCheckItem.difference != 0
    ).all()
    
    # Apply differences to stock
    for item in items:
        stock = db.query(Stock).filter(
            Stock.material_id == item.material_id,
            Stock.location_id == item.location_id,
            Stock.price_version_id == item.price_version_id
        ).first()
        
        if stock:
            # Create adjusting transaction
            trans_type = "check_in" if item.difference > 0 else "check_out"
            db.add(StockTransaction(
                material_id=item.material_id,
                location_id=item.location_id,
                price_version_id=item.price_version_id,
                transaction_type=trans_type,
                quantity_change=item.difference,
                balance=item.actual_quantity,
                reference_order=check.check_no,
                operator_id=check.operator_id
            ))
            stock.quantity = item.actual_quantity
            
            # Note: For strict accounting, we might want to adjust total_inbound/outbound as well,
            # but usually inventory checks are just adjustments to current stock.
            
    check.status = "completed"
    check.completed_at = datetime.utcnow()
    db.commit()
    return {"message": "Inventory check completed and stock adjusted"}


@router.delete("/checks/{check_id}")
def delete_check(check_id: int, db: Session = Depends(get_db)):
    check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    if check.status == "completed":
        raise HTTPException(status_code=400, detail="Completed check cannot be deleted")

    db.delete(check)
    db.commit()
    return {"message": "Inventory check deleted"}
