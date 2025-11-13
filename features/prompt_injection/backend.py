"""
Prompt Injection Detection Feature Backend
Security scanning for prompt injection attempts
"""
from flask import Blueprint, request, jsonify, send_from_directory
import logging
import os
import requests

# Create Blueprint
injection_bp = Blueprint('prompt_injection', __name__, url_prefix='/prompt-injection')

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent")

# Will be set by main app
model = None
tokenizer = None

def init_model(m, t):
    """Initialize the ML model and tokenizer from main app"""
    global model, tokenizer
    model = m
    tokenizer = t


# === ROUTES ===

@injection_bp.route('/')
def index():
    """Render the Prompt Injection Detection page"""
    return send_from_directory('features/prompt_injection', 'index.html')


@injection_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files for the prompt injection feature"""
    return send_from_directory('features/prompt_injection/static', filename)


@injection_bp.route('/api/score', methods=['POST'])
def score_prompt():
    """
    Score prompt for injection risk using ML model and heuristics.
    Returns JSON with score, label, and heuristic details.
    """
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    protection_level = data.get("protectionLevel", data.get("protection_level", "basic"))

    if not prompt.strip():
        return jsonify({"error": "Prompt cannot be empty"}), 400

    # ============== ML Detection ==============
    ml_score = 0
    label = "Safe"
    if model and tokenizer:
        try:
            import torch
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding=True, max_length=256)
            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)
                ml_score = probs[0][1].item() * 100
            label = "Prompt Injection Detected" if ml_score > 50 else "Safe"
        except Exception as e:
            logging.error(f"Model inference error: {e}")
            label = "Analysis Error"

    # ============== Heuristic Detection ==============
    heuristics = []
    suspicious_patterns = [
        "ignore previous", "override", "forget everything", "disregard",
        "new instructions", "system prompt", "admin", "root", "sudo",
        "delete", "bypass", "circumvent", "hack", "exploit"
    ]
    prompt_lower = prompt.lower()
    match_count = 0
    for pattern in suspicious_patterns:
        if pattern in prompt_lower:
            match_count += 1
            heuristics.append(f"Contains '{pattern}' pattern")

    # Heuristic points: each match gives ~25 points
    score_heuristic_points = min(100, match_count * 25)

    # Merge ML + heuristics
    if model is None:
        final_score = score_heuristic_points
    else:
        final_score = min(100, (ml_score * 0.8) + (score_heuristic_points * 0.2))
    
    if protection_level == "strict":
        final_score = min(100, final_score * 1.2)

    return jsonify({
        "score": round(final_score, 2),
        "label": label,
        "heuristics": heuristics,
        "model_available": model is not None,
        "gemini_key_configured": bool(GEMINI_API_KEY)
    })


@injection_bp.route('/api/analyze', methods=['POST'])
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
            import torch
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding=True, max_length=256)
            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)
                ml_score = probs[0][1].item() * 100
            label = "Prompt Injection Detected" if ml_score > 50 else "Safe"
        except Exception as e:
            logging.error(f"Model inference error: {e}")
            label = "Analysis Error"

    # ============== Heuristic Detection ==============
    heuristics = []
    suspicious_patterns = [
        "ignore previous", "override", "forget everything", "disregard",
        "new instructions", "system prompt", "admin", "root", "sudo",
        "delete", "bypass", "circumvent", "hack", "exploit"
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
    
    if protection_level == "strict":
        final_score = min(100, final_score * 1.2)

    # ============== Gemini AI Explanation ==============
    explanation = ""
    if GEMINI_API_KEY:
        try:
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

    return jsonify({
        "score": round(final_score, 2),
        "label": label,
        "heuristics": heuristics,
        "explanation": explanation,
        "model_available": model is not None,
        "gemini_key_configured": bool(GEMINI_API_KEY)
    })


@injection_bp.route('/api/explain', methods=['POST'])
def explain():
    """Simple Gemini explanation endpoint"""
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
