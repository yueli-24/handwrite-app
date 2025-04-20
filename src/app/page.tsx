"use client";

import React from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { TextInput } from '@/components/text-input/text-input';
import { SettingsComponents } from '@/components/settings/settings-components';
import { PreviewPanel } from '@/components/preview/preview-panel';
import { GcodeDownload } from '@/components/download/gcode-download';
import { usePreviewGenerator } from '@/lib/hooks/use-preview-generator';

export default function Home() {
  const { generatePreview } = usePreviewGenerator();
  
  return (
    <div className="space-y-8">
      <header className="text-center space-y-2">
        <h1 className="text-3xl font-bold">手写文字生成器</h1>
        <p className="text-gray-500">将文本转换为模拟手写效果的G代码和预览图像</p>
        <div className="handwriting-sample text-xl mt-2">
          这是使用上传字体的示例文字
        </div>
      </header>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-8">
          <div className="bg-white p-6 rounded-lg border shadow-sm">
            <Tabs defaultValue="input" className="w-full">
              <TabsList className="grid grid-cols-2 mb-4">
                <TabsTrigger value="input">文字输入</TabsTrigger>
                <TabsTrigger value="settings">参数设置</TabsTrigger>
              </TabsList>
              <TabsContent value="input" className="space-y-4">
                <TextInput />
              </TabsContent>
              <TabsContent value="settings" className="space-y-4">
                <SettingsComponents />
              </TabsContent>
            </Tabs>
          </div>
          
          <div className="bg-white p-6 rounded-lg border shadow-sm">
            <GcodeDownload />
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <PreviewPanel />
        </div>
      </div>
      
      <footer className="text-center text-sm text-gray-500 pt-4 border-t">
        <p>手写文字生成器 &copy; {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
}
