<template>
  <el-config-provider :size="'small'">
    <div class="task-management">
    <el-card class="header-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="12">
          <h2>任务管理</h2>
          <p class="description">管理抓取任务，查看执行状态和结果</p>
        </el-col>
        <el-col :span="12" style="text-align: right">
          <el-button type="danger" size="small" @click="handleDeleteAllTasks" :disabled="pagination.total === 0">
            <el-icon><Delete /></el-icon>
            一键删除全部 ({{ pagination.total }})
          </el-button>
          <el-button type="primary" size="small" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建任务
          </el-button>
          <el-button size="small" @click="fetchTasks">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 搜索和筛选工具栏 -->
    <el-card class="toolbar-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索任务名称"
            clearable
            size="small"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="searchForm.status"
            placeholder="筛选状态"
            clearable
            size="small"
            @change="handleSearch"
            style="width: 100%"
          >
            <el-option label="全部" value="" />
            <el-option label="待执行" value="pending" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" size="small" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button size="small" @click="handleReset">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.total || 0 }}</div>
            <div class="stat-label">总任务数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.running || 0 }}</div>
            <div class="stat-label">运行中</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.completed || 0 }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.failed || 0 }}</div>
            <div class="stat-label">失败</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 任务列表 -->
    <el-card>
      <el-table
        :data="tasks"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="task_id" label="任务ID" width="200" />
        <el-table-column prop="task_name" label="任务名称" min-width="200" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
            <el-progress
              v-if="row.status === 'running'"
              :percentage="getTaskProgress(row.task_id)"
              :stroke-width="6"
              :show-text="false"
              style="margin-top: 5px; width: 100px"
            />
          </template>
        </el-table-column>
        <el-table-column prop="items_count" label="数据条数" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.status === 'running'" class="progress-text">
              {{ getTaskItemsCount(row.task_id) || row.items_count || 0 }}
            </span>
            <span v-else>{{ row.items_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="errors_count" label="错误数" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.errors_count > 0" type="danger" size="small">
              {{ row.errors_count }}
            </el-tag>
            <span v-else>0</span>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.completed_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="viewTaskDetail(row)"
            >
              <el-icon style="margin-right: 4px"><Document /></el-icon>
              查看详情
              <span v-if="row.items_count > 0" style="margin-left: 4px">({{ row.items_count }})</span>
            </el-button>
            <el-button
              v-if="row.status === 'failed' || row.status === 'completed'"
              type="warning"
              size="small"
              @click="handleRetryTask(row)"
              :loading="retryingTaskId === row.task_id"
            >
              重试
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="handleEditTask(row)"
              :disabled="row.status === 'running'"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDeleteTask(row)"
              :disabled="row.status === 'running'"
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
        size="small"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 创建任务对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建抓取任务"
      width="900px"
      :close-on-click-modal="false"
      class="create-task-dialog"
    >
      <el-steps :active="createTaskStep" finish-status="success" class="task-steps">
        <el-step title="选择URL来源" />
        <el-step title="配置任务" />
        <el-step title="确认创建" />
      </el-steps>

      <!-- 步骤1：选择URL来源 -->
      <div v-if="createTaskStep === 0" class="step-content">
        <el-form :model="taskForm" label-width="100px" class="create-task-form">
          <el-form-item label="URL来源" required class="url-source-item">
            <el-radio-group v-model="taskForm.urlSource" @change="onUrlSourceChange" size="default">
              <el-radio-button label="ai">
                <el-icon style="margin-right: 5px"><MagicStick /></el-icon>
                AI智能推荐
              </el-radio-button>
              <el-radio-button label="manual">
                <el-icon style="margin-right: 5px"><Edit /></el-icon>
                手动输入URL
              </el-radio-button>
            </el-radio-group>
          </el-form-item>

          <!-- AI推荐模式 -->
          <div v-if="taskForm.urlSource === 'ai'" class="ai-recommend-section">
            <div class="topic-section">
              <el-form-item label="抓取主题" required class="topic-form-item">
                <el-input
                  v-model="taskForm.topic"
                  type="textarea"
                  :rows="4"
                  placeholder="请详细描述您想要抓取的内容主题&#10;例如：最新的AI技术进展、Python编程最佳实践、区块链技术应用案例等"
                  @keyup.enter.ctrl="handleGetRecommendedSites"
                  class="topic-input"
                  maxlength="500"
                  show-word-limit
                  size="small"
                />
                <div class="topic-hint-row">
                  <el-link 
                    type="primary" 
                    :underline="false" 
                    @click="activeCollapse = activeCollapse.includes('guidance') ? [] : ['guidance']"
                    class="guidance-link"
                  >
                    <el-icon><QuestionFilled /></el-icon>
                    <span>如何描述任务内容？</span>
                    <el-icon :class="{ 'rotate-icon': activeCollapse.includes('guidance') }">
                      <ArrowRight />
                    </el-icon>
                  </el-link>
                </div>
              </el-form-item>
              
              <!-- 描述提示卡片 - 可折叠 -->
              <el-collapse v-model="activeCollapse" class="guidance-collapse">
                <el-collapse-item name="guidance">
                  <div class="guidance-content">
                    <div class="guidance-grid">
                      <div class="guidance-item">
                        <div class="guidance-item-header">
                          <el-icon class="guidance-icon"><Check /></el-icon>
                          <strong>明确主题</strong>
                        </div>
                        <p>例如："AI技术"、"Python编程"、"区块链应用"</p>
                      </div>
                      <div class="guidance-item">
                        <div class="guidance-item-header">
                          <el-icon class="guidance-icon"><Check /></el-icon>
                          <strong>具体领域</strong>
                        </div>
                        <p>例如："机器学习算法"、"Web前端开发"、"加密货币"</p>
                      </div>
                      <div class="guidance-item">
                        <div class="guidance-item-header">
                          <el-icon class="guidance-icon"><Check /></el-icon>
                          <strong>内容类型</strong>
                        </div>
                        <p>例如："最新进展"、"教程文章"、"案例分析"</p>
                      </div>
                    </div>
                    <div class="guidance-examples">
                      <div class="examples-title">
                        <el-icon><Star /></el-icon>
                        <span>优秀示例</span>
                      </div>
                      <div class="examples-list">
                        <div class="example-item">
                          <el-icon class="example-icon"><Check /></el-icon>
                          <span>最新的AI技术进展，特别是大语言模型和生成式AI的最新研究</span>
                        </div>
                        <div class="example-item">
                          <el-icon class="example-icon"><Check /></el-icon>
                          <span>Python编程最佳实践和代码优化技巧，面向中级开发者</span>
                        </div>
                        <div class="example-item">
                          <el-icon class="example-icon"><Check /></el-icon>
                          <span>区块链技术在金融领域的应用案例和实际项目</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-collapse-item>
              </el-collapse>

              <!-- 操作区域 -->
              <div class="action-area">
                <el-alert
                  :closable="false"
                  type="info"
                  show-icon
                  class="action-hint-alert"
                >
                  <template #default>
                    <div class="hint-content">
                      <div class="hint-main">描述越详细，AI推荐的网站越准确</div>
                      <div class="hint-sub">提示：可按 <kbd>Ctrl + Enter</kbd> 快速获取推荐</div>
                    </div>
                  </template>
                </el-alert>
                <el-button 
                  type="primary" 
                  size="small"
                  @click="handleGetRecommendedSites" 
                  :loading="recommendingSites"
                  :disabled="!taskForm.topic || !taskForm.topic.trim()"
                  class="recommend-button-large"
                >
                  <el-icon><MagicStick /></el-icon>
                  AI推荐网站
                </el-button>
              </div>
            </div>

            <!-- 推荐网站列表 -->
            <div v-if="recommendedSites.length > 0" class="recommended-sites-section">
              <div class="section-header">
                <div class="header-left">
                  <el-icon class="header-icon"><Link /></el-icon>
                  <span class="header-title">AI推荐网站</span>
                  <el-tag type="info" size="small" class="header-tag">共 {{ recommendedSites.length }} 个</el-tag>
                  <el-tag type="success" size="small" class="header-tag">已选 {{ taskForm.selectedSites.length }} 个</el-tag>
                </div>
                <el-button 
                  text 
                  type="primary" 
                  size="small"
                  @click="taskForm.selectedSites = recommendedSites.map(s => s.url)"
                  :disabled="taskForm.selectedSites.length === recommendedSites.length"
                  class="select-all-btn"
                >
                  <el-icon><Select /></el-icon>
                  全选
                </el-button>
              </div>
              <div class="sites-list">
                <el-checkbox-group v-model="taskForm.selectedSites" class="sites-checkbox-group">
                  <div
                    v-for="site in recommendedSites"
                    :key="site.url"
                    class="site-card"
                    :class="{ 'site-selected': taskForm.selectedSites.includes(site.url) }"
                  >
                    <el-checkbox :label="site.url" class="site-checkbox">
                      <div class="site-info">
                        <div class="site-url-wrapper">
                          <div class="site-url-text" :title="site.url">{{ site.url }}</div>
                          <el-link 
                            :href="site.url" 
                            target="_blank" 
                            type="primary"
                            :underline="false"
                            class="site-link"
                            @click.stop
                          >
                            <el-icon><Link /></el-icon>
                          </el-link>
                        </div>
                        <div class="site-reason" v-if="site.reason">
                          <el-icon class="reason-icon"><InfoFilled /></el-icon>
                          <span class="reason-text">{{ site.reason }}</span>
                        </div>
                      </div>
                    </el-checkbox>
                  </div>
                </el-checkbox-group>
              </div>
            </div>
          </div>

          <!-- 手动输入模式 -->
          <div v-if="taskForm.urlSource === 'manual'" class="manual-input-section">
            <el-form-item label="URL列表" required>
              <el-input
                v-model="taskForm.urls"
                type="textarea"
                :rows="8"
                placeholder="每行一个URL，例如：&#10;https://example.com/page1&#10;https://example.com/page2&#10;https://example.com/page3"
                class="urls-input"
                size="small"
              />
              <div class="input-hint">
                <el-icon><InfoFilled /></el-icon>
                <span>支持多个URL，每行一个。系统会自动检测第一个URL的网页结构</span>
              </div>
            </el-form-item>
          </div>
        </el-form>

        <div class="step-actions">
          <el-button size="small" @click="showCreateDialog = false">取消</el-button>
          <el-button 
            type="primary" 
            size="small"
            @click="goToNextStep"
            :disabled="(taskForm.urlSource === 'ai' && taskForm.selectedSites.length === 0) || (taskForm.urlSource === 'manual' && !taskForm.urls)"
            class="next-button"
          >
            下一步
            <el-icon style="margin-left: 5px"><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 步骤2：配置任务 -->
      <div v-if="createTaskStep === 1" class="step-content">
        <el-form :model="taskForm" label-width="100px" class="create-task-form">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="任务名称" required>
                <el-input 
                  v-model="taskForm.name" 
                  placeholder="请输入任务名称"
                  clearable
                  size="small"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="数据源类型" required>
                <el-radio-group v-model="taskForm.sourceType">
                  <el-radio-button label="http">HTTP网页</el-radio-button>
                  <el-radio-button label="api">API接口</el-radio-button>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="URL列表" required>
            <el-input
              v-model="taskForm.urlDisplay"
              type="textarea"
              :rows="6"
              readonly
              class="url-display"
              size="small"
            />
            <div class="extractor-action">
              <el-button
                type="primary"
                :loading="analyzingExtractor"
                @click="analyzeExtractor"
                :disabled="!getUrlList() || getUrlList().length === 0"
                class="analyze-button"
              >
                <el-icon><MagicStick /></el-icon>
                智能检测提取器
              </el-button>
              <span class="action-hint">
                自动分析第一个URL的网页结构，推荐最适合的提取器类型
              </span>
            </div>
            <el-alert
              v-if="extractorAnalysis"
              :title="`已自动选择: ${getExtractorTypeName(extractorAnalysis.recommended_type)} (置信度: ${Math.round(extractorAnalysis.confidence * 100)}%)`"
              :description="extractorAnalysis.reason"
              type="success"
              :closable="false"
              class="extractor-alert"
              show-icon
            />
          </el-form-item>

          <!-- 智能提取器检测 -->
          <el-form-item label="提取器类型">
            <div class="extractor-display">
              <el-tag style="display: flex;" v-if="taskForm.extractorType" type="success" size="large" class="extractor-tag">
                <el-icon style="margin-right: 5px"><Check /></el-icon>
                {{ getExtractorTypeName(taskForm.extractorType) }}
              </el-tag>
              <el-tag v-else type="info" size="large" class="extractor-tag">
                <el-icon style="margin-right: 5px"><Clock /></el-icon>
                未检测
              </el-tag>
              <span class="extractor-hint">
                系统将自动检测并选择最适合的提取器类型
              </span>
            </div>
          </el-form-item>

          <!-- AI筛选描述 -->
          <el-form-item label="AI筛选描述">
            <el-input
              v-model="taskForm.aiFilterDescription"
              size="small"
              type="textarea"
              :rows="3"
              placeholder="可选：描述您希望抓取的文章特征，系统将自动筛选符合条件的文章&#10;例如：&#10;- 只抓取与AI技术相关的文章&#10;- 只抓取2024年发布的内容&#10;- 只抓取包含代码示例的技术文章&#10;留空则抓取所有文章"
              maxlength="500"
              show-word-limit
              clearable
            />
            <div class="input-hint" style="margin-top: 8px;">
              <el-icon><InfoFilled /></el-icon>
              <span>系统会先提取文章的标题和简介，通过AI判断是否符合描述，只有符合条件的文章才会继续抓取完整内容</span>
            </div>
          </el-form-item>
        </el-form>

        <div class="step-actions">
          <el-button size="small" @click="createTaskStep = 0">
            <el-icon style="margin-right: 5px"><ArrowLeft /></el-icon>
            上一步
          </el-button>
          <el-button size="small" @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" size="small" @click="createTaskStep = 2" class="next-button">
            下一步
            <el-icon style="margin-left: 5px"><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 步骤3：确认创建 -->
      <div v-if="createTaskStep === 2" class="step-content">
        <el-descriptions :column="2" border class="confirm-descriptions">
          <el-descriptions-item label="任务名称" :span="2">
            <el-tag type="primary" size="large">{{ taskForm.name }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数据源类型">
            <el-tag :type="taskForm.sourceType === 'http' ? 'success' : 'warning'">
              {{ taskForm.sourceType === 'http' ? 'HTTP网页' : 'API接口' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="URL数量">
            <el-tag type="info">{{ getUrlList().length }} 个</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="提取器类型" :span="2">
            <el-tag type="success" size="large">
              {{ getExtractorTypeName(taskForm.extractorType) || '未设置' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="AI筛选描述" :span="2" v-if="taskForm.aiFilterDescription">
            <el-tag type="warning" size="large">
              {{ taskForm.aiFilterDescription }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="AI筛选描述" :span="2" v-else>
            <span style="color: #909399">未设置（将抓取所有文章）</span>
          </el-descriptions-item>
          <el-descriptions-item label="URL列表" :span="2">
            <div class="url-list-preview">
              <el-tag
                v-for="(url, index) in getUrlList()"
                :key="url"
                :type="index < 3 ? 'primary' : 'info'"
                style="margin: 3px; display: block; text-align: left"
                effect="plain"
              >
                {{ url }}
              </el-tag>
              <div v-if="getUrlList().length > 3" class="more-urls-hint">
                还有 {{ getUrlList().length - 3 }} 个URL...
              </div>
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <div class="step-actions">
          <el-button size="small" @click="createTaskStep = 1">
            <el-icon style="margin-right: 5px"><ArrowLeft /></el-icon>
            上一步
          </el-button>
          <el-button size="small" @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" size="small" @click="createTask" :loading="creating" class="confirm-button">
            <el-icon style="margin-right: 5px"><Check /></el-icon>
            确认创建并启动
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 编辑任务对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑抓取任务"
      width="800px"
    >
      <el-form :model="editForm" label-width="120px">
        <el-form-item label="任务名称" required>
          <el-input v-model="editForm.name" placeholder="请输入任务名称" size="small" />
        </el-form-item>
        
        <el-form-item label="数据源类型" required>
          <el-radio-group v-model="editForm.sourceType">
            <el-radio label="http">HTTP网页</el-radio>
            <el-radio label="api">API接口</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="URL列表" required>
          <el-input
            v-model="editForm.urls"
            type="textarea"
            size="small"
            :rows="5"
            placeholder="每行一个URL"
          />
        </el-form-item>

        <el-form-item label="提取器类型">
          <el-tag type="info" size="large">
            {{ getExtractorTypeName(editForm.extractorType) || '未设置' }}
          </el-tag>
          <div style="font-size: 12px; color: #909399; margin-top: 5px">
            提取器类型由系统自动检测，如需修改请重新创建任务
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button size="small" @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" size="small" @click="updateTask">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="任务详情"
      width="85%"
      @close="closeDetailDialog"
    >
      <el-descriptions :column="2" border v-if="currentTask">
        <el-descriptions-item label="任务ID">{{ currentTask.task_id }}</el-descriptions-item>
        <el-descriptions-item label="任务名称">{{ currentTask.task_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentTask.status)">
            {{ currentTask.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="数据条数">{{ currentTask.items_count }}</el-descriptions-item>
        <el-descriptions-item label="错误数">{{ currentTask.errors_count }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatDateTime(currentTask.started_at) }}</el-descriptions-item>
        <el-descriptions-item label="完成时间">{{ formatDateTime(currentTask.completed_at) || '未完成' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(currentTask.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="任务配置" :span="2">
          <pre>{{ JSON.stringify(currentTask.task_config, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>

      <el-tabs v-model="activeTab" style="margin-top: 20px" @tab-change="onDetailTabChange">
        <el-tab-pane label="实时进度" name="progress">
          <div v-if="currentProgress">
            <el-descriptions :column="2" border style="margin-bottom: 20px">
              <el-descriptions-item label="任务ID">{{ currentTask.task_id }}</el-descriptions-item>
              <el-descriptions-item label="任务名称">{{ currentTask.task_name }}</el-descriptions-item>
              <el-descriptions-item label="当前阶段">
                <el-tag type="info">{{ currentProgress.current_stage || '未知' }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="进度">
                <el-progress
                  :percentage="currentProgress.progress_percentage || 0"
                  :status="currentTask.status === 'completed' ? 'success' : currentTask.status === 'failed' ? 'exception' : undefined"
                />
              </el-descriptions-item>
              <el-descriptions-item label="已抓取数据">{{ currentProgress.items_count || 0 }} 条</el-descriptions-item>
              <el-descriptions-item label="错误数">
                <el-tag v-if="currentProgress.errors_count > 0" type="danger">
                  {{ currentProgress.errors_count }}
                </el-tag>
                <span v-else>0</span>
              </el-descriptions-item>
              <el-descriptions-item label="最新消息" :span="2">
                <div style="color: #606266; font-size: 14px">
                  {{ currentProgress.latest_message || '暂无消息' }}
                </div>
              </el-descriptions-item>
            </el-descriptions>

            <!-- 进度日志 -->
            <el-divider>进度日志</el-divider>
            <div style="max-height: 400px; overflow-y: auto">
              <el-timeline v-if="currentProgress.progress_logs && currentProgress.progress_logs.length > 0">
                <el-timeline-item
                  v-for="(log, index) in currentProgress.progress_logs"
                  :key="index"
                  :timestamp="log.created_at"
                  type="primary"
                >
                  <el-card class="progress-log-card">
                    <div class="log-header">
                      <el-tag type="info" size="small">{{ log.stage }}</el-tag>
                    </div>
                    <div class="log-message">{{ log.message }}</div>
                    <div v-if="extractTitleFromMessage(log.message)" class="log-title">
                      <el-icon class="title-icon"><Document /></el-icon>
                      <span class="title-text">{{ extractTitleFromMessage(log.message) }}</span>
                    </div>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
              <el-empty v-else description="暂无进度日志" />
            </div>
          </div>
          <div v-else>
            <el-skeleton :rows="5" animated />
          </div>
        </el-tab-pane>
        <el-tab-pane label="抓取的文章" name="data">
          <div v-if="taskDataLoading" style="text-align: center; padding: 40px">
            <el-skeleton :rows="5" animated />
          </div>
          <div v-else-if="taskData.length === 0" style="text-align: center; padding: 40px">
            <el-empty description="暂无抓取数据" />
          </div>
          <el-table 
            v-else
            :data="taskData" 
            style="width: 100%"
            max-height="600"
            stripe
          >
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
                  style="color: #909399; text-decoration: none"
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
            <el-table-column prop="extracted_at" label="提取时间" width="180" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  size="small"
                  @click="viewArticleDetail(row)"
                >
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <el-pagination
            v-if="articlePagination.total > 0"
            v-model:current-page="articlePagination.page"
            v-model:page-size="articlePagination.per_page"
            :total="articlePagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleArticleSizeChange"
            @current-change="handleArticlePageChange"
            style="margin-top: 20px; justify-content: flex-end"
          />
        </el-tab-pane>
        <el-tab-pane label="执行日志" name="logs">
          <el-timeline>
            <el-timeline-item
              v-for="log in taskLogs"
              :key="log.id"
              :timestamp="log.created_at"
              :type="getLogType(log.level)"
            >
              <el-card>
                <p><strong>{{ log.stage }}</strong></p>
                <p>{{ log.message }}</p>
                <p v-if="log.error_message" style="color: #f56c6c">
                  {{ log.error_message }}
                </p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

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
        <el-descriptions-item label="提取时间">{{ currentArticle.extracted_at }}</el-descriptions-item>
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
  </el-config-provider>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Delete, InfoFilled, Search, Document, Warning, MagicStick, Edit, QuestionFilled, Check, Link, ArrowRight, ArrowLeft, Clock, Star, Select } from '@element-plus/icons-vue'
import api from '../api/index'

const loading = ref(false)
const creating = ref(false)
const tasks = ref([])
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const showArticleDetailDialog = ref(false)
const currentTask = ref(null)
const taskData = ref([])
const taskDataLoading = ref(false)
const taskLogs = ref([])
const activeTab = ref('data')
const retryingTaskId = ref(null)
const currentProgress = ref(null)
const progressPollingTimer = ref(null)
const currentArticle = ref(null)

const articlePagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

// 实时进度跟踪
const taskProgress = ref({})  // { task_id: { progress_percentage, current_stage, items_count } }
const progressPollingIntervals = ref({})  // 存储轮询定时器

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

// 搜索表单
const searchForm = reactive({
  keyword: '',
  status: ''
})

// 统计信息
const statistics = ref({
  total: 0,
  running: 0,
  completed: 0,
  failed: 0
})

const taskForm = reactive({
  name: '',
  sourceType: 'http',
  urls: '',
  extractorType: 'css',
  urlSource: 'ai', // 'ai' 或 'manual'
  topic: '',
  selectedSites: [],
  urlDisplay: '',
  aiFilterDescription: '' // AI筛选描述
})

const createTaskStep = ref(0)
const recommendingSites = ref(false)
const recommendedSites = ref([])

const analyzingExtractor = ref(false)
const extractorAnalysis = ref(null)
const activeCollapse = ref([]) // 控制折叠面板

// URL来源改变时的处理
const onUrlSourceChange = () => {
  if (taskForm.urlSource === 'manual') {
    taskForm.selectedSites = []
    taskForm.topic = ''
  } else {
    taskForm.urls = ''
  }
}

// 获取URL列表
const getUrlList = () => {
  if (taskForm.urlSource === 'ai') {
    return taskForm.selectedSites
  } else {
    return taskForm.urls.split('\n').filter(url => url.trim())
  }
}

// 进入下一步
const goToNextStep = () => {
  if (createTaskStep.value === 0) {
    // 准备URL显示
    const urls = getUrlList()
    taskForm.urlDisplay = urls.join('\n')
    
    // 如果没有任务名称，自动生成
    if (!taskForm.name) {
      if (taskForm.urlSource === 'ai' && taskForm.topic) {
        taskForm.name = `抓取主题：${taskForm.topic}`
      } else {
        taskForm.name = `抓取任务 ${new Date().toLocaleString()}`
      }
    }
    
    createTaskStep.value = 1
  }
}

// AI推荐网站
const handleGetRecommendedSites = async () => {
  if (!taskForm.topic.trim()) {
    ElMessage.warning('请输入抓取主题')
    return
  }

  recommendingSites.value = true
  try {
    const response = await api.post('/ai/recommend/sites', {
      topic: taskForm.topic
    })
    
    recommendedSites.value = response.sites || []
    
    if (recommendedSites.value.length === 0) {
      ElMessage.warning('未找到相关网站，请尝试其他主题')
    } else {
      ElMessage.success(`找到 ${recommendedSites.value.length} 个推荐网站`)
    }
  } catch (error) {
    ElMessage.error('获取推荐网站失败: ' + error.message)
  } finally {
    recommendingSites.value = false
  }
}

// 智能检测提取器
const analyzeExtractor = async () => {
  const urls = getUrlList()
  if (urls.length === 0) {
    ElMessage.warning('请先输入至少一个URL')
    return
  }
  
  const firstUrl = urls[0].trim()
  if (!firstUrl.startsWith('http://') && !firstUrl.startsWith('https://')) {
    ElMessage.warning('请输入有效的URL（以http://或https://开头）')
    return
  }
  
  analyzingExtractor.value = true
  try {
    const response = await api.post('/extractor/analyze', {
      url: firstUrl
    })
    
    extractorAnalysis.value = response
    // 自动应用推荐结果
    if (response.recommended_type) {
      taskForm.extractorType = response.recommended_type
      ElMessage.success(`已自动选择${getExtractorTypeName(response.recommended_type)}提取器`)
    }
  } catch (error) {
    ElMessage.error('分析失败: ' + error.message)
    extractorAnalysis.value = null
    // 如果检测失败，使用默认的CSS选择器
    taskForm.extractorType = 'css'
  } finally {
    analyzingExtractor.value = false
  }
}

// 获取提取器类型名称
const getExtractorTypeName = (type) => {
  const names = {
    'css': 'CSS选择器',
    'xpath': 'XPath',
    'regex': '正则表达式'
  }
  return names[type] || type
}

const editForm = reactive({
  name: '',
  sourceType: 'http',
  urls: '',
  extractorType: 'css',
  taskId: ''
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

const getStatusText = (status) => {
  const texts = {
    'pending': '待执行',
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败'
  }
  return texts[status] || status
}

const getTaskProgress = (taskId) => {
  return taskProgress.value[taskId]?.progress_percentage || 0
}

const getTaskItemsCount = (taskId) => {
  return taskProgress.value[taskId]?.items_count
}

const getLogType = (level) => {
  const types = {
    'INFO': 'primary',
    'WARNING': 'warning',
    'ERROR': 'danger'
  }
  return types[level] || 'primary'
}

const extractTitleFromMessage = (message) => {
  if (!message) return ''
  // 从消息中提取"正在抓取: xxx"部分
  const match = message.match(/正在抓取:\s*(.+?)(?:\s*\||$)/)
  return match ? match[1].trim() : ''
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page
    }
    
    // 添加搜索条件
    if (searchForm.keyword) {
      params.keyword = searchForm.keyword
    }
    
    if (searchForm.status) {
      params.status = searchForm.status
    }
    
    const response = await api.get('/tasks', { params })
    
    tasks.value = response.list || []
    pagination.total = response.total || 0
    
    // 计算统计信息
    statistics.value = {
      total: response.total || 0,
      running: tasks.value.filter(t => t.status === 'running').length,
      completed: tasks.value.filter(t => t.status === 'completed').length,
      failed: tasks.value.filter(t => t.status === 'failed').length
    }
    
    // 检查运行中的任务，启动进度轮询
    tasks.value.forEach(task => {
      if (task.status === 'running') {
        startProgressPolling(task.task_id)
      } else {
        stopProgressPolling(task.task_id)
      }
    })
  } catch (error) {
    ElMessage.error('获取任务列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchTasks()
}

// 重置
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.status = ''
  handleSearch()
}

const startProgressPolling = (taskId) => {
  // 如果已经在轮询，跳过
  if (progressPollingIntervals.value[taskId]) {
    return
  }
  
  // 立即获取一次进度
  fetchTaskProgress(taskId)
  
  // 每2秒轮询一次进度
  progressPollingIntervals.value[taskId] = setInterval(() => {
    fetchTaskProgress(taskId)
  }, 2000)
}

const stopProgressPolling = (taskId) => {
  if (progressPollingIntervals.value[taskId]) {
    clearInterval(progressPollingIntervals.value[taskId])
    delete progressPollingIntervals.value[taskId]
  }
  // 清理进度数据
  if (taskProgress.value[taskId]) {
    delete taskProgress.value[taskId]
  }
}

const fetchTaskProgress = async (taskId) => {
  try {
    const response = await api.get(`/tasks/${taskId}/progress`)
    const progress = response
    
    // 更新进度数据
    taskProgress.value[taskId] = {
      progress_percentage: progress.progress_percentage || 0,
      current_stage: progress.current_stage,
      items_count: progress.items_count || 0,
      errors_count: progress.errors_count || 0,
      latest_message: progress.latest_message,
      progress_logs: progress.progress_logs || []
    }
    
    // 如果正在查看详情对话框，更新当前进度
    if (showDetailDialog.value && currentTask.value?.task_id === taskId) {
      currentProgress.value = taskProgress.value[taskId]
    }
    
    // 如果任务已完成或失败，停止轮询
    if (progress.status !== 'running') {
      stopProgressPolling(taskId)
      if (progressPollingTimer.value) {
        clearInterval(progressPollingTimer.value)
        progressPollingTimer.value = null
      }
    }
  } catch (error) {
    // 如果任务不存在或已完成，停止轮询
    stopProgressPolling(taskId)
    if (progressPollingTimer.value) {
      clearInterval(progressPollingTimer.value)
      progressPollingTimer.value = null
    }
  }
}

const createTask = async () => {
  const urls = getUrlList()
  if (urls.length === 0) {
    ElMessage.warning('请至少输入一个URL')
    return
  }

  if (!taskForm.name) {
    ElMessage.warning('请输入任务名称')
    return
  }

  // 如果没有检测到提取器类型，使用默认的CSS选择器
  if (!taskForm.extractorType) {
    taskForm.extractorType = 'css'
    ElMessage.info('未检测到提取器类型，使用默认的CSS选择器')
  }

  creating.value = true
  try {
    // 根据提取器类型构建不同的字段配置
    let extractorFields = {}
    
    if (taskForm.extractorType === 'css') {
      // CSS选择器配置
      extractorFields = {
        container: 'body',
        fields: {
          title: { selector: 'title', attr: 'text' },
          content: { selector: 'body', attr: 'text' }
        }
      }
    } else if (taskForm.extractorType === 'xpath') {
      // XPath配置
      extractorFields = {
        container: '//body',
        fields: {
          title: { xpath: '//title/text()', attr: 'text' },
          content: { xpath: '//body//text()', attr: 'text' }
        }
      }
    } else if (taskForm.extractorType === 'regex') {
      // 正则表达式配置
      extractorFields = {
        fields: {
          title: { pattern: '<title>(.+?)</title>' },
          content: { pattern: '<body[^>]*>(.+?)</body>' }
        }
      }
    }
    
    const taskConfig = {
      name: taskForm.name,
      source: {
        type: taskForm.sourceType,
        urls: urls
      },
      parser: {
        type: taskForm.sourceType === 'http' ? 'html' : 'json'
      },
      extractor: {
        type: taskForm.extractorType,
        fields: extractorFields
      },
      transformer: {
        pipeline: [{ type: 'data' }]
      },
      output: {
        type: 'database',
        output_type: 'mysql'
      },
      ai_filter_description: taskForm.aiFilterDescription || '' // 添加AI筛选描述
    }

    await api.post('/tasks', taskConfig)
    
    ElMessage.success('任务创建成功')
    showCreateDialog.value = false
    
    // 重置表单
    createTaskStep.value = 0
    taskForm.name = ''
    taskForm.urls = ''
    taskForm.topic = ''
    taskForm.selectedSites = []
    taskForm.urlDisplay = ''
    taskForm.urlSource = 'ai'
    taskForm.extractorType = 'css'
    taskForm.aiFilterDescription = ''
    recommendedSites.value = []
    extractorAnalysis.value = null
    
    fetchTasks()
  } catch (error) {
    ElMessage.error('创建任务失败: ' + error.message)
  } finally {
    creating.value = false
  }
}

const viewTaskDetail = async (task) => {
  currentTask.value = task
  showDetailDialog.value = true
  activeTab.value = 'progress'  // 默认显示实时进度
  
  // 重置分页
  articlePagination.page = 1
  
  // 立即获取进度、日志和数据
  await Promise.all([
    fetchTaskProgress(task.task_id),
    fetchTaskLogs(task.task_id),
    fetchTaskData(task.task_id)
  ])
  
  // 如果任务正在运行，启动进度轮询
  if (task.status === 'running') {
    if (progressPollingTimer.value) {
      clearInterval(progressPollingTimer.value)
    }
    progressPollingTimer.value = setInterval(async () => {
      if (currentTask.value && currentTask.value.task_id === task.task_id) {
        await fetchTaskProgress(task.task_id)
      }
    }, 2000)
  }
}

const fetchTaskData = async (taskId) => {
  taskDataLoading.value = true
  try {
    const response = await api.get(`/tasks/${taskId}/data`, {
      params: {
        page: articlePagination.page,
        per_page: articlePagination.per_page
      }
    })
    const dataResponse = response.data || response
    taskData.value = dataResponse.list || []
    articlePagination.total = dataResponse.total || 0
  } catch (error) {
    ElMessage.error('获取任务数据失败: ' + error.message)
    taskData.value = []
    articlePagination.total = 0
  } finally {
    taskDataLoading.value = false
  }
}

const viewArticleDetail = (article) => {
  currentArticle.value = article
  showArticleDetailDialog.value = true
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

const handleArticleSizeChange = (size) => {
  articlePagination.per_page = size
  articlePagination.page = 1
  if (currentTask.value) {
    fetchTaskData(currentTask.value.task_id)
  }
}

const handleArticlePageChange = (page) => {
  articlePagination.page = page
  if (currentTask.value) {
    fetchTaskData(currentTask.value.task_id)
  }
}

const viewTaskLogs = async (task) => {
  currentTask.value = task
  showDetailDialog.value = true
  activeTab.value = 'logs'

  // 获取任务日志
  try {
    const logsResponse = await api.get(`/tasks/${task.task_id}/logs`)
    taskLogs.value = logsResponse || []
  } catch (error) {
    ElMessage.error('获取任务日志失败: ' + error.message)
  }
}

const onDetailTabChange = (tabName) => {
  if (tabName === 'logs' && currentTask.value && taskLogs.value.length === 0) {
    // 切换到日志标签页时，如果还没有加载日志，则加载
    fetchTaskLogs(currentTask.value.task_id)
  } else if (tabName === 'data' && currentTask.value && taskData.value.length === 0) {
    // 切换到数据标签页时，如果还没有加载数据，则加载
    fetchTaskData(currentTask.value.task_id)
  }
}

const fetchTaskLogs = async (taskId) => {
  try {
    const logsResponse = await api.get(`/tasks/${taskId}/logs`)
    taskLogs.value = logsResponse || []
  } catch (error) {
    console.error('获取任务日志失败:', error)
    taskLogs.value = []
  }
}


const handleSizeChange = (size) => {
  pagination.per_page = size
  pagination.page = 1
  fetchTasks()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchTasks()
}

const closeDetailDialog = () => {
  showDetailDialog.value = false
  
  // 清理轮询定时器
  if (progressPollingTimer.value) {
    clearInterval(progressPollingTimer.value)
    progressPollingTimer.value = null
  }
  
  // 清理当前进度数据
  if (currentTask.value) {
    stopProgressPolling(currentTask.value.task_id)
  }
  
  currentProgress.value = null
  taskLogs.value = []
  taskData.value = []
  activeTab.value = 'progress'
}

const handleRetryTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要重试任务 "${task.task_name}" 吗？`,
      '确认重试',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    retryingTaskId.value = task.task_id
    await api.post(`/tasks/${task.task_id}/retry`)
    ElMessage.success('任务重试已启动')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重试任务失败: ' + error.message)
    }
  } finally {
    retryingTaskId.value = null
  }
}

const handleDeleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.task_name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/tasks/${task.task_id}`)
    ElMessage.success('任务删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除任务失败: ' + error.message)
    }
  }
}

const handleEditTask = async (task) => {
  currentTask.value = task
  
  // 解析任务配置
  const config = task.task_config || {}
  const source = config.source || {}
  const extractor = config.extractor || {}
  
  editForm.taskId = task.task_id
  editForm.name = task.task_name || ''
  editForm.sourceType = source.type || 'http'
  editForm.extractorType = extractor.type || 'css'
  
  // 提取URLs
  const urls = source.urls || []
  editForm.urls = urls.join('\n')
  
  showEditDialog.value = true
}

const updateTask = async () => {
  if (!editForm.name || !editForm.urls) {
    ElMessage.warning('请填写完整信息')
    return
  }

  const urls = editForm.urls.split('\n').filter(url => url.trim())
  if (urls.length === 0) {
    ElMessage.warning('请至少输入一个URL')
    return
  }

  try {
    // 根据提取器类型构建不同的字段配置
    let extractorFields = {}
    
    if (editForm.extractorType === 'css') {
      // CSS选择器配置
      extractorFields = {
        container: 'body',
        fields: {
          title: { selector: 'title', attr: 'text' },
          content: { selector: 'body', attr: 'text' }
        }
      }
    } else if (editForm.extractorType === 'xpath') {
      // XPath配置
      extractorFields = {
        container: '//body',
        fields: {
          title: { xpath: '//title/text()', attr: 'text' },
          content: { xpath: '//body//text()', attr: 'text' }
        }
      }
    } else if (editForm.extractorType === 'regex') {
      // 正则表达式配置
      extractorFields = {
        fields: {
          title: { pattern: '<title>(.+?)</title>' },
          content: { pattern: '<body[^>]*>(.+?)</body>' }
        }
      }
    }
    
    const updateData = {
      name: editForm.name,
      source: {
        type: editForm.sourceType,
        urls: urls
      },
      parser: {
        type: editForm.sourceType === 'http' ? 'html' : 'json'
      },
      extractor: {
        type: editForm.extractorType,
        fields: extractorFields
      },
      transformer: {
        pipeline: [{ type: 'data' }]
      },
      output: {
        type: 'database',
        output_type: 'mysql'
      }
    }

    await api.put(`/tasks/${editForm.taskId}`, updateData)
    
    ElMessage.success('任务更新成功')
    showEditDialog.value = false
    fetchTasks()
  } catch (error) {
    ElMessage.error('更新任务失败: ' + error.message)
  }
}

const handleDeleteAllTasks = async () => {
  if (pagination.total === 0) {
    ElMessage.warning('没有可删除的任务')
    return
  }
  
  try {
    // 二次确认，需要输入确认文字
    await ElMessageBox.prompt(
      `确定要删除所有 ${pagination.total} 个任务吗？此操作不可恢复！\n\n注意：删除任务不会删除相关的文章数据。\n\n请输入 "删除全部" 以确认：`,
      '确认一键删除全部',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        inputPlaceholder: '请输入 "删除全部"',
        inputValidator: (value) => {
          if (value !== '删除全部') {
            return '输入不正确，请输入 "删除全部"'
          }
          return true
        }
      }
    )
    
    await api.delete('/tasks/all')
    ElMessage.success(`成功删除所有 ${pagination.total} 个任务`)
    pagination.page = 1
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('一键删除失败: ' + error.message)
    }
  }
}

onMounted(() => {
  fetchTasks()
})

// 组件卸载时清理所有轮询
onUnmounted(() => {
  Object.keys(progressPollingIntervals.value).forEach(taskId => {
    stopProgressPolling(taskId)
  })
})
</script>

<style scoped>
.task-management {
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
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
}

/* 创建任务对话框样式优化 */
.create-task-dialog :deep(.el-dialog__body) {
  padding: 20px 30px;
}

.task-steps {
  margin-bottom: 30px;
  padding: 0 20px;
}

.step-content {
  min-height: 400px;
  padding: 0 10px;
}

.create-task-form {
  margin-top: 20px;
}

.url-source-item {
  margin-bottom: 25px;
}

.url-source-item :deep(.el-radio-group) {
  width: 100%;
  display: flex;
  gap: 10px;
}

.url-source-item :deep(.el-radio-button) {
  flex: 1;
}

.url-source-item :deep(.el-radio-button__inner) {
  width: 100%;
  padding: 12px 20px;
  font-size: 14px;
}

.ai-recommend-section,
.manual-input-section {
  margin-top: 20px;
  padding: 0;
}

.topic-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.topic-form-item {
  margin-bottom: 0;
}

.topic-input :deep(.el-textarea__inner),
.urls-input :deep(.el-textarea__inner) {
  font-size: 14px;
  line-height: 1.6;
}

.topic-hint-row {
  margin-top: 8px;
  display: flex;
  align-items: center;
}

.guidance-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #409eff;
}

.guidance-link .rotate-icon {
  transform: rotate(90deg);
  transition: transform 0.3s;
}

.input-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 5px;
}

.action-area {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-top: 20px;
}

.action-hint-alert {
  flex: 1;
  border: none;
}

.action-hint-alert :deep(.el-alert__content) {
  padding: 0;
}

.hint-content {
  flex: 1;
}

.hint-main {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
  margin-bottom: 4px;
}

.hint-sub {
  font-size: 12px;
  color: #909399;
}

.hint-sub kbd {
  display: inline-block;
  padding: 2px 6px;
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 11px;
  color: #606266;
  margin: 0 2px;
}

.recommend-button-large {
  padding: 12px 32px;
  font-size: 15px;
  font-weight: 500;
  height: auto;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
  white-space: nowrap;
}

.guidance-collapse {
  margin-top: 15px;
  border: none;
}

.guidance-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
  font-weight: 500;
  font-size: 14px;
}

.guidance-content {
  padding: 15px 0;
}

.guidance-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.guidance-item {
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s;
}

.guidance-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  transform: translateY(-2px);
}

.guidance-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.guidance-icon {
  color: #67c23a;
  font-size: 18px;
}

.guidance-item strong {
  color: #303133;
  font-size: 14px;
}

.guidance-item p {
  margin: 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}

.guidance-examples {
  margin-top: 20px;
  padding: 15px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 8px;
  border: 1px solid #bae6fd;
}

.examples-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #0369a1;
  font-size: 14px;
}

.examples-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.example-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background-color: #fff;
  border-radius: 6px;
  font-size: 13px;
  color: #303133;
  line-height: 1.6;
}

.example-icon {
  color: #67c23a;
  font-size: 16px;
  margin-top: 2px;
  flex-shrink: 0;
}


.recommended-sites-section {
  margin-top: 25px;
  padding: 20px;
  background-color: #fafafa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.header-icon {
  font-size: 24px;
  color: #409eff;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-tag {
  margin-left: 8px;
}

.select-all-btn {
  white-space: nowrap;
}

.sites-list {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 8px;
}

.sites-list::-webkit-scrollbar {
  width: 6px;
}

.sites-list::-webkit-scrollbar-track {
  background: #f5f7fa;
  border-radius: 3px;
}

.sites-list::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.sites-list::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

.sites-checkbox-group {
  width: 100%;
}

.site-card {
  margin-bottom: 10px;
  border-radius: 8px;
  transition: all 0.3s;
  overflow: visible;
  width: 100%;
  display: block;
}

.site-card:hover {
  transform: translateX(2px);
}

.site-card.site-selected .site-info {
  border-color: #67c23a;
  background-color: #f0f9ff;
}

.site-checkbox {
  width: 100%;
  padding: 0;
  margin: 0;
  display: flex;
  align-items: flex-start;
  height: fit-content;
}

.site-checkbox :deep(.el-checkbox__input) {
  margin-top: 2px;
  flex-shrink: 0;
}

.site-checkbox :deep(.el-checkbox__label) {
  width: 100%;
  padding-left: 8px;
  margin-left: 0;
  display: block;
  line-height: normal;
}

.site-info {
  padding: 12px 14px;
  background-color: #fff;
  border-radius: 8px;
  border: 2px solid #e4e7ed;
  transition: all 0.3s;
  position: relative;
  min-height: 75px;
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
}

.site-card:hover .site-info {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.site-url-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  flex: 1;
  min-height: 0;
}

.site-url-text {
  flex: 1;
  font-size: 13px;
  color: #303133;
  word-break: break-all;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  line-height: 1.5;
  min-width: 0;
  overflow-wrap: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.site-link {
  flex-shrink: 0;
  padding: 4px 6px;
  opacity: 0.5;
  transition: opacity 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.site-card:hover .site-link {
  opacity: 1;
}

.site-reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  border-left: 3px solid #409eff;
  margin-top: auto;
  flex-shrink: 0;
}

.reason-icon {
  color: #409eff;
  font-size: 15px;
  margin-top: 1px;
  flex-shrink: 0;
}

.reason-text {
  flex: 1;
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
  font-weight: 400;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.extractor-action {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.action-hint {
  font-size: 12px;
  color: #909399;
  flex: 1;
}

.extractor-alert {
  margin-top: 12px;
}

.extractor-display {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 6px;

}
.extractor-display .el-tag__content {
     display: flex;
}
.extractor-tag {
  font-size: 14px;
  padding: 8px 16px;
}

.extractor-hint {
  font-size: 12px;
  color: #909399;
}

.url-display {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.step-actions {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.next-button,
.confirm-button {
  padding: 10px 24px;
  font-size: 14px;
}

.confirm-descriptions {
  margin-top: 20px;
}

.url-list-preview {
  max-height: 250px;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 6px;
}

.more-urls-hint {
  margin-top: 8px;
  text-align: center;
  color: #909399;
  font-size: 12px;
}

/* 进度日志样式 */
.progress-log-card {
  margin-bottom: 8px;
}

.log-header {
  margin-bottom: 8px;
}

.log-message {
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.log-title {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-left: 3px solid #409eff;
  border-radius: 4px;
  margin-top: 8px;
}

.title-icon {
  color: #409eff;
  font-size: 16px;
  flex-shrink: 0;
}

.title-text {
  color: #303133;
  font-weight: 500;
  font-size: 13px;
  flex: 1;
  word-break: break-word;
}
</style>
