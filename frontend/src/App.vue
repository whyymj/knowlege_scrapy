<template>
  <div id="app">
    <el-container>
      <!-- 侧边栏导航 -->
      <el-aside width="250px" class="sidebar">
        <div class="logo">
          <h2>抓取信息系统</h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          class="sidebar-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/websites">
            <el-icon><Document /></el-icon>
            <span>网站列表</span>
          </el-menu-item>
          <el-menu-item index="/articles">
            <el-icon><DocumentCopy /></el-icon>
            <span>文章管理</span>
          </el-menu-item>
          <el-menu-item index="/analysis">
            <el-icon><Search /></el-icon>
            <span>文章分析</span>
          </el-menu-item>
          <el-menu-item index="/tasks">
            <el-icon><List /></el-icon>
            <span>任务管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Odometer, Document, DocumentCopy, Star, Search, List } from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => {
  return route.path
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
  margin: 0;
  padding: 0;
}

.sidebar {
  background-color: #304156;
  height: 100vh;
  overflow-y: auto;
  position: fixed;
  left: 0;
  top: 0;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #434a55;
}

.logo h2 {
  color: #fff;
  margin: 0;
  font-size: 20px;
}

.sidebar-menu {
  border: none;
  background-color: #304156;
}

.sidebar-menu .el-menu-item {
  color: #bfcbd9;
}

.sidebar-menu .el-menu-item:hover {
  background-color: #263445 !important;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: #1890ff !important;
  color: #fff;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
  height: 100vh;
  margin-left: 250px;
}
</style>
