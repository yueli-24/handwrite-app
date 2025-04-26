from http.server import BaseHTTPRequestHandler
from .generate import handler as generate_handler
import json

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 获取请求内容长度
        content_length = int(self.headers['Content-Length'])
        # 读取请求体
        post_data = self.rfile.read(content_length)
        
        # 构造请求对象传递给实际的处理函数
        request = {
            'body': post_data.decode('utf-8'),
            'headers': dict(self.headers),
            'method': 'POST',
            'path': self.path
        }
        
        # 如果请求体是JSON格式，解析它
        if 'application/json' in self.headers.get('Content-Type', ''):
            try:
                request['body'] = json.loads(request['body'])
            except:
                pass
        
        # 调用实际的处理函数
        response = generate_handler(request)
        
        # 设置响应状态码
        self.send_response(response.get('statusCode', 200))
        
        # 设置响应头
        for header, value in response.get('headers', {}).items():
            self.send_header(header, value)
        self.end_headers()
        
        # 发送响应体
        if 'body' in response:
            self.wfile.write(response['body'].encode('utf-8'))

# 导出处理程序
handler = Handler
