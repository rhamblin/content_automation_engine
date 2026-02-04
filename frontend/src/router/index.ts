import { createRouter, createWebHistory } from 'vue-router'
import LoginPage from '@/pages/LoginPage.vue'
import WelcomePage from '@/pages/WelcomePage.vue'
import AuthCompletePage from '@/pages/AuthCompletePage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'login', component: LoginPage },
    { path: '/auth/complete', name: 'auth-complete', component: AuthCompletePage },
    { path: '/welcome', name: 'welcome', component: WelcomePage },
  ],
})

export default router
