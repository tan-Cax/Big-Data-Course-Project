from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import GBTRegressor, LinearRegression, RandomForestRegressor

from ml.config import FEATURE_COLUMNS, RANDOM_SEED


def assemble_features(frame):
    assembler = VectorAssembler(
        inputCols=FEATURE_COLUMNS,
        outputCol='features',
        handleInvalid='skip',
    )
    return assembler.transform(frame)


def candidate_estimators():
    return {
        'linear_regression': LinearRegression(
            featuresCol='features', labelCol='label', maxIter=100, regParam=0.1
        ),
        'random_forest': RandomForestRegressor(
            featuresCol='features', labelCol='label', numTrees=80,
            maxDepth=6, seed=RANDOM_SEED,
        ),
        'gradient_boosted_trees': GBTRegressor(
            featuresCol='features', labelCol='label', maxIter=60,
            maxDepth=5, stepSize=0.05, seed=RANDOM_SEED,
        ),
    }


def evaluate_predictions(predictions):
    result = {}
    for metric_name in ('rmse', 'mae', 'r2'):
        evaluator = RegressionEvaluator(
            labelCol='label', predictionCol='prediction', metricName=metric_name
        )
        result[metric_name] = float(evaluator.evaluate(predictions))
    return result


def train_and_select(train_frame, test_frame):
    train_vectors = assemble_features(train_frame).cache()
    test_vectors = assemble_features(test_frame).cache()
    comparisons = []
    trained_models = {}

    for model_name, estimator in candidate_estimators().items():
        model = estimator.fit(train_vectors)
        predictions = model.transform(test_vectors)
        metrics = evaluate_predictions(predictions)
        comparisons.append({'model_name': model_name, **metrics})
        trained_models[model_name] = model

    comparisons.sort(key=lambda item: item['rmse'])
    selected_name = comparisons[0]['model_name']
    selected_model = trained_models[selected_name]
    selected_predictions = selected_model.transform(test_vectors)
    return selected_name, selected_model, comparisons, selected_predictions


def fit_selected_on_all_data(model_name, feature_frame):
    """Retrain the chosen algorithm on all known dates before future forecasting."""
    estimator = candidate_estimators()[model_name]
    return estimator.fit(assemble_features(feature_frame))
