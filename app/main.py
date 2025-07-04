# UPDATE app/main.py - Include location router and all features

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
    location,  # NEW ROUTER
)

print("✅ All routers imported successfully including location router")

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fresh Trade API",
    description="A platform for trading fresh produce between local farmers and gardeners",
    version="2.0.0",  # Updated version with location features
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
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

# Include routers with error handling
routers_to_include = [
    (auth, "auth"),
    (users, "users"),
    (listings, "listings"),
    (messages, "messages"),
    (reviews, "reviews"),
    (favorites, "favorites"),
    (forum, "forum"),
    (upload, "upload"),
    (contact, "contact"),
    (location, "location"),  # NEW LOCATION ROUTER
]

for router_module, router_name in routers_to_include:
    try:
        app.include_router(router_module.router)
        print(f"✅ {router_name.capitalize()} router included")
    except AttributeError as e:
        print(f"❌ Error including {router_name} router: {e}")
        print(f"Available attributes in {router_name} module:", dir(router_module))


@app.get("/")
def read_root():
    return {
        "message": "Welcome to Fresh Trade API",
        "version": "2.0.0",
        "features": [
            "User authentication & profiles",
            "Location-based listing search",
            "Three listing types: for_sale, looking_for, give_away",
            "Distance calculations & nearby search",
            "WhatsApp contact integration",
            "Forum discussions",
            "Reviews & ratings",
            "File uploads",
            "Real-time messaging",
        ],
        "docs": "/docs",
        "location_features": {
            "geocoding": "OpenStreetMap/Nominatim",
            "search_radius": "User-configurable (default: 25 miles)",
            "precision_levels": ["city", "neighborhood"],
            "contact_methods": ["platform_messages", "whatsapp", "both"],
        },
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features_enabled": [
            "location_services",
            "contact_preferences",
            "give_away_listings",
            "distance_search",
        ],
    }


# New endpoint to check if location services are working
@app.get("/location/test")
async def test_location_services():
    """Test if location services are working"""
    try:
        from app.location_utils import LocationService

        # Test geocoding with a simple address
        test_result = await LocationService.geocode_address("New York, NY, USA")

        if test_result:
            return {
                "status": "working",
                "message": "Location services are operational",
                "test_geocoding": {"query": "New York, NY, USA", "result": test_result},
            }
        else:
            return {"status": "error", "message": "Geocoding service not responding"}
    except Exception as e:
        return {"status": "error", "message": f"Location services error: {str(e)}"}


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "path": str(request.url.path),
            "method": request.method,
        },
    )


# Safe route debugging
@app.on_event("startup")
async def print_routes():
    from fastapi.routing import APIRoute

    print("\n=== REGISTERED API ROUTES ===")
    route_count = 0
    for route in app.routes:
        if hasattr(route, "path"):
            if hasattr(route, "methods"):
                print(f"{route.path} - {route.methods}")
                route_count += 1
            else:
                print(f"{route.path} - (Static/Mount)")

    print(f"Total API routes: {route_count}")
    print("============================\n")

    # Test location services on startup
    try:
        from app.location_utils import LocationService

        print("🌍 Testing location services...")
        test_result = await LocationService.geocode_address("London, UK")
        if test_result:
            print("✅ Location services working correctly")
        else:
            print("⚠️ Location services may have issues")
    except Exception as e:
        print(f"❌ Location services error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Fresh Trade API shutting down...")


# Additional API info endpoint
@app.get("/api/info")
def get_api_info():
    """Get comprehensive API information"""
    return {
        "api_name": "Fresh Trade API",
        "version": "2.0.0",
        "description": "Global marketplace for fresh produce trading",
        "features": {
            "authentication": "JWT-based user authentication",
            "location_services": {
                "geocoding_provider": "OpenStreetMap Nominatim",
                "supported_precision": ["city", "neighborhood"],
                "distance_calculation": "Haversine formula",
                "default_search_radius": "25 miles",
            },
            "listing_types": {
                "for_sale": "Traditional marketplace listings",
                "looking_for": "Reverse marketplace - buyers post needs",
                "give_away": "Community sharing - free produce",
            },
            "contact_methods": {
                "platform_messages": "Built-in messaging system",
                "whatsapp_integration": "Direct WhatsApp links",
                "contact_preferences": "User-configurable",
            },
            "search_capabilities": [
                "Text search in titles/descriptions",
                "Category filtering",
                "Location-based search with radius",
                "Distance sorting",
                "Organic-only filtering",
            ],
            "community_features": [
                "User reviews and ratings",
                "Forum discussions",
                "Favorites/bookmarks",
                "File uploads for images",
            ],
        },
        "endpoints": {
            "authentication": "/auth/*",
            "user_management": "/users/*",
            "listings": "/listings/*",
            "location_services": "/location/*",
            "messaging": "/messages/*",
            "reviews": "/reviews/*",
            "favorites": "/favorites/*",
            "forum": "/forum/*",
            "file_upload": "/upload/*",
            "contact_form": "/contact/*",
        },
        "documentation": {
            "interactive_docs": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json",
        },
        "requirements": {
            "user_location": "Mandatory for creating listings",
            "supported_regions": "Global",
            "minimum_location_data": ["country", "city"],
        },
    }


print("🚀 Fresh Trade API v2.0 with location features initialized!")
