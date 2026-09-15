from pathlib import Path


FORECAST_DAYS = 7
TRAIN_RATIO = 0.8
RANDOM_SEED = 42

FEATURE_COLUMNS = [
    'day_index',
    'day_of_week',
    'month',
    'day_of_month',
    'is_weekend',
    'lag_1',
    'lag_7',
    'rolling_mean_7',
]

ARTIFACT_DIR = Path(__file__).resolve().parent / 'artifacts' / 'load_forecast'
