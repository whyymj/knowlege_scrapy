FROM node:18-alpine as builder

# 安装 pnpm
RUN npm install -g pnpm --registry=https://registry.npmmirror.com

WORKDIR /app

# 配置 pnpm 使用国内镜像源
RUN pnpm config set registry https://registry.npmmirror.com

# 复制 package 文件
COPY package*.json ./
COPY .npmrc ./
COPY .pnpmrc ./

# 安装依赖
RUN pnpm install

# 复制源代码
COPY . .

# 构建应用
RUN pnpm run build

# 生产环境镜像
FROM nginx:alpine

# 复制构建产物到 nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
