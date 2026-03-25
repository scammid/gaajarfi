import os
import uuid
import base64
import random
import replicate
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

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

    api_token = os.getenv('REPLICATE_API_TOKEN')
    if not api_token:
        return jsonify({'error': 'Service not configured. Please contact support.'}), 500

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Encode original image as base64 for safe in-browser display
        with open(filepath, 'rb') as f:
            img_bytes = f.read()
        mime = 'image/jpeg' if ext in ('jpg', 'jpeg') else f'image/{ext}'
        original_b64 = f"data:{mime};base64,{base64.b64encode(img_bytes).decode()}"

        # Run AI generation on Replicate
        os.environ['REPLICATE_API_TOKEN'] = api_token
        with open(filepath, 'rb') as f:
            output = replicate.run(
                "fofr/face-to-many:a07f252abbbd832009640b27f063ea52d87d7a23a185ca165bec23b5adc8deaf",
                input={
                    "image": f,
                    "style": "Photographic",
                    "prompt": (
                        "holding a large fresh orange carrot up to their smiling mouth, "
                        "happily licking and enjoying the carrot, vibrant healthy lifestyle, "
                        "bright natural lighting, fresh vegetables and greenery in background, "
                        "joyful energetic expression, photorealistic portrait"
                    ),
                    "negative_prompt": "ugly, deformed, disfigured, blurry, low quality, bad anatomy, watermark",
                    "num_outputs": 1,
                    "guidance_scale": 7.5,
                }
            )

        if output and len(output) > 0:
            return jsonify({
                'success': True,
                'generated_image': str(output[0]),
                'original_image': original_b64,
                'carrot_fact': random.choice(CARROT_FACTS),
            })
        else:
            return jsonify({'error': 'Image generation failed. Please try again.'}), 500

    except Exception as e:
        err = str(e)
        if 'Unauthenticated' in err or 'Invalid token' in err:
            return jsonify({'error': 'Invalid API token. Please check configuration.'}), 500
        if 'insufficient credit' in err or '402' in err:
            return jsonify({'error': 'Service billing issue. Please try again later.'}), 500
        if 'Invalid version' in err or '422' in err:
            return jsonify({'error': 'AI model error. Please try again.'}), 500
        return jsonify({'error': 'Generation failed. Please try again with a clear face photo.'}), 500

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
