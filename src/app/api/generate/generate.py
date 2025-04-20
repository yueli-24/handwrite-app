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

# 调试信息
DEBUG = True

def log_debug(message):
    """记录调试信息"""
    if DEBUG:
        print(f"DEBUG: {message}")
        sys.stdout.flush()

def safe_handler(handler_func):
    """装饰器：确保handler函数始终返回有效的JSON响应，即使发生未捕获的异常"""
    @functools.wraps(handler_func)
    def wrapper(request):
        try:
            log_debug(f"===== 开始处理请求 =====")
            log_debug(f"Python版本: {sys.version}")
            log_debug(f"当前工作目录: {os.getcwd()}")
            
            # 调用原始handler函数
            return handler_func(request)
        except Exception as e:
            # 捕获所有未处理的异常
            error_message = f"未捕获的异常: {str(e)}"
            error_trace = traceback.format_exc()
            log_debug(error_message)
            log_debug(f"错误详情: {error_trace}")
            
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

# 记录环境信息
log_debug(f"当前工作目录: {os.getcwd()}")
log_debug(f"目录内容: {os.listdir('.')}")
log_debug(f"Python版本: {sys.version}")
log_debug(f"Python路径: {sys.path}")

# 简化版的手写生成器，直接内嵌在API中，避免导入问题
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
                import random
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
    
    def add_char_gcode(self, char):
        """为字符添加G代码"""
        # 简化版本，实际应该根据字体轮廓生成G代码
        # 这里只是模拟一个简单的写字动作
        import random
        x_jitter = 0.2 * random.random() - 0.1  # -0.1到0.1的随机抖动
        y_jitter = 0.2 * random.random() - 0.1  # -0.1到0.1的随机抖动
        
        self.gcode.append(f"G1 Z5 F1000 ; 抬起笔")
        self.gcode.append(f"G1 X{self.x + x_jitter} Y{self.y + y_jitter} F3000 ; 移动到字符位置")
        self.gcode.append(f"G1 Z0 F1000 ; 放下笔")
        
        # 模拟写字的几个点
        import math
        for i in range(5):
            x_offset = (i / 4) * self.font_size * 0.8
            y_offset = math.sin(i * math.pi / 2) * self.font_size * 0.3
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
        prev_x, prev_y = 0, 0
        
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

def generate_preview(text, font_size=8, margin_top=35, margin_bottom=25, 
                    margin_left=30, margin_right=30, paper_size='A4'):
    """生成预览图像和G代码"""
    log_debug("开始生成预览")
    
    # 使用内置默认字体
    font_path = None
    
    # 尝试查找字体文件
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
        # 使用PIL默认字体
        font_path = ""
    
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

@safe_handler
def handler(request):
    """Vercel Python Serverless Function处理器
    
    按照Vercel要求的格式：def handler(request)
    request是一个HTTP请求对象，而不是事件字典
    使用safe_handler装饰器确保始终返回有效的JSON响应
    """
    try:
        # 记录详细的环境信息，帮助调试
        log_debug("===== 开始处理请求 =====")
        log_debug(f"Python版本: {sys.version}")
        log_debug(f"当前工作目录: {os.getcwd()}")
        log_debug(f"目录内容: {os.listdir('.')}")
        log_debug(f"请求方法: {request.method}")
        log_debug(f"请求头: {request.headers if hasattr(request, 'headers') else 'No headers attribute'}")
        
        # 检查请求方法
        if request.method != 'POST':
            log_debug("错误: 仅支持POST请求")
            return {
                "statusCode": 405,
                "body": json.dumps({"error": "仅支持POST请求", "trace": "Method not allowed"}),
                "headers": {"Content-Type": "application/json"}
            }
        
        # 解析请求体
        try:
            # 获取请求体
            try:
                log_debug("尝试获取请求体...")
                
                # 记录请求对象的属性，帮助调试
                request_attrs = [attr for attr in dir(request) if not attr.startswith('_')]
                log_debug(f"请求对象属性: {request_attrs}")
                
                # 尝试多种方式获取请求体
                body = None
                
                # 方式1: 直接访问body属性
                if hasattr(request, 'body'):
                    body = request.body
                    log_debug(f"通过request.body获取到请求体，类型: {type(body)}")
                
                # 方式2: 尝试使用read方法
                elif hasattr(request, 'read') and callable(request.read):
                    body = request.read()
                    log_debug(f"通过request.read()获取到请求体，类型: {type(body)}")
                
                # 方式3: 尝试使用json方法
                elif hasattr(request, 'json') and callable(request.json):
                    try:
                        body = request.json()
                        log_debug(f"通过request.json()获取到请求体，类型: {type(body)}")
                    except Exception as json_err:
                        log_debug(f"request.json()方法失败: {str(json_err)}")
                
                # 检查是否获取到请求体
                if body is None:
                    log_debug("错误: 无法获取请求体")
                    return {
                        "statusCode": 400,
                        "body": json.dumps({
                            "error": "无法获取请求体", 
                            "trace": "Request body is None, tried body attribute, read() and json() methods"
                        }),
                        "headers": {"Content-Type": "application/json"}
                    }
                
                # 尝试解析JSON
                if isinstance(body, dict):
                    data = body
                    log_debug("请求体已经是字典类型，无需解析")
                elif isinstance(body, bytes):
                    body_str = body.decode('utf-8')
                    log_debug(f"请求体(bytes->str): {body_str[:200]}...")
                    data = json.loads(body_str)
                elif isinstance(body, str):
                    log_debug(f"请求体(str): {body[:200]}...")
                    data = json.loads(body)
                else:
                    log_debug(f"错误: 无法处理的请求体类型: {type(body)}")
                    return {
                        "statusCode": 400,
                        "body": json.dumps({
                            "error": f"无法处理的请求体类型: {type(body)}", 
                            "trace": f"Unsupported body type: {type(body)}"
                        }),
                        "headers": {"Content-Type": "application/json"}
                    }
            except Exception as e:
                log_debug(f"获取或解析请求体时出错: {str(e)}")
                log_debug(f"错误详情: {traceback.format_exc()}")
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": f"获取或解析请求体时出错: {str(e)}", 
                        "trace": traceback.format_exc()
                    }),
                    "headers": {"Content-Type": "application/json"}
                }
            
            log_debug(f"请求数据: {data}")
            
            # 提取参数
            try:
                text = data.get('text', '')
                fontSize = data.get('fontSize', 8)
                marginTop = data.get('marginTop', 35)
                marginBottom = data.get('marginBottom', 25)
                marginLeft = data.get('marginLeft', 30)
                marginRight = data.get('marginRight', 30)
                paperSize = data.get('paperSize', 'A4')
                
                log_debug(f"提取的参数: text长度={len(text)}, fontSize={fontSize}, marginTop={marginTop}, marginBottom={marginBottom}, marginLeft={marginLeft}, marginRight={marginRight}, paperSize={paperSize}")
            except Exception as param_err:
                log_debug(f"提取参数时出错: {str(param_err)}")
                log_debug(f"错误详情: {traceback.format_exc()}")
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": f"提取参数时出错: {str(param_err)}", 
                        "trace": traceback.format_exc()
                    }),
                    "headers": {"Content-Type": "application/json"}
                }
            
            if not text:
                log_debug("错误: 文本内容为空")
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": "文本内容不能为空", 
                        "trace": "Empty text parameter"
                    }),
                    "headers": {"Content-Type": "application/json"}
                }
            
            # 生成预览和G代码
            try:
                log_debug("开始生成预览和G代码...")
                preview_base64, gcode_content = generate_preview(
                    text=text,
                    font_size=fontSize,
                    margin_top=marginTop,
                    margin_bottom=marginBottom,
                    margin_left=marginLeft,
                    margin_right=marginRight,
                    paper_size=paperSize
                )
                
                # 创建会话ID
                session_id = str(uuid.uuid4())
                log_debug(f"生成会话ID: {session_id}")
                
                # 构建响应
                response = {
                    'success': True,
                    'previewBase64': preview_base64,
                    'gcodeContent': gcode_content,
                    'sessionId': session_id
                }
                
                log_debug(f"生成成功，共 {len(preview_base64)} 页")
                log_debug("===== 请求处理完成 =====")
                
                return {
                    "statusCode": 200,
                    "body": json.dumps(response),
                    "headers": {"Content-Type": "application/json"}
                }
                
            except Exception as e:
                log_debug(f"生成预览时出错: {str(e)}")
                log_debug(f"错误详情: {traceback.format_exc()}")
                return {
                    "statusCode": 500,
                    "body": json.dumps({
                        "error": f"生成预览时出错: {str(e)}",
                        "trace": traceback.format_exc()
                    }),
                    "headers": {"Content-Type": "application/json"}
                }
            
        except json.JSONDecodeError as e:
            log_debug(f"JSON解析错误: {str(e)}")
            log_debug(f"错误详情: {traceback.format_exc()}")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"无效的JSON格式: {str(e)}", 
                    "trace": traceback.format_exc()
                }),
                "headers": {"Content-Type": "application/json"}
            }
            
    except Exception as e:
        log_debug(f"处理请求时出错: {str(e)}")
        log_debug(f"错误详情: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"处理请求时出错: {str(e)}",
                "trace": traceback.format_exc()
            }),
            "headers": {"Content-Type": "application/json"}
        }
