"""
Main entry point for the Admin Panel application.
Initializes and starts the FastAPI application.
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from admin.auth import authenticate_user, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from admin.database import get_db
from admin.models import AdminUser
from admin.routers import staff, bookings, schedule

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Booking Admin Panel")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="admin/static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="admin/templates")

# Include routers
app.include_router(staff.router, prefix="/staff", tags=["staff"])
app.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
app.include_router(schedule.router, prefix="/schedule", tags=["schedule"])

@app.get("/")
async def index(request: Request, current_user: AdminUser = Depends(get_current_user)):
    """
    Admin panel home page (dashboard)
    """
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "title": "Dashboard"
    })

@app.get("/login")
async def login_page(request: Request):
    """
    Login page
    """
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Login"
    })

@app.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "title": "Login",
                "error": "Incorrect username or password"
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    return response

@app.get("/logout")
async def logout(request: Request):
    """
    Logout endpoint
    """
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response

async def start_admin_panel():
    """
    Start the admin panel
    """
    config = uvicorn.Config(
        app="admin.main:app",
        host="0.0.0.0",
        port=5000,
        log_level="info",
        reload=True
    )
    server = uvicorn.Server(config)
    
    logger.info("Starting admin panel on http://0.0.0.0:5000")
    await server.serve()

if __name__ == "__main__":
    asyncio.run(start_admin_panel())
