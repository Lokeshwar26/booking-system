from fastapi import FastAPI
from database import engine
import models
from routers import auth, users, bookings

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Booking Platform API",
    description="A booking platform with role-based authentication",
    version="1.0.0"
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(bookings.router)

@app.get("/")
def root():
    return {"message": "Booking Platform API"}