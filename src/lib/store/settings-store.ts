import { create } from 'zustand';

export type PaperSize = 'A4' | 'A5' | 'B5';

interface SettingsState {
  // 文字设置
  fontSize: number;
  
  // 页边距设置（mm）
  marginTop: number;
  marginBottom: number;
  marginLeft: number;
  marginRight: number;
  
  // 纸张规格
  paperSize: PaperSize;
  
  // 文本内容
  text: string;
  
  // 预览图片URL
  previewUrls: string[];
  
  // G代码下载URL
  gcodeUrls: string[];
  
  // 设置更新函数
  setFontSize: (size: number) => void;
  setMarginTop: (margin: number) => void;
  setMarginBottom: (margin: number) => void;
  setMarginLeft: (margin: number) => void;
  setMarginRight: (margin: number) => void;
  setPaperSize: (size: PaperSize) => void;
  setText: (text: string) => void;
  setPreviewUrls: (urls: string[]) => void;
  setGcodeUrls: (urls: string[]) => void;
  reset: () => void;
}

const defaultSettings = {
  fontSize: 8,
  marginTop: 35,
  marginBottom: 25,
  marginLeft: 30,
  marginRight: 30,
  paperSize: 'A4' as PaperSize,
  text: '',
  previewUrls: [],
  gcodeUrls: [],
};

export const useSettingsStore = create<SettingsState>((set) => ({
  ...defaultSettings,
  
  setFontSize: (size) => set({ fontSize: size }),
  setMarginTop: (margin) => set({ marginTop: margin }),
  setMarginBottom: (margin) => set({ marginBottom: margin }),
  setMarginLeft: (margin) => set({ marginLeft: margin }),
  setMarginRight: (margin) => set({ marginRight: margin }),
  setPaperSize: (size) => set({ paperSize: size }),
  setText: (text) => set({ text }),
  setPreviewUrls: (urls) => set({ previewUrls: urls }),
  setGcodeUrls: (urls) => set({ gcodeUrls: urls }),
  reset: () => set(defaultSettings),
}));
