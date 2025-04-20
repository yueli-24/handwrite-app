import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const page = searchParams.get('page');
    const dir = searchParams.get('dir');
    
    if (!page || !dir) {
      return NextResponse.json({ error: '缺少必要参数' }, { status: 400 });
    }
    
    // 构建G代码文件路径
    const filePath = path.join(dir, `page_${page.padStart(3, '0')}.gcode`);
    
    try {
      // 读取文件内容
      const fileContent = await fs.readFile(filePath, 'utf-8');
      
      // 设置响应头，使浏览器将响应视为下载文件
      const headers = new Headers();
      headers.set('Content-Type', 'application/octet-stream');
      headers.set('Content-Disposition', `attachment; filename="page_${page.padStart(3, '0')}.gcode"`);
      
      return new NextResponse(fileContent, {
        status: 200,
        headers
      });
    } catch (error) {
      console.error('File read error:', error);
      return NextResponse.json({ error: '文件不存在或无法读取' }, { status: 404 });
    }
  } catch (error) {
    console.error('Download API error:', error);
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
