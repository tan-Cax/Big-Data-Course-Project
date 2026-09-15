from statistics import median


def build_vpp_recommendations(prediction_rows):
    """Create explainable daily peak-shaving suggestions for the course demo."""
    future_rows = [row for row in prediction_rows if row['data_type'] == 'future']
    if not future_rows:
        return []

    baseline = median(row['predicted_energy'] for row in future_rows)
    high_threshold = baseline * 1.08
    low_threshold = baseline * 0.92
    recommendations = []

    for row in future_rows:
        energy = row['predicted_energy']
        if energy >= high_threshold:
            load_level = 'peak'
            action = '削峰'
            shift_energy = energy * 0.15
            reason = '预测负荷高于未来7天中位数8%，建议减少或转移15%的充电量。'
        elif energy <= low_threshold:
            load_level = 'valley'
            action = '填谷'
            shift_energy = energy * 0.10
            reason = '预测负荷低于未来7天中位数8%，建议引导约10%的充电量到该日。'
        else:
            load_level = 'normal'
            action = '维持'
            shift_energy = 0.0
            reason = '预测负荷处于正常区间，维持当前调度计划。'

        recommendations.append({
            'stat_date': row['stat_date'],
            'predicted_energy': round(energy, 2),
            'load_level': load_level,
            'action': action,
            'recommended_shift_energy': round(shift_energy, 2),
            'reason': reason,
        })

    return recommendations
