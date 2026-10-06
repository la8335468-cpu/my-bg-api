import io
import os
from flask import Flask, request, send_file
from mediapipe.python.solutions import selfie_segmentation
import numpy as np
from PIL import Image, ImageDraw

app = Flask(__name__)

# Direct Module Load (Zero crash & RAM ~60MB)
segmentor = selfie_segmentation.SelfieSegmentation(model_selection=1)


@app.route('/')
def home():
  return 'Server Live & Active'


@app.route('/change-bg', methods=['POST'])
def change_background():
  try:
    img_data = request.data
    if not img_data:
      return 'No image data', 400

    # 1. Image load
    input_image = (
        Image.open(io.BytesIO(img_data)).convert('RGB').resize((512, 512))
    )
    img_np = np.array(input_image)

    # 2. Fast Human Cutout Mask
    results = segmentor.process(img_np)
    mask = results.segmentation_mask > 0.4

    # 3. Canvas Ground + Sky Background
    bg_image = Image.new('RGB', (512, 512), (135, 206, 235))
    draw = ImageDraw.Draw(bg_image)
    draw.rectangle([0, 260, 512, 512], fill=(107, 142, 35))
    bg_np = np.array(bg_image)

    # 4. Composite Photo
    condition = np.stack((mask,) * 3, axis=-1)
    output_np = np.where(condition, img_np, bg_np)

    # 5. Return Output
    output_img = Image.fromarray(output_np)
    out_io = io.BytesIO()
    output_img.save(out_io, format='JPEG', quality=85)
    out_io.seek(0)

    return send_file(out_io, mimetype='image/jpeg')

  except Exception as e:
    return str(e), 500


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)
