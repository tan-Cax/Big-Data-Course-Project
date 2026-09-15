<template>
  <div class="panel">
    <div class="panel-title">每日充电量/营收趋势</div>
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
  const dates = props.data.map(d => (d.stat_date || '').slice(5))
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['充电量(kWh)', '营收(元)'], textStyle: { color: '#8a9bc0' }, top: 0 },
    grid: { left: 12, right: 12, top: 45, bottom: 55, containLabel: true },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 14, bottom: 4, borderColor: '#2a3a5c', textStyle: { color: '#8a9bc0' } }],
    xAxis: { type: 'category', data: dates, axisLabel: { color: '#8a9bc0', rotate: 35, fontSize: 10, hideOverlap: true }, axisLine: { lineStyle: { color: '#2a3a5c' } } },
    yAxis: [
      { type: 'value', name: 'kWh', axisLabel: { color: '#8a9bc0' }, splitLine: { lineStyle: { color: '#1a2a4c' } } },
      { type: 'value', name: '元', axisLabel: { color: '#8a9bc0' }, splitLine: { show: false } },
    ],
    series: [
      {
        name: '充电量(kWh)', type: 'line', smooth: true, data: props.data.map(d => d.total_energy),
        lineStyle: { color: '#40a0ff' }, itemStyle: { color: '#40a0ff' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(64,160,255,0.3)' }, { offset: 1, color: 'rgba(64,160,255,0.02)' }]) },
      },
      {
        name: '营收(元)', type: 'line', smooth: true, yAxisIndex: 1, data: props.data.map(d => d.total_revenue),
        lineStyle: { color: '#f59e0b' }, itemStyle: { color: '#f59e0b' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(245,158,11,0.2)' }, { offset: 1, color: 'rgba(245,158,11,0.02)' }]) },
      },
    ],
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
