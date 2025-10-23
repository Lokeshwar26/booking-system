from fastapi import FastAPI
from database import engine
import models
from routers import auth, users, bookings

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Booking Platform API",
    description="A booking platform with role-based authentication"
)

# Include routers
app.include_router(auth.router,prefix="/auth", tags=["authentication"])
app.include_router(users.router,prefix="/users", tags=["users"])
app.include_router(bookings.router,prefix="/bookings", tags=["bookings"])

@app.get("/")
def root():
    return {"message": "Booking Platform API"} 