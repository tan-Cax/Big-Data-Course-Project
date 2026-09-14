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
