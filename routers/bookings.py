from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from sqlalchemy.orm import Session, joinedload
from models import Booking, User
from auth import get_current_user, get_current_admin
from schemas import BookingCreate, BookingWithUser, MessageResponse, UserResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=MessageResponse)
def create_booking(
    booking: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_booking = Booking(
        room_type=booking.room_type,
        check_in=booking.check_in,
        check_out=booking.check_out,
        guests=booking.guests,
        user_id=current_user.id
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return MessageResponse(message="Booking created", booking_id=db_booking.id)

@router.get("/", response_model=list[BookingWithUser])
def get_all_bookings(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # Use joinedload to include user data in the query
    bookings = db.query(Booking).options(joinedload(Booking.user)).all()
    
    # Convert to BookingWithUser schema
    booking_list = []
    for booking in bookings:
        booking_data = BookingWithUser(
            id=booking.id,
            room_type=booking.room_type,
            check_in=booking.check_in,
            check_out=booking.check_out,
            guests=booking.guests,
            user_id=booking.user_id,
            created_at=booking.created_at,
            user=UserResponse(
                id=booking.user.id,
                email=booking.user.email,
                full_name=booking.user.full_name,
                role=booking.user.role
            )
        )
        booking_list.append(booking_data)
    
    return booking_list