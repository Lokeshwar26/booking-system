from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from sqlalchemy.orm import Session
from models import User, OTPRequest
from auth import get_current_user, get_password_hash
from schemas import UserResponse, UserUpdate, MessageResponse, DeleteResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=MessageResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Update only provided fields
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return MessageResponse(message="User updated successfully")

@router.delete("/me", response_model=DeleteResponse)
def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if OTP is verified for account deletion
    verified_otp = db.query(OTPRequest).filter(
        OTPRequest.user_id == current_user.id,
        OTPRequest.action_type == "delete_account",
        OTPRequest.is_used == True
    ).first()
    
    if not verified_otp:
        raise HTTPException(
            status_code=403, 
            detail="OTP verification required for account deletion. Please request and verify OTP first using /otp/request-account-deletion"
        )
    
    user_id = current_user.id
    
    # Remove the used OTP first
    db.delete(verified_otp)
    db.commit()
    
    # Now delete the user (bookings will be automatically deleted due to CASCADE)
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if user_to_delete:
        db.delete(user_to_delete)
        db.commit()
    
    return DeleteResponse(message="User account and all associated bookings deleted successfully", deleted_id=user_id)