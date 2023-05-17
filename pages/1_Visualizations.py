import numpy as np
import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
import plotly.express as px
import random
import time
from datetime import datetime as dt, timedelta
from itertools import cycle


################################################
################################################

# Functions

# Load and cache the data
@st.cache_data
def load_data():
    # coordinates for each station
    data = pd.read_csv('input/clean_data.csv', low_memory=False, parse_dates=['date'])
    coords = data[["gtfs_latitude", "gtfs_longitude", "stop_name"]]

    # pivot table showing daily entries for each station
    counts_df = pd.read_csv('input/station_entry_pivot.csv', parse_dates=['date'],
                            index_col="date")


    return data, coords, counts_df


################################################
################################################

# Page parameters

# Setup page layout
st.set_page_config(layout="wide", page_title="Visualization")


# Set Body, Header and Sidebar background
with open("filtered_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


st.sidebar.header("Parameters")

################################################
################################################

# Sidebar parameters and their session state

# Date input
initial_end_date = pd.to_datetime("06-30-2020")
initial_start_date = pd.to_datetime("01-01-2020")

# Initialize session_state variables
if 'start_date' not in st.session_state:
    st.session_state.start_date = initial_start_date
if 'end_date' not in st.session_state:
    st.session_state.end_date = initial_end_date

#

menu_options = ['Dynamic Map', 'Borough Segmentation']
selected_display = st.sidebar.selectbox('Select display', menu_options)

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


data_df, coords_df, counts_df_df = load_data()

# Defining each graph's function

def dynamic_map():
    global animation_speed

    # Use a dataframe copy to allow modifications
    coords = coords_df.copy()
    counts_df = counts_df_df.copy()

    year_month_day_values = [(d.year, d.month, d.day) for d in counts_df.index if start_date <= d <= end_date]
    year, month, day = year_month_day_values[0]

    # Setup presentation widgets and placeholders

    col1, col2 = st.columns([5,3])

    col2.write("#")
    col2.write("#")
    col2.write("#")
    col2.write("---")

    date_value = st.empty()
    day_slider = st.empty()

    title_placeholder = col1.empty()
    subtitle_placeholder = col1.empty()
    map_placeholder = col1.empty()
    date_placeholder = col2.empty()
    slider_placeholder = col2.empty()


    title_placeholder.write("### Dynamic Map: Daily Entries per Station in NYC")


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
                    height=680,
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

def render_bar():
    # Load the data
    data = load_data()[0]

    # Convert 'date' column to datetime and filter
    data['date'] = pd.to_datetime(data['date'])
    data = data[data["date"].between(start_date, end_date)]

    # Group by borough and calculate the average daily entries
    data['date'] = data['date'].dt.date
    bar_data = data.groupby("borough", as_index=False)["entries"].mean()
    bar_data['entries'] = bar_data['entries'].round(0).astype(int)

    # Create the bar plot
    fig_bar = px.bar(bar_data, x='borough', y='entries',
                     title=' Average Station Daily Entries per Borough',
                     labels={'entries': 'Daily Entries', 'borough': 'Borough'},
                     )

    # Adjust y-axis range according to Manhattan
    if bar_data["entries"].max() > 15000 or bar_data["entries"].max() < 7000:
        fig_bar.update_yaxes(range=[0, 1.1*bar_data["entries"].max()])
    else:
        fig_bar.update_yaxes(range=[0, 15000])

    # Display the plot
    st.plotly_chart(fig_bar, theme=None, use_container_width=True)

def borough_sunburst():

    data = data_df.copy()
    data = data[data["date"].between(start_date, end_date)]

    col1, col2 = st.columns([4,3])


    # Group the data by borough and station, and calculate the total entries for each station
    df_borough = data.groupby(['borough', 'stop_name'])['entries'].sum().reset_index()


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

        data = load_data()[0]
        data = data[data["date"].between(start_date, end_date)]

        data['date'] = pd.to_datetime(data['date'])
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


if selected_display == "Dynamic Map":
    animation_speed=False
    # Set Body, Header and Sidebar background
    dynamic_map()

if selected_display == "Borough Segmentation":


    tab1, tab2 = st.tabs(["Borough Segmentation", "Graphs"])

    with tab1:
        borough_sunburst()

    with tab2:
        st.write("## More ways to visualize the data")
        st.write("#")

        st.write("### Daily entries by station")
        render_scatter()
        render_bar()

with st.sidebar:
    st.write("---")
    st.write("Questions or Feedback, [Contact Us](mailto:support@cybersym.com)")
    st.write("Created by [Cybersyn](https://app.snowflake.com/marketplace/listings/Cybersyn%2C%20Inc)")
