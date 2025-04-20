"use client";

import React from 'react';
import { useClientSettingsStore } from '@/lib/store/client-store';
import { useDropzone } from 'react-dropzone';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Upload } from 'lucide-react';

export const TextInput = () => {
  const { text, setText } = useClientSettingsStore();
  
  const onDrop = React.useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        const fileContent = reader.result as string;
        setText(fileContent);
      };
      reader.readAsText(file);
    }
  }, [setText]);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt']
    },
    maxFiles: 1
  });
  
  return (
    <div className="space-y-4">
      <div className="flex flex-col space-y-2">
        <label htmlFor="text-input" className="text-sm font-medium">
          输入文字
        </label>
        <Textarea
          id="text-input"
          placeholder="请输入要转换为手写体的文字..."
          className="min-h-[200px] resize-y"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </div>
      
      <div 
        {...getRootProps()} 
        className={`border-2 border-dashed rounded-md p-6 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary/50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center gap-2">
          <Upload className="h-8 w-8 text-gray-400" />
          {isDragActive ? (
            <p>拖放文件到这里...</p>
          ) : (
            <>
              <p className="text-sm text-gray-600">拖放TXT文件到这里，或点击选择文件</p>
              <Button type="button" variant="outline" size="sm">
                选择文件
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
