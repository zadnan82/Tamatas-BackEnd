# CREATE NEW FILE: app/location_utils.py

import math
import httpx
from typing import Optional, Tuple, Dict, Any, List
from fastapi import HTTPException
import asyncio


class LocationService:
    """Service for handling location-related operations"""

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in miles
        """
        if not all([lat1, lon1, lat2, lon2]):
            return float("inf")

        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in miles
        r = 3956

        return c * r

    @staticmethod
    def calculate_distance_km(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two points in kilometers
        """
        miles = LocationService.calculate_distance(lat1, lon1, lat2, lon2)
        return miles * 1.60934  # Convert miles to km

    @staticmethod
    async def geocode_address(address: str) -> Optional[Dict[str, Any]]:
        """
        Convert address to coordinates using Nominatim (OpenStreetMap)
        Returns: {latitude, longitude, formatted_address, city, state, country}
        """
        try:
            # Clean up the address
            address = address.strip()
            if not address:
                return None

            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": address,
                "format": "json",
                "limit": 1,
                "addressdetails": 1,
                "accept-language": "en",  # Get results in English
            }
            headers = {
                "User-Agent": "FreshTrade/1.0 (contact@freshtrade.com)"  # Required by Nominatim
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data:
                    result = data[0]
                    address_details = result.get("address", {})

                    # Extract location components
                    city = (
                        address_details.get("city")
                        or address_details.get("town")
                        or address_details.get("village")
                        or address_details.get("municipality")
                    )

                    state = (
                        address_details.get("state")
                        or address_details.get("province")
                        or address_details.get("region")
                    )

                    return {
                        "latitude": float(result["lat"]),
                        "longitude": float(result["lon"]),
                        "formatted_address": result.get("display_name", address),
                        "city": city,
                        "state": state,
                        "country": address_details.get("country"),
                        "postcode": address_details.get("postcode"),
                        "area": address_details.get("suburb")
                        or address_details.get("neighbourhood"),
                    }

        except Exception as e:
            print(f"Geocoding error for '{address}': {e}")

        return None

    @staticmethod
    async def search_locations(query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for locations with autocomplete suggestions
        Returns list of location suggestions
        """
        try:
            if len(query) < 2:
                return []

            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": query,
                "format": "json",
                "limit": limit,
                "addressdetails": 1,
                "accept-language": "en",
            }
            headers = {"User-Agent": "FreshTrade/1.0 (contact@freshtrade.com)"}

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                suggestions = []

                for result in data:
                    address_details = result.get("address", {})

                    city = (
                        address_details.get("city")
                        or address_details.get("town")
                        or address_details.get("village")
                    )

                    state = address_details.get("state")
                    country = address_details.get("country")

                    if city and country:  # Only return results with city and country
                        suggestion = {
                            "display_name": result.get("display_name"),
                            "city": city,
                            "state": state,
                            "country": country,
                            "latitude": float(result["lat"]),
                            "longitude": float(result["lon"]),
                            "type": result.get("type", "unknown"),
                        }
                        suggestions.append(suggestion)

                return suggestions

        except Exception as e:
            print(f"Location search error for '{query}': {e}")

        return []

    @staticmethod
    def is_within_radius(
        user_lat: float,
        user_lon: float,
        user_radius: int,
        listing_lat: float,
        listing_lon: float,
    ) -> bool:
        """Check if listing is within user's search radius"""
        distance = LocationService.calculate_distance(
            user_lat, user_lon, listing_lat, listing_lon
        )
        return distance <= user_radius

    @staticmethod
    def format_location_display(location: Dict[str, Any]) -> str:
        """
        Format location for display in UI
        Returns: "City, State, Country" or "City, Country"
        """
        if not location:
            return "Location not specified"

        parts = []

        if location.get("city"):
            parts.append(location["city"])

        if location.get("state"):
            parts.append(location["state"])

        if location.get("country"):
            parts.append(location["country"])

        return ", ".join(parts) if parts else "Location not specified"

    @staticmethod
    def add_location_privacy_offset(
        lat: float, lng: float, offset_miles: float = 0.5
    ) -> Tuple[float, float]:
        """
        Add small random offset to coordinates for privacy
        Default offset is about 0.5 miles
        """
        import random

        # Convert miles to degrees (approximate)
        lat_offset = (offset_miles / 69.0) * (random.random() - 0.5) * 2
        lng_offset = (
            (offset_miles / (69.0 * math.cos(math.radians(lat))))
            * (random.random() - 0.5)
            * 2
        )

        return lat + lat_offset, lng + lng_offset

    @staticmethod
    def validate_coordinates(lat: float, lng: float) -> bool:
        """Validate that coordinates are within valid ranges"""
        return -90 <= lat <= 90 and -180 <= lng <= 180


# Additional utility functions for WhatsApp integration
class ContactService:
    """Service for handling contact-related operations"""

    @staticmethod
    def format_whatsapp_url(phone_number: str, message: str = "") -> str:
        """
        Generate WhatsApp URL for contacting user
        """
        # Clean phone number - remove spaces, dashes, parentheses
        clean_phone = "".join(filter(str.isdigit, phone_number.replace("+", "")))

        if message:
            import urllib.parse

            encoded_message = urllib.parse.quote(message)
            return f"https://wa.me/{clean_phone}?text={encoded_message}"
        else:
            return f"https://wa.me/{clean_phone}"

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Basic phone number validation"""
        if not phone:
            return False

        # Remove common separators
        clean_phone = "".join(filter(str.isdigit, phone.replace("+", "")))

        # Should be between 7 and 15 digits (international standards)
        return 7 <= len(clean_phone) <= 15

    @staticmethod
    def generate_whatsapp_message(listing_title: str, user_name: str) -> str:
        """Generate default WhatsApp message for listings"""
        return f"Hi! I'm interested in your listing: {listing_title}. Is it still available?"
