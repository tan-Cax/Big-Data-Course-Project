<template>
  <div class="operations-grid">
    <section class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">设备预防性运维建议</div>
          <div class="panel-subtitle">按异常监测记录汇总站点健康分，建议仅供运维人员参考</div>
        </div>
        <div class="summary"><span class="high">优先检修 {{ maintenanceSummary.high || 0 }}</span></div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>站点</th><th>健康分</th><th>高风险</th><th>优先级</th><th>建议</th></tr></thead>
          <tbody>
            <tr v-for="item in maintenance.slice(0, 10)" :key="item.station_id">
              <td>{{ item.station_name || item.station_id }}</td>
              <td :class="{ 'score-alert': item.health_score <= 60 }">{{ item.health_score }}</td>
              <td>{{ item.high_risk_count }}</td>
              <td><span class="badge" :class="item.priority">{{ priorityLabel(item.priority) }}</span></td>
              <td class="advice">{{ item.recommendation }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">流失用户预测与召回</div>
          <div class="panel-subtitle">以数据集最后一天为基准，自动识别30天和60天未充电用户</div>
        </div>
        <div class="summary">
          <span class="medium">30天 {{ recallSummary['30_days'] || 0 }}</span>
          <span class="high">60天 {{ recallSummary['60_days'] || 0 }}</span>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>用户</th><th>最后充电</th><th>未充电</th><th>历史订单</th><th>召回建议</th></tr></thead>
          <tbody>
            <tr v-for="item in recall.slice(0, 10)" :key="item.user_id">
              <td>{{ item.user_id }}</td><td>{{ item.last_charge_date }}</td>
              <td>{{ item.inactive_days }}天</td><td>{{ item.total_orders }}</td>
              <td class="advice">{{ item.recall_message }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ data: { type: Object, default: () => ({}) } })
const maintenance = computed(() => props.data?.maintenance || [])
const recall = computed(() => props.data?.recall || [])
const maintenanceSummary = computed(() => props.data?.summary?.maintenance || {})
const recallSummary = computed(() => props.data?.summary?.recall || {})
function priorityLabel(value) { return ({ high: '高', medium: '中', low: '低' })[value] || value }
</script>

<style scoped>
.operations-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.panel { min-width: 0; background: rgba(16, 32, 64, 0.6); border: 1px solid rgba(64, 160, 255, 0.15); border-radius: 10px; padding: 16px; }
.panel-header { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.panel-title { font-size: 14px; font-weight: 600; color: #e0e6ed; }
.panel-subtitle { margin-top: 5px; font-size: 12px; color: #8a9bc0; }
.summary { display: flex; gap: 6px; align-items: flex-start; white-space: nowrap; }
.summary span, .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.high, .score-alert { color: #fca5a5; background: rgba(248, 113, 113, 0.13); }
.medium { color: #fcd34d; background: rgba(245, 158, 11, 0.13); }
.low { color: #86efac; background: rgba(54, 211, 153, 0.13); }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th, td { padding: 9px 8px; text-align: left; border-bottom: 1px solid rgba(64, 160, 255, 0.12); }
th { color: #8a9bc0; font-weight: 500; }
td { color: #d5dcec; }
.advice { min-width: 190px; }
@media (max-width: 1000px) { .operations-grid { grid-template-columns: 1fr; } }
@media (max-width: 768px) { .panel-header { flex-direction: column; } }
</style>
