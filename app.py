from flask import Flask, render_template, request, jsonify, redirect, url_for
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from dotenv import load_dotenv
import torch
import os
import requests
import random
import re

# === Load environment variables ===
load_dotenv()
MODEL_DIR = os.environ.get("MODEL_DIR", "models/prompt_injection_detector")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyB0vu9RLXyAGbzjyQXJWBc_aT-pTsSDBqc")
GEMINI_API_URL = os.environ.get("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent")

# === Initialize Flask ===
app = Flask(__name__, static_folder="static", template_folder="templates")

# === Load your trained model ===
print(f"🔄 Loading model from: {MODEL_DIR}")
nlp = None
MODEL_LOADED = False

try:
    # Check if model directory exists
    if not os.path.exists(MODEL_DIR):
        raise FileNotFoundError(f"Model directory not found: {MODEL_DIR}")
    
    print("📦 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    
    print("🤖 Loading model...")
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    
    print("⚙️ Setting up pipeline...")
    device = 0 if torch.cuda.is_available() else -1
    nlp = pipeline("text-classification", model=model, tokenizer=tokenizer, device=device, top_k=None)
    
    print("✅ Model loaded successfully!")
    MODEL_LOADED = True
    
except ImportError as e:
    print(f"❌ Import error (likely PyTorch compatibility): {str(e)}")
    print("🔄 Falling back to heuristic-based detection")
except Exception as e:
    print(f"⚠️ Failed to load model: {str(e)}")
    print("🔄 Falling back to heuristic-based detection")

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
        if MODEL_LOADED and nlp:
            # Use your trained model
            score, heuristics = score_with_model(prompt, protection_level)
        else:
            # Fallback to heuristic-based scoring
            score = calculate_injection_score(prompt, protection_level)
            heuristics = detect_injection_patterns(prompt)

        # Log detection for history
        os.makedirs("logs", exist_ok=True)
        with open("logs/detections.log", "a", encoding="utf-8") as f:
            f.write(f"{prompt[:200]} | Score={score} | Level={protection_level} | Model={MODEL_LOADED}\n")

        return jsonify({
            "score": score,
            "heuristics": heuristics,
            "explanation": None,
            "model_used": "ML Model" if MODEL_LOADED else "Heuristic"
        })
    
    except Exception as e:
        print(f"❌ Error in score_prompt: {str(e)}")
        # Fallback to heuristic scoring on error
        score = calculate_injection_score(prompt, protection_level)
        heuristics = detect_injection_patterns(prompt)
        
        return jsonify({
            "score": score,
            "heuristics": heuristics,
            "explanation": None,
            "model_used": "Heuristic (Fallback)",
            "error": "Model inference failed, using fallback method"
        })

def score_with_model(prompt, protection_level):
    """
    Score prompt using ONLY your trained model - no heuristics!
    """
    try:
        # Get prediction from your trained model
        predictions = nlp(prompt)
        
        # Your model should return predictions with labels and scores
        if isinstance(predictions, list) and len(predictions) > 0:
            if isinstance(predictions[0], dict):
                # Format: [{'label': 'LABEL_0', 'score': 0.9}, {'label': 'LABEL_1', 'score': 0.1}]
                probs = {pred['label']: pred['score'] for pred in predictions}
            else:
                # Handle other formats if needed
                probs = predictions[0] if predictions else {}
        else:
            probs = {}
        
        # Extract harmful probability (assuming LABEL_1 is harmful, LABEL_0 is safe)
        harmful_prob = probs.get("LABEL_1", 0.0)
        safe_prob = probs.get("LABEL_0", 0.0)
        
        # If we don't have clear labels, use the higher score as potential risk
        if harmful_prob == 0.0 and safe_prob == 0.0 and probs:
            # Take the maximum score as a conservative approach
            harmful_prob = max(probs.values()) if probs else 0.0
        
        # Convert to percentage
        base_score = harmful_prob * 100
        
        # Adjust based on protection level ONLY
        if protection_level == "strict":
            base_score = min(100.0, base_score * 1.2 + 5.0)
        elif protection_level == "advanced":
            base_score = min(100.0, base_score * 1.1 + 2.0)
        
        # Ensure score is reasonable
        score = max(0.0, min(100.0, base_score))
        
        # NO HEURISTICS - trust your model completely!
        # Only add model confidence info if it's very low
        heuristics = []
        confidence = max(probs.values()) if probs else 0.0
        if confidence < 0.7:
            heuristics.append(f"Model confidence: {confidence:.2f}")
        
        return round(score, 1), heuristics
        
    except Exception as e:
        print(f"❌ Model inference error: {str(e)}")
        # If model fails, we have to use something, so minimal fallback
        return 0.0, [f"Model error: {str(e)}"]

def calculate_injection_score(prompt, protection_level):
    """
    Mock scoring function that calculates injection risk based on heuristics
    """
    base_score = 0
    prompt_lower = prompt.lower()
    
    # High-risk patterns
    high_risk_patterns = [
        r'ignore\s+(previous|all|prior)\s+(instructions?|prompts?|commands?)',
        r'forget\s+(everything|all|previous)',
        r'you\s+are\s+now\s+a?\s*\w+',
        r'system\s*:\s*',
        r'override\s+\w+',
        r'disregard\s+\w+',
        r'new\s+instructions?',
        r'act\s+as\s+if',
        r'pretend\s+to\s+be',
        r'role\s*:\s*\w+',
    ]
    
    # Medium-risk patterns
    medium_risk_patterns = [
        r'admin\s+mode',
        r'developer\s+mode',
        r'debug\s+mode',
        r'bypass\s+\w+',
        r'sudo\s+\w+',
        r'root\s+access',
        r'execute\s+\w+',
    ]
    
    # Low-risk patterns
    low_risk_patterns = [
        r'please\s+help',
        r'can\s+you\s+\w+',
        r'what\s+if',
        r'how\s+about',
    ]
    
    # Check high-risk patterns
    for pattern in high_risk_patterns:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            base_score += random.randint(15, 25)
    
    # Check medium-risk patterns
    for pattern in medium_risk_patterns:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            base_score += random.randint(8, 15)
    
    # Check low-risk patterns (these actually reduce score)
    for pattern in low_risk_patterns:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            base_score -= random.randint(2, 5)
    
    # Add some randomness for realism
    base_score += random.randint(-5, 10)
    
    # Adjust based on protection level
    if protection_level == "strict":
        base_score = min(100, base_score + random.randint(5, 15))
    elif protection_level == "advanced":
        base_score = min(100, base_score + random.randint(2, 8))
    
    # Ensure score is within bounds
    score = max(0, min(100, base_score))
    
    return round(score, 1)

def detect_injection_patterns(prompt):
    """
    Detect specific injection patterns in the prompt
    """
    heuristics = []
    prompt_lower = prompt.lower()
    
    # Define pattern checks
    patterns = [
        (r'ignore\s+(previous|all|prior)\s+instructions?', "Instruction override attempt"),
        (r'forget\s+(everything|all)', "Memory reset attempt"),
        (r'you\s+are\s+now', "Role redefinition attempt"),
        (r'system\s*:', "System prompt injection"),
        (r'override|disregard', "Command override keywords"),
        (r'admin|developer|debug\s+mode', "Privilege escalation attempt"),
        (r'execute|run|eval', "Code execution keywords"),
        (r'\\n\\n|\\r\\n|<br>', "Line break injection"),
        (r'[<>{}[\]()]', "Special character injection"),
    ]
    
    for pattern, description in patterns:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            heuristics.append(description)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_heuristics = []
    for item in heuristics:
        if item not in seen:
            seen.add(item)
            unique_heuristics.append(item)
    
    return unique_heuristics


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
