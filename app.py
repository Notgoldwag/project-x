from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from dotenv import load_dotenv
import os
import requests

# === Load environment variables ===
load_dotenv()
GEMINI_API_KEY = os.environ.get("AIzaSyB0vu9RLXyAGbzjyQXJWBc_aT-pTsSDBqc")
GEMINI_API_URL = os.environ.get("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent")

# === Initialize Flask ===
app = Flask(__name__, static_folder="static", template_folder="templates")


# === ROUTES ===

@app.route('/')
def root():
    return send_from_directory('.', 'index.html')


@app.route('/login_signup')
def index():
    files = [f"File {i}" for i in range(1, 6)]
    return render_template('login_signup.html', files=files)


@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    message = data.get("message", "")
    reply = f"You asked: {message}"
    return jsonify({"reply": reply})


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/prompt-injections')
def prompt_injections():
    return render_template('promptinjections.html')


# === API: SCORE PROMPT ===
@app.route('/api/score_prompt', methods=['POST'])
def score_prompt():
    data = request.get_json()
    prompt = data.get("prompt", "")
    protection_level = data.get("protectionLevel", "basic")

    if not prompt.strip():
        return jsonify({"error": "Prompt cannot be empty"}), 400

    # Simple heuristic-based detection without ML model
    score = 0
    heuristics = []
    
    # Basic keyword-based heuristics
    suspicious_patterns = [
        "ignore previous", "override", "forget everything", "disregard",
        "new instructions", "system prompt", "admin", "root", "sudo",
        "delete", "bypass", "circumvent", "hack", "exploit"
    ]
    
    prompt_lower = prompt.lower()
    for pattern in suspicious_patterns:
        if pattern in prompt_lower:
            score += 20
            heuristics.append(f"Contains '{pattern}' pattern")
    
    # Additional checks
    if len(prompt) > 1000:
        score += 10
        heuristics.append("Unusually long prompt")
    
    if prompt.count('\n') > 10:
        score += 10
        heuristics.append("Multiple line breaks detected")
    
    # Apply protection level multiplier
    if protection_level == "strict":
        score = min(100.0, score * 1.5)
    
    score = min(100.0, score)  # Cap at 100%

    # Log detection for history
    os.makedirs("logs", exist_ok=True)
    with open("logs/detections.log", "a", encoding="utf-8") as f:
        f.write(f"{prompt[:200]} | Score={score} | Level={protection_level}\n")

    return jsonify({
        "score": score,
        "heuristics": heuristics,
        "explanation": None
    })


# === API: GEMINI EXPLANATION ===
@app.route('/api/explain', methods=['POST'])
def explain():
    data = request.get_json()
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "Prompt missing"}), 400
    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key not configured"}), 500

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    body = {
        "contents": [
            {"parts": [{"text": f"Explain why this prompt might be a prompt-injection: {prompt}"}]}
        ]
    }

    try:
        r = requests.post(GEMINI_API_URL, headers=headers, json=body, timeout=15)
        r.raise_for_status()
        data = r.json()
        # Gemini returns a nested structure: extract text
        explanation = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return jsonify({"explanation": explanation})
    except Exception as e:
        return jsonify({"error": "Gemini API request failed", "detail": str(e)}), 500


# === MAIN ===
if __name__ == "__main__":
    app.run(debug=True, port=5001)
