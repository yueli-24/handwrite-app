import { NextResponse } from 'next/server';
import os from 'os';
import { exec } from 'child_process';
import util from 'util';

const execPromise = util.promisify(exec);

export async function GET() {
  try {
    // 检查Python是否可用
    const pythonResult = await execPromise('python3 --version');
    const pythonVersion = pythonResult.stdout.trim();
    
    // 检查必要的Python库
    let libraryStatus = {};
    try {
      await execPromise('python3 -c "import numpy"');
      libraryStatus = { ...libraryStatus, numpy: 'available' };
    } catch (e) {
      libraryStatus = { ...libraryStatus, numpy: 'missing' };
    }
    
    try {
      await execPromise('python3 -c "import cv2"');
      libraryStatus = { ...libraryStatus, opencv: 'available' };
    } catch (e) {
      libraryStatus = { ...libraryStatus, opencv: 'missing' };
    }
    
    try {
      await execPromise('python3 -c "import PIL"');
      libraryStatus = { ...libraryStatus, pillow: 'available' };
    } catch (e) {
      libraryStatus = { ...libraryStatus, pillow: 'missing' };
    }
    
    try {
      await execPromise('python3 -c "import skimage"');
      libraryStatus = { ...libraryStatus, skimage: 'available' };
    } catch (e) {
      libraryStatus = { ...libraryStatus, skimage: 'missing' };
    }
    
    try {
      await execPromise('python3 -c "import svgwrite"');
      libraryStatus = { ...libraryStatus, svgwrite: 'available' };
    } catch (e) {
      libraryStatus = { ...libraryStatus, svgwrite: 'missing' };
    }
    
    // 获取系统信息
    const platform = os.platform();
    const release = os.release();
    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    
    return NextResponse.json({
      status: 'ok',
      system: {
        platform,
        release,
        totalMemory: totalMem,
        freeMemory: freeMem
      },
      python: {
        version: pythonVersion,
        libraries: libraryStatus
      }
    });
  } catch (error) {
    console.error('获取状态信息时出错:', error);
    return NextResponse.json(
      { 
        status: 'error',
        error: error instanceof Error ? error.message : '获取状态信息失败' 
      },
      { status: 500 }
    );
  }
}
