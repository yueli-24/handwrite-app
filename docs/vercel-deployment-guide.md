# 手写文字生成器 - Vercel部署完整指南

本文档提供了将手写文字生成器应用部署到Vercel平台的详细步骤和最佳实践。

## 前提条件

- GitHub、GitLab或Bitbucket账号
- Vercel账号（可使用GitHub账号登录）
- 已修复的项目代码（包含Python API修复）

## 部署步骤

### 1. 准备代码仓库

1. 创建一个新的GitHub仓库
   - 登录GitHub账号
   - 点击右上角"+"图标，选择"New repository"
   - 填写仓库名称（例如"handwrite-app"）
   - 选择公开或私有仓库
   - 点击"Create repository"

2. 上传项目代码
   ```bash
   # 初始化本地Git仓库
   git init
   
   # 添加所有文件
   git add .
   
   # 提交更改
   git commit -m "Initial commit"
   
   # 添加远程仓库
   git remote add origin https://github.com/your-username/handwrite-app.git
   
   # 推送代码
   git push -u origin main
   ```

### 2. 在Vercel上部署

1. 登录Vercel平台
   - 访问 [https://vercel.com](https://vercel.com)
   - 使用GitHub账号或其他方式登录

2. 导入项目
   - 点击"Add New..."按钮，然后选择"Project"
   - 选择包含手写文字生成器代码的GitHub仓库
   - 如果没有看到您的仓库，可能需要点击"Configure GitHub App"进行授权

3. 配置项目
   - **框架预设**：选择"Next.js"
   - **根目录**：保持默认（项目根目录）
   - **构建命令**：`npm run build`（默认）
   - **输出目录**：`.next`（默认）

4. 环境变量设置（重要）
   - 点击"Environment Variables"部分
   - 添加以下环境变量：
     - 名称：`PYTHON_ENABLED`
     - 值：`true`

5. 部署项目
   - 确认所有设置无误后，点击"Deploy"按钮
   - 等待部署完成（通常需要1-2分钟）

### 3. 验证部署

1. 访问部署URL
   - 部署完成后，Vercel会提供一个域名（例如`handwrite-app.vercel.app`）
   - 点击提供的链接访问应用

2. 测试功能
   - 输入一些文字
   - 调整参数设置
   - 点击"刷新预览"按钮，确认预览图像生成正常
   - 测试G代码下载功能

### 4. 故障排除

如果遇到部署问题，请检查以下几点：

1. **构建失败**
   - 查看Vercel提供的构建日志
   - 确保所有依赖项在`package.json`中正确列出
   - 验证项目结构符合Next.js标准

2. **Python API错误**
   - 确认环境变量`PYTHON_ENABLED=true`已设置
   - 检查`vercel.json`文件是否存在且格式正确
   - 验证`api/python/generate.py`文件路径正确

3. **预览生成失败**
   - 检查浏览器控制台错误信息
   - 查看Vercel函数日志（在Vercel仪表板中的"Functions"选项卡）
   - 确认字体文件已正确包含在部署中

## 高级配置

### 自定义域名

1. 在Vercel项目设置中，点击"Domains"选项卡
2. 添加您的自定义域名
3. 按照Vercel提供的说明配置DNS记录

### 性能优化

1. **启用ISR（增量静态再生成）**
   - 对于频繁访问但不常更改的页面，考虑使用Next.js的ISR功能

2. **配置缓存策略**
   - 在`vercel.json`中添加缓存规则：
     ```json
     {
       "headers": [
         {
           "source": "/static/(.*)",
           "headers": [
             { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
           ]
         }
       ]
     }
     ```

### 监控与分析

1. 在Vercel仪表板中启用Analytics功能
2. 集成第三方分析工具（如Google Analytics）

## 持续部署

Vercel支持持续部署，每当您推送新代码到GitHub仓库时，应用将自动重新部署：

1. 在本地修改代码
   ```bash
   git add .
   git commit -m "Update feature XYZ"
   git push origin main
   ```

2. Vercel将自动检测更改并重新部署
3. 在Vercel仪表板中监控部署状态

## 团队协作

如果您在团队中工作：

1. 在Vercel中创建团队
2. 邀请团队成员
3. 配置权限和部署审批流程

## 安全最佳实践

1. **环境变量**
   - 敏感信息应始终使用环境变量存储
   - 不要在代码中硬编码任何密钥或凭证

2. **API限制**
   - 考虑实施速率限制以防止API滥用
   - 添加基本的请求验证

3. **定期更新**
   - 保持依赖项更新以修复安全漏洞
   - 使用`npm audit`检查安全问题

## 常见问题解答

**Q: 为什么我的Python API返回500错误？**  
A: 最常见的原因是Vercel环境中Python处理器配置不正确。确保`vercel.json`文件格式正确，并且环境变量`PYTHON_ENABLED=true`已设置。

**Q: 如何调试Vercel函数？**  
A: 在Vercel仪表板中，转到您的项目，然后点击"Functions"选项卡。您可以在那里查看函数日志和性能指标。

**Q: 如何在本地测试Vercel部署配置？**  
A: 安装Vercel CLI（`npm i -g vercel`），然后运行`vercel dev`在本地模拟Vercel环境。

**Q: 部署后找不到字体文件怎么办？**  
A: 确保字体文件位于`public/fonts/`目录中，并且在代码中使用正确的路径引用它。

## 联系与支持

如果您在部署过程中遇到任何问题，请通过以下方式联系：

- 电子邮件：yue.work24@gmail.com

---

文档最后更新：2025年4月20日
