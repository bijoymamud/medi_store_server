from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from src.database.connection import get_db
from src.modules.contact import models, schemas
from src.utils.dependencies import get_admin_user
from src.modules.users.models import User
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from src.utils.rate_limit import RateLimiter

router = APIRouter()
contact_limiter = RateLimiter(limit=5, window=60)

def send_contact_admin_email(request: models.ContactRequest):
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")
    if not smtp_email or not smtp_password:
        print(f"MOCK CONTACT EMAIL to admin ({smtp_email}): New support request from {request.client_name} ({request.email}) in department {request.department}: {request.specifications}")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = smtp_email  # Send notification to the administrator
        msg['Subject'] = f"MediShop Support Request - {request.client_name}"
        
        body = f"""Hello Administrator,

A new contact support request has been submitted on MediShop:

Client Name: {request.client_name}
Email: {request.email}
Department / Equipment Type: {request.department}
Specifications: {request.specifications}

Received at: {request.created_at}
"""
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_email, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_email, smtp_email, text)
        server.quit()
        print(f"Successfully sent contact notification to admin.")
    except Exception as e:
        print(f"Failed to send contact notification: {str(e)}")

@router.post("/", response_model=schemas.ContactRequestResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(contact_limiter)])
def create_contact_request(
    payload: schemas.ContactRequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_request = models.ContactRequest(
        client_name=payload.client_name,
        email=payload.email,
        department=payload.department,
        specifications=payload.specifications
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    # Send email notification to admin
    background_tasks.add_task(send_contact_admin_email, db_request)
    
    return db_request

@router.get("/", response_model=List[schemas.ContactRequestResponse])
def list_contact_requests(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    requests = db.query(models.ContactRequest).order_by(models.ContactRequest.created_at.desc()).all()
    return requests
