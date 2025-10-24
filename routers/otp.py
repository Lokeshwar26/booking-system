import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from sqlalchemy.orm import Session
from models import OTPRequest, User, Booking
from auth import get_current_user
from schemas import OTPRequestCreate, OTPResponse, OTPVerify, MessageResponse, OTPRequestResponse
from utils.email_service import email_service

router = APIRouter(prefix="/otp", tags=["otp-verification"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User requests OTP - System automatically sends it via email/SMS
@router.post("/request", response_model=OTPResponse)
def request_otp(
    otp_request: OTPRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if booking exists and belongs to user
    booking = db.query(Booking).filter(Booking.id == otp_request.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Generate 6-digit OTP
    otp_code = str(secrets.randbelow(999999)).zfill(6)
    
    # Create OTP request (expires in 10 minutes)
    db_otp = OTPRequest(
        user_id=current_user.id,
        booking_id=otp_request.booking_id,
        otp_code=otp_code,
        action_type=otp_request.action_type,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)
    
    # Automatically send OTP to user's email
    email_service.send_otp_email(
        user_email=current_user.email,
        user_name=current_user.full_name,
        otp_code=otp_code,
        action_type=otp_request.action_type
    )
    
    # Optionally send SMS (if user has phone number)
    # email_service.send_sms_otp("+1234567890", otp_code, otp_request.action_type)
    
    return OTPResponse(
        message=f"OTP sent to your registered email ({current_user.email}). Please check your inbox.",
        otp_id=db_otp.id,
        otp_code=otp_code  # Keep for demo, remove in production
    )

# User verifies their own OTP (no admin needed)
@router.post("/verify", response_model=MessageResponse)
def verify_otp(
    otp_verify: OTPVerify,
    current_user: User = Depends(get_current_user),  # User verifies their own OTP
    db: Session = Depends(get_db)
):
    # Find OTP request
    otp_request = db.query(OTPRequest).filter(
        OTPRequest.otp_code == otp_verify.otp_code,
        OTPRequest.booking_id == otp_verify.booking_id,
        OTPRequest.is_used == False,
        OTPRequest.user_id == current_user.id  # User can only verify their own OTPs
    ).first()
    
    if not otp_request:
        raise HTTPException(status_code=404, detail="Invalid OTP or booking ID")
    
    # Check if OTP expired
    if datetime.utcnow() > otp_request.expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    # Mark OTP as used (auto-approved by system)
    otp_request.is_used = True
    otp_request.approved_by = "system"  # Auto-approved
    
    db.commit()
    
    return MessageResponse(
        message=f"OTP verified successfully! You can now {otp_request.action_type} your booking."
    )

# User can check their pending OTPs
@router.get("/my-pending", response_model=list[OTPRequestResponse])
def get_my_pending_otps(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pending_requests = db.query(OTPRequest).filter(
        OTPRequest.user_id == current_user.id,
        OTPRequest.is_used == False,
        OTPRequest.expires_at > datetime.utcnow()
    ).all()
    
    return pending_requests

# Resend OTP
@router.post("/resend/{otp_id}", response_model=OTPResponse)
def resend_otp(
    otp_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    otp_request = db.query(OTPRequest).filter(
        OTPRequest.id == otp_id,
        OTPRequest.user_id == current_user.id,
        OTPRequest.is_used == False
    ).first()
    
    if not otp_request:
        raise HTTPException(status_code=404, detail="OTP request not found")
    
    # Generate new OTP
    new_otp_code = str(secrets.randbelow(999999)).zfill(6)
    
    # Update OTP
    otp_request.otp_code = new_otp_code
    otp_request.expires_at = datetime.utcnow() + timedelta(minutes=10)
    otp_request.created_at = datetime.utcnow()
    
    db.commit()
    
    # Resend email
    email_service.send_otp_email(
        user_email=current_user.email,
        user_name=current_user.full_name,
        otp_code=new_otp_code,
        action_type=otp_request.action_type
    )
    
    return OTPResponse(
        message=f"New OTP sent to your email ({current_user.email})",
        otp_id=otp_request.id,
        otp_code=new_otp_code  # Keep for demo
    )