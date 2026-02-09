# 网站爬虫管理系统

一个基于 Scrapy + Vue3 + MySQL 的网站信息爬取和管理系统。

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
├── examples/               # 示例代码
│   └── run_crawlers.py     # 爬虫使用示例
├── docs/                   # 文档
│   └── 爬虫系统说明.md
├── init_db.sql             # 数据库初始化脚本
└── requirements.txt        # Python 依赖
```

## 环境要求

### 本地开发环境
- Python 3.8+
- Node.js 16+
- MySQL 5.7+ (端口 3306)

### Docker 部署环境
- Docker 20.10+
- Docker Compose 2.0+

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

### 2. 配置项目

项目使用统一的 `config.json` 配置文件管理所有配置项。

#### 配置文件说明

`config.json` 包含以下配置项：

- **database**: MySQL 数据库配置（host, port, db, user, password）
- **backend**: 后端服务配置（host, port, debug, cors_enabled）
- **frontend**: 前端服务配置（port, api_proxy）
- **scrapy**: Scrapy 爬虫配置（download_delay, concurrent_requests, user_agent 等）
- **docker**: Docker 部署配置（MySQL 密码、端口等）
- **logging**: 日志配置（level, format）

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
    "port": 3306,
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
npm install
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
- 后端 API: http://localhost:5000
- MySQL: localhost:3306

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
- 检查必要的依赖和工具
- 检查 MySQL 服务状态
- 检查端口占用情况
- 启动后端服务（端口 5000）
- 启动前端服务（端口 3000）

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

后端服务将在 `http://localhost:5000` 启动

#### 2. 启动前端服务

```bash
cd frontend
npm run dev
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

详细说明请参考：[爬虫系统说明文档](docs/爬虫系统说明.md)

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

### Web管理系统

- ✅ 网站信息爬取（标题、描述、内容、关键词等）
- ✅ MySQL 数据存储
- ✅ Web 管理界面
- ✅ 数据搜索和筛选
- ✅ 统计信息展示
- ✅ 数据详情查看
- ✅ 数据删除功能

## API 接口

- `GET /api/websites` - 获取网站列表（支持分页、搜索、筛选）
- `GET /api/websites/:id` - 获取网站详情
- `DELETE /api/websites/:id` - 删除网站记录
- `GET /api/statistics` - 获取统计信息
- `POST /api/crawl` - 启动爬取任务

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
- `MYSQL_PORT`: MySQL 端口（默认: 3306）
- `BACKEND_PORT`: 后端端口（默认: 5000）
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
