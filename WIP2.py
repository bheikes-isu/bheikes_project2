# %%
import openmeteo_requests as omr
import pandas as pd 
import requests_cache
from retry_requests import retry
from geopy.geocoders import Nominatim
from openai import OpenAI
from keys import openai_key
from datetime import datetime 

def chatoutput(activity, weatherdata):
    time= datetime.now()
    client= OpenAI(
    api_key=(openai_key)
    )
    response= client.responses.create(
        model= "gpt-4o",
        instructions= "You are recommending an outfit based on the weather and activity data that will be passed to you",
        input= "The date and time is {time}. These are the weather conditions for today: {weatherdata}. This is the activity that the user will be doing: {activity}."
    )
    return response.output_text



def getcoordinates(userlocation):
    if (userlocation is None or userlocation==""):
        return ""
    geolocator=Nominatim(user_agent="Dress for the Weather")
    location=geolocator.geocode(userlocation)
    return location.latitude, location.longitude
 

def getweather(lat, lon): # get weather data for given lat, lon
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = omr.Client(session = retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m", 
        "forecast_days": 1,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "current": ["temperature_2m"],
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

    # Access hourly temperature data (1D numpy array)
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

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
        "temperature_2m": hourly_temperature_2m
    }
    
    # Create the DataFrame
    hourly_dataframe = pd.DataFrame(data=hourly_data)

    return round(current_temperature_2m, 1), hourly_dataframe, current_date

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




