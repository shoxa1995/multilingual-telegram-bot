"""
Staff management routes for the Admin Panel.
"""
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from admin.auth import get_current_user
from admin.database import get_db
from admin.models import AdminUser
from bot.database import Staff

router = APIRouter()
templates = Jinja2Templates(directory="admin/templates")

@router.get("/", response_class=HTMLResponse)
async def get_staff_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
    page: int = Query(1, ge=1),
    search: Optional[str] = None
):
    """
    Get the list of staff members.
    """
    # Base query
    query = db.query(Staff)
    
    # Apply search filter if provided
    if search:
        query = query.filter(Staff.name.ilike(f"%{search}%"))
    
    # Count total items
    total_items = query.count()
    
    # Pagination
    items_per_page = 10
    total_pages = (total_items + items_per_page - 1) // items_per_page
    offset = (page - 1) * items_per_page
    
    # Get paginated items
    staff_members = query.offset(offset).limit(items_per_page).all()
    
    return templates.TemplateResponse("staff.html", {
        "request": request,
        "current_user": current_user,
        "title": "Staff Management",
        "staff_members": staff_members,
        "current_page": page,
        "total_pages": total_pages,
        "search": search or ""
    })

@router.get("/add", response_class=HTMLResponse)
async def get_add_staff_form(
    request: Request,
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Get the form to add a new staff member.
    """
    return templates.TemplateResponse("staff.html", {
        "request": request,
        "current_user": current_user,
        "title": "Add Staff Member",
        "form_mode": "add"
    })

@router.post("/add", response_class=HTMLResponse)
async def add_staff(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
    name: str = Form(...),
    bitrix_user_id: str = Form(...),
    description_en: str = Form(...),
    description_ru: str = Form(...),
    description_uz: str = Form(...),
    photo_url: str = Form(...),
    price: int = Form(...),
    is_active: bool = Form(True)
):
    """
    Add a new staff member.
    """
    staff = Staff(
        name=name,
        bitrix_user_id=bitrix_user_id,
        description_en=description_en,
        description_ru=description_ru,
        description_uz=description_uz,
        photo_url=photo_url,
        price=price,
        is_active=is_active
    )
    
    db.add(staff)
    db.commit()
    db.refresh(staff)
    
    return RedirectResponse(url="/staff", status_code=303)

@router.get("/edit/{staff_id}", response_class=HTMLResponse)
async def get_edit_staff_form(
    request: Request,
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Get the form to edit a staff member.
    """
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    return templates.TemplateResponse("staff.html", {
        "request": request,
        "current_user": current_user,
        "title": f"Edit Staff: {staff.name}",
        "staff": staff,
        "form_mode": "edit"
    })

@router.post("/edit/{staff_id}", response_class=HTMLResponse)
async def edit_staff(
    request: Request,
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
    name: str = Form(...),
    bitrix_user_id: str = Form(...),
    description_en: str = Form(...),
    description_ru: str = Form(...),
    description_uz: str = Form(...),
    photo_url: str = Form(...),
    price: int = Form(...),
    is_active: bool = Form(True)
):
    """
    Edit a staff member.
    """
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    staff.name = name
    staff.bitrix_user_id = bitrix_user_id
    staff.description_en = description_en
    staff.description_ru = description_ru
    staff.description_uz = description_uz
    staff.photo_url = photo_url
    staff.price = price
    staff.is_active = is_active
    
    db.commit()
    db.refresh(staff)
    
    return RedirectResponse(url="/staff", status_code=303)

@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Delete a staff member.
    """
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    db.delete(staff)
    db.commit()
    
    return {"status": "success", "message": "Staff deleted successfully"}

@router.post("/{staff_id}/toggle-active")
async def toggle_staff_active(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Toggle a staff member's active status.
    """
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    staff.is_active = not staff.is_active
    db.commit()
    
    return {"status": "success", "is_active": staff.is_active}
