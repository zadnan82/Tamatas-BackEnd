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

print("✅ All routers imported successfully")

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
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Add any other origins you need
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],  # Important for some responses
)

# Serve uploaded files
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers - FIXED: Use the correct router attributes
try:
    app.include_router(auth.router)
    print("✅ Auth router included")
except AttributeError as e:
    print(f"❌ Error including auth router: {e}")
    print("Available attributes in auth module:", dir(auth))

try:
    app.include_router(users.router)
    print("✅ Users router included")
except AttributeError as e:
    print(f"❌ Error including users router: {e}")

try:
    app.include_router(listings.router)
    print("✅ Listings router included")
except AttributeError as e:
    print(f"❌ Error including listings router: {e}")

try:
    app.include_router(messages.router)
    print("✅ Messages router included")
except AttributeError as e:
    print(f"❌ Error including messages router: {e}")

try:
    app.include_router(reviews.router)
    print("✅ Reviews router included")
except AttributeError as e:
    print(f"❌ Error including reviews router: {e}")

try:
    app.include_router(favorites.router)
    print("✅ Favorites router included")
except AttributeError as e:
    print(f"❌ Error including favorites router: {e}")

try:
    app.include_router(forum.router)
    print("✅ Forum router included")
except AttributeError as e:
    print(f"❌ Error including forum router: {e}")

try:
    app.include_router(upload.router)
    print("✅ Upload router included")
except AttributeError as e:
    print(f"❌ Error including upload router: {e}")

try:
    app.include_router(contact.router)
    print("✅ Contact router included")
except AttributeError as e:
    print(f"❌ Error including contact router: {e}")


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


# Safe route debugging
@app.on_event("startup")
async def print_routes():
    from fastapi.routing import APIRoute

    print("\n=== REGISTERED API ROUTES ===")
    for route in app.routes:
        if hasattr(route, "path"):
            if hasattr(route, "methods"):
                print(f"{route.path} - {route.methods}")
            else:
                print(f"{route.path} - (Static/Mount)")
    print("============================\n")
