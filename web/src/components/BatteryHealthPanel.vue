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
    <div class="content-wrap">
      <div ref="chartRef" class="pie-container"></div>
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
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Object, default: () => ({ summary: {}, records: [] }) },
})
const summary = computed(() => props.data?.summary || {})
const records = computed(() => props.data?.records || [])
const chartRef = ref(null)
let chart = null

function riskLabel(level) { return ({ high: '高', medium: '中', low: '低' })[level] || level }
function formatRate(value) {
  return value === null || value === undefined ? '--' : `${Number(value).toFixed(2)} ℃/h`
}

const riskColors = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#10b981',
}

async function render() {
  await nextTick()
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const data = [
    { name: '高风险', value: summary.value.high || 0, itemStyle: { color: riskColors.high } },
    { name: '中风险', value: summary.value.medium || 0, itemStyle: { color: riskColors.medium } },
    { name: '低风险', value: summary.value.low || 0, itemStyle: { color: riskColors.low } },
  ]

  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      orient: 'vertical',
      left: 'center',
      bottom: 0,
      textStyle: { color: '#8a9bc0', fontSize: 12 },
    },
    series: [{
      name: '风险分布',
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '42%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: 'rgba(16, 32, 64, 0.6)', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#e0e6ed' },
      },
      data,
    }],
  }, true)
}

function resizeChart() { chart?.resize() }

onMounted(() => { render(); window.addEventListener('resize', resizeChart) })
onUnmounted(() => { window.removeEventListener('resize', resizeChart); chart?.dispose() })
watch(() => props.data, render, { deep: true })
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

/* 内容区：左饼图 + 右表格 */
.content-wrap {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
}
.pie-container {
  width: 100%;
  height: 260px;
}
.table-wrap { overflow-x: auto; }

table { width: 100%; border-collapse: collapse; font-size: 12px; }
th, td { padding: 9px 8px; text-align: left; border-bottom: 1px solid rgba(64, 160, 255, 0.12); }
th { color: #8a9bc0; font-weight: 500; }
td { color: #d5dcec; }

@media (max-width: 900px) {
  .content-wrap { grid-template-columns: 1fr; }
  .pie-container { height: 220px; }
}
@media (max-width: 768px) { .panel-header { flex-direction: column; } }
</style>
