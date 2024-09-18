# Bridge: NYC Subway Traffic Analysis

This project provides interactive visualizations of MTA subway data during the COVID-19 pandemic. Using data from subway turnstiles, it explores traffic patterns in New York City from January to June 2020, providing insights into how the pandemic affected public transportation.

The application is built with **Streamlit**, with interactive features like time series charts, borough segmentation, dynamic maps, and choropleth maps, allowing users to explore data through an intuitive web interface.

#### You can access the demo by [clicking here](https://charlescvt-nyc-covid-demo-data-hub-hwz4d5.streamlit.app/).

## Features

### 1. **Time Series Chart**
- View total and filtered entries per day across the subway system.
- Filter by borough, line, stop name, and division.
- Overlay total entries with specific filtered data for comparison.

### 2. **Borough Segmentation**
- **Sunburst Graph**: Explore entries by borough and station, with interactive filtering options.
- **Scatter Plot**: Visualize daily entries by station, segmented by days of the week.
- **Bar Plot**: Compare average daily entries across boroughs.

### 3. **Neighborhood Map**
- Explore entries per neighborhood over a selected date range.
- Filter by borough and exclude specific stations to focus on relevant data.
- View results on an interactive map, color-coded by various metrics like total entries or population.

### 4. **Dynamic Map**
- Visualize subway station entries on a daily basis, with a time slider that animates daily changes in traffic.
- View changes dynamically on an interactive 3D map, with options to adjust animation speed and control playback.

## Data Sources

- MTA Turnstile Data: [MTA Developer Resources](http://web.mta.info/developers/turnstile.html)
- Population and Geospatial Data: Supplemented for richer visual analysis.
  
The project leverages cleaned data, stored locally as `clean_data.csv`, `station_entry_pivot.csv`, and `nta_fulldata_d.csv`.

## Requirements

You can install the required Python packages using `pip`

```bash
pip install -r requirements.txt
```


### How to Run
1. Clone the repository.
2. Ensure all dependencies are installed.
3. Run the Streamlit application:

```bash
streamlit run Data_Hub.py
```

This will launch the main page of the app, where you can explore NYC subway data through interactive visualizations.

## Project Structure

- `Data_Hub.py`: Main page for the time series and borough segmentation.
- `pages/1_Maps.py`: Neighborhood and dynamic map visualizations.
- `input/`: Folder containing cleaned datasets and supporting files like GeoJSON data.
- `output/`: Contains processed map data for use in the neighborhood maps.

## Contact

For questions or feedback, reach out via [email](mailto:cchaverot@gmail.com).





