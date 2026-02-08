import wikipedia
import requests
from .llm import llm
from dotenv import load_dotenv
import os

from tavily import TavilyClient

# Load .env file
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

Tavily_API_KEY = os.getenv("Tavily_API_KEY")



def wikipedia_tool(query: str):
    try:
        return wikipedia.summary(query, sentences=3)
    except:
        return "No Wikipedia data found."
    


tavily = TavilyClient(api_key=Tavily_API_KEY)

def tavily_search(query: str, max_results: int = 3):
    """
    Search Tavily and return structured results.
    """
    res = tavily.search(query=query, max_results=max_results)

    if not res["results"]:
        return []

    # Return a structured list instead of a single string
    return [
        {
            "title": r.get("title", "No title"),
            "content": r.get("content", "No summary"),
            "source": r.get("source", "Nepali News")
        }
        for r in res["results"]
    ]



def weather_tool(user_text: str, days: int = 3):
    """
    Fetch weather forecast for a Nepali city mentioned in user_text.
    Returns either a string forecast or a dict with "error".
    """
    if not OPENWEATHER_API_KEY:
        return {"error": "Weather API key missing."}

    # Step 1: Extract city name using LLM
    prompt = f"Extract the city name from this text (Nepal only): '{user_text}'. Respond only with city name."
    city_response = llm.invoke([{"role": "user", "content": prompt}])
    city = city_response.content.strip()

    if not city:
        return {"error": "Could not detect city."}

    # Step 2: Fetch weather from OpenWeatherMap
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": f"{city},NP", "appid": OPENWEATHER_API_KEY, "units": "metric"}

    try:
        res = requests.get(url, params=params)
        if res.status_code != 200:
            return {"error": res.json().get("message", "Unable to fetch weather.")}

        data = res.json()
        forecast_list = data.get("list", [])

        # Step 3: Aggregate per day
        daily = {}
        for entry in forecast_list:
            date = entry["dt_txt"].split(" ")[0]
            if date not in daily:
                daily[date] = {"temps": [], "conds": []}
            daily[date]["temps"].append(entry["main"]["temp"])
            daily[date]["conds"].append(entry["weather"][0]["description"])

        # Step 4: Build readable string
        sorted_dates = sorted(daily.keys())[:days]
        lines = []
        for i, date in enumerate(sorted_dates):
            temps = daily[date]["temps"]
            avg_temp = round(sum(temps) / len(temps), 1)
            conds = daily[date]["conds"]
            main_condition = max(set(conds), key=conds.count)
            lines.append(f"{i+1}) Date: {date}, Avg Temp: {avg_temp}°C, Condition: {main_condition}")

        if not lines:
            return {"error": "No forecast data found."}

        return f"Weather forecast for {data['city']['name']}, {data['city']['country']}:\n" + "\n".join(lines)

    except Exception as e:
        return {"error": str(e)} 


    
def nepali_news_tool(query: str, max_results: int = 5):
    """
    Fetch latest Nepali news using Tavily.
    Returns structured list of articles.
    """
    search_query = f"Nepal {query} site:onlinekhabar.com OR site:setopati.com OR site:ratopati.com"
    articles = tavily_search(search_query, max_results=max_results)

    if not articles:
        return []

    return articles


