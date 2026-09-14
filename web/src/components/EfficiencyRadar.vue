<template>
  <div class="panel">
    <div class="panel-title">充电效率分析 TOP10</div>
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
  const top = props.data.slice(0, 10)
  const indicators = [
    { name: '平均电压(V)', max: 400 },
    { name: '平均电流(A)', max: 40 },
    { name: '平均电量(kWh)', max: 15 },
    { name: '平均时长(h)', max: 6 },
    { name: '平均SOC(%)', max: 100 },
  ]
  const series = top.map((d, i) => ({
    name: (d.station_name || '').slice(0, 8),
    value: [d.avg_voltage, d.avg_current, d.avg_energy, d.avg_duration, d.avg_soc],
    lineStyle: { width: 1.5 },
    areaStyle: { opacity: 0.1 },
  }))
  chart.setOption({
    tooltip: {},
    legend: { data: top.map(d => (d.station_name || '').slice(0, 8)), textStyle: { color: '#8a9bc0', fontSize: 10 }, top: 0, type: 'scroll' },
    radar: { indicator: indicators, shape: 'polygon', axisName: { color: '#8a9bc0', fontSize: 11 }, splitArea: { areaStyle: { color: ['rgba(64,160,255,0.02)', 'rgba(64,160,255,0.05)'] } }, splitLine: { lineStyle: { color: '#1a2a4c' } }, axisLine: { lineStyle: { color: '#1a2a4c' } } },
    series: [{ type: 'radar', data: series }],
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
