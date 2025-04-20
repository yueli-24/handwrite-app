"use client";

import { useState } from 'react';
import { useClientSettingsStore } from '@/lib/store/client-store';

export const usePreviewGenerator = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
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

  const generatePreview = async () => {
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
        throw new Error(errorData.message || '生成预览失败');
      }

      const data = await response.json();
      setPreviewUrls(data.previewUrls);
      setGcodeUrls(data.gcodeUrls);
    } catch (err) {
      console.error('预览生成错误:', err);
      setError(err instanceof Error ? err.message : '生成预览时发生未知错误');
    } finally {
      setIsGenerating(false);
    }
  };

  return {
    isGenerating,
    error,
    generatePreview
  };
};
