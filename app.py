import os
import io
import uuid
import base64
import random
import requests
from PIL import Image
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

HF_API_URL = 'https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell'

CARROT_PROMPTS = [
    "a joyful person licking a large fresh orange carrot, holding it up to their smiling mouth, vibrant healthy lifestyle, bright natural lighting, photorealistic portrait, high quality",
    "a happy smiling person biting into a fresh orange carrot, healthy glow, energetic expression, natural green background, photorealistic, studio quality",
    "a cheerful person holding a bunch of fresh carrots, one carrot up to their mouth licking it, radiant healthy skin, warm lighting, photorealistic portrait",
    "a delighted person enjoying a fresh carrot, licking it playfully, vibrant skin, natural sunlight, healthy lifestyle portrait, photorealistic high quality",
]

CARROT_FACTS = [
    "Carrots are the richest vegetable source of beta-carotene, which your body converts to Vitamin A — essential for sharp eyesight and a strong immune system.",
    "Studies show that eating carrots regularly can reduce the risk of cardiovascular disease by up to 32%!",
    "Carrots contain powerful antioxidants called polyacetylenes that actively fight cancer-causing free radicals in your body.",
    "The dietary fiber in carrots feeds beneficial gut bacteria, improving digestion and boosting overall immunity.",
    "Carrots are 88% water — munching on one is one of the tastiest ways to stay naturally hydrated.",
    "Vitamin C in carrots helps your body produce collagen, keeping your skin firm, bright, and youthful.",
    "One medium carrot has just 25 calories but provides 3% of your daily fiber needs — the perfect guilt-free snack.",
    "Carrots contain luteolin, a compound shown to reduce brain inflammation and improve memory and cognitive function.",
    "The potassium in carrots helps regulate blood pressure and significantly reduces the risk of stroke.",
    "Carrot consumption is linked to healthier teeth and gums — their crunchy texture acts as a natural toothbrush!",
    "Carrots contain falcarinol, a natural pesticide compound that also has powerful anti-tumor properties.",
    "Eating cooked carrots actually increases beta-carotene absorption by up to 40% compared to raw carrots!",
    "Carrots are rich in Vitamin K1, which plays a crucial role in blood clotting and bone health.",
    "The antioxidants in carrots help protect skin from sun damage and reduce signs of premature aging.",
]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/generate', methods=['POST'])
def generate():
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo uploaded.'}), 400

    file = request.files['photo']
    if not file.filename:
        return jsonify({'error': 'No file selected.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only JPG, PNG, or WEBP images are allowed.'}), 400

    hf_token = os.getenv('HF_TOKEN')
    if not hf_token:
        return jsonify({'error': 'Service not configured. Please contact support.'}), 500

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Encode original image for display
        img = Image.open(filepath).convert('RGB')
        img_display = img.resize((512, 512), Image.LANCZOS)
        orig_buf = io.BytesIO()
        img_display.save(orig_buf, format='JPEG', quality=88)
        original_b64 = f"data:image/jpeg;base64,{base64.b64encode(orig_buf.getvalue()).decode()}"

        # Generate carrot champion image with FLUX.1-schnell (free)
        prompt = random.choice(CARROT_PROMPTS)
        resp = requests.post(
            HF_API_URL,
            headers={'Authorization': f'Bearer {hf_token}'},
            json={'inputs': prompt},
            timeout=60,
        )

        if resp.status_code == 200:
            generated_b64 = f"data:image/jpeg;base64,{base64.b64encode(resp.content).decode()}"
        elif resp.status_code == 429:
            return jsonify({'error': 'Too many requests. Please wait a moment and try again.'}), 429
        elif resp.status_code in (401, 403):
            return jsonify({'error': 'Invalid API token. Please contact support.'}), 500
        else:
            return jsonify({'error': 'Generation failed. Please try again in a moment.'}), 500

        return jsonify({
            'success': True,
            'generated_image': generated_b64,
            'original_image': original_b64,
            'carrot_fact': random.choice(CARROT_FACTS),
        })

    except requests.Timeout:
        return jsonify({'error': 'Generation timed out. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
