import './globals.css';
import type { Metadata } from 'next';
import localFont from 'next/font/local';

// 导入本地字体
const handwritingFont = localFont({
  src: '../../public/fonts/しょかきさらり行体.ttf',
  variable: '--font-handwriting',
  display: 'swap',
});

export const metadata: Metadata = {
  title: '手写文字生成器',
  description: '将文本转换为模拟手写效果的G代码和预览图像',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className={handwritingFont.variable}>
      <body className="min-h-screen bg-background">
        <main className="container mx-auto py-8 px-4 max-w-6xl">
          {children}
        </main>
      </body>
    </html>
  );
}
