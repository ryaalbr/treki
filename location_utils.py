import requests
from geopy.geocoders import Nominatim

def get_current_location():
    try:
        response = requests.get("https://ipinfo.io")
        data = response.json()
        loc = data["loc"]  # e.g., "38.5816,-121.4944"
        lat, lon = map(float, loc.split(","))
        return lat, lon
    except Exception as e:
        print("Error getting location from IP:", e)
        return None, None

def get_city_from_coords(lat, lon):
    try:
        geolocator = Nominatim(user_agent="tour_guide_app")
        location = geolocator.reverse((lat, lon), language='en')
        if location and 'address' in location.raw:
            address = location.raw['address']
            # Try multiple possible city-level fields
            return (
                address.get('city') or 
                address.get('town') or 
                address.get('village') or 
                address.get('hamlet') or 
                "City not found"
            )
        return "Unknown location"
    except Exception as e:
        print("Error in reverse geocoding:", e)
        return "Error"