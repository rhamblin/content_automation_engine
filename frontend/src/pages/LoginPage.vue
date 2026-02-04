<script setup lang="ts">
import { msalInstance } from '@/auth/msalInstance'
import { useRouter } from 'vue-router'

const router = useRouter()

async function login() {
  try {
    await msalInstance.loginPopup({ scopes: ['User.Read'] })
    router.push({ name: 'welcome' })
  } catch (error) {
    console.error('Login failed:', error)
  }
}
</script>

<template>
  <div class="login-page">
    <h1>Content Automation Engine</h1>
    <button @click="login">Login with Microsoft</button>
  </div>
</template>

<style scoped>
.login-page {
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
  background-color: #0078d4;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #106ebe;
}
</style>
