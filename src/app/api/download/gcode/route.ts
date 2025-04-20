import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';
import os from 'os';

// 使用与generate路由相同的临时目录
const tempDir = path.join(os.tmpdir(), 'handwrite-app');

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const file = searchParams.get('file');
  
  if (!file) {
    return NextResponse.json({ error: '文件参数缺失' }, { status: 400 });
  }
  
  try {
    const filePath = path.join(tempDir, file);
    
    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: '文件不存在' }, { status: 404 });
    }
    
    const fileBuffer = fs.readFileSync(filePath);
    const fileName = path.basename(file);
    
    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': 'text/x-gcode',
        'Content-Disposition': `attachment; filename="${fileName}"`,
        'Cache-Control': 'public, max-age=3600'
      }
    });
  } catch (error) {
    console.error('下载G代码文件时出错:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : '下载G代码文件失败' },
      { status: 500 }
    );
  }
}
