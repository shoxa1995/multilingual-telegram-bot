"""
Booking management routes for the Admin Panel.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from admin.auth import get_current_user
from admin.database import get_db
from admin.models import AdminUser
from bot.database import Booking, BookingStatus, User, Staff
from bot.utils.zoom import update_zoom_meeting
from bot.utils.bitrix24 import update_bitrix_event

router = APIRouter()
templates = Jinja2Templates(directory="admin/templates")

@router.get("/", response_class=HTMLResponse)
async def get_bookings_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
    page: int = Query(1, ge=1),
    status: Optional[str] = None,
    staff_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Get the list of bookings with filters.
    """
    # Base query
    query = db.query(Booking).join(User).join(Staff)
    
    # Apply filters
    if status:
        try:
            booking_status = BookingStatus[status.upper()]
            query = query.filter(Booking.status == booking_status)
        except (KeyError, ValueError):
            pass
    
    if staff_id:
        query = query.filter(Booking.staff_id == staff_id)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(Booking.booking_date >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d")
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.filter(Booking.booking_date <= to_date)
        except ValueError:
            pass
    
    if search:
        query = query.filter(
            (User.first_name.ilike(f"%{search}%")) |
            (User.last_name.ilike(f"%{search}%")) |
            (User.phone_number.ilike(f"%{search}%")) |
            (User.username.ilike(f"%{search}%"))
        )
    
    # Order by date, most recent first
    query = query.order_by(Booking.booking_date.desc())
    
    # Count total items
    total_items = query.count()
    
    # Pagination
    items_per_page = 10
    total_pages = (total_items + items_per_page - 1) // items_per_page
    offset = (page - 1) * items_per_page
    
    # Get paginated items
    bookings = query.offset(offset).limit(items_per_page).all()
    
    # Get all staff for filter dropdown
    staff_members = db.query(Staff).all()
    
    return templates.TemplateResponse("bookings.html", {
        "request": request,
        "current_user": current_user,
        "title": "Booking Management",
        "bookings": bookings,
        "current_page": page,
        "total_pages": total_pages,
        "status_filter": status,
        "staff_id_filter": staff_id,
        "date_from_filter": date_from,
        "date_to_filter": date_to,
        "search": search or "",
        "staff_members": staff_members,
        "booking_statuses": [status.name for status in BookingStatus]
    })

@router.get("/{booking_id}", response_class=HTMLResponse)
async def get_booking_details(
    request: Request,
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Get details of a specific booking.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return templates.TemplateResponse("bookings.html", {
        "request": request,
        "current_user": current_user,
        "title": f"Booking #{booking.id}",
        "booking": booking,
        "form_mode": "detail"
    })

@router.post("/{booking_id}/status", response_class=HTMLResponse)
async def update_booking_status(
    request: Request,
    booking_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Update a booking's status.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    try:
        new_status = BookingStatus[status.upper()]
        booking.status = new_status
        db.commit()
    except (KeyError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid status")
    
    return RedirectResponse(url=f"/bookings/{booking.id}", status_code=303)

@router.post("/{booking_id}/reschedule", response_class=HTMLResponse)
async def reschedule_booking(
    request: Request,
    booking_id: int,
    new_date: str = Form(...),
    new_time: str = Form(...),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Reschedule a booking to a new date and time.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    try:
        # Parse new date and time
        new_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
        
        # Update booking date
        old_date = booking.booking_date
        booking.booking_date = new_datetime
        db.commit()
        
        # Update Zoom meeting if exists
        if booking.zoom_meeting_id:
            await update_zoom_meeting(
                booking.zoom_meeting_id,
                new_datetime,
                booking.duration_minutes or 30
            )
        
        # Update Bitrix24 event if exists
        if booking.bitrix_event_id and booking.staff and booking.staff.bitrix_user_id:
            await update_bitrix_event(
                booking.staff.bitrix_user_id,
                booking.bitrix_event_id,
                new_datetime,
                booking.duration_minutes or 30
            )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format")
    
    return RedirectResponse(url=f"/bookings/{booking.id}", status_code=303)

@router.delete("/{booking_id}")
async def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Delete a booking.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    db.delete(booking)
    db.commit()
    
    return {"status": "success", "message": "Booking deleted successfully"}

@router.get("/export", response_class=HTMLResponse)
async def export_bookings(
    request: Request,
    format: str = "csv",
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Export bookings data.
    """
    # This would normally generate a CSV or Excel file for download
    # For simplicity, we'll just redirect to the bookings page
    return RedirectResponse(url="/bookings", status_code=303)
