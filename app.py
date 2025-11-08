from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import requests
import time
import logging
import os

# === Load environment variables ===
load_dotenv()
# Read Gemini API key from a normal env var name. Do NOT embed keys in code.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent")

# === Initialize Flask ===
app = Flask(__name__, static_folder="static", template_folder=".")

# === Setup logging ===
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/detections.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# === Setup logging ===
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/detections.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

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


# === API: AI CHAT (LangChain Orchestration) ===
@app.route('/api/chat', methods=['POST'])
def ai_chat():
    """New chat endpoint using three-agent orchestration from main_enhanced.py"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        message = data.get("message", "").strip()
        session_id = data.get("session_id")
        
        if not message:
            return jsonify({
                "error": "Message cannot be empty",
                "reply": "Please enter a message to continue."
            }), 400
        
        # Import and call the LangChain orchestration
        process_prompt_engineering_sync = None
        try:
            # Use sys.path to import from the langchain-implement directory
            import sys
            import importlib.util
            
            # Add the langchain-implement directory to the path
            langchain_dir = os.path.join(os.path.dirname(__file__), 'langchain-implement')
            if langchain_dir not in sys.path:
                sys.path.insert(0, langchain_dir)
            
            # Import from the standalone orchestration module (no FastAPI dependencies)
            spec = importlib.util.spec_from_file_location(
                "orchestration", 
                os.path.join(langchain_dir, "orchestration.py")
            )
            orchestration = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(orchestration)
            
            process_prompt_engineering_sync = orchestration.process_prompt_engineering
            logging.info("✅ Successfully imported LangChain orchestration from orchestration.py")
                
        except Exception as import_error:
            logging.error(f"❌ Failed to import LangChain orchestration: {import_error}", exc_info=True)
            # Try to provide helpful error message
            error_msg = str(import_error)
            if "langchain" in error_msg.lower():
                hint = "Missing LangChain dependencies. Install with: pip install langchain langchain-openai"
            elif "pydantic" in error_msg.lower():
                hint = "Missing Pydantic. Install with: pip install pydantic"
            elif "fastapi" in error_msg.lower():
                hint = "Missing FastAPI. Install with: pip install fastapi"
            else:
                hint = f"Check the error: {error_msg}"
            
            return jsonify({
                "error": "LangChain orchestration unavailable",
                "reply": f"The AI system is not fully configured. {hint}",
                "debug": str(import_error) if app.debug else None
            }), 503
        
        if not process_prompt_engineering_sync:
            return jsonify({
                "error": "Import failed",
                "reply": "Could not load the AI orchestration system."
            }), 503
        
        # Process through three-agent orchestration
        try:
            logging.info(f"Processing message through LangChain 3-agent pipeline: '{message[:50]}...'")
            result = process_prompt_engineering_sync(message, session_id)
            
            logging.info(f"LangChain result status: {result.get('status')}")
            
            # Extract response from the orchestration result
            # Handle the structured format from main_enhanced.py
            final_output = result.get('final_output', {})
            
            if isinstance(final_output, dict):
                # Extract the final prompt template from the 3-agent pipeline
                ai_response = final_output.get('final_prompt_template')
                
                if not ai_response:
                    # Fallback to other possible fields
                    ai_response = final_output.get('response', 
                                                   final_output.get('text', 
                                                   final_output.get('error', 
                                                   str(final_output))))
            else:
                # If final_output is just a string
                ai_response = str(final_output)
            
            # Prepare response with all metadata
            response_data = {
                "reply": ai_response,
                "session_id": result.get('session_id'),
                "status": result.get('status', 'completed'),
                "execution_time_ms": result.get('total_execution_time_ms', 0),
                "immediate_response": result.get('immediate_response'),
                "workflow_id": result.get('workflow_id')
            }
            
            # Add execution history if available (for debugging)
            if app.debug and result.get('execution_history'):
                response_data['execution_history'] = result.get('execution_history')
            
            # Log successful request
            total_latency = (time.time() - start_time) * 1000
            logging.info(f"✅ Chat request completed - Total: {total_latency:.2f}ms, LangChain: {result.get('total_execution_time_ms', 0):.2f}ms")
            
            return jsonify(response_data)
            
        except Exception as e:
            logging.error(f"LangChain orchestration error: {e}")
            return jsonify({
                "error": "AI processing failed",
                "reply": "I encountered an error processing your request. Please try again.",
                "debug": str(e) if app.debug else None
            }), 500
            
    except Exception as e:
        # Log total latency even for errors
        total_latency = (time.time() - start_time) * 1000
        logging.error(f"Chat request failed after {total_latency:.2f}ms: {e}")
        return jsonify({
            "error": "Internal server error",
            "reply": "Something unexpected happened. Please try again.",
            "debug": str(e) if app.debug else None
        }), 500


# === API: N8N WEBHOOK PROXY (Legacy) ===
@app.route('/api/chat/webhook', methods=['POST'])
def chat_proxy():
    """Proxy endpoint to forward chat messages to n8n webhook"""
    try:
        data = request.get_json()
        message = data.get("message", "")
        
        if not message.strip():
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # n8n webhook URL - UPDATE THIS WITH YOUR CORRECT WEBHOOK URL
        n8n_webhook_url = "https://jkathila.app.n8n.cloud/webhook/dd754342-79d4-4d96-9805-1a46e97cbca3"
        
        print(f"Sending message to n8n webhook: {n8n_webhook_url}")
        print(f"Message: {message}")
        
        # Forward request to n8n webhook
        webhook_response = requests.post(
            n8n_webhook_url,
            json={"message": message},
            headers={"Content-Type": "application/json"},
            timeout=30  # 30 second timeout
        )
        
        print(f"n8n webhook response status: {webhook_response.status_code}")
        print(f"n8n webhook response body: {webhook_response.text[:500]}")  # Log first 500 chars
        
        if webhook_response.status_code == 200:
            # Try to parse the response as JSON
            try:
                response_data = webhook_response.json()
                print(f"n8n webhook response: {response_data}")
                
                # If the response doesn't have a 'reply' field, check for common alternatives
                if 'reply' not in response_data:
                    # Try to find the AI response in different possible fields
                    if 'output' in response_data:
                        response_data = {"reply": response_data['output']}
                    elif 'response' in response_data:
                        response_data = {"reply": response_data['response']}
                    elif 'message' in response_data:
                        response_data = {"reply": response_data['message']}
                    elif 'text' in response_data:
                        response_data = {"reply": response_data['text']}
                    else:
                        # If we got a JSON response but no recognizable reply field
                        response_data = {
                            "reply": "✅ n8n workflow is active and responding!",
                            "raw_response": response_data
                        }
                
                return jsonify(response_data)
                
            except ValueError as e:
                # n8n returned 200 but response is not JSON or is empty
                print(f"n8n response is not valid JSON: {e}")
                
                # Check if there's any text response
                if webhook_response.text:
                    return jsonify({
                        "reply": f"✅ n8n workflow responded with: {webhook_response.text}",
                        "note": "The n8n workflow is working but not returning JSON. Add a 'Respond to Webhook' node with JSON output."
                    })
                else:
                    return jsonify({
                        "reply": "✅ n8n workflow is active and processing your request!",
                        "note": "The workflow responded successfully but didn't return any data. To see AI responses, add a 'Respond to Webhook' node in your n8n workflow that returns JSON with a 'reply' field.",
                        "troubleshooting": {
                            "issue": "n8n workflow returns empty response",
                            "solution": "Add a 'Respond to Webhook' node at the end of your workflow",
                            "example_response": {
                                "reply": "Your AI response here"
                            }
                        }
                    })
        elif webhook_response.status_code == 404:
            # Specific handling for 404 errors
            return jsonify({
                "error": "n8n webhook not found",
                "reply": "🔧 Configuration Issue: The n8n workflow appears to be inactive or the webhook URL needs to be updated. Please check your n8n workflow status.",
                "troubleshooting": {
                    "issue": "404 Not Found from n8n webhook",
                    "webhook_url": n8n_webhook_url,
                    "steps": [
                        "1. Log into your n8n cloud instance",
                        "2. Check if the workflow is active (not paused)",
                        "3. Verify the webhook URL in your workflow",
                        "4. Update the URL in app.py if changed"
                    ]
                }
            }), 200  # Return 200 so the frontend can display the troubleshooting info
        else:
            # Handle other non-200 responses
            return jsonify({
                "error": f"Webhook returned status {webhook_response.status_code}",
                "reply": f"Sorry, the AI service returned an error (status {webhook_response.status_code}). Please try again later."
            }), 200
            
    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Request timed out",
            "reply": "⏱️ The AI service is taking too long to respond. Please try again with a shorter message."
        }), 200
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Connection failed", 
            "reply": "🌐 Network Issue: Unable to connect to the AI service. Please check your internet connection and try again. If the problem persists, the n8n workflow might need attention.",
            "troubleshooting": {
                "issue": "Connection error to n8n webhook",
                "possible_causes": [
                    "Internet connection issues",
                    "n8n cloud service temporarily down",
                    "Incorrect webhook URL",
                    "Workflow not active in n8n"
                ]
            }
        }), 200
        
    except Exception as e:
        print(f"Error in chat proxy: {e}")
        return jsonify({
            "error": "Internal server error",
            "reply": "❌ Something unexpected happened. Please try again. If the issue persists, check the server logs.",
            "debug_info": str(e) if app.debug else None
        }), 200


# === API: SCORE PROMPT ===
@app.route('/api/score_prompt', methods=['POST'])
def score_prompt():
    """
    Score prompt for injection risk using ML model and heuristics.
    Returns JSON with score, label, and heuristic details.
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
 # if __name__ == "__main__":
    # app.run(debug=True, port=5001)
