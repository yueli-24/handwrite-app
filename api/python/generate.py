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
            "G21",          # mmモード
            "G90",          # 絶対座標モード
            f"F20000",      # 基本送り速度設定
            "G1G90 Z0.0F20000"  # 初期位置でペンを上げる
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
        # 这里需要实现具体的字符G代码生成逻辑
        pass

    def create_preview(self) -> Image.Image:
        """创建预览图像"""
        # 这里需要实现具体的预览图像生成逻辑
        pass

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
            required_params = ['text']
            missing_params = [param for param in required_params if param not in data]
            if missing_params:
                log_debug(f"缺少必要参数: {missing_params}")
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": f"缺少必要参数: {', '.join(missing_params)}",
                        "trace": "Missing required parameters"
                    }),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }

            # 获取参数
            text = data.get('text', '')
            font_size = int(data.get('fontSize', 8))
            margin_top = int(data.get('marginTop', 35))
            margin_bottom = int(data.get('marginBottom', 25))
            margin_left = int(data.get('marginLeft', 30))
            margin_right = int(data.get('marginRight', 30))
            paper_size = data.get('paperSize', 'A4')

            # 验证参数
            if not text.strip():
                log_debug("文本内容为空")
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": "文本内容不能为空",
                        "trace": "Empty text content"
                    }),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }

            # 尝试查找字体文件
            font_path = None
            possible_font_paths = [
                os.path.join(os.getcwd(), 'public', 'fonts', 'しょかきさらり行体.ttf'),
                os.path.join(os.getcwd(), 'fonts', 'しょかきさらり行体.ttf'),
                os.path.join(os.path.dirname(os.getcwd()), 'public', 'fonts', 'しょかきさらり行体.ttf'),
                os.path.join('/tmp', 'fonts', 'しょかきさらり行体.ttf'),
                # Vercel环境中的可能路径
                '/var/task/public/fonts/しょかきさらり行体.ttf',
                '/var/task/fonts/しょかきさらり行体.ttf'
            ]

            for path in possible_font_paths:
                log_debug(f"检查字体路径: {path}")
                if os.path.exists(path):
                    font_path = path
                    log_debug(f"找到字体文件: {path}")
                    break

            if not font_path:
                log_debug("未找到字体文件，将使用默认字体")
                font_path = ""

            # 生成预览
            try:
                log_debug("开始生成预览")
                generator = HandwritingGenerator(
                    font_path=font_path,
                    font_size=font_size,
                    margin_top=margin_top,
                    margin_bottom=margin_bottom,
                    margin_left=margin_left,
                    margin_right=margin_right,
                    paper_size=paper_size
                )

                preview_base64, gcode_content = generator.process_text(text)

                # 构建响应
                response = {
                    "success": True,
                    "sessionId": str(uuid.uuid4()),