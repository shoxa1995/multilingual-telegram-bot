"""
Staff schedule management routes for the Admin Panel.
"""
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from admin.auth import get_current_user
from admin.database import get_db
from admin.models import AdminUser
from admin.config import DEFAULT_WORKING_HOURS
from bot.database import Staff, StaffSchedule

router = APIRouter()
templates = Jinja2Templates(directory="admin/templates")

@router.get("/", response_class=HTMLResponse)
async def get_schedule_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
    staff_id: Optional[int] = None
):
    """
    Get the schedule management page.
    """
    # Get all staff members
    staff_members = db.query(Staff).all()
    
    # If staff_id is provided, get schedules for that staff
    selected_staff = None
    staff_schedules = []
    
    if staff_id:
        selected_staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if selected_staff:
            staff_schedules = db.query(StaffSchedule).filter(
                StaffSchedule.staff_id == staff_id
            ).all()
    
    # Organize schedules by weekday
    weekday_schedules = {
        0: None,  # Monday
        1: None,  # Tuesday
        2: None,  # Wednesday
        3: None,  # Thursday
        4: None,  # Friday
        5: None,  # Saturday
        6: None   # Sunday
    }
    
    for schedule in staff_schedules:
        weekday_schedules[schedule.weekday] = schedule
    
    return templates.TemplateResponse("schedule.html", {
        "request": request,
        "current_user": current_user,
        "title": "Schedule Management",
        "staff_members": staff_members,
        "selected_staff": selected_staff,
        "weekday_schedules": weekday_schedules,
        "weekdays": [
            {"id": 0, "name": "Monday"},
            {"id": 1, "name": "Tuesday"},
            {"id": 2, "name": "Wednesday"},
            {"id": 3, "name": "Thursday"},
            {"id": 4, "name": "Friday"},
            {"id": 5, "name": "Saturday"},
            {"id": 6, "name": "Sunday"}
        ]
    })

@router.post("/update", response_class=HTMLResponse)
async def update_schedule(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
    staff_id: int = Form(...),
    weekday: int = Form(...),
    start_time: Optional[str] = Form(None),
    end_time: Optional[str] = Form(None),
    is_working_day: bool = Form(False)
):
    """
    Update a staff member's schedule for a specific weekday.
    """
    # Check if staff exists
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Check if schedule already exists for this weekday
    schedule = db.query(StaffSchedule).filter(
        StaffSchedule.staff_id == staff_id,
        StaffSchedule.weekday == weekday
    ).first()
    
    if is_working_day and start_time and end_time:
        # Working day - create or update schedule
        if schedule:
            schedule.start_time = start_time
            schedule.end_time = end_time
        else:
            schedule = StaffSchedule(
                staff_id=staff_id,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time
            )
            db.add(schedule)
    else:
        # Not a working day - delete schedule if exists
        if schedule:
            db.delete(schedule)
    
    db.commit()
    
    return RedirectResponse(url=f"/schedule?staff_id={staff_id}", status_code=303)

@router.post("/bulk-update", response_class=HTMLResponse)
async def bulk_update_schedule(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
    staff_id: int = Form(...)
):
    """
    Bulk update a staff member's schedule for all weekdays.
    """
    # Check if staff exists
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Process each weekday
    for weekday in range(7):
        is_working_day = request.form.get(f"is_working_day_{weekday}", "off") == "on"
        start_time = request.form.get(f"start_time_{weekday}")
        end_time = request.form.get(f"end_time_{weekday}")
        
        # Check if schedule already exists for this weekday
        schedule = db.query(StaffSchedule).filter(
            StaffSchedule.staff_id == staff_id,
            StaffSchedule.weekday == weekday
        ).first()
        
        if is_working_day and start_time and end_time:
            # Working day - create or update schedule
            if schedule:
                schedule.start_time = start_time
                schedule.end_time = end_time
            else:
                schedule = StaffSchedule(
                    staff_id=staff_id,
                    weekday=weekday,
                    start_time=start_time,
                    end_time=end_time
                )
                db.add(schedule)
        else:
            # Not a working day - delete schedule if exists
            if schedule:
                db.delete(schedule)
    
    db.commit()
    
    return RedirectResponse(url=f"/schedule?staff_id={staff_id}", status_code=303)

@router.post("/apply-default", response_class=HTMLResponse)
async def apply_default_schedule(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
    staff_id: int = Form(...)
):
    """
    Apply default working schedule to a staff member.
    """
    # Check if staff exists
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Delete existing schedules
    db.query(StaffSchedule).filter(StaffSchedule.staff_id == staff_id).delete()
    
    # Apply default schedule
    for weekday, hours in DEFAULT_WORKING_HOURS.items():
        if hours:
            start_time, end_time = hours
            schedule = StaffSchedule(
                staff_id=staff_id,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time
            )
            db.add(schedule)
    
    db.commit()
    
    return RedirectResponse(url=f"/schedule?staff_id={staff_id}", status_code=303)
