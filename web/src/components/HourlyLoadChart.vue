<template>
  <div class="panel">
    <div ref="chartRef" style="width:100%;height:380px"></div>
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
    chart.setOption({ title: { text: '充电负荷时序分析（暂无数据）', left: 'center', textStyle: { fontSize: 15, color: '#8896ab' } } }, true)
    return
  }

  const hours = [...new Set(props.data.map(v => v.hour))].sort()
  const stations = [...new Set(props.data.map(v => v.stationName))]
  const heatData = []
  props.data.forEach(v => {
    const x = hours.indexOf(v.hour)
    const y = stations.indexOf(v.stationName)
    if (x >= 0 && y >= 0) heatData.push([x, y, v.totalEnergy || 0])
  })

  chart.setOption({
    title: { text: '充电负荷时序热力图', left: 'center', textStyle: { fontSize: 15, fontWeight: 600, color: '#344158' } },
    tooltip: { formatter: (p) => `${stations[p.value[1]]} ${hours[p.value[0]]}<br/>充电量: ${p.value[2].toFixed(1)} kWh` },
    grid: { top: 50, bottom: 60, left: 120, right: 40 },
    xAxis: { type: 'category', data: hours, axisLabel: { color: '#8896ab' }, splitArea: { show: true } },
    yAxis: { type: 'category', data: stations, axisLabel: { color: '#8896ab', fontSize: 11 }, splitArea: { show: true } },
    visualMap: { min: 0, max: Math.max(10, ...heatData.map(v => v[2])), calculable: true, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: ['#f0f3f8', '#4878e8', '#e86448'] } },
    series: [{ type: 'heatmap', data: heatData, label: { show: false } }]
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
