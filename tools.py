from langchain.tools import tool
import requests
import getpass
import os

YELP_API_KEY = os.environ.get("YELP_API_KEY") or getpass.getpass("Enter Yelp API key: ")
HEADERS = {"Authorization": f"Bearer {YELP_API_KEY}"}

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
    Get top landmarks, museums, and restaurants from Yelp in a city.
    """
    categories = rec_type
    output = ""
    for cat in categories:
        output += search_yelp(city, cat) + "\n\n"
    return output