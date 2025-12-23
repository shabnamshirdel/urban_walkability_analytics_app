# 🗺️ Urban Walkability Analytics Dashboard

![15 minute accessibility app screenshot](./urban_walkability_analytics_app.png)


This application is a **Geospatial Analytics Dashboard** designed to visualize and analyze street-level walkability metrics. It integrates street segment geometries with diverse urban data—such as greenery, slope, and population density—providing an interactive interface for urban planners and researchers.

## ✨ Features

* **Optimized Geospatial Rendering:** Uses a Leaflet Canvas renderer and geometry simplification (0.00005 tolerance) to ensure smooth performance even with thousands of street segments.
* **Interactive Multi-Metric Analysis:** Click any street segment to view a detailed breakdown of 7 key walkability indicators:
	* **Luminosity & Shade:** Assessing environmental comfort.
	* **Greenery:** Visualizing urban vegetation.
	* **Slope:** Normalized terrain difficulty.
	* **Social Metrics:** Population density and space for interaction.

* **Real-time Data Visualization:** Dynamic bar charts that update instantly upon segment selection.



## ⚙️ Prerequisites

To run this application, you need to have **Python 3.8+** installed on your system.

### Required Files

The application expects a `data/` directory with the following files:

1.  `./data/GCWI_SCORE_streetswithsidewalk_Cleaned.shp`: Shapefile containing street geometries and walkability scores.
2.  `./data/street_segment_slope.csv`: CSV file containing slope of the street segments for merging.

## 💻 Local Installation and Setup

Follow these steps to set up and run the application on your local machine.

### 1. Clone or Download the Project

First, download the `urban_walkability_analytics_app.py` script and the required `data` folder into a new project folder. 

Open the terminal and navigate to the newly created project folder.

### 2. Create a Virtual Environment (Recommended)

It's best practice to use a virtual environment to manage dependencies. In the terminal:

```bash
# Create the environment
python -m venv venv 

# Activate the environment (on macOS/Linux)
source venv/bin/activate

# Activate the environment (on Windows)
venv\Scripts\activate
```

### 3. Install Required Libraries

The project uses `Flask` for the backend, `GeoPandas` for spatial processing, and `NumPy` for data optimization:


```bash
pip install flask geopandas pandas numpy
```


### 4. Run the Application

Execute the main script. The application is configured to automatically open your default web browser once the data is cached.

```bash
python3 urban_walkability_analytics_app.py
```


### 5. Access the App

The server will run at: `http://127.0.0.1:5000/`.







