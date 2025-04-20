"use client";

import React from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { TextInput } from '@/components/text-input/text-input';
import { FontSizeSettings, MarginSettings, PaperSizeSettings } from '@/components/settings/settings-components';
import { PreviewPanel } from '@/components/preview/preview-panel';
import { GcodeDownload } from '@/components/download/gcode-download';
import { Button } from '@/components/ui/button';
import { usePreviewGenerator } from '@/lib/hooks/use-preview-generator';

export default function Home() {
  const { isGenerating, generatePreview } = usePreviewGenerator();
  
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8 px-4">
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold mb-2">手写文字生成器</h1>
          <p className="text-gray-600">将文本转换为自然手写效果的G代码</p>
        </header>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h2 className="text-xl font-semibold mb-4">文字输入</h2>
              <TextInput />
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h2 className="text-xl font-semibold mb-4">参数设置</h2>
              <Tabs defaultValue="font-size">
                <TabsList className="w-full grid grid-cols-3">
                  <TabsTrigger value="font-size">字体大小</TabsTrigger>
                  <TabsTrigger value="margins">页边距</TabsTrigger>
                  <TabsTrigger value="paper-size">纸张规格</TabsTrigger>
                </TabsList>
                <TabsContent value="font-size" className="pt-4">
                  <FontSizeSettings />
                </TabsContent>
                <TabsContent value="margins" className="pt-4">
                  <MarginSettings />
                </TabsContent>
                <TabsContent value="paper-size" className="pt-4">
                  <PaperSizeSettings />
                </TabsContent>
              </Tabs>
            </div>
            
            <Button 
              onClick={generatePreview} 
              disabled={isGenerating}
              className="w-full py-6 text-lg"
            >
              {isGenerating ? '生成中...' : '生成手写效果'}
            </Button>
            
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h2 className="text-xl font-semibold mb-4">G代码下载</h2>
              <GcodeDownload />
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <PreviewPanel />
          </div>
        </div>
        
        <footer className="mt-12 text-center text-gray-500 text-sm">
          <p>© 2025 手写文字生成器 | 支持中文和其他文字的自然手写效果</p>
        </footer>
      </div>
    </main>
  );
}
