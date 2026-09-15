<template>
  <div class="panel">
    <div class="panel-title">时段×站点充电热力图</div>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ data: { type: Array, default: () => [] } })
const chartRef = ref(null)
let chart = null

function render() {
  if (!chart || !props.data.length) return
  const stationMap = {}
  props.data.forEach(d => { stationMap[d.station_id] = d.station_name })
  const stations = Object.entries(stationMap).slice(0, 15).map(([id, name]) => ({ id, name: name || '' }))
  const hours = [...new Set(props.data.map(d => d.hour_of_day))].sort((a, b) => a - b)
  const heatData = []
  let maxVal = 0
  props.data.forEach(d => {
    const si = stations.findIndex(s => s.id === d.station_id)
    if (si < 0) return
    const hi = hours.indexOf(d.hour_of_day)
    if (hi < 0) return
    heatData.push([hi, si, d.total_energy])
    if (d.total_energy > maxVal) maxVal = d.total_energy
  })
  chart.setOption({
    tooltip: { formatter: p => `${stations[p.data[1]]?.name} ${hours[p.data[0]]}:00<br/>充电量: ${p.data[2]} kWh` },
    grid: { left: 12, right: 75, top: 12, bottom: 12, containLabel: true },
    xAxis: { type: 'category', data: hours.map(h => h + ':00'), axisLabel: { color: '#8a9bc0', fontSize: 10, interval: 1, rotate: 35, hideOverlap: true }, axisLine: { lineStyle: { color: '#2a3a5c' } } },
    yAxis: { type: 'category', data: stations.map(s => s.name), axisLabel: { color: '#8a9bc0', fontSize: 10, width: 190, overflow: 'truncate' }, axisLine: { lineStyle: { color: '#2a3a5c' } } },
    visualMap: { min: 0, max: maxVal || 100, calculable: true, orient: 'vertical', right: 0, top: 'center', inRange: { color: ['#0f1729', '#1a3a6c', '#2563eb', '#40a0ff', '#f59e0b', '#ef4444'] }, textStyle: { color: '#8a9bc0' } },
    series: [{ type: 'heatmap', data: heatData, emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } } }],
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
.chart-container { width: 100%; height: 480px; }
</style>
