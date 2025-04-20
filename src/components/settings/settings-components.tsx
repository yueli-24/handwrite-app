"use client";

import React from 'react';
import { Slider } from '@/components/ui/slider';
import { useClientSettingsStore } from '@/lib/store/client-store';
import { Input } from '@/components/ui/input';

export const FontSizeSettings = () => {
  const { fontSize, setFontSize } = useClientSettingsStore();
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label htmlFor="font-size" className="text-sm font-medium">
          字体大小 (mm)
        </label>
        <span className="text-sm font-medium">{fontSize} mm</span>
      </div>
      <Slider
        id="font-size"
        min={4}
        max={12}
        step={0.5}
        value={[fontSize]}
        onValueChange={(value) => setFontSize(value[0])}
        className="w-full"
      />
    </div>
  );
};

export const MarginSettings = () => {
  const { 
    marginTop, setMarginTop,
    marginBottom, setMarginBottom,
    marginLeft, setMarginLeft,
    marginRight, setMarginRight
  } = useClientSettingsStore();
  
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium">页边距 (mm)</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label htmlFor="margin-top" className="text-xs">上边距</label>
          <div className="flex items-center space-x-2">
            <Input
              id="margin-top"
              type="number"
              min={10}
              max={50}
              value={marginTop}
              onChange={(e) => setMarginTop(Number(e.target.value))}
              className="w-full"
            />
            <span className="text-xs">mm</span>
          </div>
        </div>
        
        <div className="space-y-2">
          <label htmlFor="margin-bottom" className="text-xs">下边距</label>
          <div className="flex items-center space-x-2">
            <Input
              id="margin-bottom"
              type="number"
              min={10}
              max={50}
              value={marginBottom}
              onChange={(e) => setMarginBottom(Number(e.target.value))}
              className="w-full"
            />
            <span className="text-xs">mm</span>
          </div>
        </div>
        
        <div className="space-y-2">
          <label htmlFor="margin-left" className="text-xs">左边距</label>
          <div className="flex items-center space-x-2">
            <Input
              id="margin-left"
              type="number"
              min={10}
              max={50}
              value={marginLeft}
              onChange={(e) => setMarginLeft(Number(e.target.value))}
              className="w-full"
            />
            <span className="text-xs">mm</span>
          </div>
        </div>
        
        <div className="space-y-2">
          <label htmlFor="margin-right" className="text-xs">右边距</label>
          <div className="flex items-center space-x-2">
            <Input
              id="margin-right"
              type="number"
              min={10}
              max={50}
              value={marginRight}
              onChange={(e) => setMarginRight(Number(e.target.value))}
              className="w-full"
            />
            <span className="text-xs">mm</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export const PaperSizeSettings = () => {
  const { paperSize, setPaperSize } = useClientSettingsStore();
  
  return (
    <div className="space-y-4">
      <label htmlFor="paper-size" className="text-sm font-medium">
        纸张规格
      </label>
      <select
        id="paper-size"
        value={paperSize}
        onChange={(e) => setPaperSize(e.target.value as 'A4' | 'A5' | 'B5')}
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      >
        <option value="A4">A4 (210 × 297 mm)</option>
        <option value="A5">A5 (148 × 210 mm)</option>
        <option value="B5">B5 (176 × 250 mm)</option>
      </select>
    </div>
  );
};
