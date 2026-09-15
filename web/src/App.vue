<template>
  <div class="app">
    <header class="top-bar">
      <h1 class="app-title">NCS 充电桩数据分析大屏</h1>
      <div class="top-bar-info">
        <span class="update-time" v-if="lastUpdate">更新: {{ lastUpdate }}</span>
        <button class="reload-btn" @click="reload" :disabled="loading">
          {{ loading ? '分析中...' : '重新分析' }}
        </button>
      </div>
    </header>
    <DashboardView :data="data" />
  </div>
</template>

<script setup>
import { useApi } from './composables/useApi.js'
import DashboardView from './views/DashboardView.vue'

const { data, loading, lastUpdate, reload } = useApi()
</script>
