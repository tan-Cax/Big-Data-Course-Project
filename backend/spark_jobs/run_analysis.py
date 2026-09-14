import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType

from config import MYSQL_CONFIG, DATA_SOURCE, HDFS_PATH, LOCAL_PATH
import db

APP_NAME = 'NCS Charging Analysis'


def get_spark():
    return (SparkSession.builder
            .appName(APP_NAME)
            .master('local[*]')
            .config('spark.driver.memory', '2g')
            .config('spark.sql.legacy.timeParserPolicy', 'LEGACY')
            .getOrCreate())


def get_csv_path(spark, filename):
    if DATA_SOURCE == 'hdfs':
        hdfs_path = f'{HDFS_PATH}/{filename}'
        try:
            spark.read.csv(hdfs_path, header=True, encoding='UTF-8').limit(1).count()
            return hdfs_path
        except Exception:
            print(f'[WARN] HDFS not available, falling back to local: {filename}')
    return f'file://{LOCAL_PATH}/{filename}'


def read_csv(spark, filename):
    path = get_csv_path(spark, filename)
    return spark.read.csv(path, header=True, inferSchema=False, encoding='UTF-8')


def clean_orders(spark):
    df = read_csv(spark, 'nvv2t.csv')

    df = df.withColumn('sessionId', F.col('sessionId').cast('string'))
    df = df.withColumn('kwhTotal', F.col('kwhTotal').cast(DoubleType()))
    df = df.withColumn('charging_fees', F.col('charging_fees').cast(DoubleType()))
    df = df.withColumn('chargeTimeHrs', F.col('chargeTimeHrs').cast(DoubleType()))
    df = df.withColumn('startTime', F.col('startTime').cast(IntegerType()))
    df = df.withColumn('endTime', F.col('endTime').cast(IntegerType()))
    df = df.withColumn('facilityType', F.col('facilityType').cast(IntegerType()))

    df = df.withColumn('created', F.regexp_replace(F.trim(F.col('created')), r'^001', '201'))
    df = df.withColumn('ended', F.regexp_replace(F.trim(F.col('ended')), r'^001', '201'))
    df = df.withColumn('created_date', F.to_date(F.col('created'), 'yyyy-MM-dd HH:mm:ss'))
    df = df.withColumn('weekday', F.trim(F.col('weekday')))

    df = df.withColumn('is_weekend',
        F.when(F.col('weekday').isin('Sat', 'Sun'), 1).otherwise(0))

    df = df.withColumn('weekday_num',
        F.when(F.col('weekday') == 'Mon', 1)
         .when(F.col('weekday') == 'Tue', 2)
         .when(F.col('weekday') == 'Wed', 3)
         .when(F.col('weekday') == 'Thu', 4)
         .when(F.col('weekday') == 'Fri', 5)
         .when(F.col('weekday') == 'Sat', 6)
         .when(F.col('weekday') == 'Sun', 7)
         .otherwise(0))

    df = df.withColumn('facility_name',
        F.when(F.col('facilityType') == 1, '交流慢充')
         .when(F.col('facilityType') == 2, '直流快充')
         .when(F.col('facilityType') == 3, '交直流一体')
         .otherwise('其他'))

    df = df.na.fill(0, subset=['kwhTotal', 'charging_fees', 'chargeTimeHrs'])

    df.createOrReplaceTempView('orders')
    return df


def clean_station_meta(spark):
    df = read_csv(spark, 'nvv2t_md_end.csv')

    df = df.withColumnRenamed('\ufeffstationId', 'stationId')
    for col_name in df.columns:
        if col_name.startswith('\ufeff'):
            df = df.withColumnRenamed(col_name, col_name.replace('\ufeff', ''))

    for col_name in df.columns:
        df = df.withColumn(col_name, F.trim(F.col(col_name)))

    df.createOrReplaceTempView('station_meta')
    return df


def clean_monitoring(spark):
    df = read_csv(spark, 'dsv13r2.csv')

    df = df.withColumnRenamed('\ufeffesd', 'esd')
    for col_name in df.columns:
        if col_name.startswith('\ufeff'):
            df = df.withColumnRenamed(col_name, col_name.replace('\ufeff', ''))

    for col_name in df.columns:
        df = df.withColumn(col_name, F.trim(F.col(col_name)))

    df = df.withColumn('esd', F.col('esd').cast('string'))
    df = df.withColumn('soc', F.col('soc').cast(DoubleType()))
    df = df.withColumn('pack_voltage', F.col('pack_voltage (V)').cast(DoubleType()))
    df = df.withColumn('charge_current', F.col('charge_current (A)').cast(DoubleType()))
    df = df.withColumn('available_energy', F.col('available_energy (kw)').cast(DoubleType()))
    df = df.withColumn('available_capacity', F.col('available_capacity (Ah)').cast(DoubleType()))

    df.createOrReplaceTempView('monitoring')
    return df


def save_to_mysql(table_name, df):
    jdbc_url = f'jdbc:mysql://{MYSQL_CONFIG["host"]}:{MYSQL_CONFIG["port"]}/{MYSQL_CONFIG["database"]}?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai'
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
    df = spark.table('orders')
    total_orders = df.count()
    total_energy = df.agg(F.sum('kwhTotal')).collect()[0][0] or 0
    total_revenue = df.agg(F.sum('charging_fees')).collect()[0][0] or 0
    station_count = df.select('stationId').distinct().count()
    user_count = df.select('userId').distinct().count()

    peak_row = (df.groupBy('stationId')
        .agg(F.sum('kwhTotal').alias('e'))
        .orderBy(F.desc('e'))
        .first())
    peak_station = peak_row['stationId'] if peak_row else ''

    peak_meta = spark.table('station_meta').filter(F.col('stationId') == peak_station).first()
    peak_name = peak_meta['station_name'] if peak_meta else peak_station

    avg_duration = df.agg(F.avg('chargeTimeHrs')).collect()[0][0] or 0

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
    df = spark.table('orders').filter(F.col('created_date').isNotNull())
    agg = (df.groupBy('created_date')
        .agg(
            F.round(F.sum('kwhTotal'), 2).alias('total_energy'),
            F.count('*').alias('total_orders'),
            F.round(F.sum('charging_fees'), 2).alias('total_revenue'),
            F.countDistinct('userId').alias('unique_users'),
            F.round(F.avg('chargeTimeHrs'), 2).alias('avg_charge_time'),
        )
        .orderBy('created_date'))
    rows = [row.asDict() for row in agg.collect()]
    for r in rows:
        r['stat_date'] = r['created_date']
        del r['created_date']
    save_list_to_mysql('ads_daily_trend', rows)


def analysis_station(spark):
    orders = spark.table('orders')
    meta = spark.table('station_meta').select(
        F.col('stationId').alias('meta_stationId'),
        F.col('station_name').alias('meta_station_name'),
    )
    joined = orders.join(meta, orders.stationId == meta.meta_stationId, 'left')

    agg = (joined.groupBy(orders.stationId, 'meta_station_name', 'facilityType', 'facility_name')
        .agg(
            F.round(F.sum('kwhTotal'), 2).alias('total_energy'),
            F.count('*').alias('total_orders'),
            F.round(F.sum('charging_fees'), 2).alias('total_revenue'),
            F.round(F.avg('chargeTimeHrs'), 2).alias('avg_charge_time'),
        )
        .orderBy(F.desc('total_energy')))
    rows = []
    for row in agg.collect():
        rows.append({
            'station_id': row['stationId'],
            'station_name': row['meta_station_name'],
            'total_energy': row['total_energy'],
            'total_orders': row['total_orders'],
            'total_revenue': row['total_revenue'],
            'avg_charge_time': row['avg_charge_time'],
            'facility_type': row['facilityType'],
            'facility_name': row['facility_name'],
            'location_id': '',
        })
    save_list_to_mysql('ads_station_analysis', rows)


def analysis_hourly(spark):
    df = spark.table('orders')
    agg = (df.groupBy('startTime')
        .agg(
            F.round(F.sum('kwhTotal'), 2).alias('total_energy'),
            F.count('*').alias('total_orders'),
            F.round(F.avg('kwhTotal'), 2).alias('avg_energy_per_order'),
        )
        .orderBy('startTime'))
    rows = []
    for row in agg.collect():
        rows.append({
            'hour_of_day': row['startTime'],
            'total_energy': row['total_energy'],
            'total_orders': row['total_orders'],
            'avg_energy_per_order': row['avg_energy_per_order'],
        })
    save_list_to_mysql('ads_hourly_distribution', rows)


def analysis_weekday(spark):
    df = spark.table('orders')
    agg = (df.groupBy('weekday', 'weekday_num')
        .agg(
            F.round(F.sum('kwhTotal'), 2).alias('total_energy'),
            F.count('*').alias('total_orders'),
            F.round(F.sum('charging_fees'), 2).alias('total_revenue'),
            F.round(F.avg('chargeTimeHrs'), 2).alias('avg_charge_time'),
        )
        .orderBy('weekday_num'))
    rows = [row.asDict() for row in agg.collect()]
    save_list_to_mysql('ads_weekday_distribution', rows)


def analysis_facility(spark):
    df = spark.table('orders')
    agg = (df.groupBy('facilityType', 'facility_name')
        .agg(
            F.round(F.sum('kwhTotal'), 2).alias('total_energy'),
            F.count('*').alias('total_orders'),
            F.round(F.sum('charging_fees'), 2).alias('total_revenue'),
            F.countDistinct('stationId').alias('station_count'),
            F.round(F.avg('chargeTimeHrs'), 2).alias('avg_charge_time'),
        )
        .orderBy('facilityType'))
    rows = []
    for row in agg.collect():
        rows.append({
            'facility_type': row['facilityType'],
            'facility_name': row['facility_name'],
            'total_energy': row['total_energy'],
            'total_orders': row['total_orders'],
            'total_revenue': row['total_revenue'],
            'station_count': row['station_count'],
            'avg_charge_time': row['avg_charge_time'],
        })
    save_list_to_mysql('ads_facility_analysis', rows)


def analysis_user_behavior(spark):
    df = spark.table('orders').filter(F.col('kwhTotal') > 0)

    agg = (df.groupBy('userId')
        .agg(
            F.count('*').alias('total_orders'),
            F.round(F.sum('kwhTotal'), 2).alias('total_energy'),
            F.round(F.avg('kwhTotal'), 2).alias('avg_energy_per_order'),
            F.round(F.max('kwhTotal'), 2).alias('max_energy'),
            F.round(F.min('kwhTotal'), 2).alias('min_energy'),
            F.first('startTime').alias('preferred_hour'),
        )
        .orderBy(F.desc('total_orders')))

    rows = []
    for row in agg.collect():
        rows.append({
            'user_id': row['userId'],
            'total_orders': row['total_orders'],
            'total_energy': row['total_energy'],
            'avg_energy_per_order': row['avg_energy_per_order'],
            'max_energy': row['max_energy'],
            'min_energy': row['min_energy'],
            'preferred_hour': row['preferred_hour'],
        })
    save_list_to_mysql('ads_user_behavior', rows)


def analysis_platform(spark):
    df = spark.table('orders')
    agg = (df.groupBy('platform')
        .agg(
            F.count('*').alias('total_orders'),
            F.countDistinct('userId').alias('total_users'),
            F.round(F.sum('kwhTotal'), 2).alias('total_energy'),
            F.round(F.avg('kwhTotal'), 2).alias('avg_energy_per_order'),
        )
        .orderBy(F.desc('total_orders')))
    rows = [row.asDict() for row in agg.collect()]
    save_list_to_mysql('ads_platform_analysis', rows)


def analysis_efficiency(spark):
    orders = spark.table('orders')
    mon = spark.table('monitoring')
    joined = orders.join(mon, orders.sessionId == mon.esd, 'inner')

    meta = spark.table('station_meta').select(
        'stationId',
        F.col('station_name').alias('meta_station_name'),
    )
    joined = joined.join(meta, 'stationId', 'left')

    agg = (joined.groupBy('stationId', 'meta_station_name')
        .agg(
            F.round(F.avg('pack_voltage'), 1).alias('avg_voltage'),
            F.round(F.avg(F.abs('charge_current')), 1).alias('avg_current'),
            F.round(F.avg('available_energy'), 2).alias('avg_energy'),
            F.round(F.avg('chargeTimeHrs'), 2).alias('avg_duration'),
            F.round(F.avg('soc'), 1).alias('avg_soc'),
        )
        .orderBy(F.desc('avg_energy')))

    rows = []
    for row in agg.collect():
        rows.append({
            'station_id': row['stationId'],
            'station_name': row['meta_station_name'],
            'avg_voltage': row['avg_voltage'],
            'avg_current': row['avg_current'],
            'avg_energy': row['avg_energy'],
            'avg_duration': row['avg_duration'],
            'avg_soc': row['avg_soc'],
        })
    save_list_to_mysql('ads_efficiency_analysis', rows)


def analysis_utilization(spark):
    df = spark.table('orders')
    meta = spark.table('station_meta').select(
        'stationId',
        F.col('station_name').alias('meta_station_name'),
    )

    station_hours = (df.groupBy('stationId', 'startTime')
        .agg(F.count('*').alias('cnt'))
        .groupBy('stationId')
        .agg(F.countDistinct('startTime').alias('active_hours')))

    station_orders = (df.groupBy('stationId')
        .agg(F.count('*').alias('total_orders')))

    agg = (station_hours
        .join(station_orders, 'stationId')
        .join(meta, 'stationId', 'left')
        .withColumn('utilization_rate', F.round(F.col('active_hours') / 24.0, 4))
        .select('stationId', 'meta_station_name', 'utilization_rate', 'active_hours', 'total_orders')
        .orderBy(F.desc('utilization_rate')))

    rows = []
    for row in agg.collect():
        rows.append({
            'station_id': row['stationId'],
            'station_name': row['meta_station_name'],
            'utilization_rate': row['utilization_rate'],
            'active_hours': row['active_hours'],
            'total_orders': row['total_orders'],
        })
    save_list_to_mysql('ads_station_utilization', rows)


def analysis_hourly_station_cross(spark):
    orders = spark.table('orders')
    meta = spark.table('station_meta').select(
        'stationId',
        F.col('station_name').alias('meta_station_name'),
    )
    joined = orders.join(meta, 'stationId', 'left')

    agg = (joined.groupBy('startTime', 'stationId', 'meta_station_name')
        .agg(
            F.round(F.sum('kwhTotal'), 2).alias('total_energy'),
            F.count('*').alias('total_orders'),
        )
        .orderBy('startTime', F.desc('total_energy')))

    rows = []
    for row in agg.collect():
        rows.append({
            'hour_of_day': row['startTime'],
            'station_id': row['stationId'],
            'station_name': row['meta_station_name'],
            'total_energy': row['total_energy'],
            'total_orders': row['total_orders'],
        })
    save_list_to_mysql('ads_hourly_station_cross', rows)


def analysis_weekday_facility_cross(spark):
    df = spark.table('orders')

    agg = (df.groupBy('weekday', 'weekday_num', 'facilityType', 'facility_name')
        .agg(
            F.round(F.sum('kwhTotal'), 2).alias('total_energy'),
            F.count('*').alias('total_orders'),
            F.round(F.sum('charging_fees'), 2).alias('total_revenue'),
        )
        .orderBy('weekday_num', 'facilityType'))

    rows = []
    for row in agg.collect():
        rows.append({
            'weekday': row['weekday'],
            'weekday_num': row['weekday_num'],
            'facility_type': row['facilityType'],
            'facility_name': row['facility_name'],
            'total_energy': row['total_energy'],
            'total_orders': row['total_orders'],
            'total_revenue': row['total_revenue'],
        })
    save_list_to_mysql('ads_weekday_facility_cross', rows)


def run_all():
    print('=' * 60)
    print('NCS Charging Data Analysis - Starting...')
    print('=' * 60)

    spark = get_spark()
    spark.sparkContext.setLogLevel('WARN')

    print('\n[1/4] Cleaning data...')
    clean_orders(spark)
    clean_station_meta(spark)
    clean_monitoring(spark)
    print('  Data cleaning complete.')

    print('\n[2/4] Running 12 analysis dimensions...')

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

    print('\n[3/4] All analysis complete.')

    spark.stop()

    print('\n[4/4] Verifying MySQL data...')
    for table in ['ads_overview', 'ads_daily_trend', 'ads_station_analysis',
                   'ads_hourly_distribution', 'ads_weekday_distribution',
                   'ads_facility_analysis', 'ads_user_behavior',
                   'ads_platform_analysis', 'ads_efficiency_analysis',
                   'ads_station_utilization', 'ads_hourly_station_cross',
                   'ads_weekday_facility_cross']:
        rows = db.query_all(f'SELECT COUNT(*) as cnt FROM {table}')
        print(f'  {table}: {rows[0]["cnt"]} rows')

    print('\n' + '=' * 60)
    print('All done!')
    print('=' * 60)


if __name__ == '__main__':
    run_all()
