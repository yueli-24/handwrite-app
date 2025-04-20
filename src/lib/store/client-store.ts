"use client";

import { create } from 'zustand';

// 创建一个客户端存储
const createClientStore = () => 
  create<{
    text: string;
    fontSize: number;
    marginTop: number;
    marginBottom: number;
    marginLeft: number;
    marginRight: number;
    paperSize: 'A4' | 'A5' | 'B5';
    previewUrls: string[];
    gcodeUrls: string[];
    setText: (text: string) => void;
    setFontSize: (size: number) => void;
    setMarginTop: (margin: number) => void;
    setMarginBottom: (margin: number) => void;
    setMarginLeft: (margin: number) => void;
    setMarginRight: (margin: number) => void;
    setPaperSize: (size: 'A4' | 'A5' | 'B5') => void;
    setPreviewUrls: (urls: string[]) => void;
    setGcodeUrls: (urls: string[]) => void;
    reset: () => void;
  }>((set) => ({
    text: '',
    fontSize: 8,
    marginTop: 35,
    marginBottom: 25,
    marginLeft: 30,
    marginRight: 30,
    paperSize: 'A4',
    previewUrls: [],
    gcodeUrls: [],
    setText: (text) => set({ text }),
    setFontSize: (size) => set({ fontSize: size }),
    setMarginTop: (margin) => set({ marginTop: margin }),
    setMarginBottom: (margin) => set({ marginBottom: margin }),
    setMarginLeft: (margin) => set({ marginLeft: margin }),
    setMarginRight: (margin) => set({ marginRight: margin }),
    setPaperSize: (size) => set({ paperSize: size }),
    setPreviewUrls: (urls) => set({ previewUrls: urls }),
    setGcodeUrls: (urls) => set({ gcodeUrls: urls }),
    reset: () => set({
      text: '',
      fontSize: 8,
      marginTop: 35,
      marginBottom: 25,
      marginLeft: 30,
      marginRight: 30,
      paperSize: 'A4',
      previewUrls: [],
      gcodeUrls: []
    })
  }));

// 使用懒加载确保只在客户端创建store
let clientStore: ReturnType<typeof createClientStore> | undefined;

export const useClientSettingsStore = () => {
  if (typeof window === 'undefined') {
    // 服务器端返回空对象
    return {
      text: '',
      fontSize: 8,
      marginTop: 35,
      marginBottom: 25,
      marginLeft: 30,
      marginRight: 30,
      paperSize: 'A4' as const,
      previewUrls: [],
      gcodeUrls: [],
      setText: () => {},
      setFontSize: () => {},
      setMarginTop: () => {},
      setMarginBottom: () => {},
      setMarginLeft: () => {},
      setMarginRight: () => {},
      setPaperSize: () => {},
      setPreviewUrls: () => {},
      setGcodeUrls: () => {},
      reset: () => {}
    };
  }
  
  if (!clientStore) {
    clientStore = createClientStore();
  }
  
  return clientStore();
};
