<template>
  <div class="website-list">
    <!-- 工具栏 -->
    <el-card class="toolbar-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索关键词"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-input
            v-model="searchForm.domain"
            placeholder="筛选域名"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Link /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
        <el-col :span="6" style="text-align: right">
          <el-button type="success" @click="$router.push('/tasks')">
            <el-icon><Plus /></el-icon>
            创建任务
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.total || 0 }}</div>
            <div class="stat-label">总网站数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.domain_stats?.length || 0 }}</div>
            <div class="stat-label">域名数量</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.date_stats?.length || 0 }}</div>
            <div class="stat-label">最近7天爬取</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        :data="tableData"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="domain" label="域名" width="180" />
        <el-table-column prop="description" label="简介" min-width="250" show-overflow-tooltip />
        <el-table-column prop="status_code" label="状态码" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status_code === 200 ? 'success' : 'danger'">
              {{ row.status_code }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="crawl_time" label="爬取时间" width="180" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleViewDetail(row)"
            >
              查看详情
            </el-button>
            <el-button
              type="info"
              size="small"
              @click="analyzeArticle(row)"
            >
              AI分析
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="文章详情"
      width="70%"
    >
      <el-descriptions :column="2" border v-if="currentDetail">
        <el-descriptions-item label="ID">{{ currentDetail.id }}</el-descriptions-item>
        <el-descriptions-item label="域名">{{ currentDetail.domain }}</el-descriptions-item>
        <el-descriptions-item label="URL" :span="2">
          <a :href="currentDetail.url" target="_blank">{{ currentDetail.url }}</a>
        </el-descriptions-item>
        <el-descriptions-item label="标题" :span="2">{{ currentDetail.title }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentDetail.description }}</el-descriptions-item>
        <el-descriptions-item label="关键词">{{ currentDetail.keywords }}</el-descriptions-item>
        <el-descriptions-item label="作者">{{ currentDetail.author }}</el-descriptions-item>
        <el-descriptions-item label="发布时间">{{ currentDetail.publish_time }}</el-descriptions-item>
        <el-descriptions-item label="爬取时间">{{ currentDetail.crawl_time }}</el-descriptions-item>
        <el-descriptions-item label="状态码">
          <el-tag :type="currentDetail.status_code === 200 ? 'success' : 'danger'">
            {{ currentDetail.status_code }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="内容" :span="2">
          <div class="content-preview">
            {{ currentDetail.content ? (currentDetail.content.substring(0, 500) + '...') : '无内容' }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Link, Plus } from '@element-plus/icons-vue'
import api from '../api/index'

const router = useRouter()

// 搜索表单
const searchForm = reactive({
  keyword: '',
  domain: ''
})

// 表格数据
const tableData = ref([])
const loading = ref(false)

// 分页
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 统计信息
const statistics = ref({
  total: 0,
  domain_stats: [],
  date_stats: []
})

// 详情对话框
const detailDialogVisible = ref(false)
const currentDetail = ref(null)

// 创建爬虫功能已合并到任务管理页面

// 获取网站列表
const fetchWebsiteList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: searchForm.keyword,
      domain: searchForm.domain
    }
    const result = await api.get('/websites', { params })
    tableData.value = result.list
    pagination.total = result.total
  } catch (error) {
    ElMessage.error('获取网站列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 获取统计信息
const fetchStatistics = async () => {
  try {
    const result = await api.get('/statistics')
    statistics.value = result
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchWebsiteList()
}

// 重置
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.domain = ''
  handleSearch()
}

// 分页大小改变
const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  fetchWebsiteList()
}

// 页码改变
const handlePageChange = (page) => {
  pagination.page = page
  fetchWebsiteList()
}

// 查看详情
const handleViewDetail = async (row) => {
  try {
    const result = await api.get(`/websites/${row.id}`)
    currentDetail.value = result
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取详情失败: ' + error.message)
  }
}

// AI分析文章
const analyzeArticle = (row) => {
  router.push({
    path: '/analysis',
    query: { articleId: row.id }
  })
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '提示', {
      type: 'warning'
    })
    await api.delete(`/websites/${row.id}`)
    ElMessage.success('删除成功')
    fetchWebsiteList()
    fetchStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

// 创建爬虫功能已合并到任务管理页面，相关代码已移除

// 初始化
onMounted(() => {
  fetchWebsiteList()
  fetchStatistics()
})
</script>

<style scoped>
.website-list {
  max-width: 1400px;
  margin: 0 auto;
}

.toolbar-card {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.table-card {
  margin-top: 20px;
}

.content-preview {
  max-height: 200px;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
  line-height: 1.6;
}
</style>
