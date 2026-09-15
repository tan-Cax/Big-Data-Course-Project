import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.vpp import build_vpp_recommendations


class VppRecommendationTests(unittest.TestCase):
    def test_peak_valley_and_normal_actions(self):
        values = [70, 90, 100, 100, 100, 110, 130]
        rows = [
            {
                'stat_date': date(2026, 1, index + 1),
                'data_type': 'future',
                'predicted_energy': value,
            }
            for index, value in enumerate(values)
        ]
        result = build_vpp_recommendations(rows)
        actions = {row['action'] for row in result}
        self.assertEqual(len(result), 7)
        self.assertEqual(actions, {'削峰', '填谷', '维持'})

    def test_ignores_test_predictions(self):
        result = build_vpp_recommendations([
            {'stat_date': date(2026, 1, 1), 'data_type': 'test', 'predicted_energy': 50}
        ])
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
