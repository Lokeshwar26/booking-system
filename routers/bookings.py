from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from sqlalchemy.orm import Session, joinedload
from models import Booking, User
from auth import get_current_user, get_current_admin
from schemas import BookingCreate, BookingUpdate, BookingResponse, BookingWithUser, MessageResponse, DeleteResponse, UserResponse

router = APIRouter(prefix="/bookings", tags=["bookings"])

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

@router.get("/adminview", response_model=list[BookingWithUser])
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

@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Users can only see their own bookings, admins can see all
    if current_user.role == "user" and booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return booking

@router.put("/{booking_id}", response_model=MessageResponse)
def update_booking(
    booking_id: int,
    booking_update: BookingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Users can only update their own bookings, admins can update all
    if current_user.role == "user" and booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update only provided fields
    update_data = booking_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    db.commit()
    db.refresh(booking)
    
    return MessageResponse(message="Booking updated successfully")

@router.delete("/{booking_id}", response_model=DeleteResponse)
def delete_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Users can only delete their own bookings, admins can delete all
    if current_user.role == "user" and booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(booking)
    db.commit()
    
    return DeleteResponse(message="Booking deleted successfully", deleted_id=booking_id)