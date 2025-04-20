"use client";

import React from 'react';
import { useClientSettingsStore } from '@/lib/store/client-store';

export const usePreviewGenerator = () => {
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  
  const {
    text,
    fontSize,
    marginTop,
    marginBottom,
    marginLeft,
    marginRight,
    paperSize,
    setPreviewUrls,
    setGcodeUrls
  } = useClientSettingsStore();
  
  const generatePreview = React.useCallback(async () => {
    if (!text.trim()) {
      setError('请输入文字内容');
      return;
    }
    
    setIsGenerating(true);
    setError(null);
    
    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          fontSize,
          marginTop,
          marginBottom,
          marginLeft,
          marginRight,
          paperSize
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '生成预览失败');
      }
      
      const data = await response.json();
      setPreviewUrls(data.previewUrls);
      setGcodeUrls(data.gcodeUrls);
    } catch (err) {
      console.error('生成预览时出错:', err);
      setError(err instanceof Error ? err.message : '生成预览失败，请稍后重试');
    } finally {
      setIsGenerating(false);
    }
  }, [
    text,
    fontSize,
    marginTop,
    marginBottom,
    marginLeft,
    marginRight,
    paperSize,
    setPreviewUrls,
    setGcodeUrls
  ]);
  
  return {
    isGenerating,
    error,
    generatePreview
  };
};
