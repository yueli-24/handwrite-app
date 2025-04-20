# 手写文字生成网页应用项目结构

## 技术栈

### 前端
- Next.js 14 (React框架)
- TypeScript
- Tailwind CSS (样式框架)
- shadcn/ui (UI组件库)
- React Dropzone (文件上传)
- React Hook Form (表单处理)
- Zustand (状态管理)

### 后端
- Next.js API Routes (API路由)
- Python (处理核心逻辑)
- OpenCV, NumPy, PIL (图像处理)
- svgwrite (SVG生成)

## 项目结构

```
handwrite-app/
├── public/                    # 静态资源
│   ├── fonts/                 # 字体文件
│   │   └── shoukaki-sarari.ttf  # 手写字体
│   └── images/                # 图片资源
│
├── src/                       # 源代码
│   ├── app/                   # Next.js App Router
│   │   ├── api/               # API路由
│   │   │   ├── generate/      # 生成G代码和预览图API
│   │   │   │   └── route.ts   # 处理生成请求
│   │   │   └── upload/        # 文件上传API
│   │   │       └── route.ts   # 处理文件上传
│   │   ├── page.tsx           # 主页面
│   │   ├── layout.tsx         # 应用布局
│   │   └── globals.css        # 全局样式
│   │
│   ├── components/            # React组件
│   │   ├── ui/                # 基础UI组件
│   │   ├── text-input/        # 文字输入组件
│   │   │   ├── text-area.tsx  # 文本区域组件
│   │   │   └── file-upload.tsx # 文件上传组件
│   │   ├── settings/          # 设置组件
│   │   │   ├── font-size.tsx  # 字体大小设置
│   │   │   ├── margin.tsx     # 页边距设置
│   │   │   └── paper-size.tsx # 纸张规格设置
│   │   ├── preview/           # 预览组件
│   │   │   └── image-preview.tsx # 图片预览组件
│   │   └── download/          # 下载组件
│   │       └── gcode-download.tsx # G代码下载按钮
│   │
│   ├── lib/                   # 工具函数和库
│   │   ├── python/            # Python脚本
│   │   │   └── handwrite.py   # 手写文字生成核心逻辑
│   │   ├── utils/             # 工具函数
│   │   │   ├── api.ts         # API调用函数
│   │   │   └── file-helpers.ts # 文件处理辅助函数
│   │   └── store/             # 状态管理
│   │       └── settings-store.ts # 设置状态存储
│   │
│   └── types/                 # TypeScript类型定义
│       └── index.ts           # 类型定义文件
│
├── .env                       # 环境变量
├── .gitignore                 # Git忽略文件
├── next.config.js             # Next.js配置
├── package.json               # 项目依赖
├── postcss.config.js          # PostCSS配置
├── tailwind.config.js         # Tailwind CSS配置
└── tsconfig.json              # TypeScript配置
```

## 功能模块设计

### 1. 文字输入/上传模块
- 文本区域：直接输入文字
- 文件上传：支持上传TXT文件
- 实时预览：输入文字后自动更新预览

### 2. 参数调整模块
- 字体大小调整：滑块控制，范围4-12mm
- 页边距调整：上、下、左、右边距独立控制
- 纸张规格选择：默认A4，可扩展支持其他规格

### 3. 预览图片展示模块
- 实时预览：显示生成的手写效果预览图
- 缩放功能：支持放大查看细节
- 分页预览：支持多页文档的预览和切换

### 4. G代码下载模块
- 下载按钮：生成并下载G代码文件
- 格式选择：单文件或分页多文件
- 预览下载：可选择同时下载预览图片

## API设计

### 1. 文本处理API
- 端点：`/api/generate`
- 方法：POST
- 请求体：
  ```json
  {
    "text": "要转换的文本内容",
    "settings": {
      "fontSize": 8,
      "marginTop": 35,
      "marginBottom": 25,
      "marginLeft": 30,
      "marginRight": 30,
      "paperSize": "A4"
    }
  }
  ```
- 响应：
  ```json
  {
    "success": true,
    "previewUrls": ["data:image/png;base64,..."],
    "gcodeUrls": ["/api/download/gcode?page=1"]
  }
  ```

### 2. 文件上传API
- 端点：`/api/upload`
- 方法：POST
- 请求：FormData包含文件
- 响应：
  ```json
  {
    "success": true,
    "text": "文件内容"
  }
  ```

### 3. 文件下载API
- 端点：`/api/download/gcode`
- 方法：GET
- 参数：page（页码）
- 响应：G代码文件下载
