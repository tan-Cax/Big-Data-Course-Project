<!--
  NCS 充电桩数据分析平台 - 根组件
  
  本组件是 Vue 应用的根组件，包含：
  1. 顶部导航栏：显示应用标题、最后更新时间、重新分析按钮、训练模型按钮
  2. 仪表板视图：展示所有图表和数据卡片
  
  组件结构：
  - App (根组件)
    - Header (顶部导航栏)
    - DashboardView (仪表板视图)
-->
<template>
  <div class="app">
    <!-- 顶部导航栏 -->
    <header class="top-bar">
      <h1 class="app-title">NCS 充电桩数据分析大屏</h1>
      <div class="top-bar-info">
        <!-- 显示最后更新时间 -->
        <span class="update-time" v-if="lastUpdate">更新: {{ lastUpdate }}</span>
        <!-- 重新分析按钮 -->
        <button class="reload-btn" @click="reload" :disabled="loading">
          {{ loading ? '分析中...' : '重新分析' }}
        </button>
        <!-- 训练模型按钮 -->
        <button class="train-btn" @click="trainModel" :disabled="loading">
          {{ loading ? '训练中...' : '训练模型' }}
        </button>
      </div>
    </header>
    <!-- 仪表板视图，传递所有数据 -->
    <DashboardView :data="data" />
  </div>
</template>

<script setup>
import { useApi } from './composables/useApi.js'
import DashboardView from './views/DashboardView.vue'

// 使用 REST API composable 获取数据
const { data, loading, lastUpdate, reload, trainModel } = useApi()
</script>
