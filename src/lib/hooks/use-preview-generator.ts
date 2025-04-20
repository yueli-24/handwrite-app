"use client";

import { useState } from 'react';
import { useClientSettingsStore } from '@/lib/store/client-store';

/**
 * 检查响应是否为HTML
 * 用于检测Vercel返回的HTML错误页面
 */
const isHtmlResponse = (text: string): boolean => {
  return text.trim().startsWith('<!') || 
         text.trim().startsWith('<html') || 
         text.trim().startsWith('<HTML') ||
         text.includes('<!doctype html') ||
         text.includes('<!DOCTYPE html');
};

/**
 * 从HTML响应中提取错误信息
 */
const extractErrorFromHtml = (html: string): string => {
  try {
    // 尝试提取有用的错误信息
    const titleMatch = html.match(/<title>(.*?)<\/title>/i);
    const title = titleMatch ? titleMatch[1] : '';
    
    // 返回提取的信息或通用错误
    return title ? `服务器错误: ${title}` : '服务器返回了HTML错误页面';
  } catch (e) {
    return '服务器返回了HTML错误页面';
  }
};

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

      // 添加超时处理
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时

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
          signal: controller.signal
        });

        clearTimeout(timeoutId); // 清除超时
        console.log('API响应状态:', response.status);
        
        // 检查响应是否为空
        let responseText = '';
        try {
          responseText = await response.text();
          console.log('API响应内容长度:', responseText.length);
          console.log('API响应内容预览:', responseText.substring(0, 200) + (responseText.length > 200 ? '...' : ''));
        } catch (textError) {
          console.error('获取响应文本失败:', textError);
          throw new Error('无法读取服务器响应: ' + (textError instanceof Error ? textError.message : String(textError)));
        }
        
        if (!responseText || responseText.trim() === '') {
          console.error('服务器返回了空响应');
          throw new Error('服务器返回了空响应');
        }
        
        // 检查是否为HTML响应
        if (isHtmlResponse(responseText)) {
          console.error('服务器返回了HTML错误页面:', responseText.substring(0, 500));
          const errorMessage = extractErrorFromHtml(responseText);
          throw new Error(`Python处理失败: ${responseText.substring(0, 100)}...\n详细信息: ${errorMessage}`);
        }
        
        // 尝试解析JSON
        let data;
        try {
          data = JSON.parse(responseText);
        } catch (jsonError) {
          console.error('JSON解析错误:', jsonError);
          console.error('无效的JSON响应:', responseText.substring(0, 500));
          throw new Error(`无法解析错误响应: ${(jsonError as Error).message}`);
        }

        if (!response.ok) {
          // 显示详细的错误信息，包括trace
          const errorMessage = data && data.error ? data.error : '生成预览失败';
          const errorTrace = data && data.trace ? data.trace : '无详细错误信息';
          console.error('API错误详情:', errorMessage);
          console.error('错误跟踪:', errorTrace);
          throw new Error(`${errorMessage}\n详细信息: ${errorTrace}`);
        }

        // 验证响应数据结构
        if (!data) {
          throw new Error('服务器返回了空数据');
        }

        // 检查是否有预览数据
        if (data.previewBase64) {
          // 处理单页或多页预览
          const previewArray: string[] = Array.isArray(data.previewBase64) 
            ? data.previewBase64 
            : [data.previewBase64];
          
          setPreviewUrls(previewArray.map((base64: string) => `data:image/png;base64,${base64}`));
          
          // 处理G代码
          const gcodeArray: string[] = Array.isArray(data.gcodeContent) 
            ? data.gcodeContent 
            : [data.gcodeContent];
          
          setGcodeUrls(gcodeArray);
          console.log('预览生成成功，页数:', previewArray.length);
        } else if (data.previewUrls) {
          // 兼容旧版API响应格式
          setPreviewUrls(data.previewUrls);
          setGcodeUrls(data.gcodeUrls || []);
          console.log('预览生成成功(旧格式):', data);
        } else {
          throw new Error('服务器响应缺少预览数据');
        }
      } catch (error) {
        const fetchError = error as Error;
        if (fetchError && fetchError.name === 'AbortError') {
          throw new Error('请求超时，请稍后重试');
        }
        throw fetchError;
      }
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
