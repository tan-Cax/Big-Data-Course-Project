<template>
  <div class="panel">
    <div class="panel-title">工作日 vs 周末充电对比</div>
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
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['充电量(kWh)', '订单数', '营收(元)'], textStyle: { color: '#8a9bc0' }, top: 0 },
    grid: { left: 12, right: 12, top: 45, bottom: 12, containLabel: true },
    xAxis: { type: 'category', data: props.data.map(d => d.weekday), axisLabel: { color: '#8a9bc0' }, axisLine: { lineStyle: { color: '#2a3a5c' } } },
    yAxis: [
      { type: 'value', axisLabel: { color: '#8a9bc0' }, splitLine: { lineStyle: { color: '#1a2a4c' } } },
      { type: 'value', axisLabel: { color: '#8a9bc0' }, splitLine: { show: false } },
    ],
    series: [
      { name: '充电量(kWh)', type: 'bar', data: props.data.map(d => d.total_energy), barWidth: 20, itemStyle: { borderRadius: [4, 4, 0, 0], color: '#40a0ff' } },
      { name: '订单数', type: 'bar', data: props.data.map(d => d.total_orders), barWidth: 20, itemStyle: { borderRadius: [4, 4, 0, 0], color: '#36d399' } },
      { name: '营收(元)', type: 'line', smooth: true, yAxisIndex: 1, data: props.data.map(d => d.total_revenue), lineStyle: { color: '#f59e0b' }, itemStyle: { color: '#f59e0b' } },
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
.chart-container { width: 100%; height: 320px; }
</style>
