
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



# Page parameters

# Set the page layout
icon = Image.open("objects/cybersyn_icon.png")

st.set_page_config(page_title="Cybersyn - NYC Subway Traffic Dataset",
                   layout="wide", page_icon=icon)

# Renaming pages
show_pages(
    [
        Page("streamlit_app.py", "Data Hub"),
        Page("pages/1_Maps.py", "Map Views")
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

display_options = ['Chart', 'Borough Segmentation']
selected_display = st.sidebar.selectbox('Select display', display_options)

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
    one, two = st.columns([5,2])
    with one:
        st.write("#  Cybersyn: MTA Turnstile Dataset")
        st.markdown("""<h3> Understanding the early impact of COVID-19 <br> on NYC Public Transportation</h3>""", unsafe_allow_html=True)


# Dataset description
with st.container():

    st.markdown("""
    The Metropolitan Transportation Authority (MTA) collects data from the turnstiles
    in its subway stations to provide an overall view of traffic in NYC public transport. \n
    The raw data can be found [here](http://web.mta.info/developers/turnstile.html)
    but we recommend you check out our cleaned dataset below. It's free!
    """)


################################################
################################################

# Data Loading function

# Caching all these data loading functions in the start allows for faster page interaction
st.cache_data()
def load_chart_data():
    # Load the data
    data = pd.read_csv('input/clean_data.csv', low_memory=False)
    data['date'] = pd.to_datetime(data['date'])
    data = data[['stop_name', 'date', 'entries', 'line', 'borough', 'daytime_routes', 'division',
        'structure', 'gtfs_longitude', 'gtfs_latitude', 'complex_id']]

    # Filter the data based on the selected date range
    data['date'] = pd.to_datetime(data['date'])
    data = data[data["date"].between(start_date, end_date)]

    return data


################################################
################################################

st.text("")
st.text("")
st.text("")

a,b,c,d,e,f = st.columns([1,2,2,1,1,1])
with c:
    st.markdown("### Explore the Data")

st.write("---")

# Load and cache the data that each function will copy
data = load_chart_data()

# Chart rendering function

def render_df_chart():

    # Create a copy of the data for filtering
    filtered_data = data.copy()

    total_entries = data.groupby(["date"])["entries"].sum().reset_index()


    # Create a dictionary to store the selected filter values
    selected_filters = {
        'stop_name': [],
        'line': [],
        'borough': [],
        'division': []
    }

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

def render_bar():
    # Load the data
    data_b = data.copy()

    # Group by borough and calculate the average daily entries
    data_b['date'] = data_b['date'].dt.date
    bar_data = data_b.groupby("borough", as_index=False)["entries"].mean()
    bar_data['entries'] = bar_data['entries'].round(0).astype(int)

    # Create the bar plot
    fig_bar = px.bar(bar_data, x='borough', y='entries',
                     labels={'entries': 'Average Daily Entries', 'borough': 'Borough'},
                     )

    # Adjust y-axis range according to Manhattan
    if bar_data["entries"].max() > 15000 or bar_data["entries"].max() < 7000:
        fig_bar.update_yaxes(range=[0, 1.1*bar_data["entries"].max()])
    else:
        fig_bar.update_yaxes(range=[0, 15000])



    # Display the plot
    st.plotly_chart(fig_bar, theme=None, use_container_width=True)

def borough_sunburst():

    # Load the data
    data_s = data.copy()

    col1, col2 = st.columns([4,3])


    # Group the data by borough and station, and calculate the total entries for each station
    df_borough = data_s.groupby(['borough', 'stop_name'])['entries'].sum().reset_index()


        # Create the dropdown menu for selecting the number of top stations to keep

    # Place title and dropdown menu on right
    with col2:
        st.write("#")
        st.write("#")
        gauche, droite = st.columns([1,4])
        with droite:
            st.write("---")
            st.write("### Stations by borough")
            top_n = st.selectbox('Select the number of top stations to keep:', [i*5 for i in range(1,7)])
            st.write("_Hint: Don't hesitate to click on a borough for focus_")
            st.write("---")

    with col1:
        # For each borough, get the top N stations by entries and combine the rest as "Others"
        df_borough_top = pd.DataFrame()
        for borough in df_borough['borough'].unique():
            df_borough_b = df_borough[df_borough['borough'] == borough]
            df_borough_b = df_borough_b.sort_values('entries', ascending=False)
            df_borough_b_top = df_borough_b.head(top_n)
            if len(df_borough_b) > top_n:
                df_borough_b_other = pd.DataFrame({
                    'borough': borough,
                    'stop_name': ['Others'],
                    'entries': [df_borough_b['entries'][top_n:].sum()]
                })
                df_borough_b_top = pd.concat([df_borough_b_top, df_borough_b_other])
            df_borough_top = pd.concat([df_borough_top, df_borough_b_top])


        color_sequence = ['#267d7a', '#4f267d', '#feefff', '#A83a50', 'black']
        # Create the sunburst graph
        fig = px.sunburst(df_borough_top, path=['borough', 'stop_name'], values='entries',
                            color_discrete_sequence=color_sequence)

        # Update the graph
        fig.update_traces(textinfo='label+percent entry')
        fig.update_layout(width=600, height=600,
                        margin=dict(l=50, r=50, t=50, b=50), # Adjust the margins to leave space for the square
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        shapes=[
                            dict(
                                type='rect',
                                xref='paper',
                                yref='paper',
                                x0=-0.08,
                                y0=-0.07,
                                x1=1.08,
                                y1=1.07,
                                line=dict(
                                    color='#ffffff',
                                    width=5
                                ),
                        fillcolor='rgba(0,0,0,0)',  # Set fillcolor as transparent
                        opacity=0.1
                            )
                        ]
                    )

        # Display the sunburst graph in the Streamlit app
        st.plotly_chart(fig)

def render_scatter():

        data_sc = data.copy()

        data['day_of_week'] = data['date'].dt.day_name()

        scatter_data = data.groupby(["stop_name", "date", "day_of_week", "borough"], as_index=False)["entries"].sum()

        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


        # Multiselect box for days of the week
        selected_days = st.multiselect('Select days of the week', options=days_of_week,
                                       default=days_of_week, format_func=lambda day: day)


        # Multiselect box for boroughs and stop names
        column_list = st.columns(2)

        # Filter scatter_data based on the selected days
        filtered_data = scatter_data[scatter_data['day_of_week'].isin(selected_days)]

        # Borough filter
        filtered_boroughs = list(sorted(filtered_data['borough'].dropna().unique()))
        st.session_state.selected_borough = column_list[0].multiselect('Borough', filtered_boroughs, default=[])
        if st.session_state.selected_borough:
            filtered_data = filtered_data[filtered_data['borough'].isin(st.session_state.selected_borough)]


        # Stop name filter
        filtered_stop_names = list(sorted(filtered_data['stop_name'].dropna().unique()))
        st.session_state.selected_stop_name = column_list[1].multiselect('Stop Name', filtered_stop_names, default=[])
        if st.session_state.selected_stop_name:
            filtered_data = filtered_data[filtered_data['stop_name'].isin(st.session_state.selected_stop_name)]




        fig = px.scatter(filtered_data, x='stop_name', y='entries', color='day_of_week',
                         labels={'entries': 'Daily Entries', 'stop_name': ''},  # Adjust marker size based on the number of entries
                         color_continuous_scale='Viridis'  # Choose a color scale for intensity
                         )

        fig.update_traces(marker=dict(line=dict(width=1, color='Gray')))

        fig.update_layout(
            autosize=True,
            width=1200,  # Set the width of the plot
            height=600,  # Set the height of the plot
            plot_bgcolor="#613B77",
            xaxis=dict(
                title_standoff=0
            ),
            legend=dict(
                title=dict(text='Day of Week'),
                bgcolor='rgba(0,0,0,0)',
                bordercolor='gray',
                borderwidth=1,
            ),
            margin=dict(l=80, r=50, t=20, b=150),
            annotations=[
                    dict(
                        x=0.5,  # X-coordinate of the annotation (midpoint of x-axis)
                        y=0,  # Y-coordinate of the annotation (below the plot)
                        text='Stations',  # Text of the annotation
                        showarrow=False,  # Hide the arrow
                        xref='paper',  # Set the x-coordinate reference to 'paper' (relative to the entire plot)
                        yref='paper',  # Set the y-coordinate reference to 'paper' (relative to the entire plot)
                        font=dict(color='white', size=14)  # Set the font color and size
                    )
            ]

        )


        st.plotly_chart(fig, theme=None, use_container_width=True)


# Create a Streamlit menu to choose the display

if selected_display == "Chart":
    render_df_chart()

if selected_display == "Borough Segmentation":

    tab1, tab2 = st.tabs(["Borough Segmentation", "Graphs"])

    with tab1:
        borough_sunburst()

    with tab2:
        st.write("## More ways to visualize the data")
        st.write("#")

        st.write("### Daily entries by station")
        render_scatter()
        st.text("")
        st.write("### Average Station Daily Entries per Borough")
        render_bar()


with st.sidebar:
    st.write("---")
    st.write("Questions or Feedback, [Contact Us](mailto:support@cybersym.com)")
    st.write("Created by [Cybersyn](https://app.snowflake.com/marketplace/listings/Cybersyn%2C%20Inc)")

st.write("---")


################################################
################################################

# Graveyard: Ideas for later if useful

# # Define a function that returns a lottie image from JSON
# def get_lottie(path):
#     with open(path, "r") as f:
#         lottie_image = json.load(f)

#     return lottie_image

# # Function to temporarily shows lottie animation
# def spin():
#     lottie = get_lottie("objects/resize.json")

#     if 'spin_wait' in st.session_state:
#         with st_lottie_spinner(lottie, key="You can always resize the side bar!", height=100):
#             time.sleep(2)
#             st.session_state.spinned = True

# # Function to write text letter by letter
# def writer(text):
#     if "writer_wait" in st.session_state:
#         t = st.empty()
#         for i in range(len(text) + 1):
#             t.markdown("#### %s..." % text[0:i])
#             time.sleep(0.05)

# # Placed after everything has run, waiter return a session state variable which can activate other funcitons
# # Since Streamlit runs Top-Down, only way to activate function after the rest without placing it at the top
# def waiter(x_seconds, session_var):

#     time.sleep(x_seconds)
#     st.session_state[session_var] = True





# This would play the lottie resize icon and a text (activated by waiter )

# spin_cols = st.columns([1,10])
# with spin_cols[0]:
#     spin()
#
# writer("Don't forget you can resize the spin bar! :)")

# Activate waiter for spin or writer
# waiter(2, "spin_wait")
# waiter(0, "writer_wait")

# Lottie animation integration
# lottie_subway = get_lottie("objects/subway_image.json")
# lottie_show = st_lottie(lottie_subway, width=280)
