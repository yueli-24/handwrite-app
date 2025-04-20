# 手写文字生成器 - 增强错误处理文档

本文档详细说明了手写文字生成器应用中增强的错误处理和调试功能，特别是针对Vercel环境中的Python处理失败问题。

## 问题背景

在Vercel部署后，应用在生成预览时出现以下错误：

```
Python API返回错误: Python处理失败:
```

这个错误信息过于简略，无法提供足够的信息来诊断和解决问题。

## 增强的错误处理方案

我们实施了全面的错误处理增强方案，涵盖了应用的三个关键层面：

### 1. Python API端点增强

在`api/python/generate.py`文件中：

- **详细的环境信息记录**：
  ```python
  log_debug("===== 开始处理请求 =====")
  log_debug(f"Python版本: {sys.version}")
  log_debug(f"当前工作目录: {os.getcwd()}")
  log_debug(f"目录内容: {os.listdir('.')}")
  ```

- **请求对象属性记录**：
  ```python
  request_attrs = [attr for attr in dir(request) if not attr.startswith('_')]
  log_debug(f"请求对象属性: {request_attrs}")
  ```

- **多种请求体获取方式**：
  ```python
  # 方式1: 直接访问body属性
  if hasattr(request, 'body'):
      body = request.body
  
  # 方式2: 尝试使用read方法
  elif hasattr(request, 'read') and callable(request.read):
      body = request.read()
  
  # 方式3: 尝试使用json方法
  elif hasattr(request, 'json') and callable(request.json):
      try:
          body = request.json()
      except Exception as json_err:
          log_debug(f"request.json()方法失败: {str(json_err)}")
  ```

- **详细的错误响应**：
  ```python
  return {
      "statusCode": 500,
      "body": json.dumps({
          "error": f"处理请求时出错: {str(e)}",
          "trace": traceback.format_exc()
      }),
      "headers": {"Content-Type": "application/json"}
  }
  ```

### 2. Node.js API路由增强

在`src/app/api/generate/route.ts`文件中：

- **错误信息传递**：
  ```typescript
  if (!pythonResponse.ok) {
      const errorText = await pythonResponse.text();
      let errorMessage = 'Python处理失败';
      let errorTrace = '';
      
      try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.error || errorMessage;
          errorTrace = errorData.trace || '';
          
          console.error('Python API返回错误:', errorMessage);
          console.error('Python API错误详情:', errorTrace);
          
          // 返回完整的错误信息，包括trace
          return NextResponse.json({ 
              error: errorMessage, 
              trace: errorTrace 
          }, { status: 500 });
      } catch (e) {
          // 处理无法解析的错误响应
      }
  }
  ```

### 3. 前端错误处理增强

在`src/lib/hooks/use-preview-generator.ts`文件中：

- **详细的错误显示**：
  ```typescript
  if (!response.ok) {
      // 显示详细的错误信息，包括trace
      const errorMessage = data.error || '生成预览失败';
      const errorTrace = data.trace || '无详细错误信息';
      console.error('API错误详情:', errorMessage);
      console.error('错误跟踪:', errorTrace);
      throw new Error(`${errorMessage}\n详细信息: ${errorTrace}`);
  }
  ```

- **错误堆栈显示**：
  ```typescript
  catch (err) {
      console.error('预览生成错误:', err);
      // 显示完整的错误信息，包括堆栈跟踪
      const errorMessage = err instanceof Error ? err.message : '生成预览时发生未知错误';
      const errorStack = err instanceof Error && err.stack ? `\n堆栈: ${err.stack}` : '';
      setError(`${errorMessage}${errorStack}`);
  }
  ```

## 调试流程

当遇到Python处理失败问题时，可以按照以下流程进行调试：

1. **检查前端错误信息**：
   - 查看应用界面上显示的错误信息，包括详细的错误跟踪
   - 打开浏览器控制台，查看更多日志信息

2. **检查Vercel函数日志**：
   - 在Vercel仪表板中，转到项目的"Functions"选项卡
   - 查找相关函数的日志，特别是Python API函数
   - 查看详细的环境信息和错误跟踪

3. **分析错误原因**：
   - 根据错误跟踪信息，确定错误发生的位置和原因
   - 常见问题包括：请求格式不正确、Python环境问题、文件路径问题等

4. **解决方案**：
   - 根据具体错误类型，采取相应的解决方案
   - 可能需要调整代码、更新配置或修改部署设置

## 常见错误及解决方案

### 1. 请求体获取失败

**错误信息**：
```
获取或解析请求体时出错: 'NoneType' object has no attribute 'decode'
```

**解决方案**：
- 检查请求格式是否正确
- 确保Content-Type设置为application/json
- 尝试使用不同的请求体获取方式

### 2. 字体文件找不到

**错误信息**：
```
生成预览时出错: cannot open resource
```

**解决方案**：
- 确保字体文件已上传到正确位置
- 检查字体文件路径是否正确
- 尝试使用默认字体作为备选

### 3. Python环境问题

**错误信息**：
```
ModuleNotFoundError: No module named 'PIL'
```

**解决方案**：
- 确保Vercel环境中安装了所有必要的Python依赖
- 在vercel.json中正确配置Python运行时
- 考虑使用requirements.txt文件指定依赖

## 结论

通过实施这些增强的错误处理和调试功能，我们大大提高了应用的可靠性和可维护性。当出现问题时，用户和开发者可以获得详细的错误信息，快速定位和解决问题。

这些改进不仅解决了当前的Python处理失败问题，还为未来可能出现的问题提供了强大的调试工具。
