from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import argparse
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO
import tempfile
import shutil
import uuid

# 导入原始Python脚本中的核心功能
sys.path.append(os.path.join(os.getcwd(), 'src', 'lib', 'python'))
try:
    from handwrite import HandwritingGenerator, generate_preview
except ImportError:
    # 如果无法导入，定义一个简化版本的核心功能
    class HandwritingGenerator:
        def __init__(self, font_path, font_size=8, margin_top=35, margin_bottom=25, 
                    margin_left=30, margin_right=30, paper_size='A4'):
            self.font_path = font_path
            self.font_size = font_size
            self.margin_top = margin_top
            self.margin_bottom = margin_bottom
            self.margin_left = margin_left
            self.margin_right = margin_right
            self.paper_size = paper_size
            
            # 设置纸张尺寸（单位：毫米）
            if paper_size == 'A4':
                self.paper_width = 210
                self.paper_height = 297
            elif paper_size == 'A5':
                self.paper_width = 148
                self.paper_height = 210
            elif paper_size == 'B5':
                self.paper_width = 176
                self.paper_height = 250
            else:
                raise ValueError(f"不支持的纸张规格: {paper_size}")
            
            # 计算可写区域
            self.writing_width = self.paper_width - self.margin_left - self.margin_right
            self.writing_height = self.paper_height - self.margin_top - self.margin_bottom
            
            # 加载字体
            self.font = ImageFont.truetype(self.font_path, int(self.font_size * 10))
            
            # 初始化当前位置
            self.x = self.margin_left
            self.y = self.margin_top
            self.line_height = self.font_size * 1.5  # 行高为字体大小的1.5倍
            
            # 初始化页面计数
            self.page_count = 1
            
            # 初始化G代码
            self.gcode = []
            self.init_gcode()
        
        def init_gcode(self):
            """初始化G代码"""
            self.gcode = [
                "G21 ; 设置单位为毫米",
                "G90 ; 使用绝对坐标",
                "G92 X0 Y0 Z0 ; 设置当前位置为原点",
                "G1 Z5 F1000 ; 抬起笔",
                f"G1 X{self.margin_left} Y{self.margin_top} F3000 ; 移动到起始位置"
            ]
        
        def process_text(self, text):
            """处理文本，生成G代码和预览图像"""
            # 创建一个空白图像用于预览
            preview_images = []
            gcode_files = []
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            
            # 处理文本
            lines = text.split('\n')
            for line in lines:
                if not line.strip():  # 空行
                    self.y += self.line_height
                    if self.y + self.line_height > self.margin_top + self.writing_height:
                        # 创建预览图像
                        preview_img = self.create_preview()
                        preview_path = os.path.join(temp_dir, f"page_{self.page_count:03d}_preview.png")
                        preview_img.save(preview_path)
                        preview_images.append(preview_path)
                        
                        # 保存G代码
                        gcode_path = os.path.join(temp_dir, f"page_{self.page_count:03d}.gcode")
                        with open(gcode_path, 'w') as f:
                            f.write('\n'.join(self.gcode))
                        gcode_files.append(gcode_path)
                        
                        # 准备新页面
                        self.page_count += 1
                        self.x = self.margin_left
                        self.y = self.margin_top
                        self.init_gcode()
                    continue
                
                # 处理一行文字
                for char in line:
                    # 检查是否需要换行
                    if self.x + self.font_size > self.margin_left + self.writing_width:
                        self.x = self.margin_left
                        self.y += self.line_height
                        
                        # 检查是否需要新页面
                        if self.y + self.line_height > self.margin_top + self.writing_height:
                            # 创建预览图像
                            preview_img = self.create_preview()
                            preview_path = os.path.join(temp_dir, f"page_{self.page_count:03d}_preview.png")
                            preview_img.save(preview_path)
                            preview_images.append(preview_path)
                            
                            # 保存G代码
                            gcode_path = os.path.join(temp_dir, f"page_{self.page_count:03d}.gcode")
                            with open(gcode_path, 'w') as f:
                                f.write('\n'.join(self.gcode))
                            gcode_files.append(gcode_path)
                            
                            # 准备新页面
                            self.page_count += 1
                            self.x = self.margin_left
                            self.y = self.margin_top
                            self.init_gcode()
                    
                    # 添加字符的G代码
                    self.add_char_gcode(char)
                    
                    # 更新位置
                    self.x += self.font_size * (1 + 0.1 * np.random.random())  # 添加一些随机间距
                
                # 行尾换行
                self.x = self.margin_left
                self.y += self.line_height
                
                # 检查是否需要新页面
                if self.y + self.line_height > self.margin_top + self.writing_height:
                    # 创建预览图像
                    preview_img = self.create_preview()
                    preview_path = os.path.join(temp_dir, f"page_{self.page_count:03d}_preview.png")
                    preview_img.save(preview_path)
                    preview_images.append(preview_path)
                    
                    # 保存G代码
                    gcode_path = os.path.join(temp_dir, f"page_{self.page_count:03d}.gcode")
                    with open(gcode_path, 'w') as f:
                        f.write('\n'.join(self.gcode))
                    gcode_files.append(gcode_path)
                    
                    # 准备新页面
                    self.page_count += 1
                    self.x = self.margin_left
                    self.y = self.margin_top
                    self.init_gcode()
            
            # 处理最后一页
            if self.gcode and self.gcode[-1] != "G1 Z5 F1000 ; 抬起笔":
                # 创建预览图像
                preview_img = self.create_preview()
                preview_path = os.path.join(temp_dir, f"page_{self.page_count:03d}_preview.png")
                preview_img.save(preview_path)
                preview_images.append(preview_path)
                
                # 保存G代码
                gcode_path = os.path.join(temp_dir, f"page_{self.page_count:03d}.gcode")
                with open(gcode_path, 'w') as f:
                    f.write('\n'.join(self.gcode))
                gcode_files.append(gcode_path)
            
            # 读取生成的文件并转换为base64
            preview_base64 = []
            gcode_content = []
            
            for preview_path in preview_images:
                with open(preview_path, 'rb') as f:
                    img_data = f.read()
                    preview_base64.append(base64.b64encode(img_data).decode('utf-8'))
            
            for gcode_path in gcode_files:
                with open(gcode_path, 'r') as f:
                    gcode_content.append(f.read())
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            return preview_base64, gcode_content
        
        def add_char_gcode(self, char):
            """为字符添加G代码"""
            # 简化版本，实际应该根据字体轮廓生成G代码
            # 这里只是模拟一个简单的写字动作
            x_jitter = 0.2 * np.random.random() - 0.1  # -0.1到0.1的随机抖动
            y_jitter = 0.2 * np.random.random() - 0.1  # -0.1到0.1的随机抖动
            
            self.gcode.append(f"G1 Z5 F1000 ; 抬起笔")
            self.gcode.append(f"G1 X{self.x + x_jitter} Y{self.y + y_jitter} F3000 ; 移动到字符位置")
            self.gcode.append(f"G1 Z0 F1000 ; 放下笔")
            
            # 模拟写字的几个点
            for i in range(5):
                x_offset = (i / 4) * self.font_size * 0.8
                y_offset = np.sin(i * np.pi / 2) * self.font_size * 0.3
                self.gcode.append(f"G1 X{self.x + x_offset + x_jitter} Y{self.y + y_offset + y_jitter} F1000 ; 写字")
            
            self.gcode.append(f"G1 Z5 F1000 ; 抬起笔")
        
        def create_preview(self):
            """创建预览图像"""
            # 创建空白图像
            dpi = 72
            width_px = int(self.paper_width * dpi / 25.4)
            height_px = int(self.paper_height * dpi / 25.4)
            image = Image.new('RGB', (width_px, height_px), color='white')
            draw = ImageDraw.Draw(image)
            
            # 绘制边框
            margin_left_px = int(self.margin_left * dpi / 25.4)
            margin_top_px = int(self.margin_top * dpi / 25.4)
            margin_right_px = int(self.margin_right * dpi / 25.4)
            margin_bottom_px = int(self.margin_bottom * dpi / 25.4)
            
            draw.rectangle(
                [
                    margin_left_px, 
                    margin_top_px, 
                    width_px - margin_right_px, 
                    height_px - margin_bottom_px
                ],
                outline='lightgray'
            )
            
            # 解析G代码并绘制
            x, y = 0, 0
            pen_down = False
            
            for line in self.gcode:
                if 'G1 X' in line and 'Y' in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith('X'):
                            x = float(part[1:]) * dpi / 25.4
                        elif part.startswith('Y'):
                            y = float(part[1:]) * dpi / 25.4
                    
                    if pen_down:
                        draw.line([prev_x, prev_y, x, y], fill='black', width=1)
                    
                    prev_x, prev_y = x, y
                
                if 'Z0' in line:  # 笔放下
                    pen_down = True
                elif 'Z5' in line:  # 笔抬起
                    pen_down = False
            
            return image

    def generate_preview(text, font_path, font_size=8, margin_top=35, margin_bottom=25, 
                        margin_left=30, margin_right=30, paper_size='A4'):
        """生成预览图像和G代码"""
        generator = HandwritingGenerator(
            font_path=font_path,
            font_size=font_size,
            margin_top=margin_top,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            margin_right=margin_right,
            paper_size=paper_size
        )
        
        return generator.process_text(text)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            text = data.get('text', '')
            fontSize = data.get('fontSize', 8)
            marginTop = data.get('marginTop', 35)
            marginBottom = data.get('marginBottom', 25)
            marginLeft = data.get('marginLeft', 30)
            marginRight = data.get('marginRight', 30)
            paperSize = data.get('paperSize', 'A4')
            
            if not text:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': '文本内容不能为空'}).encode('utf-8'))
                return
            
            # 获取字体路径
            font_path = os.path.join(os.getcwd(), 'public', 'fonts', 'しょかきさらり行体.ttf')
            
            # 检查字体文件是否存在
            if not os.path.exists(font_path):
                # 尝试其他可能的路径
                alt_paths = [
                    os.path.join(os.getcwd(), 'fonts', 'しょかきさらり行体.ttf'),
                    os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), 'public', 'fonts', 'しょかきさらり行体.ttf')
                ]
                
                for path in alt_paths:
                    if os.path.exists(path):
                        font_path = path
                        break
                else:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': '字体文件不存在'}).encode('utf-8'))
                    return
            
            # 生成预览和G代码
            preview_base64, gcode_content = generate_preview(
                text=text,
                font_path=font_path,
                font_size=fontSize,
                margin_top=marginTop,
                margin_bottom=marginBottom,
                margin_left=marginLeft,
                margin_right=marginRight,
                paper_size=paperSize
            )
            
            # 创建会话ID
            session_id = str(uuid.uuid4())
            
            # 构建响应
            response = {
                'success': True,
                'previewBase64': preview_base64,
                'gcodeContent': gcode_content,
                'sessionId': session_id
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
