-- NCS 充电桩数据分析平台 - ADS 层建表
CREATE DATABASE IF NOT EXISTS ncs_dashboard DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ncs_dashboard;

-- 1. 总览指标
CREATE TABLE IF NOT EXISTS ads_overview (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(64),
    metric_value DOUBLE,
    metric_str_value VARCHAR(255),
    metric_unit VARCHAR(32),
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 每日趋势
CREATE TABLE IF NOT EXISTS ads_daily_trend (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stat_date DATE,
    total_energy DOUBLE,
    total_orders INT,
    total_revenue DOUBLE,
    unique_users INT,
    avg_charge_time DOUBLE,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 站点分析
CREATE TABLE IF NOT EXISTS ads_station_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_id VARCHAR(64),
    station_name VARCHAR(256),
    total_energy DOUBLE,
    total_orders INT,
    total_revenue DOUBLE,
    avg_charge_time DOUBLE,
    facility_type INT,
    facility_name VARCHAR(64),
    location_id VARCHAR(64),
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 时段分布
CREATE TABLE IF NOT EXISTS ads_hourly_distribution (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hour_of_day INT,
    total_energy DOUBLE,
    total_orders INT,
    avg_energy_per_order DOUBLE,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. 星期分布
CREATE TABLE IF NOT EXISTS ads_weekday_distribution (
    id INT AUTO_INCREMENT PRIMARY KEY,
    weekday VARCHAR(10),
    weekday_num INT,
    total_energy DOUBLE,
    total_orders INT,
    total_revenue DOUBLE,
    avg_charge_time DOUBLE,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. 设施类型分析
CREATE TABLE IF NOT EXISTS ads_facility_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    facility_type INT,
    facility_name VARCHAR(64),
    total_energy DOUBLE,
    total_orders INT,
    total_revenue DOUBLE,
    station_count INT,
    avg_charge_time DOUBLE,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. 用户行为分析
CREATE TABLE IF NOT EXISTS ads_user_behavior (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64),
    total_orders INT,
    total_energy DOUBLE,
    avg_energy_per_order DOUBLE,
    max_energy DOUBLE,
    min_energy DOUBLE,
    preferred_hour INT,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. 平台分布分析
CREATE TABLE IF NOT EXISTS ads_platform_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(64),
    total_orders INT,
    total_users INT,
    total_energy DOUBLE,
    avg_energy_per_order DOUBLE,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. 充电效率分析
CREATE TABLE IF NOT EXISTS ads_efficiency_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_id VARCHAR(64),
    station_name VARCHAR(256),
    avg_voltage DOUBLE,
    avg_current DOUBLE,
    avg_energy DOUBLE,
    avg_duration DOUBLE,
    avg_soc DOUBLE,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. 站点利用率
CREATE TABLE IF NOT EXISTS ads_station_utilization (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_id VARCHAR(64),
    station_name VARCHAR(256),
    utilization_rate DOUBLE COMMENT '有充电活动的小时数/24',
    active_hours INT,
    total_orders INT,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. 时段×站点交叉
CREATE TABLE IF NOT EXISTS ads_hourly_station_cross (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hour_of_day INT,
    station_id VARCHAR(64),
    station_name VARCHAR(256),
    total_energy DOUBLE,
    total_orders INT,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. 星期×设施交叉
CREATE TABLE IF NOT EXISTS ads_weekday_facility_cross (
    id INT AUTO_INCREMENT PRIMARY KEY,
    weekday VARCHAR(10),
    weekday_num INT,
    facility_type INT,
    facility_name VARCHAR(64),
    total_energy DOUBLE,
    total_orders INT,
    total_revenue DOUBLE,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 机器学习：负荷预测模型评估结果
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 机器学习：测试集预测及未来7天预测
CREATE TABLE IF NOT EXISTS ml_load_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stat_date DATE NOT NULL,
    data_type ENUM('test', 'future') NOT NULL,
    actual_energy DOUBLE NULL,
    predicted_energy DOUBLE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_prediction_date_type (stat_date, data_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 机器学习：VPP日级削峰填谷建议（课程演示）
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 机器学习：SOH参考分与热风险评估
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 智能营销：流失用户识别与召回建议（以数据集最后日期为分析基准）
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 设备预防性运维：站点健康评分与派修建议
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
