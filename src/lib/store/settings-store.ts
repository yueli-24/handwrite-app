"use client";

import { create } from 'zustand';

export interface SettingsState {
  fontSize: number;
  marginTop: number;
  marginBottom: number;
  marginLeft: number;
  marginRight: number;
  paperSize: 'A4' | 'A5' | 'B5';
  setFontSize: (size: number) => void;
  setMarginTop: (margin: number) => void;
  setMarginBottom: (margin: number) => void;
  setMarginLeft: (margin: number) => void;
  setMarginRight: (margin: number) => void;
  setPaperSize: (size: 'A4' | 'A5' | 'B5') => void;
  reset: () => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  fontSize: 8,
  marginTop: 35,
  marginBottom: 25,
  marginLeft: 30,
  marginRight: 30,
  paperSize: 'A4',
  setFontSize: (size) => set({ fontSize: size }),
  setMarginTop: (margin) => set({ marginTop: margin }),
  setMarginBottom: (margin) => set({ marginBottom: margin }),
  setMarginLeft: (margin) => set({ marginLeft: margin }),
  setMarginRight: (margin) => set({ marginRight: margin }),
  setPaperSize: (size) => set({ paperSize: size }),
  reset: () => set({
    fontSize: 8,
    marginTop: 35,
    marginBottom: 25,
    marginLeft: 30,
    marginRight: 30,
    paperSize: 'A4'
  })
}));
