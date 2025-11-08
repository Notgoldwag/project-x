from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from dotenv import load_dotenv
import os
import requests

# === Load environment variables ===
load_dotenv()
GEMINI_API_KEY = os.environ.get("AIzaSyB0vu9RLXyAGbzjyQXJWBc_aT-pTsSDBqc")
GEMINI_API_URL = os.environ.get("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent")

# === Initialize Flask ===
app = Flask(__name__, static_folder="static", template_folder=".")


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


@app.route('/api-test')
def api_test():
    return send_from_directory('.', 'api_test.html')


@app.route('/webhook-test')
def webhook_test():
    return send_from_directory('.', 'webhook-test.html')


@app.route('/prompt-injections')
def prompt_injections():
    return render_template('promptinjections.html')


# === API: N8N WEBHOOK PROXY ===
@app.route('/api/chat', methods=['POST'])
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
