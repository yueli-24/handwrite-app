import json
import os
import sys
import base64
from io import BytesIO
import tempfile
import shutil
import uuid
import traceback
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import math
import functools
from typing import Any, Dict, List, Tuple, Union
from http.server import BaseHTTPRequestHandler

# 调试信息
DEBUG = True

def log_debug(message):
    """记录调试信息"""
    if DEBUG:
        print(f"DEBUG: {message}")
        sys.stdout.flush()

# 记录环境信息
log_debug(f"当前工作目录: {os.getcwd()}")
log_debug(f"目录内容: {os.listdir('.')}")
log_debug(f"Python版本: {sys.version}")
log_debug(f"Python路径: {sys.path}")

# 简化版的手写生成器，直接内嵌在API中，避免导入问题
class HandwritingGenerator:
    def __init__(self, font_path: str, font_size: int = 8, margin_top: int = 35, margin_bottom: int = 25, 
                margin_left: int = 30, margin_right: int = 30, paper_size: str = 'A4'):
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
        try:
            if self.font_path and os.path.exists(self.font_path):
                log_debug(f"尝试加载字体: {self.font_path}")
                self.font = ImageFont.truetype(self.font_path, int(self.font_size * 10))
                log_debug("字体加载成功")
            else:
                # 直接使用默认字体
                log_debug("使用默认字体")
                self.font = ImageFont.load_default()
        except Exception as e:
            log_debug(f"字体加载失败: {str(e)}")
            # 使用默认字体作为备选
            self.font = ImageFont.load_default()
            log_debug("已加载默认字体")
        
        # 初始化当前位置
        self.x = self.margin_left
        self.y = self.margin_top
        self.line_height = self.font_size * 1.5  # 行高为字体大小的1.5倍
        
        # 初始化页面计数
        self.page_count = 1
        
        # 初始化G代码
        self.gcode = []
        self.init_gcode()
    
    def init_gcode(self) -> None:
        """初始化G代码"""
        self.gcode = [
            "G21 ; 设置单位为毫米",
            "G90 ; 使用绝对坐标",
            "G92 X0 Y0 Z0 ; 设置当前位置为原点",
            "G1 Z5 F1000 ; 抬起笔",
            f"G1 X{self.margin_left} Y{self.margin_top} F3000 ; 移动到起始位置"
        ]
    
    def process_text(self, text: str) -> Tuple[List[str], List[str]]:
        """处理文本，生成G代码和预览图像"""
        log_debug("开始处理文本")
        # 直接在内存中处理，避免文件系统操作
        preview_base64 = []
        gcode_content = []
        
        # 处理文本
        lines = text.split('\n')
        for line in lines:
            if not line.strip():  # 空行
                self.y += self.line_height
                if self.y + self.line_height > self.margin_top + self.writing_height:
                    # 创建预览图像
                    preview_img = self.create_preview()
                    # 直接转换为base64
                    buffered = BytesIO()
                    preview_img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    preview_base64.append(img_str)
                    
                    # 保存G代码
                    gcode_content.append('\n'.join(self.gcode))
                    
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
                        # 直接转换为base64
                        buffered = BytesIO()
                        preview_img.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        preview_base64.append(img_str)
                        
                        # 保存G代码
                        gcode_content.append('\n'.join(self.gcode))
                        
                        # 准备新页面
                        self.page_count += 1
                        self.x = self.margin_left
                        self.y = self.margin_top
                        self.init_gcode()
                
                # 添加字符的G代码
                self.add_char_gcode(char)
                
                # 更新位置
                self.x += self.font_size * (1 + 0.1 * random.random())  # 添加一些随机间距
            
            # 行尾换行
            self.x = self.margin_left
            self.y += self.line_height
            
            # 检查是否需要新页面
            if self.y + self.line_height > self.margin_top + self.writing_height:
                # 创建预览图像
                preview_img = self.create_preview()
                # 直接转换为base64
                buffered = BytesIO()
                preview_img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                preview_base64.append(img_str)
                
                # 保存G代码
                gcode_content.append('\n'.join(self.gcode))
                
                # 准备新页面
                self.page_count += 1
                self.x = self.margin_left
                self.y = self.margin_top
                self.init_gcode()
        
        # 处理最后一页
        if self.gcode and self.gcode[-1] != "G1 Z5 F1000 ; 抬起笔":
            # 创建预览图像
            preview_img = self.create_preview()
            # 直接转换为base64
            buffered = BytesIO()
            preview_img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            preview_base64.append(img_str)
            
            # 保存G代码
            gcode_content.append('\n'.join(self.gcode))
        
        log_debug(f"文本处理完成，生成了 {len(preview_base64)} 页")
        return preview_base64, gcode_content
    
    def add_char_gcode(self, char: str) -> None:
        """为字符添加G代码"""
        # 简化版本，实际应该根据字体轮廓生成G代码
        # 这里只是模拟一个简单的写字动作
        x_jitter = 0.2 * random.random() - 0.1  # -0.1到0.1的随机抖动
        y_jitter = 0.2 * random.random() - 0.1  # -0.1到0.1的随机抖动
        
        self.gcode.append(f"G1 Z5 F1000 ; 抬起笔")
        self.gcode.append(f"G1 X{self.x + x_jitter} Y{self.y + y_jitter} F3000 ; 移动到字符位置")
        self.gcode.append(f"G1 Z0 F1000 ; 放下笔")
        
        # 模拟写字的几个点
        for i in range(5):
            x_offset = (i / 4) * self.font_size * 0.8
            y_offset = math.sin(i * math.pi / 2) * self.font_size * 0.3
            self.gcode.append(f"G1 X{self.x + x_offset + x_jitter} Y{self.y + y_offset + y_jitter} F1000 ; 写字")
        
        self.gcode.append(f"G1 Z5 F1000 ; 抬起笔")
    
    def create_preview(self) -> Image.Image:
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
        prev_x, prev_y = 0, 0
        
        for line in self.gcode:
            if line.startswith('G1'):
                parts = line.split()
                if len(parts) >= 2:
                    x_val = None
                    y_val = None
                    for part in parts[1:]:
                        if part.startswith('X'):
                            x_val = float(part[1:])
                        elif part.startswith('Y'):
                            y_val = float(part[1:])
                        elif part.startswith('Z'):
                            z_val = float(part[1:])
                            pen_down = z_val < 2.5  # 如果Z值小于2.5，认为笔是放下的
                    
                    if x_val is not None and y_val is not None:
                        # 转换坐标到像素
                        x_px = int(x_val * dpi / 25.4)
                        y_px = int(y_val * dpi / 25.4)
                        
                        if pen_down and prev_x is not None and prev_y is not None:
                            # 绘制线条
                            draw.line([(prev_x, prev_y), (x_px, y_px)], fill='black', width=1)
                        
                        prev_x, prev_y = x_px, y_px
        
        return image

def handler(request):
    """Vercel Python Serverless Function处理器"""
    try:
        # 记录详细的环境信息，帮助调试
        log_debug("===== 开始处理请求 =====")
        log_debug(f"当前工作目录: {os.getcwd()}")
        log_debug(f"目录内容: {os.listdir('.')}")
        log_debug(f"Python版本: {sys.version}")
        log_debug(f"Python路径: {sys.path}")
        
        # 获取请求方法
        request_method = getattr(request, 'method', 'UNKNOWN')
        log_debug(f"请求方法: {request_method}")
        
        # 检查请求方法
        if request_method != 'POST':
            log_debug("错误: 仅支持POST请求")
            return {
                "statusCode": 405,
                "body": json.dumps({
                    "error": "仅支持POST请求",
                    "trace": "Method not allowed"
                }),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }
        
        # 解析请求体
        try:
            # 获取请求体
            body = None
            if hasattr(request, 'body'):
                body = request.body
                log_debug(f"通过request.body获取到请求体，类型: {type(body)}")
            elif hasattr(request, 'read') and callable(request.read):
                body = request.read()
                log_debug(f"通过request.read()获取到请求体，类型: {type(body)}")
            elif hasattr(request, 'json') and callable(request.json):
                body = request.json()
                log_debug(f"通过request.json()获取到请求体，类型: {type(body)}")
            
            if not body:
                log_debug("无法获取请求体")
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": "无法获取请求体",
                        "trace": "No request body found"
                    }),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }
            
            # 解析JSON
            try:
                if isinstance(body, str):
                    data = json.loads(body)
                elif isinstance(body, bytes):
                    data = json.loads(body.decode('utf-8'))
                else:
                    data = body
                log_debug(f"解析后的数据: {data}")
            except json.JSONDecodeError as e:
                log_debug(f"JSON解析错误: {str(e)}")
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": "无效的JSON格式",
                        "trace": str(e)
                    }),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }
            
            # 验证必要参数
            required_fields = ['text', 'fontSize', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'paperSize']
            for field in required_fields:
                if field not in data:
                    log_debug(f"缺少必要参数: {field}")
                    return {
                        "statusCode": 400,
                        "body": json.dumps({
                            "error": f"缺少必要参数: {field}",
                            "trace": f"Missing required field: {field}"
                        }),
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*"
                        }
                    }
            
            # 尝试加载字体文件
            font_paths = [
                os.path.join(os.getcwd(), 'public', 'fonts', 'NotoSansSC-Regular.ttf'),
                os.path.join(os.getcwd(), 'fonts', 'NotoSansSC-Regular.ttf'),
                os.path.join(os.getcwd(), 'NotoSansSC-Regular.ttf'),
                '/var/task/public/fonts/NotoSansSC-Regular.ttf',
                '/var/task/fonts/NotoSansSC-Regular.ttf',
                '/var/task/NotoSansSC-Regular.ttf'
            ]
            
            font_path = None
            for path in font_paths:
                if os.path.exists(path):
                    font_path = path
                    log_debug(f"找到字体文件: {path}")
                    break
            
            if not font_path:
                log_debug("未找到字体文件")
                return {
                    "statusCode": 500,
                    "body": json.dumps({
                        "error": "未找到字体文件",
                        "trace": "Font file not found"
                    }),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }
            
            # 创建生成器实例
            generator = HandwritingGenerator(
                font_path=font_path,
                font_size=data['fontSize'],
                margin_top=data['marginTop'],
                margin_bottom=data['marginBottom'],
                margin_left=data['marginLeft'],
                margin_right=data['marginRight'],
                paper_size=data['paperSize']
            )
            
            # 处理文本
            preview_base64, gcode_content = generator.process_text(data['text'])
            
            # 返回结果
            response = {
                "statusCode": 200,
                "body": json.dumps({
                    "previewBase64": preview_base64,
                    "gcodeContent": gcode_content
                }),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }
            
            log_debug(f"返回响应: {response}")
            return response
            
        except Exception as e:
            log_debug(f"处理请求时发生错误: {str(e)}")
            log_debug(f"错误堆栈: {traceback.format_exc()}")
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": str(e),
                    "trace": traceback.format_exc()
                }),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }
            
    except Exception as e:
        log_debug(f"处理请求时发生未捕获的错误: {str(e)}")
        log_debug(f"错误堆栈: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "服务器内部错误",
                "trace": traceback.format_exc()
            }),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }
