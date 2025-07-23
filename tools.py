from langchain.tools import tool
import requests
import getpass
import os
from amadeus import Client, ResponseError
from langchain.tools import tool
from geopy.geocoders import Nominatim

AMADEUS_API_KEY = os.environ.get("AMADEUS_API_KEY") or getpass.getpass("Enter Amadeus API key: ")
AMADEUS_API_SECRET = os.environ.get("AMADEUS_API_SECRET") or getpass.getpass("Enter Amadeus API secret: ")
YELP_API_KEY = os.environ.get("YELP_API_KEY") or getpass.getpass("Enter Yelp API key: ")
HEADERS = {"Authorization": f"Bearer {YELP_API_KEY}"}

amadeus = Client(
    client_id=AMADEUS_API_KEY,
    client_secret=AMADEUS_API_SECRET
)

def search_yelp(city, term, limit=5):
    url = "https://api.yelp.com/v3/businesses/search"
    params = {
        "location": city,
        "term": term,
        "limit": limit,
        "sort_by": "rating"
    }
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()

    if 'businesses' not in data:
        return f"No results for {term} in {city}."

    results = [f"{i+1}. {biz['name']} ({biz['rating']}⭐) - {biz['location']['address1']}" 
               for i, biz in enumerate(data['businesses'])]
    
    return f"Top {term.title()} in {city}:\n" + "\n".join(results)

@tool
def get_yelp_recommendations(city: str, rec_type: str) -> str:
    """
    Use this to get the best restaurants, hotels, museums, landmarks, and other places in a given city.
    """
    output = ""
    output += search_yelp(city, rec_type) + "\n\n"
    return output

def get_coordinates(city_name: str) -> tuple:
    geolocator = Nominatim(user_agent="travel_guide_app")
    location = geolocator.geocode(city_name)
    if location:
        return location.latitude, location.longitude
    else:
        return None

def find_airports_near_city(city: str):
    try:
        lat, lon = get_coordinates(city)
    except error:
        return f"Error: {error}"
    try:
        response = amadeus.reference_data.locations.airports.get(
            latitude=lat,
            longitude=lon
        )
        airports = [
            f"{a['iataCode']} - {a['name']} ({a['address']['cityName']}, {a['address']['countryCode']})"
            for a in response.data
        ]
        return "\n".join(airports)
    except ResponseError as error:
        return f"Error: {error}"

def search_amadeus_flights(origin: str, destination: str, date: str) -> str:
    """
    Search for flights using Amadeus API.
    origin and destination must be IATA airport codes (e.g. SFO, JFK, LHR).
    date should be YYYY-MM-DD.
    """
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=date,
            adults=1,
            max=5
        )

        results = []
        for i, offer in enumerate(response.data):
            itinerary = offer['itineraries'][0]['segments'][0]
            dep = itinerary['departure']['iataCode']
            arr = itinerary['arrival']['iataCode']
            dep_time = itinerary['departure']['at']
            arr_time = itinerary['arrival']['at']
            price = offer['price']['total']
            carrier = itinerary['carrierCode']
            results.append(f"{i+1}. {carrier} | {dep} → {arr} | {dep_time} → {arr_time} | ${price}")
        
        return "\n".join(results)
    except ResponseError as e:
        return f"Error: {e}"

@tool
def airports_near_city(city: str) -> str:
    """Find the IATA codes of airports near a given city using Amadeus API."""
    return find_airports_near_city(city)

@tool
def amadeus_flight_search(origin: str, destination: str, date: str) -> str:
    """
    Search for available flights using Amadeus API.
    origin and destination must be IATA codes (e.g. JFK, LAX), and date in YYYY-MM-DD format.
    """
    return search_amadeus_flights(origin, destination, date)

