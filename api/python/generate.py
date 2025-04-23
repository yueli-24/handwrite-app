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
import cv2
from skimage.morphology import skeletonize
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

# 集成 StrokeWriter 类
class StrokeWriter:
    def __init__(self):
        # A4レイアウト設定（mm単位）
        self.page_width = 210
        self.page_height = 297
        
        # A4の中心座標を計算
        self.center_x = self.page_width / 2  # 105mm
        self.center_y = self.page_height / 2  # 148.5mm
        
        # A4紙に対する絶対余白（mm単位）
        self.paper_margin_left = 30   # 左余白30mm
        self.paper_margin_right = 30  # 右余白30mm
        self.paper_margin_top = 35    # 上余白35mm
        self.paper_margin_bottom = 25 # 下余白25mm
        
        # 文字サイズと間隔の設定（mm単位）
        self.char_size = 60  # 8mm程度の文字（10倍スケール）
        # 文字間隔を文字サイズに対する比率で定義
        self.spacing_ratio_min = 0.06  # 文字サイズの6%
        self.spacing_ratio_max = 0.12  # 文字サイズの12%
        self.line_spacing = self.char_size * 1.35  # 文字サイズの1.35倍
        
        # ペン設定
        self.pen_up_z = 0.0      # ペンが上がった位置 (mm)
        self.pen_down_z = -7.0   # ペンが下がった位置 (mm)
        self.move_speed = 20000  # 移動速度 (mm/min)
        self.pen_speed = 20000   # ペンの上下速度 (mm/min)
        
        # 実際の書き込み可能領域を計算
        self.writing_width = self.page_width - (self.paper_margin_left + self.paper_margin_right)
        self.writing_height = self.page_height - (self.paper_margin_top + self.paper_margin_bottom)
        
        # 文字の揺れ設定（mm単位）
        self.vertical_wobble_min = -2  # 上下の揺れ最小値 -0.2mm（10倍スケール）
        self.vertical_wobble_max = 2   # 上下の揺れ最大値 0.2mm（10倍スケール）
        
        # 改行を防ぐ記号のリスト
        self.no_break_chars = ['、', '。', '，', '．', '」', '』', '）', '｝', '］',
                             ',', '.', ')', '}', ']', '!', '?', '！', '？']
        # 前の文字と離さない記号のリスト
        self.keep_with_prev_chars = ['」', '』', '）', '｝', '］', ')', '}', ']']
        
        print(f"=== Layout Debug ===")
        print(f"Paper margins (absolute): L={self.paper_margin_left}mm, R={self.paper_margin_right}mm, " 
              f"T={self.paper_margin_top}mm, B={self.paper_margin_bottom}mm")
        print(f"Writing area: {self.writing_width}x{self.writing_height}mm")

    def convert_to_center_coordinates(self, x, y):
        """絶対座標を中心原点の相対座標に変換"""
        # 左上からの座標を中心からの座標に変換
        center_relative_x = x - self.center_x
        center_relative_y = -(y - self.center_y)  # Y軸は上が負
        return center_relative_x, center_relative_y

    def get_font_strokes(self, char, font_path):
        """フォントから文字のストロークを抽出"""
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
        """文字サイズに比例したランダムな文字間隔を生成"""
        if char_width is None:
            char_width = self.char_size/10  # デフォルトサイズ
        
        # 文字幅に基づいて間隔を計算
        min_spacing = char_width * self.spacing_ratio_min * 10  # 10倍スケールに戻す
        max_spacing = char_width * self.spacing_ratio_max * 10
        
        return random.uniform(min_spacing, max_spacing)

    def get_vertical_wobble(self):
        """ランダムな上下の揺れを生成"""
        return random.uniform(self.vertical_wobble_min, self.vertical_wobble_max) / 10

    def generate_gcode(self, contour, start_x, start_y, vertical_offset=0, scale=1.0):
        """輪郭からG-codeを生成（中心原点基準）"""
        points = contour.reshape(-1, 2)
        if len(points) < 2:
            return []
        
        stroke_commands = []
        
        # 開始点への移動（ペンを上げた状態で）
        x, y = points[0]
        abs_x = start_x + x*scale/10
        abs_y = start_y + y*scale/10 + vertical_offset  # 上下の揺れを追加
        x_pos, y_pos = self.convert_to_center_coordinates(abs_x, abs_y)
        stroke_commands.append(f"G0 X{x_pos:.3f}Y{y_pos:.3f}F{self.move_speed}")
        
        # ペンを下ろす
        stroke_commands.append(f"G1G90 Z{self.pen_down_z}F{self.pen_speed}")
        
        # ストロークの描画
        for point in points[1:]:
            x, y = point
            abs_x = start_x + x*scale/10
            abs_y = start_y + y*scale/10 + vertical_offset  # 上下の揺れを追加
            x_pos, y_pos = self.convert_to_center_coordinates(abs_x, abs_y)
            stroke_commands.append(f"G1 X{x_pos:.3f}Y{y_pos:.3f}F{self.move_speed}")
        
        # ペンを上げる
        stroke_commands.append(f"G1G90 Z{self.pen_up_z}F{self.pen_speed}")
        
        return stroke_commands

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
        
        stroke_writer = StrokeWriter()
        
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
                
                # 获取字符的轮廓
                contours, _ = stroke_writer.get_font_strokes(char, self.font_path)
                for contour in contours:
                    vertical_offset = stroke_writer.get_vertical_wobble()
                    gcode_commands = stroke_writer.generate_gcode(contour, self.x, self.y, vertical_offset)
                    self.gcode.extend(gcode_commands)
                
                # 更新位置
                self.x += stroke_writer.get_random_spacing()
            
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
            if line.startswith('G1') or line.startswith('G0'):
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

def safe_handler(handler_func):
    """装饰器：确保handler函数始终返回有效的JSON响应，即使发生未捕获的异常"""
    @functools.wraps(handler_func)
    def wrapper(request):
        try:
            # 调用原始handler函数
            return handler_func(request)
        except Exception as e:
            # 捕获所有未处理的异常
            error_message = f"未捕获的异常: {str(e)}"
            error_trace = traceback.format_exc()
            
            # 确保返回有效的JSON响应
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": error_message,
                    "trace": error_trace
                }),
                "headers": {"Content-Type": "application/json"}
            }
    return wrapper

@safe_handler
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
        text = data.get('text', '')
        if not text:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "文本内容不能为空",
                    "trace": "Empty text"
                }),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }
        
        # 创建生成器实例
        generator = HandwritingGenerator(
            font_path='fonts/NotoSansSC-Regular.otf',
            font_size=8,
            paper_size='A4'
        )
        
        # 处理文本
        gcode_lines, preview_lines = generator.process_text(text)
        
        # 返回结果
        return {
            "statusCode": 200,
            "body": json.dumps({
                "gcode": gcode_lines,
                "preview": preview_lines
            }),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }
        
    except Exception as e:
        log_debug(f"处理请求时出错: {str(e)}")
        log_debug(traceback.format_exc())
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
