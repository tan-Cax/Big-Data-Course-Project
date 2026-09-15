from collections import defaultdict


def build_maintenance_rows(health_rows):
    """Aggregate session risks into explainable station maintenance advice."""
    stations = defaultdict(lambda: {
        'station_name': None,
        'total_sessions': 0,
        'high_risk_count': 0,
        'medium_risk_count': 0,
        'overtemp_count': 0,
        'voltage_abnormal_count': 0,
    })

    for item in health_rows:
        station_id = item.get('station_id')
        if not station_id:
            continue
        station = stations[str(station_id)]
        station['station_name'] = item.get('station_name') or station['station_name']
        station['total_sessions'] += 1
        station['high_risk_count'] += item.get('risk_level') == 'high'
        station['medium_risk_count'] += item.get('risk_level') == 'medium'
        station['overtemp_count'] += (item.get('max_temperature') or 0) >= 40
        station['voltage_abnormal_count'] += (item.get('voltage_delta') or 0) >= 0.030

    results = []
    for station_id, item in stations.items():
        score = max(0, min(100, 100
            - item['high_risk_count'] * 5
            - item['medium_risk_count'] * 2
            - item['overtemp_count'] * 2
            - item['voltage_abnormal_count'] * 2))

        if score <= 60 or item['high_risk_count'] >= 3:
            priority = 'high'
            recommendation = '建议优先检修：检查电池连接、温控系统及电压采集模块'
        elif score <= 80 or item['high_risk_count'] > 0:
            priority = 'medium'
            recommendation = '建议安排巡检：复测高温与电芯压差异常记录'
        else:
            priority = 'low'
            recommendation = '设备状态正常，按原计划进行例行维护'

        results.append({
            'station_id': station_id,
            'station_name': item['station_name'],
            'health_score': score,
            **{key: item[key] for key in (
                'total_sessions', 'high_risk_count', 'medium_risk_count',
                'overtemp_count', 'voltage_abnormal_count',
            )},
            'priority': priority,
            'recommendation': recommendation,
        })

    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    return sorted(results, key=lambda row: (priority_order[row['priority']], row['health_score']))
