import localFont from 'next/font/local';
import './globals.css';

// 导入本地手写字体
const handwritingFont = localFont({
  src: '../../public/fonts/しょかきさらり行体.ttf',
  variable: '--font-handwriting',
});

export const metadata = {
  title: '手写文字生成器',
  description: '将文本转换为模拟手写效果的G代码和预览图像',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={`${handwritingFont.variable} max-w-6xl mx-auto p-4 md:p-8`}>
        {children}
      </body>
    </html>
  );
}
