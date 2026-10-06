import gc
import io
import os
import random
from flask import Flask, request, send_file
import onnxruntime as ort
from PIL import Image
from rembg import new_session, remove
import requests

app = Flask(__name__)

# Memory Optimization: CPU single-thread limit (RAM bachaane ke liye)
opts = ort.SessionOptions()
opts.intra_op_num_threads = 1
opts.inter_op_num_threads = 1
session = new_session('u2netp', providers=['CPUExecutionProvider'], sess_opts=opts)

BACKGROUND_URLS = [
    'https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=512&h=512&fit=crop&fm=jpg',
    'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=512&h=512&fit=crop&fm=jpg',
    'https://images.unsplash.com/photo-1558904541-efa8c4a08931?w=512&h=512&fit=crop&fm=jpg',
    'https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?w=512&h=512&fit=crop&fm=jpg',
    'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=512&h=512&fit=crop&fm=jpg',
    'https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=512&h=512&fit=crop&fm=jpg',
    'https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?w=512&h=512&fit=crop&fm=jpg',
    'https://images.unsplash.com/photo-1448375240586-882707db888b?w=512&h=512&fit=crop&fm=jpg',
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

        # 1. Image ko low RAM size (300px) par process karna
        input_img = Image.open(io.BytesIO(img_data)).convert('RGB')
        small_img = input_img.resize((300, 300))
        del input_img
        gc.collect()

        # 2. Fast & Light AI Cutout
        cutout = remove(small_img, session=session).convert('RGBA')
        cutout = cutout.resize((512, 512), Image.Resampling.BILINEAR)
        del small_img
        gc.collect()

        # 3. Background Download & Paste
        bg_url = random.choice(BACKGROUND_URLS)
        bg_resp = requests.get(bg_url, timeout=10)
        bg_img = Image.open(io.BytesIO(bg_resp.content)).convert('RGBA').resize((512, 512))

        bg_img.paste(cutout, (0, 0), cutout)
        final_img = bg_img.convert('RGB')
        del cutout, bg_img
        gc.collect()

        # 4. Response Return
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
