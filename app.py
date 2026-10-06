import gc
import io
import os
from flask import Flask, request, send_file
import onnxruntime as ort
from PIL import Image, ImageDraw
from rembg import new_session, remove

app = Flask(__name__)

# Single thread optimization for low RAM
opts = ort.SessionOptions()
opts.intra_op_num_threads = 1
opts.inter_op_num_threads = 1
session = new_session('u2netp', providers=['CPUExecutionProvider'], sess_opts=opts)

# Natural Field / Ground Color Themes (Offline - Zero Network Lag)
THEMES = [
    ((110, 139, 61), (194, 178, 128)),   # Khet Green + Mitti Ground
    ((76, 115, 60), (142, 126, 92)),     # Forest Green + Path
    ((130, 140, 80), (210, 180, 140)),   # Sunny Crop Field
    ((90, 120, 70), (160, 140, 110)),    # Garden Outdoor
]

@app.route('/')
def home():
    return "Server Live & Active"

@app.route('/change-bg', methods=['POST'])
def change_background():
    try:
        img_data = request.data
        if not img_data:
            return "No data", 400

        # 1. Input Image ko resize karein
        input_img = Image.open(io.BytesIO(img_data)).convert('RGB')
        small_img = input_img.resize((300, 300))
        del input_img
        gc.collect()

        # 2. AI Cutout
        cutout = remove(small_img, session=session).convert('RGBA')
        cutout = cutout.resize((512, 512), Image.Resampling.BILINEAR)
        del small_img
        gc.collect()

        # 3. Fast Canvas Background (No external download delay)
        bg = Image.new('RGBA', (512, 512), (135, 206, 235, 255)) # Sky
        draw = ImageDraw.Draw(bg)
        draw.rectangle([0, 260, 512, 512], fill=(107, 142, 35, 255)) # Ground
        
        # 4. Composite & Export
        bg.paste(cutout, (0, 0), cutout)
        final_img = bg.convert('RGB')
        del cutout, bg
        gc.collect()

        out_io = io.BytesIO()
        final_img.save(out_io, format='JPEG', quality=80)
        out_io.seek(0)
        del final_img
        gc.collect()

        return send_file(out_io, mimetype='image/jpeg')

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
