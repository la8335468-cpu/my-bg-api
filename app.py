import gc
import io
import os
from flask import Flask, request, send_file
import onnxruntime as ort
from PIL import Image, ImageDraw
from rembg import new_session, remove

app = Flask(__name__)

# Single Thread + Disable Mem Arena (RAM 512MB ke andar rakhne ke liye)
opts = ort.SessionOptions()
opts.intra_op_num_threads = 1
opts.inter_op_num_threads = 1
opts.enable_cpu_mem_arena = False

# u2netp lightweight model (Sirf 4MB size - zero crash)
session = new_session(
    'u2netp', providers=['CPUExecutionProvider'], sess_opts=opts
)


@app.route('/')
def home():
  return 'Server Live & Active'


@app.route('/change-bg', methods=['POST'])
def change_background():
  try:
    img_data = request.data
    if not img_data:
      return 'No photo data', 400

    # 1. Image ko 260px par process karein taaki RAM spike na ho
    input_img = Image.open(io.BytesIO(img_data)).convert('RGB')
    small_img = input_img.resize((260, 260))
    del input_img
    gc.collect()

    # 2. Fast Cutout
    cutout_small = remove(small_img, session=session).convert('RGBA')
    cutout = cutout_small.resize((512, 512), Image.Resampling.BILINEAR)
    del small_img, cutout_small
    gc.collect()

    # 3. Canvas Background (No Internet Lag)
    bg = Image.new('RGBA', (512, 512), (135, 206, 235, 255))
    draw = ImageDraw.Draw(bg)
    draw.rectangle([0, 260, 512, 512], fill=(107, 142, 35, 255))

    # 4. Merge
    bg.paste(cutout, (0, 0), cutout)
    final_output = bg.convert('RGB')
    del cutout, bg
    gc.collect()

    out_io = io.BytesIO()
    final_output.save(out_io, format='JPEG', quality=80)
    out_io.seek(0)
    del final_output
    gc.collect()

    return send_file(out_io, mimetype='image/jpeg')

  except Exception as e:
    return str(e), 500


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)
