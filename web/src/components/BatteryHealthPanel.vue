<template>
  <div class="panel">
    <div class="panel-header">
      <div>
        <div class="panel-title">电池 SOH 参考与热风险预警</div>
        <div class="panel-subtitle">基于电压差、最高温度和温升速率计算，仅作保养参考</div>
      </div>
      <div class="summary">
        <span class="high">高风险 {{ summary.high || 0 }}</span>
        <span class="medium">中风险 {{ summary.medium || 0 }}</span>
        <span class="low">低风险 {{ summary.low || 0 }}</span>
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>会话</th><th>站点</th><th>SOH参考分</th><th>电压差</th><th>最高温度</th><th>温升速率</th><th>风险</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in records.slice(0, 15)" :key="item.session_id">
            <td>{{ item.session_id }}</td>
            <td>{{ item.station_name || item.station_id || '--' }}</td>
            <td>{{ Number(item.soh_reference).toFixed(1) }}</td>
            <td>{{ Number(item.voltage_delta).toFixed(4) }} V</td>
            <td>{{ Number(item.max_temperature).toFixed(1) }} ℃</td>
            <td>{{ formatRate(item.temperature_rise_rate) }}</td>
            <td><span class="badge" :class="item.risk_level">{{ riskLabel(item.risk_level) }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Object, default: () => ({ summary: {}, records: [] }) },
})
const summary = computed(() => props.data?.summary || {})
const records = computed(() => props.data?.records || [])
function riskLabel(level) { return ({ high: '高', medium: '中', low: '低' })[level] || level }
function formatRate(value) {
  return value === null || value === undefined ? '--' : `${Number(value).toFixed(2)} ℃/h`
}
</script>

<style scoped>
.panel { background: rgba(16, 32, 64, 0.6); border: 1px solid rgba(64, 160, 255, 0.15); border-radius: 10px; padding: 16px; }
.panel-header { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 12px; }
.panel-title { font-size: 14px; font-weight: 600; color: #e0e6ed; }
.panel-subtitle { margin-top: 5px; font-size: 12px; color: #8a9bc0; }
.summary { display: flex; gap: 8px; flex-wrap: wrap; }
.summary span, .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.high { color: #fca5a5; background: rgba(248, 113, 113, 0.13); }
.medium { color: #fcd34d; background: rgba(245, 158, 11, 0.13); }
.low { color: #86efac; background: rgba(54, 211, 153, 0.13); }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th, td { padding: 9px 8px; text-align: left; border-bottom: 1px solid rgba(64, 160, 255, 0.12); }
th { color: #8a9bc0; font-weight: 500; }
td { color: #d5dcec; }
@media (max-width: 768px) { .panel-header { flex-direction: column; } }
</style>
