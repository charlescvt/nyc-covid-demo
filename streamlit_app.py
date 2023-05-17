
################################################
################################################

# Imports

import streamlit as st
from PIL import Image
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt, timedelta
from streamlit_lottie import st_lottie_spinner
from st_pages import show_pages, Page
import time

# import random
# from itertools import cycle
# from shapely.geometry import Polygon
# import geopandas as gpd
# from streamlit_lottie import st_lottie
# import streamlit.components.v1 as components


################################################
################################################

# Functions

# Define a function that returns a lottie image from JSON
def get_lottie(path):
    with open(path, "r") as f:
        lottie_image = json.load(f)

    return lottie_image

# Caching all these data loading functions in the start allows for faster page interaction
st.cache_data()
def load_chart_data():
    # Load the data
    data = pd.read_csv('input/clean_data.csv', low_memory=False)
    data['date'] = pd.to_datetime(data['date'])
    data = data[['stop_name', 'date', 'entries', 'line', 'borough', 'daytime_routes', 'division',
        'structure', 'gtfs_longitude', 'gtfs_latitude', 'complex_id']]

    # Filter the data based on the selected date range
    data = data[(data['date'] >= start_date) & (data['date'] <=  end_date)].reset_index(drop=True)

    return data

@st.cache_data
def load_map_data():
    map_data = pd.read_csv('output/nta_fulldata.csv')

    return map_data

# Ideas for later if useful
# Function to temporarily shows lottie animation
def spin():
    lottie = get_lottie("objects/resize.json")

    if 'spin_wait' in st.session_state:
        with st_lottie_spinner(lottie, key="You can always resize the side bar!", height=100):
            time.sleep(2)
            st.session_state.spinned = True

# Function to write text letter by letter
def writer(text):
    if "writer_wait" in st.session_state:
        t = st.empty()
        for i in range(len(text) + 1):
            t.markdown("#### %s..." % text[0:i])
            time.sleep(0.05)

# Placed after everything has run, waiter return a session state variable which can activate other funcitons
# Since Streamlit runs Top-Down, only way to activate function after the rest without placing it at the top
def waiter(x_seconds, session_var):

    time.sleep(x_seconds)
    st.session_state[session_var] = True


################################################
################################################

# Page parameters

# Set the page layout
icon = Image.open("objects/cybersyn_icon.png")
lottie_subway = get_lottie("objects/subway_image.json")

st.set_page_config(page_title="Cybersyn - NYC Subway Traffic Dataset",
                   layout="wide", page_icon=icon)

# Renaming pages
show_pages(
    [
        Page("streamlit_app.py", "Data Hub"),
        Page("pages/1_Visualizations.py", "Story-Teller")
    ]
)

# Import all CSS configurations
with open("filtered_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


################################################
################################################

# Sidebar parameters

st.sidebar.write("# Parameters")

initial_start_date = pd.to_datetime("01-01-2020")
initial_end_date = pd.to_datetime("06-30-2020")

# Initialize session_state variables
if 'start_date' not in st.session_state:
    st.session_state.start_date = initial_start_date
if 'end_date' not in st.session_state:
    st.session_state.end_date = initial_end_date

# Select boxes session states
if 'selected_borough' not in st.session_state:
    st.session_state.selected_borough = ''
if 'selected_line' not in st.session_state:
    st.session_state.selected_line = ''
if 'selected_stop_name' not in st.session_state:
    st.session_state.selected_stop_name = ''
if 'selected_division' not in st.session_state:
    st.session_state.selected_division = ''

display_options = ['Chart', 'Map']
selected_display = st.sidebar.selectbox('Select display', display_options)

if selected_display == "Chart":

    st.sidebar.write("---")
    start_date = pd.to_datetime(st.sidebar.date_input('Start Date:', value=st.session_state.start_date,
                                    min_value=pd.to_datetime("01-01-2020"),
                                    max_value=st.session_state.end_date - timedelta(days=1)))

    end_date = pd.to_datetime(st.sidebar.date_input('Select an end start:', value=st.session_state.end_date,
                                    min_value=start_date + timedelta(days=1),
                                    max_value=pd.to_datetime("06-30-2020")))

    st.sidebar.text("")

    # Update session_state variables
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date


################################################
################################################

# Introduction

# Title
with st.container():
    one, two, three = st.columns([5,1,1])
    with one:
        st.write("#  MTA Turnstile Dataset")
        st.markdown("""<h3> Understanding the early impact of COVID-19 <br> on NYC Public Transportation</h3>""", unsafe_allow_html=True)
   # Lottie animation integration
   # with three:
    #     lottie_url = st_lottie(lottie_subway, width=280)


# Dataset description
with st.container():

    st.markdown("""
    The Metropolitan Transportation Authority (MTA) collects data from the turnstiles
    in its subway stations to provide an overall view of traffic in NYC public transport. \n
    The raw data can be found [here](http://web.mta.info/developers/turnstile.html)
    but we recommend you check out our cleaned dataset below. It's free!
    """)

# This would play the lottie resize icon and a text (activated by waiter )

# spin_cols = st.columns([1,10])
# with spin_cols[0]:
#     spin()
#
# writer("Don't forget you can resize the spin bar! :)")

################################################
################################################

################################################
################################################

st.text("")
st.text("")
st.text("")

a,b,c,d,e,f = st.columns([1,2,2,1,1,1])
with c:
    st.markdown("### Explore the Data")

st.write("---")

# Chart rendering function

def render_df_chart():

    data = load_chart_data()

    total_entries = data.groupby(["date"])["entries"].sum().reset_index()


    # Create a dictionary to store the selected filter values
    selected_filters = {
        'stop_name': [],
        'line': [],
        'borough': [],
        'division': []
    }

    # Create a copy of the data for filtering
    filtered_data = data.copy()

    # Create columns for select boxes
    column_list = st.columns([2,2,2,3])

    activator = False

    # Borough filter
    filtered_boroughs = list(sorted(filtered_data['borough'].dropna().unique()))
    st.session_state.selected_borough = column_list[0].multiselect('Borough', filtered_boroughs, default=[])
    if st.session_state.selected_borough:
        filtered_data = filtered_data[filtered_data['borough'].isin(st.session_state.selected_borough)]
        activator = True

    # Division filter
    filtered_divisions = list(sorted(filtered_data['division'].dropna().unique()))
    st.session_state.selected_division = column_list[1].multiselect('Division', filtered_divisions, default=[])
    if st.session_state.selected_division:
        filtered_data = filtered_data[filtered_data['division'].isin(st.session_state.selected_division)]
        activator = True

    # Line filter
    filtered_lines = list(sorted(filtered_data['line'].dropna().unique()))
    st.session_state.selected_line = column_list[2].multiselect('Line', filtered_lines, default=[])
    if st.session_state.selected_line:
        filtered_data = filtered_data[filtered_data['line'].isin(st.session_state.selected_line)]
        activator = True

    # Stop name filter
    filtered_stop_names = list(sorted(filtered_data['stop_name'].dropna().unique()))
    st.session_state.selected_stop_name = column_list[3].multiselect('Stop Name', filtered_stop_names, default=[])
    if st.session_state.selected_stop_name:
        filtered_data = filtered_data[filtered_data['stop_name'].isin(st.session_state.selected_stop_name)]
        activator = True


    filtered_data = filtered_data.sort_values(["line", "stop_name", "date"])

    x1 = total_entries["date"]
    y1 = total_entries["entries"]

    fig = go.Figure()

    # Add the first line to the figure
    fig.add_trace(go.Scatter(x=x1, y=y1,
                             name="Total Entries",
                             mode="lines", line=dict(color="#1c7575")))

    fig.update_layout(yaxis=dict(title="Total Entries"),
                    width = 920, height=400,
                    margin=dict(t=15, b=2, l=10, r=10),
                    showlegend=True,
                    legend=dict(x=1, y=.95, xanchor="right", yanchor="top"),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)")

    if activator:
        x2 = filtered_data["date"]
        y2 = filtered_data.groupby(["date"])["entries"].sum()

        # Add the second line to the figure with a separate y-axis
        fig.add_trace(go.Scatter(x=x2, y=y2, name="Filtered Entries",
                                 mode="lines", line=dict(color="#e38a8a"), yaxis="y2"))

        # Update the layout to show the second y-axis
        fig.update_layout(
            yaxis=dict(title="Total Entries"),
            yaxis2=dict(title="Filtered Entries",
                        side="right", overlaying="y", showgrid=False),
            width = 920, height=400, margin=dict(t=0, b=0, l=0, r=0),
            legend=dict(x=1, y=.95, xanchor="right", yanchor="top"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
                    )

    df_display, chart_display = st.columns([4,5])

    # Display the filtered dataframe and chart
    with df_display:
        st.write("#### Raw Data")
        pretty_df = filtered_data.copy().reset_index(drop=True)
        pretty_df["date"] = pretty_df["date"].dt.date

        st.write(pretty_df)

    with chart_display:
        st.write("#### Entries per day")
        st.plotly_chart(fig, use_container_width=True)


################################################
################################################

# Map rendering function

def render_df_map():
    # Load your data
    # -> caching original data load and calling a copy of it prevents reloading data with every user interaction

    map_df = load_map_data()

    filtered_map_df = map_df.copy()
    filtered_map_df = filtered_map_df[["NTACode", "NTAName", "borough", "entries", "population", "entries_ratio", "geometry"]]

    # Create a dictionary to store the selected filter values
    selected_filters = {
        'borough': []
    }


    # Create columns for select boxes
    column_list = st.columns(3)

    # Create select boxes for each filter
    for i, column in enumerate(selected_filters.keys()):
        selected_filters[column] = column_list[0].multiselect(
            f"Select {column}",
            options=list(sorted(filtered_map_df[column].dropna().unique())),
            default=[]
        )

    centroid_coordinates = {
    'Bronx': (40.8448, -73.8648),
    'Brooklyn': (40.6782, -73.9442),
    'Manhattan': (40.7831, -73.9712),
    'Queens': (40.7282, -73.7949),
    'Staten Island': (40.5795, -74.1502)
    }

    selected_boroughs = selected_filters['borough']
    if selected_boroughs:
        centroid_lat_list = []
        centroid_lon_list = []
        for borough in selected_boroughs:
            if borough in centroid_coordinates:
                centroid_lat, centroid_lon = centroid_coordinates[borough]
                centroid_lat_list.append(centroid_lat)
                centroid_lon_list.append(centroid_lon)
        if centroid_lat_list and centroid_lon_list:
            centroid_lat = sum(centroid_lat_list) / len(centroid_lat_list)
            centroid_lon = sum(centroid_lon_list) / len(centroid_lon_list)
        else:
            centroid_lat, centroid_lon = 40.7128, -74.0060  # Default to New York
    else:
        centroid_lat, centroid_lon = 40.7128, -74.0060  # Default to New York


    for column, values in selected_filters.items():
        if values:
            filtered_map_df = filtered_map_df[filtered_map_df[column].isin(values)]


    # Create metrics select_box and variable for map color paramater
    metrics = {"Entries": "entries",
               "Population": "population",
               "Log-Ratio of Entries / Population (parks & cemiteries not included)": "entries_ratio"}
    selected_metric = column_list[1].selectbox("Choose a metric", list(metrics.keys()))


    # Create stations to exclude select_box (mainly to remove outliers)
    stations = filtered_map_df.sort_values("entries", ascending=False).NTAName.unique()
    selected_exclude = column_list[2].multiselect("Exclude a station",options=stations)
    # Apply station filter to dataframe
    filtered_map_df = filtered_map_df[~filtered_map_df['NTAName'].isin(selected_exclude)].reset_index(drop=True)


    # Load GeoJSON file
    with open("input/nyc_nta.json") as f:
        geojson = json.load(f)

    # Merge the dataframe with the GeoJSON features based on a common identifier
    for feature in geojson["features"]:
        feature['id'] = feature['properties']['NTACode']  # adjust 'NTACode' to match the data

    # Set a zoom if only one borough selected
    map_zoom = 9
    if len(selected_boroughs) == 1:
        map_zoom = 9.5

    fig = px.choropleth_mapbox(filtered_map_df,
                            geojson=geojson,
                            locations='NTACode', # change to your identifier column
                            color=metrics[selected_metric], # or 'entries' or 'entries_ratio'
                            featureidkey="properties.NTACode", # matches the identifier column in the GeoJSON
                            hover_data="NTAName",
                            color_continuous_scale="purples_r",
                            mapbox_style="carto-darkmatter",
                            center={"lat": centroid_lat, "lon": centroid_lon},
                            zoom=map_zoom)


    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                    width=1000, height=500,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",)

    df_display, map_display = st.columns([2,3])

    # Display the filtered dataframe and chart
    with df_display:
        st.write("#### Raw Data")
        st.dataframe(filtered_map_df, width=750, height=500)

    with map_display:
        st.write("#### Mapping by neighborhood")
        st.plotly_chart(fig, use_container_width=True)

# Create a Streamlit menu to choose the display

if selected_display == "Chart":
    render_df_chart()

    # Activate for spin or writer
    # waiter(2, "spin_wait")
    # waiter(0, "writer_wait")


if selected_display == "Map":
    render_df_map()


with st.sidebar:
    st.write("---")
    st.write("Questions or Feedback, [Contact Us](mailto:support@cybersym.com)")
    st.write("Created by [Cybersyn](https://app.snowflake.com/marketplace/listings/Cybersyn%2C%20Inc)")

st.write("---")
