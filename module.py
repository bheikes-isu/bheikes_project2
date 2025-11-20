# %%
import openmeteo_requests as omr
import pandas as pd 
import requests_cache
from retry_requests import retry
from geopy.geocoders import Nominatim
from openai import OpenAI
from keys import openai_key
from datetime import datetime 

def chatoutput(activity, current_weather, location, hourly_forecast=None):
    time= datetime.now()
    client= OpenAI(
    api_key=(openai_key)
    )
    
    # Format current weather (including wind and precipitation) for the prompt
    current_text = f"Current conditions at {location}:\n"
    current_text += f"- Temperature: {current_weather['temperature']}°F\n"
    current_text += f"- Wind Speed: {current_weather['wind_speed']} mph\n"
    current_text += f"- Precipitation: {current_weather['precipitation']} inches"
    
    # Format hourly forecast for the prompt
    forecast_text = ""
    if hourly_forecast is not None:
        forecast_text = f"\n\nHourly forecast for the next few hours:\n{hourly_forecast.to_string(index=False)}"
    
    response= client.responses.create(
        model= "gpt-4o",
        instructions= f"You are recommending an outfit based on the weather and activity data for {location}. Provide practical, specific clothing recommendations. Consider temperature, wind and precipitation values for the next 6 hours. IMPORTANT: Do NOT use markdown headings (# ## ###). Instead, format section titles using **bold text** only (e.g., **Base Layer:** not ## Base Layer). Use bullet points for lists. ",
        input= f"The date and time is {time}. {current_text}. This is the activity that the user will be doing: {activity}.{forecast_text}"
    )
    print(forecast_text)
    return response.output_text



def getcoordinates(userlocation):
    if (userlocation is None or userlocation==""):
        return ""
    try:
        geolocator=Nominatim(user_agent="Dress for the Weather")
        location=geolocator.geocode(userlocation, timeout=10)
        if location:
            return location.latitude, location.longitude
        return ""
    except Exception as e:
        print(f"Geocoding error: {e}")
        return ""
 

def getweather(lat, lon): # get weather data for given lat, lon
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = omr.Client(session = retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "wind_speed_10m", "precipitation"], 
        "forecast_days": 1,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "current": ["temperature_2m", "wind_speed_10m", "precipitation"], #CH get wind and precip
        "timezone": "auto", # needed for local time conversion
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")
    #get rid of print statements
    # You could also return elevation and timezone difference if needed

    # Process hourly data. The order of variables needs to be the same as requested.
    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_wind_speed = current.Variables(1).Value()
    current_precipitation = current.Variables(2).Value()

    # Access hourly data (1D numpy arrays)
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_wind_speed = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()

    # You can also get the hourly timestamps (secs since Jan 1, 1970)
    hourly_time = hourly.Time()
    hourly_time_end = hourly.TimeEnd()

    #
    # Create a pandas DataFrame with the hourly data
    #

    # Get the timezone offset for this location
    timezone_offset_seconds = response.UtcOffsetSeconds()
    
    # Convert Unix timestamps to UTC datetime objects first
    start_time_utc = pd.to_datetime(hourly_time, unit="s")
    end_time_utc = pd.to_datetime(hourly_time_end, unit="s")
    
    #  Convert to local time by adding the timezone offset
    start_time_local = start_time_utc + pd.Timedelta(seconds=timezone_offset_seconds)
    end_time_local = end_time_utc + pd.Timedelta(seconds=timezone_offset_seconds)
    
    # Get the interval between data points (usually 3600 seconds = 1 hour)
    interval_seconds = hourly.Interval()
    time_step = pd.Timedelta(seconds=interval_seconds)
    
    # Create a range of dates from start to end with the given interval (in local time)
    date_range_local = pd.date_range(
        start=start_time_local,
        end=end_time_local,
        freq=time_step,
        inclusive="left"  # Don't include the end time
    )
    
    # Extract just the hour from the datetime objects
    hours_only = date_range_local.strftime('%H:%S')  # Format as HH:MM (e.g., "14:00")
    
    # Get the current date (using the first timestamp)
    current_date = date_range_local[0].date()
    
    # Create the dictionary for the DataFrame
    hourly_data = {
        "hour": hours_only,
        "temperature_2m": hourly_temperature_2m,
        "wind_speed_10m": hourly_wind_speed,
        "precipitation": hourly_precipitation
    }
    
    # Create the DataFrame
    hourly_dataframe = pd.DataFrame(data=hourly_data)
    
    # Create current weather dictionary
    current_weather = {
        "temperature": round(current_temperature_2m, 1),
        "wind_speed": round(current_wind_speed, 1),
        "precipitation": round(current_precipitation, 2)
    }

    return current_weather, hourly_dataframe, current_date, timezone_offset_seconds

def weather (temperature):
    if temperature > 80:
        return "Shorts and a t-shirt"
    elif 70 <= temperature <= 80:
        return "Shorts and a t-shirt"
    elif 60 <= temperature <= 70:
        return "Shorts and a t-shirt or a light jacket"
    elif 50 <= temperature < 60:
        return "pants and a longsleeve"
    elif 40 <= temperature < 50:
        return "pants and a longsleeve with a light jacket"
    
activities = ["", "Going for a run", "Going out", "Fancy dinner", "Going for a walk", "Coffee run", "Hiking", "Going to an outdoor sporting event", "Indoor Concert", "School/work"]




