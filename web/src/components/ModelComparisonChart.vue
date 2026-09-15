<template>
  <div class="panel">
    <div class="panel-title">三种预测模型效果对比</div>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ data: { type: Array, default: () => [] } })
const chartRef = ref(null)
let chart = null

const labels = {
  linear_regression: '线性回归',
  random_forest: '随机森林',
  gradient_boosted_trees: '梯度提升树',
}

async function render() {
  await nextTick()
  if (!chartRef.value || !props.data.length) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(items) {
        const row = props.data[items[0]?.dataIndex]
        const lines = items.map(item => `${item.marker}${item.seriesName}：${Number(item.value).toFixed(2)}`)
        lines.push(`R²：${Number(row?.r2).toFixed(3)}`)
        return `${labels[row?.model_name] || row?.model_name}<br>${lines.join('<br>')}`
      },
    },
    legend: { data: ['RMSE', 'MAE'], textStyle: { color: '#8a9bc0' }, top: 0 },
    grid: { left: 88, right: 22, top: 42, bottom: 30 },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#8a9bc0' },
      splitLine: { lineStyle: { color: '#1a2a4c' } },
    },
    yAxis: {
      type: 'category',
      data: props.data.map(item => labels[item.model_name] || item.model_name),
      axisLabel: { color: '#8a9bc0' },
      axisLine: { lineStyle: { color: '#2a3a5c' } },
    },
    series: [
      { name: 'RMSE', type: 'bar', data: props.data.map(item => item.rmse), itemStyle: { color: '#40a0ff' } },
      { name: 'MAE', type: 'bar', data: props.data.map(item => item.mae), itemStyle: { color: '#a78bfa' } },
    ],
  }, true)
}

function resize() { chart?.resize() }
onMounted(() => { render(); window.addEventListener('resize', resize) })
onUnmounted(() => { window.removeEventListener('resize', resize); chart?.dispose() })
watch(() => props.data, render, { deep: true })
</script>

<style scoped>
.panel { background: rgba(16, 32, 64, 0.6); border: 1px solid rgba(64, 160, 255, 0.15); border-radius: 10px; padding: 16px; }
.panel-title { font-size: 14px; font-weight: 600; color: #e0e6ed; margin-bottom: 8px; }
.chart-container { width: 100%; height: 300px; }
</style>
