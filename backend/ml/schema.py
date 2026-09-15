import db


SCHEMA_STATEMENTS = (
    '''
    CREATE TABLE IF NOT EXISTS ml_load_model_metrics (
        id INT AUTO_INCREMENT PRIMARY KEY,
        model_name VARCHAR(64) NOT NULL,
        rmse DOUBLE NOT NULL,
        mae DOUBLE NOT NULL,
        r2 DOUBLE NOT NULL,
        is_selected BOOLEAN NOT NULL DEFAULT FALSE,
        training_rows INT NOT NULL,
        test_rows INT NOT NULL,
        trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ml_load_predictions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stat_date DATE NOT NULL,
        data_type ENUM('test', 'future') NOT NULL,
        actual_energy DOUBLE NULL,
        predicted_energy DOUBLE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_prediction_date_type (stat_date, data_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ml_vpp_recommendations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stat_date DATE NOT NULL,
        predicted_energy DOUBLE NOT NULL,
        load_level ENUM('peak', 'valley', 'normal') NOT NULL,
        action VARCHAR(32) NOT NULL,
        recommended_shift_energy DOUBLE NOT NULL,
        reason VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_vpp_date (stat_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ml_battery_health (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_id VARCHAR(64) NOT NULL,
        station_id VARCHAR(64),
        station_name VARCHAR(256),
        user_id VARCHAR(64),
        soh_reference DOUBLE NOT NULL,
        voltage_delta DOUBLE,
        max_temperature DOUBLE,
        temperature_rise_rate DOUBLE,
        risk_level ENUM('high', 'medium', 'low') NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_health_session (session_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ml_user_recall (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(64) NOT NULL,
        last_charge_date DATE NOT NULL,
        inactive_days INT NOT NULL,
        total_orders INT NOT NULL,
        total_energy DOUBLE NOT NULL,
        recall_level ENUM('30_days', '60_days') NOT NULL,
        recall_message VARCHAR(255) NOT NULL,
        analysis_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_recall_user (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ml_maintenance_recommendations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        station_id VARCHAR(64) NOT NULL,
        station_name VARCHAR(256),
        health_score INT NOT NULL,
        total_sessions INT NOT NULL,
        high_risk_count INT NOT NULL,
        medium_risk_count INT NOT NULL,
        overtemp_count INT NOT NULL,
        voltage_abnormal_count INT NOT NULL,
        priority ENUM('high', 'medium', 'low') NOT NULL,
        recommendation VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_maintenance_station (station_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''',
)


def ensure_ml_tables():
    for statement in SCHEMA_STATEMENTS:
        db.execute(statement)
