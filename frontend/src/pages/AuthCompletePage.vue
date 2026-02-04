<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const params = ref<Record<string, string>>({})

onMounted(() => {
  const query = route.query
  params.value = Object.fromEntries(
    Object.entries(query).map(([k, v]) => [k, String(v)]),
  )
  console.log('Auth callback params:', params.value)
})
</script>

<template>
  <div class="auth-complete">
    <h1>Auth Complete</h1>
    <pre>{{ JSON.stringify(params, null, 2) }}</pre>
  </div>
</template>

<style scoped>
.auth-complete {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  gap: 2rem;
}

pre {
  background: #f4f4f4;
  padding: 1rem;
  border-radius: 4px;
  max-width: 600px;
  overflow-x: auto;
}
</style>
