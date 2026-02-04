<script setup lang="ts">
const clientId = import.meta.env.VITE_AZURE_CLIENT_ID
const tenantId = import.meta.env.VITE_AZURE_TENANT_ID
const redirectUri = `${import.meta.env.VITE_MANAGEMENT_API_URL}/entra/callback`

function login() {
  const params = new URLSearchParams({
    client_id: clientId,
    response_type: 'code',
    redirect_uri: redirectUri,
    scope: 'openid profile email User.Read',
    response_mode: 'query',
  })
  window.location.href = `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/authorize?${params}`
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
