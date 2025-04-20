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
    setPreviewUrls([]);
    setGcodeUrls([]);

    try {
      console.log('发送预览生成请求，参数:', {
        text: text.length > 100 ? text.substring(0, 100) + '...' : text,
        fontSize,
        marginTop,
        marginBottom,
        marginLeft,
        marginRight,
        paperSize
      });

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

      console.log('API响应状态:', response.status);
      
      // 检查响应是否为空
      const responseText = await response.text();
      console.log('API响应内容:', responseText);
      
      if (!responseText) {
        throw new Error('服务器返回了空响应');
      }
      
      // 尝试解析JSON
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (jsonError) {
        console.error('JSON解析错误:', jsonError);
        throw new Error('无法解析服务器响应: ' + responseText.substring(0, 100));
      }

      if (!response.ok) {
        // 显示详细的错误信息，包括trace
        const errorMessage = data.error || '生成预览失败';
        const errorTrace = data.trace || '无详细错误信息';
        console.error('API错误详情:', errorMessage);
        console.error('错误跟踪:', errorTrace);
        throw new Error(`${errorMessage}\n详细信息: ${errorTrace}`);
      }

      if (!data.previewUrls || !data.gcodeUrls) {
        throw new Error('服务器响应缺少必要的数据');
      }

      setPreviewUrls(data.previewUrls);
      setGcodeUrls(data.gcodeUrls);
      console.log('预览生成成功:', data);
    } catch (err) {
      console.error('预览生成错误:', err);
      // 显示完整的错误信息，包括堆栈跟踪
      const errorMessage = err instanceof Error ? err.message : '生成预览时发生未知错误';
      const errorStack = err instanceof Error && err.stack ? `\n堆栈: ${err.stack}` : '';
      setError(`${errorMessage}${errorStack}`);
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
