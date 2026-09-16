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

    <!-- 机器学习分区标题 -->
    <div class="section-title">
      <span class="section-line"></span>
      <span class="section-icon">⚡</span>
      <span class="section-text">机器学习智能分析</span>
      <span class="section-icon">⚡</span>
      <span class="section-line"></span>
    </div>

    <LoadPredictionChart :data="data.loadPrediction" />

    <div class="chart-row">
      <ModelComparisonChart :data="data.loadPrediction?.metrics" />
      <VppRecommendationTable :data="data.loadPrediction?.vpp" />
    </div>

    <BatteryHealthPanel :data="data.batteryHealth" />
    <OperationsIntelligencePanel :data="data.operations" />
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
import LoadPredictionChart from '../components/LoadPredictionChart.vue'
import ModelComparisonChart from '../components/ModelComparisonChart.vue'
import VppRecommendationTable from '../components/VppRecommendationTable.vue'
import BatteryHealthPanel from '../components/BatteryHealthPanel.vue'
import OperationsIntelligencePanel from '../components/OperationsIntelligencePanel.vue'

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

/* 机器学习分区标题 */
.section-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 8px 0 4px;
}
.section-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(to right, transparent, rgba(167, 139, 250, 0.4), transparent);
}
.section-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--purple);
  letter-spacing: 2px;
}
.section-icon {
  color: var(--purple);
  font-size: 14px;
  opacity: 0.8;
}
</style>
