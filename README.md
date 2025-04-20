# 手写文字生成器

这是一个基于Next.js和Python的Web应用程序，可以将文本转换为模拟手写效果的G代码和预览图像。

## 功能特点

- 支持中文和其他文字的书写
- 模拟自然手写效果
  - 文字大小可调
  - 随机的文字间距
  - 垂直方向的抖动效果
  - 行间距自动调整
- 自动分页处理
- 支持A4、A5和B5纸张布局
- 生成预览图像
- 生成G代码文件

## 技术栈

- 前端：Next.js、React、TypeScript、TailwindCSS、Zustand
- 后端：Next.js API Routes、Python
- 依赖库：numpy、opencv-python、Pillow、scikit-image、svgwrite

## 本地开发

### 前提条件

- Node.js 18+
- Python 3.8+
- npm 或 yarn

### 安装步骤

1. 克隆仓库

```bash
git clone <repository-url>
cd handwrite-app
```

2. 安装前端依赖

```bash
npm install
# 或
yarn install
```

3. 安装Python依赖

```bash
pip install numpy opencv-python Pillow scikit-image svgwrite
```

4. 启动开发服务器

```bash
npm run dev
# 或
yarn dev
```

5. 打开浏览器访问 http://localhost:3000

## 部署到Vercel

### 自动部署

1. Fork这个仓库到你的GitHub账户
2. 在Vercel上创建一个新项目
3. 导入你fork的仓库
4. 添加以下环境变量：
   - `PYTHON_ENABLED`: `true`
5. 点击部署

### 手动部署

1. 安装Vercel CLI

```bash
npm install -g vercel
```

2. 登录Vercel

```bash
vercel login
```

3. 部署项目

```bash
vercel
```

## 使用说明

1. 在文本输入框中输入要转换的文字，或上传TXT文件
2. 调整字体大小、页边距和纸张规格
3. 点击"生成手写效果"按钮
4. 查看预览图像
5. 下载生成的G代码文件

## 项目结构

```
.
├── public/                  # 静态资源
│   └── fonts/               # 字体文件
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── api/             # API路由
│   │   │   ├── download/    # G代码下载API
│   │   │   ├── generate/    # 生成预览和G代码API
│   │   │   └── status/      # 状态检查API
│   │   ├── layout.tsx       # 布局组件
│   │   └── page.tsx         # 主页面
│   ├── components/          # React组件
│   │   ├── download/        # 下载相关组件
│   │   ├── preview/         # 预览相关组件
│   │   ├── settings/        # 设置相关组件
│   │   ├── text-input/      # 文本输入组件
│   │   └── ui/              # UI组件
│   └── lib/                 # 工具库
│       ├── hooks/           # React钩子
│       ├── python/          # Python脚本
│       ├── store/           # 状态管理
│       └── utils/           # 工具函数
├── .eslintrc.json          # ESLint配置
├── .gitignore              # Git忽略文件
├── next.config.js          # Next.js配置
├── package.json            # 项目依赖
├── postcss.config.js       # PostCSS配置
├── tailwind.config.ts      # Tailwind配置
├── tsconfig.json           # TypeScript配置
└── vercel.json             # Vercel配置
```

## 许可证

MIT
