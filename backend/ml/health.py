from pyspark.sql import Window
from pyspark.sql import functions as F


def _column_starting_with(frame, prefix):
    return next((name for name in frame.columns if name.startswith(prefix)), None)


def build_battery_health_rows(spark):
    """Estimate an explainable SOH reference score and thermal-risk level."""
    monitoring = spark.table('monitoring')
    orders = spark.table('orders')
    station_meta = spark.table('station_meta')

    max_voltage_column = _column_starting_with(monitoring, 'max_cell_voltage')
    min_voltage_column = _column_starting_with(monitoring, 'min_cell_voltage')
    max_temperature_column = _column_starting_with(monitoring, 'max_temperature')
    min_temperature_column = _column_starting_with(monitoring, 'min_temperature')
    required = {
        'max_cell_voltage': max_voltage_column,
        'min_cell_voltage': min_voltage_column,
        'max_temperature': max_temperature_column,
        'min_temperature': min_temperature_column,
    }
    missing = [label for label, column in required.items() if column is None]
    if missing:
        raise ValueError(f'Monitoring data is missing columns: {", ".join(missing)}')

    readings = (
        monitoring
        .withColumn('record_ts', F.to_timestamp(F.col('record_time').cast('string'), 'yyyyMMddHHmmss'))
        .withColumn('max_cell_voltage_num', F.col(max_voltage_column).cast('double'))
        .withColumn('min_cell_voltage_num', F.col(min_voltage_column).cast('double'))
        .withColumn('max_temperature_num', F.col(max_temperature_column).cast('double'))
        .withColumn('min_temperature_num', F.col(min_temperature_column).cast('double'))
        .withColumn('available_capacity_num', F.col('available_capacity').cast('double'))
        .withColumn(
            'voltage_delta',
            F.abs(F.col('max_cell_voltage_num') - F.col('min_cell_voltage_num')),
        )
        .withColumn(
            'temperature_delta',
            F.abs(F.col('max_temperature_num') - F.col('min_temperature_num')),
        )
    )

    session_window = Window.partitionBy('esd').orderBy('record_ts')
    readings = (
        readings
        .withColumn('previous_temperature', F.lag('max_temperature_num').over(session_window))
        .withColumn('previous_time', F.lag('record_ts').over(session_window))
        .withColumn(
            'elapsed_hours',
            (F.unix_timestamp('record_ts') - F.unix_timestamp('previous_time')) / 3600.0,
        )
        .withColumn(
            'temperature_rise_rate',
            F.when(
                F.col('elapsed_hours') > 0,
                F.greatest(
                    F.lit(0.0),
                    (F.col('max_temperature_num') - F.col('previous_temperature'))
                    / F.col('elapsed_hours'),
                ),
            ).otherwise(F.lit(None).cast('double')),
        )
    )

    if readings.filter(F.col('record_ts').isNotNull()).limit(1).count() == 0:
        print('      [WARN] record_time is invalid; temperature rise rate is unavailable.')

    sessions = (
        readings.groupBy('esd')
        .agg(
            F.max('voltage_delta').alias('voltage_delta'),
            F.max('max_temperature_num').alias('max_temperature'),
            F.max('temperature_delta').alias('temperature_delta'),
            F.max('temperature_rise_rate').alias('temperature_rise_rate'),
            F.avg('available_capacity_num').alias('avg_available_capacity'),
        )
        .withColumn(
            'soh_reference',
            F.round(
                F.greatest(
                    F.lit(0.0),
                    F.least(
                        F.lit(100.0),
                        F.lit(100.0)
                        - F.col('voltage_delta') * 800.0
                        - F.greatest(F.col('max_temperature') - 35.0, F.lit(0.0)) * 4.0
                        - F.col('temperature_delta') * 3.0
                        - F.greatest(
                            F.coalesce(F.col('temperature_rise_rate'), F.lit(0.0)) - 2.0,
                            F.lit(0.0),
                        ) * 1.5,
                    ),
                ),
                1,
            ),
        )
        .withColumn(
            'risk_level',
            F.when(
                (F.col('max_temperature') >= 40.0)
                | (F.col('voltage_delta') >= 0.030)
                | (F.coalesce(F.col('temperature_rise_rate'), F.lit(0.0)) >= 6.0),
                'high',
            )
            .when(
                (F.col('max_temperature') >= 36.0)
                | (F.col('voltage_delta') >= 0.020)
                | (F.coalesce(F.col('temperature_rise_rate'), F.lit(0.0)) >= 3.0),
                'medium',
            )
            .otherwise('low'),
        )
    )

    order_lookup = orders.select(
        F.col('sessionId').alias('order_session_id'), 'stationId', 'userId'
    ).dropDuplicates(['order_session_id'])
    meta_lookup = station_meta.select(
        F.col('stationId').alias('meta_station_id'), 'station_name'
    ).dropDuplicates(['meta_station_id'])

    result = (
        sessions
        .join(order_lookup, sessions.esd == order_lookup.order_session_id, 'left')
        .join(meta_lookup, F.col('stationId') == F.col('meta_station_id'), 'left')
        .select(
            F.col('esd').cast('string').alias('session_id'),
            F.col('stationId').cast('string').alias('station_id'),
            'station_name',
            F.col('userId').cast('string').alias('user_id'),
            'soh_reference',
            F.round('voltage_delta', 4).alias('voltage_delta'),
            F.round('max_temperature', 1).alias('max_temperature'),
            F.round('temperature_rise_rate', 2).alias('temperature_rise_rate'),
            'risk_level',
        )
        .orderBy(
            F.when(F.col('risk_level') == 'high', 1)
            .when(F.col('risk_level') == 'medium', 2)
            .otherwise(3),
            F.asc('soh_reference'),
        )
    )
    return [row.asDict() for row in result.collect()]
