from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from app.database import engine, Base
from app.routers import (
    auth,
    users,
    listings,
    messages,
    reviews,
    favorites,
    forum,
    upload,
    contact,
)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fresh Trade API",
    description="A platform for trading fresh produce between local farmers and gardeners",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve uploaded files
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(listings.router)
app.include_router(messages.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(forum.router)
app.include_router(upload.router)
app.include_router(contact.router)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to Fresh Trade API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, content={"detail": f"Internal server error: {str(exc)}"}
    )
