import os
import json
import uuid
from src.lib.python.handwrite import generate_preview

def handler(request, response):
    try:
        body = request.json()
        text = body.get("text", "")
        font_size = body.get("fontSize", 8)
        margin_top = body.get("marginTop", 35)
        margin_bottom = body.get("marginBottom", 25)
        margin_left = body.get("marginLeft", 30)
        margin_right = body.get("marginRight", 30)
        paper_size = body.get("paperSize", "A4")

        if not text:
            return response.status(400).json({ "error": "文本内容不能为空" })

        # 字体路径查找
        font_candidates = [
            os.path.join(os.getcwd(), "public", "fonts", "しょかきさらり行体.ttf"),
            os.path.join(os.getcwd(), "fonts", "しょかきさらり行体.ttf"),
        ]
        font_path = next((f for f in font_candidates if os.path.exists(f)), None)

        if not font_path:
            return response.status(500).json({ "error": "字体文件不存在" })

        preview_base64, gcode_content = generate_preview(
            text=text,
            font_path=font_path,
            font_size=font_size,
            margin_top=margin_top,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            margin_right=margin_right,
            paper_size=paper_size
        )

        return response.json({
            "success": True,
            "previewBase64": preview_base64,
            "gcodeContent": gcode_content,
            "sessionId": str(uuid.uuid4())
        })

    except Exception as e:
        import traceback
        return response.status(500).json({
            "error": str(e),
            "trace": traceback.format_exc()
        })
