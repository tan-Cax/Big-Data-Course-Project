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
    chart.setOption({ title: { text: '站点利用率分析（暂无数据）', left: 'center', textStyle: { fontSize: 15, color: '#8896ab' } } }, true)
    return
  }

  // 取最新一天的数据
  const latestDate = props.data[0]?.date || ''
  const latest = props.data.filter(v => v.date === latestDate)
  const names = latest.map(v => (v.stationName || '').slice(0, 10))
  const rates = latest.map(v => ((v.utilizationRate || 0) * 100).toFixed(1))

  chart.setOption({
    title: { text: `站点利用率排名 (${latestDate})`, left: 'center', textStyle: { fontSize: 15, fontWeight: 600, color: '#344158' } },
    tooltip: { trigger: 'axis', formatter: (p) => `${p[0].name}<br/>利用率: ${p[0].value}%` },
    grid: { top: 50, bottom: 30, left: 120, right: 40 },
    yAxis: { type: 'category', data: names.reverse(), axisLabel: { color: '#8896ab', fontSize: 11 } },
    xAxis: { type: 'value', max: 100, axisLabel: { color: '#8896ab', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#f0f3f8' } } },
    series: [{
      type: 'bar', data: rates.reverse(), barWidth: '60%',
      itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
        { offset: 0, color: '#3B5FC0' }, { offset: 1, color: '#5D84E8' }
      ]), borderRadius: [0, 6, 6, 0] },
      label: { show: true, position: 'right', formatter: '{c}%', fontSize: 11, color: '#8896ab' }
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
