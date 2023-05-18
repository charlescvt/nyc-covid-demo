import numpy as np
import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
import plotly.express as px
from PIL import Image
import random
import time
from datetime import datetime as dt, timedelta
from itertools import cycle
import json


################################################
################################################

# Functions

# DYN MAP
@st.cache_data
def load_data():
    # coordinates for each station
    data = pd.read_csv('input/clean_data.csv', low_memory=False, parse_dates=['date'])
    coords = data[["gtfs_latitude", "gtfs_longitude", "stop_name"]]

    # pivot table showing daily entries for each station
    counts_df = pd.read_csv('input/station_entry_pivot.csv', parse_dates=['date'],
                            index_col="date")


    return data, coords, counts_df

# CHORO MAP
@st.cache_data
def load_map_data_daily():
    map_data = pd.read_csv('output/nta_fulldata_d.csv')

    return map_data


################################################
################################################

# Page parameters

# Setup page layout
icon = Image.open("objects/cybersyn_icon.png")

st.set_page_config(page_title="Cybersyn - NYC Subway Traffic Dataset",
                   layout="wide", page_icon=icon)


# Set Body, Header and Sidebar background
with open("filtered_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


st.sidebar.header("Parameters")

################################################
################################################

# Sidebar parameters and their session state
date_format = "%Y-%m-%d"
# Date input
initial_end_date = pd.to_datetime("2020-06-30", format = date_format)
initial_start_date = pd.to_datetime("2020-01-01", format = date_format)

# Initialize session_state variables
if 'start_date' not in st.session_state:
    st.session_state.start_date = initial_start_date
if 'end_date' not in st.session_state:
    st.session_state.end_date = initial_end_date


menu_options = ['Neighborhood Map', 'Dynamic Map']
selected_display = st.sidebar.selectbox('Select display', menu_options)


st.sidebar.write("---")

start_date = pd.to_datetime(st.sidebar.date_input('Start Date:', value=st.session_state.start_date,
                                min_value=initial_start_date,
                                max_value=st.session_state.end_date - timedelta(days=1)))

end_date = pd.to_datetime(st.sidebar.date_input('Select an end start:', value=st.session_state.end_date,
                                min_value=start_date + timedelta(days=1),
                                max_value=initial_end_date))

st.sidebar.text("")

# Update session_state variables
st.session_state.start_date = start_date
st.session_state.end_date = end_date

################################################
################################################

# Introduction

st.write("# Cybersyn: MTA Turnstile Dataset")
st.write("###")
st.write("---")


data_df, coords_df, counts_df_df = load_data()

# Defining each graph's function


def render_df_map():

    # Load your data
    # -> caching original data load and calling a copy of it prevents reloading data with every user interaction
    map_df = load_map_data_daily()

    filtered_map_df = map_df.copy()
    filtered_map_df['date'] = pd.to_datetime(filtered_map_df['date'], format = date_format)

    filtered_map_df = filtered_map_df[filtered_map_df["date"].between(start_date, end_date)]


    ##################################

    # Filters

    # Create columns for select boxes
    column_list = st.columns([5,5,5,3])


    selected_boroughs = column_list[0].multiselect(
    "Select borough",
    options=sorted(filtered_map_df['borough'].dropna().unique()),
    default=[]
    )

    #######
    # Getting coordinates of selected borough to zoom map

    centroid_coordinates = {
    'Bronx': (40.8448, -73.8648),
    'Brooklyn': (40.6782, -73.9442),
    'Manhattan': (40.7831, -73.9712),
    'Queens': (40.7282, -73.7949),
    'Staten Island': (40.5795, -74.1502)
    }

    # Calculating the centroid
    if selected_boroughs:
        total_lat = total_lon = 0
        for borough in selected_boroughs:
            if borough in centroid_coordinates:
                lat, lon = centroid_coordinates[borough]
                total_lat += lat
                total_lon += lon
        centroid_lat = total_lat / len(selected_boroughs)
        centroid_lon = total_lon / len(selected_boroughs)
    else:
        centroid_lat, centroid_lon = 40.7128, -74.0060  # Default to New York

    # Filtering the dataframe
    if selected_boroughs:
        filtered_map_df = filtered_map_df[filtered_map_df['borough'].isin(selected_boroughs)]




    ########
    # Select the metric to influence the map's color scale
    metrics = {"Entries": "entries",
               "Population": "population",
               "Log-Ratio of Entries / Population (parks & cemiteries not included)": "entries_ratio"}
    selected_metric = column_list[1].selectbox("Choose a metric", list(metrics.keys()))

    #######
    # Select any station to exclue (outliers mess with the coloring)
    stations = filtered_map_df.sort_values("entries", ascending=False).NTAName.unique()
    selected_exclude = column_list[2].multiselect("Exclude a station",options=stations)

    # Apply station filter to dataframe
    filtered_map_df = filtered_map_df[~filtered_map_df['NTAName'].isin(selected_exclude)].reset_index(drop=True)

    som_options = {"Sum": "sum",
                   "Mean": "mean"}

    #######
    # Select sum or mean for aggregation of entries over the selected period
    if selected_metric== "Entries":
        st.session_state.sum_or_mean = column_list[3].selectbox("Sum or Mean", list(som_options.keys()))

    # Group the dataframe to map all selected fields over the date interval (apply sum_or_mean option)
    filtered_map_df = filtered_map_df.groupby("NTACode").agg({
        'NTAName': 'first',
        'borough': 'first',
        'entries': som_options[st.session_state.sum_or_mean] if st.session_state.sum_or_mean in som_options else 'sum',
        'population': 'last',
        'entries_ratio': 'mean',
        'geometry': 'first'}).reset_index()
    
    # Reordering columns
    filtered_map_df = filtered_map_df[["NTAName", "borough", "entries",
                                       "population", "entries_ratio", "NTACode",
                                       "geometry"]]

    # Load GeoJSON file
    with open("input/nyc_nta.json") as f:
        geojson = json.load(f)

    # Merge the dataframe with the GeoJSON features based on a common identifier
    for feature in geojson["features"]:
        feature['id'] = feature['properties']['NTACode']  # adjust 'NTACode' to match the data

    # Set a zoom if only one borough selected, zoom back out if more
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



def dynamic_map():
    global animation_speed

    # Use a dataframe copy to allow modifications
    coords = coords_df.copy()
    counts_df = counts_df_df.copy()

    year_month_day_values = [(d.year, d.month, d.day) for d in counts_df.index if start_date <= d <= end_date]
    year, month, day = year_month_day_values[0]

    # Setup presentation widgets and placeholders

    st.write("### Dynamic Map: Daily entries per station in NYC")
    st.write("---")

    # Setup presentation widgets and placeholders
    col1, col2 = st.columns([5,3])

    col2.write("#")
    col2.write("#")
    col2.write("---")

    date_value = st.empty()
    day_slider = st.empty()


    map_placeholder = col1.empty()
    date_placeholder = col2.empty()
    slider_placeholder = col2.empty()


    def render_slider(year, month, day):
        key = random.random() if animation_speed else None

        slider_value = dt(year, month, day)
        date_index = year_month_day_values.index((year, month, day))

        slider_value = slider_placeholder.slider(
            "",
            min_value=0,
            max_value=len(year_month_day_values) - 1,
            value=date_index,
            format="",
            key=key,
        )

        year, month, day = year_month_day_values[slider_value]
        d = dt(year, month, day)
        date_placeholder.write(f"#### Date: {d:%Y}-{d:%m}-{d:%d}")
        return year, month, day

    def render_map(year, month, day):
        mask = (counts_df.index.year == year) & (counts_df.index.month == month) & (counts_df.index.day == day)
        daily_counts = counts_df[mask].transpose().reset_index()
        daily_counts.rename(
            columns={
                daily_counts.columns[0]: "name",
                daily_counts.columns[1]: "daily_counts",
            },
            inplace=True,
        )

        coords["counts"] = coords.merge(
            daily_counts, left_on="stop_name", right_on="name", how="left"
        )["daily_counts"]

        max_entry = daily_counts["daily_counts"].max()

        display_counts = coords[~pd.isna(coords["counts"])]

        if display_counts.empty:
            return

        # Create Pydeck's initial view
        deck = pdk.Deck(
                map_style="mapbox://styles/mapbox/dark-v9",
                initial_view_state=pdk.ViewState(
                    latitude=(display_counts.gtfs_latitude.mean()+0.03),
                    longitude=display_counts.gtfs_longitude.mean(),
                    zoom=9.8,
                    pitch=40,
                    height=630,
                    width=550
                ),
                # Add a layer to the view
                layers=[
                    pdk.Layer(
                        "ColumnLayer",
                        data=display_counts,
                        disk_resolution=12,
                        radius=100,
                        get_position="[gtfs_longitude, gtfs_latitude]",
                        get_fill_color=f'[135-(counts*(135/{max_entry})),0,255-(counts*(255/{max_entry})),255]',
                        get_elevation="[counts]",
                        coverage=4,
                        getElevation=True,
                        elevation_scale=0.12,
                        elevation_range=[0, 8],
                        pickable=True,
                        wireframe=True,
                    ),
                ],
            )

        map_placeholder.pydeck_chart(deck)


    # Set animation speed
    with col2:
        speed_options = {"Fast": 0.1,
                        "Slow": 1}
        selected_speed = st.selectbox("Choose a speed", list(speed_options.keys()))

    # Animation start and stop button
    with col2:
        one, two = st.columns(2)

        with one:
            start_anim = st.button("Start", use_container_width=True)
        with two:
            stop_anim = st.button("Stop", use_container_width=True)

        st.write("---")

    # Button activation
    if start_anim:
        animation_speed = speed_options[selected_speed]
    if stop_anim:
        animation_speed = False

    # Run the animation
    if animation_speed:
        for year, month, day in cycle(year_month_day_values):
            time.sleep(animation_speed)
            render_slider(year, month, day)
            render_map(year, month, day)

    else:
        year, month, day = render_slider(year, month, day)
        render_map(year, month, day)


################################################
################################################

# Map rendering function

if selected_display == "Neighborhood Map":
    st.write("### Neighborhood Map: Entries per neighborhood over a period of time")
    st.write("---")
    render_df_map()

if selected_display == "Dynamic Map":
    animation_speed=False
    # Set Body, Header and Sidebar background
    dynamic_map()



with st.sidebar:
    st.write("---")
    st.write("Questions or Feedback, [Contact Us](mailto:support@cybersym.com)")
    st.write("Created by [Cybersyn](https://app.snowflake.com/marketplace/listings/Cybersyn%2C%20Inc)")
