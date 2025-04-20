"use client";

import React from 'react';
import { useClientSettingsStore } from '@/lib/store/client-store';

export const usePreviewGenerator = () => {
  const { text, fontSize, marginTop, marginBottom, marginLeft, marginRight, paperSize, setPreviewUrls, setGcodeUrls } = useClientSettingsStore();
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

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
          settings: {
            fontSize,
            marginTop,
            marginBottom,
            marginLeft,
            marginRight,
            paperSize,
          },
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setPreviewUrls(data.previewUrls);
        setGcodeUrls(data.gcodeUrls);
        return true;
      } else {
        setError(data.error || '生成失败');
        return false;
      }
    } catch (error) {
      console.error('生成错误:', error);
      setError('生成过程中发生错误，请重试');
      return false;
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
