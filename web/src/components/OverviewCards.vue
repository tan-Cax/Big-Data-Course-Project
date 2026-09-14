<template>
  <div class="card-row">
    <div class="data-card" v-for="card in cards" :key="card.label">
      <div class="card-icon" :style="{ background: card.color }">
        <span>{{ card.icon }}</span>
      </div>
      <div class="card-info">
        <div class="card-label">{{ card.label }}</div>
        <div class="card-value" :style="{ color: card.color }">
          {{ card.prefix }}{{ formatNum(card.value) }}{{ card.suffix }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ overview: { type: Object, default: () => ({}) } })

const cards = computed(() => [
  { label: '总订单数', value: props.overview.total_orders || 0, icon: '#', color: '#40a0ff', prefix: '', suffix: '' },
  { label: '总充电量', value: props.overview.total_energy || 0, icon: '#', color: '#36d399', prefix: '', suffix: ' kWh' },
  { label: '总营收', value: props.overview.total_revenue || 0, icon: '#', color: '#f59e0b', prefix: '¥', suffix: '' },
  { label: '充电站点', value: props.overview.station_count || 0, icon: '#', color: '#a78bfa', prefix: '', suffix: '' },
  { label: '活跃用户', value: props.overview.user_count || 0, icon: '#', color: '#f472b6', prefix: '', suffix: '' },
])

function formatNum(v) {
  if (typeof v !== 'number') return v
  if (v >= 10000) return (v / 10000).toFixed(1) + '万'
  if (v % 1 === 0) return v.toLocaleString()
  return v.toFixed(2)
}
</script>

<style scoped>
.card-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}
.data-card {
  background: rgba(16, 32, 64, 0.6);
  border: 1px solid rgba(64, 160, 255, 0.15);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.card-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #fff;
  opacity: 0.85;
  flex-shrink: 0;
}
.card-label {
  font-size: 12px;
  color: #8a9bc0;
  margin-bottom: 4px;
}
.card-value {
  font-size: 22px;
  font-weight: 700;
  font-family: 'Rajdhani', 'Orbitron', monospace;
}
@media (max-width: 1200px) { .card-row { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 768px) { .card-row { grid-template-columns: repeat(2, 1fr); } }
</style>
