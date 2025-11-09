from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import requests
import os

# === Load environment variables ===
load_dotenv()
# Read Gemini API key from a normal env var name. Do NOT embed keys in code.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent")

# === Initialize Flask ===
app = Flask(__name__, static_folder="static", template_folder=".")

# === Load ML Model (RoBERTa fine-tuned) ===
MODEL_DIR = os.getenv('MODEL_DIR', 'models/prompt_injection_detector')
try:
    print(f"🔍 Loading prompt injection model from {MODEL_DIR}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"⚠️ Warning: Could not load model. Details: {e}")
    tokenizer = None
    model = None


# === ROUTES ===

@app.route('/')
def root():
    return send_from_directory('.', 'index.html')


@app.route('/login_signup')
def index():
    files = [f"File {i}" for i in range(1, 6)]
    return render_template('login_signup.html', files=files)


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/api-test')
def api_test():
    return send_from_directory('.', 'api_test.html')


@app.route('/webhook-test')
def webhook_test():
    return send_from_directory('.', 'webhook-test.html')


@app.route('/prompt-injections')
def prompt_injections():
    return render_template('promptinjections.html')


# === COMBINED API: Analyze Prompt ===
@app.route('/api/analyze_prompt', methods=['POST'])
def analyze_prompt():
    """
    Full analysis pipeline:
      - Detect prompt injection using ML model
      - Compute heuristic patterns
      - Ask Gemini for natural-language explanation
    """
    data = request.get_json()
    prompt = data.get("prompt", "")
    protection_level = data.get("protectionLevel", "basic")

    if not prompt.strip():
        return jsonify({"error": "Prompt cannot be empty"}), 400

    # ============== ML Detection ==============
    ml_score = 0
    label = "Safe"
    if model and tokenizer:
        try:
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding=True, max_length=256)
            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)
                ml_score = probs[0][1].item() * 100
            label = "Prompt Injection Detected" if ml_score > 50 else "Safe"
        except Exception as e:
            print(f"Model inference error: {e}")
            label = "Analysis Error"

    # ============== Heuristic Detection ==============
    heuristics = []
    suspicious_patterns = [
        "ignore previous", "override", "forget everything", "disregard",
        "new instructions", "system prompt", "admin", "root", "sudo",
        "delete", "bypass", "circumvent", "hack", "exploit"
    ]
    prompt_lower = prompt.lower()
    # Count matches and produce human-friendly heuristics
    match_count = 0
    for pattern in suspicious_patterns:
        if pattern in prompt_lower:
            match_count += 1
            heuristics.append(f"Contains '{pattern}' pattern")

    # Heuristic points: each match gives ~25 points (1 -> 25, 2 -> 50, 3 -> 75, 4+ -> 100)
    score_heuristic_points = min(100, match_count * 25)

    # Merge ML + heuristics. If model isn't available, fall back to heuristics alone.
    if model is None:
        final_score = score_heuristic_points
    else:
        final_score = min(100, (ml_score * 0.8) + (score_heuristic_points * 0.2))
    if protection_level == "strict":
        final_score = min(100, final_score * 1.2)

    # ============== Gemini AI Explanation ==============
    explanation = ""
    if GEMINI_API_KEY:
        try:
            # Gemini API uses key as URL parameter
            headers = {"Content-Type": "application/json"}
            body = {
                "contents": [
                    {"parts": [
                        {"text": f"Explain in simple terms why the following text might be a prompt injection attempt or safe user input:\n\n{prompt}"}
                    ]}
                ]
            }
            url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
            r = requests.post(url, headers=headers, json=body, timeout=15)
            r.raise_for_status()
            data = r.json()
            explanation = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
        except Exception as e:
            explanation = f"Gemini API error: {e}"
    else:
        explanation = "Gemini API key not configured."

    # ============== Return JSON ==============
    return jsonify({
        "score": round(final_score, 2),
        "label": label,
        "heuristics": heuristics,
        "explanation": explanation,
        "model_available": model is not None,
        "gemini_key_configured": bool(GEMINI_API_KEY)
    })


# === SIMPLE GEMINI EXPLAIN ENDPOINT (optional) ===
@app.route('/api/explain', methods=['POST'])
def explain():
    data = request.get_json()
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "Prompt missing"}), 400
    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key not configured"}), 500

    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {"parts": [{"text": f"Explain why this prompt might be a prompt-injection: {prompt}"}]}
        ]
    }
    try:
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        r = requests.post(url, headers=headers, json=body, timeout=15)
        r.raise_for_status()
        data = r.json()
        explanation = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return jsonify({"explanation": explanation})
    except Exception as e:
        return jsonify({"error": "Gemini API request failed", "detail": str(e)}), 500


# === New compatibility endpoints for front-end integrations ===
@app.route('/api/prompt_injection_detector/score', methods=['POST'])
def detector_score():
    data = request.get_json() or {}
    prompt = data.get('prompt', '')
    protection_level = data.get('protectionLevel', data.get('protection_level', 'basic'))

    if not prompt.strip():
        return jsonify({'error': 'Prompt cannot be empty'}), 400

    # ML detection (reuse model/tokenizer if available)
    ml_score = 0
    label = 'Safe'
    if model and tokenizer:
        try:
            inputs = tokenizer(prompt, return_tensors='pt', truncation=True, padding=True, max_length=256)
            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)
                ml_score = float(probs[0][1].item() * 100)
            label = 'Prompt Injection Detected' if ml_score > 50 else 'Safe'
        except Exception as e:
            print('Model inference error in detector_score:', e)
            label = 'Analysis Error'

    # Heuristic detection
    heuristics = []
    suspicious_patterns = [
        'ignore previous', 'override', 'forget everything', 'disregard',
        'new instructions', 'system prompt', 'admin', 'root', 'sudo',
        'delete', 'bypass', 'circumvent', 'hack', 'exploit'
    ]
    prompt_lower = prompt.lower()

    match_count = 0
    for pattern in suspicious_patterns:
        if pattern in prompt_lower:
            match_count += 1
            heuristics.append(f"Contains '{pattern}' pattern")

    score_heuristic_points = min(100, match_count * 25)

    if model is None:
        final_score = score_heuristic_points
    else:
        final_score = min(100, (ml_score * 0.8) + (score_heuristic_points * 0.2))

    if protection_level == 'strict':
        final_score = min(100, final_score * 1.2)

    return jsonify({
        'score': round(final_score, 2),
        'label': label,
        'heuristics': heuristics,
        'model_available': model is not None,
        'gemini_key_configured': bool(GEMINI_API_KEY)
    })


@app.route('/api/prompt_injection_detector/explain', methods=['POST'])
def detector_explain():
    data = request.get_json() or {}
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'Prompt missing'}), 400

    # Delegate to the existing Gemini explain logic where possible
    if not GEMINI_API_KEY:
        return jsonify({'explanation': 'Gemini API key not configured.'})

    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {"parts": [{"text": f"Explain in simple terms why the following text might be a prompt injection attempt or safe user input:\n\n{prompt}"} ]}
        ]
    }
    try:
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        r = requests.post(url, headers=headers, json=body, timeout=15)
        r.raise_for_status()
        resp = r.json()
        explanation = (
            resp.get('candidates', [{}])[0]
            .get('content', {})
            .get('parts', [{}])[0]
            .get('text', '')
        )
        return jsonify({'explanation': explanation})
    except Exception as e:
        return jsonify({'error': 'Gemini API request failed', 'detail': str(e)}), 500


@app.route('/api/gemini/chat', methods=['POST'])
def gemini_chat():
    """Simple proxy to send a single message to Gemini and return a text reply."""
    data = request.get_json() or {}
    message = data.get('message') or data.get('prompt') or ''
    if not message:
        return jsonify({'error': 'Message missing'}), 400

    if not GEMINI_API_KEY:
        return jsonify({'error': 'Gemini API key not configured'}), 500

    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {"parts": [{"text": message}]}
        ]
    }
    try:
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        r = requests.post(url, headers=headers, json=body, timeout=20)
        r.raise_for_status()
        resp = r.json()
        reply = (
            resp.get('candidates', [{}])[0]
            .get('content', {})
            .get('parts', [{}])[0]
            .get('text', '')
        )
        return jsonify({'reply': reply})
    except Exception as e:
        print('Gemini proxy error:', e)
        return jsonify({'error': 'Gemini request failed', 'detail': str(e)}), 500


# === MAIN ===
if __name__ == "__main__":
    app.run(debug=True, port=5001)
