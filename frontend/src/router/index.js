import { createRouter, createWebHistory } from 'vue-router'
import WebsiteList from '../views/WebsiteList.vue'

const routes = [
  {
    path: '/',
    name: 'WebsiteList',
    component: WebsiteList
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
