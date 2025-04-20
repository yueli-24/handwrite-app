import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
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
    
    // 创建唯一的会话ID
    const sessionId = Date.now().toString();
    const sessionDir = path.join(tempDir, sessionId);
    
    // 添加错误处理，确保目录创建成功
    try {
      fs.mkdirSync(sessionDir, { recursive: true });
    } catch (dirError) {
      console.error('创建会话目录失败:', dirError);
      return NextResponse.json({ error: '创建临时目录失败' }, { status: 500 });
    }
    
    // 创建输入文本文件
    const inputTextPath = path.join(sessionDir, 'input_text.txt');
    try {
      fs.writeFileSync(inputTextPath, text);
    } catch (fileError) {
      console.error('写入输入文件失败:', fileError);
      return NextResponse.json({ error: '创建输入文件失败' }, { status: 500 });
    }
    
    // 获取Python脚本路径
    const pythonScriptPath = path.join(process.cwd(), 'src', 'lib', 'python', 'handwrite.py');
    
    // 检查Python脚本是否存在
    if (!fs.existsSync(pythonScriptPath)) {
      console.error('Python脚本不存在:', pythonScriptPath);
      return NextResponse.json({ error: 'Python脚本文件不存在' }, { status: 500 });
    }
    
    // 获取字体路径
    const fontPath = path.join(process.cwd(), 'public', 'fonts', 'しょかきさらり行体.ttf');
    
    // 检查字体文件是否存在
    if (!fs.existsSync(fontPath)) {
      console.error('字体文件不存在:', fontPath);
      return NextResponse.json({ error: '字体文件不存在' }, { status: 500 });
    }
    
    // 准备命令行参数
    const args = [
      pythonScriptPath,
      '--input', inputTextPath,
      '--output-dir', sessionDir,
      '--font-size', fontSize.toString(),
      '--margin-top', marginTop.toString(),
      '--margin-bottom', marginBottom.toString(),
      '--margin-left', marginLeft.toString(),
      '--margin-right', marginRight.toString(),
      '--paper-size', paperSize,
      '--font', fontPath,
      '--preview'
    ];
    
    console.log('执行Python命令:', 'python3', args.join(' '));
    
    // 执行Python脚本
    const result = await new Promise((resolve, reject) => {
      const process = spawn('python3', args);
      
      let stdout = '';
      let stderr = '';
      
      process.stdout.on('data', (data) => {
        stdout += data.toString();
        console.log('Python stdout:', data.toString());
      });
      
      process.stderr.on('data', (data) => {
        stderr += data.toString();
        console.error('Python stderr:', data.toString());
      });
      
      process.on('error', (error) => {
        console.error('启动Python进程失败:', error);
        reject(new Error(`启动Python进程失败: ${error.message}`));
      });
      
      process.on('close', (code) => {
        console.log(`Python进程退出，退出码: ${code}`);
        if (code !== 0) {
          reject(new Error(`Python脚本执行失败 (退出码 ${code}): ${stderr}`));
          return;
        }
        
        resolve(stdout);
      });
    });
    
    // 检查会话目录是否存在
    if (!fs.existsSync(sessionDir)) {
      console.error('会话目录不存在:', sessionDir);
      return NextResponse.json({ error: '生成文件失败' }, { status: 500 });
    }
    
    // 读取生成的文件
    let files;
    try {
      files = fs.readdirSync(sessionDir);
      console.log('生成的文件:', files);
    } catch (readError) {
      console.error('读取生成的文件失败:', readError);
      return NextResponse.json({ error: '读取生成的文件失败' }, { status: 500 });
    }
    
    const previewFiles = files.filter(file => file.includes('_preview.png'));
    const gcodeFiles = files.filter(file => file.endsWith('.gcode') && !file.includes('_preview'));
    
    // 检查是否有生成的文件
    if (previewFiles.length === 0 || gcodeFiles.length === 0) {
      console.error('没有生成预览文件或G代码文件');
      return NextResponse.json({ error: '生成文件失败，没有找到预览图像或G代码文件' }, { status: 500 });
    }
    
    // 排序文件
    previewFiles.sort();
    gcodeFiles.sort();
    
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
