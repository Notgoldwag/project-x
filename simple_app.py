#!/usr/bin/env python3
"""
Simple Flask app runner that skips ML model loading for quick testing
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import os
import logging
import jinja2

# === Load environment variables ===
load_dotenv()

# === Initialize Flask ===
app = Flask(__name__, static_folder="static")
app.jinja_loader = jinja2.ChoiceLoader([
    jinja2.FileSystemLoader('.'),  # For root templates
    jinja2.FileSystemLoader('features/prompt_playground'),  # For playground
])

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

# === Skip ML Model Loading ===
print("ℹ️ Running in simple mode - skipping ML model loading")
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

@app.route('/playground')
def playground():
    return render_template('index.html')  # From features/prompt_playground/

# === Simple API Endpoint ===
@app.route('/api/chat', methods=['POST'])
def simple_chat():
    """Simple chat endpoint without ML processing"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        # Simple response without AI processing
        response = {
            'status': 'success',
            'message': f'Echo: {user_message}',
            'note': 'Running in simple mode - AI features disabled'
        }
        
        return jsonify(response)
    
    except Exception as e:
        logging.error(f"Chat API error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Simple chat service error'
        }), 500

# === Playground API Endpoints ===
@app.route('/api/playground/run_prompt', methods=['POST'])
def run_prompt():
    """Simple playground endpoint - returns mock responses"""
    try:
        data = request.json
        system_instruction = data.get('system_instruction', '')
        prompt = data.get('prompt', '')
        models = data.get('models', [])
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Mock responses for each model
        results = []
        for model_id in models:
            if model_id == 'gemini-2.0-flash-exp':
                result = {
                    'model': model_id,
                    'response': '🔄 Gemini API key needs to be updated (currently compromised). Please get a new key from Google AI Studio.',
                    'status': 'Configuration Required',
                    'metadata': {'latency': 0.5, 'tokens': 0, 'cost_estimate': 0}
                }
            elif model_id in ['gpt-4-turbo', 'gpt-3.5-turbo']:
                result = {
                    'model': model_id,
                    'response': f'✅ This would be the {model_id} response to: "{prompt}"\n\nNote: Azure OpenAI is configured but running in demo mode.',
                    'status': 'Demo Mode',
                    'metadata': {'latency': 0.3, 'tokens': 50, 'cost_estimate': 0.002}
                }
            else:
                result = {
                    'model': model_id,
                    'response': f'Model {model_id} response simulation.',
                    'status': 'Demo Mode',
                    'metadata': {'latency': 0.4, 'tokens': 30, 'cost_estimate': 0.001}
                }
            
            results.append(result)
        
        return jsonify({
            'results': results,
            'total_time': 0.8
        })
        
    except Exception as e:
        logging.error(f"Playground error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/playground/analyze_results', methods=['POST'])
def analyze_results():
    """Mock analysis endpoint"""
    return jsonify({
        'analysis': {
            'overall_clarity_score': 8.5,
            'overall_relevance_score': 9.0,
            'overall_summary': '🎯 Demo mode: Analysis would appear here with proper API keys configured.'
        }
    })

# === Static files ===
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# === MAIN ===
if __name__ == "__main__":
    print("🚀 Starting Project X in Simple Mode")
    print("📍 Open http://localhost:5001 in your browser")
    print("ℹ️ ML features are disabled in this mode")
    app.run(debug=True, port=5001, host='0.0.0.0')