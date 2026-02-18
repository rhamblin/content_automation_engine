<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useAuth } from '@/composables/useAuth'

const { fetchWithAuth, startRefreshTimer, stopRefreshTimer, logout } = useAuth()
const apiUrl = import.meta.env.VITE_MANAGEMENT_API_URL
const displayName = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const response = await fetchWithAuth(`${apiUrl}/me`)
    if (!response.ok) {
      await logout()
      return
    }
    const user = await response.json()
    displayName.value = user.email ?? 'User'
    startRefreshTimer()
  } catch {
    await logout()
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  stopRefreshTimer()
})
</script>

<template>
  <div class="welcome-page">
    <template v-if="!loading">
      <h1>Welcome, {{ displayName }}</h1>
      <button @click="logout">Logout</button>
    </template>
  </div>
</template>

<style scoped>
.welcome-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  gap: 2rem;
}

button {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  background-color: #d43b2f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #b32d23;
}
</style>
