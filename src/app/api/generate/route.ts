import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';
import os from 'os';

// 创建临时目录用于存储生成的文件
const tempDir = path.join(os.tmpdir(), 'handwrite-app');
if (!fs.existsSync(tempDir)) {
  fs.mkdirSync(tempDir, { recursive: true });
}

export async function POST(request: Request) {
  try {
    // 添加错误处理，确保请求体可以被正确解析为JSON
    let data;
    try {
      data = await request.json();
    } catch (jsonError) {
      console.error('JSON解析错误:', jsonError);
      return NextResponse.json({ error: '无效的请求数据格式' }, { status: 400 });
    }
    
    const { text, fontSize, marginTop, marginBottom, marginLeft, marginRight, paperSize } = data;
    
    if (!text) {
      return NextResponse.json({ error: '文本内容不能为空' }, { status: 400 });
    }
    
    console.log('调用Python API生成预览...');
    
    try {
      // 从请求URL获取主机名，用于构建绝对URL
      const requestUrl = new URL(request.url);
      const host = requestUrl.origin;
      
      // 构建Python API的绝对URL
      const pythonApiUrl = `${host}/api/python/generate`;
      
      console.log('Python API URL:', pythonApiUrl);
      
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
      
      if (!pythonResponse.ok) {
        const errorText = await pythonResponse.text();
        let errorMessage = 'Python处理失败';
        
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.error || errorMessage;
        } catch (e) {
          errorMessage = `Python处理失败: ${errorText.substring(0, 100)}`;
        }
        
        console.error('Python API返回错误:', errorMessage);
        return NextResponse.json({ error: errorMessage }, { status: 500 });
      }
      
      const responseText = await pythonResponse.text();
      let pythonData;
      
      try {
        pythonData = JSON.parse(responseText);
      } catch (jsonError) {
        console.error('Python API响应解析错误:', jsonError, responseText.substring(0, 100));
        return NextResponse.json({ error: '无法解析Python API响应' }, { status: 500 });
      }
      
      console.log('Python API响应成功');
      
      // 创建会话目录
      const sessionId = pythonData.sessionId;
      const sessionDir = path.join(tempDir, sessionId);
      
      try {
        fs.mkdirSync(sessionDir, { recursive: true });
      } catch (dirError) {
        console.error('创建会话目录失败:', dirError);
        return NextResponse.json({ error: '创建临时目录失败' }, { status: 500 });
      }
      
      // 将base64图像保存为文件
      const previewFiles = [];
      for (let i = 0; i < pythonData.previewBase64.length; i++) {
        const previewFileName = `page_${String(i + 1).padStart(3, '0')}_preview.png`;
        const previewPath = path.join(sessionDir, previewFileName);
        
        try {
          const imgBuffer = Buffer.from(pythonData.previewBase64[i], 'base64');
          fs.writeFileSync(previewPath, imgBuffer);
          previewFiles.push(previewFileName);
        } catch (fileError) {
          console.error('保存预览图像失败:', fileError);
          return NextResponse.json({ error: '保存预览图像失败' }, { status: 500 });
        }
      }
      
      // 将G代码内容保存为文件
      const gcodeFiles = [];
      for (let i = 0; i < pythonData.gcodeContent.length; i++) {
        const gcodeFileName = `page_${String(i + 1).padStart(3, '0')}.gcode`;
        const gcodePath = path.join(sessionDir, gcodeFileName);
        
        try {
          fs.writeFileSync(gcodePath, pythonData.gcodeContent[i]);
          gcodeFiles.push(gcodeFileName);
        } catch (fileError) {
          console.error('保存G代码文件失败:', fileError);
          return NextResponse.json({ error: '保存G代码文件失败' }, { status: 500 });
        }
      }
      
      // 创建URL
      const previewUrls = previewFiles.map(file => `/api/generate?file=${sessionId}/${file}&type=preview`);
      const gcodeUrls = gcodeFiles.map(file => `/api/download/gcode?file=${sessionId}/${file}`);
      
      // 返回成功响应
      const responseData = {
        success: true,
        previewUrls,
        gcodeUrls,
        sessionId
      };
      
      console.log('API响应数据:', responseData);
      return NextResponse.json(responseData);
    } catch (pythonError) {
      console.error('调用Python API失败:', pythonError);
      return NextResponse.json(
        { error: pythonError instanceof Error ? pythonError.message : '调用Python API失败' },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('生成手写效果时出错:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : '生成手写效果失败' },
      { status: 500 }
    );
  }
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const file = searchParams.get('file');
  const type = searchParams.get('type');
  
  if (!file) {
    return NextResponse.json({ error: '文件参数缺失' }, { status: 400 });
  }
  
  try {
    const filePath = path.join(tempDir, file);
    
    // 检查文件是否存在
    if (!fs.existsSync(filePath)) {
      console.error('请求的文件不存在:', filePath);
      return NextResponse.json({ error: '文件不存在' }, { status: 404 });
    }
    
    // 读取文件内容
    let fileBuffer;
    try {
      fileBuffer = fs.readFileSync(filePath);
    } catch (readError) {
      console.error('读取文件失败:', readError);
      return NextResponse.json({ error: '读取文件失败' }, { status: 500 });
    }
    
    // 根据类型返回不同的响应
    if (type === 'preview') {
      return new NextResponse(fileBuffer, {
        headers: {
          'Content-Type': 'image/png',
          'Cache-Control': 'public, max-age=3600'
        }
      });
    } else {
      return new NextResponse(fileBuffer, {
        headers: {
          'Content-Type': 'application/octet-stream',
          'Content-Disposition': `attachment; filename="${path.basename(file)}"`,
          'Cache-Control': 'public, max-age=3600'
        }
      });
    }
  } catch (error) {
    console.error('获取文件时出错:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : '获取文件失败' },
      { status: 500 }
    );
  }
}
