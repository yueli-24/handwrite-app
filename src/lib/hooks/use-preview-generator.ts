import { useState } from 'react';

const usePreviewGenerator = () => {
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const generatePreview = async (
        text: string,
        fontSize: number,
        marginTop: number,
        marginBottom: number,
        marginLeft: number,
        marginRight: number,
        paperSize: string
    ) => {
        setIsGenerating(true);
        setError(null);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text,
                    fontSize,
                    marginTop,
                    marginBottom,
                    marginLeft,
                    marginRight,
                    paperSize
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId); // 清除超时

            // 检查响应状态
            if (!response.ok) {
                const errorData = await response.json();
                const errorMessage = errorData.error || '生成预览失败';
                const errorTrace = errorData.trace || '无详细错误信息';
                console.error('API错误详情:', errorMessage);
                console.error('错误跟踪:', errorTrace);
                throw new Error(`${errorMessage}\n详细信息: ${errorTrace}`);
            }

            // 获取响应文本并检查
            const responseText = await response.text();
            console.log('API响应内容长度:', responseText.length);
            console.log('API响应内容预览:', responseText.substring(0, 200) + (responseText.length > 200 ? '...' : ''));

            if (!responseText || responseText.trim() === '') {
                console.error('服务器返回了空响应');
                throw new Error('服务器返回了空响应');
            }

            // 尝试解析JSON
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (jsonError) {
                console.error('JSON解析错误:', jsonError);
                throw new Error('无法解析服务器响应: ' + responseText.substring(0, 100));
            }

            // 处理成功响应
            return data;
        } catch (err) {
            if (err.name === 'AbortError') {
                setError('请求超时，请稍后重试');
            } else {
                console.error('预览生成错误:', err);
                const errorMessage = err instanceof Error ? err.message : '生成预览时发生未知错误';
                const errorStack = err instanceof Error && err.stack ? `\n堆栈: ${err.stack}` : '';
                setError(`${errorMessage}${errorStack}`);
            }
        } finally {
            setIsGenerating(false);
        }
    };

    return {
        isGenerating,
        error,
        generatePreview
    };
};

export default usePreviewGenerator;