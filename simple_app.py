#!/usr/bin/env python3
"""
Simple Flask app runner that skips ML model loading for quick testing
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import os
import logging

# === Load environment variables ===
load_dotenv()

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
    return send_from_directory('.', 'playground.html')

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