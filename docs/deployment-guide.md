# 手写文字生成器 - 部署指南

本文档提供了将手写文字生成器应用部署到生产环境的详细说明。

## 部署选项

手写文字生成器可以通过以下几种方式部署：

1. **Vercel 部署**（推荐）：最简单的方法，支持自动部署和持续集成
2. **自托管服务器**：适用于需要完全控制的场景
3. **Docker 容器**：适用于容器化环境

## Vercel 部署（推荐）

### 前提条件

- GitHub、GitLab 或 Bitbucket 账号
- Vercel 账号（可使用 GitHub 账号登录）

### 部署步骤

1. **准备代码仓库**
   - 创建一个新的 GitHub/GitLab/Bitbucket 仓库
   - 将项目代码上传到仓库

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repository-url>
   git push -u origin main
   ```

2. **连接 Vercel**
   - 登录 [Vercel 平台](https://vercel.com)
   - 点击 "New Project" 按钮
   - 选择并导入您的代码仓库

3. **配置项目**
   - 框架预设：选择 "Next.js"
   - 根目录：保持默认（项目根目录）
   - 构建命令：`npm run build`（默认）
   - 输出目录：`.next`（默认）

4. **环境变量设置**
   - 点击 "Environment Variables" 部分
   - 添加以下环境变量：
     - 名称：`PYTHON_ENABLED`
     - 值：`true`

5. **部署项目**
   - 点击 "Deploy" 按钮
   - 等待部署完成（通常需要 1-2 分钟）

6. **验证部署**
   - 部署完成后，Vercel 会提供一个域名（例如 `your-project.vercel.app`）
   - 访问该域名，确认应用正常运行

### 自定义域名（可选）

1. 在 Vercel 项目设置中，点击 "Domains" 选项卡
2. 添加您的自定义域名
3. 按照 Vercel 提供的说明配置 DNS 记录

### 持续部署

Vercel 会自动监控您的代码仓库，当有新的提交时自动重新部署。

## 自托管服务器部署

### 前提条件

- Node.js 18.x 或更高版本
- Python 3.x
- npm 或 yarn
- 具有 SSH 访问权限的 Linux 服务器（推荐 Ubuntu 20.04 或更高版本）

### 部署步骤

1. **准备服务器**

   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade -y
   
   # 安装 Node.js 和 npm
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt install -y nodejs
   
   # 安装 Python 和依赖
   sudo apt install -y python3 python3-pip
   pip3 install numpy opencv-python Pillow scikit-image svgwrite
   
   # 安装 PM2 进程管理器
   sudo npm install -g pm2
   ```

2. **上传项目文件**

   ```bash
   # 从本地上传项目文件到服务器
   scp -r ./handwrite-app-complete user@your-server:/path/to/handwrite-app
   
   # 或者直接在服务器上克隆仓库
   git clone <your-repository-url> /path/to/handwrite-app
   ```

3. **安装依赖并构建项目**

   ```bash
   cd /path/to/handwrite-app
   npm install
   npm run build
   ```

4. **使用 PM2 启动应用**

   ```bash
   # 创建 PM2 配置文件
   cat > ecosystem.config.js << EOL
   module.exports = {
     apps: [{
       name: 'handwrite-app',
       script: 'node_modules/next/dist/bin/next',
       args: 'start',
       instances: 'max',
       autorestart: true,
       watch: false,
       max_memory_restart: '1G',
       env: {
         NODE_ENV: 'production',
         PORT: 3000
       }
     }]
   };
   EOL
   
   # 启动应用
   pm2 start ecosystem.config.js
   
   # 设置开机自启
   pm2 startup
   pm2 save
   ```

5. **配置 Nginx 反向代理**

   ```bash
   # 安装 Nginx
   sudo apt install -y nginx
   
   # 创建 Nginx 配置文件
   sudo nano /etc/nginx/sites-available/handwrite-app
   ```

   添加以下配置：

   ```nginx
   server {
     listen 80;
     server_name your-domain.com;
   
     location / {
       proxy_pass http://localhost:3000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection 'upgrade';
       proxy_set_header Host $host;
       proxy_cache_bypass $http_upgrade;
     }
   }
   ```

   启用配置并重启 Nginx：

   ```bash
   sudo ln -s /etc/nginx/sites-available/handwrite-app /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **配置 SSL（推荐）**

   ```bash
   # 安装 Certbot
   sudo apt install -y certbot python3-certbot-nginx
   
   # 获取并配置 SSL 证书
   sudo certbot --nginx -d your-domain.com
   ```

## Docker 部署

### 前提条件

- Docker 和 Docker Compose 已安装

### 部署步骤

1. **创建 Dockerfile**

   在项目根目录创建 `Dockerfile`：

   ```dockerfile
   # 构建阶段
   FROM node:18-alpine AS builder
   WORKDIR /app
   
   # 安装依赖
   COPY package*.json ./
   RUN npm install
   
   # 复制源代码
   COPY . .
   
   # 构建应用
   RUN npm run build
   
   # 运行阶段
   FROM node:18-alpine
   WORKDIR /app
   
   # 安装 Python 和依赖
   RUN apk add --no-cache python3 py3-pip
   RUN pip3 install numpy opencv-python Pillow scikit-image svgwrite
   
   # 从构建阶段复制文件
   COPY --from=builder /app/package*.json ./
   COPY --from=builder /app/next.config.js ./
   COPY --from=builder /app/public ./public
   COPY --from=builder /app/.next ./.next
   COPY --from=builder /app/node_modules ./node_modules
   COPY --from=builder /app/src/lib/python ./src/lib/python
   
   # 设置环境变量
   ENV NODE_ENV production
   ENV PYTHON_ENABLED true
   
   # 暴露端口
   EXPOSE 3000
   
   # 启动应用
   CMD ["npm", "start"]
   ```

2. **创建 Docker Compose 配置**

   创建 `docker-compose.yml`：

   ```yaml
   version: '3'
   
   services:
     handwrite-app:
       build: .
       ports:
         - "3000:3000"
       restart: always
       environment:
         - NODE_ENV=production
         - PYTHON_ENABLED=true
   ```

3. **构建和启动容器**

   ```bash
   docker-compose up -d --build
   ```

4. **配置反向代理（可选）**

   如果您使用 Nginx 或其他反向代理，配置方式与自托管服务器部署类似。

## 故障排除

### 常见问题

1. **Python 依赖安装失败**
   - 确保安装了正确版本的 Python（3.6+）
   - 尝试单独安装每个依赖：`pip install numpy && pip install opencv-python` 等

2. **Vercel 部署失败**
   - 检查环境变量是否正确设置
   - 查看构建日志以获取详细错误信息
   - 确保项目结构符合 Next.js 标准

3. **应用启动但无法生成预览**
   - 检查 Python 是否正确安装
   - 验证所有 Python 依赖是否已安装
   - 检查字体文件路径是否正确

4. **内存不足错误**
   - 增加服务器或容器的内存分配
   - 对于 Vercel，考虑升级到 Pro 计划以获取更多资源

### 日志查看

- **Vercel**：在项目仪表板中查看 "Deployments" 和 "Functions" 日志
- **自托管**：`pm2 logs handwrite-app`
- **Docker**：`docker-compose logs handwrite-app`

## 性能优化

1. **启用缓存**
   - 配置 Nginx 缓存静态资源
   - 使用 CDN 分发静态内容

2. **调整 Node.js 内存限制**
   - 对于大型应用，增加 Node.js 内存限制：`NODE_OPTIONS="--max-old-space-size=4096"`

3. **优化图像处理**
   - 考虑使用 WebP 格式预览图像
   - 实现图像处理的服务端缓存

## 安全考虑

1. **启用 HTTPS**
   - 始终使用 SSL/TLS 加密
   - 对于自托管，使用 Let's Encrypt 获取免费证书

2. **设置适当的 CORS 策略**
   - 限制跨域请求来源

3. **实施速率限制**
   - 防止 API 滥用和 DoS 攻击

4. **定期更新依赖**
   - 使用 `npm audit` 检查安全漏洞
   - 定期更新所有依赖包

---

如果您在部署过程中遇到任何问题，请参考项目文档或联系开发团队获取支持。
