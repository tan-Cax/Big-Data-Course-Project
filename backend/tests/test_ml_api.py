import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


class MachineLearningApiTests(unittest.TestCase):
    @patch('app.ensure_ml_tables')
    @patch('app.db.query_all')
    def test_load_prediction_response_shape(self, query_all, ensure_tables):
        query_all.side_effect = [
            [{'model_name': 'random_forest', 'is_selected': 1, 'rmse': 12.3}],
            [{'stat_date': '2015-10-05', 'data_type': 'future', 'predicted_energy': 80.0}],
            [{'stat_date': '2015-10-05', 'action': '削峰'}],
        ]
        with app.test_client() as client:
            response = client.get('/api/prediction/load')

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['code'], 0)
        self.assertEqual(len(payload['data']['metrics']), 1)
        self.assertEqual(len(payload['data']['predictions']), 1)
        self.assertEqual(len(payload['data']['vpp']), 1)
        ensure_tables.assert_called_once_with()

    @patch('app.ensure_ml_tables')
    @patch('app.db.query_all')
    def test_battery_health_response_shape(self, query_all, ensure_tables):
        query_all.side_effect = [
            [{'session_id': '1001', 'soh_reference': 86.0, 'risk_level': 'low'}],
            [{'risk_level': 'low', 'total': 1}],
        ]
        with app.test_client() as client:
            response = client.get('/api/prediction/battery-health')

        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['data']['summary']['low'], 1)
        self.assertEqual(len(payload['data']['records']), 1)
        ensure_tables.assert_called_once_with()

    @patch('app.ensure_ml_tables')
    @patch('app.db.query_all')
    def test_operations_response_shape(self, query_all, ensure_tables):
        query_all.side_effect = [
            [{'station_id': 'S1', 'health_score': 58, 'priority': 'high'}],
            [{'user_id': 'U1', 'inactive_days': 60, 'recall_level': '60_days'}],
            [{'priority': 'high', 'total': 1}],
            [{'recall_level': '60_days', 'total': 1}],
        ]
        with app.test_client() as client:
            response = client.get('/api/prediction/operations')

        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['data']['summary']['maintenance']['high'], 1)
        self.assertEqual(payload['data']['summary']['recall']['60_days'], 1)
        self.assertEqual(len(payload['data']['maintenance']), 1)
        self.assertEqual(len(payload['data']['recall']), 1)
        ensure_tables.assert_called_once_with()

    def test_training_route_is_registered_as_post(self):
        rules = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}
        self.assertIn('POST', rules['/api/prediction/train'])


if __name__ == '__main__':
    unittest.main()
