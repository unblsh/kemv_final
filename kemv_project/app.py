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
    # 1. Crime count by NIBRS Offense Category with Group A/B breakdown (Stacked Bar Chart)
    offense_category_group_data = db.session.query(
        Crime.Offense_Category,
        Crime.NIBRS_Group_AB,
        func.count(Crime.Report_Number)
    ).group_by(Crime.Offense_Category, Crime.NIBRS_Group_AB).all()
    
    # Transform data for stacked bar chart
    offense_categories = sorted(list(set(item[0] for item in offense_category_group_data)))
    nibrs_groups = sorted(list(set(item[1] for item in offense_category_group_data)))
    
    stacked_data = {
        'labels': offense_categories,
        'datasets': []
    }
    
    for group in nibrs_groups:
        group_data = [0] * len(offense_categories)
        for item in offense_category_group_data:
            if item[1] == group:
                idx = offense_categories.index(item[0])
                group_data[idx] = item[2]
        stacked_data['datasets'].append({
            'label': f'Group {group}',
            'data': group_data
        })

    # 2. Total crime count per month over past 12 months (Line Chart with Trendline)
    latest_offense_date_strategic = db.session.query(func.max(Crime.Offense_Date)).scalar()
    end_date_strategic = latest_offense_date_strategic if latest_offense_date_strategic else datetime.now()
    start_date_strategic = end_date_strategic - timedelta(days=365)
    
    monthly_crime_data = db.session.query(
        func.DATE_FORMAT(Crime.Report_DateTime, '%Y-%m').label('month'),
        func.count(Crime.Report_Number)
    ).filter(Crime.Report_DateTime.between(start_date_strategic, end_date_strategic)) \
     .group_by(func.DATE_FORMAT(Crime.Report_DateTime, '%Y-%m')) \
     .order_by(func.DATE_FORMAT(Crime.Report_DateTime, '%Y-%m')).all()

    # Calculate trendline using simple linear regression
    x = list(range(len(monthly_crime_data)))
    y = [item[1] for item in monthly_crime_data]
    n = len(x)
    if n > 1:
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(i * j for i, j in zip(x, y))
        sum_xx = sum(i * i for i in x)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        trendline = [slope * i + intercept for i in x]
    else:
        trendline = y

    monthly_chart_data = {
        'labels': [item[0] for item in monthly_crime_data],
        'values': [item[1] for item in monthly_crime_data],
        'trendline': trendline
    }

    # 3. Crime distribution by Neighborhood (Sortable Bar Chart)
    neighborhood_crime_data = db.session.query(
        Crime.Neighborhood,
        func.count(Crime.Report_Number)
    ).group_by(Crime.Neighborhood).order_by(func.count(Crime.Report_Number).desc()).all()
    
    neighborhood_chart_data = {
        'labels': [item[0] for item in neighborhood_crime_data],
        'values': [item[1] for item in neighborhood_crime_data],
        'sort_order': 'desc'  # Default sort order
    }

    # 4. Crime count per precinct (Vertical Bar)
    precinct_crime_data = db.session.query(
        Crime.Precinct,
        func.count(Crime.Report_Number)
    ).group_by(Crime.Precinct).all()
    
    precinct_chart_data = {
        'labels': [item[0] for item in precinct_crime_data],
        'values': [item[1] for item in precinct_crime_data]
    }

    return jsonify({
        'offense_category_group_chart': stacked_data,
        'monthly_crime_chart': monthly_chart_data,
        'neighborhood_chart': neighborhood_chart_data,
        'precinct_crime_chart': precinct_chart_data,
        'top_neighborhoods': [{'neighborhood': n[0], 'crime_count': n[1]} for n in neighborhood_crime_data[:5]],
        'all_neighborhood_crime_data': [{'neighborhood': n[0], 'crime_count': n[1]} for n in neighborhood_crime_data]
    })

@app.route('/api/operational-data')
def get_operational_data():
    # Get date parameters from request
    view_type = request.args.get('view_type', 'all')  # 'all', 'weekday', 'weekend'
    top_offenses = request.args.getlist('top_offenses')  # List of selected top offenses
    
    # Determine 'today' based on the latest Offense_Date in the database
    latest_offense_date_query = db.session.query(func.max(Crime.Offense_Date)).scalar()
    today = latest_offense_date_query.date() if latest_offense_date_query else datetime.now().date()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)

    # 1. Live Table: Last 50 reported crimes with searchable fields
    recent_crimes = Crime.query.order_by(Crime.Report_DateTime.desc()).limit(50).all()
    recent_crimes_list = [{
        'Report_Number': crime.Report_Number,
        'Report_DateTime': crime.Report_DateTime.strftime('%Y-%m-%d %H:%M:%S') if crime.Report_DateTime else None,
        'Offense_Category': crime.Offense_Category,
        'Precinct': crime.Precinct,
        'Neighborhood': crime.Neighborhood,
        'NIBRS_Group_AB': crime.NIBRS_Group_AB,
        'Offense_Description': crime.Offense_Description,
        'Location': crime.Location,
        'Latitude': crime.Latitude,
        'Longitude': crime.Longitude
    } for crime in recent_crimes]

    # 2. Map or Chart: Crimes by sector
    crime_by_sector = db.session.query(
        Crime.Sector, func.count(Crime.Report_Number)
    ).group_by(Crime.Sector).all()
    sector_labels = [item[0] for item in crime_by_sector]
    sector_values = [item[1] for item in crime_by_sector]

    # 3. Time Chart: Crime count by hour of day (24-hour clock) with weekday/weekend toggle
    base_hour_query = db.session.query(
        func.extract('hour', Crime.Report_DateTime).label('hour'),
        func.extract('dow', Crime.Report_DateTime).label('day_of_week'),
        func.count(Crime.Report_Number)
    ).filter(Crime.Report_DateTime >= last_week)

    if view_type == 'weekday':
        base_hour_query = base_hour_query.filter(func.extract('dow', Crime.Report_DateTime).in_([1, 2, 3, 4, 5]))
    elif view_type == 'weekend':
        base_hour_query = base_hour_query.filter(func.extract('dow', Crime.Report_DateTime).in_([0, 6]))

    crime_by_hour = base_hour_query.group_by('hour', 'day_of_week').order_by('hour').all()
    
    # Process hour data for different views
    hour_data = {}
    for hour, dow, count in crime_by_hour:
        if hour not in hour_data:
            hour_data[hour] = {'weekday': 0, 'weekend': 0, 'all': 0}
        if dow in [0, 6]:  # Weekend
            hour_data[hour]['weekend'] += count
        else:  # Weekday
            hour_data[hour]['weekday'] += count
        hour_data[hour]['all'] += count

    hour_labels = sorted(hour_data.keys())
    hour_values = {
        'all': [hour_data[h]['all'] for h in hour_labels],
        'weekday': [hour_data[h]['weekday'] for h in hour_labels],
        'weekend': [hour_data[h]['weekend'] for h in hour_labels]
    }

    # 4. Get top 3 offenses by count
    top_offenses_query = db.session.query(
        Crime.Offense_Category,
        func.count(Crime.Report_Number).label('count')
    ).group_by(Crime.Offense_Category).order_by(func.count(Crime.Report_Number).desc()).limit(3).all()
    
    top_offense_categories = [item[0] for item in top_offenses_query]
    
    # If no specific offenses selected, use top 3
    if not top_offenses:
        top_offenses = top_offense_categories

    # 5. Grouped Bar Chart: Crime by selected categories today vs yesterday
    crimes_today = db.session.query(
        Crime.Offense_Category,
        func.count(Crime.Report_Number)
    ).filter(
        func.DATE(Crime.Offense_Date) == today,
        Crime.Offense_Category.in_(top_offenses)
    ).group_by(Crime.Offense_Category).all()

    crimes_yesterday = db.session.query(
        Crime.Offense_Category,
        func.count(Crime.Report_Number)
    ).filter(
        func.DATE(Crime.Offense_Date) == yesterday,
        Crime.Offense_Category.in_(top_offenses)
    ).group_by(Crime.Offense_Category).all()

    # Convert to dict for easier lookup
    crimes_today_dict = {item[0]: item[1] for item in crimes_today}
    crimes_yesterday_dict = {item[0]: item[1] for item in crimes_yesterday}

    # Calculate today's values and percentage changes
    today_vs_yesterday_data = {
        'labels': top_offenses,
        'today_values': [crimes_today_dict.get(cat, 0) for cat in top_offenses],
        'yesterday_values': [crimes_yesterday_dict.get(cat, 0) for cat in top_offenses],
        'percent_changes': []
    }

    for cat in top_offenses:
        today_val = crimes_today_dict.get(cat, 0)
        yesterday_val = crimes_yesterday_dict.get(cat, 0)
        if yesterday_val > 0:
            pct_change = ((today_val - yesterday_val) / yesterday_val) * 100
        else:
            pct_change = 0 if today_val == 0 else 100
        today_vs_yesterday_data['percent_changes'].append(round(pct_change, 1))

    # 6. KPI Cards with % change indicators
    total_crimes_today = sum(crimes_today_dict.values())
    total_crimes_yesterday = sum(crimes_yesterday_dict.values())
    total_crimes_last_week = db.session.query(func.count(Crime.Report_Number)) \
        .filter(func.DATE(Crime.Offense_Date) == last_week).scalar()

    # Calculate percentage changes
    if total_crimes_yesterday > 0:
        daily_pct_change = ((total_crimes_today - total_crimes_yesterday) / total_crimes_yesterday) * 100
    else:
        daily_pct_change = 0

    if total_crimes_last_week > 0:
        weekly_pct_change = ((total_crimes_today - total_crimes_last_week) / total_crimes_last_week) * 100
    else:
        weekly_pct_change = 0

    active_sectors = db.session.query(func.count(Crime.Sector.distinct())) \
        .filter(func.DATE(Crime.Offense_Date) == today).scalar()
    
    active_sectors_yesterday = db.session.query(func.count(Crime.Sector.distinct())) \
        .filter(func.DATE(Crime.Offense_Date) == yesterday).scalar()
    
    if active_sectors_yesterday > 0:
        sectors_pct_change = ((active_sectors - active_sectors_yesterday) / active_sectors_yesterday) * 100
    else:
        sectors_pct_change = 0

    most_reported_offense_today = None
    if crimes_today:
        most_reported_offense_today = max(crimes_today, key=lambda item: item[1])[0]

    kpis = {
        'total_crimes_today': {
            'value': total_crimes_today,
            'daily_change': round(daily_pct_change, 1),
            'weekly_change': round(weekly_pct_change, 1)
        },
        'active_sectors': {
            'value': active_sectors,
            'change': round(sectors_pct_change, 1)
        },
        'most_reported_offense_today': most_reported_offense_today
    }

    # 7. Stacked Area Chart: Daily crime totals over last 7 days
    seven_days_ago = today - timedelta(days=6)
    daily_crime_data = db.session.query(
        func.DATE(Crime.Offense_Date).label('date'),
        func.count(Crime.Report_Number)
    ).filter(func.DATE(Crime.Offense_Date) >= seven_days_ago) \
     .group_by('date').order_by('date').all()

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
            'values': hour_values,
            'view_type': view_type
        },
        'crime_today_yesterday_chart': today_vs_yesterday_data,
        'kpis': kpis,
        'daily_crime_chart': {
            'labels': daily_labels,
            'values': daily_values
        },
        'available_top_offenses': top_offense_categories
    })

@app.route('/api/analytical-data')
def get_analytical_data():
    # Get filter parameters from request
    selected_offense_categories = request.args.getlist('offense_categories')
    selected_nibrs_groups = request.args.getlist('nibrs_groups')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    selected_precincts = request.args.getlist('precincts')
    selected_neighborhoods = request.args.getlist('neighborhoods')
    export_format = request.args.get('export_format')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Fetch min/max dates for filter defaults
    min_offense_date = db.session.query(func.min(Crime.Offense_Date)).scalar()
    max_offense_date = db.session.query(func.max(Crime.Offense_Date)).scalar()
    min_report_datetime = db.session.query(func.min(Crime.Report_DateTime)).scalar()
    max_report_datetime = db.session.query(func.max(Crime.Report_DateTime)).scalar()

    # Get all available filter options
    filter_options = {
        'offense_categories': [row[0] for row in db.session.query(Crime.Offense_Category).distinct().order_by(Crime.Offense_Category).all()],
        'nibrs_groups': [row[0] for row in db.session.query(Crime.NIBRS_Group_AB).distinct().order_by(Crime.NIBRS_Group_AB).all()],
        'precincts': [row[0] for row in db.session.query(Crime.Precinct).distinct().order_by(Crime.Precinct).all()],
        'neighborhoods': [row[0] for row in db.session.query(Crime.Neighborhood).distinct().order_by(Crime.Neighborhood).all()]
    }

    # Build base query with filters
    query = Crime.query

    if selected_offense_categories:
        query = query.filter(Crime.Offense_Category.in_(selected_offense_categories))
    if selected_nibrs_groups:
        query = query.filter(Crime.NIBRS_Group_AB.in_(selected_nibrs_groups))
    if start_date_str:
        query = query.filter(Crime.Offense_Date >= datetime.strptime(start_date_str, '%Y-%m-%d').date())
    else:
        if min_offense_date:
            query = query.filter(Crime.Offense_Date >= min_offense_date.date())
    if end_date_str:
        query = query.filter(Crime.Offense_Date <= datetime.strptime(end_date_str, '%Y-%m-%d').date())
    else:
        if max_offense_date:
            query = query.filter(Crime.Offense_Date <= max_offense_date.date())
    if selected_precincts:
        query = query.filter(Crime.Precinct.in_(selected_precincts))
    if selected_neighborhoods:
        query = query.filter(Crime.Neighborhood.in_(selected_neighborhoods))

    # 1. Interactive Leaflet Map: Crime locations with clustering
    map_data = query.with_entities(
        Crime.Latitude,
        Crime.Longitude,
        Crime.Offense_Category,
        Crime.NIBRS_Group_AB,
        Crime.Report_DateTime,
        Crime.Location,
        Crime.Report_Number
    ).filter(
        Crime.Latitude.isnot(None),
        Crime.Longitude.isnot(None)
    ).limit(1000).all()

    map_points = [{
        'lat': point[0],
        'lng': point[1],
        'offense_category': point[2],
        'nibrs_group': point[3],
        'datetime': point[4].strftime('%Y-%m-%d %H:%M:%S') if point[4] else None,
        'location': point[5],
        'report_number': point[6]
    } for point in map_data]

    # 2. Bar Chart: Top reporting areas
    top_reporting_areas = query.with_entities(
        Crime.Reporting_Area,
        func.count(Crime.Report_Number).label('count')
    ).group_by(Crime.Reporting_Area) \
     .order_by(func.count(Crime.Report_Number).desc()) \
     .limit(20).all()

    reporting_area_chart = {
        'labels': [item[0] for item in top_reporting_areas],
        'values': [item[1] for item in top_reporting_areas]
    }

    # 3. Treemap: Crime distribution by category and NIBRS group
    treemap_data = query.with_entities(
        Crime.Offense_Category,
        Crime.NIBRS_Group_AB,
        func.count(Crime.Report_Number).label('count')
    ).group_by(Crime.Offense_Category, Crime.NIBRS_Group_AB).all()

    # Transform data for treemap visualization
    treemap_hierarchy = {
        'name': 'Crime Distribution',
        'children': []
    }
    
    # Group by offense category first
    category_groups = {}
    for cat, group, count in treemap_data:
        if cat not in category_groups:
            category_groups[cat] = {'total': 0, 'groups': {}}
        category_groups[cat]['groups'][group] = count
        category_groups[cat]['total'] += count

    # Build treemap hierarchy
    for cat, data in category_groups.items():
        category_node = {
            'name': cat,
            'value': data['total'],
            'children': [
                {'name': f'Group {group}', 'value': count}
                for group, count in data['groups'].items()
            ]
        }
        treemap_hierarchy['children'].append(category_node)

    # 4. Line Chart: Crimes over time for selected filters
    crimes_over_time = query.with_entities(
        func.DATE_FORMAT(Crime.Report_DateTime, '%Y-%m-%d').label('date'),
        func.count(Crime.Report_Number)
    ).group_by('date').order_by('date').all()
    
    crimes_over_time_chart = {
        'labels': [item[0] for item in crimes_over_time],
        'values': [item[1] for item in crimes_over_time]
    }

    # 5. Table: Filtered crime records with pagination and export support
    if export_format == 'csv':
        # Return CSV data for export
        crimes_export = query.all()
        csv_data = []
        for crime in crimes_export:
            csv_data.append({
                'Report_Number': crime.Report_Number,
                'Report_DateTime': crime.Report_DateTime.strftime('%Y-%m-%d %H:%M:%S') if crime.Report_DateTime else None,
                'Offense_Category': crime.Offense_Category,
                'NIBRS_Group_AB': crime.NIBRS_Group_AB,
                'Precinct': crime.Precinct,
                'Neighborhood': crime.Neighborhood,
                'Location': crime.Location,
                'Latitude': crime.Latitude,
                'Longitude': crime.Longitude,
                'Offense_Description': crime.Offense_Description
            })
        return jsonify({'csv_data': csv_data})

    # Regular paginated table data
    paginated_crimes = query.paginate(page=page, per_page=per_page, error_out=False)
    filtered_crimes_list = [{
        'Report_Number': crime.Report_Number,
        'Report_DateTime': crime.Report_DateTime.strftime('%Y-%m-%d %H:%M:%S') if crime.Report_DateTime else None,
        'Offense_Category': crime.Offense_Category,
        'NIBRS_Group_AB': crime.NIBRS_Group_AB,
        'Precinct': crime.Precinct,
        'Neighborhood': crime.Neighborhood,
        'Location': crime.Location,
        'Latitude': crime.Latitude,
        'Longitude': crime.Longitude,
        'Offense_Description': crime.Offense_Description
    } for crime in paginated_crimes.items]

    return jsonify({
        'filters': {
            'options': filter_options,
            'min_offense_date': min_offense_date.strftime('%Y-%m-%d') if min_offense_date else '',
            'max_offense_date': max_offense_date.strftime('%Y-%m-%d') if max_offense_date else '',
            'min_report_datetime': min_report_datetime.strftime('%Y-%m-%d %H:%M:%S') if min_report_datetime else '',
            'max_report_datetime': max_report_datetime.strftime('%Y-%m-%d %H:%M:%S') if max_report_datetime else ''
        },
        'map_data': map_points,
        'reporting_area_chart': reporting_area_chart,
        'treemap_data': treemap_hierarchy,
        'crimes_over_time_chart': crimes_over_time_chart,
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