import sys
import os
import json
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request
from flask_cors import CORS

import db

app = Flask(__name__)
CORS(app)


def success(data=None):
    return jsonify({'code': 0, 'data': data, 'message': 'ok'})


def error(msg):
    return jsonify({'code': -1, 'data': None, 'message': msg})


def rows_to_list(rows):
    result = []
    for row in rows:
        d = {}
        for k, v in row.items():
            if isinstance(v, datetime):
                d[k] = v.strftime('%Y-%m-%d')
            else:
                d[k] = v
        result.append(d)
    return result


@app.route('/api/overview')
def api_overview():
    rows = db.query_all('SELECT metric_name, metric_value, metric_str_value, metric_unit FROM ads_overview')
    data = {}
    for row in rows:
        if row['metric_str_value'] is not None:
            data[row['metric_name']] = row['metric_str_value']
        else:
            data[row['metric_name']] = row['metric_value']
    return success(data)


@app.route('/api/trend/daily')
def api_trend_daily():
    rows = db.query_all(
        'SELECT stat_date, total_energy, total_orders, total_revenue, unique_users, avg_charge_time '
        'FROM ads_daily_trend ORDER BY stat_date'
    )
    return success(rows_to_list(rows))


@app.route('/api/station/ranking')
def api_station_ranking():
    rows = db.query_all(
        'SELECT station_id, station_name, total_energy, total_orders, total_revenue, avg_charge_time, facility_name '
        'FROM ads_station_analysis ORDER BY total_energy DESC'
    )
    return success(rows_to_list(rows))


@app.route('/api/station/utilization')
def api_station_utilization():
    rows = db.query_all(
        'SELECT station_id, station_name, utilization_rate, active_hours, total_orders '
        'FROM ads_station_utilization ORDER BY utilization_rate DESC'
    )
    return success(rows_to_list(rows))


@app.route('/api/distribution/hourly')
def api_distribution_hourly():
    rows = db.query_all(
        'SELECT hour_of_day, total_energy, total_orders, avg_energy_per_order '
        'FROM ads_hourly_distribution ORDER BY hour_of_day'
    )
    return success(rows_to_list(rows))


@app.route('/api/distribution/weekday')
def api_distribution_weekday():
    rows = db.query_all(
        'SELECT weekday, weekday_num, total_energy, total_orders, total_revenue, avg_charge_time '
        'FROM ads_weekday_distribution ORDER BY weekday_num'
    )
    return success(rows_to_list(rows))


@app.route('/api/facility/type')
def api_facility_type():
    rows = db.query_all(
        'SELECT facility_type, facility_name, total_energy, total_orders, total_revenue, station_count, avg_charge_time '
        'FROM ads_facility_analysis ORDER BY facility_type'
    )
    return success(rows_to_list(rows))


@app.route('/api/user/behavior')
def api_user_behavior():
    rows = db.query_all(
        'SELECT user_id, total_orders, total_energy, avg_energy_per_order, max_energy, min_energy, preferred_hour '
        'FROM ads_user_behavior ORDER BY total_orders DESC'
    )
    return success(rows_to_list(rows))


@app.route('/api/platform/distribution')
def api_platform_distribution():
    rows = db.query_all(
        'SELECT platform, total_orders, total_users, total_energy, avg_energy_per_order '
        'FROM ads_platform_analysis ORDER BY total_orders DESC'
    )
    return success(rows_to_list(rows))


@app.route('/api/efficiency/radar')
def api_efficiency_radar():
    rows = db.query_all(
        'SELECT station_id, station_name, avg_voltage, avg_current, avg_energy, avg_duration, avg_soc '
        'FROM ads_efficiency_analysis ORDER BY avg_energy DESC'
    )
    return success(rows_to_list(rows))


@app.route('/api/comparison/hourly-station')
def api_comparison_hourly_station():
    rows = db.query_all(
        'SELECT hour_of_day, station_id, station_name, total_energy, total_orders '
        'FROM ads_hourly_station_cross ORDER BY hour_of_day, total_energy DESC'
    )
    return success(rows_to_list(rows))


@app.route('/api/comparison/weekday-facility')
def api_comparison_weekday_facility():
    rows = db.query_all(
        'SELECT weekday, weekday_num, facility_type, facility_name, total_energy, total_orders, total_revenue '
        'FROM ads_weekday_facility_cross ORDER BY weekday_num, facility_type'
    )
    return success(rows_to_list(rows))


@app.route('/api/reload', methods=['POST'])
def api_reload():
    try:
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spark_jobs', 'run_analysis.py')
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, timeout=300,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env={**os.environ, 'PYTHONPATH': os.environ.get('PYTHONPATH', '')}
        )
        if result.returncode == 0:
            return success({'message': 'Analysis complete', 'output': result.stdout[-500:]})
        else:
            return error(f'Analysis failed: {result.stderr[-500:]}')
    except subprocess.TimeoutExpired:
        return error('Analysis timed out (300s)')
    except Exception as e:
        return error(str(e))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
