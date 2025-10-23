from fastapi import APIRouter, Depends
from database import SessionLocal
from sqlalchemy.orm import Session
from models import User, Booking
from auth import get_current_user
from schemas import UserResponse, BookingResponse

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