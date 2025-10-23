from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from sqlalchemy.orm import Session
from models import User, Booking
from auth import get_current_user, get_password_hash
from schemas import UserResponse, UserUpdate, MessageResponse, DeleteResponse, BookingResponse

router = APIRouter(prefix="/users", tags=["users"])

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
    user_id = current_user.id
    db.delete(current_user)
    db.commit()
    
    return DeleteResponse(message="User deleted successfully", deleted_id=user_id)

@router.get("/bookings", response_model=list[BookingResponse])
def get_user_bookings(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if current_user.role == "user":
        bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    else:
        bookings = db.query(Booking).all()
    
    return bookings