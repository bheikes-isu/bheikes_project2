import WIP2
import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Dress for the Weather")
place = st.text_input("Enter your location")
activity = st.selectbox("Select your activity", WIP2.activities)
lat,long= WIP2.getcoordinates(place)
weatherdata, hourly_dataframe, current_data= WIP2.getweather(lat,long)
st.write(f"Current Temperature in {place}: {weatherdata}°F")
st.write("Suggested outfit is:", WIP2.weather(weatherdata))

#Trying to incorporate the Plotly weather graph into Streamlit
#fig_linechart = px.line(hourly_dataframe, x="hour", y="temperature_2m", markers=True)
# Update the configuration to enable lasso selection
#fig_linechart.update_layout(dragmode="select", xaxis_title="Time", yaxis_title="Temperature")
#event_data = st.plotly_chart(fig_linechart, on_select="rerun")
