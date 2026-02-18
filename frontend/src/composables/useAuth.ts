import { ref } from 'vue'
import { useRouter } from 'vue-router'

const apiUrl = import.meta.env.VITE_MANAGEMENT_API_URL

const refreshTimerId = ref<ReturnType<typeof setTimeout> | null>(null)

export function useAuth() {
  const router = useRouter()

  async function refreshToken(): Promise<boolean> {
    try {
      const response = await fetch(`${apiUrl}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      })
      return response.ok
    } catch {
      return false
    }
  }

  function startRefreshTimer() {
    stopRefreshTimer()
    // Refresh 5 minutes before the 1-hour expiry (55 min)
    const interval = 55 * 60 * 1000
    refreshTimerId.value = setTimeout(async function tick() {
      const success = await refreshToken()
      if (success) {
        refreshTimerId.value = setTimeout(tick, interval)
      } else {
        await logout()
      }
    }, interval)
  }

  function stopRefreshTimer() {
    if (refreshTimerId.value !== null) {
      clearTimeout(refreshTimerId.value)
      refreshTimerId.value = null
    }
  }

  async function logout() {
    stopRefreshTimer()
    try {
      await fetch(`${apiUrl}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      })
    } catch {
      // Best-effort — clear cookie on server
    }
    router.push({ name: 'login' })
  }

  async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    const opts: RequestInit = { ...options, credentials: 'include' }
    let response = await fetch(url, opts)

    if (response.status === 401) {
      const refreshed = await refreshToken()
      if (refreshed) {
        response = await fetch(url, opts)
      } else {
        await logout()
      }
    }

    return response
  }

  return {
    refreshToken,
    startRefreshTimer,
    stopRefreshTimer,
    logout,
    fetchWithAuth,
  }
}
