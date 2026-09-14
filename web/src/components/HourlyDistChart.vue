<template>
  <div class="panel">
    <div class="panel-title">24小时充电负荷分布</div>
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
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: props.data.map(d => d.hour_of_day + ':00'), axisLabel: { color: '#8a9bc0', fontSize: 10 }, axisLine: { lineStyle: { color: '#2a3a5c' } } },
    yAxis: [
      { type: 'value', name: 'kWh', axisLabel: { color: '#8a9bc0' }, splitLine: { lineStyle: { color: '#1a2a4c' } } },
      { type: 'value', name: '订单', axisLabel: { color: '#8a9bc0' }, splitLine: { show: false } },
    ],
    series: [
      {
        name: '充电量', type: 'bar', data: props.data.map(d => d.total_energy), barWidth: 16,
        itemStyle: { borderRadius: [4, 4, 0, 0], color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#40a0ff' }, { offset: 1, color: '#2563eb' }]) },
      },
      {
        name: '订单数', type: 'line', smooth: true, yAxisIndex: 1, data: props.data.map(d => d.total_orders),
        lineStyle: { color: '#f472b6' }, itemStyle: { color: '#f472b6' },
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
.chart-container { width: 100%; height: 320px; }
</style>
