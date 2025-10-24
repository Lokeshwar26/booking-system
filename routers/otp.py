import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from sqlalchemy.orm import Session
from models import OTPRequest, User
from auth import get_current_user
from schemas import OTPRequestCreate, OTPResponse, OTPVerify, MessageResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def send_otp_notification(user_email: str, user_name: str, otp_code: str, action_type: str):
    """Simulate OTP notification (replace with actual email/SMS in production)"""
    print("=" * 60)
    print("🔐 ACCOUNT DELETION OTP VERIFICATION")
    print("=" * 60)
    print(f"👤 User: {user_name}")
    print(f"📧 Email: {user_email}")
    print(f"🚨 Action: {action_type.upper()}")
    print(f"🔢 OTP Code: {otp_code}")
    print(f"⏰ Valid for: 10 minutes")
    print("=" * 60)
    print("💡 In production, this OTP would be sent via email/SMS")
    print("=" * 60)
    return True

# User requests OTP for account deletion
@router.post("/request-account-deletion", response_model=OTPResponse)
def request_account_deletion_otp(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Generate 6-digit OTP
    otp_code = str(secrets.randbelow(999999)).zfill(6)
    
    # Create OTP request for account deletion (expires in 10 minutes)
    db_otp = OTPRequest(
        user_id=current_user.id,
        otp_code=otp_code,
        action_type="delete_account",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)
    
    # Send OTP notification
    send_otp_notification(
        user_email=current_user.email,
        user_name=current_user.full_name,
        otp_code=otp_code,
        action_type="delete_account"
    )
    
    return OTPResponse(
        message="OTP sent to your registered email for account deletion verification.",
        otp_id=db_otp.id,
        otp_code=otp_code  # Keep for demo, remove in production
    )

# User verifies OTP for account deletion
@router.post("/verify-account-deletion", response_model=MessageResponse)
def verify_account_deletion_otp(
    otp_verify: OTPVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find OTP request for account deletion
    otp_request = db.query(OTPRequest).filter(
        OTPRequest.otp_code == otp_verify.otp_code,
        OTPRequest.action_type == "delete_account",
        OTPRequest.is_used == False,
        OTPRequest.user_id == current_user.id
    ).first()
    
    if not otp_request:
        raise HTTPException(status_code=404, detail="Invalid OTP")
    
    # Check if OTP expired
    if datetime.utcnow() > otp_request.expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    # Mark OTP as used
    otp_request.is_used = True
    db.commit()
    
    return MessageResponse(
        message="OTP verified successfully. You can now delete your account."
    )