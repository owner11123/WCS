from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta
import pandas as pd
import io
from urllib.parse import quote

from app.db.session import SessionLocal
from app.models.stock import Stock
from app.models.stock import StockTransaction
from app.models.order import InboundOrder, OutboundOrder
from app.models.material import Material, MaterialPriceVersion
from app.models.transit import TransitInventory


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def parse_start_end(start_date: str, end_date: str):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) if end_date else None
    return start_dt, end_dt


def to_cny(amount: float, currency: str, usd_to_cny: float) -> float:
    if amount is None:
        return 0.0
    cur = (currency or "CNY").upper()
    if cur == "CNY":
        return float(amount)
    if cur == "USD":
        return float(amount) * float(usd_to_cny)
    return float(amount)


def build_summary(items):
    summary = {
        "contract_no": "汇总",
        "category_major": "汇总",
        "vehicle_model": "汇总",
        "inbound_qty": 0,
        "inbound_amount_cny": 0.0,
        "outbound_qty": 0,
        "outbound_amount_cny": 0.0,
        "stock_qty": 0,
        "stock_amount_cny": 0.0,
        "transit_qty": 0,
        "transit_amount_cny": 0.0
    }
    for x in items:
        summary["inbound_qty"] += int(x.get("inbound_qty") or 0)
        summary["inbound_amount_cny"] += float(x.get("inbound_amount_cny") or 0)
        summary["outbound_qty"] += int(x.get("outbound_qty") or 0)
        summary["outbound_amount_cny"] += float(x.get("outbound_amount_cny") or 0)
        summary["stock_qty"] += int(x.get("stock_qty") or 0)
        summary["stock_amount_cny"] += float(x.get("stock_amount_cny") or 0)
        summary["transit_qty"] += int(x.get("transit_qty") or 0)
        summary["transit_amount_cny"] += float(x.get("transit_amount_cny") or 0)
    summary["inbound_amount_cny"] = round(summary["inbound_amount_cny"], 2)
    summary["outbound_amount_cny"] = round(summary["outbound_amount_cny"], 2)
    summary["stock_amount_cny"] = round(summary["stock_amount_cny"], 2)
    summary["transit_amount_cny"] = round(summary["transit_amount_cny"], 2)
    return summary


def contract_stock_amount(db: Session, usd_to_cny: float):
    rows = db.query(
        MaterialPriceVersion.batch_no.label("contract_no"),
        MaterialPriceVersion.currency.label("currency"),
        func.sum(Stock.quantity).label("qty"),
        func.sum(Stock.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(
        MaterialPriceVersion, Stock.price_version_id == MaterialPriceVersion.id
    ).filter(
        Stock.quantity > 0
    ).group_by(
        MaterialPriceVersion.batch_no,
        MaterialPriceVersion.currency
    ).all()
    by_contract = {}
    for r in rows:
        key = r.contract_no or "DEFAULT"
        by_contract.setdefault(key, {"stock_qty": 0, "stock_amount_cny": 0.0})
        by_contract[key]["stock_qty"] += int(r.qty or 0)
        by_contract[key]["stock_amount_cny"] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)
    return by_contract


def contract_inout_amount(db: Session, start_dt, end_dt, usd_to_cny: float):
    inbound_q = db.query(
        MaterialPriceVersion.batch_no.label("contract_no"),
        MaterialPriceVersion.currency.label("currency"),
        func.sum(InboundOrder.quantity).label("qty"),
        func.sum(InboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(
        MaterialPriceVersion, InboundOrder.price_version_id == MaterialPriceVersion.id
    )
    if start_dt:
        inbound_q = inbound_q.filter(InboundOrder.inbound_time >= start_dt)
    if end_dt:
        inbound_q = inbound_q.filter(InboundOrder.inbound_time < end_dt)
    inbound_rows = inbound_q.group_by(MaterialPriceVersion.batch_no, MaterialPriceVersion.currency).all()

    outbound_q = db.query(
        MaterialPriceVersion.batch_no.label("contract_no"),
        MaterialPriceVersion.currency.label("currency"),
        func.sum(OutboundOrder.quantity).label("qty"),
        func.sum(OutboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(
        MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id
    )
    if start_dt:
        outbound_q = outbound_q.filter(OutboundOrder.outbound_time >= start_dt)
    if end_dt:
        outbound_q = outbound_q.filter(OutboundOrder.outbound_time < end_dt)
    outbound_rows = outbound_q.group_by(MaterialPriceVersion.batch_no, MaterialPriceVersion.currency).all()

    inbound_by = {}
    for r in inbound_rows:
        key = r.contract_no or "DEFAULT"
        inbound_by.setdefault(key, {"inbound_qty": 0, "inbound_amount_cny": 0.0})
        inbound_by[key]["inbound_qty"] += int(r.qty or 0)
        inbound_by[key]["inbound_amount_cny"] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    outbound_by = {}
    for r in outbound_rows:
        key = r.contract_no or "DEFAULT"
        outbound_by.setdefault(key, {"outbound_qty": 0, "outbound_amount_cny": 0.0})
        outbound_by[key]["outbound_qty"] += int(r.qty or 0)
        outbound_by[key]["outbound_amount_cny"] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    return inbound_by, outbound_by


def contract_transit_amount(db: Session, usd_to_cny: float):
    rows = db.query(
        TransitInventory.contract_no.label("contract_no"),
        TransitInventory.currency.label("currency"),
        func.sum(TransitInventory.quantity).label("qty"),
        func.sum(TransitInventory.quantity * TransitInventory.sale_price).label("amt")
    ).filter(
        TransitInventory.status == "in_transit",
        TransitInventory.quantity > 0
    ).group_by(
        TransitInventory.contract_no,
        TransitInventory.currency
    ).all()

    by_contract = {}
    for r in rows:
        key = r.contract_no or "DEFAULT"
        by_contract.setdefault(key, {"transit_qty": 0, "transit_amount_cny": 0.0})
        by_contract[key]["transit_qty"] += int(r.qty or 0)
        by_contract[key]["transit_amount_cny"] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)
    return by_contract


@router.get("/stock-amount/by-contract")
def stock_amount_by_contract(start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    start_dt, end_dt = parse_start_end(start_date, end_date)
    inbound_by, outbound_by = contract_inout_amount(db, start_dt, end_dt, usd_to_cny)
    stock_by = contract_stock_amount(db, usd_to_cny)
    transit_by = contract_transit_amount(db, usd_to_cny)

    contracts = set(inbound_by.keys()) | set(outbound_by.keys()) | set(stock_by.keys()) | set(transit_by.keys())
    items = []
    for c in sorted(list(contracts)):
        row = {
            "contract_no": c,
            "inbound_qty": inbound_by.get(c, {}).get("inbound_qty", 0),
            "inbound_amount_cny": round(inbound_by.get(c, {}).get("inbound_amount_cny", 0.0), 2),
            "outbound_qty": outbound_by.get(c, {}).get("outbound_qty", 0),
            "outbound_amount_cny": round(outbound_by.get(c, {}).get("outbound_amount_cny", 0.0), 2),
            "stock_qty": stock_by.get(c, {}).get("stock_qty", 0),
            "stock_amount_cny": round(stock_by.get(c, {}).get("stock_amount_cny", 0.0), 2),
            "transit_qty": transit_by.get(c, {}).get("transit_qty", 0),
            "transit_amount_cny": round(transit_by.get(c, {}).get("transit_amount_cny", 0.0), 2)
        }
        items.append(row)

    return {
        "usd_to_cny": usd_to_cny,
        "start_date": start_date,
        "end_date": end_date,
        "items": items,
        "summary": build_summary(items)
    }


@router.get("/stock-amount/by-category")
def stock_amount_by_category(start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    start_dt, end_dt = parse_start_end(start_date, end_date)

    inbound_rows = db.query(
        Material.category_major.label("category_major"),
        MaterialPriceVersion.currency.label("currency"),
        func.sum(InboundOrder.quantity).label("qty"),
        func.sum(InboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(Material, InboundOrder.material_id == Material.id).join(MaterialPriceVersion, InboundOrder.price_version_id == MaterialPriceVersion.id)
    if start_dt:
        inbound_rows = inbound_rows.filter(InboundOrder.inbound_time >= start_dt)
    if end_dt:
        inbound_rows = inbound_rows.filter(InboundOrder.inbound_time < end_dt)
    inbound_rows = inbound_rows.group_by(Material.category_major, MaterialPriceVersion.currency).all()

    outbound_rows = db.query(
        Material.category_major.label("category_major"),
        MaterialPriceVersion.currency.label("currency"),
        func.sum(OutboundOrder.quantity).label("qty"),
        func.sum(OutboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(Material, OutboundOrder.material_id == Material.id).join(MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id)
    if start_dt:
        outbound_rows = outbound_rows.filter(OutboundOrder.outbound_time >= start_dt)
    if end_dt:
        outbound_rows = outbound_rows.filter(OutboundOrder.outbound_time < end_dt)
    outbound_rows = outbound_rows.group_by(Material.category_major, MaterialPriceVersion.currency).all()

    stock_rows = db.query(
        Material.category_major.label("category_major"),
        MaterialPriceVersion.currency.label("currency"),
        func.sum(Stock.quantity).label("qty"),
        func.sum(Stock.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(Material, Stock.material_id == Material.id).join(MaterialPriceVersion, Stock.price_version_id == MaterialPriceVersion.id).filter(Stock.quantity > 0)
    stock_rows = stock_rows.group_by(Material.category_major, MaterialPriceVersion.currency).all()

    transit_rows = db.query(
        Material.category_major.label("category_major"),
        TransitInventory.currency.label("currency"),
        func.sum(TransitInventory.quantity).label("qty"),
        func.sum(TransitInventory.quantity * TransitInventory.sale_price).label("amt")
    ).join(Material, TransitInventory.material_id == Material.id).filter(TransitInventory.status == "in_transit", TransitInventory.quantity > 0)
    transit_rows = transit_rows.group_by(Material.category_major, TransitInventory.currency).all()

    def key_name(x):
        return x or "未分类"

    inbound_by = {}
    for r in inbound_rows:
        k = key_name(r.category_major)
        inbound_by.setdefault(k, {"inbound_qty": 0, "inbound_amount_cny": 0.0})
        inbound_by[k]["inbound_qty"] += int(r.qty or 0)
        inbound_by[k]["inbound_amount_cny"] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    outbound_by = {}
    for r in outbound_rows:
        k = key_name(r.category_major)
        outbound_by.setdefault(k, {"outbound_qty": 0, "outbound_amount_cny": 0.0})
        outbound_by[k]["outbound_qty"] += int(r.qty or 0)
        outbound_by[k]["outbound_amount_cny"] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    stock_by = {}
    for r in stock_rows:
        k = key_name(r.category_major)
        stock_by.setdefault(k, {"stock_qty": 0, "stock_amount_cny": 0.0})
        stock_by[k]["stock_qty"] += int(r.qty or 0)
        stock_by[k]["stock_amount_cny"] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    transit_by = {}
    for r in transit_rows:
        k = key_name(r.category_major)
        transit_by.setdefault(k, {"transit_qty": 0, "transit_amount_cny": 0.0})
        transit_by[k]["transit_qty"] += int(r.qty or 0)
        transit_by[k]["transit_amount_cny"] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    categories = set(inbound_by.keys()) | set(outbound_by.keys()) | set(stock_by.keys()) | set(transit_by.keys())
    items = []
    for k in sorted(list(categories)):
        items.append({
            "category_major": k,
            "inbound_qty": inbound_by.get(k, {}).get("inbound_qty", 0),
            "inbound_amount_cny": round(inbound_by.get(k, {}).get("inbound_amount_cny", 0.0), 2),
            "outbound_qty": outbound_by.get(k, {}).get("outbound_qty", 0),
            "outbound_amount_cny": round(outbound_by.get(k, {}).get("outbound_amount_cny", 0.0), 2),
            "stock_qty": stock_by.get(k, {}).get("stock_qty", 0),
            "stock_amount_cny": round(stock_by.get(k, {}).get("stock_amount_cny", 0.0), 2),
            "transit_qty": transit_by.get(k, {}).get("transit_qty", 0),
            "transit_amount_cny": round(transit_by.get(k, {}).get("transit_amount_cny", 0.0), 2)
        })

    return {
        "usd_to_cny": usd_to_cny,
        "start_date": start_date,
        "end_date": end_date,
        "items": items,
        "summary": build_summary(items)
    }


@router.get("/vehicle-amount")
def vehicle_amount(start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    start_dt, end_dt = parse_start_end(start_date, end_date)

    inbound_rows = db.query(
        Material.vehicle_model.label("vehicle_model"),
        MaterialPriceVersion.batch_no.label("contract_no"),
        MaterialPriceVersion.currency.label("currency"),
        func.sum(InboundOrder.quantity).label("qty"),
        func.sum(InboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(Material, InboundOrder.material_id == Material.id).join(MaterialPriceVersion, InboundOrder.price_version_id == MaterialPriceVersion.id)
    if start_dt:
        inbound_rows = inbound_rows.filter(InboundOrder.inbound_time >= start_dt)
    if end_dt:
        inbound_rows = inbound_rows.filter(InboundOrder.inbound_time < end_dt)
    inbound_rows = inbound_rows.group_by(Material.vehicle_model, MaterialPriceVersion.batch_no, MaterialPriceVersion.currency).all()

    outbound_rows = db.query(
        Material.vehicle_model.label("vehicle_model"),
        MaterialPriceVersion.batch_no.label("contract_no"),
        MaterialPriceVersion.currency.label("currency"),
        func.sum(OutboundOrder.quantity).label("qty"),
        func.sum(OutboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(Material, OutboundOrder.material_id == Material.id).join(MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id)
    if start_dt:
        outbound_rows = outbound_rows.filter(OutboundOrder.outbound_time >= start_dt)
    if end_dt:
        outbound_rows = outbound_rows.filter(OutboundOrder.outbound_time < end_dt)
    outbound_rows = outbound_rows.group_by(Material.vehicle_model, MaterialPriceVersion.batch_no, MaterialPriceVersion.currency).all()

    stock_rows = db.query(
        Material.vehicle_model.label("vehicle_model"),
        MaterialPriceVersion.batch_no.label("contract_no"),
        MaterialPriceVersion.currency.label("currency"),
        func.sum(Stock.quantity).label("qty"),
        func.sum(Stock.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(Material, Stock.material_id == Material.id).join(MaterialPriceVersion, Stock.price_version_id == MaterialPriceVersion.id).filter(Stock.quantity > 0)
    stock_rows = stock_rows.group_by(Material.vehicle_model, MaterialPriceVersion.batch_no, MaterialPriceVersion.currency).all()

    def vname(x):
        return x or "未维护车型"

    def cname(x):
        return x or "DEFAULT"

    inbound_by = {}
    for r in inbound_rows:
        k = (vname(r.vehicle_model), cname(r.contract_no))
        inbound_by.setdefault(k, {"inbound_qty": 0, "inbound_amount_cny": 0.0})
        inbound_by[k]["inbound_qty"] += int(r.qty or 0)
        inbound_by[k]["inbound_amount_cny"] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    outbound_by = {}
    for r in outbound_rows:
        k = (vname(r.vehicle_model), cname(r.contract_no))
        outbound_by.setdefault(k, {"outbound_qty": 0, "outbound_amount_cny": 0.0})
        outbound_by[k]["outbound_qty"] += int(r.qty or 0)
        outbound_by[k]["outbound_amount_cny"] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    stock_by = {}
    for r in stock_rows:
        k = (vname(r.vehicle_model), cname(r.contract_no))
        stock_by.setdefault(k, {"stock_qty": 0, "stock_amount_cny": 0.0})
        stock_by[k]["stock_qty"] += int(r.qty or 0)
        stock_by[k]["stock_amount_cny"] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    keys = set(inbound_by.keys()) | set(outbound_by.keys()) | set(stock_by.keys())
    items = []
    for (vehicle_model, contract_no) in sorted(list(keys), key=lambda x: (x[0], x[1])):
        items.append({
            "vehicle_model": vehicle_model,
            "contract_no": contract_no,
            "inbound_qty": inbound_by.get((vehicle_model, contract_no), {}).get("inbound_qty", 0),
            "inbound_amount_cny": round(inbound_by.get((vehicle_model, contract_no), {}).get("inbound_amount_cny", 0.0), 2),
            "outbound_qty": outbound_by.get((vehicle_model, contract_no), {}).get("outbound_qty", 0),
            "outbound_amount_cny": round(outbound_by.get((vehicle_model, contract_no), {}).get("outbound_amount_cny", 0.0), 2),
            "stock_qty": stock_by.get((vehicle_model, contract_no), {}).get("stock_qty", 0),
            "stock_amount_cny": round(stock_by.get((vehicle_model, contract_no), {}).get("stock_amount_cny", 0.0), 2)
        })

    summary = {
        "vehicle_model": "汇总",
        "contract_no": "",
        "inbound_qty": 0,
        "inbound_amount_cny": 0.0,
        "outbound_qty": 0,
        "outbound_amount_cny": 0.0,
        "stock_qty": 0,
        "stock_amount_cny": 0.0
    }
    for x in items:
        summary["inbound_qty"] += int(x.get("inbound_qty") or 0)
        summary["inbound_amount_cny"] += float(x.get("inbound_amount_cny") or 0)
        summary["outbound_qty"] += int(x.get("outbound_qty") or 0)
        summary["outbound_amount_cny"] += float(x.get("outbound_amount_cny") or 0)
        summary["stock_qty"] += int(x.get("stock_qty") or 0)
        summary["stock_amount_cny"] += float(x.get("stock_amount_cny") or 0)
    summary["inbound_amount_cny"] = round(summary["inbound_amount_cny"], 2)
    summary["outbound_amount_cny"] = round(summary["outbound_amount_cny"], 2)
    summary["stock_amount_cny"] = round(summary["stock_amount_cny"], 2)

    return {
        "usd_to_cny": usd_to_cny,
        "start_date": start_date,
        "end_date": end_date,
        "items": items,
        "summary": summary
    }


@router.get("/vehicle-amount/pivot")
def vehicle_amount_pivot(start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    data = vehicle_amount(start_date=start_date, end_date=end_date, usd_to_cny=usd_to_cny, db=db)
    items = data["items"]

    vehicles = sorted({x.get("vehicle_model") for x in items if x.get("vehicle_model")})
    contracts = sorted({x.get("contract_no") for x in items if x.get("contract_no")})

    vehicle_defs = []
    for idx, name in enumerate(vehicles):
        vehicle_defs.append({"id": f"v{idx+1}", "name": name})
    vehicle_id_by_name = {x["name"]: x["id"] for x in vehicle_defs}

    rows_by_contract = {}
    for c in contracts:
        row = {"contract_no": c}
        for v in vehicle_defs:
            row[f"{v['id']}_inbound_amount_cny"] = 0.0
            row[f"{v['id']}_outbound_amount_cny"] = 0.0
            row[f"{v['id']}_stock_amount_cny"] = 0.0
        rows_by_contract[c] = row

    for it in items:
        c = it.get("contract_no")
        vname = it.get("vehicle_model")
        if not c or not vname:
            continue
        vid = vehicle_id_by_name.get(vname)
        if not vid:
            continue
        row = rows_by_contract.get(c)
        if not row:
            continue
        row[f"{vid}_inbound_amount_cny"] = float(it.get("inbound_amount_cny") or 0)
        row[f"{vid}_outbound_amount_cny"] = float(it.get("outbound_amount_cny") or 0)
        row[f"{vid}_stock_amount_cny"] = float(it.get("stock_amount_cny") or 0)

    summary_row = {"contract_no": "汇总"}
    for v in vehicle_defs:
        summary_row[f"{v['id']}_inbound_amount_cny"] = 0.0
        summary_row[f"{v['id']}_outbound_amount_cny"] = 0.0
        summary_row[f"{v['id']}_stock_amount_cny"] = 0.0
    for r in rows_by_contract.values():
        for v in vehicle_defs:
            summary_row[f"{v['id']}_inbound_amount_cny"] += float(r.get(f"{v['id']}_inbound_amount_cny") or 0)
            summary_row[f"{v['id']}_outbound_amount_cny"] += float(r.get(f"{v['id']}_outbound_amount_cny") or 0)
            summary_row[f"{v['id']}_stock_amount_cny"] += float(r.get(f"{v['id']}_stock_amount_cny") or 0)
    for v in vehicle_defs:
        summary_row[f"{v['id']}_inbound_amount_cny"] = round(summary_row[f"{v['id']}_inbound_amount_cny"], 2)
        summary_row[f"{v['id']}_outbound_amount_cny"] = round(summary_row[f"{v['id']}_outbound_amount_cny"], 2)
        summary_row[f"{v['id']}_stock_amount_cny"] = round(summary_row[f"{v['id']}_stock_amount_cny"], 2)

    rows = [rows_by_contract[c] for c in contracts]
    rows.append(summary_row)
    return {
        "usd_to_cny": usd_to_cny,
        "start_date": start_date,
        "end_date": end_date,
        "vehicles": vehicle_defs,
        "items": rows
    }


def export_xlsx(rows, filename: str):
    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dashboard")
    output.seek(0)
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"}
    return StreamingResponse(iter([output.getvalue()]), headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@router.get("/kpi")
def dashboard_kpi(usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    stock_rows = db.query(
        MaterialPriceVersion.currency.label("currency"),
        func.sum(Stock.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(
        MaterialPriceVersion, Stock.price_version_id == MaterialPriceVersion.id
    ).filter(
        Stock.quantity > 0
    ).group_by(MaterialPriceVersion.currency).all()

    stock_amount_cny = 0.0
    for r in stock_rows:
        stock_amount_cny += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    transit_rows = db.query(
        TransitInventory.currency.label("currency"),
        func.sum(TransitInventory.quantity * TransitInventory.sale_price).label("amt")
    ).filter(
        TransitInventory.status == "in_transit",
        TransitInventory.quantity > 0
    ).group_by(TransitInventory.currency).all()

    transit_amount_cny = 0.0
    for r in transit_rows:
        transit_amount_cny += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    week_start = func.date_trunc("week", func.now())
    month_start = func.date_trunc("month", func.now())

    week_rows = db.query(
        MaterialPriceVersion.currency.label("currency"),
        func.sum(OutboundOrder.quantity).label("qty"),
        func.sum(OutboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(
        MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id
    ).filter(
        OutboundOrder.outbound_time >= week_start
    ).group_by(MaterialPriceVersion.currency).all()

    week_outbound_qty = 0
    week_outbound_amount_cny = 0.0
    for r in week_rows:
        week_outbound_qty += int(r.qty or 0)
        week_outbound_amount_cny += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    month_rows = db.query(
        MaterialPriceVersion.currency.label("currency"),
        func.sum(OutboundOrder.quantity).label("qty"),
        func.sum(OutboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(
        MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id
    ).filter(
        OutboundOrder.outbound_time >= month_start
    ).group_by(MaterialPriceVersion.currency).all()

    month_outbound_qty = 0
    month_outbound_amount_cny = 0.0
    for r in month_rows:
        month_outbound_qty += int(r.qty or 0)
        month_outbound_amount_cny += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    return {
        "usd_to_cny": usd_to_cny,
        "stock_amount_cny": round(stock_amount_cny, 2),
        "transit_amount_cny": round(transit_amount_cny, 2),
        "total_stock_amount_cny": round(stock_amount_cny + transit_amount_cny, 2),
        "week_outbound_qty": week_outbound_qty,
        "week_outbound_amount_cny": round(week_outbound_amount_cny, 2),
        "month_outbound_qty": month_outbound_qty,
        "month_outbound_amount_cny": round(month_outbound_amount_cny, 2)
    }


@router.get("/stock-age/buckets")
def stock_age_buckets(usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    inbound_first = db.query(
        InboundOrder.price_version_id.label("price_version_id"),
        func.min(InboundOrder.inbound_time).label("first_inbound_time")
    ).group_by(InboundOrder.price_version_id).subquery()

    age_days = func.floor(func.date_part("day", func.now() - inbound_first.c.first_inbound_time))
    bucket = case(
        (age_days <= 30, "0-30天"),
        (age_days <= 60, "31-60天"),
        (age_days <= 90, "61-90天"),
        (age_days <= 180, "91-180天"),
        else_=">180天"
    ).label("bucket")

    rows = db.query(
        bucket,
        MaterialPriceVersion.currency.label("currency"),
        func.sum(Stock.quantity).label("qty"),
        func.sum(Stock.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(
        MaterialPriceVersion, Stock.price_version_id == MaterialPriceVersion.id
    ).join(
        inbound_first, inbound_first.c.price_version_id == Stock.price_version_id
    ).filter(
        Stock.quantity > 0,
        inbound_first.c.first_inbound_time.isnot(None)
    ).group_by(
        bucket, MaterialPriceVersion.currency
    ).all()

    bucket_order = ["0-30天", "31-60天", "61-90天", "91-180天", ">180天"]
    agg = {b: {"bucket": b, "stock_qty": 0, "stock_amount_cny": 0.0} for b in bucket_order}
    for r in rows:
        b = r.bucket
        if b not in agg:
            agg[b] = {"bucket": b, "stock_qty": 0, "stock_amount_cny": 0.0}
        agg[b]["stock_qty"] += int(r.qty or 0)
        agg[b]["stock_amount_cny"] += float(to_cny(float(r.amt or 0), r.currency, usd_to_cny))

    items = []
    for b in bucket_order:
        row = agg[b]
        row["stock_amount_cny"] = round(row["stock_amount_cny"], 2)
        items.append(row)
    return {"usd_to_cny": usd_to_cny, "items": items}


def group_amount_by_currency(rows, usd_to_cny: float):
    total = 0.0
    for r in rows:
        total += to_cny(float(r.amt or 0), r.currency, usd_to_cny)
    return round(total, 2)


def amount_by_dimension(db: Session, dimension_field, usd_to_cny: float, kind: str, start_dt=None, end_dt=None):
    if kind == "inbound":
        q = db.query(
            dimension_field.label("name"),
            MaterialPriceVersion.currency.label("currency"),
            func.sum(InboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
        ).join(Material, InboundOrder.material_id == Material.id).join(MaterialPriceVersion, InboundOrder.price_version_id == MaterialPriceVersion.id)
        if start_dt:
            q = q.filter(InboundOrder.inbound_time >= start_dt)
        if end_dt:
            q = q.filter(InboundOrder.inbound_time < end_dt)
        q = q.group_by(dimension_field, MaterialPriceVersion.currency).all()
    elif kind == "outbound":
        q = db.query(
            dimension_field.label("name"),
            MaterialPriceVersion.currency.label("currency"),
            func.sum(OutboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
        ).join(Material, OutboundOrder.material_id == Material.id).join(MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id)
        if start_dt:
            q = q.filter(OutboundOrder.outbound_time >= start_dt)
        if end_dt:
            q = q.filter(OutboundOrder.outbound_time < end_dt)
        q = q.group_by(dimension_field, MaterialPriceVersion.currency).all()
    elif kind == "stock":
        q = db.query(
            dimension_field.label("name"),
            MaterialPriceVersion.currency.label("currency"),
            func.sum(Stock.quantity * MaterialPriceVersion.sale_price).label("amt")
        ).join(Material, Stock.material_id == Material.id).join(MaterialPriceVersion, Stock.price_version_id == MaterialPriceVersion.id).filter(Stock.quantity > 0)
        q = q.group_by(dimension_field, MaterialPriceVersion.currency).all()
    else:
        return []

    bucket = {}
    for r in q:
        n = r.name or "未分类"
        bucket.setdefault(n, 0.0)
        bucket[n] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    items = [{"name": k, "value": round(v, 2)} for k, v in bucket.items()]
    items.sort(key=lambda x: x["value"], reverse=True)
    return items


@router.get("/stock-amount/total")
def stock_amount_total(usd_to_cny: float = 7.2, contract_no: str = None, db: Session = Depends(get_db)):
    inbound_q = db.query(
        MaterialPriceVersion.currency.label("currency"),
        func.sum(InboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(MaterialPriceVersion, InboundOrder.price_version_id == MaterialPriceVersion.id)
    if contract_no:
        inbound_q = inbound_q.filter(MaterialPriceVersion.batch_no == contract_no)
    inbound_rows = inbound_q.group_by(MaterialPriceVersion.currency).all()

    outbound_q = db.query(
        MaterialPriceVersion.currency.label("currency"),
        func.sum(OutboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id)
    if contract_no:
        outbound_q = outbound_q.filter(MaterialPriceVersion.batch_no == contract_no)
    outbound_rows = outbound_q.group_by(MaterialPriceVersion.currency).all()

    stock_q = db.query(
        MaterialPriceVersion.currency.label("currency"),
        func.sum(Stock.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(MaterialPriceVersion, Stock.price_version_id == MaterialPriceVersion.id).filter(Stock.quantity > 0)
    if contract_no:
        stock_q = stock_q.filter(MaterialPriceVersion.batch_no == contract_no)
    stock_rows = stock_q.group_by(MaterialPriceVersion.currency).all()

    return {
        "usd_to_cny": usd_to_cny,
        "contract_no": contract_no,
        "inbound_amount_cny": group_amount_by_currency(inbound_rows, usd_to_cny),
        "outbound_amount_cny": group_amount_by_currency(outbound_rows, usd_to_cny),
        "stock_amount_cny": group_amount_by_currency(stock_rows, usd_to_cny)
    }


def sum_stock_tx_amount(db: Session, tx_types, usd_to_cny: float, contract_no: str = None):
    q = db.query(
        MaterialPriceVersion.currency.label("currency"),
        func.sum(StockTransaction.quantity_change * MaterialPriceVersion.sale_price).label("amt")
    ).join(
        MaterialPriceVersion, StockTransaction.price_version_id == MaterialPriceVersion.id
    ).filter(
        StockTransaction.transaction_type.in_(tx_types)
    )
    if contract_no:
        q = q.filter(MaterialPriceVersion.batch_no == contract_no)
    rows = q.group_by(MaterialPriceVersion.currency).all()
    return group_amount_by_currency(rows, usd_to_cny)


@router.get("/stock-reconcile/total")
def stock_reconcile_total(usd_to_cny: float = 7.2, contract_no: str = None, db: Session = Depends(get_db)):
    base = stock_amount_total(usd_to_cny=usd_to_cny, contract_no=contract_no, db=db)

    check_net_amount_cny = sum_stock_tx_amount(db, ["check_in", "check_out"], usd_to_cny, contract_no)

    borrow_net = sum_stock_tx_amount(db, ["borrow_out", "borrow_return"], usd_to_cny, contract_no)
    borrow_outstanding_amount_cny = round(max(0.0, -float(borrow_net or 0)), 2)

    inbound_amount = float(base["inbound_amount_cny"] or 0)
    outbound_amount = float(base["outbound_amount_cny"] or 0)
    stock_amount = float(base["stock_amount_cny"] or 0)
    check_amount = float(check_net_amount_cny or 0)

    reconcile_delta = round(inbound_amount - (outbound_amount + stock_amount + borrow_outstanding_amount_cny - check_amount), 2)

    return {
        "usd_to_cny": usd_to_cny,
        "contract_no": contract_no,
        "inbound_amount_cny": round(inbound_amount, 2),
        "outbound_amount_cny": round(outbound_amount, 2),
        "stock_amount_cny": round(stock_amount, 2),
        "borrow_outstanding_amount_cny": borrow_outstanding_amount_cny,
        "check_net_amount_cny": round(check_amount, 2),
        "reconcile_delta_cny": reconcile_delta
    }


@router.get("/stock-amount/topn/by-contract")
def stock_amount_topn_by_contract(n: int = 10, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    data = stock_amount_by_contract(db=db, usd_to_cny=usd_to_cny)
    items = data["items"]
    items.sort(key=lambda x: float(x.get("stock_amount_cny") or 0), reverse=True)
    top = items[: max(1, min(int(n), 50))]
    return {
        "usd_to_cny": usd_to_cny,
        "items": top
    }


@router.get("/stock-amount/contracts")
def stock_amount_contracts(usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    data = stock_amount_by_contract(db=db, usd_to_cny=usd_to_cny)
    contracts = [x["contract_no"] for x in data["items"] if x.get("contract_no")]
    contracts.sort()
    return {"items": contracts}


@router.get("/pie/by-category")
def pie_by_category(usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    return {
        "usd_to_cny": usd_to_cny,
        "inbound": amount_by_dimension(db, Material.category_major, usd_to_cny, "inbound"),
        "outbound": amount_by_dimension(db, Material.category_major, usd_to_cny, "outbound"),
        "stock": amount_by_dimension(db, Material.category_major, usd_to_cny, "stock")
    }


@router.get("/pie/by-vehicle")
def pie_by_vehicle(usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    return {
        "usd_to_cny": usd_to_cny,
        "inbound": amount_by_dimension(db, Material.vehicle_model, usd_to_cny, "inbound"),
        "outbound": amount_by_dimension(db, Material.vehicle_model, usd_to_cny, "outbound"),
        "stock": amount_by_dimension(db, Material.vehicle_model, usd_to_cny, "stock")
    }


@router.get("/outbound-amount/by-month")
def outbound_amount_by_month(months: int = 12, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    m = max(1, min(int(months), 60))
    start_dt = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=31 * (m - 1))

    month_expr = func.to_char(func.date_trunc("month", OutboundOrder.outbound_time), "YYYY-MM")
    rows = db.query(
        month_expr.label("month"),
        MaterialPriceVersion.currency.label("currency"),
        func.sum(OutboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id).filter(
        OutboundOrder.outbound_time >= start_dt
    ).group_by(month_expr, MaterialPriceVersion.currency).all()

    bucket = {}
    for r in rows:
        k = r.month or ""
        bucket.setdefault(k, 0.0)
        bucket[k] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    items = [{"month": k, "outbound_amount_cny": round(v, 2)} for k, v in bucket.items() if k]
    items.sort(key=lambda x: x["month"])
    return {"usd_to_cny": usd_to_cny, "items": items}


@router.get("/export/stock-amount/by-contract")
def export_stock_amount_by_contract(start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    data = stock_amount_by_contract(start_date=start_date, end_date=end_date, usd_to_cny=usd_to_cny, db=db)
    items = data["items"] + [data["summary"]]
    rows = []
    for x in items:
        rows.append({
            "合同号": x["contract_no"],
            "总入库数量": x["inbound_qty"],
            "总入库金额(CNY)": x["inbound_amount_cny"],
            "总出库数量": x["outbound_qty"],
            "总出库金额(CNY)": x["outbound_amount_cny"],
            "剩余库存数量": x["stock_qty"],
            "剩余库存金额(CNY)": x["stock_amount_cny"],
            "在途数量": x["transit_qty"],
            "在途金额(CNY)": x["transit_amount_cny"]
        })
    name = "库存金额_按合同号.xlsx"
    return export_xlsx(rows, name)


@router.get("/export/stock-amount/by-category")
def export_stock_amount_by_category(start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    data = stock_amount_by_category(start_date=start_date, end_date=end_date, usd_to_cny=usd_to_cny, db=db)
    items = data["items"] + [data["summary"]]
    rows = []
    for x in items:
        rows.append({
            "物料大类": x["category_major"],
            "总入库数量": x["inbound_qty"],
            "总入库金额(CNY)": x["inbound_amount_cny"],
            "总出库数量": x["outbound_qty"],
            "总出库金额(CNY)": x["outbound_amount_cny"],
            "剩余库存数量": x["stock_qty"],
            "剩余库存金额(CNY)": x["stock_amount_cny"],
            "在途数量": x["transit_qty"],
            "在途金额(CNY)": x["transit_amount_cny"]
        })
    name = "库存金额_按物料大类.xlsx"
    return export_xlsx(rows, name)


@router.get("/export/vehicle-amount")
def export_vehicle_amount(start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    data = vehicle_amount(start_date=start_date, end_date=end_date, usd_to_cny=usd_to_cny, db=db)
    items = data["items"] + [data["summary"]]
    rows = []
    for x in items:
        rows.append({
            "车型": x["vehicle_model"],
            "合同号": x["contract_no"],
            "总入库数量": x["inbound_qty"],
            "总入库金额(CNY)": x["inbound_amount_cny"],
            "总出库数量": x["outbound_qty"],
            "总出库金额(CNY)": x["outbound_amount_cny"],
            "剩余数量": x["stock_qty"],
            "剩余金额(CNY)": x["stock_amount_cny"]
        })
    name = "车型金额_按车型合同.xlsx"
    return export_xlsx(rows, name)


@router.get("/export/vehicle-amount/pivot")
def export_vehicle_amount_pivot(start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    data = vehicle_amount_pivot(start_date=start_date, end_date=end_date, usd_to_cny=usd_to_cny, db=db)
    vehicles = data["vehicles"]
    items = data["items"]

    rows = []
    for r in items:
        out = {"合同号": r.get("contract_no")}
        for v in vehicles:
            out[f"{v['name']}_入库金额(CNY)"] = r.get(f"{v['id']}_inbound_amount_cny", 0)
            out[f"{v['name']}_出库金额(CNY)"] = r.get(f"{v['id']}_outbound_amount_cny", 0)
            out[f"{v['name']}_剩余金额(CNY)"] = r.get(f"{v['id']}_stock_amount_cny", 0)
        rows.append(out)

    name = "车型金额_按合同号透视.xlsx"
    return export_xlsx(rows, name)


@router.get("/outbound-summary/month-vehicle")
def outbound_summary_month_vehicle(start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    start_dt, end_dt = parse_start_end(start_date, end_date)

    month_expr = func.to_char(func.date_trunc("month", OutboundOrder.outbound_time), "YYYY-MM")
    q = db.query(
        month_expr.label("month"),
        Material.vehicle_model.label("vehicle_model"),
        MaterialPriceVersion.currency.label("currency"),
        func.sum(OutboundOrder.quantity * MaterialPriceVersion.sale_price).label("amt")
    ).join(
        Material, OutboundOrder.material_id == Material.id
    ).join(
        MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id
    )
    if start_dt:
        q = q.filter(OutboundOrder.outbound_time >= start_dt)
    if end_dt:
        q = q.filter(OutboundOrder.outbound_time < end_dt)
    rows = q.group_by(month_expr, Material.vehicle_model, MaterialPriceVersion.currency).all()

    bucket = {}
    for r in rows:
        m = r.month or ""
        v = r.vehicle_model or "未维护车型"
        key = (m, v)
        bucket.setdefault(key, 0.0)
        bucket[key] += to_cny(float(r.amt or 0), r.currency, usd_to_cny)

    months = sorted({k[0] for k in bucket.keys() if k[0]})
    vehicles = sorted({k[1] for k in bucket.keys() if k[1]})

    vehicle_defs = []
    for idx, name in enumerate(vehicles):
        vehicle_defs.append({"id": f"v{idx+1}", "name": name})
    vehicle_id_by_name = {x["name"]: x["id"] for x in vehicle_defs}

    items = []
    for m in months:
        row = {"month": m}
        for v in vehicle_defs:
            row[f"{v['id']}_outbound_amount_cny"] = 0.0
        items.append(row)

    rows_by_month = {x["month"]: x for x in items}
    for (m, vname), amt in bucket.items():
        vid = vehicle_id_by_name.get(vname)
        if not vid:
            continue
        if m not in rows_by_month:
            continue
        rows_by_month[m][f"{vid}_outbound_amount_cny"] = round(float(amt or 0), 2)

    summary_row = {"month": "汇总"}
    for v in vehicle_defs:
        summary_row[f"{v['id']}_outbound_amount_cny"] = 0.0
    for r in items:
        for v in vehicle_defs:
            summary_row[f"{v['id']}_outbound_amount_cny"] += float(r.get(f"{v['id']}_outbound_amount_cny") or 0)
    for v in vehicle_defs:
        summary_row[f"{v['id']}_outbound_amount_cny"] = round(summary_row[f"{v['id']}_outbound_amount_cny"], 2)
    items.append(summary_row)

    return {
        "usd_to_cny": usd_to_cny,
        "start_date": start_date,
        "end_date": end_date,
        "vehicles": vehicle_defs,
        "items": items
    }


@router.get("/export/outbound-summary/month-vehicle")
def export_outbound_summary_month_vehicle(start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    data = outbound_summary_month_vehicle(start_date=start_date, end_date=end_date, usd_to_cny=usd_to_cny, db=db)
    vehicles = data["vehicles"]
    items = data["items"]

    rows = []
    for r in items:
        out = {"年月": r.get("month")}
        for v in vehicles:
            out[v["name"]] = r.get(f"{v['id']}_outbound_amount_cny", 0)
        rows.append(out)
    name = "出库汇总_按年月车型.xlsx"
    return export_xlsx(rows, name)


@router.get("/outbound-detail")
def outbound_detail(date: str = None, start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    if date and (not start_date) and (not end_date):
        start_date = date
        end_date = date
    if (not start_date) or (not end_date):
        raise HTTPException(status_code=400, detail="start_date and end_date are required")

    day_start = datetime.strptime(start_date, "%Y-%m-%d")
    day_end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

    q = db.query(
        OutboundOrder.order_no,
        OutboundOrder.group_no,
        OutboundOrder.outbound_time,
        OutboundOrder.customer,
        OutboundOrder.receiver,
        OutboundOrder.quantity,
        Material.code.label("material_code"),
        Material.description.label("material_description"),
        Material.vehicle_model.label("vehicle_model"),
        MaterialPriceVersion.batch_no.label("contract_no"),
        MaterialPriceVersion.sale_price.label("sale_price"),
        MaterialPriceVersion.currency.label("currency"),
        (OutboundOrder.quantity * MaterialPriceVersion.sale_price).label("amount")
    ).join(
        Material, OutboundOrder.material_id == Material.id
    ).join(
        MaterialPriceVersion, OutboundOrder.price_version_id == MaterialPriceVersion.id
    ).filter(
        OutboundOrder.outbound_time >= day_start,
        OutboundOrder.outbound_time < day_end
    ).order_by(OutboundOrder.outbound_time.desc()).all()

    items = []
    total_amount_cny = 0.0
    for r in q:
        amount_cny = to_cny(float(r.amount or 0), r.currency, usd_to_cny)
        total_amount_cny += amount_cny
        items.append({
            "order_no": r.order_no,
            "group_no": r.group_no,
            "outbound_time": r.outbound_time,
            "customer": r.customer,
            "receiver": r.receiver,
            "material_code": r.material_code,
            "material_description": r.material_description,
            "vehicle_model": r.vehicle_model,
            "contract_no": r.contract_no,
            "quantity": int(r.quantity or 0),
            "sale_price": float(r.sale_price or 0),
            "currency": r.currency,
            "amount_cny": round(amount_cny, 2)
        })

    summary = {
        "order_no": "合计",
        "group_no": "",
        "outbound_time": None,
        "customer": "",
        "receiver": "",
        "material_code": "",
        "material_description": "",
        "vehicle_model": "",
        "contract_no": "",
        "quantity": 0,
        "sale_price": 0,
        "currency": "CNY",
        "amount_cny": round(total_amount_cny, 2)
    }

    return {
        "usd_to_cny": usd_to_cny,
        "start_date": start_date,
        "end_date": end_date,
        "items": items,
        "summary": summary
    }


@router.get("/export/outbound-detail")
def export_outbound_detail(date: str = None, start_date: str = None, end_date: str = None, usd_to_cny: float = 7.2, db: Session = Depends(get_db)):
    data = outbound_detail(date=date, start_date=start_date, end_date=end_date, usd_to_cny=usd_to_cny, db=db)
    items = data["items"] + [data["summary"]]
    rows = []
    for x in items:
        rows.append({
            "出库单号": x.get("group_no") or x.get("order_no"),
            "行单号": x.get("order_no"),
            "出库时间": x.get("outbound_time"),
            "客户": x.get("customer"),
            "领用人": x.get("receiver"),
            "车型": x.get("vehicle_model"),
            "合同号": x.get("contract_no"),
            "物料编码": x.get("material_code"),
            "物料描述": x.get("material_description"),
            "数量": x.get("quantity"),
            "销售价": x.get("sale_price"),
            "币种": x.get("currency"),
            "出库金额(CNY)": x.get("amount_cny")
        })
    name = f"出库明细_{data['start_date']}_{data['end_date']}.xlsx"
    return export_xlsx(rows, name)
