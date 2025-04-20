import numpy as np
import cv2
from svgwrite import Drawing
import os
from PIL import Image, ImageDraw, ImageFont
from skimage.morphology import skeletonize
import random  # 追加

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

    def write_text_to_pages(self, text, font_path, output_dir):
        """テキストを複数ページのG-codeに変換"""
        os.makedirs(output_dir, exist_ok=True)
        
        current_page = 1
        text_position = 0  # テキスト処理位置を追跡
        total_text = text
        
        print(f"\n=== Starting text processing ===")
        print(f"Total text length: {len(total_text)} characters")
        
        while text_position < len(total_text):
            # 各ページの開始位置をリセット
            current_x = self.paper_margin_left
            current_y = self.paper_margin_top
            page_content = []
            
            # G-codeの初期設定
            gcode = [
                "G21",          # mmモード
                "G90",          # 絶対座標モード
                f"F{self.move_speed}",  # 基本送り速度設定
                f"G1G90 Z{self.pen_up_z}F{self.pen_speed}",  # 初期位置でペンを上げる
                f"G0 X0Y0F{self.move_speed}"  # 中心位置に移動
            ]
            
            print(f"\nProcessing page {current_page}")
            print(f"Starting at text position: {text_position}")
            
            # 現在のページで処理する文字列を取得
            current_text = total_text[text_position:]
            lines = current_text.split('\n')
            
            for line_idx, line in enumerate(lines):
                current_x = self.paper_margin_left
                chars_in_line = []
                base_wobble = self.get_vertical_wobble()
                i = 0
                
                while i < len(line):
                    # 下余白チェック - ページ終了条件
                    if current_y + self.line_spacing/10 > self.page_height - self.paper_margin_bottom:
                        print(f"Reached bottom margin at Y={current_y:.3f}mm")
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
                    
                    # 右余白チェック
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
                    
                    # 文字の描画
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
                
                # 行の終わりの処理
                if chars_in_line:
                    page_content.append(''.join(chars_in_line))
                    current_y += self.line_spacing/10
                
                # 改行文字の処理
                if line_idx < len(lines) - 1:  # 最後の行以外で改行を処理
                    text_position += 1  # 改行文字をカウント
                
                # ページ終了条件チェック
                if current_y + self.line_spacing/10 > self.page_height - self.paper_margin_bottom:
                    break
            
            # G-codeの終了処理
            gcode.extend([
                f"G1G90 Z{self.pen_up_z}F{self.pen_speed}",
                "G0 X0Y0F20000",
                ""
            ])
            
            # ファイルの保存
            gcode_filename = f"page_{current_page:03d}.gcode"
            preview_filename = f"page_{current_page:03d}_preview.png"
            gcode_path = os.path.join(output_dir, gcode_filename)
            preview_path = os.path.join(output_dir, preview_filename)
            
            with open(gcode_path, "w") as f:
                f.write("\n".join(gcode))
            
            # プレビュー生成
            page_text = '\n'.join(page_content)
            generate_preview(page_text, font_path, preview_path, self)
            
            print(f"\nPage {current_page} complete:")
            print(f"- Characters processed: {text_position}")
            print(f"- Lines on page: {len(page_content)}")
            print(f"- Files generated: {gcode_filename}, {preview_filename}")
            
            current_page += 1
            
            # 全テキストの処理が完了したら終了
            if text_position >= len(total_text):
                break
        
        print(f"\nProcessing complete:")
        print(f"- Total pages: {current_page}")
        print(f"- Total characters processed: {text_position}")
        
        return current_page

def generate_preview(text, font_path, output_path, writer):
    """検証用のプレビュー画像を生成"""
    px_per_mm = 11.811  # 300 DPI / 25.4 mm
    width_px = int(writer.page_width * px_per_mm)
    height_px = int(writer.page_height * px_per_mm)
    
    print(f"=== Preview Generation Debug ===")
    print(f"A4 size: {writer.page_width}x{writer.page_height}mm")
    print(f"Writing start position: X={writer.paper_margin_left}mm, Y={writer.paper_margin_top}mm")
    
    # 白地の画像を作成
    image = Image.new('RGB', (width_px, height_px), 'white')
    draw = ImageDraw.Draw(image)
    
    # 余白の計算（ピクセル単位）
    margin_top_px = int(writer.paper_margin_top * px_per_mm)
    margin_right_px = int(writer.paper_margin_right * px_per_mm)
    margin_left_px = int(writer.paper_margin_left * px_per_mm)
    margin_bottom_px = int(writer.paper_margin_bottom * px_per_mm)
    
    # 余白エリアを描画（薄いグレー）
    draw.rectangle([0, 0, width_px, margin_top_px], fill=(240, 240, 240))
    draw.rectangle([0, height_px - margin_bottom_px, width_px, height_px], fill=(240, 240, 240))
    draw.rectangle([0, 0, margin_left_px, height_px], fill=(240, 240, 240))
    draw.rectangle([width_px - margin_right_px, 0, width_px, height_px], fill=(240, 240, 240))
    
    # 原点を表示（赤の点）
    origin_marker_size = 5
    draw.ellipse([-origin_marker_size, -origin_marker_size,
                  origin_marker_size, origin_marker_size],
                 fill=(255, 0, 0))
    
    # テキストの軌跡を描画
    current_x = writer.paper_margin_left
    current_y = writer.paper_margin_top
    base_wobble = writer.get_vertical_wobble()
    
    print(f"\nDebug - Text path:")
    print(f"Starting at: ({current_x}mm, {current_y}mm)")
    
    for char in text:
        if char == '\n':
            current_x = writer.paper_margin_left
            current_y += writer.line_spacing/10
            base_wobble = writer.get_vertical_wobble()  # 新しい行の揺れ
            print(f"New line at: ({current_x}mm, {current_y}mm)")
            continue
            
        char_wobble = base_wobble + writer.get_vertical_wobble()
        
        if char == ' ':
            current_x += writer.get_random_spacing()/5
            continue
            
        # 文字の軌跡を取得
        contours, _ = writer.get_font_strokes(char, font_path)
        
        # 各輪郭を描画
        for contour in contours:
            points = contour.reshape(-1, 2)
            for i in range(len(points) - 1):
                x1 = int((current_x + points[i][0]/10) * px_per_mm)
                y1 = int((current_y + points[i][1]/10 + char_wobble) * px_per_mm)
                x2 = int((current_x + points[i+1][0]/10) * px_per_mm)
                y2 = int((current_y + points[i+1][1]/10 + char_wobble) * px_per_mm)
                
                draw.line([(x1, y1), (x2, y2)], fill=(0, 0, 255), width=2)
                print(f"Drawing line: ({x1}, {y1}) to ({x2}, {y2})")
        
        current_x += (writer.char_size/10 + writer.get_random_spacing()/10)
    
    # 書き出し開始位置を表示（緑の点）
    start_x_px = int(writer.paper_margin_left * px_per_mm)
    start_y_px = int(writer.paper_margin_top * px_per_mm)
    marker_size = 5
    draw.ellipse([start_x_px - marker_size, start_y_px - marker_size,
                  start_x_px + marker_size, start_y_px + marker_size],
                 fill=(0, 255, 0))
    
    # 原点から書き出し開始位置までの移動を赤い点線で表示
    dash_length = 5
    for i in range(0, start_x_px, dash_length * 2):
        draw.line([(i, 0), (min(i + dash_length, start_x_px), 0)],
                 fill=(255, 0, 0), width=1)
    for i in range(0, start_y_px, dash_length * 2):
        draw.line([(start_x_px, i), (start_x_px, min(i + dash_length, start_y_px))],
                 fill=(255, 0, 0), width=1)
    
    # 凡例を追加
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
    
    # 画像を保存
    image.save(output_path)
    print(f"\nPreview saved to {output_path}")

def text_to_gcode(text, font_path, output_dir):
    """テキストをG-codeに変換（メイン関数）"""
    writer = StrokeWriter()
    
    print("\n=== Starting text processing ===")
    print(f"Output directory: {output_dir}")
    print(f"Text length: {len(text)} characters")
    
    # 出力ディレクトリの作成
    os.makedirs(output_dir, exist_ok=True)
    
    # テキストを複数ページに分割して処理
    total_pages = writer.write_text_to_pages(text, font_path, output_dir)
    
    print(f"\nProcessing complete:")
    print(f"- Total pages: {total_pages}")
    print(f"- Output directory: {output_dir}")

def generate_test_pattern_gcode(output_path):
    """検証用のテストパターンG-codeを生成"""
    writer = StrokeWriter()
    
    # G-code初期設定
    gcode = [
        "G21",          # mmモード
        "G90",          # 絶対座標モード
        f"F20000",      # 基本送り速度設定
        "G1G90 Z0.0F20000"  # 初期位置でペンを上げる
    ]
    
    # A4中央のX座標
    center_x = writer.page_width / 2  # 105mm
    
    # 上端から50mmの位置から開始
    start_y = 50
    line_length = 20  # 各線の長さ
    
    # 5本の縦線を描く（中心から左右に10mm間隔）
    for i in range(-2, 3):  # -2, -1, 0, 1, 2
        x = center_x + (i * 10)  # 中心から10mm間隔
        
        # ペンを上げて開始位置に移動
        gcode.append("G1G90 Z0.0F20000")
        gcode.append(f"G0 X{x:.3f}Y-{start_y:.3f}F20000")
        
        # ペンを下ろして線を描く
        gcode.append("G1G90 Z-7.0F20000")
        
        # 縦線を描く
        gcode.append(f"G1 X{x:.3f}Y-{start_y + line_length:.3f}F20000")
        
        # ペンを上げる
        gcode.append("G1G90 Z0.0F20000")
    
    # 終了時に原点に戻る
    gcode.extend([
        "G1G90 Z0.0F20000",
        "G90G0 X0Y0",
        "M2"
    ])
    
    # G-codeファイルを保存
    with open(output_path, "w") as f:
        f.write("\n".join(gcode))
    
    print(f"\nテストパターンG-code生成完了:")
    print(f"- 中心線: X={center_x}mm")
    print(f"- 開始位置: Y={start_y}mm")
    print(f"- 線の長さ: {line_length}mm")
    print(f"- 間隔: 10mm")
    print(f"- 出力ファイル: {output_path}")

# テキストファイルを読み込んで実行
with open("input_text.txt", "r", encoding="utf-8") as f:
    text_content = f.read()

text_to_gcode(text_content, 
              "font/しょかきさらり行体.ttf",
              "output")

# メイン処理の最後に追加
generate_test_pattern_gcode("output/test_pattern.gcode")