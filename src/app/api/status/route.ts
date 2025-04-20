import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  try {
    // 简单的状态检查，确认API服务正常运行
    return NextResponse.json({
      status: 'ok',
      message: '服务正常运行',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('状态检查API错误:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : '状态检查失败' },
      { status: 500 }
    );
  }
}
