"use client";

import React from 'react';
import { useClientSettingsStore } from '@/lib/store/client-store';
import Image from 'next/image';

export const ImagePreview = () => {
  const { previewUrls } = useClientSettingsStore();
  const [currentPage, setCurrentPage] = React.useState(0);
  
  if (previewUrls.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px] border-2 border-dashed rounded-md p-6">
        <p className="text-gray-400">预览将在这里显示</p>
        <p className="text-xs text-gray-400 mt-2">输入文字并调整设置后生成预览</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      <div className="relative border rounded-md overflow-hidden bg-white h-[500px] flex items-center justify-center">
        {previewUrls[currentPage] ? (
          <div className="relative w-full h-full">
            <Image
              src={previewUrls[currentPage]}
              alt={`预览图片 ${currentPage + 1}`}
              fill
              className="object-contain"
            />
          </div>
        ) : (
          <p className="text-gray-400">加载预览中...</p>
        )}
      </div>
      
      {previewUrls.length > 1 && (
        <div className="flex items-center justify-between">
          <button
            onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
            disabled={currentPage === 0}
            className="px-3 py-1 rounded-md bg-gray-100 text-sm disabled:opacity-50"
          >
            上一页
          </button>
          
          <span className="text-sm">
            第 {currentPage + 1} 页，共 {previewUrls.length} 页
          </span>
          
          <button
            onClick={() => setCurrentPage(prev => Math.min(previewUrls.length - 1, prev + 1))}
            disabled={currentPage === previewUrls.length - 1}
            className="px-3 py-1 rounded-md bg-gray-100 text-sm disabled:opacity-50"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
};
