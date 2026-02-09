<template>
  <el-card class="smart-recommendation-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon><MagicStick /></el-icon>
        <span>智能推荐</span>
        <el-button
          type="text"
          size="small"
          @click="refreshRecommendations"
          :loading="loading"
          style="margin-left: auto"
        >
          刷新
        </el-button>
      </div>
    </template>

    <div v-if="recommendations.length > 0" class="recommendations">
      <div
        v-for="(rec, index) in recommendations.slice(0, 3)"
        :key="index"
        class="recommendation-item"
        @click="selectRecommendation(rec)"
      >
        <el-icon class="recommendation-icon"><Star /></el-icon>
        <div class="recommendation-content">
          <div class="recommendation-title">{{ rec.topic }}</div>
          <div class="recommendation-meta">
            {{ rec.article_count }} 篇相关文章
          </div>
        </div>
      </div>
    </div>

    <el-empty v-else description="暂无推荐" :image-size="80" />

    <div class="card-footer">
      <el-button type="text" @click="$router.push('/topics')">
        查看更多推荐 →
      </el-button>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Star } from '@element-plus/icons-vue'
import api from '../api/index'

const loading = ref(false)
const recommendations = ref([])

const fetchRecommendations = async () => {
  loading.value = true
  try {
    const articlesResponse = await api.get('/websites', {
      params: { page: 1, page_size: 10 }
    })
    
    const articles = articlesResponse.list || []
    
    if (articles.length === 0) {
      return
    }
    
    const response = await api.post('/ai/recommend/topics', {
      articles: articles.map(a => ({
        id: a.id,
        title: a.title,
        content: a.content || ''
      })),
      num_topics: 3
    })
    
    recommendations.value = response.recommendations || []
  } catch (error) {
    // 静默失败，不显示错误
    console.error('获取推荐失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshRecommendations = () => {
  fetchRecommendations()
}

const selectRecommendation = (rec) => {
  // 跳转到主题推荐页面或显示详情
  ElMessage.info(`选择主题: ${rec.topic}`)
}

onMounted(() => {
  fetchRecommendations()
})
</script>

<style scoped>
.smart-recommendation-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.recommendations {
  min-height: 150px;
}

.recommendation-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
}

.recommendation-item:hover {
  background-color: #f5f7fa;
  border-color: #409eff;
  transform: translateX(5px);
}

.recommendation-icon {
  font-size: 24px;
  color: #409eff;
}

.recommendation-content {
  flex: 1;
}

.recommendation-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.recommendation-meta {
  font-size: 12px;
  color: #909399;
}

.card-footer {
  text-align: right;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}
</style>
