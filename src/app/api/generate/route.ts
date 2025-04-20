import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';
import os from 'os';
import util from 'util';

const execPromise = util.promisify(exec);

// 创建临时目录用于存储生成的文件
const createTempDir = async () => {
  const tempDir = path.join(os.tmpdir(), 'handwrite-' + Date.now());
  await fs.mkdir(tempDir, { recursive: true });
  return tempDir;
};

// 将Python代码写入临时文件
const createPythonScript = async (tempDir: string) => {
  const pythonScriptPath = path.join(tempDir, 'handwrite.py');
  
  // 这里是原始Python代码，需要进行适当修改以适应API调用
  const pythonCode = `
import numpy as np
import cv2
from svgwrite import Drawing
import os
from PIL import Image, ImageDraw, ImageFont
from skimage.morphology import skeletonize
import random
import sys
import json
import base64
from io import BytesIO

class StrokeWriter:
    def __init__(self, font_size=8, margin_top=35, margin_bottom=25, margin_left=30, margin_right=30, paper_size='A4'):
        # 纸张规格设置
        if paper_size == 'A4':
            self.page_width = 210
            self.page_height = 297
        elif paper_size == 'A5':
            self.page_width = 148
            self.page_height = 210
        elif paper_size == 'B5':
            self.page_width = 176
            self.page_height = 250
        else:
            # 默认A4
            self.page_width = 210
            self.page_height = 297
        
        # 计算中心坐标
        self.center_x = self.page_width / 2
        self.center_y = self.page_height / 2
        
        # 页边距设置（mm单位）
        self.paper_margin_left = margin_left
        self.paper_margin_right = margin_right
        self.paper_margin_top = margin_top
        self.paper_margin_bottom = margin_bottom
        
        # 文字大小和间距设置（mm单位）
        self.char_size = font_size * 10  # 转换为内部单位
        # 文字间隔比例
        self.spacing_ratio_min = 0.06
        self.spacing_ratio_max = 0.12
        self.line_spacing = self.char_size * 1.35
        
        # 笔设置
        self.pen_up_z = 0.0
        self.pen_down_z = -7.0
        self.move_speed = 20000
        self.pen_speed = 20000
        
        # 计算实际可写区域
        self.writing_width = self.page_width - (self.paper_margin_left + self.paper_margin_right)
        self.writing_height = self.page_height - (self.paper_margin_top + self.paper_margin_bottom)
        
        # 文字抖动设置（mm单位）
        self.vertical_wobble_min = -2
        self.vertical_wobble_max = 2
        
        # 防止在行尾断开的字符
        self.no_break_chars = ['、', '。', '，', '．', '」', '』', '）', '｝', '］',
                             ',', '.', ')', '}', ']', '!', '?', '！', '？']
        # 与前一个字符不分开的字符
        self.keep_with_prev_chars = ['」', '』', '）', '｝', '］', ')', '}', ']']

    def convert_to_center_coordinates(self, x, y):
        """将绝对坐标转换为中心原点的相对坐标"""
        center_relative_x = x - self.center_x
        center_relative_y = -(y - self.center_y)  # Y轴向上为正
        return center_relative_x, center_relative_y

    def get_font_strokes(self, char, font_path):
        """从字体中提取字符的笔画"""
        img_size = (self.char_size * 2, self.char_size * 2)
        image = Image.new('L', img_size, 255)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_path, self.char_size)
        
        bbox = draw.textbbox((0, 0), char, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (img_size[0] - text_width) // 2
        y = (img_size[1] - text_height) // 2
        
        draw.text((x, y), char, font=font, fill=0)
        
        img_array = np.array(image)
        _, binary = cv2.threshold(img_array, 128, 255, cv2.THRESH_BINARY_INV)
        skeleton = skeletonize(binary > 0).astype(np.uint8) * 255
        
        contours, _ = cv2.findContours(skeleton, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        
        return contours, (x, y, text_width, text_height)

    def get_random_spacing(self, char_width=None):
        """生成与字符大小成比例的随机间距"""
        if char_width is None:
            char_width = self.char_size/10
        
        min_spacing = char_width * self.spacing_ratio_min * 10
        max_spacing = char_width * self.spacing_ratio_max * 10
        
        return random.uniform(min_spacing, max_spacing)

    def get_vertical_wobble(self):
        """生成随机的垂直抖动"""
        return random.uniform(self.vertical_wobble_min, self.vertical_wobble_max) / 10

    def generate_gcode(self, contour, start_x, start_y, vertical_offset=0, scale=1.0):
        """从轮廓生成G代码（基于中心原点）"""
        points = contour.reshape(-1, 2)
        if len(points) < 2:
            return []
        
        stroke_commands = []
        
        # 移动到起始点（笔抬起）
        x, y = points[0]
        abs_x = start_x + x*scale/10
        abs_y = start_y + y*scale/10 + vertical_offset
        x_pos, y_pos = self.convert_to_center_coordinates(abs_x, abs_y)
        stroke_commands.append(f"G0 X{x_pos:.3f}Y{y_pos:.3f}F{self.move_speed}")
        
        # 笔放下
        stroke_commands.append(f"G1G90 Z{self.pen_down_z}F{self.pen_speed}")
        
        # 绘制笔画
        for point in points[1:]:
            x, y = point
            abs_x = start_x + x*scale/10
            abs_y = start_y + y*scale/10 + vertical_offset
            x_pos, y_pos = self.convert_to_center_coordinates(abs_x, abs_y)
            stroke_commands.append(f"G1 X{x_pos:.3f}Y{y_pos:.3f}F{self.move_speed}")
        
        # 笔抬起
        stroke_commands.append(f"G1G90 Z{self.pen_up_z}F{self.pen_speed}")
        
        return stroke_commands

    def write_text_to_pages(self, text, font_path, output_dir):
        """将文本转换为多页G代码"""
        os.makedirs(output_dir, exist_ok=True)
        
        current_page = 1
        text_position = 0
        total_text = text
        
        result = {
            'pages': [],
            'preview_images': []
        }
        
        while text_position < len(total_text):
            # 重置每页的起始位置
            current_x = self.paper_margin_left
            current_y = self.paper_margin_top
            page_content = []
            
            # G代码初始设置
            gcode = [
                "G21",          # mm模式
                "G90",          # 绝对坐标模式
                f"F{self.move_speed}",  # 基本速度设置
                f"G1G90 Z{self.pen_up_z}F{self.pen_speed}",  # 初始位置笔抬起
                f"G0 X0Y0F{self.move_speed}"  # 移动到中心位置
            ]
            
            # 获取当前页要处理的文本
            current_text = total_text[text_position:]
            lines = current_text.split('\\n')
            
            for line_idx, line in enumerate(lines):
                current_x = self.paper_margin_left
                chars_in_line = []
                base_wobble = self.get_vertical_wobble()
                i = 0
                
                while i < len(line):
                    # 检查下边距 - 页面结束条件
                    if current_y + self.line_spacing/10 > self.page_height - self.paper_margin_bottom:
                        break
                    
                    char = line[i]
                    contours, bbox = self.get_font_strokes(char, font_path)
                    char_actual_width = bbox[2] / 10
                    char_spacing = self.get_random_spacing(char_actual_width)
                    char_wobble = base_wobble + self.get_vertical_wobble()
                    char_width = char_actual_width + char_spacing/10
                    
                    if char == ' ':
                        current_x += char_spacing/5
                        chars_in_line.append(' ')
                        i += 1
                        text_position += 1
                        continue
                    
                    # 检查右边距
                    if current_x + char_width > self.page_width - self.paper_margin_right:
                        if char in self.no_break_chars:
                            if chars_in_line:
                                page_content.append(''.join(chars_in_line))
                                current_y += self.line_spacing/10
                                current_x = self.paper_margin_left
                                chars_in_line = []
                                base_wobble = self.get_vertical_wobble()
                            continue
                        
                        if i + 1 < len(line) and line[i + 1] in self.keep_with_prev_chars:
                            if len(chars_in_line) > 1:
                                chars_in_line.pop()
                                page_content.append(''.join(chars_in_line))
                                current_y += self.line_spacing/10
                                current_x = self.paper_margin_left
                                chars_in_line = []
                                base_wobble = self.get_vertical_wobble()
                            continue
                        
                        if chars_in_line:
                            page_content.append(''.join(chars_in_line))
                            current_y += self.line_spacing/10
                            current_x = self.paper_margin_left
                            chars_in_line = []
                            base_wobble = self.get_vertical_wobble()
                    
                    # 绘制字符
                    if current_x + char_width <= self.page_width - self.paper_margin_right:
                        for contour in contours:
                            stroke_commands = self.generate_gcode(
                                contour, 
                                current_x, 
                                current_y,
                                vertical_offset=char_wobble
                            )
                            gcode.extend(stroke_commands)
                        chars_in_line.append(char)
                        text_position += 1
                    
                    current_x += char_width
                    i += 1
                
                # 处理行尾
                if chars_in_line:
                    page_content.append(''.join(chars_in_line))
                    current_y += self.line_spacing/10
                
                # 处理换行符
                if line_idx < len(lines) - 1:
                    text_position += 1
                
                # 检查页面结束条件
                if current_y + self.line_spacing/10 > self.page_height - self.paper_margin_bottom:
                    break
            
            # G代码结束处理
            gcode.extend([
                f"G1G90 Z{self.pen_up_z}F{self.pen_speed}",
                "G0 X0Y0F20000",
                ""
            ])
            
            # 保存文件
            gcode_filename = f"page_{current_page:03d}.gcode"
            preview_filename = f"page_{current_page:03d}_preview.png"
            gcode_path = os.path.join(output_dir, gcode_filename)
            preview_path = os.path.join(output_dir, preview_filename)
            
            with open(gcode_path, "w") as f:
                f.write("\\n".join(gcode))
            
            # 生成预览
            page_text = '\\n'.join(page_content)
            preview_base64 = generate_preview_base64(page_text, font_path, self)
            
            # 添加到结果
            result['pages'].append({
                'page': current_page,
                'filename': gcode_filename,
                'path': gcode_path
            })
            
            result['preview_images'].append({
                'page': current_page,
                'base64': preview_base64
            })
            
            current_page += 1
            
            # 检查是否处理完所有文本
            if text_position >= len(total_text):
                break
        
        return result

def generate_preview_base64(text, font_path, writer):
    """生成预览图像并返回base64编码"""
    px_per_mm = 11.811  # 300 DPI / 25.4 mm
    width_px = int(writer.page_width * px_per_mm)
    height_px = int(writer.page_height * px_per_mm)
    
    # 创建白色背景图像
    image = Image.new('RGB', (width_px, height_px), 'white')
    draw = ImageDraw.Draw(image)
    
    # 计算边距（像素单位）
    margin_top_px = int(writer.paper_margin_top * px_per_mm)
    margin_right_px = int(writer.paper_margin_right * px_per_mm)
    margin_left_px = int(writer.paper_margin_left * px_per_mm)
    margin_bottom_px = int(writer.paper_margin_bottom * px_per_mm)
    
    # 绘制边距区域（浅灰色）
    draw.rectangle([0, 0, width_px, margin_top_px], fill=(240, 240, 240))
    draw.rectangle([0, height_px - margin_bottom_px, width_px, height_px], fill=(240, 240, 240))
    draw.rectangle([0, 0, margin_left_px, height_px], fill=(240, 240, 240))
    draw.rectangle([width_px - margin_right_px, 0, width_px, height_px], fill=(240, 240, 240))
    
    # 显示原点（红点）
    origin_marker_size = 5
    center_x_px = width_px // 2
    center_y_px = height_px // 2
    draw.ellipse([center_x_px - origin_marker_size, center_y_px - origin_marker_size,
                  center_x_px + origin_marker_size, center_y_px + origin_marker_size],
                 fill=(255, 0, 0))
    
    # 绘制文本轨迹
    current_x = writer.paper_margin_left
    current_y = writer.paper_margin_top
    base_wobble = writer.get_vertical_wobble()
    
    for char in text:
        if char == '\\n':
            current_x = writer.paper_margin_left
            current_y += writer.line_spacing/10
            base_wobble = writer.get_vertical_wobble()
            continue
            
        char_wobble = base_wobble + writer.get_vertical_wobble()
        
        if char == ' ':
            current_x += writer.get_random_spacing()/5
            continue
            
        # 获取字符轨迹
        contours, _ = writer.get_font_strokes(char, font_path)
        
        # 绘制每个轮廓
        for contour in contours:
            points = contour.reshape(-1, 2)
            for i in range(len(points) - 1):
                x1 = int((current_x + points[i][0]/10) * px_per_mm)
                y1 = int((current_y + points[i][1]/10 + char_wobble) * px_per_mm)
                x2 = int((current_x + points[i+1][0]/10) * px_per_mm)
                y2 = int((current_y + points[i+1][1]/10 + char_wobble) * px_per_mm)
                
                draw.line([(x1, y1), (x2, y2)], fill=(0, 0, 255), width=2)
        
        current_x += (writer.char_size/10 + writer.get_random_spacing()/10)
    
    # 显示起始位置（绿点）
    start_x_px = int(writer.paper_margin_left * px_per_mm)
    start_y_px = int(writer.paper_margin_top * px_per_mm)
    marker_size = 5
    draw.ellipse([start_x_px - marker_size, start_y_px - marker_size,
                  start_x_px + marker_size, start_y_px + marker_size],
                 fill=(0, 255, 0))
    
    # 添加图例
    legend_y = height_px - 80
    draw.ellipse([10, legend_y-5, 20, legend_y+5], fill=(255, 0, 0))
    draw.text((25, legend_y-7), "Origin (0, 0)", fill=(0, 0, 0))
    
    legend_y += 20
    draw.ellipse([10, legend_y-5, 20, legend_y+5], fill=(0, 255, 0))
    draw.text((25, legend_y-7), f"Writing Start ({writer.paper_margin_left}mm, {writer.paper_margin_top}mm)", 
              fill=(0, 0, 0))
    
    legend_y += 20
    draw.line([(10, legend_y), (30, legend_y)], fill=(0, 0, 255), width=2)
    draw.text((35, legend_y-7), "Text Path", fill=(0, 0, 0))
    
    # 转换为base64
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str

def text_to_gcode(text, font_path, output_dir, settings):
    """将文本转换为G代码（主函数）"""
    writer = StrokeWriter(
        font_size=settings.get('fontSize', 8),
        margin_top=settings.get('marginTop', 35),
        margin_bottom=settings.get('marginBottom', 25),
        margin_left=settings.get('marginLeft', 30),
        margin_right=settings.get('marginRight', 30),
        paper_size=settings.get('paperSize', 'A4')
    )
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理文本并返回结果
    return writer.write_text_to_pages(text, font_path, output_dir)

# 主函数
if __name__ == "__main__":
    # 从命令行参数获取JSON配置
    input_json = sys.argv[1]
    data = json.loads(input_json)
    
    text = data['text']
    settings = data['settings']
    output_dir = data['outputDir']
    font_path = data['fontPath']
    
    # 处理文本
    result = text_to_gcode(text, font_path, output_dir, settings)
    
    # 输出JSON结果
    print(json.dumps(result))
`;

  await fs.writeFile(pythonScriptPath, pythonCode);
  return pythonScriptPath;
};

// 创建字体目录并复制字体文件
const setupFontFile = async (tempDir: string) => {
  const fontDir = path.join(tempDir, 'font');
  await fs.mkdir(fontDir, { recursive: true });
  
  // 使用默认字体（这里需要确保有一个默认字体文件）
  const defaultFontPath = path.join(process.cwd(), 'public', 'fonts', 'shoukaki-sarari.ttf');
  const targetFontPath = path.join(fontDir, 'shoukaki-sarari.ttf');
  
  try {
    await fs.copyFile(defaultFontPath, targetFontPath);
  } catch {
    // 如果字体文件不存在，创建一个空的字体目录
    console.error('Font file not found, will use system font');
  }
  
  return path.join(fontDir, 'shoukaki-sarari.ttf');
};

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { text, settings } = body;
    
    if (!text) {
      return NextResponse.json({ success: false, error: '文本内容不能为空' }, { status: 400 });
    }
    
    // 创建临时目录
    const tempDir = await createTempDir();
    const outputDir = path.join(tempDir, 'output');
    await fs.mkdir(outputDir, { recursive: true });
    
    // 设置Python脚本
    const pythonScriptPath = await createPythonScript(tempDir);
    
    // 设置字体文件
    const fontPath = await setupFontFile(tempDir);
    
    // 准备输入数据
    const inputData = {
      text,
      settings,
      outputDir,
      fontPath
    };
    
    // 执行Python脚本
    const { stdout, stderr } = await execPromise(`python3 ${pythonScriptPath} '${JSON.stringify(inputData)}'`);
    
    if (stderr) {
      console.error('Python script error:', stderr);
      return NextResponse.json({ success: false, error: stderr }, { status: 500 });
    }
    
    // 解析Python脚本的输出
    const result = JSON.parse(stdout);
    
    // 构建响应数据
    const previewUrls = result.preview_images.map((img: { base64: string }) => `data:image/png;base64,${img.base64}`);
    const gcodeUrls = result.pages.map((page: { page: number }) => `/api/download/gcode?page=${page.page}&dir=${encodeURIComponent(outputDir)}`);
    
    return NextResponse.json({
      success: true,
      previewUrls,
      gcodeUrls
    });
    
  } catch {
    console.error('API error occurred');
    return NextResponse.json({ success: false, error: '处理请求时发生错误' }, { status: 500 });
  }
}
