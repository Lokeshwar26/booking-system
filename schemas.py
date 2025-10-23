from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str

class UserCreate(UserBase):
    password: str
    role: str = "user"

class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True

# Booking Schemas
class BookingBase(BaseModel):
    room_type: str
    check_in: datetime
    check_out: datetime
    guests: int

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Booking with user details (for admin)
class BookingWithUser(BookingResponse):
    user: UserResponse

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Response Schemas
class MessageResponse(BaseModel):
    message: str
    user_id: Optional[int] = None
    booking_id: Optional[int] = None