"use client";

import React from 'react';
import { usePreviewGenerator } from '@/lib/hooks/use-preview-generator';
import { Button } from '@/components/ui/button';
import { ImagePreview } from '@/components/preview/image-preview';
import { useClientSettingsStore } from '@/lib/store/client-store';
import { AlertCircle } from 'lucide-react';

export const PreviewPanel = () => {
  const { text } = useClientSettingsStore();
  const { isGenerating, error, generatePreview } = usePreviewGenerator();
  
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">预览效果</h2>
        <Button 
          onClick={generatePreview} 
          disabled={isGenerating || !text.trim()}
          size="sm"
        >
          {isGenerating ? '生成中...' : '刷新预览'}
        </Button>
      </div>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md flex items-start">
          <AlertCircle className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}
      
      <ImagePreview />
      
      <p className="text-xs text-gray-500 mt-2">
        预览图像显示了文字的手写效果，包括随机的文字间距和垂直抖动。
        灰色区域表示页边距，蓝色线条表示笔画路径。
      </p>
    </div>
  );
};
