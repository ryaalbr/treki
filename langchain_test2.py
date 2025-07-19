import getpass
import os
import requests
from geopy.geocoders import Nominatim
import wikipedia
from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
import requests
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model

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

# search = TavilySearch(max_results=2)
tools = [get_yelp_recommendations]

get_location = ""
while get_location.strip().lower() not in ["n", "y"]:
    get_location = input("Do you want to use your current location? (Y/N) ")

    if get_location.strip().lower() == "y":
        lat, lon = get_current_location()
        if lat is not None and lon is not None:
            place = get_city_from_coords(lat, lon)
            print(f"You are currently in: {place}")
        else:
            print("Could not determine your location. Please try again.")
    elif get_location.strip().lower() == "n":
        place = input("Type in place that you want to info for: ")
    else:
        print("Could not process input. Please try again")

if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")

model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

agent = create_react_agent(model=model, tools=tools)

feature = ""
while feature.strip().lower() not in ["recs", "plan"]:
    feature = input("What do you want to do? (recs, plan): ")
    if feature == "recs":
        rec_type = input("What do you want recommendations for? (ex. restaurants) ")
        input_message = {"role": "user", "content": f"Your task is to come up with a list of {rec_type}s in " + place + "."}
    elif feature == "plan":
        num_days = int(input("How many days? "))
        time_of_year = input("What time of year are you visiting " + place + "? ")
        interests = input("What are your interests? Do you prefer outdoor activities, historical sites, museums, fine dining, or something else? ")
        budget = input("What is your budget for accommodations? ")
        input_message = {"role": "user", "content": f"Your task is to plan a {str(num_days)} day itenerary for {place}. The user who requested this itenerary has answered the following questions:\n\n**What time of year are you visiting?** Answer: {time_of_year}.\n**What interests do you have?** Answer: {interests}.\n**What is your budget for accommodations?** Answer: {budget}.\n\nYou will use this information to create the itenerary. First, find what activities to do, place to go to, and restuaraunts to eat at. Next, find a hotel or apartment to stay at (this is mandatory!). Then, organize these findings in a " + str(num_days) + " day itenerary, organized by day. If the city the user is visiting in does not have many hotels or things to do, then look for experiences in nearby cities."}
    else:
        print("Could not process input. Please try again")

response = agent.invoke({"messages": [input_message]})

"""for step in agent.stream({"messages": [input_message]}, stream_mode="values"):
    step["messages"][-1].pretty_print()"""

print(response["messages"][-1].content)
save = input("Do you want to save this response to files? (Y/N) ")
if save.lower().strip() == "y":
    filename = input("What do you want to save it as? ")
    if filename.split(".")[-1] != "txt":
        filename = filename + ".txt"
    with open(filename, "w") as f:
        f.write(response["messages"][-1].content)