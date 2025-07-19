import getpass
import os
import requests
import tools
import location_utils
from geopy.geocoders import Nominatim
import wikipedia
from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
import requests
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model

# search = TavilySearch(max_results=2)
model_tools = [tools.get_yelp_recommendations]

get_location = ""
while get_location.strip().lower() not in ["n", "y"]:
    get_location = input("Do you want to use your current location? (Y/N) ")

    if get_location.strip().lower() == "y":
        lat, lon = location_utils.get_current_location()
        if lat is not None and lon is not None:
            place = location_utils.get_city_from_coords(lat, lon)
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

agent = create_react_agent(model=model, tools=model_tools)

feature = ""
while feature.strip().lower() not in ["recs", "plan"]:
    feature = input("What do you want to do? (recs, plan): ")
    if feature == "recs":
        rec_type = input("What do you want recommendations for? Type out a single keyword, or multiple keywords separated by commas (ex. restaurants, dining, museums) ")
        categories = [c.strip() for c in rec_type.split(",")]
        if len(categories) > 1:
            categories[-1] = "and " + categories[-1]
        input_message = {"role": "user", "content": f"Your task is to come up with a list of {", ".join(categories)} in " + place + "."}
    elif feature == "plan":
        num_days = int(input("How many days? "))
        time_of_year = input("What time of year are you visiting " + place + "? ")
        interests = input("What are your interests? Do you prefer outdoor activities, historical sites, museums, fine dining, or something else? ")
        budget = input("What is your budget for accommodations? ")
        input_message = {"role": "user", "content": f"""Plan a {num_days}-day itinerary for a trip to {place}. User preferences:
                         
                         - Time of year: {time_of_year}
                         - Interests: {interests}
                         - Accommodation budget: {budget}

                         The itinerary should include activities, places to eat, and recommended places to stay. Organize the response by day."""}
    else:
        print("Could not process input. Please try again")

response = agent.invoke({"messages": [input_message]})

for step in agent.stream({"messages": [input_message]}, stream_mode="values"):
    step["messages"][-1].pretty_print()

print(response["messages"][-1].content)
save = input("Do you want to save this response to files? (Y/N) ")
if save.lower().strip() == "y":
    filename = input("What do you want to save it as? ")
    if filename.split(".")[-1] != "txt":
        filename = filename + ".txt"
    with open(filename, "w") as f:
        f.write(response["messages"][-1].content)