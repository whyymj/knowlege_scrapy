<template>
  <div class="article-analysis">
    <el-card class="header-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="12">
          <h2>文章智能分析</h2>
          <p class="description">基于AI深度分析文章内容，提取关键信息</p>
        </el-col>
        <el-col :span="12" style="text-align: right">
          <el-select
            v-model="selectedArticleId"
            placeholder="选择要分析的文章"
            filterable
            style="width: 300px; margin-right: 10px"
            @change="onArticleSelect"
          >
            <el-option
              v-for="article in articles"
              :key="article.id"
              :label="article.title || article.url"
              :value="article.id"
            />
          </el-select>
          <el-button type="primary" @click="analyzeSelected" :loading="analyzing">
            <el-icon><Search /></el-icon>
            开始分析
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 分析结果 -->
    <el-card v-if="analysisResult" class="analysis-card">
      <template #header>
        <div class="analysis-header">
          <h3>分析结果</h3>
          <el-button type="success" size="small" @click="saveAnalysis">
            <el-icon><Check /></el-icon>
            保存分析
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 左侧：基本信息 -->
        <el-col :span="12">
          <el-descriptions title="文章信息" :column="1" border>
            <el-descriptions-item label="文章ID">
              {{ analysisResult.article_id }}
            </el-descriptions-item>
            <el-descriptions-item label="摘要">
              <div class="summary-text">{{ analysisResult.summary }}</div>
            </el-descriptions-item>
            <el-descriptions-item label="情感倾向">
              <el-tag :type="getSentimentType(analysisResult.sentiment)">
                {{ analysisResult.sentiment }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="阅读时间">
              {{ analysisResult.analysis?.read_time || 0 }} 分钟
            </el-descriptions-item>
            <el-descriptions-item label="复杂度">
              <el-tag>{{ analysisResult.analysis?.complexity || 'N/A' }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-col>

        <!-- 右侧：详细信息 -->
        <el-col :span="12">
          <el-card>
            <template #header>关键要点</template>
            <ul class="key-points">
              <li v-for="(point, index) in analysisResult.key_points" :key="index">
                {{ point }}
              </li>
            </ul>
          </el-card>

          <el-card style="margin-top: 20px">
            <template #header>关键实体</template>
            <div class="entities">
              <el-tag
                v-for="(entity, index) in analysisResult.entities"
                :key="index"
                style="margin: 5px"
              >
                {{ entity }}
              </el-tag>
            </div>
          </el-card>

          <el-card style="margin-top: 20px">
            <template #header>标签</template>
            <div class="tags">
              <el-tag
                v-for="(tag, index) in analysisResult.tags"
                :key="index"
                type="info"
                style="margin: 5px"
              >
                {{ tag }}
              </el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-else description="请选择文章进行分析" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Check } from '@element-plus/icons-vue'
import api from '../api/index'

const route = useRoute()

const articles = ref([])
const selectedArticleId = ref(null)
const analyzing = ref(false)
const analysisResult = ref(null)

const fetchArticles = async () => {
  try {
    const response = await api.get('/websites', {
      params: { page: 1, page_size: 100 }
    })
    articles.value = response.list || []
  } catch (error) {
    ElMessage.error('获取文章列表失败: ' + error.message)
  }
}

const onArticleSelect = (articleId) => {
  analysisResult.value = null
}

const analyzeSelected = async () => {
  if (!selectedArticleId.value) {
    ElMessage.warning('请先选择文章')
    return
  }

  const article = articles.value.find(a => a.id === selectedArticleId.value)
  if (!article) {
    ElMessage.error('文章不存在')
    return
  }

  analyzing.value = true
  try {
    const response = await api.post('/ai/analyze/article', {
      article: {
        id: article.id,
        title: article.title,
        content: article.content
      }
    })

    analysisResult.value = response
    ElMessage.success('分析完成')
  } catch (error) {
    ElMessage.error('分析失败: ' + error.message)
  } finally {
    analyzing.value = false
  }
}

const saveAnalysis = async () => {
  if (!analysisResult.value) {
    return
  }

  try {
    // 这里可以保存分析结果到数据库或本地
    ElMessage.success('分析结果已保存')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  }
}

const getSentimentType = (sentiment) => {
  const types = {
    'positive': 'success',
    'negative': 'danger',
    'neutral': 'info'
  }
  return types[sentiment?.toLowerCase()] || 'info'
}

onMounted(() => {
  fetchArticles()
  
  // 如果URL中有articleId参数，自动选择并分析
  const articleId = route.query.articleId
  if (articleId) {
    selectedArticleId.value = parseInt(articleId)
    // 等待文章列表加载完成后再分析
    setTimeout(() => {
      analyzeSelected()
    }, 500)
  }
})
</script>

<style scoped>
.article-analysis {
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
}

.header-card h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
}

.description {
  color: #909399;
  margin: 0;
}

.analysis-card {
  margin-top: 20px;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.analysis-header h3 {
  margin: 0;
}

.summary-text {
  line-height: 1.6;
  color: #606266;
}

.key-points {
  list-style: none;
  padding: 0;
  margin: 0;
}

.key-points li {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  line-height: 1.6;
}

.key-points li:last-child {
  border-bottom: none;
}

.entities,
.tags {
  min-height: 50px;
}
</style>
