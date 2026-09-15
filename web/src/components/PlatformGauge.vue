<template>
  <div class="panel">
    <div class="panel-title">平台分布</div>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ data: { type: Array, default: () => [] } })
const chartRef = ref(null)
let chart = null

const COLORS = { android: '#36d399', ios: '#40a0ff', web: '#f59e0b' }

function render() {
  if (!chart || !props.data.length) return
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 10, textStyle: { color: '#8a9bc0' } },
    series: [{
      type: 'pie', radius: ['35%', '60%'], center: ['50%', '45%'],
      data: props.data.map(d => ({
        name: d.platform,
        value: d.total_orders,
        itemStyle: { color: COLORS[d.platform] || '#888' },
      })),
      label: { color: '#e0e6ed', formatter: '{b}\n{c}单 ({d}%)' },
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
