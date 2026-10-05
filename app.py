import io
import random
from flask import Flask, request, send_file
from PIL import Image
from rembg import new_session, remove
import requests

app = Flask(__name__)

# Lightweight u2netp AI model (Taaki Render ke free tier me RAM full na ho)
session = new_session('u2netp')

# 8 Natural 4x4 Backgrounds Pool (Road, Khet, Ped-paudhe, Garden)
BACKGROUND_URLS = [
    'https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=512&h=512&fit=crop&fm=jpg',  # Gaon/Khet Wali Road
    'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=512&h=512&fit=crop&fm=jpg',  # Garden Walkway & Flower Pots
    'https://images.unsplash.com/photo-1558904541-efa8c4a08931?w=512&h=512&fit=crop&fm=jpg',  # Bada Chhavedaar Ped & Ghaas
    'https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?w=512&h=512&fit=crop&fm=jpg',  # Mitti Ka Rasta / Kacchi Sadak
    'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=512&h=512&fit=crop&fm=jpg',  # Khula Khet / Maidan
    'https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=512&h=512&fit=crop&fm=jpg',  # Patthar Ka Rasta & Ped
    'https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?w=512&h=512&fit=crop&fm=jpg',  # Ghani Hariyali & Dense Trees
    'https://images.unsplash.com/photo-1448375240586-882707db888b?w=512&h=512&fit=crop&fm=jpg',  # Roadside Trees & Plants
]


@app.route('/change-bg', methods=['POST'])
def change_background():
  try:
    # 1. Android se aayi photo read karein
    img_data = request.data
    if not img_data:
      return 'No photo data received', 400

    input_img = Image.open(io.BytesIO(img_data)).convert('RGB')
    input_img = input_img.resize((512, 512))

    # 2. rembg se background kaat kar worker ka cutout banana
    cutout = remove(input_img, session=session).convert('RGBA')

    # 3. Random background uthana (Road / Trees / Garden)
    random_bg_url = random.choice(BACKGROUND_URLS)
    bg_resp = requests.get(random_bg_url, timeout=10)
    bg_img = (
        Image.open(io.BytesIO(bg_resp.content))
        .convert('RGBA')
        .resize((512, 512))
    )

    # 4. Background ke upar worker paste karna
    bg_img.paste(cutout, (0, 0), cutout)
    final_output = bg_img.convert('RGB')

    # 5. Result phone ko wapas bhejna
    output_io = io.BytesIO()
    final_output.save(output_io, format='JPEG', quality=85)
    output_io.seek(0)
    return send_file(output_io, mimetype='image/jpeg')

  except Exception as e:
    return str(e), 500


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=10000)
