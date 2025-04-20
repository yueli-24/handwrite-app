"use client";

import React from 'react';
import { useClientSettingsStore } from '@/lib/store/client-store';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

export const GcodeDownload = () => {
  const { gcodeUrls } = useClientSettingsStore();
  
  if (gcodeUrls.length === 0) {
    return (
      <Button disabled className="w-full">
        <Download className="mr-2 h-4 w-4" />
        下载G代码
      </Button>
    );
  }
  
  const handleDownloadAll = () => {
    // 如果只有一个文件，直接下载
    if (gcodeUrls.length === 1) {
      window.open(gcodeUrls[0], '_blank');
      return;
    }
    
    // 如果有多个文件，创建一个隐藏的下载链接并点击
    gcodeUrls.forEach((url, index) => {
      const link = document.createElement('a');
      link.href = url;
      link.download = `page_${index + 1}.gcode`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // 添加延迟，避免浏览器阻止多个下载
      setTimeout(() => {}, 500);
    });
  };
  
  return (
    <div className="space-y-4">
      <Button 
        onClick={handleDownloadAll}
        className="w-full"
      >
        <Download className="mr-2 h-4 w-4" />
        下载G代码 ({gcodeUrls.length} 个文件)
      </Button>
      
      {gcodeUrls.length > 1 && (
        <div className="grid grid-cols-2 gap-2">
          {gcodeUrls.map((url, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              onClick={() => window.open(url, '_blank')}
            >
              下载第 {index + 1} 页
            </Button>
          ))}
        </div>
      )}
    </div>
  );
};
