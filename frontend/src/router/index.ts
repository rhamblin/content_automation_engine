import { createRouter, createWebHistory } from 'vue-router'
import { msalInstance } from '@/auth/msalInstance'
import LoginPage from '@/pages/LoginPage.vue'
import WelcomePage from '@/pages/WelcomePage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'login', component: LoginPage },
    {
      path: '/welcome',
      name: 'welcome',
      component: WelcomePage,
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth) {
    const accounts = msalInstance.getAllAccounts()
    if (accounts.length === 0) {
      return { name: 'login' }
    }
  }
})

export default router
