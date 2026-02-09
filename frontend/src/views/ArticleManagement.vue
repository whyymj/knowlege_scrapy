<template>
  <div class="article-management">
    <el-card class="header-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="12">
          <h2>文章管理</h2>
          <p class="description">管理所有抓取到的文章，支持搜索、筛选和查看</p>
        </el-col>
        <el-col :span="12" style="text-align: right">
          <el-button 
            type="danger" 
            @click="handleDeleteSelected" 
            :disabled="selectedArticles.length === 0"
          >
            <el-icon><Delete /></el-icon>
            一键删除选中 ({{ selectedArticles.length }})
          </el-button>
          <el-button @click="fetchArticles">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 搜索和筛选 -->
    <el-card style="margin-top: 20px">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索标题或内容..."
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
            <template #append>
              <el-button @click="handleSearch">搜索</el-button>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterDataType" placeholder="数据类型" clearable @change="handleSearch">
            <el-option label="全部" value="" />
            <el-option label="通用" value="general" />
            <el-option label="AI" value="ai" />
            <el-option label="新闻" value="news" />
            <el-option label="股票" value="stock" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterTaskId" placeholder="任务筛选" clearable filterable @change="handleSearch">
            <el-option label="全部任务" value="" />
            <el-option
              v-for="task in taskList"
              :key="task.task_id"
              :label="task.task_name"
              :value="task.task_id"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleSearch"
          />
        </el-col>
      </el-row>
    </el-card>

    <!-- 文章列表 -->
    <el-card style="margin-top: 20px">
      <el-table
        ref="articleTableRef"
        :data="articles"
        v-loading="loading"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="标题" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            <a 
              v-if="getArticleUrl(row)" 
              :href="getArticleUrl(row)" 
              target="_blank"
              style="color: #409eff; text-decoration: none"
            >
              {{ row.title || '无标题' }}
            </a>
            <span v-else>{{ row.title || '无标题' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="source_url" label="源URL" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">
            <a 
              :href="row.source_url" 
              target="_blank"
              style="color: #909399; text-decoration: none; font-size: 12px"
            >
              {{ row.source_url }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="data_type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.data_type || 'general' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="task_id" label="任务ID" width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="goToTask(row.task_id)" style="font-size: 12px">
              {{ row.task_id }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="extracted_at" label="抓取时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="viewArticleDetail(row)"
            >
              查看详情
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDeleteArticle(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 文章详情对话框 -->
    <el-dialog
      v-model="showArticleDetailDialog"
      title="文章详情"
      width="80%"
    >
      <el-descriptions :column="2" border v-if="currentArticle">
        <el-descriptions-item label="标题" :span="2">
          <a 
            v-if="getArticleUrl(currentArticle)" 
            :href="getArticleUrl(currentArticle)" 
            target="_blank"
            style="color: #409eff; text-decoration: none; font-size: 18px; font-weight: bold"
          >
            {{ currentArticle.title || '无标题' }}
          </a>
          <span v-else style="font-size: 18px; font-weight: bold">{{ currentArticle.title || '无标题' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="源URL" :span="2">
          <a 
            :href="currentArticle.source_url" 
            target="_blank"
            style="color: #909399; text-decoration: none"
          >
            {{ currentArticle.source_url }}
          </a>
        </el-descriptions-item>
        <el-descriptions-item label="数据类型">
          <el-tag>{{ currentArticle.data_type || 'general' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="抓取时间">{{ currentArticle.extracted_at }}</el-descriptions-item>
        <el-descriptions-item label="任务ID">
          <el-link type="primary" @click="goToTask(currentArticle.task_id)">
            {{ currentArticle.task_id }}
          </el-link>
        </el-descriptions-item>
        <el-descriptions-item label="内容" :span="2">
          <div 
            style="max-height: 400px; overflow-y: auto; padding: 10px; background-color: #f5f5f5; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word"
            v-html="formatContent(currentArticle.content)"
          ></div>
        </el-descriptions-item>
        <el-descriptions-item label="元数据" :span="2" v-if="currentArticle.metadata">
          <pre style="max-height: 300px; overflow-y: auto; background-color: #f5f5f5; padding: 10px; border-radius: 4px">{{ JSON.stringify(currentArticle.metadata, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search, Delete } from '@element-plus/icons-vue'
import api from '../api/index'

const router = useRouter()

const loading = ref(false)
const articles = ref([])
const selectedArticles = ref([])
const showArticleDetailDialog = ref(false)
const currentArticle = ref(null)
const searchKeyword = ref('')
const filterDataType = ref('')
const filterTaskId = ref('')
const dateRange = ref(null)
const taskList = ref([])
const articleTableRef = ref(null)

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const getStatusType = (status) => {
  const types = {
    'pending': 'info',
    'running': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return types[status] || 'info'
}

const getArticleUrl = (article) => {
  if (article.metadata && typeof article.metadata === 'object') {
    return article.metadata.url || article.metadata.source_url
  }
  return article.source_url
}

const formatContent = (content) => {
  if (!content) return '暂无内容'
  // 简单的HTML转义和换行处理
  return content.replace(/\n/g, '<br>').replace(/  /g, '&nbsp;&nbsp;')
}

const fetchArticles = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page
    }
    
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }
    
    if (filterDataType.value) {
      params.data_type = filterDataType.value
    }
    
    if (filterTaskId.value) {
      params.task_id = filterTaskId.value
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const response = await api.get('/articles', { params })
    // API返回格式: { code: 200, data: { list: [], total: 0 } }
    const dataResponse = response.data || response
    
    articles.value = dataResponse.list || []
    pagination.total = dataResponse.total || 0
  } catch (error) {
    ElMessage.error('获取文章列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const fetchTaskList = async () => {
  try {
    const response = await api.get('/tasks', {
      params: {
        per_page: 100
      }
    })
    // API返回格式: { code: 200, data: { list: [] } }
    const dataResponse = response.data || response
    taskList.value = dataResponse.list || []
  } catch (error) {
    console.error('获取任务列表失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchArticles()
}

const handleSizeChange = (size) => {
  pagination.per_page = size
  pagination.page = 1
  fetchArticles()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchArticles()
}

const handleSelectionChange = (selection) => {
  selectedArticles.value = selection
}

const viewArticleDetail = (article) => {
  currentArticle.value = article
  showArticleDetailDialog.value = true
}

const handleDeleteArticle = async (article) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文章 "${article.title || '无标题'}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/articles/${article.id}`)
    ElMessage.success('文章删除成功')
    fetchArticles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除文章失败: ' + error.message)
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedArticles.value.length === 0) {
    ElMessage.warning('请选择要删除的文章')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedArticles.value.length} 篇文章吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const ids = selectedArticles.value.map(a => a.id)
    await api.post('/articles/batch-delete', { ids })
    ElMessage.success('批量删除成功')
    selectedArticles.value = []
    fetchArticles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败: ' + error.message)
    }
  }
}

const handleDeleteSelected = async () => {
  if (selectedArticles.value.length === 0) {
    ElMessage.warning('请先选择要删除的文章')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedArticles.value.length} 篇文章吗？此操作不可恢复。`,
      '确认一键删除选中',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const ids = selectedArticles.value.map(a => a.id)
    await api.post('/articles/batch-delete', { ids })
    ElMessage.success(`成功删除 ${selectedArticles.value.length} 篇文章`)
    selectedArticles.value = []
    fetchArticles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('一键删除失败: ' + error.message)
    }
  }
}

const goToTask = (taskId) => {
  router.push({ name: 'Tasks', query: { task_id: taskId } })
}

onMounted(() => {
  fetchTaskList()
  fetchArticles()
})
</script>

<style scoped>
.article-management {
  max-width: 1600px;
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

pre {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
  font-size: 12px;
}
</style>
