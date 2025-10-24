from fastapi import FastAPI
from database import engine
import models
from routers import auth, users, bookings, otp

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Booking Platform API",
    description="A booking platform with role-based authentication and OTP for account deletion",
    version="1.0.0"
)

# Include routers
app.include_router(auth.router,prefix="/auth", tags=["authentication"])
app.include_router(users.router,prefix="/users", tags=["users"])
app.include_router(bookings.router,prefix="/bookings", tags=["bookings"])
app.include_router(otp.router,prefix="/otp", tags=["otp-verification"])  # Add OTP router

@app.get("/")
def root():
    return {"message": "Booking Platform API with OTP Security"}