import streamlit as st
import json
import requests
import os
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="airplane",
    layout="centered"
)
GROQ_API_KEY = "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"

@st.cache_data
def load_data():
    import os
    base_path = os.path.dirname(__file__)
    with open(os.path.join(base_path, "flights.json")) as f:
        flights = json.load(f)
    with open(os.path.join(base_path, "hotels.json")) as f:
        hotels = json.load(f)
    with open(os.path.join(base_path, "places.json")) as f:
        places = json.load(f)
    return flights, hotels, places
@tool
def search_flights(source: str, destination: str) -> str:
    """Search for available flights. Args: source city, destination city."""
    try:
        results = [f for f in flights_data
                   if f["from"].lower() == source.lower()
                   and f["to"].lower() == destination.lower()]
        if not results:
            return f"No flights found from {source} to {destination}."
        cheapest = sorted(results, key=lambda x: x["price"])[0]
        return (f"Airline: {cheapest['airline']} | Price: {cheapest['price']} | "
                f"Departure: {cheapest['departure_time']} | Arrival: {cheapest['arrival_time']}")
    except Exception as e:
        return f"Error: {str(e)}"
@tool
def search_hotels(city: str, max_price: int = 99999) -> str:
    """Search for best hotel in a city. Args: city name, optional max price per night."""
    try:
        results = [h for h in hotels_data
                   if h["city"].lower() == city.lower()
                   and h["price_per_night"] <= max_price]
        if not results:
            return f"No hotels found in {city}."
        best = sorted(results, key=lambda x: x["stars"], reverse=True)[0]
        return (f"Hotel: {best['name']} | Stars: {best['stars']} | "
                f"Price: {best['price_per_night']} per night | "
                f"Amenities: {', '.join(best['amenities'])}")
    except Exception as e:
        return f"Error: {str(e)}"
@tool
def search_places(city: str, num_days: int) -> str:
    """Search top attractions. Args: city name, number of days."""
    try:
        results = [p for p in places_data if p["city"].lower() == city.lower()]
        if not results:
            return f"No places found in {city}."
        top_places = sorted(results, key=lambda x: x["rating"], reverse=True)[:num_days * 2]
        itinerary = ""
        for day in range(num_days):
            day_places = top_places[day*2:(day+1)*2]
            names = [f"{p['name']} ({p['type']}, {p['rating']} stars)" for p in day_places]
            itinerary += f"Day {day+1}: {' | '.join(names)}\n"
        return itinerary.strip()
    except Exception as e:
        return f"Error: {str(e)}"
@tool
def get_weather(city: str) -> str:
    """Get weather forecast. Args: city name."""
    COORDS = {
        "delhi": (28.6139, 77.2090), "mumbai": (19.0760, 72.8777),
        "goa": (15.2993, 74.1240), "bangalore": (12.9716, 77.5946),
        "hyderabad": (17.3850, 78.4867), "chennai": (13.0827, 80.2707),
        "kolkata": (22.5726, 88.3639), "jaipur": (26.9124, 75.7873)
    }
    try:
        city_lower = city.strip().lower()
        if city_lower not in COORDS:
            return f"Weather not available for {city}."
        lat, lon = COORDS[city_lower]
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&daily=temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=7")
        data = requests.get(url, timeout=10).json()
        forecast = ""
        for date, mx, mn in zip(data["daily"]["time"][:7],
                                data["daily"]["temperature_2m_max"][:7],
                                data["daily"]["temperature_2m_min"][:7]):
            forecast += f"{date}: Max {mx}C | Min {mn}C\n"
        return f"Weather for {city.title()}:\n{forecast.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"
@tool
def calculate_budget(flight_cost: int, hotel_per_night: int, num_nights: int, daily_expenses: int = 800) -> str:
    """Calculate trip budget. Args: flight cost, hotel per night, number of nights, daily expenses."""
    try:
        hotel_total = hotel_per_night * num_nights
        food_total = daily_expenses * num_nights
        total = flight_cost + hotel_total + food_total
        return (f"Budget Breakdown:\n"
                f"  Flight: {flight_cost}\n"
                f"  Hotel ({num_nights} nights): {hotel_total}\n"
                f"  Food and Travel: {food_total}\n"
                f"  Total: {total}")
    except Exception as e:
        return f"Error: {str(e)}"

@st.cache_resource
def get_agent():
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=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)
    tools = [search_flights, search_hotels, search_places, get_weather, calculate_budget]
    system_prompt = """You are an expert AI travel planning assistant for Indian cities.
Available cities: Delhi, Mumbai, Goa, Bangalore, Hyderabad, Chennai, Kolkata, Jaipur
Steps: 1) search_flights 2) search_hotels 3) get_weather 4) search_places 5) calculate_budget
Use exact prices from tool results in calculate_budget. Never use 0 values."""
    return create_react_agent(model=llm, tools=tools, prompt=system_prompt)

st.title("AI Travel Planner")
st.markdown("Plan your perfect Indian trip with AI")
CITIES = ["Delhi", "Mumbai", "Goa", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Jaipur"]
col1, col2 = st.columns(2)
with col1:
    source = st.selectbox("Travelling From", CITIES, index=1)
with col2:
    destination = st.selectbox("Travelling To", CITIES, index=2)
days = st.slider("Number of Days", min_value=2, max_value=7, value=3)
budget = st.number_input("Your Budget (Rs)", min_value=5000, max_value=200000,
                          value=15000, step=1000)
if st.button("Plan My Trip", use_container_width=True):
    if source == destination:
        st.error("Source and destination cannot be the same city.")
    else:
        with st.spinner("Planning your trip... this may take 20-30 seconds"):
            agent = get_agent()
            query = f"Plan a {days}-day trip to {destination} from {source}. Budget is {budget}."
            result = agent.invoke({"messages": [{"role": "user", "content": query}]})
        st.success("Your itinerary is ready!")
        st.markdown("---")
        st.markdown("### Your Trip Itinerary")
        st.write(result["messages"][-1].content)
