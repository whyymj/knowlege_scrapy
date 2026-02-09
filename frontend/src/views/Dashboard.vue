<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="30"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 智能推荐 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <SmartRecommendation />
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>最近任务</span>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="task in recentTasks"
              :key="task.id"
              :timestamp="task.created_at"
            >
              <el-card>
                <p><strong>{{ task.task_name }}</strong></p>
                <p>
                  <el-tag :type="getStatusType(task.status)" size="small">
                    {{ task.status }}
                  </el-tag>
                  <span style="margin-left: 10px">{{ task.items_count }} 条数据</span>
                </p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速操作 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <el-icon><Lightning /></el-icon>
          <span>快速操作</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <el-button type="primary" size="large" @click="$router.push('/tasks')" style="width: 100%">
            <el-icon><Plus /></el-icon>
            创建任务
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button type="success" size="large" @click="$router.push('/topics')" style="width: 100%">
            <el-icon><Star /></el-icon>
            AI推荐
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button type="info" size="large" @click="$router.push('/analysis')" style="width: 100%">
            <el-icon><Search /></el-icon>
            文章分析
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button type="warning" size="large" @click="$router.push('/websites')" style="width: 100%">
            <el-icon><Document /></el-icon>
            查看数据
          </el-button>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { 
  Document, Star, Search, List, Clock, Lightning, Plus 
} from '@element-plus/icons-vue'
import api from '../api/index'
import SmartRecommendation from '../components/SmartRecommendation.vue'

const stats = ref([
  { label: '总数据', value: 0, icon: 'Document', color: '#409eff' },
  { label: '任务数', value: 0, icon: 'List', color: '#67c23a' },
  { label: '主题数', value: 0, icon: 'Star', color: '#e6a23c' },
  { label: '今日新增', value: 0, icon: 'Plus', color: '#f56c6c' }
])

const recentTasks = ref([])

const getStatusType = (status) => {
  const types = {
    'pending': 'info',
    'running': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return types[status] || 'info'
}

const fetchStats = async () => {
  try {
    // 获取统计数据
    const statsResponse = await api.get('/statistics')
    stats.value[0].value = statsResponse.total || 0
    
    // 获取任务列表
    const tasksResponse = await api.get('/tasks', {
      params: { page: 1, per_page: 5 }
    })
    recentTasks.value = tasksResponse.list || []
    stats.value[1].value = tasksResponse.total || 0
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}
</style>
