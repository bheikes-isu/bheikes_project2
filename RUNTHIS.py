import module as module
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta
import pandas as pda

st.set_page_config(
    page_title="Dress for the Weather",
    page_icon="👗",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("Dress for the Weather")
st.caption("Get personalized outfit recommendations based on real-time weather.")

# Ask for location
place = st.text_input("Enter your location")

# Only get weather data if a location is provided
if place:
    with st.spinner("Fetching data..."):
        coordinates = module.getcoordinates(place)
        if coordinates:
            lat, long = coordinates
            weatherdata, hourly_dataframe, current_data, timezone_offset = module.getweather(lat, long)
    
    if coordinates:
        # Show current weather conditions
        st.write(f"### Current Conditions in {place}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Temperature", f"{weatherdata['temperature']}°F")
        with col2:
            st.metric("Wind Speed", f"{weatherdata['wind_speed']} mph")
        with col3:
            st.metric("Precipitation", f"{weatherdata['precipitation']} in")
        
        # Show temperature plot with vertical line at current time
        # Calculate the current time in the location's timezone
        utc_now = datetime.now(timezone.utc)
        location_now = utc_now + timedelta(seconds=timezone_offset)
        
        # Find the closest hour in the dataframe
        hours_list = hourly_dataframe['hour'].tolist()
        closest_hour = min(hours_list, key=lambda x: abs(
            int(x.split(':')[0]) * 60 + int(x.split(':')[1]) - 
            (location_now.hour * 60 + location_now.minute)
        ))
        
        fig = px.line(hourly_dataframe, x="hour", y="temperature_2m", markers=True)
        fig.update_layout(
            xaxis_title="Time (24-hour)",
            yaxis_title="Temperature (°F)",
            title="Today's Temperature Forecast"
        )
        
        # Add vertical line at current time using a shape
        fig.add_shape(
            type="line",
            x0=closest_hour, x1=closest_hour,
            y0=0, y1=1,
            yref="paper",
            line=dict(color="red", width=2, dash="dash")
        )
        fig.add_annotation(
            x=closest_hour,
            y=1,
            yref="paper",
            text="Now",
            showarrow=False,
            yshift=10
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        #Ask for activity and provide recommendations
        st.write("---")
        activity = st.selectbox("Select your activity", module.activities)
        
        if activity:
            st.write("### Outfit Recommendation")
            # Get next 6 hours of forecast for context
            next_hours = hourly_dataframe.head(6)
            with st.spinner("AI is generating your recommendation..."):
                recommendation = module.chatoutput(activity, weatherdata, place, next_hours)
            st.write(recommendation)
        else:
            st.info("Please select an activity to get outfit recommendations.")
    else:
        st.warning("Could not find this location. Please try again.")
else:
    st.info("Please enter a location to see the weather.")
