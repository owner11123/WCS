from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import datetime

from app.db.session import SessionLocal
from app.models.stock import Stock, StockTransaction
from app.models.order import InboundOrder, OutboundOrder, PendingInbound
from app.models.transit import TransitInventory
from app.models.material import MaterialPriceVersion, Material
from app.models.location import Location
from app.models.user import User
from app.schemas.order import InboundOrderCreate, InboundOrder as InboundOrderSchema
from app.schemas.order import OutboundOrderCreate, OutboundOrder as OutboundOrderSchema

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_default_price_version(db: Session, material_id: int, item_data=None):
    contract_no = item_data.contract_no if item_data and item_data.contract_no else "DEFAULT"

    # Find by contract_no (which is now batch_no)
    pv = db.query(MaterialPriceVersion).filter(
        MaterialPriceVersion.material_id == material_id,
        MaterialPriceVersion.batch_no == contract_no
    ).first()
    
    if not pv:
        pv = MaterialPriceVersion(
            material_id=material_id,
            batch_no=contract_no,
            purchase_price=item_data.purchase_price if item_data else 0,
            sale_price=item_data.sale_price if item_data else 0,
            currency=item_data.currency if item_data else "CNY"
        )
        db.add(pv)
        db.flush()
    return pv.id

@router.get("/inbound")
def get_inbound_orders(skip: int = 0, limit: int = 20, material_code: str = None, db: Session = Depends(get_db)):
    query = db.query(
        InboundOrder.id,
        InboundOrder.order_no,
        InboundOrder.material_id,
        InboundOrder.location_id,
        InboundOrder.quantity,
        InboundOrder.contract_no,
        InboundOrder.inbound_time,
        InboundOrder.status,
        InboundOrder.operator_id,
        User.username.label('operator_name'),
        Material.code.label('material_code'),
        Material.description.label('material_description'),
        Location.code.label('location_code'),
        Location.code.label('location_name') # Fallback
    ).join(
        Material, InboundOrder.material_id == Material.id
    ).join(
        Location, InboundOrder.location_id == Location.id
    ).outerjoin(
        User, InboundOrder.operator_id == User.id
    )
    
    if material_code:
        query = query.filter(Material.code.ilike(f"%{material_code}%"))
        
    total = query.count()
    orders = query.order_by(desc(InboundOrder.inbound_time)).offset(skip).limit(limit).all()
    
    items = []
    for o in orders:
        items.append({
            "id": o.id,
            "order_no": o.order_no,
            "material_id": o.material_id,
            "location_id": o.location_id,
            "quantity": o.quantity,
            "contract_no": o.contract_no,
            "inbound_time": o.inbound_time,
            "status": o.status,
            "operator_id": o.operator_id,
            "operator_name": o.operator_name,
            "material_code": o.material_code,
            "material_description": o.material_description,
            "location_code": o.location_code,
            "location_name": o.location_name
        })
        
    return {
        "total": total,
        "items": items
    }

@router.get("/outbound")
def get_outbound_orders(skip: int = 0, limit: int = 20, material_code: str = None, db: Session = Depends(get_db)):
    query = db.query(
        OutboundOrder.id,
        OutboundOrder.group_no.label('order_no'),
        OutboundOrder.order_no.label('line_no'),
        OutboundOrder.customer,
        OutboundOrder.receiver,
        OutboundOrder.material_id,
        OutboundOrder.location_id,
        OutboundOrder.quantity,
        OutboundOrder.outbound_time,
        OutboundOrder.status,
        OutboundOrder.operator_id,
        User.username.label('operator_name'),
        Material.code.label('material_code'),
        Material.model.label('material_model'),
        Material.description.label('material_description'),
        Material.vehicle_model.label('vehicle_model'),
        Location.code.label('location_code'),
        Location.code.label('location_name'),
        MaterialPriceVersion.sale_price,
        MaterialPriceVersion.currency,
        MaterialPriceVersion.batch_no.label('contract_no')
    ).join(
        Material, OutboundOrder.material_id == Material.id
    ).join(
        Location, OutboundOrder.location_id == Location.id
    ).outerjoin(
        User, OutboundOrder.operator_id == User.id
    ).join(
        MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id
    )
    
    if material_code:
        query = query.filter(Material.code.ilike(f"%{material_code}%"))
        
    total = query.count()
    orders = query.order_by(desc(OutboundOrder.outbound_time)).offset(skip).limit(limit).all()
    
    items = []
    for o in orders:
        items.append({
            "id": o.id,
            "order_no": o.order_no,
            "line_no": o.line_no,
            "customer": o.customer,
            "receiver": o.receiver,
            "material_id": o.material_id,
            "location_id": o.location_id,
            "quantity": o.quantity,
            "outbound_time": o.outbound_time,
            "status": o.status,
            "operator_id": o.operator_id,
            "operator_name": o.operator_name,
            "material_code": o.material_code,
            "material_description": o.material_description,
            "location_code": o.location_code,
            "location_name": o.location_name,
            "sale_price": float(o.sale_price) if o.sale_price else None,
            "currency": o.currency,
            "contract_no": o.contract_no
        })
        
    return {
        "total": total,
        "items": items
    }

@router.get("/outbound/print/{group_no}")
def get_outbound_print(group_no: str, db: Session = Depends(get_db)):
    rows = db.query(
        OutboundOrder.id,
        OutboundOrder.group_no,
        OutboundOrder.customer,
        OutboundOrder.receiver,
        OutboundOrder.outbound_time,
        User.username.label('operator_name'),
        Material.code.label('material_code'),
        Material.model.label('material_model'),
        Material.description.label('material_description'),
        Material.vehicle_model.label('vehicle_model'),
        MaterialPriceVersion.batch_no.label('contract_no'),
        OutboundOrder.quantity
    ).join(
        Material, OutboundOrder.material_id == Material.id
    ).outerjoin(
        User, OutboundOrder.operator_id == User.id
    ).join(
        MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id
    ).filter(
        OutboundOrder.group_no == group_no
    ).order_by(OutboundOrder.id.asc()).all()

    if not rows:
        raise HTTPException(status_code=404, detail="Outbound order not found")

    header = {
        "order_no": rows[0].group_no,
        "customer": rows[0].customer,
        "receiver": rows[0].receiver,
        "outbound_time": rows[0].outbound_time,
        "operator_name": rows[0].operator_name
    }

    items = []
    for idx, r in enumerate(rows, start=1):
        items.append({
            "seq": idx,
            "material_code": r.material_code,
            "material_model": r.material_model,
            "material_description": r.material_description,
            "vehicle_model": r.vehicle_model,
            "contract_no": r.contract_no,
            "quantity": r.quantity
        })

    return {"header": header, "items": items}

from pydantic import BaseModel
from typing import List

class TransitItemRequest(BaseModel):
    transit_id: int
    location_id: int
    inbound_quantity: int

class TransitInboundRequest(BaseModel):
    box_no: str
    operator_id: int
    items: List[TransitItemRequest]

@router.post("/inbound/transit")
def inbound_from_transit(req: TransitInboundRequest, db: Session = Depends(get_db)):
    # Verify all items belong to this box and are in transit
    transit_ids = [item.transit_id for item in req.items]
    transits = db.query(TransitInventory).filter(
        TransitInventory.id.in_(transit_ids),
        TransitInventory.box_no == req.box_no,
        TransitInventory.status == 'in_transit'
    ).all()
    
    if len(transits) != len(req.items):
        raise HTTPException(status_code=400, detail="Some items are invalid or already received")
        
    transit_map = {t.id: t for t in transits}
    
    for req_item in req.items:
        transit = transit_map[req_item.transit_id]
        
        # Verify quantity
        if req_item.inbound_quantity <= 0 or req_item.inbound_quantity > transit.quantity:
            raise HTTPException(status_code=400, detail=f"Invalid inbound quantity for item {transit.id}")
            
        # 1. Ensure price version exists
        pv = db.query(MaterialPriceVersion).filter(
            MaterialPriceVersion.material_id == transit.material_id,
            MaterialPriceVersion.batch_no == transit.contract_no
        ).first()
        
        if not pv:
            pv = MaterialPriceVersion(
                material_id=transit.material_id,
                batch_no=transit.contract_no,
                purchase_price=transit.purchase_price or 0,
                sale_price=transit.sale_price or 0,
                currency=transit.currency or "CNY"
            )
            db.add(pv)
            db.flush()
            
        # 2. Create Inbound Order
        order_no = f"IN-{transit.box_no}-{transit.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        order = InboundOrder(
            order_no=order_no,
            material_id=transit.material_id,
            price_version_id=pv.id,
            location_id=req_item.location_id,
            quantity=req_item.inbound_quantity,
            contract_no=transit.contract_no,
            operator_id=req.operator_id,
            status="completed",
            inbound_time=datetime.utcnow()
        )
        db.add(order)
        
        # 3. Update Stock
        stock = db.query(Stock).filter(
            Stock.material_id == transit.material_id,
            Stock.location_id == req_item.location_id,
            Stock.price_version_id == pv.id
        ).first()

        if stock:
            stock.quantity += req_item.inbound_quantity
            if stock.total_inbound is None: stock.total_inbound = 0
            stock.total_inbound += req_item.inbound_quantity
        else:
            stock = Stock(
                material_id=transit.material_id,
                location_id=req_item.location_id,
                price_version_id=pv.id,
                quantity=req_item.inbound_quantity,
                total_inbound=req_item.inbound_quantity,
                total_outbound=0
            )
            db.add(stock)
        
        db.flush()

        # 4. Create Transaction Log
        transaction = StockTransaction(
            material_id=transit.material_id,
            location_id=req_item.location_id,
            price_version_id=pv.id,
            transaction_type="inbound",
            quantity_change=req_item.inbound_quantity,
            balance=stock.quantity,
            reference_order=order_no,
            operator_id=req.operator_id
        )
        db.add(transaction)
        
        # 5. Update Transit Quantity
        transit.received_quantity = (transit.received_quantity or 0) + req_item.inbound_quantity
        transit.quantity -= req_item.inbound_quantity
        if transit.quantity <= 0:
            db.delete(transit)
        
    db.query(TransitInventory).filter(
        TransitInventory.box_no == req.box_no,
        (TransitInventory.quantity <= 0) | (TransitInventory.status == 'received')
    ).delete(synchronize_session=False)

    db.commit()
    return {"message": "Inbound from transit successful"}

@router.post("/inbound/bulk")
def create_bulk_inbound_order(order_in: InboundOrderCreate, db: Session = Depends(get_db)):
    if not order_in.items:
        raise HTTPException(status_code=400, detail="Order items cannot be empty")

    for item in order_in.items:
        # Ensure a valid price version exists
        valid_pv_id = ensure_default_price_version(db, item.material_id, item)

        # 1. Create Inbound Order
        order = InboundOrder(
            order_no=f"{order_in.order_no}-{item.material_id}-{item.location_id}", # Append IDs to ensure uniqueness per item
            material_id=item.material_id,
            price_version_id=valid_pv_id,
            location_id=item.location_id,
            quantity=item.quantity,
            contract_no=item.contract_no,
            operator_id=order_in.operator_id,
            status="completed",
            inbound_time=datetime.utcnow()
        )
        db.add(order)
        
        # 3. Update Stock
        stock = db.query(Stock).filter(
            Stock.material_id == item.material_id,
            Stock.location_id == item.location_id,
            Stock.price_version_id == valid_pv_id
        ).first()

        if stock:
            stock.quantity += item.quantity
            stock.total_inbound += item.quantity
        else:
            stock = Stock(
                material_id=item.material_id,
                location_id=item.location_id,
                price_version_id=valid_pv_id,
                quantity=item.quantity,
                total_inbound=item.quantity,
                total_outbound=0
            )
            db.add(stock)
        
        db.flush()

        # 3. Create Transaction Log
        transaction = StockTransaction(
            material_id=item.material_id,
            location_id=item.location_id,
            price_version_id=valid_pv_id,
            transaction_type="inbound",
            quantity_change=item.quantity,
            balance=stock.quantity,
            reference_order=order_in.order_no,
            operator_id=order_in.operator_id
        )
        db.add(transaction)
    
    db.commit()
    return {"message": "Bulk inbound order created successfully"}

@router.post("/outbound/bulk")
def create_bulk_outbound_order(order_in: OutboundOrderCreate, db: Session = Depends(get_db)):
    if not order_in.items:
        raise HTTPException(status_code=400, detail="Order items cannot be empty")

    today = datetime.utcnow().strftime("%Y%m%d")
    if order_in.order_no:
        group_no = order_in.order_no
    else:
        prefix = f"OUT-{today}-"
        last = db.query(OutboundOrder.group_no).filter(
            OutboundOrder.group_no.ilike(f"{prefix}%")
        ).order_by(desc(OutboundOrder.group_no)).first()
        if last and last[0]:
            try:
                last_seq = int(str(last[0]).split("-")[-1])
            except Exception:
                last_seq = 0
        else:
            last_seq = 0
        group_no = f"{prefix}{last_seq + 1:03d}"

    line_no = 1
    for item in order_in.items:
        target_material_id = item.actual_material_id if item.actual_material_id else item.material_id
        
        # 1. Check Stock
        stock_query = db.query(Stock).filter(
            Stock.material_id == target_material_id,
            Stock.location_id == item.location_id
        )
        
        # If the frontend passes sale_price, we should find the corresponding price version to deduct
        if item.sale_price is not None:
            pv = db.query(MaterialPriceVersion).filter(
                MaterialPriceVersion.material_id == target_material_id,
                MaterialPriceVersion.sale_price == item.sale_price,
                MaterialPriceVersion.currency == (item.currency or "CNY")
            ).first()
            if pv:
                stock_query = stock_query.filter(Stock.price_version_id == pv.id)
            else:
                # If for some reason we can't find exact match, we just use the default query without price filter
                pass

        stock = stock_query.filter(Stock.quantity >= item.quantity).with_for_update().first()
        
        if not stock:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Insufficient stock for material {target_material_id} at location {item.location_id}")

        valid_pv_id = stock.price_version_id

        # 2. Create Outbound Order
        order = OutboundOrder(
            order_no=f"{group_no}-{line_no:03d}",
            group_no=group_no,
            material_id=target_material_id,
            price_version_id=valid_pv_id,
            location_id=item.location_id,
            quantity=item.quantity,
            customer=order_in.customer,
            receiver=order_in.receiver,
            operator_id=order_in.operator_id,
            status="completed",
            outbound_time=datetime.utcnow()
        )
        db.add(order)
        line_no += 1
        
        # 3. Deduct Stock
        stock.quantity -= item.quantity
        if stock.total_outbound is None:
            stock.total_outbound = 0
        stock.total_outbound += item.quantity
        
        db.flush()

        # 4. Create Transaction Log
        transaction = StockTransaction(
            material_id=target_material_id,
            location_id=item.location_id,
            price_version_id=valid_pv_id,
            transaction_type="outbound",
            quantity_change=-item.quantity,
            balance=stock.quantity,
            reference_order=group_no,
            operator_id=order_in.operator_id
        )
        db.add(transaction)
    
    db.commit()
    return {"message": "Bulk outbound order created successfully", "order_no": group_no}
