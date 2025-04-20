"use client";

import React from 'react';
import { Slider } from '@/components/ui/slider';
import { useClientSettingsStore } from '@/lib/store/client-store';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

export const SettingsComponents = () => {
  const { 
    fontSize, 
    marginTop, 
    marginBottom, 
    marginLeft, 
    marginRight, 
    paperSize,
    setFontSize,
    setMarginTop,
    setMarginBottom,
    setMarginLeft,
    setMarginRight,
    setPaperSize
  } = useClientSettingsStore();
  
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <label htmlFor="font-size" className="text-sm font-medium">
            字体大小: {fontSize}mm
          </label>
          <span className="text-xs text-gray-500">
            4-12mm
          </span>
        </div>
        <Slider
          id="font-size"
          min={4}
          max={12}
          step={0.5}
          value={[fontSize]}
          onValueChange={(value) => setFontSize(value[0])}
        />
      </div>
      
      <div className="space-y-4">
        <h3 className="text-sm font-medium">页边距设置</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label htmlFor="margin-top" className="text-xs">
                上边距: {marginTop}mm
              </label>
            </div>
            <Slider
              id="margin-top"
              min={10}
              max={50}
              step={1}
              value={[marginTop]}
              onValueChange={(value) => setMarginTop(value[0])}
            />
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label htmlFor="margin-bottom" className="text-xs">
                下边距: {marginBottom}mm
              </label>
            </div>
            <Slider
              id="margin-bottom"
              min={10}
              max={50}
              step={1}
              value={[marginBottom]}
              onValueChange={(value) => setMarginBottom(value[0])}
            />
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label htmlFor="margin-left" className="text-xs">
                左边距: {marginLeft}mm
              </label>
            </div>
            <Slider
              id="margin-left"
              min={10}
              max={50}
              step={1}
              value={[marginLeft]}
              onValueChange={(value) => setMarginLeft(value[0])}
            />
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label htmlFor="margin-right" className="text-xs">
                右边距: {marginRight}mm
              </label>
            </div>
            <Slider
              id="margin-right"
              min={10}
              max={50}
              step={1}
              value={[marginRight]}
              onValueChange={(value) => setMarginRight(value[0])}
            />
          </div>
        </div>
      </div>
      
      <div className="space-y-2">
        <label className="text-sm font-medium">
          纸张规格
        </label>
        <Tabs 
          defaultValue={paperSize} 
          onValueChange={(value) => setPaperSize(value as 'A4' | 'A5' | 'B5')}
          className="w-full"
        >
          <TabsList className="grid grid-cols-3 w-full">
            <TabsTrigger value="A4">A4</TabsTrigger>
            <TabsTrigger value="A5">A5</TabsTrigger>
            <TabsTrigger value="B5">B5</TabsTrigger>
          </TabsList>
          <TabsContent value="A4" className="text-xs text-gray-500 mt-1">
            210 × 297 mm
          </TabsContent>
          <TabsContent value="A5" className="text-xs text-gray-500 mt-1">
            148 × 210 mm
          </TabsContent>
          <TabsContent value="B5" className="text-xs text-gray-500 mt-1">
            176 × 250 mm
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};
