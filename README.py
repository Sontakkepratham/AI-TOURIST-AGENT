import streamlit as st
import json
import requests
import os
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
 
# --- Page Config ---
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="centered"
)
 
# --- GROQ API KEY---
GROQ_API_KEY = "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"

GROQ_API_KEY = st.sidebar.text_input(
    "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", 
    type="123456789",
    placeholder="gsk_..."
)

if not GROQ_API_KEY:
    st.warning("Please enter your Groq API key in the sidebar to continue.")
    st.stop()
 
# --- Load Data ---
@st.cache_data
def load_data():
    base_path = os.path.dirname(__file__)
    with open(os.path.join(base_path, "flights.json")) as f:
        flights = json.load(f)
    with open(os.path.join(base_path, "hotels.json")) as f:
        hotels = json.load(f)
    with open(os.path.join(base_path, "places.json")) as f:
        places = json.load(f)
    return flights, hotels, places
 
flights_data, hotels_data, places_data = load_data()
 
# --- Tools ---
@tool
def search_flights(source: str, destination: str) -> str:
    """
    Search for available flights between two cities.
    Args:
        source: departure city name e.g. Mumbai
        destination: arrival city name e.g. Goa
    Returns cheapest available flight.
    """
    try:
        results = [
            f for f in flights_data
            if f["from"].lower() == source.lower()
            and f["to"].lower() == destination.lower()
        ]
        if not results:
            return f"No flights found from {source} to {destination}."
        cheapest = sorted(results, key=lambda x: x["price"])[0]
        return (
            f"Airline: {cheapest['airline']} | "
            f"Price: {cheapest['price']} | "
            f"Departure: {cheapest['departure_time']} | "
            f"Arrival: {cheapest['arrival_time']}"
        )
    except Exception as e:
        return f"Error searching flights: {str(e)}"
 
 
@tool
def search_hotels(city: str, max_price: int = 99999) -> str:
    """
    Search for best available hotel in a city.
    Args:
        city: city name e.g. Goa
        max_price: maximum price per night in rupees default 99999
    Returns highest rated hotel within budget.
    """
    try:
        results = [
            h for h in hotels_data
            if h["city"].lower() == city.lower()
            and h["price_per_night"] <= max_price
        ]
        if not results:
            return f"No hotels found in {city} under {max_price} per night."
        best = sorted(results, key=lambda x: x["stars"], reverse=True)[0]
        return (
            f"Hotel: {best['name']} | "
            f"Stars: {best['stars']} | "
            f"Price: {best['price_per_night']} per night | "
            f"Amenities: {', '.join(best['amenities'])}"
        )
    except Exception as e:
        return f"Error searching hotels: {str(e)}"
 
 
@tool
def search_places(city: str, num_days: int) -> str:
    """
    Search top attractions and places to visit in a city.
    Args:
        city: city name e.g. Goa
        num_days: number of days for the trip e.g. 3
    Returns day-wise itinerary of top rated places.
    """
    try:
        results = [
            p for p in places_data
            if p["city"].lower() == city.lower()
        ]
        if not results:
            return f"No places found in {city}."
        top_places = sorted(results, key=lambda x: x["rating"], reverse=True)
        top_places = top_places[:num_days * 2]
        itinerary = ""
        for day in range(num_days):
            day_places = top_places[day*2:(day+1)*2]
            place_names = [
                f"{p['name']} ({p['type']}, {p['rating']} stars)"
                for p in day_places
            ]
            itinerary += f"Day {day+1}: {' | '.join(place_names)}\n"
        return itinerary.strip()
    except Exception as e:
        return f"Error searching places: {str(e)}"
 
 
@tool
def get_weather(city: str) -> str:
    """
    Get 7-day weather forecast for a city.
    Args:
        city: city name e.g. Goa
    Returns day-wise temperature forecast.
    """
    CITY_COORDS = {
        "delhi": (28.6139, 77.2090),
        "mumbai": (19.0760, 72.8777),
        "goa": (15.2993, 74.1240),
        "bangalore": (12.9716, 77.5946),
        "hyderabad": (17.3850, 78.4867),
        "chennai": (13.0827, 80.2707),
        "kolkata": (22.5726, 88.3639),
        "jaipur": (26.9124, 75.7873)
    }
    try:
        city_lower = city.strip().lower()
        if city_lower not in CITY_COORDS:
            return f"Weather not available for {city}."
        lat, lon = CITY_COORDS[city_lower]
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&timezone=auto&forecast_days=7"
        )
        data = requests.get(url, timeout=10).json()
        forecast = ""
        for date, mx, mn in zip(
            data["daily"]["time"][:7],
            data["daily"]["temperature_2m_max"][:7],
            data["daily"]["temperature_2m_min"][:7]
        ):
            forecast += f"{date}: Max {mx}C | Min {mn}C\n"
        return f"Weather for {city.title()}:\n{forecast.strip()}"
    except Exception as e:
        return f"Error fetching weather: {str(e)}"
 
 
@tool
def calculate_budget(flight_cost: int, hotel_per_night: int, num_nights: int, daily_expenses: int = 800) -> str:
    """
    Calculate total trip budget breakdown.
    Args:
        flight_cost: flight price in rupees use exact number from search_flights result
        hotel_per_night: hotel price per night in rupees use exact number from search_hotels result
        num_nights: number of nights staying
        daily_expenses: estimated daily food and local travel cost default 800
    Returns complete budget breakdown with total.
    """
    try:
        hotel_total = hotel_per_night * num_nights
        food_total = daily_expenses * num_nights
        grand_total = flight_cost + hotel_total + food_total
        return (
            f"Budget Breakdown:\n"
            f"  Flight:                  {flight_cost}\n"
            f"  Hotel ({num_nights} nights): {hotel_total}\n"
            f"  Food and Local Travel:   {food_total}\n"
            f"  ---------------------------------\n"
            f"  Total:                   {grand_total}"
        )
    except Exception as e:
        return f"Error calculating budget: {str(e)}"
 
 
# --- Agent ---
@st.cache_resource
def get_agent():
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=GROQ_API_KEY
    )
    tools = [search_flights, search_hotels, search_places, get_weather, calculate_budget]
    system_prompt = """You are an expert AI travel planning assistant for Indian cities.
Available cities: Delhi, Mumbai, Goa, Bangalore, Hyderabad, Chennai, Kolkata, Jaipur
Steps: 1) search_flights 2) search_hotels 3) get_weather 4) search_places 5) calculate_budget
Use exact prices from tool results in calculate_budget. Never use 0 values."""
    return create_react_agent(model=llm, tools=tools, prompt=system_prompt) 
 
# --- UI ---
st.title("✈️ AI Travel Planner")
st.markdown("Plan your perfect Indian trip powered by Gemini AI")
st.markdown("---")
 
CITIES = ["Delhi", "Mumbai", "Goa", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Jaipur"]
 
col1, col2 = st.columns(2)
with col1:
    source = st.selectbox("Travelling From", CITIES, index=1)
with col2:
    destination = st.selectbox("Travelling To", CITIES, index=2)
 
days = st.slider("Number of Days", min_value=2, max_value=7, value=3)
budget = st.number_input(
    "Your Budget (Rs)",
    min_value=5000,
    max_value=200000,
    value=15000,
    step=1000
)
 
if st.button("Plan My Trip ✈️", use_container_width=True):
    if source == destination:
        st.error("Source and destination cannot be the same city.")
    else:
        try:
            with st.spinner("Planning your trip... this may take 20-30 seconds"):
                agent = get_agent()
                query = f"Plan a {days}-day trip to {destination} from {source}. Budget is {budget}."
                result = agent.invoke({
                    "messages": [{"role": "user", "content": query}]
                })
            st.success("Your itinerary is ready!")
            st.markdown("---")
            st.markdown("### Your Trip Itinerary")
            st.write(result["messages"][-1].content)
        except Exception as e:
            st.error(f"Full error: {str(e)}")
