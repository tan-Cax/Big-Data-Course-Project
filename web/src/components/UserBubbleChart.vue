<template>
  <div class="panel">
    <div class="panel-title">用户充电行为分布</div>
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
  const scatter = props.data.map(d => [d.total_orders, d.total_energy, d.avg_energy_per_order, d.user_id])
  chart.setOption({
    tooltip: {
      formatter: p => `订单数: ${p.data[0]}<br/>总电量: ${p.data[1]} kWh<br/>均电量: ${p.data[2]} kWh`
    },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { name: '订单数', type: 'value', axisLabel: { color: '#8a9bc0' }, splitLine: { lineStyle: { color: '#1a2a4c' } } },
    yAxis: { name: '总充电量(kWh)', type: 'value', axisLabel: { color: '#8a9bc0' }, splitLine: { lineStyle: { color: '#1a2a4c' } } },
    series: [{
      type: 'scatter', symbolSize: d => Math.max(8, Math.min(30, d[2] * 3)),
      data: scatter,
      itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [{ offset: 0, color: '#a78bfa' }, { offset: 1, color: '#f472b6' }]), opacity: 0.8 },
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
