import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';
import os from 'os';

// 获取临时目录路径
const tempDir = path.join(os.tmpdir(), 'handwrite-app');

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const file = searchParams.get('file');
  
  if (!file) {
    return NextResponse.json({ error: '文件参数缺失' }, { status: 400 });
  }
  
  try {
    const filePath = path.join(tempDir, file);
    
    // 检查文件是否存在
    if (!fs.existsSync(filePath)) {
      console.error('请求的G代码文件不存在:', filePath);
      return NextResponse.json({ error: '文件不存在' }, { status: 404 });
    }
    
    // 读取文件内容
    let fileBuffer;
    try {
      fileBuffer = fs.readFileSync(filePath);
    } catch (readError) {
      console.error('读取G代码文件失败:', readError);
      return NextResponse.json({ error: '读取文件失败' }, { status: 500 });
    }
    
    // 返回文件作为下载
    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': `attachment; filename="${path.basename(file)}"`,
        'Cache-Control': 'public, max-age=3600'
      }
    });
  } catch (error) {
    console.error('获取G代码文件时出错:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : '获取G代码文件失败' },
      { status: 500 }
    );
  }
}
