from fastapi import APIRouter, Depends

from app.api.v1.endpoints import auth, materials, locations, orders, excel, inventory, system, inventory_management, transit, borrow, dashboard
from app.api import deps

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["login"])
api_router.include_router(materials.router, prefix="/materials", tags=["materials"], dependencies=[Depends(deps.get_current_active_user)])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"], dependencies=[Depends(deps.get_current_active_user)])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"], dependencies=[Depends(deps.get_current_active_user)])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"], dependencies=[Depends(deps.get_current_active_user)])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(deps.get_current_active_user)])
api_router.include_router(excel.router, prefix="/excel", tags=["excel"], dependencies=[Depends(deps.get_current_active_user)])
api_router.include_router(inventory_management.router, prefix="/inventory-management", tags=["inventory-management"], dependencies=[Depends(deps.get_current_active_user)])
api_router.include_router(transit.router, prefix="/transit", tags=["transit"], dependencies=[Depends(deps.get_current_active_user)])
api_router.include_router(borrow.router, prefix="/borrow", tags=["borrow"], dependencies=[Depends(deps.get_current_active_user)])
api_router.include_router(system.router, prefix="/system", tags=["system"], dependencies=[Depends(deps.require_admin)])
