import unittest

from ml.churn import recall_recommendation
from ml.maintenance import build_maintenance_rows


class RecallRecommendationTests(unittest.TestCase):
    def test_recall_thresholds(self):
        self.assertEqual(recall_recommendation(29), (None, None))
        self.assertEqual(recall_recommendation(30)[0], '30_days')
        self.assertEqual(recall_recommendation(60)[0], '60_days')


class MaintenanceRecommendationTests(unittest.TestCase):
    def test_high_risk_sessions_create_priority_repair(self):
        rows = [
            {
                'station_id': 'S1', 'station_name': '测试站', 'risk_level': 'high',
                'max_temperature': 41, 'voltage_delta': 0.031,
            }
            for _ in range(3)
        ]
        result = build_maintenance_rows(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['priority'], 'high')
        self.assertLessEqual(result[0]['health_score'], 79)
        self.assertEqual(result[0]['high_risk_count'], 3)


if __name__ == '__main__':
    unittest.main()
