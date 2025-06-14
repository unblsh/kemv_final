# KEMV Crime Dashboard

## Overview
The KEMV Crime Dashboard is a comprehensive web application designed to provide insightful analytics and visualizations of crime data. It offers different perspectives—Strategic, Operational, and Analytical—to cater to various levels of detail and types of analysis, helping users understand crime patterns, trends, and key performance indicators.

## Features

### Strategic Dashboard
- **Crime Count by NIBRS Offense Category**: Stacked bar chart showing the distribution of crimes by NIBRS (National Incident-Based Reporting System) categories, broken down into Group A (serious offenses) and Group B (less serious offenses).
- **Total Crime Count Per Month (Past 12 Months)**: A line chart displaying monthly crime counts with an overlaid trendline to visualize long-term patterns.
- **Crime Count Per Precinct**: Horizontal bar chart illustrating the number of crimes reported in each police precinct.
- **Top 5 Neighborhoods with Highest Crime**: A quick overview table highlighting neighborhoods with the highest crime counts.
- **Crime Distribution by Neighborhood**: A sortable horizontal bar chart showing crime counts across all neighborhoods, with options to sort alphabetically or by crime count.

### Operational Dashboard
- **Key Performance Indicators (KPIs)**: Displays real-time metrics such as total crimes today, active sectors, most reported offense, and the last crime committed, along with daily and weekly percentage changes.
- **Date Selector for KPIs**: Allows users to select specific dates to view KPIs relevant to that day.
- **Crime Count by Hour of Day**: A line chart showing crime distribution across a 24-hour cycle, with toggles for "All", "Weekday", and "Weekend" views.
- **Crime by Category: Today vs Yesterday**: A bar chart comparing crime counts for selected categories between today and yesterday. Features a modern, compact horizontal toggle bar for category selection (replacing the old dropdown).
- **Crime by Sector**: Bar chart displaying crime counts per sector.
- **Daily Crime Totals (Last 7 Days)**: A line chart showing the trend of daily crime totals over the past week.
- **Recent Crimes Table**: A searchable and paginated table listing recent crime incidents with details and a "Details" button to view more information.
- **Crime Details Modal with Map**: Clicking "Details" on a recent crime opens a modal with comprehensive information and a Leaflet map showing the crime's location.

### Analytical Dashboard
- **Interactive Map**: Displays crime locations on a Leaflet map with clustering for areas with high crime density.
- **Filters**: Comprehensive filtering options for crime data, including:
    - Offense Categories (multi-select)
    - NIBRS Groups (multi-select)
    - Date Range (start and end dates)
    - Precincts (multi-select)
    - Neighborhoods (multi-select)
- **Top Reporting Areas Bar Chart**: Visualizes crime counts by reporting area.
- **Crime Distribution by Category and NIBRS Group**: Stacked bar chart showing crime distribution, allowing for granular analysis.
- **Crimes Over Time Chart**: A line chart illustrating crime trends based on the applied filters.
- **Filtered Crime Records Table**: A paginated table displaying crime records based on the selected filters, with export to CSV functionality.

## Technologies Used
- **Backend**: Flask (Python)
- **Database**: SQLite (or any other configured by SQLAlchemy)
- **Frontend**:
    - HTML5
    - CSS3 (Custom styles and Bootstrap 5)
    - JavaScript
    - [Bootstrap 5](https://getbootstrap.com/) for responsive design and UI components.
    - [Chart.js](https://www.chartjs.org/) for interactive data visualizations.
    - [jQuery](https://jquery.com/) and [jQuery UI Datepicker](https://jqueryui.com/datepicker/) for UI enhancements.
    - [Select2](https://select2.org/) for enhanced dropdowns (though now largely replaced by custom toggles for category selection).
    - [Leaflet](https://leafletjs.com/) for interactive maps.
    - [Bootstrap Icons](https://icons.getbootstrap.com/) for iconography.

## Setup Instructions

### Prerequisites
- Python 3.x
- pip (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/kemv_final.git
    cd kemv_final
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (Note: You might need to create a `requirements.txt` file if one doesn't exist, by running `pip freeze > requirements.txt` after installing necessary packages like Flask, SQLAlchemy, pandas, etc.)

4.  **Database Setup:**
    The application uses SQLite by default. Ensure you have a `site.db` file in your `instance/` folder or configure your database connection in `config.py`. You might need to initialize the database and potentially load some initial data.
    ```bash
    flask shell
    >>> from app import db
    >>> db.create_all()
    >>> exit()
    ```
    (You may need a separate script or method to populate your `Crime` table with data.)

### Running the Application

1.  **Ensure your virtual environment is active.**
2.  **Run the Flask application:**
    ```bash
    python app.py
    ```

3.  **Access the Dashboard:**
    Open your web browser and navigate to `http://127.0.0.1:5000/`.

## Project Structure (Conceptual)

```
kemv_final/
├── app.py                  # Main Flask application
├── config.py               # Application configuration
├── models.py               # SQLAlchemy database models
├── instance/               # Database files (e.g., site.db for SQLite)
├── static/
│   ├── style.css           # Custom CSS styles
│   └── scripts.js          # Custom JavaScript functions (if any, separate from template scripts)
└── templates/
    ├── base.html           # Base HTML template for common structure
    ├── index.html          # Main landing page
    ├── dashboard_strategic.html # Strategic dashboard layout
    ├── dashboard_operational.html # Operational dashboard layout
    └── dashboard_analytical.html # Analytical dashboard layout
```

## Author
Azim A.

