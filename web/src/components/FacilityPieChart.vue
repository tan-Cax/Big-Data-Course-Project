<template>
  <div class="panel">
    <div class="panel-title">充电设施类型占比</div>
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
  const total = props.data.reduce((s, d) => s + d.total_energy, 0)
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} kWh ({d}%)' },
    legend: { orient: 'horizontal', left: 'center', bottom: 0, type: 'scroll', textStyle: { color: '#8a9bc0' } },
    series: [{
      type: 'pie', radius: ['35%', '58%'], center: ['50%', '45%'],
      data: props.data.map((d, i) => ({ name: d.facility_name, value: d.total_energy, itemStyle: { color: COLORS[i % COLORS.length] } })),
      label: { color: '#e0e6ed', formatter: '{b}\n{d}%' },
      labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' } },
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
