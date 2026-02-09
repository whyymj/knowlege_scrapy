<template>
  <el-container class="app-container">
    <el-header>
      <div class="header-content">
        <h1>网站爬虫管理系统</h1>
      </div>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  width: 100%;
  height: 100vh;
}

.app-container {
  height: 100vh;
}

.el-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content h1 {
  font-size: 24px;
  font-weight: 500;
}

.el-main {
  padding: 20px;
  background-color: #f5f5f5;
}
</style>
