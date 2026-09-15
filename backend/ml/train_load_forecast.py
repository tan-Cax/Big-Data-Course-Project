import os
import shutil
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from ml.config import ARTIFACT_DIR, FORECAST_DAYS, TRAIN_RATIO
from ml.churn import build_user_recall_rows
from ml.features import build_daily_features, chronological_split
from ml.forecast import future_prediction_rows, test_prediction_rows
from ml.health import build_battery_health_rows
from ml.maintenance import build_maintenance_rows
from ml.models import fit_selected_on_all_data, train_and_select
from ml.repository import (
    save_battery_health,
    save_load_predictions,
    save_maintenance_recommendations,
    save_model_metrics,
    save_user_recall,
    save_vpp_recommendations,
)
from ml.schema import ensure_ml_tables
from ml.vpp import build_vpp_recommendations
from spark_jobs.run_analysis import (
    clean_monitoring,
    clean_orders,
    clean_station_meta,
    get_spark,
)


def train_load_forecast():
    ensure_ml_tables()
    spark = get_spark()
    spark.sparkContext.setLogLevel('WARN')
    try:
        print('[1/9] Loading and aggregating charging orders...')
        orders = clean_orders(spark)
        daily_features = build_daily_features(orders).cache()
        train_frame, test_frame = chronological_split(daily_features, TRAIN_RATIO)
        training_rows = train_frame.count()
        test_rows = test_frame.count()
        print(f'      training days={training_rows}, test days={test_rows}')

        print('[2/9] Training and comparing three Spark ML models...')
        selected_name, _evaluation_model, comparisons, predictions = train_and_select(
            train_frame, test_frame
        )
        for item in comparisons:
            print(
                f"      {item['model_name']}: RMSE={item['rmse']:.2f}, "
                f"MAE={item['mae']:.2f}, R2={item['r2']:.4f}"
            )

        print(f'[3/9] Selected model: {selected_name}; refitting on all known days...')
        final_model = fit_selected_on_all_data(selected_name, daily_features)
        shutil.rmtree(ARTIFACT_DIR, ignore_errors=True)
        final_model.write().overwrite().save(str(ARTIFACT_DIR))

        print(f'[4/9] Forecasting the next {FORECAST_DAYS} days...')
        result_rows = test_prediction_rows(predictions)
        result_rows.extend(
            future_prediction_rows(spark, final_model, daily_features, FORECAST_DAYS)
        )

        print('[5/9] Creating VPP peak-shaving suggestions...')
        vpp_rows = build_vpp_recommendations(result_rows)

        print('[6/9] Calculating SOH reference scores and thermal risk...')
        clean_station_meta(spark)
        clean_monitoring(spark)
        health_rows = build_battery_health_rows(spark)

        print('[7/9] Finding inactive users and creating recall suggestions...')
        recall_rows = build_user_recall_rows(spark)

        print('[8/9] Creating preventive-maintenance suggestions...')
        maintenance_rows = build_maintenance_rows(health_rows)

        print('[9/9] Saving ML results to MySQL...')
        save_model_metrics(comparisons, selected_name, training_rows, test_rows)
        save_load_predictions(result_rows)
        save_vpp_recommendations(vpp_rows)
        save_battery_health(health_rows)
        save_user_recall(recall_rows)
        save_maintenance_recommendations(maintenance_rows)
        print(
            f'      saved {len(result_rows)} predictions, {len(vpp_rows)} VPP suggestions, '
            f'{len(health_rows)} battery-health rows, {len(recall_rows)} recall suggestions, '
            f'and {len(maintenance_rows)} maintenance suggestions'
        )
        print('Machine-learning analysis complete.')
    finally:
        spark.stop()


if __name__ == '__main__':
    train_load_forecast()
