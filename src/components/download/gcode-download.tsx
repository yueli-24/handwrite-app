"use client";

import React from 'react';
import { Button } from '@/components/ui/button';
import { useClientSettingsStore } from '@/lib/store/client-store';
import { Download } from 'lucide-react';

export const GcodeDownload = () => {
  const { gcodeUrls, previewUrls } = useClientSettingsStore();
  
  const handleDownload = (url: string, index: number) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = `handwriting_page_${(index + 1).toString().padStart(3, '0')}.gcode`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  const handleDownloadAll = () => {
    gcodeUrls.forEach((url, index) => {
      setTimeout(() => {
        handleDownload(url, index);
      }, index * 500); // 每个下载间隔500毫秒，避免浏览器阻止多个下载
    });
  };
  
  if (gcodeUrls.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-4 border-2 border-dashed rounded-md">
        <Download className="h-8 w-8 text-gray-300 mb-2" />
        <p className="text-gray-400 text-center">生成预览后可下载G代码文件</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">下载G代码</h3>
      
      {gcodeUrls.length === 1 ? (
        <Button 
          onClick={() => handleDownload(gcodeUrls[0], 0)}
          className="w-full"
        >
          <Download className="h-4 w-4 mr-2" />
          下载G代码文件
        </Button>
      ) : (
        <div className="space-y-3">
          <Button 
            onClick={handleDownloadAll}
            className="w-full"
          >
            <Download className="h-4 w-4 mr-2" />
            下载所有页面 ({gcodeUrls.length} 页)
          </Button>
          
          <div className="text-sm text-gray-500 mb-2">或下载单个页面：</div>
          
          <div className="grid grid-cols-3 gap-2">
            {gcodeUrls.map((url, index) => (
              <Button 
                key={index}
                variant="outline"
                size="sm"
                onClick={() => handleDownload(url, index)}
              >
                第 {index + 1} 页
              </Button>
            ))}
          </div>
        </div>
      )}
      
      <p className="text-xs text-gray-500">
        G代码文件可用于控制绘图设备，实现手写效果的物理输出。
      </p>
    </div>
  );
};
