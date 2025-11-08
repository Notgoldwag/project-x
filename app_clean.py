from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
import os
import requests

# === Load environment variables ===
load_dotenv()
MODEL_DIR = os.environ.get("MODEL_DIR", "models/prompt_injection_detector")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyB0vu9RLXyAGbzjyQXJWBc_aT-pTsSDBqc")
GEMINI_API_URL = os.environ.get("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent")

# === Initialize Flask ===
app = Flask(__name__, static_folder="static", template_folder="templates")

# === Try to load your trained model ===
print(f"🔄 Loading model from: {MODEL_DIR}")
nlp = None
MODEL_LOADED = False

def load_model():
    """Lazy loading of the model to avoid startup crashes"""
    global nlp, MODEL_LOADED
    
    if MODEL_LOADED or nlp is not None:
        return True
    
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
        
        print("📦 Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        
        print("🤖 Loading model...")
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
        
        print("⚙️ Setting up pipeline...")
        nlp = pipeline("text-classification", model=model, tokenizer=tokenizer, device=-1, top_k=None)
        
        print("✅ Model loaded successfully!")
        MODEL_LOADED = True
        return True
        
    except Exception as e:
        print(f"❌ Failed to load model: {str(e)}")
        return False

print("🚀 Flask app initialized")

# === ROUTES ===

@app.route('/')
def root():
    return render_template('index.html')

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

    try:
        # Try to use your model first
        if load_model() and nlp:
            score, heuristics = score_with_model_pure(prompt, protection_level)
            model_used = "ML Model"
        else:
            # Fallback - but you wanted NO heuristics when model works
            score = 50.0  # Neutral score when model fails
            heuristics = ["Model unavailable - cannot score"]
            model_used = "No Model"

        # Log detection for history
        os.makedirs("logs", exist_ok=True)
        with open("logs/detections.log", "a", encoding="utf-8") as f:
            f.write(f"{prompt[:200]} | Score={score} | Level={protection_level} | Model={MODEL_LOADED}\n")

        return jsonify({
            "score": score,
            "heuristics": heuristics,
            "explanation": None,
            "model_used": model_used
        })
    
    except Exception as e:
        print(f"❌ Error in score_prompt: {str(e)}")
        return jsonify({
            "score": 0.0,
            "heuristics": [f"Error: {str(e)}"],
            "explanation": None,
            "model_used": "Error",
            "error": str(e)
        })

def score_with_model_pure(prompt, protection_level):
    """
    Score prompt using ONLY your trained model - NO heuristics whatsoever!
    """
    try:
        # Get prediction from your trained model
        predictions = nlp(prompt)
        
        # Extract the predictions (your model returns nested list)
        if isinstance(predictions, list) and len(predictions) > 0:
            preds = predictions[0] if isinstance(predictions[0], list) else predictions
            probs = {pred['label']: pred['score'] for pred in preds}
        else:
            probs = {}
        
        # Extract harmful probability (LABEL_1 is harmful based on your test)
        harmful_prob = probs.get("LABEL_1", 0.0)
        
        # Convert to percentage
        base_score = harmful_prob * 100
        
        # Adjust ONLY based on protection level (no other modifications)
        if protection_level == "strict":
            base_score = min(100.0, base_score * 1.15 + 3.0)
        elif protection_level == "advanced":
            base_score = min(100.0, base_score * 1.05 + 1.0)
        
        # Ensure score is reasonable
        score = max(0.0, min(100.0, base_score))
        
        # ZERO heuristics - pure model trust!
        # Only add info if model is very uncertain
        heuristics = []
        confidence = max(probs.values()) if probs else 0.0
        if confidence < 0.6:
            heuristics.append(f"Low model confidence: {confidence:.2f}")
        
        return round(score, 1), heuristics
        
    except Exception as e:
        print(f"❌ Model inference error: {str(e)}")
        return 0.0, [f"Model error: {str(e)}"]

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