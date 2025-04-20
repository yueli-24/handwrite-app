import { useState } from "react";
import { useClientSettingsStore } from "@/lib/store/settings-store";

export function usePreviewGenerator() {
  const {
    fontSize,
    marginTop,
    marginBottom,
    marginLeft,
    marginRight,
    paperSize,
  } = useClientSettingsStore();

  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [gcodeContent, setGcodeContent] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function generatePreview(input: string | File) {
    setError(null);
    setPreviewUrls([]);
    setGcodeContent([]);

    const isFile = input instanceof File;
    const endpoint = "/api/generate"; // ✅ 修复路径
    const payload = isFile ? input : JSON.stringify({
      text: input,
      fontSize,
      marginTop,
      marginBottom,
      marginLeft,
      marginRight,
      paperSize,
    });

    const headers = isFile
      ? {}
      : { "Content-Type": "application/json" };

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body: payload,
        headers,
      });

      if (!response.ok) {
        const fallback = await response.text(); // ✅ fallback for HTML error
        throw new Error(`Server error (${response.status}): ${fallback}`);
      }

      const data = await response.json();

      const previews = Array.isArray(data.previewBase64)
        ? data.previewBase64
        : [data.previewBase64];

      setPreviewUrls(previews.map((base64: string) => `data:image/png;base64,${base64}`));
      setGcodeContent(data.gcodeContent ?? []);
    } catch (fetchError: unknown) {
      console.error("❌ 生成失败:", fetchError);
      if (fetchError instanceof Error) {
        setError(fetchError.message);
      } else {
        setError("Unknown error occurred.");
      }
    }
  }

  return {
    previewUrls,
    gcodeContent,
    error,
    generatePreview,
  };
}
