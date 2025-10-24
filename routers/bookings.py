from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from sqlalchemy.orm import Session, joinedload
from models import Booking, User
from auth import get_current_user, get_current_admin, get_current_superadmin
from schemas import BookingCreate, BookingUpdate, BookingResponse, BookingWithUser, MessageResponse, DeleteResponse, UserResponse, UserBookingUpdate
from datetime import datetime

router = APIRouter(prefix="/bookings", tags=["bookings"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== USER ENDPOINTS ====================

# Create booking - Any authenticated user
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

# Get my bookings - Users see their own, admins & superadmins see all
@router.get("/user/my-bookings", response_model=list[BookingResponse])
def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "user":
        bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    else:
        bookings = db.query(Booking).all()
    return bookings

# Update own booking - Users can update their own bookings (room_type and guests only)
@router.put("/user/my-bookings/{booking_id}", response_model=MessageResponse)
def update_my_booking(
    booking_id: int,
    booking_update: UserBookingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Users can only update their own bookings
    if current_user.role == "user" and booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update only provided fields
    update_data = booking_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    booking.updated_by = current_user.email
    db.commit()
    
    return MessageResponse(message="Booking updated successfully")

# Delete own booking - Users can delete their own bookings
@router.delete("/user/my-bookings/{booking_id}", response_model=DeleteResponse)
def delete_my_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Users can only delete their own bookings
    if current_user.role == "user" and booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(booking)
    db.commit()
    
    return DeleteResponse(message="Booking deleted successfully", deleted_id=booking_id)

# ==================== ADMIN ENDPOINTS ====================

# Get all bookings with user details - ADMIN & SUPERADMIN ONLY
@router.get("/adminview", response_model=list[BookingWithUser])
def get_all_bookings(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    bookings = db.query(Booking).options(joinedload(Booking.user)).all()
    
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
            updated_at=booking.updated_at,
            updated_by=booking.updated_by,
            user=UserResponse(
                id=booking.user.id,
                email=booking.user.email,
                full_name=booking.user.full_name,
                role=booking.user.role
            )
        )
        booking_list.append(booking_data)
    
    return booking_list

# Get booking by ID - ADMIN & SUPERADMIN ONLY
@router.get("/adminview/{booking_id}", response_model=BookingResponse)
def get_booking_by_id(
    booking_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

# Update any booking - ADMIN & SUPERADMIN ONLY (can update all fields)
@router.put("/adminview/{booking_id}", response_model=MessageResponse)
def update_booking_admin(
    booking_id: int,
    booking_update: BookingUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Update only provided fields
    update_data = booking_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    booking.updated_by = current_user.email
    db.commit()
    
    return MessageResponse(message="Booking updated successfully")

# Delete any booking - ADMIN & SUPERADMIN ONLY
@router.delete("/adminview/{booking_id}", response_model=DeleteResponse)
def delete_booking_admin(
    booking_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    db.delete(booking)
    db.commit()
    
    return DeleteResponse(message="Booking deleted successfully", deleted_id=booking_id)

# ==================== SUPERADMIN ENDPOINTS ====================

# SUPERADMIN ONLY: Get admin activity log (all changes made by admins)
@router.get("/superadmin/activity", response_model=list[BookingWithUser])
def get_admin_activity(
    current_user: User = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    # Get all bookings that were updated by admins (not users)
    bookings = db.query(Booking).options(joinedload(Booking.user)).filter(
        Booking.updated_by.isnot(None)
    ).all()
    
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
            updated_at=booking.updated_at,
            updated_by=booking.updated_by,
            user=UserResponse(
                id=booking.user.id,
                email=booking.user.email,
                full_name=booking.user.full_name,
                role=booking.user.role
            )
        )
        booking_list.append(booking_data)
    
    return booking_list

# SUPERADMIN ONLY: Get all users with their roles
@router.get("/superadmin/users")
def get_all_users(
    current_user: User = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users