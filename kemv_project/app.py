from flask import Flask, render_template, jsonify, request
from config import Config
from models import db, Crime
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/strategic-dashboard')
def strategic_dashboard():
    return render_template('dashboard_strategic.html')

@app.route('/operational-dashboard')
def operational_dashboard():
    return render_template('dashboard_operational.html')

@app.route('/analytical-dashboard')
def analytical_dashboard():
    return render_template('dashboard_analytical.html')

@app.route('/api/strategic-data')
def get_strategic_data():
    # 1. Crime count by NIBRS Offense Category (Bar Chart)
    offense_category_data = db.session.query(
        Crime.Offense_Category, func.count(Crime.Report_Number)
    ).group_by(Crime.Offense_Category).all()
    offense_category_labels = [item[0] for item in offense_category_data]
    offense_category_values = [item[1] for item in offense_category_data]

    # 2. Total crime count per month over past 12 months (Line Chart)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    monthly_crime_data = db.session.query(
        func.DATE_FORMAT(Crime.Report_DateTime, '%Y-%m').label('month'),
        func.count(Crime.Report_Number)
    ).filter(Crime.Report_DateTime.between(start_date, end_date)).group_by(func.DATE_FORMAT(Crime.Report_DateTime, '%Y-%m')).order_by(func.DATE_FORMAT(Crime.Report_DateTime, '%Y-%m')).all()

    monthly_labels = [item[0] for item in monthly_crime_data]
    monthly_values = [item[1] for item in monthly_crime_data]

    # 3. Crime distribution by Neighborhood (Heatmap/Table)
    neighborhood_crime_data = db.session.query(
        Crime.Neighborhood, func.count(Crime.Report_Number)
    ).group_by(Crime.Neighborhood).order_by(func.count(Crime.Report_Number).desc()).all()
    
    # 4. Share of Group A vs B offenses (Pie Chart)
    nibrs_group_data = db.session.query(
        Crime.NIBRS_Group_AB, func.count(Crime.Report_Number)
    ).group_by(Crime.NIBRS_Group_AB).all()
    nibrs_group_labels = [item[0] for item in nibrs_group_data]
    nibrs_group_values = [item[1] for item in nibrs_group_data]

    # 5. Crime count per precinct (Vertical Bar)
    precinct_crime_data = db.session.query(
        Crime.Precinct, func.count(Crime.Report_Number)
    ).group_by(Crime.Precinct).all()
    precinct_labels = [item[0] for item in precinct_crime_data]
    precinct_values = [item[1] for item in precinct_crime_data]

    # 6. Distribution of offense categories (Donut Chart) - Same as offense_category_data, just different visualization type
    
    # 7. Table: Top 5 neighborhoods with highest crime - from neighborhood_crime_data

    return jsonify({
        'offense_category_chart': {
            'labels': offense_category_labels,
            'values': offense_category_values
        },
        'monthly_crime_chart': {
            'labels': monthly_labels,
            'values': monthly_values
        },
        'nibrs_group_chart': {
            'labels': nibrs_group_labels,
            'values': nibrs_group_values
        },
        'precinct_crime_chart': {
            'labels': precinct_labels,
            'values': precinct_values
        },
        'top_neighborhoods': [{'neighborhood': n[0], 'crime_count': n[1]} for n in neighborhood_crime_data[:5]],
        'all_neighborhood_crime_data': [{'neighborhood': n[0], 'crime_count': n[1]} for n in neighborhood_crime_data]
    })

@app.route('/api/operational-data')
def get_operational_data():
    # 1. Live Table: Last 50 reported crimes
    recent_crimes = Crime.query.order_by(Crime.Report_DateTime.desc()).limit(50).all()
    recent_crimes_list = [{
        'Report_Number': crime.Report_Number,
        'Report_DateTime': crime.Report_DateTime.strftime('%Y-%m-%d %H:%M:%S') if crime.Report_DateTime else None,
        'Offense_Category': crime.Offense_Category,
        'Precinct': crime.Precinct,
        'Neighborhood': crime.Neighborhood
    } for crime in recent_crimes]

    # 2. Map or Chart: Crimes by sector
    crime_by_sector = db.session.query(
        Crime.Sector, func.count(Crime.Report_Number)
    ).group_by(Crime.Sector).all()
    sector_labels = [item[0] for item in crime_by_sector]
    sector_values = [item[1] for item in crime_by_sector]

    # 3. Time Chart: Crime count by hour of day (24-hour clock)
    crime_by_hour = db.session.query(
        func.extract('hour', Crime.Report_DateTime).label('hour'),
        func.count(Crime.Report_Number)
    ).group_by('hour').order_by('hour').all()
    hour_labels = [int(item[0]) for item in crime_by_hour]
    hour_values = [item[1] for item in crime_by_hour]

    # 4. Grouped Bar Chart: Crime by category today vs yesterday
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    crimes_today = db.session.query(
        Crime.Offense_Category, func.count(Crime.Report_Number)
    ).filter(func.DATE(Crime.Offense_Date) == today).group_by(Crime.Offense_Category).all()

    crimes_yesterday = db.session.query(
        Crime.Offense_Category, func.count(Crime.Report_Number)
    ).filter(func.DATE(Crime.Offense_Date) == yesterday).group_by(Crime.Offense_Category).all()

    # Convert to dict for easier lookup
    crimes_today_dict = {item[0]: item[1] for item in crimes_today}
    crimes_yesterday_dict = {item[0]: item[1] for item in crimes_yesterday}

    all_offense_categories = sorted(list(set(crimes_today_dict.keys()) | set(crimes_yesterday_dict.keys())))
    today_values = [crimes_today_dict.get(cat, 0) for cat in all_offense_categories]
    yesterday_values = [crimes_yesterday_dict.get(cat, 0) for cat in all_offense_categories]
    
    # 5. KPI Cards: Today's total crimes, active sectors, most reported offense
    total_crimes_today = sum(today_values)
    active_sectors = db.session.query(func.count(Crime.Sector.distinct())) \
        .filter(func.DATE(Crime.Offense_Date) == today).scalar()
    
    most_reported_offense_today = None
    if crimes_today:
        most_reported_offense_today = max(crimes_today, key=lambda item: item[1])[0]

    # 6. Stacked Area Chart: Daily crime totals over last 7 days
    seven_days_ago = today - timedelta(days=6)
    daily_crime_data = db.session.query(
        func.DATE(Crime.Offense_Date).label('date'),
        func.count(Crime.Report_Number)
    ).filter(func.DATE(Crime.Offense_Date) >= seven_days_ago).group_by('date').order_by('date').all()

    daily_labels = [item[0].strftime('%Y-%m-%d') for item in daily_crime_data]
    daily_values = [item[1] for item in daily_crime_data]

    return jsonify({
        'recent_crimes': recent_crimes_list,
        'crime_by_sector_chart': {
            'labels': sector_labels,
            'values': sector_values
        },
        'crime_by_hour_chart': {
            'labels': hour_labels,
            'values': hour_values
        },
        'crime_today_yesterday_chart': {
            'labels': all_offense_categories,
            'today_values': today_values,
            'yesterday_values': yesterday_values
        },
        'kpis': {
            'total_crimes_today': total_crimes_today,
            'active_sectors': active_sectors,
            'most_reported_offense_today': most_reported_offense_today
        },
        'daily_crime_chart': {
            'labels': daily_labels,
            'values': daily_values
        }
    })

@app.route('/api/analytical-data')
def get_analytical_data():
    # Filters: Offense category, date range, precinct, neighborhood
    offense_categories = [row[0] for row in db.session.query(Crime.Offense_Category).distinct().order_by(Crime.Offense_Category).all()]
    precincts = [row[0] for row in db.session.query(Crime.Precinct).distinct().order_by(Crime.Precinct).all()]
    neighborhoods = [row[0] for row in db.session.query(Crime.Neighborhood).distinct().order_by(Crime.Neighborhood).all()]

    # Get filter parameters from request
    selected_offense_category = request.args.get('offense_category')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    selected_precinct = request.args.get('precinct')
    selected_neighborhood = request.args.get('neighborhood')

    query = Crime.query

    if selected_offense_category and selected_offense_category != 'all':
        query = query.filter(Crime.Offense_Category == selected_offense_category)
    if start_date_str:
        query = query.filter(Crime.Offense_Date >= datetime.strptime(start_date_str, '%Y-%m-%d').date())
    if end_date_str:
        query = query.filter(Crime.Offense_Date <= datetime.strptime(end_date_str, '%Y-%m-%d').date())
    if selected_precinct and selected_precinct != 'all':
        query = query.filter(Crime.Precinct == selected_precinct)
    if selected_neighborhood and selected_neighborhood != 'all':
        query = query.filter(Crime.Neighborhood == selected_neighborhood)

    # 1. Line Chart: Crimes over time for selected offense category (filtered)
    crimes_over_time_filtered = query.with_entities(
        func.DATE_FORMAT(Crime.Report_DateTime, '%Y-%m-%d').label('date'),
        func.count(Crime.Report_Number)
    ).group_by('date').order_by('date').all()
    
    crimes_over_time_labels = [item[0] for item in crimes_over_time_filtered]
    crimes_over_time_values = [item[1] for item in crimes_over_time_filtered]

    # 2. Grouped Bar Chart: Crime by neighborhood filtered by offense type
    crime_by_neighborhood_filtered = query.with_entities(
        Crime.Neighborhood, func.count(Crime.Report_Number)
    ).group_by(Crime.Neighborhood).order_by(func.count(Crime.Report_Number).desc()).all()

    crime_by_neighborhood_labels = [item[0] for item in crime_by_neighborhood_filtered]
    crime_by_neighborhood_values = [item[1] for item in crime_by_neighborhood_filtered]

    # 3. Scatter Plot: Latitude vs Longitude colored by offense category
    # To avoid returning too much data, limit the scatter plot data
    scatter_plot_data = query.with_entities(
        Crime.Latitude, Crime.Longitude, Crime.Offense_Category
    ).limit(1000).all()
    scatter_plot_list = [{'latitude': s[0], 'longitude': s[1], 'offense_category': s[2]} for s in scatter_plot_data]

    # 4. Bubble Chart: Offense frequency by reporting area size (Conceptual - using Reporting_Area for size)
    offense_frequency_by_reporting_area = db.session.query(
        Crime.Reporting_Area, func.count(Crime.Report_Number).label('frequency'), func.avg(Crime.Latitude), func.avg(Crime.Longitude)
    ).group_by(Crime.Reporting_Area).order_by(func.count(Crime.Report_Number).desc()).limit(50).all()
    
    bubble_chart_data = [{
        'reporting_area': r[0],
        'frequency': r[1],
        'avg_latitude': r[2],
        'avg_longitude': r[3]
    } for r in offense_frequency_by_reporting_area]

    # 5. Pie Chart: Crime share by NIBRS Group AB (A or B)
    nibrs_group_filtered = query.with_entities(
        Crime.NIBRS_Group_AB, func.count(Crime.Report_Number)
    ).group_by(Crime.NIBRS_Group_AB).all()
    nibrs_group_filtered_labels = [item[0] for item in nibrs_group_filtered]
    nibrs_group_filtered_values = [item[1] for item in nibrs_group_filtered]

    # 6. Table: Filtered crime records (paginated)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    paginated_crimes = query.paginate(page=page, per_page=per_page, error_out=False)

    filtered_crimes_list = [{
        'Report_Number': crime.Report_Number,
        'Report_DateTime': crime.Report_DateTime.strftime('%Y-%m-%d %H:%M:%S') if crime.Report_DateTime else None,
        'Offense_Category': crime.Offense_Category,
        'Precinct': crime.Precinct,
        'Neighborhood': crime.Neighborhood
    } for crime in paginated_crimes.items]

    return jsonify({
        'filters': {
            'offense_categories': ['all'] + offense_categories,
            'precincts': ['all'] + precincts,
            'neighborhoods': ['all'] + neighborhoods
        },
        'crimes_over_time_chart': {
            'labels': crimes_over_time_labels,
            'values': crimes_over_time_values
        },
        'crime_by_neighborhood_chart': {
            'labels': crime_by_neighborhood_labels,
            'values': crime_by_neighborhood_values
        },
        'scatter_plot_data': scatter_plot_list,
        'bubble_chart_data': bubble_chart_data,
        'nibrs_group_filtered_chart': {
            'labels': nibrs_group_filtered_labels,
            'values': nibrs_group_filtered_values
        },
        'paginated_crimes': {
            'items': filtered_crimes_list,
            'total': paginated_crimes.total,
            'pages': paginated_crimes.pages,
            'page': paginated_crimes.page,
            'has_next': paginated_crimes.has_next,
            'has_prev': paginated_crimes.has_prev
        }
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 