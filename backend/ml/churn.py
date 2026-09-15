def recall_recommendation(inactive_days):
    """Return the matrix-defined recall level and copy for an inactive user."""
    if inactive_days >= 60:
        return '60_days', '老用户回归，送10元优惠券'
    if inactive_days >= 30:
        return '30_days', '您已30天未充电，本周充电立减5元'
    return None, None


def build_user_recall_rows(spark):
    """Find inactive users relative to the latest valid date in the dataset."""
    from pyspark.sql import functions as F

    orders = spark.table('orders').filter(F.col('created_date').isNotNull())
    analysis_date = orders.agg(F.max('created_date').alias('date')).first()['date']
    if analysis_date is None:
        return []

    users = (
        orders.groupBy('userId')
        .agg(
            F.max('created_date').alias('last_charge_date'),
            F.count('*').alias('total_orders'),
            F.round(F.sum('kwhTotal'), 2).alias('total_energy'),
        )
        .withColumn('inactive_days', F.datediff(F.lit(analysis_date), 'last_charge_date'))
        .filter(F.col('inactive_days') >= 30)
        .orderBy(F.desc('inactive_days'), F.desc('total_orders'))
    )

    rows = []
    for row in users.collect():
        level, message = recall_recommendation(row['inactive_days'])
        rows.append({
            'user_id': str(row['userId']),
            'last_charge_date': row['last_charge_date'],
            'inactive_days': row['inactive_days'],
            'total_orders': row['total_orders'],
            'total_energy': row['total_energy'],
            'recall_level': level,
            'recall_message': message,
            'analysis_date': analysis_date,
        })
    return rows
