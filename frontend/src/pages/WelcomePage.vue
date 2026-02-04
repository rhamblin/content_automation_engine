<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const apiUrl = import.meta.env.VITE_MANAGEMENT_API_URL
const displayName = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const response = await fetch(`${apiUrl}/me`, { credentials: 'include' })
    if (!response.ok) {
      router.push({ name: 'login' })
      return
    }
    const user = await response.json()
    displayName.value = user.displayName ?? 'User'
  } catch {
    router.push({ name: 'login' })
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="welcome-page">
    <template v-if="!loading">
      <h1>Welcome, {{ displayName }}</h1>
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
</style>
