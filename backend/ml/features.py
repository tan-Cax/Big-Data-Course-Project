from pyspark.sql import Window
from pyspark.sql import functions as F


def build_daily_features(orders):
    """Aggregate orders by day and add leakage-free calendar/lag features."""
    daily = (
        orders.filter(F.col('created_date').isNotNull())
        .groupBy(F.col('created_date').alias('stat_date'))
        .agg(F.sum('kwhTotal').alias('label'))
        .orderBy('stat_date')
    )

    bounds = daily.agg(F.min('stat_date'), F.max('stat_date')).first()
    first_date, last_date = bounds[0], bounds[1]
    calendar = orders.sparkSession.range(1).select(
        F.explode(
            F.sequence(
                F.lit(first_date), F.lit(last_date), F.expr('interval 1 day')
            )
        ).alias('stat_date')
    )
    daily = calendar.join(daily, 'stat_date', 'left').fillna({'label': 0.0})
    ordered = Window.orderBy('stat_date')
    previous_week = ordered.rowsBetween(-7, -1)

    return (
        daily
        .withColumn('day_index', F.datediff('stat_date', F.lit(first_date)).cast('double'))
        .withColumn('day_of_week', F.dayofweek('stat_date').cast('double'))
        .withColumn('month', F.month('stat_date').cast('double'))
        .withColumn('day_of_month', F.dayofmonth('stat_date').cast('double'))
        .withColumn(
            'is_weekend',
            F.when(F.dayofweek('stat_date').isin(1, 7), 1.0).otherwise(0.0),
        )
        .withColumn('lag_1', F.lag('label', 1).over(ordered))
        .withColumn('lag_7', F.lag('label', 7).over(ordered))
        .withColumn('rolling_mean_7', F.avg('label').over(previous_week))
        .dropna()
    )


def chronological_split(feature_frame, train_ratio):
    """Use earlier dates for training and later dates for honest evaluation."""
    total = feature_frame.count()
    if total < 30:
        raise ValueError(f'At least 30 usable days are required; found {total}.')

    train_size = max(1, min(total - 1, int(total * train_ratio)))
    numbered = feature_frame.withColumn(
        '_row_number', F.row_number().over(Window.orderBy('stat_date'))
    )
    train = numbered.filter(F.col('_row_number') <= train_size).drop('_row_number')
    test = numbered.filter(F.col('_row_number') > train_size).drop('_row_number')
    return train, test
