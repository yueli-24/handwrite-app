import { NextResponse } from 'next/server';
import util from 'util';
import { exec } from 'child_process';

const execPromise = util.promisify(exec);

// 安装必要的Python依赖
async function installDependencies() {
  try {
    await execPromise('pip3 install numpy opencv-python Pillow scikit-image svgwrite');
    return true;
  } catch {
    console.error('Failed to install dependencies');
    return false;
  }
}

export async function GET() {
  // 安装依赖（首次请求时）
  await installDependencies();
  
  return NextResponse.json({ status: 'API is ready' });
}
