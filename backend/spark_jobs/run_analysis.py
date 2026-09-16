import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, StringType

from config import MYSQL_CONFIG, DATA_SOURCE, HDFS_PATH, LOCAL_PATH
import db

APP_NAME = 'NCS Charging Data Warehouse'

HDFS_BASE = '/ncs/data'
HDFS_ODS = f'{HDFS_BASE}/ods'
HDFS_DWD = f'{HDFS_BASE}/dwd'
HDFS_DWS = f'{HDFS_BASE}/dws'


def get_spark():
    return (SparkSession.builder
            .appName(APP_NAME)
            .master('local[*]')
            .config('spark.driver.memory', '2g')
            .config('spark.sql.legacy.timeParserPolicy', 'LEGACY')
            .config('spark.sql.parquet.compression.codec', 'snappy')
            .config('spark.hadoop.fs.defaultFS', 'hdfs://localhost:9000')
            .getOrCreate())


def hdfs_mkdir(spark, path):
    import subprocess
    subprocess.run(['/opt/hadoop/bin/hdfs', 'dfs', '-mkdir', '-p', path],
                   capture_output=True, check=False)


def read_csv_local(spark, filename):
    path = f'file://{LOCAL_PATH}/{filename}'
    return spark.read.csv(path, header=True, inferSchema=False, encoding='UTF-8')


# =============================================================================
# 第1层 ODS — 原始数据层：读CSV，原样注册为临时视图
# =============================================================================
def build_ods(spark):
    print('\n[ODS] 原始数据层 — 读取CSV，注册ODS临时视图')
    hdfs_mkdir(spark, HDFS_ODS)

    # --- ods_charging_process (dsv13r2.csv 充电过程监测) ---
    df_proc = read_csv_local(spark, 'dsv13r2.csv')
    for c in df_proc.columns:
        if c.startswith('\ufeff'):
            df_proc = df_proc.withColumnRenamed(c, c.replace('\ufeff', ''))
        df_proc = df_proc.withColumn(c, F.trim(F.col(c)))
    df_proc = (df_proc
        .withColumn('esd', F.col('esd').cast('string'))
        .withColumn('record_time', F.col('record_time').cast('string'))
        .withColumn('soc', F.col('soc').cast(DoubleType()))
        .withColumn('pack_voltage', F.col('pack_voltage (V)').cast(DoubleType()))
        .withColumn('charge_current', F.col('charge_current (A)').cast(DoubleType()))
        .withColumn('max_cell_voltage', F.col('max_cell_voltage (V)').cast(DoubleType()))
        .withColumn('min_cell_voltage', F.col('min_cell_voltage (V)').cast(DoubleType()))
        .withColumn('max_temperature', F.col('max_temperature (\u2103)').cast(DoubleType()))
        .withColumn('min_temperature', F.col('min_temperature (\u2103)').cast(DoubleType()))
        .withColumn('available_energy', F.col('available_energy (kw)').cast(DoubleType()))
        .withColumn('available_capacity', F.col('available_capacity (Ah)').cast(DoubleType()))
    )
    df_proc.write.mode('overwrite').parquet(f'{HDFS_ODS}/ods_charging_process')
    df_proc.createOrReplaceTempView('ods_charging_process')
    print(f'  ods_charging_process: {df_proc.count()} rows')

    # --- ods_charging_order (nvv2t.csv 充电订单) ---
    df_ord = read_csv_local(spark, 'nvv2t.csv')
    for c in df_ord.columns:
        if c.startswith('\ufeff'):
            df_ord = df_ord.withColumnRenamed(c, c.replace('\ufeff', ''))
    df_ord = (df_ord
        .withColumn('sessionId', F.col('sessionId').cast('string'))
        .withColumn('kwhTotal', F.col('kwhTotal').cast(DoubleType()))
        .withColumn('charging_fees', F.col('charging_fees').cast(DoubleType()))
        .withColumn('chargeTimeHrs', F.col('chargeTimeHrs').cast(DoubleType()))
        .withColumn('startTime', F.col('startTime').cast(IntegerType()))
        .withColumn('endTime', F.col('endTime').cast(IntegerType()))
        .withColumn('facilityType', F.col('facilityType').cast(IntegerType()))
        .withColumn('created', F.trim(F.col('created')))
        .withColumn('ended', F.trim(F.col('ended')))
        .withColumn('weekday', F.trim(F.col('weekday')))
        .withColumn('platform', F.lower(F.trim(F.col('platform'))))
        .withColumn('userId', F.trim(F.col('userId')))
        .withColumn('stationId', F.trim(F.col('stationId')))
        .withColumn('locationId', F.trim(F.col('locationId')))
        .withColumn('created_date', F.to_date(F.regexp_replace(F.trim(F.col('created')), r'^001', '201'), 'yyyy-MM-dd HH:mm:ss'))
    )
    df_ord.write.mode('overwrite').parquet(f'{HDFS_ODS}/ods_charging_order')
    df_ord.createOrReplaceTempView('ods_charging_order')
    print(f'  ods_charging_order: {df_ord.count()} rows')

    # --- ods_charging_station_meta (nvv2t_md_end.csv 站点元数据) ---
    df_meta = read_csv_local(spark, 'nvv2t_md_end.csv')
    for c in df_meta.columns:
        if c.startswith('\ufeff'):
            df_meta = df_meta.withColumnRenamed(c, c.replace('\ufeff', ''))
    for c in df_meta.columns:
        df_meta = df_meta.withColumn(c, F.trim(F.col(c)))
    df_meta.write.mode('overwrite').parquet(f'{HDFS_ODS}/ods_charging_station_meta')
    df_meta.createOrReplaceTempView('ods_charging_station_meta')
    print(f'  ods_charging_station_meta: {df_meta.count()} rows')


# =============================================================================
# 第2层 DWD — 明细数据层：三表JOIN清洗，写HDFS
# =============================================================================
def build_dwd(spark):
    print('\n[DWD] 明细数据层 — 三表JOIN + 清洗 → dwd_charge_detail')

    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW dwd_charge_detail AS
        SELECT
            o.sessionId                                                    AS session_id,
            o.userId                                                       AS user_id,
            o.stationId                                                    AS station_id,
            o.locationId                                                   AS location_id,
            m.station_name                                                 AS station_name,
            m.address                                                      AS address,
            CAST(o.facilityType AS STRING)                                  AS facility_type,
            CASE o.facilityType WHEN 1 THEN '交流慢充'
                                WHEN 2 THEN '直流快充'
                                WHEN 3 THEN '交直流一体'
                                ELSE '其他' END                            AS station_type,
            CAST(COALESCE(NULLIF(m.device_count, ''), '0') AS INT)        AS device_count,
            o.platform                                                     AS platform,
            CAST(o.managerVehicle AS INT)                                  AS manager_vehicle,
            o.kwhTotal                                                     AS kwh,
            o.charging_fees                                                AS total_fee,
            o.chargeTimeHrs                                                AS duration_hrs,
            o.startTime                                                    AS start_hour,
            o.endTime                                                      AS end_hour,
            o.weekday                                                      AS weekday,
            CASE WHEN o.weekday IN ('Sat', 'Sun') THEN 1 ELSE 0 END       AS is_weekend,
            p.soc                                                          AS soc,
            p.pack_voltage                                                 AS pack_voltage,
            p.charge_current                                               AS charge_current,
            p.max_temperature                                              AS max_temp,
            p.min_temperature                                              AS min_temp,
            CAST(NULL AS STRING)                                           AS start_time,
            CAST(NULL AS STRING)                                           AS charge_date,
            to_date(regexp_replace(trim(o.created), '^001', '201'), 'yyyy-MM-dd HH:mm:ss') AS created_date,
            CAST(substr(CAST(CAST(p.record_time AS DOUBLE) AS BIGINT),1,4) AS INT) AS year,
            CAST(NULL AS INT)                                              AS month,
            CAST(NULL AS INT)                                              AS day
        FROM ods_charging_order o
        LEFT JOIN ods_charging_process p ON o.sessionId = p.esd
        LEFT JOIN ods_charging_station_meta m ON o.stationId = m.stationId
        WHERE o.kwhTotal > 0
          AND o.chargeTimeHrs > 0
    """)

    df_dwd = spark.table('dwd_charge_detail')
    hdfs_mkdir(spark, HDFS_DWD)
    df_dwd.write.mode('overwrite').parquet(f'{HDFS_DWD}/dwd_charge_detail')
    print(f'  dwd_charge_detail: {df_dwd.count()} rows')

    # 重新从HDFS读取注册（确保持久化后一致性）
    spark.read.parquet(f'{HDFS_DWD}/dwd_charge_detail').createOrReplaceTempView('dwd_charge_detail')


# =============================================================================
# 第3层 DWS — 聚合数据层：5张主题表，写HDFS
# =============================================================================
def build_dws(spark):
    print('\n[DWS] 聚合数据层 — 5张主题聚合表')
    hdfs_mkdir(spark, HDFS_DWS)

    # --- 1. dws_station_agg：按充电站汇总 ---
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW dws_station_agg AS
        SELECT
            station_id,
            station_name,
            MAX(address)        AS address,
            MAX(location_id)    AS location_id,
            MAX(station_type)   AS station_type,
            MAX(device_count) AS device_count,
            COUNT(*)            AS total_sessions,
            ROUND(SUM(kwh), 2)  AS total_kwh,
            ROUND(SUM(total_fee), 2) AS total_fee,
            ROUND(AVG(duration_hrs), 3) AS avg_duration,
            ROUND(AVG(kwh), 3)  AS avg_kwh
        FROM dwd_charge_detail
        GROUP BY station_id, station_name
    """)
    spark.table('dws_station_agg').write.mode('overwrite').parquet(f'{HDFS_DWS}/dws_station_agg')
    spark.read.parquet(f'{HDFS_DWS}/dws_station_agg').createOrReplaceTempView('dws_station_agg')
    print(f'  dws_station_agg: {spark.table("dws_station_agg").count()} rows')

    # --- 2. dws_user_agg：按用户汇总 ---
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW dws_user_agg AS
        SELECT
            user_id,
            COUNT(*)            AS charge_count,
            ROUND(SUM(kwh), 2)  AS total_kwh,
            ROUND(SUM(total_fee), 2) AS total_fee,
            ROUND(AVG(kwh), 3)  AS avg_kwh,
            MAX(platform)       AS main_platform
        FROM dwd_charge_detail
        GROUP BY user_id
    """)
    spark.table('dws_user_agg').write.mode('overwrite').parquet(f'{HDFS_DWS}/dws_user_agg')
    spark.read.parquet(f'{HDFS_DWS}/dws_user_agg').createOrReplaceTempView('dws_user_agg')
    print(f'  dws_user_agg: {spark.table("dws_user_agg").count()} rows')

    # --- 3. dws_hour_agg：按充电开始小时汇总 ---
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW dws_hour_agg AS
        SELECT
            start_hour          AS hour,
            COUNT(*)            AS sessions,
            ROUND(SUM(kwh), 2)  AS total_kwh,
            ROUND(SUM(total_fee), 2) AS total_fee
        FROM dwd_charge_detail
        WHERE start_hour BETWEEN 0 AND 23
        GROUP BY start_hour
    """)
    spark.table('dws_hour_agg').write.mode('overwrite').parquet(f'{HDFS_DWS}/dws_hour_agg')
    spark.read.parquet(f'{HDFS_DWS}/dws_hour_agg').createOrReplaceTempView('dws_hour_agg')
    print(f'  dws_hour_agg: {spark.table("dws_hour_agg").count()} rows')

    # --- 4. dws_dim_agg：通用维度聚合（weekday/platform/station_type/is_weekend/soc_segment） ---
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW dws_dim_agg AS
        SELECT 'weekday' AS dim_type, weekday AS dim_value,
               COUNT(*) AS sessions, ROUND(SUM(kwh),2) AS total_kwh, ROUND(SUM(total_fee),2) AS total_fee
        FROM dwd_charge_detail GROUP BY weekday
        UNION ALL
        SELECT 'platform', platform,
               COUNT(*), ROUND(SUM(kwh),2), ROUND(SUM(total_fee),2)
        FROM dwd_charge_detail GROUP BY platform
        UNION ALL
        SELECT 'station_type', station_type,
               COUNT(*), ROUND(SUM(kwh),2), ROUND(SUM(total_fee),2)
        FROM dwd_charge_detail GROUP BY station_type
        UNION ALL
        SELECT 'is_weekend', CASE WHEN is_weekend=1 THEN '周末' ELSE '工作日' END,
               COUNT(*), ROUND(SUM(kwh),2), ROUND(SUM(total_fee),2)
        FROM dwd_charge_detail GROUP BY is_weekend
        UNION ALL
        SELECT 'soc_segment',
               CASE WHEN soc IS NULL THEN '无BMS明细'
                    WHEN soc < 20 THEN '低电量(<20%)'
                    WHEN soc < 50 THEN '中电量(20-50%)'
                    WHEN soc < 80 THEN '高电量(50-80%)'
                    ELSE '满电(>=80%)' END,
               COUNT(*), ROUND(SUM(kwh),2), ROUND(SUM(total_fee),2)
        FROM dwd_charge_detail
        GROUP BY CASE WHEN soc IS NULL THEN '无BMS明细'
                      WHEN soc < 20 THEN '低电量(<20%)'
                      WHEN soc < 50 THEN '中电量(20-50%)'
                      WHEN soc < 80 THEN '高电量(50-80%)'
                      ELSE '满电(>=80%)' END
    """)
    spark.table('dws_dim_agg').write.mode('overwrite').parquet(f'{HDFS_DWS}/dws_dim_agg')
    spark.read.parquet(f'{HDFS_DWS}/dws_dim_agg').createOrReplaceTempView('dws_dim_agg')
    print(f'  dws_dim_agg: {spark.table("dws_dim_agg").count()} rows')

    # --- 5. dws_bms_agg：BMS电池健康监测 ---
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW dws_bms_agg AS
        SELECT
            CASE WHEN soc < 20 THEN '亏电(<20%)'
                 WHEN soc < 50 THEN '低电量(20-50%)'
                 WHEN soc < 80 THEN '健康(50-80%)'
                 ELSE '满电(>=80%)' END       AS health_level,
            COUNT(*)                           AS sess_count,
            ROUND(AVG(soc), 2)                 AS avg_soc,
            ROUND(AVG(pack_voltage), 2)        AS avg_pack_voltage,
            ROUND(MAX(max_temp), 2)            AS max_temp
        FROM dwd_charge_detail
        WHERE soc IS NOT NULL
        GROUP BY CASE WHEN soc < 20 THEN '亏电(<20%)'
                      WHEN soc < 50 THEN '低电量(20-50%)'
                      WHEN soc < 80 THEN '健康(50-80%)'
                      ELSE '满电(>=80%)' END
    """)
    spark.table('dws_bms_agg').write.mode('overwrite').parquet(f'{HDFS_DWS}/dws_bms_agg')
    spark.read.parquet(f'{HDFS_DWS}/dws_bms_agg').createOrReplaceTempView('dws_bms_agg')
    print(f'  dws_bms_agg: {spark.table("dws_bms_agg").count()} rows')


# =============================================================================
# 第4层 ADS — 应用数据层：12个分析维度，从DWS/DWD读取 → 写MySQL
# =============================================================================
def save_to_mysql(table_name, df):
    jdbc_url = (f'jdbc:mysql://{MYSQL_CONFIG["host"]}:{MYSQL_CONFIG["port"]}'
                f'/{MYSQL_CONFIG["database"]}?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai')
    props = {
        'user': MYSQL_CONFIG['user'],
        'password': MYSQL_CONFIG['password'],
        'driver': 'com.mysql.cj.jdbc.Driver',
    }
    df.write.mode('overwrite').jdbc(jdbc_url, table_name, properties=props)
    print(f'  -> {table_name}: {df.count()} rows saved')


def save_list_to_mysql(table_name, rows):
    db.execute(f'DELETE FROM {table_name}')
    if not rows:
        print(f'  -> {table_name}: 0 rows (empty)')
        return
    cols = list(rows[0].keys())
    placeholders = ','.join(['%s'] * len(cols))
    col_str = ','.join(cols)
    sql = f'INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})'
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(sql, list(row.values()))
        conn.commit()
        print(f'  -> {table_name}: {len(rows)} rows saved')
    finally:
        conn.close()


def analysis_overview(spark):
    df = spark.table('dwd_charge_detail')
    total_orders = df.count()
    total_energy = df.agg(F.sum('kwh')).collect()[0][0] or 0
    total_revenue = df.agg(F.sum('total_fee')).collect()[0][0] or 0
    station_count = df.select('station_id').distinct().count()
    user_count = df.select('user_id').distinct().count()

    peak_row = (df.groupBy('station_id')
        .agg(F.sum('kwh').alias('e'))
        .orderBy(F.desc('e'))
        .first())
    peak_station = peak_row['station_id'] if peak_row else ''
    peak_meta = spark.table('ods_charging_station_meta').filter(F.col('stationId') == peak_station).first()
    peak_name = peak_meta['station_name'] if peak_meta else peak_station

    avg_duration = df.agg(F.avg('duration_hrs')).collect()[0][0] or 0

    rows = [
        {'metric_name': 'total_orders', 'metric_value': total_orders, 'metric_str_value': None, 'metric_unit': ''},
        {'metric_name': 'total_energy', 'metric_value': round(total_energy, 2), 'metric_str_value': None, 'metric_unit': 'kWh'},
        {'metric_name': 'total_revenue', 'metric_value': round(total_revenue, 2), 'metric_str_value': None, 'metric_unit': '元'},
        {'metric_name': 'station_count', 'metric_value': station_count, 'metric_str_value': None, 'metric_unit': ''},
        {'metric_name': 'user_count', 'metric_value': user_count, 'metric_str_value': None, 'metric_unit': ''},
        {'metric_name': 'peak_station', 'metric_value': 0, 'metric_str_value': peak_name, 'metric_unit': ''},
        {'metric_name': 'avg_duration', 'metric_value': round(avg_duration, 2), 'metric_str_value': None, 'metric_unit': '小时'},
    ]
    save_list_to_mysql('ads_overview', rows)


def analysis_daily_trend(spark):
    df = spark.table('dwd_charge_detail').filter(F.col('created_date').isNotNull())
    agg = (df.groupBy('created_date')
        .agg(
            F.round(F.sum('kwh'), 2).alias('total_energy'),
            F.count('*').alias('total_orders'),
            F.round(F.sum('total_fee'), 2).alias('total_revenue'),
            F.countDistinct('user_id').alias('unique_users'),
            F.round(F.avg('duration_hrs'), 2).alias('avg_charge_time'),
        )
        .orderBy('created_date'))
    rows = []
    for row in agg.collect():
        rows.append({
            'stat_date': row['created_date'],
            'total_energy': row['total_energy'],
            'total_orders': row['total_orders'],
            'total_revenue': row['total_revenue'],
            'unique_users': row['unique_users'],
            'avg_charge_time': row['avg_charge_time'],
        })
    save_list_to_mysql('ads_daily_trend', rows)


def analysis_station(spark):
    df = spark.table('dws_station_agg')
    agg = (df.select(
            F.col('station_id'),
            F.col('station_name'),
            F.col('total_kwh').alias('total_energy'),
            F.col('total_sessions').alias('total_orders'),
            F.col('total_fee').alias('total_revenue'),
            F.col('avg_duration').alias('avg_charge_time'),
            F.lit(0).alias('facility_type'),
            F.col('station_type').alias('facility_name'),
            F.lit('').alias('location_id'),
        ).orderBy(F.desc('total_energy')))
    rows = [row.asDict() for row in agg.collect()]
    save_list_to_mysql('ads_station_analysis', rows)


def analysis_hourly(spark):
    df = spark.table('dws_hour_agg')
    rows = []
    for row in df.orderBy('hour').collect():
        rows.append({
            'hour_of_day': row['hour'],
            'total_energy': row['total_kwh'],
            'total_orders': row['sessions'],
            'avg_energy_per_order': round(row['total_kwh'] / row['sessions'], 2) if row['sessions'] > 0 else 0,
        })
    save_list_to_mysql('ads_hourly_distribution', rows)


def analysis_weekday(spark):
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW _tmp_weekday AS
        SELECT dim_value AS weekday,
               sessions AS total_orders,
               total_kwh AS total_energy,
               total_fee AS total_revenue
        FROM dws_dim_agg
        WHERE dim_type = 'weekday'
    """)
    df = spark.table('_tmp_weekday')
    weekday_map = {'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5, 'Sat': 6, 'Sun': 7}
    rows = []
    for row in df.collect():
        rows.append({
            'weekday': row['weekday'],
            'weekday_num': weekday_map.get(row['weekday'], 0),
            'total_energy': row['total_energy'],
            'total_orders': row['total_orders'],
            'total_revenue': row['total_revenue'],
            'avg_charge_time': 0,
        })
    rows.sort(key=lambda r: r['weekday_num'])
    save_list_to_mysql('ads_weekday_distribution', rows)


def analysis_facility(spark):
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW _tmp_facility AS
        SELECT dim_value AS facility_name,
               sessions AS total_orders,
               total_kwh AS total_energy,
               total_fee AS total_revenue
        FROM dws_dim_agg
        WHERE dim_type = 'station_type'
    """)
    df = spark.table('_tmp_facility')
    type_map = {'交流慢充': 1, '直流快充': 2, '交直流一体': 3, '其他': 4}
    rows = []
    for row in df.collect():
        rows.append({
            'facility_type': type_map.get(row['facility_name'], 0),
            'facility_name': row['facility_name'],
            'total_energy': row['total_energy'],
            'total_orders': row['total_orders'],
            'total_revenue': row['total_revenue'],
            'station_count': 0,
            'avg_charge_time': 0,
        })
    save_list_to_mysql('ads_facility_analysis', rows)


def analysis_user_behavior(spark):
    df = spark.table('dws_user_agg')
    rows = []
    for row in df.orderBy(F.desc('charge_count')).collect():
        rows.append({
            'user_id': row['user_id'],
            'total_orders': row['charge_count'],
            'total_energy': row['total_kwh'],
            'avg_energy_per_order': row['avg_kwh'],
            'max_energy': row['total_kwh'],
            'min_energy': 0,
            'preferred_hour': 0,
        })
    save_list_to_mysql('ads_user_behavior', rows)


def analysis_platform(spark):
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW _tmp_platform AS
        SELECT dim_value AS platform,
               sessions AS total_orders,
               total_kwh AS total_energy
        FROM dws_dim_agg
        WHERE dim_type = 'platform'
    """)
    df = spark.table('_tmp_platform')
    rows = []
    for row in df.orderBy(F.desc('total_orders')).collect():
        rows.append({
            'platform': row['platform'],
            'total_orders': row['total_orders'],
            'total_users': 0,
            'total_energy': row['total_energy'],
            'avg_energy_per_order': round(row['total_energy'] / row['total_orders'], 2) if row['total_orders'] > 0 else 0,
        })
    save_list_to_mysql('ads_platform_analysis', rows)


def analysis_efficiency(spark):
    df = spark.table('dwd_charge_detail').filter(F.col('soc').isNotNull())
    agg = (df.groupBy('station_id', 'station_name')
        .agg(
            F.round(F.avg('pack_voltage'), 1).alias('avg_voltage'),
            F.round(F.avg(F.abs('charge_current')), 1).alias('avg_current'),
            F.round(F.avg('kwh'), 2).alias('avg_energy'),
            F.round(F.avg('duration_hrs'), 2).alias('avg_duration'),
            F.round(F.avg('soc'), 1).alias('avg_soc'),
        )
        .orderBy(F.desc('avg_energy')))
    rows = []
    for row in agg.collect():
        rows.append({
            'station_id': row['station_id'],
            'station_name': row['station_name'],
            'avg_voltage': row['avg_voltage'],
            'avg_current': row['avg_current'],
            'avg_energy': row['avg_energy'],
            'avg_duration': row['avg_duration'],
            'avg_soc': row['avg_soc'],
        })
    save_list_to_mysql('ads_efficiency_analysis', rows)


def analysis_utilization(spark):
    df = spark.table('dwd_charge_detail')
    station_hours = (df.groupBy('station_id', 'start_hour')
        .agg(F.count('*').alias('cnt'))
        .groupBy('station_id')
        .agg(F.countDistinct('start_hour').alias('active_hours')))
    station_orders = (df.groupBy('station_id')
        .agg(F.count('*').alias('total_orders')))
    agg = (station_hours
        .join(station_orders, 'station_id')
        .withColumn('utilization_rate', F.round(F.col('active_hours') / 24.0, 4))
        .orderBy(F.desc('utilization_rate')))
    rows = []
    for row in agg.collect():
        meta = spark.table('ods_charging_station_meta').filter(F.col('stationId') == row['station_id']).first()
        rows.append({
            'station_id': row['station_id'],
            'station_name': meta['station_name'] if meta else row['station_id'],
            'utilization_rate': row['utilization_rate'],
            'active_hours': row['active_hours'],
            'total_orders': row['total_orders'],
        })
    save_list_to_mysql('ads_station_utilization', rows)


def analysis_hourly_station_cross(spark):
    df = spark.table('dwd_charge_detail')
    agg = (df.groupBy('start_hour', 'station_id', 'station_name')
        .agg(
            F.round(F.sum('kwh'), 2).alias('total_energy'),
            F.count('*').alias('total_orders'),
        )
        .orderBy('start_hour', F.desc('total_energy')))
    rows = []
    for row in agg.collect():
        rows.append({
            'hour_of_day': row['start_hour'],
            'station_id': row['station_id'],
            'station_name': row['station_name'],
            'total_energy': row['total_energy'],
            'total_orders': row['total_orders'],
        })
    save_list_to_mysql('ads_hourly_station_cross', rows)


def analysis_weekday_facility_cross(spark):
    df = spark.table('dwd_charge_detail')
    weekday_map = {'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5, 'Sat': 6, 'Sun': 7}
    type_map = {'交流慢充': 1, '直流快充': 2, '交直流一体': 3, '其他': 4}
    agg = (df.groupBy('weekday', 'station_type')
        .agg(
            F.round(F.sum('kwh'), 2).alias('total_energy'),
            F.count('*').alias('total_orders'),
            F.round(F.sum('total_fee'), 2).alias('total_revenue'),
        )
        .orderBy('weekday', 'station_type'))
    rows = []
    for row in agg.collect():
        rows.append({
            'weekday': row['weekday'],
            'weekday_num': weekday_map.get(row['weekday'], 0),
            'facility_type': type_map.get(row['station_type'], 0),
            'facility_name': row['station_type'],
            'total_energy': row['total_energy'],
            'total_orders': row['total_orders'],
            'total_revenue': row['total_revenue'],
        })
    save_list_to_mysql('ads_weekday_facility_cross', rows)


# =============================================================================
# 主流程
# =============================================================================
def run_all():
    print('=' * 60)
    print('NCS Charging Data Warehouse — 四层架构 ETL Pipeline')
    print('=' * 60)

    spark = get_spark()
    spark.sparkContext.setLogLevel('WARN')

    # 第1层 ODS
    build_ods(spark)

    # 第2层 DWD
    build_dwd(spark)

    # 第3层 DWS
    build_dws(spark)

    # 第4层 ADS → MySQL
    print('\n[ADS] 应用数据层 — 12个分析维度写入MySQL')

    print('  [1/12] Overview...')
    analysis_overview(spark)
    print('  [2/12] Daily trend...')
    analysis_daily_trend(spark)
    print('  [3/12] Station analysis...')
    analysis_station(spark)
    print('  [4/12] Hourly distribution...')
    analysis_hourly(spark)
    print('  [5/12] Weekday distribution...')
    analysis_weekday(spark)
    print('  [6/12] Facility type...')
    analysis_facility(spark)
    print('  [7/12] User behavior...')
    analysis_user_behavior(spark)
    print('  [8/12] Platform distribution...')
    analysis_platform(spark)
    print('  [9/12] Charging efficiency...')
    analysis_efficiency(spark)
    print('  [10/12] Station utilization...')
    analysis_utilization(spark)
    print('  [11/12] Hourly x Station cross...')
    analysis_hourly_station_cross(spark)
    print('  [12/12] Weekday x Facility cross...')
    analysis_weekday_facility_cross(spark)

    spark.stop()

    print('\n[VERIFY] 验证MySQL写入...')
    for table in ['ads_overview', 'ads_daily_trend', 'ads_station_analysis',
                   'ads_hourly_distribution', 'ads_weekday_distribution',
                   'ads_facility_analysis', 'ads_user_behavior',
                   'ads_platform_analysis', 'ads_efficiency_analysis',
                   'ads_station_utilization', 'ads_hourly_station_cross',
                   'ads_weekday_facility_cross']:
        rows = db.query_all(f'SELECT COUNT(*) as cnt FROM {table}')
        print(f'  {table}: {rows[0]["cnt"]} rows')

    print('\n' + '=' * 60)
    print('Four-layer data warehouse ETL complete!')
    print('=' * 60)


# =============================================================================
# ML 兼容接口 — 向后兼容 ml/ 模块的导入
# =============================================================================
def clean_orders(spark):
    build_ods(spark)
    df = spark.table('ods_charging_order')
    df.createOrReplaceTempView('orders')
    return df


def clean_station_meta(spark):
    build_ods(spark)
    df = spark.table('ods_charging_station_meta')
    df.createOrReplaceTempView('station_meta')
    return df


def clean_monitoring(spark):
    build_ods(spark)
    df = spark.table('ods_charging_process')
    df.createOrReplaceTempView('monitoring')
    return df


if __name__ == '__main__':
    run_all()
