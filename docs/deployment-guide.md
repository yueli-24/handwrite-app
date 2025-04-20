# 部署指南

本文档提供了将手写文字生成器部署到Vercel的详细步骤。

## 前提条件

- 一个Vercel账户
- 一个GitHub账户（如果使用GitHub集成部署）

## 部署选项

### 选项1：通过GitHub集成部署（推荐）

1. Fork这个仓库到你的GitHub账户
2. 登录Vercel并点击"New Project"
3. 从"Import Git Repository"部分选择你fork的仓库
4. 配置项目：
   - 框架预设：选择"Next.js"
   - 构建命令：`npm run build`（默认）
   - 输出目录：`.next`（默认）
   - 安装命令：`npm install`（默认）
5. 环境变量：
   - 添加`PYTHON_ENABLED`环境变量，设置为`true`
6. 点击"Deploy"开始部署

### 选项2：使用Vercel CLI部署

1. 全局安装Vercel CLI：
   ```bash
   npm install -g vercel
   ```

2. 登录Vercel：
   ```bash
   vercel login
   ```

3. 在项目根目录下运行：
   ```bash
   vercel
   ```

4. 按照提示配置项目：
   - 是否要链接到现有项目？选择"No"创建新项目
   - 项目名称：输入你想要的项目名称
   - 在哪个范围内部署？选择你的个人账户或团队
   - 想要覆盖设置？选择"No"使用vercel.json中的设置

5. 部署完成后，CLI会提供一个URL，可以访问你的应用

## 部署后配置

### 自定义域名

1. 在Vercel仪表板中，选择你的项目
2. 点击"Settings" > "Domains"
3. 添加你的自定义域名并按照指示配置DNS

### 环境变量

如果需要添加或修改环境变量：

1. 在Vercel仪表板中，选择你的项目
2. 点击"Settings" > "Environment Variables"
3. 添加或修改环境变量

## 故障排除

### Python依赖问题

如果部署后遇到Python依赖相关的错误：

1. 确保`PYTHON_ENABLED`环境变量设置为`true`
2. 检查Vercel构建日志，查看是否有Python依赖安装错误
3. 如果有特定依赖问题，可以在项目根目录添加`requirements.txt`文件，列出所有Python依赖

### API路由错误

如果API路由返回500错误：

1. 检查Vercel函数日志，查看具体错误信息
2. 确保Python代码与Vercel环境兼容
3. 考虑使用Vercel的无服务器函数调试工具进行调试

## 性能优化

### 缓存策略

为了提高应用性能，可以考虑：

1. 在`next.config.js`中配置缓存策略
2. 使用Vercel的Edge缓存功能
3. 对于频繁生成的预览图像，考虑实现客户端缓存

### 资源优化

1. 确保字体文件已经优化（压缩）
2. 考虑使用Vercel的图像优化功能
3. 启用Brotli或Gzip压缩

## 监控与分析

1. 在Vercel仪表板中启用Analytics
2. 考虑集成第三方监控工具，如Sentry或LogRocket
3. 定期检查Vercel的使用统计和性能指标
