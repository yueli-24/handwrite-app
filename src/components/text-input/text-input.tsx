"use client";

import React from 'react';
import { useDropzone } from 'react-dropzone';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { useClientSettingsStore } from '@/lib/store/client-store';
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
    multiple: false
  });
  
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
  };
  
  return (
    <div className="space-y-4">
      <div className="flex flex-col space-y-2">
        <label htmlFor="text-input" className="text-sm font-medium">
          输入文字
        </label>
        <Textarea
          id="text-input"
          placeholder="在此输入要转换为手写体的文字..."
          className="min-h-[200px] resize-y"
          value={text}
          onChange={handleTextChange}
        />
      </div>
      
      <div 
        {...getRootProps()} 
        className={`border-2 border-dashed rounded-md p-6 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary/50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center space-y-2">
          <Upload className="h-8 w-8 text-gray-400" />
          <p className="text-sm text-gray-600">
            {isDragActive
              ? "拖放文件到这里..."
              : "拖放TXT文件到这里，或点击选择文件"}
          </p>
          <p className="text-xs text-gray-400">
            仅支持TXT文本文件
          </p>
        </div>
      </div>
      
      {text && (
        <div className="flex justify-end">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setText('')}
          >
            清空文本
          </Button>
        </div>
      )}
    </div>
  );
};
