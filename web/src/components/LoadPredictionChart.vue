<template>
  <div class="panel prediction-panel">
    <div class="panel-header">
      <div>
        <div class="panel-title">机器学习 · 每日充电负荷预测</div>
        <div class="panel-subtitle">三种 Spark ML 模型自动比较，虚线部分为未来7天预测</div>
      </div>
      <div v-if="selectedMetric" class="metric-list">
        <span>最佳模型：{{ modelLabel(selectedMetric.model_name) }}</span>
        <span>RMSE：{{ formatMetric(selectedMetric.rmse) }}</span>
        <span>MAE：{{ formatMetric(selectedMetric.mae) }}</span>
        <span>R²：{{ formatMetric(selectedMetric.r2, 3) }}</span>
      </div>
    </div>
    <div v-if="!predictions.length" class="empty-state">
      暂无预测结果，请先运行后端机器学习训练脚本。
    </div>
    <div v-else ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({ metrics: [], predictions: [] }),
  },
})

const chartRef = ref(null)
let chart = null

const metrics = computed(() => props.data?.metrics || [])
const predictions = computed(() => props.data?.predictions || [])
const selectedMetric = computed(
  () => metrics.value.find(item => Number(item.is_selected) === 1) || metrics.value[0]
)

const labels = {
  linear_regression: '线性回归',
  random_forest: '随机森林',
  gradient_boosted_trees: '梯度提升树',
}

function modelLabel(name) {
  return labels[name] || name || '--'
}

function formatMetric(value, digits = 2) {
  const number = Number(value)
  return Number.isFinite(number) ? number.toFixed(digits) : '--'
}

async function render() {
  if (!predictions.value.length) {
    chart?.dispose()
    chart = null
    return
  }

  await nextTick()
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const rows = predictions.value
  const dates = rows.map(item => formatDate(item.stat_date))
  const firstFutureIndex = rows.findIndex(item => item.data_type === 'future')
  const firstFuture = firstFutureIndex >= 0 ? dates[firstFutureIndex] : null
  const labelInterval = Math.max(0, Math.ceil(dates.length / 12) - 1)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['实际充电量', '模型预测值'],
      textStyle: { color: '#8a9bc0' },
      top: 0,
    },
    grid: { left: 58, right: 24, top: 42, bottom: 42 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { color: '#8a9bc0', interval: labelInterval, rotate: dates.length > 20 ? 30 : 0, fontSize: 10 },
      axisLine: { lineStyle: { color: '#2a3a5c' } },
    },
    yAxis: {
      type: 'value',
      name: 'kWh',
      axisLabel: { color: '#8a9bc0' },
      splitLine: { lineStyle: { color: '#1a2a4c' } },
    },
    series: [
      {
        name: '实际充电量',
        type: 'line',
        data: rows.map(item => item.actual_energy),
        symbolSize: 5,
        lineStyle: { color: '#40a0ff', width: 2 },
        itemStyle: { color: '#40a0ff' },
      },
      {
        name: '模型预测值',
        type: 'line',
        data: rows.map(item => item.predicted_energy),
        symbolSize: 5,
        lineStyle: { color: '#36d399', width: 2, type: 'dashed' },
        itemStyle: { color: '#36d399' },
        markArea: firstFuture ? {
          silent: true,
          itemStyle: { color: 'rgba(54, 211, 153, 0.07)' },
          label: { color: '#36d399', formatter: '未来预测' },
          data: [[{ xAxis: firstFuture }, { xAxis: dates.at(-1) }]],
        } : undefined,
      },
    ],
  }, true)
}

function formatDate(value) {
  const text = String(value || '')
  const isoMatch = text.match(/^\d{4}-(\d{2})-(\d{2})/)
  if (isoMatch) return `${isoMatch[1]}-${isoMatch[2]}`
  const parsed = new Date(text)
  if (!Number.isNaN(parsed.getTime())) {
    return `${String(parsed.getMonth() + 1).padStart(2, '0')}-${String(parsed.getDate()).padStart(2, '0')}`
  }
  return text
}

function resizeChart() {
  chart?.resize()
}

onMounted(() => {
  render()
  window.addEventListener('resize', resizeChart)
})
onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  chart?.dispose()
})
watch(() => props.data, render, { deep: true })
</script>

<style scoped>
.panel {
  background: rgba(16, 32, 64, 0.6);
  border: 1px solid rgba(64, 160, 255, 0.15);
  border-radius: 10px;
  padding: 16px;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}
.panel-title { font-size: 14px; font-weight: 600; color: #e0e6ed; }
.panel-subtitle { margin-top: 5px; font-size: 12px; color: #8a9bc0; }
.metric-list { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.metric-list span {
  padding: 4px 8px;
  color: #b9f6df;
  background: rgba(54, 211, 153, 0.1);
  border: 1px solid rgba(54, 211, 153, 0.25);
  border-radius: 4px;
  font-size: 12px;
}
.chart-container { width: 100%; height: 360px; margin-top: 8px; }
.empty-state { padding: 70px 20px; color: #8a9bc0; text-align: center; }
@media (max-width: 768px) {
  .panel-header { flex-direction: column; }
  .metric-list { justify-content: flex-start; }
}
</style>
