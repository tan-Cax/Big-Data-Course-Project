from datetime import timedelta

from pyspark.sql import functions as F

from ml.config import FEATURE_COLUMNS
from ml.models import assemble_features


def test_prediction_rows(predictions):
    rows = predictions.select('stat_date', 'label', 'prediction').orderBy('stat_date').collect()
    return [
        {
            'stat_date': row['stat_date'],
            'data_type': 'test',
            'actual_energy': round(float(row['label']), 2),
            'predicted_energy': round(max(0.0, float(row['prediction'])), 2),
        }
        for row in rows
    ]


def future_prediction_rows(spark, model, daily_frame, forecast_days):
    history = [
        (row['stat_date'], float(row['label']))
        for row in daily_frame.select('stat_date', 'label').orderBy('stat_date').collect()
    ]
    if len(history) < 7:
        raise ValueError('At least seven daily observations are required for forecasting.')

    first_date = history[0][0]
    values = [value for _, value in history]
    next_date = history[-1][0] + timedelta(days=1)
    results = []

    for _ in range(forecast_days):
        python_weekday = next_date.isoweekday()
        feature_row = {
            'stat_date': next_date,
            'day_index': float((next_date - first_date).days),
            # Spark dayofweek uses Sunday=1 through Saturday=7.
            'day_of_week': float((python_weekday % 7) + 1),
            'month': float(next_date.month),
            'day_of_month': float(next_date.day),
            'is_weekend': float(python_weekday >= 6),
            'lag_1': float(values[-1]),
            'lag_7': float(values[-7]),
            'rolling_mean_7': float(sum(values[-7:]) / 7),
        }
        prediction_frame = assemble_features(spark.createDataFrame([feature_row]))
        prediction = model.transform(prediction_frame).select('prediction').first()[0]
        prediction = max(0.0, float(prediction))
        values.append(prediction)
        results.append({
            'stat_date': next_date,
            'data_type': 'future',
            'actual_energy': None,
            'predicted_energy': round(prediction, 2),
        })
        next_date += timedelta(days=1)

    return results
