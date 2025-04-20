# Vercel生产环境错误处理增强文档

本文档详细说明了手写文字生成器应用在Vercel生产环境中的错误处理增强方案，特别针对"Unexpected end of JSON input"错误问题。

## 问题描述

在Vercel生产环境中，应用在生成预览时出现以下错误：

```
Python处理失败: 详细信息: 无法解析错误响应: Unexpected end of JSON input 
堆栈: Error: Python处理失败: 详细信息: 无法解析错误响应: Unexpected end of JSON input 
at generatePreview (https://handwrite-app-green.vercel.app/_next/static/chunks/app/page-2681b00b013dfa52.js:1:9181)
```

这个错误表明Python后端抛出异常后没有返回合法的JSON格式，导致前端在解析时报错。

## 问题分析

通过分析错误信息，我们发现了以下关键问题：

1. **Python后端异常处理不完善**：
   - 当Python代码崩溃或出现未捕获的异常时，可能返回空字符串或HTML错误页面
   - 这导致前端在尝试解析JSON时失败，抛出"Unexpected end of JSON input"错误

2. **前端错误处理不够健壮**：
   - 前端代码假设后端始终返回有效的JSON
   - 缺乏对非JSON响应的处理机制
   - 错误信息不够详细，难以诊断问题

3. **Node.js API路由错误传递不完整**：
   - 中间层API路由没有完全传递Python API的错误详情
   - 错误日志不够详细，难以追踪问题根源

## 全面解决方案

我们实施了三层全面的错误处理增强方案：

### 1. Python API层增强

在`api/python/generate.py`文件中：

- **添加全局异常处理装饰器**：
  ```python
  def safe_handler(handler_func):
      """装饰器：确保handler函数始终返回有效的JSON响应，即使发生未捕获的异常"""
      @functools.wraps(handler_func)
      def wrapper(request):
          try:
              # 调用原始handler函数
              return handler_func(request)
          except Exception as e:
              # 捕获所有未处理的异常
              error_message = f"未捕获的异常: {str(e)}"
              error_trace = traceback.format_exc()
              
              # 确保返回有效的JSON响应
              return {
                  "statusCode": 500,
                  "body": json.dumps({
                      "error": error_message,
                      "trace": error_trace
                  }),
                  "headers": {"Content-Type": "application/json"}
              }
      return wrapper
  ```

- **应用装饰器到handler函数**：
  ```python
  @safe_handler
  def handler(request):
      # 处理逻辑
  ```

- **详细的环境信息记录**：
  ```python
  log_debug(f"===== 开始处理请求 =====")
  log_debug(f"Python版本: {sys.version}")
  log_debug(f"当前工作目录: {os.getcwd()}")
  ```

### 2. Node.js API路由层增强

在`src/app/api/generate/route.ts`文件中：

- **增强错误信息传递**：
  ```typescript
  try {
    pythonData = JSON.parse(responseText);
  } catch (jsonError) {
    console.error('Python API响应解析错误:', jsonError);
    console.error('无效的JSON响应:', responseText.substring(0, 500));
    return NextResponse.json({ 
      error: '无法解析Python API响应', 
      trace: `JSON解析错误: ${jsonError instanceof Error ? jsonError.message : String(jsonError)}\n响应内容: ${responseText.substring(0, 200)}${responseText.length > 200 ? '...' : ''}`
    }, { status: 500 });
  }
  ```

- **完整的错误处理链**：
  ```typescript
  if (!pythonResponse.ok) {
    const errorText = await pythonResponse.text();
    let errorMessage = 'Python处理失败';
    let errorTrace = '';
    
    try {
      const errorData = JSON.parse(errorText);
      errorMessage = errorData.error || errorMessage;
      errorTrace = errorData.trace || '';
      
      // 返回完整的错误信息，包括trace
      return NextResponse.json({ 
        error: errorMessage, 
        trace: errorTrace 
      }, { status: 500 });
    } catch (e) {
      // 处理非JSON错误响应
    }
  }
  ```

### 3. 前端错误处理增强

在`src/lib/hooks/use-preview-generator.ts`文件中：

- **请求超时处理**：
  ```typescript
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时

  try {
    const response = await fetch('/api/generate', {
      // ...其他选项
      signal: controller.signal
    });

    clearTimeout(timeoutId); // 清除超时
  } catch (fetchError) {
    if (fetchError.name === 'AbortError') {
      throw new Error('请求超时，请稍后重试');
    }
    throw fetchError;
  }
  ```

- **健壮的响应解析**：
  ```typescript
  let responseText = '';
  try {
    responseText = await response.text();
    console.log('API响应内容长度:', responseText.length);
    console.log('API响应内容预览:', responseText.substring(0, 200) + (responseText.length > 200 ? '...' : ''));
  } catch (textError) {
    console.error('获取响应文本失败:', textError);
    throw new Error('无法读取服务器响应: ' + (textError instanceof Error ? textError.message : String(textError)));
  }
  
  if (!responseText || responseText.trim() === '') {
    console.error('服务器返回了空响应');
    throw new Error('服务器返回了空响应');
  }
  ```

- **安全的JSON解析**：
  ```typescript
  let data;
  try {
    data = JSON.parse(responseText);
  } catch (jsonError) {
    console.error('JSON解析错误:', jsonError);
    console.error('无效的JSON响应:', responseText.substring(0, 500));
    throw new Error('无法解析服务器响应，可能不是有效的JSON格式');
  }
  ```

- **灵活的数据处理**：
  ```typescript
  // 检查是否有预览数据
  if (data.previewBase64) {
    // 处理单页或多页预览
    const previewArray = Array.isArray(data.previewBase64) 
      ? data.previewBase64 
      : [data.previewBase64];
    
    setPreviewUrls(previewArray.map(base64 => `data:image/png;base64,${base64}`));
    
    // 处理G代码
    const gcodeArray = Array.isArray(data.gcodeContent) 
      ? data.gcodeContent 
      : [data.gcodeContent];
    
    setGcodeUrls(gcodeArray);
  } else if (data.previewUrls) {
    // 兼容旧版API响应格式
    setPreviewUrls(data.previewUrls);
    setGcodeUrls(data.gcodeUrls || []);
  } else {
    throw new Error('服务器响应缺少预览数据');
  }
  ```

## 错误处理流程

当出现错误时，系统会按照以下流程处理：

1. **Python API层**：
   - 捕获所有异常，包括未处理的异常
   - 生成包含错误信息和堆栈跟踪的JSON响应
   - 确保即使在崩溃情况下也返回有效的JSON

2. **Node.js API路由层**：
   - 接收Python API的响应
   - 尝试解析JSON，处理解析失败的情况
   - 传递完整的错误信息和跟踪到前端

3. **前端层**：
   - 处理请求超时和网络错误
   - 安全地解析响应文本和JSON
   - 显示详细的错误信息，包括堆栈跟踪
   - 记录完整的错误日志，便于调试

## 调试技巧

当遇到问题时，可以使用以下方法进行调试：

1. **查看浏览器控制台**：
   - 打开浏览器开发者工具（F12）
   - 查看控制台中的错误信息和日志
   - 特别注意"API响应内容预览"和"无效的JSON响应"等日志

2. **检查Vercel函数日志**：
   - 在Vercel仪表板中，转到项目的"Functions"选项卡
   - 查找相关函数的日志，特别是Python API函数
   - 查看详细的环境信息和错误跟踪

3. **测试API端点**：
   - 使用工具如Postman直接测试API端点
   - 检查原始响应内容，确认是否为有效的JSON
   - 验证错误处理机制是否正常工作

## 部署注意事项

在Vercel上部署时，请确保：

1. 使用最新的修复代码，包含所有增强的错误处理功能
2. 确认`api/python/generate.py`文件存在且格式正确
3. 确认`vercel.json`文件正确配置了Python运行时
4. 部署后，进行全面测试，确保错误处理机制正常工作

## 结论

通过实施这些全面的错误处理增强，我们解决了Vercel生产环境中的"Unexpected end of JSON input"错误问题。这些改进不仅提高了应用的稳定性和可靠性，还提供了更好的用户体验和更容易的问题诊断能力。

无论Python后端发生什么异常，系统现在都能够返回有效的JSON响应，并提供详细的错误信息，帮助开发者和用户快速定位和解决问题。
