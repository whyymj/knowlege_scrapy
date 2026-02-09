# 通用抓取信息系统

一个配置驱动、插件化、可观测、容错的通用抓取信息系统。支持多种数据源、多种存储后端，通过配置文件即可快速创建抓取任务。

## 项目结构

```
scrapy/
├── scrapy_project/          # Scrapy 爬虫项目
│   ├── scrapy_project/
│   │   ├── spiders/         # 爬虫文件
│   │   ├── items.py         # 数据模型
│   │   ├── pipelines.py     # 数据管道（MySQL存储）
│   │   └── settings.py      # 爬虫配置
│   └── scrapy.cfg
├── backend/                  # Flask 后端 API
│   ├── app.py               # Flask 应用
│   └── requirements.txt
├── frontend/                # Vue3 前端项目
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── router/          # 路由配置
│   │   └── api/             # API 接口
│   └── package.json
├── dev.sh                   # 本地开发一键启动脚本
├── stop.sh                  # 本地开发停止服务脚本
├── docker-dev.sh            # Docker 一键启动脚本
├── docker-compose.yml       # Docker Compose 配置（开发环境）
├── docker-compose.prod.yml  # Docker Compose 配置（生产环境）
├── .env.example             # 环境变量示例文件
├── config.json              # 统一配置文件
├── utils/                   # 工具模块
│   └── config_loader.py     # 配置加载器
├── crawlers/                # 数据采集层
│   ├── base.py             # 爬虫基类
│   ├── config.py           # 爬虫配置管理
│   ├── manager.py          # 爬虫管理器
│   ├── utils.py            # 爬虫工具（代理池、去重）
│   ├── ai/                 # AI技术信息爬虫
│   │   ├── arxiv_crawler.py
│   │   ├── paperswithcode_crawler.py
│   │   ├── github_trending_crawler.py
│   │   ├── openai_blog_crawler.py
│   │   └── jiqizhixin_crawler.py
│   └── stock/              # 股市信息爬虫
│       ├── yahoo_finance_crawler.py
│       ├── tushare_crawler.py
│       ├── sina_finance_crawler.py
│       └── xueqiu_crawler.py
├── pipeline/               # 数据处理管道
│   ├── normalizer.py       # 数据标准化
│   ├── quality_monitor.py   # 数据质量监控
│   └── processor.py        # 数据处理器（整合）
├── analyzer/               # AI分析模块
│   ├── deepseek_analyzer.py  # DeepSeek API 集成
│   └── config.py           # 分析器配置
├── storage/                # 存储层
│   ├── base.py            # 存储基类和接口
│   ├── manager.py         # 统一存储管理器
│   ├── timeseries.py      # 时序数据库（InfluxDB/TimescaleDB）
│   ├── vector.py          # 向量数据库（Qdrant/Pinecone）
│   ├── document.py        # 文档数据库（MongoDB/Elasticsearch）
│   └── cache.py           # 缓存层（Redis）
├── engine/                 # 通用抓取引擎
│   ├── core.py            # 引擎核心
│   ├── config.py          # 引擎配置
│   ├── pipeline.py        # 抽象抓取管道
│   ├── registry.py        # 组件注册表
│   ├── observability.py   # 可观测性管理
│   └── fault_tolerance.py # 容错恢复管理
├── components/             # 可插拔组件层
│   ├── base.py            # 组件基类
│   ├── adapters.py        # 源适配器（HTTP/API）
│   ├── parsers.py         # 解析器（HTML/JSON）
│   ├── extractors.py      # 提取器（CSS/XPath/Regex）
│   ├── transformers.py   # 转换器（数据转换/标准化）
│   ├── outputs.py         # 输出器（数据库/文件）
│   └── validators.py      # 验证器（数据验证/质量检查）
├── ai_recommender/         # AI推荐模块
│   ├── recommender.py     # AI推荐器主类
│   ├── topic_recommender.py  # 主题推荐器
│   ├── article_analyzer.py   # 文章分析器
│   ├── selector.py        # 手动选择器
│   └── service.py         # 推荐服务（整合）
├── examples/               # 示例代码
│   ├── run_crawlers.py     # 爬虫使用示例
│   ├── test_pipeline.py    # 数据处理管道测试
│   ├── test_analyzer.py    # DeepSeek分析器测试
│   ├── test_storage.py     # 存储层测试
│   ├── test_engine.py     # 通用抓取引擎测试
│   └── test_ai_recommender.py  # AI推荐功能测试
├── docs/                   # 文档
│   ├── 爬虫系统说明.md
│   ├── 数据处理管道说明.md
│   ├── DeepSeek分析器说明.md
│   └── 存储层说明.md
├── init_db.sql             # 数据库初始化脚本
└── requirements.txt        # Python 依赖
```

## 环境要求

### 本地开发环境
- Python 3.8+
- Node.js 16+
- pnpm（前端包管理器）
- Docker（用于 MySQL 容器，脚本会自动创建）

### Docker 部署环境
- Docker 20.10+
- Docker Compose 2.0+

## 安装步骤

### 1. 安装 Python 依赖

**方式一：使用安装脚本（推荐）**

```bash
./scripts/install_deps.sh
```

**方式二：手动安装**

```bash
# 安装项目依赖（包含 Scrapy）
pip install -r requirements.txt

# 安装后端依赖（包含 Flask）
pip install -r backend/requirements.txt
```

**方式三：配置 pip 镜像源（推荐，一次配置永久使用）**

项目已包含 `pip.conf.example` 配置文件示例。安装脚本会自动配置镜像源，也可以手动配置：

**Linux/Mac:**
```bash
mkdir -p ~/.pip
cp pip.conf.example ~/.pip/pip.conf
```

**Windows:**
```bash
# 创建目录（如果不存在）
mkdir %APPDATA%\pip
# 复制配置文件
copy pip.conf.example %APPDATA%\pip\pip.ini
```

配置完成后，直接使用 `pip install` 即可自动使用国内镜像源：

```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

**方式四：临时使用镜像源**

如果不想配置，也可以临时指定镜像源：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 配置项目

项目使用统一的 `config.json` 配置文件管理所有配置项。

#### 配置文件说明

`config.json` 包含以下配置项：

- **database**: MySQL 数据库配置（host, port, db, user, password）
- **backend**: 后端服务配置（host, port, debug, cors_enabled）
- **frontend**: 前端服务配置（port, api_proxy）
- **engine**: 通用抓取引擎配置（并发数、可观测性、容错等）
- **storage**: 存储层配置（MySQL、MongoDB、Redis等）
- **pipeline**: 数据处理管道配置（质量监控阈值、标准化选项等）
- **analyzer**: AI分析器配置（DeepSeek API密钥、缓存、批处理等）

#### 配置优先级

1. **环境变量**（最高优先级）
2. **config.json**（默认配置）

环境变量会覆盖 `config.json` 中的对应配置项。

#### 修改配置

直接编辑 `config.json` 文件即可修改配置。例如修改数据库连接：

```json
{
  "database": {
    "host": "localhost",
    "port": 3308,
    "db": "scrapy_db",
    "user": "your_user",
    "password": "your_password"
  }
}
```

#### 创建数据库

创建数据库：

```sql
CREATE DATABASE scrapy_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

或者使用提供的初始化脚本：

```bash
mysql -u root -p < init_db.sql
```

### 3. 安装前端依赖

```bash
cd frontend

# 安装 pnpm（如果未安装）
npm install -g pnpm --registry=https://registry.npmmirror.com

# 配置 pnpm 使用国内镜像源
pnpm config set registry https://registry.npmmirror.com

# 安装依赖
pnpm install
```

## 使用方法

### 方式一：Docker 部署（推荐）

使用 Docker Compose 一键部署所有服务：

```bash
# 使用交互式脚本（推荐）
./docker-dev.sh

# 或直接使用 docker-compose
docker-compose up -d --build
```

访问服务：
- 前端界面: http://localhost:3000
- 后端 API: http://localhost:6000
- MySQL: localhost:3308

常用命令：
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 清理并重建（删除数据卷）
docker-compose down -v
docker-compose up -d --build
```

#### 生产环境部署

使用生产环境配置：

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑环境变量（修改密码等）
vim .env

# 使用生产配置启动
docker-compose -f docker-compose.prod.yml up -d --build
```

### 方式二：本地开发启动

使用提供的启动脚本一键启动所有服务：

```bash
./dev.sh
```

脚本会自动：
- ✅ 检查必要的依赖和工具（Python、Node.js、Docker）
- ✅ **自动创建 MySQL Docker 容器**（如果不存在）
- ✅ **自动启动 MySQL 容器**（如果已停止）
- ✅ 检查端口占用情况（6000, 3000）
- ✅ 自动安装前端依赖（如未安装）
- ✅ 启动后端服务（端口 6000）
- ✅ 启动前端服务（端口 3000）

**MySQL 容器管理**：
- 容器名称：`scrapy_mysql_local`
- 端口：`3308:3306`
- 自动重启：系统重启后自动启动
- 手动管理：`./scripts/manage_mysql.sh {create|start|stop|restart|status|remove}`

停止所有服务：

```bash
./stop.sh
```

### 方式三：手动启动

#### 1. 启动后端服务

```bash
cd backend
python app.py
```

后端服务将在 `http://localhost:6000` 启动

#### 2. 启动前端服务

```bash
cd frontend
pnpm run dev
```

前端服务将在 `http://localhost:3000` 启动

### 3. 运行爬虫

#### 方式一：通过管理界面

1. 访问 `http://localhost:3000`
2. 点击"新增爬取任务"
3. 输入要爬取的网站URL
4. 点击"开始爬取"

#### 方式二：命令行运行

```bash
cd scrapy_project
scrapy crawl website -a start_url=https://example.com
```

#### 方式三：使用数据采集层爬虫

```bash
# 运行爬虫示例
python examples/run_crawlers.py

# 或在Python代码中使用
python
>>> from crawlers import CrawlerManager, CrawlerConfig
>>> manager = CrawlerManager()
>>> results = manager.run_ai_crawlers()  # 运行AI爬虫
>>> results = manager.run_stock_crawlers()  # 运行股市爬虫
```

详细说明请参考：
- [爬虫系统说明文档](docs/爬虫系统说明.md)
- [数据处理管道说明文档](docs/数据处理管道说明.md)

## 功能特性

### 数据采集层（Crawlers）

#### AI技术信息爬虫
- ✅ **arXiv**: AI论文爬取（标题、作者、摘要）
- ✅ **PapersWithCode**: 带代码的AI论文
- ✅ **GitHub Trending**: 热门AI仓库
- ✅ **OpenAI Blog**: OpenAI官方博客
- ✅ **机器之心**: AI新闻和资讯

#### 股市信息爬虫
- ✅ **Yahoo Finance**: 股票实时行情和新闻
- ✅ **Tushare**: 中国股票市场数据
- ✅ **新浪财经**: 财经新闻
- ✅ **雪球**: 股票讨论和情绪数据

#### 核心功能
- ✅ **配置管理**: 统一的 `CrawlerConfig` 配置管理
- ✅ **爬取频率控制**: 支持自定义爬取频率
- ✅ **代理池管理**: 支持代理池轮换
- ✅ **反爬策略**: User-Agent轮换、请求延迟、重试机制
- ✅ **数据去重**: 支持URL/标题/内容哈希去重
- ✅ **定时调度**: 自动按频率运行爬虫

### 数据处理管道（Pipeline）

#### 数据标准化（DataNormalizer）
- ✅ **文本清洗**: 去除HTML标签、标准化编码
- ✅ **结构化提取**: 标题、正文、发布时间、来源统一提取
- ✅ **情感标签预标注**: 基于关键词的情感分析
- ✅ **关键实体识别**: 公司、技术、人物实体提取

#### 数据质量监控（DataQualityMonitor）
- ✅ **完整性检查**: 必需字段、内容长度验证
- ✅ **时效性验证**: 发布时间解析、数据年龄检查
- ✅ **重复检测**: 内容哈希、URL哈希、相似度检测
- ✅ **异常值检测**: 可疑模式、异常长度、时间异常检测

### AI分析模块（Analyzer）

#### DeepSeek API 集成
- ✅ **多维度分析**: 技术趋势、市场情绪、关联性分析
- ✅ **请求合并**: 自动合并相似内容批量分析
- ✅ **缓存机制**: 内存缓存，避免重复分析
- ✅ **异步处理**: 支持异步批量分析，提高吞吐量
- ✅ **错误处理**: 自动重试、降级策略

### 存储层（Storage）

#### 多数据库支持
- ✅ **时序数据库**: InfluxDB / TimescaleDB（股价、交易量等时间序列数据）
- ✅ **向量数据库**: Qdrant / Pinecone（AI论文/新闻语义检索）
- ✅ **关系数据库**: MySQL / PostgreSQL（结构化数据）
- ✅ **文档数据库**: MongoDB / Elasticsearch（非结构化文本、分析结果）
- ✅ **缓存层**: Redis（热点数据、会话状态）
- ✅ **统一管理**: StorageManager 统一管理所有存储

### 通用抓取引擎（Crawler Engine）

#### 核心特性
- ✅ **配置驱动**: 通过配置文件定义抓取任务，无需修改代码
- ✅ **插件化**: 支持自定义插件扩展功能
- ✅ **可观测性**: 完整的日志、指标、追踪系统
- ✅ **容错恢复**: 自动重试、降级、故障转移

#### 抽象抓取管道
- ✅ **请求生成**: 根据配置生成抓取请求
- ✅ **页面获取**: 下载页面内容
- ✅ **内容解析**: 解析HTML/JSON等格式
- ✅ **数据提取**: 提取结构化数据
- ✅ **数据清洗**: 清洗和标准化数据
- ✅ **结果输出**: 输出到目标存储

#### 可插拔组件层
- ✅ **源适配器**: HTTP适配器、API适配器
- ✅ **解析器**: HTML解析器、JSON解析器
- ✅ **提取器**: CSS选择器、XPath、正则表达式
- ✅ **转换器**: 数据格式转换、标准化
- ✅ **输出器**: 数据库输出、文件输出
- ✅ **验证器**: 数据完整性验证、质量检查

### AI推荐模块（AI Recommender）

#### LangChain集成
- ✅ **主题推荐**: 智能分析文章内容，推荐相关主题
- ✅ **文章分析**: 深度分析文章，提取摘要、关键要点、情感倾向等
- ✅ **手动选择**: 支持手动选择主题和文章，记录选择历史
- ✅ **推荐流程**: 完整的推荐流程，整合所有功能
- ✅ **多提供商支持**: 支持OpenAI、DeepSeek等LLM提供商

### Web管理系统

- ✅ **现代化界面**: 侧边栏导航，清晰的模块划分
- ✅ **仪表盘**: 系统概览、统计信息、快速操作
- ✅ **网站列表**: 数据查看、搜索筛选、批量操作
- ✅ **AI主题推荐**: 智能推荐、主题卡片、手动选择
- ✅ **文章分析**: AI深度分析、结果可视化展示
- ✅ **任务管理**: 任务创建、状态监控、日志查看
- ✅ **智能推荐组件**: 实时推荐、快速跳转
- ✅ **响应式设计**: 适配不同屏幕尺寸

## API 接口

### 任务管理
- `GET /api/tasks` - 获取任务列表（支持分页、状态筛选）
- `GET /api/tasks/:task_id` - 获取任务详情
- `POST /api/tasks` - 创建并启动抓取任务
- `GET /api/tasks/:task_id/data` - 获取任务数据
- `GET /api/tasks/:task_id/logs` - 获取任务日志

### 系统信息
- `GET /api/health` - 健康检查
- `GET /api/statistics` - 获取统计信息

### AI推荐接口
- `POST /api/ai/recommend/topics` - AI主题推荐
- `POST /api/ai/analyze/article` - 分析文章细节
- `POST /api/ai/select/topics` - 手动选择主题
- `POST /api/ai/select/articles` - 手动选择文章
- `GET /api/ai/selections/:user_id` - 获取用户选择记录
- `POST /api/ai/recommend/pipeline` - 完整推荐流程

## 快速开始

### 1. 安装依赖

```bash
# Python依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && pnpm install
```

### 2. 配置数据库

```bash
# 使用Docker启动MySQL
docker run -d \
  --name scrapy_mysql_local \
  -e MYSQL_ROOT_PASSWORD=root123456 \
  -e MYSQL_DATABASE=scrapy_db \
  -p 3308:3306 \
  mysql:8.0

# 初始化数据库
mysql -h localhost -P 3308 -u root -proot123456 < init_db.sql
```

### 3. 配置系统

```bash
# 复制配置示例
cp config.json.example config.json

# 编辑配置
vim config.json
```

### 4. 启动服务

```bash
# 一键启动（推荐）
./dev.sh

# 或手动启动
# 后端
cd backend && python app.py

# 前端（另一个终端）
cd frontend && pnpm run dev
```

### 5. 创建抓取任务

通过API创建任务：

```bash
curl -X POST http://localhost:6000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my_task",
    "name": "示例任务",
    "source": {
      "type": "http",
      "urls": ["https://example.com"]
    },
    "parser": {"type": "html"},
    "extractor": {
      "type": "css",
      "fields": {
        "container": "article",
        "fields": {
          "title": {"selector": "h1", "attr": "text"}
        }
      }
    },
    "output": {
      "type": "database",
      "output_type": "mysql"
    }
  }'
```

## Docker 配置说明

### 服务说明

- **mysql**: MySQL 8.0 数据库服务
- **backend**: Flask 后端 API 服务
- **frontend**: Vue3 前端服务（使用 Nginx）

### 环境变量

可以通过环境变量或 `.env` 文件配置：

- `MYSQL_ROOT_PASSWORD`: MySQL root 密码（默认: root123456）
- `MYSQL_USER`: MySQL 用户（默认: scrapy_user）
- `MYSQL_PASSWORD`: MySQL 密码（默认: scrapy_pass）
- `MYSQL_PORT`: MySQL 端口（默认: 3308）
- `BACKEND_PORT`: 后端端口（默认: 6000）
- `FRONTEND_PORT`: 前端端口（默认: 3000）

### 数据持久化

MySQL 数据存储在 Docker volume `mysql_data` 中，删除容器不会丢失数据。

## 注意事项

1. **Docker 部署**：
   - 首次运行前确保 Docker 和 Docker Compose 已安装
   - 生产环境请修改默认密码（通过 `.env` 文件）
   - 数据卷会自动创建，数据持久化存储

2. **本地开发**：
   - 首次运行前请确保 MySQL 服务已启动
   - 根据实际情况修改 `config.json` 中的数据库配置
   - 所有配置统一在 `config.json` 中管理，无需修改代码文件

3. **爬虫配置**：
   - 爬虫遵守网站的 robots.txt 规则（可在 settings.py 中修改）
   - 建议设置合理的爬取延迟，避免对目标网站造成压力
   - 支持通过环境变量配置数据库连接
