import db


def _replace_rows(table_name, columns, rows):
    db.execute(f'DELETE FROM {table_name}')
    if not rows:
        return

    placeholders = ', '.join(['%s'] * len(columns))
    sql = f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES ({placeholders})'
    connection = db.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.executemany(sql, [[row.get(column) for column in columns] for row in rows])
        connection.commit()
    finally:
        connection.close()


def save_model_metrics(comparisons, selected_name, training_rows, test_rows):
    rows = [
        {
            **item,
            'is_selected': item['model_name'] == selected_name,
            'training_rows': training_rows,
            'test_rows': test_rows,
        }
        for item in comparisons
    ]
    _replace_rows(
        'ml_load_model_metrics',
        ['model_name', 'rmse', 'mae', 'r2', 'is_selected', 'training_rows', 'test_rows'],
        rows,
    )


def save_load_predictions(rows):
    _replace_rows(
        'ml_load_predictions',
        ['stat_date', 'data_type', 'actual_energy', 'predicted_energy'],
        rows,
    )


def save_vpp_recommendations(rows):
    _replace_rows(
        'ml_vpp_recommendations',
        [
            'stat_date', 'predicted_energy', 'load_level', 'action',
            'recommended_shift_energy', 'reason',
        ],
        rows,
    )


def save_battery_health(rows):
    _replace_rows(
        'ml_battery_health',
        [
            'session_id', 'station_id', 'station_name', 'user_id',
            'soh_reference', 'voltage_delta', 'max_temperature',
            'temperature_rise_rate', 'risk_level',
        ],
        rows,
    )


def save_user_recall(rows):
    _replace_rows(
        'ml_user_recall',
        [
            'user_id', 'last_charge_date', 'inactive_days', 'total_orders',
            'total_energy', 'recall_level', 'recall_message', 'analysis_date',
        ],
        rows,
    )


def save_maintenance_recommendations(rows):
    _replace_rows(
        'ml_maintenance_recommendations',
        [
            'station_id', 'station_name', 'health_score', 'total_sessions',
            'high_risk_count', 'medium_risk_count', 'overtemp_count',
            'voltage_abnormal_count', 'priority', 'recommendation',
        ],
        rows,
    )
