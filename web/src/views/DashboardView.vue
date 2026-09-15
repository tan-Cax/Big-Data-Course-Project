<template>
  <div class="dashboard">
    <OverviewCards :overview="data.overview" />

    <div class="chart-row">
      <DailyTrendChart :data="data.dailyTrend" />
      <StationRankChart :data="data.stationRanking" />
    </div>

    <div class="chart-row">
      <HourlyDistChart :data="data.hourlyDist" />
      <EfficiencyRadar :data="data.efficiency" />
    </div>

    <div class="chart-row">
      <WeekdayChart :data="data.weekdayDist" />
      <FacilityPieChart :data="data.facilityType" />
    </div>

    <div class="chart-row">
      <UserBubbleChart :data="data.userBehavior" />
      <PlatformGauge :data="data.platformDist" />
    </div>

    <div class="chart-row">
      <CrossHeatmap :data="data.hourlyStation" />
      <WeekdayFacilityChart :data="data.weekdayFacility" />
    </div>
  </div>
</template>

<script setup>
import OverviewCards from '../components/OverviewCards.vue'
import DailyTrendChart from '../components/DailyTrendChart.vue'
import StationRankChart from '../components/StationRankChart.vue'
import HourlyDistChart from '../components/HourlyDistChart.vue'
import WeekdayChart from '../components/WeekdayChart.vue'
import FacilityPieChart from '../components/FacilityPieChart.vue'
import UserBubbleChart from '../components/UserBubbleChart.vue'
import PlatformGauge from '../components/PlatformGauge.vue'
import EfficiencyRadar from '../components/EfficiencyRadar.vue'
import CrossHeatmap from '../components/CrossHeatmap.vue'
import WeekdayFacilityChart from '../components/WeekdayFacilityChart.vue'

defineProps({ data: { type: Object, default: () => ({}) } })
</script>

<style scoped>
.dashboard {
  padding: 12px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
/* A chart needs more horizontal room than an ordinary content card. */
@media (max-width: 1200px) {
  .chart-row { grid-template-columns: 1fr; }
  .dashboard { padding: 8px; }
}
</style>
