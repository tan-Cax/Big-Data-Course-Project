<template>
  <div class="panel">
    <div class="panel-title">星期×设施类型充电对比</div>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ data: { type: Array, default: () => [] } })
const chartRef = ref(null)
let chart = null

const COLORS = ['#40a0ff', '#36d399', '#a78bfa', '#f472b6']

function render() {
  if (!chart || !props.data.length) return
  const weekdays = [...new Set(props.data.map(d => d.weekday))].sort((a, b) => {
    const order = { Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6, Sun: 7 }
    return (order[a] || 0) - (order[b] || 0)
  })
  const facilities = [...new Set(props.data.map(d => d.facility_name))]
  const series = facilities.map((f, i) => ({
    name: f, type: 'bar', stack: 'total', barWidth: 24,
    data: weekdays.map(w => {
      const row = props.data.find(d => d.weekday === w && d.facility_name === f)
      return row ? row.total_energy : 0
    }),
    itemStyle: { color: COLORS[i % COLORS.length], borderRadius: i === facilities.length - 1 ? [4, 4, 0, 0] : 0 },
  }))
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: facilities, textStyle: { color: '#8a9bc0' }, top: 0 },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: weekdays, axisLabel: { color: '#8a9bc0' }, axisLine: { lineStyle: { color: '#2a3a5c' } } },
    yAxis: { type: 'value', name: 'kWh', axisLabel: { color: '#8a9bc0' }, splitLine: { lineStyle: { color: '#1a2a4c' } } },
    series,
  }, true)
}

onMounted(() => { chart = echarts.init(chartRef.value); render() })
onUnmounted(() => chart?.dispose())
watch(() => props.data, render, { deep: true })
window.addEventListener('resize', () => chart?.resize())
</script>

<style scoped>
.panel { background: rgba(16, 32, 64, 0.6); border: 1px solid rgba(64, 160, 255, 0.15); border-radius: 10px; padding: 16px; }
.panel-title { font-size: 14px; font-weight: 600; color: #e0e6ed; margin-bottom: 8px; }
.chart-container { width: 100%; height: 320px; }
</style>
