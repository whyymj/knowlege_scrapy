# 前端项目说明

## 包管理器

本项目使用 **pnpm** 作为包管理器。

### 安装 pnpm

```bash
# 使用 npm 安装（推荐使用国内镜像）
npm install -g pnpm --registry=https://registry.npmmirror.com

# 或使用其他方式
curl -fsSL https://get.pnpm.io/install.sh | sh -
```

### 配置国内镜像源

项目已包含 `.npmrc` 和 `.pnpmrc` 配置文件，自动使用国内镜像源。

如需手动配置：

```bash
# 设置镜像源
pnpm config set registry https://registry.npmmirror.com

# 查看当前配置
pnpm config get registry
```

### 常用命令

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm run dev

# 构建生产版本
pnpm run build

# 预览生产构建
pnpm run preview

# 添加依赖
pnpm add <package-name>

# 添加开发依赖
pnpm add -D <package-name>

# 移除依赖
pnpm remove <package-name>
```

## 国内镜像源

### 推荐镜像源

- **npmmirror.com**（原淘宝镜像）：`https://registry.npmmirror.com`
- **腾讯云镜像**：`https://mirrors.cloud.tencent.com/npm/`
- **华为云镜像**：`https://repo.huaweicloud.com/repository/npm/`

### 切换镜像源

```bash
# 使用 npmmirror（推荐）
pnpm config set registry https://registry.npmmirror.com

# 使用腾讯云
pnpm config set registry https://mirrors.cloud.tencent.com/npm/

# 使用官方源
pnpm config set registry https://registry.npmjs.org/
```

## 项目结构

```
frontend/
├── src/              # 源代码
│   ├── views/       # 页面组件
│   ├── router/      # 路由配置
│   ├── api/         # API 接口
│   └── App.vue      # 根组件
├── .npmrc           # npm/pnpm 配置（镜像源）
├── .pnpmrc           # pnpm 配置
├── package.json      # 项目依赖
└── vite.config.js    # Vite 配置
```

## 开发说明

- 开发服务器运行在 `http://localhost:3000`
- API 代理到后端 `http://localhost:6000`
- 支持热重载（HMR）
