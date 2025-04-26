import json
import os
import sys
import base64
from io import BytesIO
import tempfile
import shutil
import uuid
import traceback
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import random
import math
import functools
from typing import Any, Dict, List, Tuple, Union

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
        """生成与字符大小成比例的随机字符间距"""
        if char_width is None:
            char_width = self.char_size/10  # 默认大小
        
        # 基于字符宽度计算间距
        min_spacing = char_width * self.spacing_ratio_min * 10  # 10倍缩放
        max_spacing = char_width * self.spacing_ratio_max * 10
        
        return random.uniform(min_spacing, max_spacing)

    def get_vertical_wobble(self):
        """生成随机垂直抖动"""
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
        stroke_commands.append(f"G0 X{x_pos:.3f} Y{y_pos:.3f} F{self.move_speed}")
        
        # ペンを下ろす
        stroke_commands.append(f"G1 G90 Z{self.pen_down_z} F{self.pen_speed}")
        
        # ストロークの描画
        for point in points[1:]:
            x, y = point
            abs_x = start_x + x*scale/10
            abs_y = start_y + y*scale/10 + vertical_offset  # 上下の揺れを追加
            x_pos, y_pos = self.convert_to_center_coordinates(abs_x, abs_y)
            stroke_commands.append(f"G1 X{x_pos:.3f} Y{y_pos:.3f} F{self.move_speed}")
        
        # ペンを上げる
        stroke_commands.append(f"G1 G90 Z{self.pen_up_z} F{self.pen_speed}")
        
        return stroke_commands

# 简化版的手写生成器，直接内嵌在API中，避免导入问题
class HandwritingGenerator:
    def __init__(self, font_path: str = None, font_size: int = 8, margin_top: int = 35, margin_bottom: int = 25, 
                margin_left: int = 30, margin_right: int = 30, paper_size: str = 'A4'):
        self.font_path = font_path
        self.font_size = min(max(font_size, 6), 12)  # 限制字体大小在6-12之间
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
        
        # 计算页面中心坐标
        self.center_x = self.paper_width / 2
        self.center_y = self.paper_height / 2
        
        # 计算可写区域
        self.writing_width = self.paper_width - (self.margin_left + self.margin_right)
        self.writing_height = self.paper_height - (self.margin_top + self.margin_bottom)
        
        # 设置字符大小和间距（10倍缩放）
        self.char_size = self.font_size * 10  # 字体大小乘以10
        self.spacing_ratio_min = 0.06
        self.spacing_ratio_max = 0.12
        self.line_spacing = self.char_size * 1.35
        
        # 设置笔的参数
        self.pen_up_z = 0.0
        self.pen_down_z = -7.0
        self.move_speed = 20000
        self.pen_speed = 20000
        
        # 设置字符抖动参数
        self.vertical_wobble_min = -2
        self.vertical_wobble_max = 2
        
        # 加载字体
        try:
            if self.font_path and os.path.exists(self.font_path):
                log_debug(f"尝试加载字体: {self.font_path}")
                self.font = ImageFont.truetype(self.font_path, int(self.char_size))
                log_debug("字体加载成功")
            else:
                log_debug("使用默认字体")
                self.font = ImageFont.load_default()
        except Exception as e:
            log_debug(f"字体加载失败: {str(e)}")
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
        
        # 打印布局调试信息
        log_debug(f"=== Layout Debug ===")
        log_debug(f"Paper margins (absolute): L={self.margin_left}mm, R={self.margin_right}mm, "
                 f"T={self.margin_top}mm, B={self.margin_bottom}mm")
        log_debug(f"Writing area: {self.writing_width}x{self.writing_height}mm")

    def init_gcode(self) -> None:
        """初始化G代码"""
        self.gcode = [
            "G21 ; 设置单位为毫米",
            "G90 ; 使用绝对坐标",
            "G92 X0 Y0 Z0 ; 设置当前位置为原点",
            "G1 Z5 F1000 ; 抬起笔",
            f"G1 X{self.margin_left} Y{self.margin_top} F3000 ; 移动到起始位置"
        ]
    
    def process_text(self, text: str, max_pages: int = 3) -> Dict[str, Any]:
        try:
            log_debug("开始处理文本")
            preview_base64 = []
            gcode_content = []
            
            # エラー処理を追加
            if not text:
                raise ValueError("テキストが空です")
                
            # 处理文本
            lines = text.split('\n')
            for line in lines:
                if len(preview_base64) >= max_pages:
                    log_debug(f"达到最大页数限制: {max_pages}")
                    break
                
                if not line.strip():  # 空行
                    self.y += self.line_height
                    if self.y + self.line_height > self.margin_top + self.writing_height:
                        try:
                            preview_img = self.create_preview(max_pages)
                            buffered = BytesIO()
                            preview_img.save(buffered, format="PNG", optimize=True, quality=75)
                            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                            preview_base64.append(img_str)
                            log_debug(f"预览图像编码完成，长度: {len(img_str)}")
                        except Exception as e:
                            log_debug(f"生成预览图像时出错: {str(e)}")
                            raise
                        
                        gcode_content.append('\n'.join(self.gcode))
                        self.page_count += 1
                        self.x = self.margin_left
                        self.y = self.margin_top
                        self.init_gcode()
                    continue
                
                # 处理一行文字
                for char in line:
                    if len(preview_base64) >= max_pages:
                        break
                    
                    if self.x + self.font_size > self.margin_left + self.writing_width:
                        self.x = self.margin_left
                        self.y += self.line_height
                        
                        if self.y + self.line_height > self.margin_top + self.writing_height:
                            try:
                                preview_img = self.create_preview(max_pages)
                                buffered = BytesIO()
                                preview_img.save(buffered, format="PNG", optimize=True, quality=75)
                                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                                preview_base64.append(img_str)
                                log_debug(f"预览图像编码完成，长度: {len(img_str)}")
                            except Exception as e:
                                log_debug(f"生成预览图像时出错: {str(e)}")
                                raise
                            
                            gcode_content.append('\n'.join(self.gcode))
                            self.page_count += 1
                            self.x = self.margin_left
                            self.y = self.margin_top
                            self.init_gcode()
                    
                    try:
                        contours, _ = self.get_font_strokes(char)
                        for contour in contours:
                            vertical_offset = self.get_vertical_wobble()
                            gcode_commands = self.generate_gcode(contour, self.x, self.y, vertical_offset)
                            self.gcode.extend(gcode_commands)
                    except Exception as e:
                        log_debug(f"处理字符 '{char}' 时出错: {str(e)}")
                        continue
                    
                    self.x += self.get_random_spacing()
                
                if len(preview_base64) >= max_pages:
                    break
                
                self.x = self.margin_left
                self.y += self.line_height
                
                if self.y + self.line_height > self.margin_top + self.writing_height:
                    try:
                        preview_img = self.create_preview(max_pages)
                        buffered = BytesIO()
                        preview_img.save(buffered, format="PNG", optimize=True, quality=75)
                        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        preview_base64.append(img_str)
                        log_debug(f"预览图像编码完成，长度: {len(img_str)}")
                    except Exception as e:
                        log_debug(f"生成预览图像时出错: {str(e)}")
                        raise
                    
                    gcode_content.append('\n'.join(self.gcode))
                    self.page_count += 1
                    self.x = self.margin_left
                    self.y = self.margin_top
                    self.init_gcode()
            
            if len(preview_base64) < max_pages and self.gcode and self.gcode[-1] != "G1 Z5 F1000 ; 抬起笔":
                try:
                    preview_img = self.create_preview(max_pages)
                    buffered = BytesIO()
                    preview_img.save(buffered, format="PNG", optimize=True, quality=75)
                    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    preview_base64.append(img_str)
                    log_debug(f"预览图像编码完成，长度: {len(img_str)}")
                except Exception as e:
                    log_debug(f"生成预览图像时出错: {str(e)}")
                    raise
                
                gcode_content.append('\n'.join(self.gcode))
            
            return {
                "success": True,
                "previewBase64": preview_base64,
                "gcodeContent": gcode_content
            }
        except Exception as e:
            log_debug(f"处理文本时出错: {str(e)}")
            log_debug(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "trace": traceback.format_exc()
            }

    def get_font_strokes(self, char: str) -> Tuple[List[np.ndarray], Tuple[int, int, int, int]]:
        """获取字体笔画"""
        img_size = (self.char_size*2, self.char_size*2)
        image = Image.new('L', img_size, 255)
        draw = ImageDraw.Draw(image)
        
        # 绘制文字
        bbox = draw.textbbox((0,0), char, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (img_size[0] - text_width) // 2
        y = (img_size[1] - text_height) // 2
        
        draw.text((x,y), char, font=self.font, fill=0)
        
        # 使用Pillow和numpy处理图像
        img_array = np.array(image)
        # 二值化
        binary = img_array < 128
        
        # 简化版的轮廓提取
        contours = []
        visited = np.zeros_like(binary, dtype=bool)
        
        for i in range(binary.shape[0]):
            for j in range(binary.shape[1]):
                if binary[i,j] and not visited[i,j]:
                    contour = self._trace_contour(binary, visited, i, j)
                    if len(contour) > 2:
                        contours.append(np.array(contour))
        
        return contours, (x, y, text_width, text_height)

    def _trace_contour(self, binary: np.ndarray, visited: np.ndarray, start_i: int, start_j: int) -> List[List[int]]:
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

    def create_preview(self, max_pages: int = 3) -> Image.Image:
        """创建预览图像，限制最大页数"""
        try:
            # 提高DPI以提高清晰度
            dpi = 72  # 提高到72 DPI
            width_px = int(self.paper_width * dpi / 25.4)
            height_px = int(self.paper_height * dpi / 25.4)
            
            log_debug(f"创建预览图像: {width_px}x{height_px} 像素")
            
            # 创建白色背景图像
            image = Image.new('RGB', (width_px, height_px), 'white')
            draw = ImageDraw.Draw(image)
            
            # 计算边距（像素单位）
            margin_top_px = int(self.margin_top * dpi / 25.4)
            margin_right_px = int(self.margin_right * dpi / 25.4)
            margin_left_px = int(self.margin_left * dpi / 25.4)
            margin_bottom_px = int(self.margin_bottom * dpi / 25.4)
            
            # 绘制边距区域（浅灰色）
            draw.rectangle([0, 0, width_px, margin_top_px], fill=(240, 240, 240))
            draw.rectangle([0, height_px - margin_bottom_px, width_px, height_px], fill=(240, 240, 240))
            draw.rectangle([0, 0, margin_left_px, height_px], fill=(240, 240, 240))
            draw.rectangle([width_px - margin_right_px, 0, width_px, height_px], fill=(240, 240, 240))
            
            # 计算缩放比例和偏移
            scale = dpi / 25.4  # 毫米到像素的转换比例
            offset_x = self.center_x * scale
            offset_y = self.center_y * scale
            
            # 绘制机器人运动路径（蓝色）
            points = []
            pen_down = False
            
            for line in self.gcode:
                if line.startswith('G1') or line.startswith('G0'):
                    parts = line.split()
                    if len(parts) >= 2:
                        x_val = None
                        y_val = None
                        z_val = None
                        for part in parts[1:]:
                            if part.startswith('X'):
                                x_val = float(part[1:])
                            elif part.startswith('Y'):
                                y_val = float(part[1:])
                            elif part.startswith('Z'):
                                z_val = float(part[1:])
                                pen_down = z_val < 2.5
                        
                        if x_val is not None and y_val is not None:
                            # 转换坐标到像素，考虑中心偏移
                            x_px = int(x_val * scale + offset_x)
                            y_px = int(-y_val * scale + offset_y)  # Y轴反转
                            
                            # 确保坐标在图像范围内
                            x_px = max(0, min(x_px, width_px - 1))
                            y_px = max(0, min(y_px, height_px - 1))
                            
                            if pen_down:
                                points.append((x_px, y_px))
                            else:
                                if len(points) > 1:
                                    # 使用蓝色绘制机器人运动路径
                                    draw.line(points, fill=(0, 0, 255), width=1, joint="curve")
                                points = [(x_px, y_px)]
            
            # 绘制最后一条线
            if len(points) > 1:
                draw.line(points, fill=(0, 0, 255), width=1, joint="curve")
            
            # 绘制实际书写内容（黑色）
            points = []
            pen_down = False
            
            for line in self.gcode:
                if line.startswith('G1') or line.startswith('G0'):
                    parts = line.split()
                    if len(parts) >= 2:
                        x_val = None
                        y_val = None
                        z_val = None
                        for part in parts[1:]:
                            if part.startswith('X'):
                                x_val = float(part[1:])
                            elif part.startswith('Y'):
                                y_val = float(part[1:])
                            elif part.startswith('Z'):
                                z_val = float(part[1:])
                                pen_down = z_val < 2.5
                        
                        if x_val is not None and y_val is not None:
                            # 转换坐标到像素，考虑中心偏移
                            x_px = int(x_val * scale + offset_x)
                            y_px = int(-y_val * scale + offset_y)  # Y轴反转
                            
                            # 确保坐标在图像范围内
                            x_px = max(0, min(x_px, width_px - 1))
                            y_px = max(0, min(y_px, height_px - 1))
                            
                            if pen_down:
                                points.append((x_px, y_px))
                            else:
                                if len(points) > 1:
                                    # 使用黑色绘制实际书写内容
                                    draw.line(points, fill='black', width=2, joint="curve")
                                points = [(x_px, y_px)]
            
            # 绘制最后一条线
            if len(points) > 1:
                draw.line(points, fill='black', width=2, joint="curve")
            
            # 应用锐化滤镜提高清晰度
            image = image.filter(ImageFilter.SHARPEN)
            
            log_debug("预览图像生成完成")
            return image
        except Exception as e:
            log_debug(f"创建预览图像时出错: {str(e)}")
            raise

    def convert_to_center_coordinates(self, x, y):
        """将绝对坐标转换为以页面中心为原点的相对坐标"""
        # 计算相对于左上角的坐标
        center_relative_x = x - self.center_x
        center_relative_y = self.center_y - y  # Y轴向上为正
        return center_relative_x, center_relative_y

    def generate_gcode(self, contour, start_x, start_y, vertical_offset=0, scale=1.0):
        """从轮廓生成G代码（以中心为原点）"""
        points = np.array(contour)
        if len(points) < 2:
            return []
        
        stroke_commands = []
        
        # 移动到起始点（笔抬起状态）
        x, y = points[0]
        # 移除scale/10的缩放，因为contour已经是正确的大小
        abs_x = start_x + x
        abs_y = start_y + y + vertical_offset
        x_pos, y_pos = self.convert_to_center_coordinates(abs_x, abs_y)
        stroke_commands.append(f"G0 X{x_pos:.3f} Y{y_pos:.3f} F{self.move_speed}")
        
        # 落笔
        stroke_commands.append(f"G1 G90 Z{self.pen_down_z} F{self.pen_speed}")
        
        # 绘制笔画
        for point in points[1:]:
            x, y = point
            abs_x = start_x + x
            abs_y = start_y + y + vertical_offset
            x_pos, y_pos = self.convert_to_center_coordinates(abs_x, abs_y)
            stroke_commands.append(f"G1 X{x_pos:.3f} Y{y_pos:.3f} F{self.move_speed}")
        
        # 抬笔
        stroke_commands.append(f"G1 G90 Z{self.pen_up_z} F{self.pen_speed}")
        
        return stroke_commands

    def get_random_spacing(self, char_width=None):
        """生成与字符大小成比例的随机字符间距"""
        if char_width is None:
            char_width = self.font_size/10  # 默认大小
        
        # 基于字符宽度计算间距
        min_spacing = char_width * self.spacing_ratio_min * 10  # 10倍缩放
        max_spacing = char_width * self.spacing_ratio_max * 10
        
        return random.uniform(min_spacing, max_spacing)

    def get_vertical_wobble(self):
        """生成随机垂直抖动"""
        return random.uniform(self.vertical_wobble_min, self.vertical_wobble_max) / 10

# Vercel Serverless Function 处理函数
def handler(request):
    try:
        log_debug("===== 开始处理请求 =====")
        log_debug(f"当前工作目录: {os.getcwd()}")
        log_debug(f"目录内容: {os.listdir('.')}")
        log_debug(f"Python版本: {sys.version}")
        log_debug(f"Python路径: {sys.path}")
        
        # 获取请求体
        try:
            body = request.get('body', {})
            if isinstance(body, str):
                data = json.loads(body)
            else:
                data = body
            log_debug(f"请求数据: {data}")
        except (KeyError, ValueError) as e:
            log_debug(f"请求体解析错误: {str(e)}")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "status": "error",
                    "error": "invalid_request",
                    "message": "无效的请求格式",
                    "trace": str(e)
                }),
                "headers": {"Content-Type": "application/json; charset=utf-8"}
            }
        
        # 验证必要参数
        text = data.get('text', '')
        if not text:
            log_debug("错误: 文本内容为空")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "status": "error",
                    "error": "empty_text",
                    "message": "文本内容不能为空"
                }),
                "headers": {"Content-Type": "application/json; charset=utf-8"}
            }
        
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
                font_path = None
            
            generator = HandwritingGenerator(
                font_path=font_path,
                font_size=data.get('fontSize', 8),
                margin_top=data.get('marginTop', 35),
                margin_bottom=data.get('marginBottom', 25),
                margin_left=data.get('marginLeft', 30),
                margin_right=data.get('marginRight', 30),
                paper_size=data.get('paperSize', 'A4')
            )
        except Exception as e:
            log_debug(f"生成器初始化错误: {str(e)}")
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "status": "error",
                    "error": "generator_init_failed",
                    "message": "生成器初始化失败",
                    "trace": traceback.format_exc()
                }),
                "headers": {"Content-Type": "application/json; charset=utf-8"}
            }
        
        # 处理文本
        try:
            result = generator.process_text(text)
            if not result.get("success", False):
                raise Exception(result.get("error", "未知错误"))
            
            # 返回响应
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "success",
                    "previewBase64": result.get("previewBase64", []),
                    "gcodeContent": result.get("gcodeContent", [])
                }),
                "headers": {"Content-Type": "application/json; charset=utf-8"}
            }
        except Exception as e:
            log_debug(f"文本处理错误: {str(e)}")
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "status": "error",
                    "error": "text_processing_failed",
                    "message": "文本处理失败",
                    "trace": traceback.format_exc()
                }),
                "headers": {"Content-Type": "application/json; charset=utf-8"}
            }
    except Exception as e:
        log_debug(f"处理请求时出错: {str(e)}")
        log_debug(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "error": "internal_server_error",
                "message": "服务器内部错误",
                "trace": traceback.format_exc()
            }),
            "headers": {"Content-Type": "application/json; charset=utf-8"}
        }
