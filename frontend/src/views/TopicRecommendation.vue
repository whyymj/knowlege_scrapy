<template>
  <div class="topic-recommendation">
    <el-card class="header-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="12">
          <h2>AI主题推荐</h2>
          <p class="description">基于LangChain智能分析文章内容，自动推荐相关主题</p>
        </el-col>
        <el-col :span="12" style="text-align: right">
          <el-button type="primary" @click="fetchRecommendations" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新推荐
          </el-button>
          <el-button type="success" @click="showManualSelect = true">
            <el-icon><Plus /></el-icon>
            手动选择主题
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 推荐主题列表 -->
    <el-row :gutter="20" v-if="recommendations.length > 0">
      <el-col :span="8" v-for="(rec, index) in recommendations" :key="index">
        <el-card class="topic-card" shadow="hover">
          <template #header>
            <div class="topic-header">
              <el-tag :type="getTagType(rec.category)">{{ rec.category || '未分类' }}</el-tag>
              <span class="topic-title">{{ rec.topic }}</span>
            </div>
          </template>
          
          <div class="topic-content">
            <p class="reason">{{ rec.reason }}</p>
            <div class="article-count">
              <el-icon><Document /></el-icon>
              <span>{{ rec.article_count }} 篇相关文章</span>
            </div>
            
            <el-divider />
            
            <div class="article-preview">
              <div 
                v-for="article in rec.articles.slice(0, 3)" 
                :key="article.id"
                class="article-item"
                @click="viewArticle(article)"
              >
                <el-icon><Document /></el-icon>
                <span>{{ article.title || '无标题' }}</span>
              </div>
            </div>
            
            <el-button 
              type="primary" 
              size="small" 
              style="width: 100%; margin-top: 10px"
              @click="selectTopic(rec)"
            >
              选择此主题
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 空状态 -->
    <el-empty v-else description="暂无推荐主题，请先添加文章数据" />

    <!-- 手动选择对话框 -->
    <el-dialog
      v-model="showManualSelect"
      title="手动选择主题"
      width="600px"
    >
      <el-form :model="manualForm" label-width="100px">
        <el-form-item label="主题名称" required>
          <el-input
            v-model="manualForm.topic"
            placeholder="请输入主题名称"
          />
        </el-form-item>
        <el-form-item label="选择文章">
          <el-select
            v-model="manualForm.articleIds"
            multiple
            placeholder="选择相关文章"
            style="width: 100%"
          >
            <el-option
              v-for="article in availableArticles"
              :key="article.id"
              :label="article.title || article.url"
              :value="article.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="manualForm.reason"
            type="textarea"
            placeholder="选择理由（可选）"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showManualSelect = false">取消</el-button>
        <el-button type="primary" @click="submitManualSelect" :loading="submitting">
          确认选择
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Plus, Document } from '@element-plus/icons-vue'
import api from '../api/index'

const loading = ref(false)
const submitting = ref(false)
const recommendations = ref([])
const showManualSelect = ref(false)
const availableArticles = ref([])

const manualForm = reactive({
  topic: '',
  articleIds: [],
  reason: ''
})

const getTagType = (category) => {
  const types = {
    '技术': 'success',
    '商业': 'warning',
    '学术': 'info',
    '新闻': 'danger'
  }
  return types[category] || 'info'
}

const fetchRecommendations = async () => {
  loading.value = true
  try {
    // 先获取文章列表
    const articlesResponse = await api.get('/websites', {
      params: { page: 1, page_size: 20 }
    })
    
    const articles = articlesResponse.list || []
    
    if (articles.length === 0) {
      ElMessage.warning('暂无文章数据，无法生成推荐')
      return
    }
    
    // 调用AI推荐接口
    const response = await api.post('/ai/recommend/topics', {
      articles: articles.map(a => ({
        id: a.id,
        title: a.title,
        content: a.content || ''
      })),
      num_topics: 6
    })
    
    recommendations.value = response.recommendations || []
    availableArticles.value = articles
    
    ElMessage.success('推荐生成成功')
  } catch (error) {
    ElMessage.error('获取推荐失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const selectTopic = async (rec) => {
  try {
    await api.post('/ai/select/topics', {
      user_id: 'current_user',
      topics: [rec.topic],
      articles: rec.articles
    })
    
    ElMessage.success('主题选择成功')
  } catch (error) {
    ElMessage.error('选择失败: ' + error.message)
  }
}

const submitManualSelect = async () => {
  if (!manualForm.topic) {
    ElMessage.warning('请输入主题名称')
    return
  }
  
  submitting.value = true
  try {
    const selectedArticles = availableArticles.value.filter(a => 
      manualForm.articleIds.includes(a.id)
    )
    
    await api.post('/ai/select/topics', {
      user_id: 'current_user',
      topics: [manualForm.topic],
      articles: selectedArticles,
      reason: manualForm.reason
    })
    
    ElMessage.success('主题选择成功')
    showManualSelect.value = false
    manualForm.topic = ''
    manualForm.articleIds = []
    manualForm.reason = ''
  } catch (error) {
    ElMessage.error('选择失败: ' + error.message)
  } finally {
    submitting.value = false
  }
}

const viewArticle = (article) => {
  // 跳转到文章详情或打开对话框
  ElMessage.info(`查看文章: ${article.title}`)
}

onMounted(() => {
  fetchRecommendations()
})
</script>

<style scoped>
.topic-recommendation {
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

.topic-card {
  margin-bottom: 20px;
  height: 100%;
}

.topic-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.topic-title {
  font-size: 16px;
  font-weight: bold;
  flex: 1;
}

.topic-content {
  min-height: 200px;
}

.reason {
  color: #606266;
  margin-bottom: 10px;
  line-height: 1.6;
}

.article-count {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #909399;
  font-size: 14px;
}

.article-preview {
  max-height: 150px;
  overflow-y: auto;
}

.article-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.article-item:hover {
  background-color: #f5f7fa;
}

.article-item span {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
