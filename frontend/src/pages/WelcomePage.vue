<script setup lang="ts">
import { computed } from 'vue'
import { msalInstance } from '@/auth/msalInstance'
import { useRouter } from 'vue-router'

const router = useRouter()
const account = computed(() => msalInstance.getAllAccounts()[0])

async function logout() {
  await msalInstance.logoutPopup()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="welcome-page">
    <h1>Welcome, {{ account?.name ?? 'User' }}</h1>
    <button @click="logout">Logout</button>
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
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  background-color: #d43b00;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #b03200;
}
</style>
