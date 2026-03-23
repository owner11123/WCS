from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.models.stock import Stock, StockTransaction
from app.models.user import User
from app.models.material import Material, MaterialPriceVersion
from app.models.location import Location
from app.schemas.stock import StockDetail

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_inventory(skip: int = 0, limit: int = 1000, material_code: str = None, location_code: str = None, q: str = None, db: Session = Depends(get_db)):
    # Subquery to calculate total check diffs (check_in - check_out) per material/location/price_version
    check_diff_subq = db.query(
        StockTransaction.material_id,
        StockTransaction.location_id,
        StockTransaction.price_version_id,
        func.sum(StockTransaction.quantity_change).label('total_diff')
    ).filter(
        StockTransaction.transaction_type.in_(['check_in', 'check_out'])
    ).group_by(
        StockTransaction.material_id,
        StockTransaction.location_id,
        StockTransaction.price_version_id
    ).subquery()

    borrow_diff_subq = db.query(
        StockTransaction.material_id,
        StockTransaction.location_id,
        StockTransaction.price_version_id,
        func.sum(StockTransaction.quantity_change).label('total_borrow')
    ).filter(
        StockTransaction.transaction_type.in_(['borrow_out', 'borrow_return'])
    ).group_by(
        StockTransaction.material_id,
        StockTransaction.location_id,
        StockTransaction.price_version_id
    ).subquery()

    query = db.query(
        Stock.id,
        Stock.material_id,
        Stock.location_id,
        Stock.price_version_id,
        Stock.quantity,
        Stock.total_inbound,
        Stock.total_outbound,
        Material.code.label('material_code'),
        Material.description.label('material_description'),
        Location.code.label('location_code'),
        Location.code.label('location_name'),
        MaterialPriceVersion.purchase_price,
        MaterialPriceVersion.sale_price,
        MaterialPriceVersion.currency,
        MaterialPriceVersion.batch_no.label('batch_no'),
        check_diff_subq.c.total_diff.label('check_diff'),
        borrow_diff_subq.c.total_borrow.label('borrow_diff')
    ).join(
        Material, Stock.material_id == Material.id
    ).join(
        Location, Stock.location_id == Location.id
    ).join(
        MaterialPriceVersion, Stock.price_version_id == MaterialPriceVersion.id
    ).outerjoin(
        check_diff_subq,
        (Stock.material_id == check_diff_subq.c.material_id) &
        (Stock.location_id == check_diff_subq.c.location_id) &
        (Stock.price_version_id == check_diff_subq.c.price_version_id)
    ).outerjoin(
        borrow_diff_subq,
        (Stock.material_id == borrow_diff_subq.c.material_id) &
        (Stock.location_id == borrow_diff_subq.c.location_id) &
        (Stock.price_version_id == borrow_diff_subq.c.price_version_id)
    ).filter(
        Stock.quantity > 0
    )

    if q:
        kw = q.strip()
        if kw:
            query = query.filter(
                or_(
                    Material.code.ilike(f"%{kw}%"),
                    Material.description.ilike(f"%{kw}%"),
                    Location.code.ilike(f"%{kw}%")
                )
            )
    elif material_code:
        query = query.filter(Material.code.ilike(f"%{material_code}%") | Material.description.ilike(f"%{material_code}%"))
    if location_code and (not q):
        query = query.filter(Location.code.ilike(f"%{location_code}%"))

    total = query.count()
    results = query.offset(skip).limit(limit).all()

    # Format the results to match StockDetail schema
    formatted_results = []
    for r in results:
        formatted_results.append({
            "id": r.id,
            "material_id": r.material_id,
            "location_id": r.location_id,
            "price_version_id": r.price_version_id,
            "quantity": r.quantity,
            "total_inbound": r.total_inbound,
            "total_outbound": r.total_outbound,
            "material_code": r.material_code,
            "material_description": r.material_description,
            "location_code": r.location_code,
            "location_name": r.location_name,
            "purchase_price": float(r.purchase_price) if r.purchase_price else None,
            "sale_price": float(r.sale_price) if r.sale_price else None,
            "currency": r.currency,
            "batch_no": r.batch_no,
            "check_diff": int(r.check_diff) if r.check_diff else 0,
            "borrow": int(r.borrow_diff) if r.borrow_diff else 0
        })

    return {
        "total": total,
        "items": formatted_results
    }

@router.get("/transactions")
def get_transactions(skip: int = 0, limit: int = 20, transaction_type: str = None, material_code: str = None, start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    query = db.query(
        StockTransaction.id,
        StockTransaction.transaction_type,
        StockTransaction.quantity_change,
        StockTransaction.balance,
        StockTransaction.reference_order,
        StockTransaction.created_at.label('transaction_time'),
        User.username.label('operator_name'),
        Material.code.label('material_code'),
        Material.description.label('material_description'),
        Location.code.label('location_code'),
        MaterialPriceVersion.batch_no.label('batch_no')
    ).join(
        Material, StockTransaction.material_id == Material.id
    ).join(
        Location, StockTransaction.location_id == Location.id
    ).outerjoin(
        User, StockTransaction.operator_id == User.id
    ).outerjoin(
        MaterialPriceVersion, StockTransaction.price_version_id == MaterialPriceVersion.id
    )

    if transaction_type:
        query = query.filter(StockTransaction.transaction_type == transaction_type)
    if material_code:
        query = query.filter(Material.code.ilike(f"%{material_code}%") | Material.description.ilike(f"%{material_code}%"))
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(StockTransaction.created_at >= start_dt)
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(StockTransaction.created_at < end_dt)

    total = query.count()
    results = query.order_by(StockTransaction.created_at.desc()).offset(skip).limit(limit).all()

    formatted_results = []
    for r in results:
        formatted_results.append({
            "id": r.id,
            "transaction_type": r.transaction_type,
            "quantity_change": r.quantity_change,
            "balance": r.balance,
            "reference_order": r.reference_order,
            "transaction_time": r.transaction_time,
            "operator_name": r.operator_name,
            "material_code": r.material_code,
            "material_description": r.material_description,
            "location_code": r.location_code,
            "batch_no": r.batch_no
        })

    return {
        "total": total,
        "items": formatted_results
    }
