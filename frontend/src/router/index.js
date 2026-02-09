import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import WebsiteList from '../views/WebsiteList.vue'
import ArticleAnalysis from '../views/ArticleAnalysis.vue'
import TaskManagement from '../views/TaskManagement.vue'
import ArticleManagement from '../views/ArticleManagement.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Dashboard,
    meta: { title: '仪表盘' }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { title: '仪表盘' }
  },
  {
    path: '/websites',
    name: 'Websites',
    component: WebsiteList,
    meta: { title: '网站列表' }
  },
  {
    path: '/articles',
    name: 'Articles',
    component: ArticleManagement,
    meta: { title: '文章管理' }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: ArticleAnalysis,
    meta: { title: '文章分析' }
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: TaskManagement,
    meta: { title: '任务管理' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
