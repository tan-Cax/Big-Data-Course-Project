import { ref, onMounted, onUnmounted } from 'vue'

const API_BASE = 'http://127.0.0.1:5000'

export function useApi() {
  const data = ref({
    overview: {},
    dailyTrend: [],
    stationRanking: [],
    stationUtilization: [],
    hourlyDist: [],
    weekdayDist: [],
    facilityType: [],
    userBehavior: [],
    platformDist: [],
    efficiency: [],
    hourlyStation: [],
    weekdayFacility: [],
    loadPrediction: { metrics: [], predictions: [] },
    batteryHealth: { summary: {}, records: [] },
    operations: { maintenance: [], recall: [], summary: {} },
  })
  const loading = ref(false)
  const lastUpdate = ref('')
  let timer = null

  async function fetchJson(url) {
    try {
      const res = await fetch(`${API_BASE}${url}`)
      const json = await res.json()
      if (json.code === 0) return json.data
    } catch (e) {
      console.warn(`API ${url} failed:`, e.message)
    }
    return null
  }

  async function fetchAll() {
    loading.value = true
    const [overview, dailyTrend, stationRanking, stationUtilization,
      hourlyDist, weekdayDist, facilityType, userBehavior,
      platformDist, efficiency, hourlyStation, weekdayFacility, loadPrediction,
      batteryHealth, operations] = await Promise.all([
      fetchJson('/api/overview'),
      fetchJson('/api/trend/daily'),
      fetchJson('/api/station/ranking'),
      fetchJson('/api/station/utilization'),
      fetchJson('/api/distribution/hourly'),
      fetchJson('/api/distribution/weekday'),
      fetchJson('/api/facility/type'),
      fetchJson('/api/user/behavior'),
      fetchJson('/api/platform/distribution'),
      fetchJson('/api/efficiency/radar'),
      fetchJson('/api/comparison/hourly-station'),
      fetchJson('/api/comparison/weekday-facility'),
      fetchJson('/api/prediction/load'),
      fetchJson('/api/prediction/battery-health'),
      fetchJson('/api/prediction/operations'),
    ])

    if (overview) data.value.overview = overview
    if (dailyTrend) data.value.dailyTrend = dailyTrend
    if (stationRanking) data.value.stationRanking = stationRanking
    if (stationUtilization) data.value.stationUtilization = stationUtilization
    if (hourlyDist) data.value.hourlyDist = hourlyDist
    if (weekdayDist) data.value.weekdayDist = weekdayDist
    if (facilityType) data.value.facilityType = facilityType
    if (userBehavior) data.value.userBehavior = userBehavior
    if (platformDist) data.value.platformDist = platformDist
    if (efficiency) data.value.efficiency = efficiency
    if (hourlyStation) data.value.hourlyStation = hourlyStation
    if (weekdayFacility) data.value.weekdayFacility = weekdayFacility
    if (loadPrediction) data.value.loadPrediction = loadPrediction
    if (batteryHealth) data.value.batteryHealth = batteryHealth
    if (operations) data.value.operations = operations

    lastUpdate.value = new Date().toLocaleString('zh-CN')
    loading.value = false
  }

  async function reload() {
    loading.value = true
    try {
      await fetch(`${API_BASE}/api/reload`, { method: 'POST' })
      await fetchAll()
    } catch (e) {
      console.warn('Reload failed:', e.message)
    }
    loading.value = false
  }

  async function trainModel() {
    loading.value = true
    try {
      await fetch(`${API_BASE}/api/prediction/train`, { method: 'POST' })
      await fetchAll()
    } catch (e) {
      console.warn('Model training failed:', e.message)
    }
    loading.value = false
  }

  onMounted(() => {
    fetchAll()
    timer = setInterval(fetchAll, 10000)
  })

  onUnmounted(() => {
    clearInterval(timer)
  })

  return { data, loading, lastUpdate, fetchAll, reload, trainModel }
}
