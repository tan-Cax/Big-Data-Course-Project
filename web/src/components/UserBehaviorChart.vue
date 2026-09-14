<template>
  <div class="panel">
    <div ref="chartRef" style="width:100%;height:340px"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ data: { type: Array, default: () => [] } })
const chartRef = ref(null)
let chart = null

function render() {
  if (!chart || !chartRef.value) return
  if (!props.data.length) {
    chart.setOption({ title: { text: '用户行为分析（暂无数据）', left: 'center', textStyle: { fontSize: 15, color: '#8896ab' } } }, true)
    return
  }

  // 统计各时段用户数
  const hourMap = {}
  props.data.forEach(v => {
    const h = v.preferredHour
    if (h >= 0) {
      const label = `${h}:00`
      hourMap[label] = (hourMap[label] || 0) + 1
    }
  })
  const sorted = Object.entries(hourMap).sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
  const hours = sorted.map(v => v[0])
  const counts = sorted.map(v => v[1])

  chart.setOption({
    title: { text: '用户偏好充电时段分布', left: 'center', textStyle: { fontSize: 15, fontWeight: 600, color: '#344158' } },
    tooltip: { trigger: 'axis', formatter: (p) => `${p[0].name}<br/>用户数: ${p[0].value}` },
    grid: { top: 50, bottom: 30, left: 50, right: 20 },
    xAxis: { type: 'category', data: hours, axisLabel: { color: '#8896ab', interval: 0, rotate: hours.length > 12 ? 45 : 0 } },
    yAxis: { type: 'value', axisLabel: { color: '#8896ab' }, splitLine: { lineStyle: { color: '#f0f3f8' } } },
    series: [{
      type: 'bar', data: counts, barWidth: '60%',
      itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: '#e86448' }, { offset: 1, color: '#c84848' }
      ]), borderRadius: [6, 6, 0, 0] }
    }]
  }, true)
}

onMounted(() => {
  chart = echarts.init(chartRef.value)
  render()
  window.addEventListener('resize', () => chart?.resize())
})
onUnmounted(() => { chart?.dispose() })
watch(() => props.data, render, { deep: true })
</script>
