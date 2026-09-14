<template>
  <div class="panel">
    <div class="panel-title">站点充电量排名 TOP15</div>
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
  const top = props.data.slice(0, 15).reverse()
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 140, right: 60, top: 10, bottom: 10 },
    xAxis: { type: 'value', axisLabel: { color: '#8a9bc0' }, splitLine: { lineStyle: { color: '#1a2a4c' } } },
    yAxis: { type: 'category', data: top.map(d => (d.station_name || '').slice(0, 12)), axisLabel: { color: '#8a9bc0', fontSize: 11 }, axisLine: { lineStyle: { color: '#2a3a5c' } } },
    series: [{
      type: 'bar', data: top.map(d => d.total_energy),
      barWidth: 14,
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#2563eb' }, { offset: 1, color: '#40a0ff' }]),
      },
      label: { show: true, position: 'right', color: '#8a9bc0', fontSize: 11, formatter: '{c} kWh' },
    }],
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
