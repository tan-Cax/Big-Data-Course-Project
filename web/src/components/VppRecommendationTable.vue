<template>
  <div class="panel">
    <div class="panel-title">VPP 削峰填谷建议</div>
    <div class="panel-subtitle">基于未来7天预测负荷生成，不连接真实电网控制接口</div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>日期</th><th>预测电量</th><th>建议</th><th>调整电量</th></tr></thead>
        <tbody>
          <tr v-for="item in data" :key="item.stat_date">
            <td>{{ item.stat_date }}</td>
            <td>{{ Number(item.predicted_energy).toFixed(2) }} kWh</td>
            <td><span class="badge" :class="item.load_level">{{ item.action }}</span></td>
            <td>{{ Number(item.recommended_shift_energy).toFixed(2) }} kWh</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({ data: { type: Array, default: () => [] } })
</script>

<style scoped>
.panel { background: rgba(16, 32, 64, 0.6); border: 1px solid rgba(64, 160, 255, 0.15); border-radius: 10px; padding: 16px; }
.panel-title { font-size: 14px; font-weight: 600; color: #e0e6ed; }
.panel-subtitle { margin: 5px 0 12px; font-size: 12px; color: #8a9bc0; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th, td { padding: 9px 8px; text-align: left; border-bottom: 1px solid rgba(64, 160, 255, 0.12); }
th { color: #8a9bc0; font-weight: 500; }
td { color: #d5dcec; }
.badge { display: inline-block; min-width: 42px; padding: 3px 7px; border-radius: 4px; text-align: center; }
.peak { color: #fca5a5; background: rgba(248, 113, 113, 0.13); }
.valley { color: #86efac; background: rgba(54, 211, 153, 0.13); }
.normal { color: #93c5fd; background: rgba(64, 160, 255, 0.13); }
</style>
