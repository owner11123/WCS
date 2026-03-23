from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.models.borrow import BorrowOrder, BorrowItem
from app.models.stock import Stock, StockTransaction
from app.models.user import User
from app.models.material import Material, MaterialPriceVersion
from app.models.location import Location
from app.schemas.borrow import BorrowOrderCreate, BorrowReturnRequest, BorrowOrder as BorrowOrderSchema
from app.api import deps


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_borrow_no(db: Session) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"BORROW-{today}-"
    last = db.query(BorrowOrder.borrow_no).filter(
        BorrowOrder.borrow_no.ilike(f"{prefix}%")
    ).order_by(desc(BorrowOrder.borrow_no)).first()
    if last and last[0]:
        try:
            last_seq = int(str(last[0]).split("-")[-1])
        except Exception:
            last_seq = 0
    else:
        last_seq = 0
    return f"{prefix}{last_seq + 1:03d}"


@router.get("/orders")
def list_borrow_orders(skip: int = 0, limit: int = 20, status: str = None, borrower: str = None, start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    q = db.query(BorrowOrder).order_by(BorrowOrder.borrow_time.desc())
    if status:
        q = q.filter(BorrowOrder.status == status)
    if borrower:
        q = q.filter(BorrowOrder.borrower.ilike(f"%{borrower}%"))
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        q = q.filter(BorrowOrder.borrow_time >= start_dt)
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        q = q.filter(BorrowOrder.borrow_time < end_dt)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return {"total": total, "items": items}


@router.get("/orders/{borrow_no}", response_model=BorrowOrderSchema)
def get_borrow_order(borrow_no: str, db: Session = Depends(get_db)):
    order = db.query(BorrowOrder).options(joinedload(BorrowOrder.items)).filter(BorrowOrder.borrow_no == borrow_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="Borrow order not found")
    return order


@router.post("/orders")
def create_borrow_order(req: BorrowOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)):
    if not req.items:
        raise HTTPException(status_code=400, detail="Items cannot be empty")

    operator_id = current_user.id
    borrow_no = generate_borrow_no(db)
    order = BorrowOrder(
        borrow_no=borrow_no,
        borrower=req.borrower,
        borrower_unit=req.borrower_unit,
        remark=req.remark,
        status="open",
        operator_id=operator_id,
        borrow_time=datetime.utcnow()
    )
    db.add(order)
    db.flush()

    for it in req.items:
        if it.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be > 0")

        stock = db.query(Stock).filter(
            Stock.material_id == it.material_id,
            Stock.location_id == it.location_id,
            Stock.price_version_id == it.price_version_id,
            Stock.quantity >= it.quantity
        ).with_for_update().first()
        if not stock:
            raise HTTPException(status_code=400, detail="Insufficient stock for borrow")

        stock.quantity -= it.quantity
        stock.total_outbound = (stock.total_outbound or 0) + it.quantity
        db.flush()

        tx = StockTransaction(
            material_id=it.material_id,
            location_id=it.location_id,
            price_version_id=it.price_version_id,
            transaction_type="borrow_out",
            quantity_change=-it.quantity,
            balance=stock.quantity,
            reference_order=borrow_no,
            operator_id=operator_id
        )
        db.add(tx)

        item = BorrowItem(
            borrow_order_id=order.id,
            material_id=it.material_id,
            location_id=it.location_id,
            price_version_id=it.price_version_id,
            quantity=it.quantity,
            returned_quantity=0,
            status="open"
        )
        db.add(item)

    db.commit()
    return {"message": "Borrow order created successfully", "borrow_no": borrow_no}


@router.post("/orders/{borrow_no}/return")
def return_borrow_order(borrow_no: str, req: BorrowReturnRequest, db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)):
    operator_id = current_user.id
    order = db.query(BorrowOrder).filter(BorrowOrder.borrow_no == borrow_no).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Borrow order not found")
    if order.status != "open":
        raise HTTPException(status_code=400, detail="Borrow order is not open")
    if not req.items:
        raise HTTPException(status_code=400, detail="Return items cannot be empty")

    item_ids = [x.borrow_item_id for x in req.items]
    items = db.query(BorrowItem).filter(BorrowItem.borrow_order_id == order.id, BorrowItem.id.in_(item_ids)).with_for_update().all()
    items_by_id = {x.id: x for x in items}
    if len(items_by_id) != len(set(item_ids)):
        raise HTTPException(status_code=400, detail="Invalid borrow_item_id")

    for rit in req.items:
        bi = items_by_id.get(rit.borrow_item_id)
        if not bi:
            raise HTTPException(status_code=400, detail="Invalid borrow_item_id")
        if rit.return_quantity <= 0:
            raise HTTPException(status_code=400, detail="Return quantity must be > 0")
        remaining = bi.quantity - (bi.returned_quantity or 0)
        if rit.return_quantity > remaining:
            raise HTTPException(status_code=400, detail="Return quantity exceeds remaining")

        target_location_id = rit.location_id or bi.location_id
        stock = db.query(Stock).filter(
            Stock.material_id == bi.material_id,
            Stock.location_id == target_location_id,
            Stock.price_version_id == bi.price_version_id
        ).with_for_update().first()
        if stock:
            stock.quantity += rit.return_quantity
            stock.total_inbound = (stock.total_inbound or 0) + rit.return_quantity
        else:
            stock = Stock(
                material_id=bi.material_id,
                location_id=target_location_id,
                price_version_id=bi.price_version_id,
                quantity=rit.return_quantity,
                total_inbound=rit.return_quantity,
                total_outbound=0
            )
            db.add(stock)
        db.flush()

        tx = StockTransaction(
            material_id=bi.material_id,
            location_id=target_location_id,
            price_version_id=bi.price_version_id,
            transaction_type="borrow_return",
            quantity_change=rit.return_quantity,
            balance=stock.quantity,
            reference_order=borrow_no,
            operator_id=operator_id
        )
        db.add(tx)

        bi.returned_quantity = (bi.returned_quantity or 0) + rit.return_quantity
        if bi.returned_quantity >= bi.quantity:
            bi.status = "closed"

    db.flush()
    open_count = db.query(BorrowItem).filter(BorrowItem.borrow_order_id == order.id, BorrowItem.status == "open").count()
    if open_count == 0:
        order.status = "closed"

    db.commit()
    return {"message": "Borrow return processed successfully", "borrow_no": borrow_no, "status": order.status}


@router.delete("/orders/{borrow_no}")
def delete_borrow_order(borrow_no: str, db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)):
    operator_id = current_user.id
    order = db.query(BorrowOrder).filter(BorrowOrder.borrow_no == borrow_no).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Borrow order not found")
    if order.status != "open":
        raise HTTPException(status_code=400, detail="Only open borrow order can be deleted")

    items = db.query(BorrowItem).filter(BorrowItem.borrow_order_id == order.id).with_for_update().all()
    if not items:
        db.delete(order)
        db.commit()
        return {"message": "Borrow order deleted", "borrow_no": borrow_no}

    for it in items:
        if (it.returned_quantity or 0) > 0:
            raise HTTPException(status_code=400, detail="Borrow order with returned items cannot be deleted")

    for it in items:
        stock = db.query(Stock).filter(
            Stock.material_id == it.material_id,
            Stock.location_id == it.location_id,
            Stock.price_version_id == it.price_version_id
        ).with_for_update().first()
        if stock:
            stock.quantity += it.quantity
            stock.total_outbound = max((stock.total_outbound or 0) - it.quantity, 0)
            db.flush()
            db.add(StockTransaction(
                material_id=it.material_id,
                location_id=it.location_id,
                price_version_id=it.price_version_id,
                transaction_type="borrow_cancel",
                quantity_change=it.quantity,
                balance=stock.quantity,
                reference_order=borrow_no,
                operator_id=operator_id
            ))
        else:
            stock = Stock(
                material_id=it.material_id,
                location_id=it.location_id,
                price_version_id=it.price_version_id,
                quantity=it.quantity,
                total_inbound=0,
                total_outbound=0
            )
            db.add(stock)
            db.flush()
            db.add(StockTransaction(
                material_id=it.material_id,
                location_id=it.location_id,
                price_version_id=it.price_version_id,
                transaction_type="borrow_cancel",
                quantity_change=it.quantity,
                balance=stock.quantity,
                reference_order=borrow_no,
                operator_id=operator_id
            ))

    db.delete(order)
    db.commit()
    return {"message": "Borrow order deleted", "borrow_no": borrow_no}
