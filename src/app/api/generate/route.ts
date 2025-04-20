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
    const data = await request.json();
    const { text, fontSize, marginTop, marginBottom, marginLeft, marginRight, paperSize } = data;
    
    if (!text) {
      return NextResponse.json({ error: '文本内容不能为空' }, { status: 400 });
    }
    
    // 创建唯一的会话ID
    const sessionId = Date.now().toString();
    const sessionDir = path.join(tempDir, sessionId);
    fs.mkdirSync(sessionDir, { recursive: true });
    
    // 创建输入文本文件
    const inputTextPath = path.join(sessionDir, 'input_text.txt');
    fs.writeFileSync(inputTextPath, text);
    
    // 获取Python脚本路径
    const pythonScriptPath = path.join(process.cwd(), 'src', 'lib', 'python', 'handwrite.py');
    
    // 获取字体路径
    const fontPath = path.join(process.cwd(), 'public', 'fonts', 'しょかきさらり行体.ttf');
    
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
    
    // 执行Python脚本
    const result = await new Promise((resolve, reject) => {
      const process = spawn('python3', args);
      
      let stdout = '';
      let stderr = '';
      
      process.stdout.on('data', (data) => {
        stdout += data.toString();
      });
      
      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });
      
      process.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python脚本执行失败: ${stderr}`));
          return;
        }
        
        resolve(stdout);
      });
    });
    
    // 读取生成的文件
    const files = fs.readdirSync(sessionDir);
    const previewFiles = files.filter(file => file.includes('_preview.png'));
    const gcodeFiles = files.filter(file => file.endsWith('.gcode') && !file.includes('_preview'));
    
    // 排序文件
    previewFiles.sort();
    gcodeFiles.sort();
    
    // 创建URL
    const previewUrls = previewFiles.map(file => `/api/generate?file=${sessionId}/${file}&type=preview`);
    const gcodeUrls = gcodeFiles.map(file => `/api/download/gcode?file=${sessionId}/${file}`);
    
    return NextResponse.json({
      success: true,
      previewUrls,
      gcodeUrls,
      sessionId
    });
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
    
    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: '文件不存在' }, { status: 404 });
    }
    
    const fileBuffer = fs.readFileSync(filePath);
    
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
