# 手写文字生成器 - 项目说明文档

## 项目概述

手写文字生成器是一个基于Web的应用程序，可以将输入的文本转换为模拟手写效果的G代码和预览图像。该应用程序使用Next.js框架构建，结合了React前端和Python后端处理，提供了直观的用户界面和强大的功能。

## 功能特点

- **支持中文和其他文字的书写**：应用可以处理各种语言的文字输入
- **模拟自然手写效果**：
  - 文字大小可调整（4-12mm）
  - 随机的文字间距，增加真实感
  - 垂直方向的抖动效果，模拟手写不稳定性
  - 行间距自动调整，确保文字布局合理
- **自动分页处理**：根据纸张大小和内容长度自动分页
- **支持多种纸张规格**：A4、A5和B5纸张布局
- **可调整页边距**：上、下、左、右边距均可独立调整
- **生成预览图像**：实时查看手写效果的预览图像
- **G代码下载**：生成可用于控制绘图设备的G代码文件

## 技术栈

- **前端**：
  - Next.js 15.x
  - React 18.x
  - TypeScript
  - TailwindCSS
  - Zustand (状态管理)
  - Radix UI (组件库)
  
- **后端**：
  - Next.js API Routes
  - Python 3.x
  - 依赖库：numpy, opencv-python, Pillow, scikit-image, svgwrite

## 项目结构

```
handwrite-app/
├── public/                  # 静态资源
│   └── fonts/               # 字体文件
│       └── しょかきさらり行体.ttf  # 默认手写字体
├── src/                     # 源代码
│   ├── app/                 # Next.js App Router
│   │   ├── api/             # API路由
│   │   │   ├── generate/    # 生成预览和G代码
│   │   │   ├── download/    # 下载G代码
│   │   │   └── status/      # 系统状态检查
│   │   ├── globals.css      # 全局样式
│   │   ├── layout.tsx       # 应用布局
│   │   └── page.tsx         # 主页面
│   ├── components/          # React组件
│   │   ├── ui/              # 基础UI组件
│   │   ├── text-input/      # 文本输入组件
│   │   ├── settings/        # 设置调整组件
│   │   ├── preview/         # 预览显示组件
│   │   └── download/        # G代码下载组件
│   └── lib/                 # 工具库
│       ├── hooks/           # React钩子
│       ├── store/           # 状态管理
│       ├── utils/           # 工具函数
│       └── python/          # Python脚本
│           └── handwrite.py # 核心手写生成脚本
├── next.config.js           # Next.js配置
├── postcss.config.js        # PostCSS配置
├── tailwind.config.js       # TailwindCSS配置
├── tsconfig.json            # TypeScript配置
└── package.json             # 项目依赖
```

## 安装与运行

### 前提条件

- Node.js 18.x 或更高版本
- Python 3.x
- npm 或 yarn

### 本地开发

1. 克隆仓库或解压项目文件
   ```bash
   git clone <repository-url>
   # 或解压下载的zip文件
   ```

2. 安装Node.js依赖
   ```bash
   cd handwrite-app
   npm install
   ```

3. 安装Python依赖
   ```bash
   pip install numpy opencv-python Pillow scikit-image svgwrite
   ```

4. 启动开发服务器
   ```bash
   npm run dev
   ```

5. 访问 http://localhost:3000 查看应用

### 生产构建

1. 构建应用
   ```bash
   npm run build
   ```

2. 启动生产服务器
   ```bash
   npm start
   ```

## 部署指南

### 部署到Vercel

1. 创建GitHub/GitLab/Bitbucket仓库，上传项目代码
2. 登录Vercel平台 (https://vercel.com)
3. 点击"New Project"，导入您的代码仓库
4. 在配置页面：
   - 框架预设选择"Next.js"
   - 添加环境变量`PYTHON_ENABLED=true`
5. 点击"Deploy"按钮

### 部署到其他平台

确保部署环境满足以下条件：
- 支持Next.js应用
- 支持Python运行时
- 已安装所有必要的Python依赖

## 使用指南

### 文本输入

1. 直接在文本框中输入要转换的文字
2. 或者拖放/上传TXT文本文件

### 参数设置

1. 调整字体大小（4-12mm）
2. 设置页边距（上、下、左、右）
3. 选择纸张规格（A4、A5或B5）

### 生成预览

1. 输入文字并设置参数后，点击"刷新预览"按钮
2. 预览区域将显示手写效果的图像
3. 如果内容超过一页，可以使用页面导航按钮查看所有页面

### 下载G代码

1. 生成预览后，点击"下载G代码"按钮
2. 如果有多个页面，可以选择下载单个页面或所有页面

## 自定义与扩展

### 更换字体

1. 将新字体文件放入`public/fonts/`目录
2. 修改`src/app/layout.tsx`中的字体导入路径
3. 更新`src/app/globals.css`中的字体类名（如需要）

### 修改UI样式

1. 编辑`src/app/globals.css`调整全局样式
2. 或修改各组件文件中的TailwindCSS类名

### 调整Python脚本

1. 编辑`src/lib/python/handwrite.py`文件
2. 修改后需要重新启动应用以应用更改

## 故障排除

### 常见问题

1. **预览生成失败**
   - **Python运行时问题**
     - 检查Vercel构建日志中的Python相关错误
     - 确认`vercel.json`中的Python配置正确
     - 验证Python依赖是否正确安装
     - 检查环境变量`PYTHON_ENABLED=true`是否设置正确
   
   - **字体文件问题**
     - 确保字体文件被正确部署到`public/fonts`目录
     - 检查字体文件路径是否正确
     - 验证字体文件权限设置
     - 尝试使用绝对路径访问字体文件
   
   - **文件系统权限**
     - 确保代码使用Vercel提供的临时目录（/tmp）进行文件操作
     - 避免在非临时目录进行文件写入操作
     - 检查文件操作权限

2. **部署问题**
   - **构建失败**
     - 查看Vercel提供的构建日志
     - 确保所有依赖项在`package.json`中正确列出
     - 验证项目结构符合Next.js标准
     - 检查Python运行时配置是否正确
   
   - **Python API错误**
     - 确认环境变量`PYTHON_ENABLED=true`已设置
     - 检查`vercel.json`文件是否存在且格式正确
     - 验证`api/python/generate.py`文件路径正确
     - 检查Python依赖是否正确安装
   
   - **环境变量问题**
     - 确保所有必要的环境变量都已设置
     - 检查环境变量是否在所有环境中生效
     - 验证环境变量值是否正确

3. **字体显示问题**
   - **字体加载失败**
     - 确认字体文件路径正确
     - 检查字体文件格式是否支持
     - 尝试使用不同的字体文件
     - 验证字体文件是否被正确部署
   
   - **字体渲染问题**
     - 检查字体文件是否完整
     - 验证字体文件编码是否正确
     - 确保字体文件权限设置正确

### 调试建议

1. **日志记录**
   - 在Python代码中添加详细的日志记录
   - 使用`print`语句输出关键变量值
   - 记录文件系统操作的结果
   - 保存错误堆栈信息

2. **本地测试**
   - 使用Vercel CLI在本地测试部署
   - 模拟Vercel环境进行测试
   - 检查本地和线上环境的差异

3. **性能优化**
   - 监控Python函数的执行时间
   - 优化文件操作逻辑
   - 使用缓存减少重复计算
   - 考虑使用更高效的算法

4. **错误处理**
   - 添加适当的错误处理机制
   - 实现重试逻辑
   - 提供友好的错误提示
   - 记录详细的错误信息

### 联系支持

如果遇到无法解决的问题，请通过以下方式联系支持：

- 项目仓库：https://github.com/yueli-24/handwrite-app.git
- 电子邮件：yue.work24@gmail.com

请提供以下信息以便快速解决问题：
1. 详细的错误信息
2. 复现步骤
3. 环境信息（Vercel部署URL、构建ID等）
4. 相关日志输出

## 许可证

本项目使用MIT许可证。

## 联系方式

如有任何问题或建议，请通过以下方式联系：

- 项目仓库：https://github.com/yueli-24/handwrite-app.git
- 电子邮件：yue.work24@gmail.com

---

文档最后更新：2025年4月20日
