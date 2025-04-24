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
        """使用Pillow替代scikit-image"""
        img_size = (self.char_size*2, self.char_size*2)
        image = Image.new('L', img_size, 255)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_path, self.char_size)
        
        bbox = draw.textbbox((0,0), char, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (img_size[0] - text_width) // 2
        y = (img_size[1] - text_height) // 2
        
        draw.text((x,y), char, font=font, fill=0)
        
        # 使用Pillow和numpy处理图像
        img_array = np.array(image)
        # 二值化
        binary = img_array < 128
        # 骨架化（简化版）
        skeleton = self.skeletonize(binary)
        # 轮廓提取
        contours = self.find_contours(skeleton)
        
        return contours, (x,y,text_width,text_height)

    def skeletonize(self, binary):
        """简化版的骨架化算法"""
        skeleton = binary.copy()
        while True:
            eroded = self.erode(skeleton)
            if np.all(eroded == 0):
                break
            skeleton = eroded
        return skeleton

    def erode(self, img):
        """简化版的腐蚀操作"""
        kernel = np.ones((3,3), dtype=np.uint8)
        eroded = np.zeros_like(img)
        for i in range(1, img.shape[0]-1):
            for j in range(1, img.shape[1]-1):
                if img[i,j] and np.all(img[i-1:i+2, j-1:j+2] * kernel):
                    eroded[i,j] = 1
        return eroded

    def find_contours(self, binary):
        """简化版的轮廓提取"""
        contours = []
        visited = np.zeros_like(binary, dtype=bool)
        
        for i in range(binary.shape[0]):
            for j in range(binary.shape[1]):
                if binary[i,j] and not visited[i,j]:
                    contour = self.trace_contour(binary, visited, i, j)
                    if len(contour) > 2:
                        contours.append(np.array(contour))
        
        return contours

    def trace_contour(self, binary, visited, start_i, start_j):
        """追踪单个轮廓"""
        contour = []
        i, j = start_i, start_j
        directions = [(0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1), (-1,0), (-1,1)]
        dir_idx = 0
        
        while True:
            if visited[i,j]:
                break
            visited[i,j] = True
            contour.append([j,i])  # 注意坐标顺序
            
            # 寻找下一个点
            found = False
            for _ in range(8):
                di, dj = directions[dir_idx]
                ni, nj = i + di, j + dj
                if 0 <= ni < binary.shape[0] and 0 <= nj < binary.shape[1]:
                    if binary[ni,nj] and not visited[ni,nj]:
                        i, j = ni, nj
                        found = True
                        break
                dir_idx = (dir_idx + 1) % 8
            
            if not found:
                break
        
        return contour

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
        points = np.array(contour)
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
    def __init__(self, font_path: str = None, font_size: int = 8, margin_top: int = 35, margin_bottom: int = 25, 
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
        
        # 设置字符大小和间距
        self.char_size = self.font_size * 10  # 字符大小（10倍缩放）
        self.spacing_ratio_min = 0.06  # 字符间距最小比例
        self.spacing_ratio_max = 0.12  # 字符间距最大比例
        self.line_spacing = self.char_size * 1.35  # 行间距
        
        # 设置笔的参数
        self.pen_up_z = 0.0      # 笔抬起位置 (mm)
        self.pen_down_z = -7.0   # 笔落下位置 (mm)
        self.move_speed = 20000  # 移动速度 (mm/min)
        self.pen_speed = 20000   # 笔的上下速度 (mm/min)
        
        # 设置字符抖动参数
        self.vertical_wobble_min = -2  # 垂直抖动最小值
        self.vertical_wobble_max = 2   # 垂直抖动最大值
        
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
                
                # 获取字符的轮廓
                try:
                    contours, _ = self.get_font_strokes(char)
                    for contour in contours:
                        vertical_offset = self.get_vertical_wobble()
                        gcode_commands = self.generate_gcode(contour, self.x, self.y, vertical_offset)
                        self.gcode.extend(gcode_commands)
                except Exception as e:
                    log_debug(f"处理字符 '{char}' 时出错: {str(e)}")
                    # 跳过这个字符，继续处理下一个
                    continue
                
                # 更新位置
                self.x += self.get_random_spacing()
            
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
        return gcode_content, preview_base64
    
    def get_font_strokes(self, char: str) -> Tuple[List[np.ndarray], Tuple[int, int, int, int]]:
        """使用Pillow替代scikit-image"""
        img_size = (self.char_size*2, self.char_size*2)
        image = Image.new('L', img_size, 255)
        draw = ImageDraw.Draw(image)
        
        try:
            # 尝试使用加载的字体
            bbox = draw.textbbox((0,0), char, font=self.font)
        except Exception as e:
            log_debug(f"使用字体绘制字符失败: {str(e)}")
            # 使用默认字体
            bbox = draw.textbbox((0,0), char)
        
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (img_size[0] - text_width) // 2
        y = (img_size[1] - text_height) // 2
        
        try:
            # 尝试使用加载的字体
            draw.text((x,y), char, font=self.font, fill=0)
        except Exception as e:
            log_debug(f"使用字体绘制字符失败: {str(e)}")
            # 使用默认字体
            draw.text((x,y), char, fill=0)
        
        # 使用Pillow和numpy处理图像
        img_array = np.array(image)
        # 二值化
        binary = img_array < 128
        # 骨架化（简化版）
        skeleton = self.skeletonize(binary)
        # 轮廓提取
        contours = self.find_contours(skeleton)
        
        return contours, (x,y,text_width,text_height)

    def skeletonize(self, binary):
        """简化版的骨架化算法"""
        skeleton = binary.copy()
        while True:
            eroded = self.erode(skeleton)
            if np.all(eroded == 0):
                break
            skeleton = eroded
        return skeleton

    def erode(self, img):
        """简化版的腐蚀操作"""
        kernel = np.ones((3,3), dtype=np.uint8)
        eroded = np.zeros_like(img)
        for i in range(1, img.shape[0]-1):
            for j in range(1, img.shape[1]-1):
                if img[i,j] and np.all(img[i-1:i+2, j-1:j+2] * kernel):
                    eroded[i,j] = 1
        return eroded

    def find_contours(self, binary):
        """简化版的轮廓提取"""
        contours = []
        visited = np.zeros_like(binary, dtype=bool)
        
        for i in range(binary.shape[0]):
            for j in range(binary.shape[1]):
                if binary[i,j] and not visited[i,j]:
                    contour = self.trace_contour(binary, visited, i, j)
                    if len(contour) > 2:
                        contours.append(np.array(contour))
        
        return contours

    def trace_contour(self, binary, visited, start_i, start_j):
        """追踪单个轮廓"""
        contour = []
        i, j = start_i, start_j
        directions = [(0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1), (-1,0), (-1,1)]
        dir_idx = 0
        
        while True:
            if visited[i,j]:
                break
            visited[i,j] = True
            contour.append([j,i])  # 注意坐标顺序
            
            # 寻找下一个点
            found = False
            for _ in range(8):
                di, dj = directions[dir_idx]
                ni, nj = i + di, j + dj
                if 0 <= ni < binary.shape[0] and 0 <= nj < binary.shape[1]:
                    if binary[ni,nj] and not visited[ni,nj]:
                        i, j = ni, nj
                        found = True
                        break
                dir_idx = (dir_idx + 1) % 8
            
            if not found:
                break
        
        return contour

    def get_random_spacing(self):
        """文字サイズに比例したランダムな文字間隔を生成"""
        return random.uniform(self.spacing_ratio_min * self.char_size, self.spacing_ratio_max * self.char_size)

    def get_vertical_wobble(self):
        """ランダムな上下の揺れを生成"""
        return random.uniform(self.vertical_wobble_min, self.vertical_wobble_max) / 10

    def generate_gcode(self, contour, start_x, start_y, vertical_offset=0, scale=1.0):
        """輪郭からG-codeを生成（中心原点基準）"""
        points = np.array(contour)
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

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """处理 POST 请求"""
        try:
            # 记录详细的环境信息，帮助调试
            log_debug("===== 开始处理请求 =====")
            log_debug(f"当前工作目录: {os.getcwd()}")
            log_debug(f"目录内容: {os.listdir('.')}")
            log_debug(f"Python版本: {sys.version}")
            log_debug(f"Python路径: {sys.path}")
            
            # 获取请求体
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)
                log_debug(f"请求数据: {data}")
            except (KeyError, ValueError) as e:
                log_debug(f"请求体解析错误: {str(e)}")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "无效的请求格式",
                    "trace": str(e)
                }).encode())
                return
            
            # 验证必要参数
            text = data.get('text', '')
            if not text:
                log_debug("错误: 文本内容为空")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "文本内容不能为空",
                    "trace": "Empty text"
                }).encode())
                return
            
            # 创建生成器实例
            try:
                font_paths = [
                    os.path.join(os.getcwd(), 'public', 'fonts', 'しょかきさらり行体.ttf'),
                    os.path.join(os.getcwd(), 'fonts', 'しょかきさらり行体.ttf'),
                    os.path.join(os.getcwd(), 'しょかきさらり行体.ttf'),
                    '/var/task/public/fonts/しょかきさらり行体.ttf',
                    '/var/task/fonts/しょかきさらり行体.ttf',
                    '/var/task/しょかきさらり行体.ttf'
                ]
                
                font_path = None
                for path in font_paths:
                    if os.path.exists(path):
                        font_path = path
                        log_debug(f"找到字体文件: {path}")
                        break
                
                if not font_path:
                    log_debug("未找到字体文件，使用默认字体")
                    font_path = None  # 使用默认字体
                
                generator = HandwritingGenerator(
                    font_path=font_path,
                    font_size=8,
                    paper_size='A4'
                )
            except Exception as e:
                log_debug(f"生成器初始化错误: {str(e)}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "生成器初始化失败",
                    "trace": str(e)
                }).encode())
                return
            
            # 处理文本
            try:
                gcode_lines, preview_lines = generator.process_text(text)
                log_debug(f"处理完成，生成 {len(gcode_lines)} 行 G 代码")
            except Exception as e:
                log_debug(f"文本处理错误: {str(e)}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "文本处理失败",
                    "trace": str(e)
                }).encode())
                return
            
            # 发送响应
            try:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "gcode": gcode_lines,
                    "preview": preview_lines
                }).encode())
                log_debug("响应发送成功")
            except Exception as e:
                log_debug(f"响应发送错误: {str(e)}")
                # 这里不能发送新的响应，因为已经发送了响应头
            
        except Exception as e:
            log_debug(f"处理请求时出错: {str(e)}")
            log_debug(traceback.format_exc())
            try:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": str(e),
                    "trace": traceback.format_exc()
                }).encode())
            except:
                pass  # 如果响应已经发送，忽略错误

# 导出处理程序
handler = Handler
