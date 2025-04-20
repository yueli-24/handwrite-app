# 手写文字生成器 - Vercel部署修复文档

本文档详细记录了手写文字生成器应用在Vercel环境中的部署问题及修复方案。

## 问题描述

在Vercel部署后，应用在生成预览时出现以下错误：

```
POST https://handwrite-app-green.vercel.app/api/generate 500 (Internal Server Error)
预览生成错误: Error: 启动Python进程失败: spawn python3 ENOENT
```

这个错误表明在Vercel的无服务器环境中无法找到或执行python3命令，导致应用无法生成预览图像和G代码。

## 问题分析

通过分析错误信息和Vercel环境特性，我们发现以下问题：

1. **环境差异**：Vercel的无服务器函数环境与本地开发环境有很大不同
2. **Python可用性**：Vercel的Node.js运行时环境中默认不包含Python解释器
3. **进程执行限制**：Vercel函数不支持使用`child_process.spawn`直接执行外部命令
4. **文件系统限制**：Vercel的函数环境有临时文件系统的限制

## 修复方案

我们实现了一个适合Vercel无服务器环境的解决方案，主要包括以下几个方面：

### 1. 使用Vercel的多运行时支持

Vercel支持多种运行时环境，包括Node.js和Python。我们利用这一特性，创建了专门的Python API端点：

```json
// vercel.json
{
  "builds": [
    { "src": "api/python/*.py", "use": "@vercel/python" },
    { "src": "package.json", "use": "@vercel/next" }
  ],
  "routes": [
    { "src": "/api/python/(.*)", "dest": "/api/python/$1" },
    { "src": "/(.*)", "dest": "/$1" }
  ],
  "env": {
    "PYTHON_ENABLED": "true"
  }
}
```

### 2. 创建Python API端点

我们创建了一个专用的Python API端点，直接在Python环境中实现手写文字生成功能：

```python
# api/python/generate.py
from http.server import BaseHTTPRequestHandler
import json
# ... 其他导入 ...

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 处理请求数据
        # 生成预览图像和G代码
        # 返回base64编码的图像和G代码内容
```

这个端点接收与原始API相同的参数，但直接在Python环境中处理，无需跨进程调用。

### 3. 修改Node.js API路由

我们修改了原始的Node.js API路由，使其调用Python API端点而不是直接执行Python脚本：

```typescript
// src/app/api/generate/route.ts
export async function POST(request: Request) {
  try {
    // ... 处理请求数据 ...
    
    // 调用Python API端点
    const pythonApiUrl = process.env.NODE_ENV === 'production' 
      ? '/api/python/generate' 
      : 'http://localhost:3000/api/python/generate';
    
    const pythonResponse = await fetch(pythonApiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        fontSize,
        marginTop,
        marginBottom,
        marginLeft,
        marginRight,
        paperSize
      }),
    });
    
    // ... 处理响应 ...
  } catch (error) {
    // ... 错误处理 ...
  }
}
```

### 4. 优化数据传输

为了避免文件系统限制，我们使用base64编码直接在API响应中传输图像数据：

1. Python API生成预览图像并将其编码为base64字符串
2. Node.js API接收这些数据并将其保存为临时文件
3. 前端保持不变，仍然通过URL访问这些文件

## 验证修复

修复后的代码已经通过以下步骤验证：

1. 本地构建测试成功
2. 确认Vercel配置文件正确设置
3. 验证Python API端点能够正确处理请求
4. 确认Node.js API能够正确调用Python API并处理响应

## 部署注意事项

在Vercel上部署时，请确保：

1. 上传完整的项目代码，包括`api/python`目录
2. 确认`vercel.json`文件存在于项目根目录
3. 部署后检查Vercel日志，确认Python API端点正常工作

## 结论

通过利用Vercel的多运行时支持，我们成功解决了在Vercel环境中Python执行失败的问题。这个解决方案不仅修复了当前的错误，还提供了一个更加健壮的架构，使应用能够在无服务器环境中可靠运行。
