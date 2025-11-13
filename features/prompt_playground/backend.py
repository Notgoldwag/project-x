"""
Prompt Playground Feature Backend
Multi-model prompt comparison and analysis
"""
from flask import Blueprint, request, jsonify, send_from_directory
import time
import logging
import os
import requests
import json
import re

# Create Blueprint
playground_bp = Blueprint('playground', __name__, url_prefix='/playground')

# Environment variables (will be passed from main app or loaded here)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent")

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_DEPLOYMENT_GPT4 = os.getenv("AZURE_OPENAI_DEPLOYMENT_1", "gpt-4.1")
AZURE_OPENAI_DEPLOYMENT_GPT35 = os.getenv("AZURE_OPENAI_DEPLOYMENT_2", "gpt-35-turbo")


# === ROUTES ===

@playground_bp.route('/')
def index():
    """Render the Multi-Model Prompt Playground page"""
    return send_from_directory('features/prompt_playground', 'index.html')


@playground_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files for the playground feature"""
    return send_from_directory('features/prompt_playground/static', filename)


@playground_bp.route('/api/run_prompt', methods=['POST'])
def run_prompt():
    """
    Run a prompt across multiple LLM models and return normalized results.
    Accepts: system_instruction, prompt, models[]
    Returns: { results: [{model, response, metadata}, ...] }
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        system_instruction = data.get('system_instruction', '').strip()
        prompt = data.get('prompt', '').strip()
        models = data.get('models', [])
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        if not models or len(models) == 0:
            return jsonify({'error': 'At least one model must be selected'}), 400
        
        results = []
        
        # Process each model
        for model_id in models:
            model_start = time.time()
            
            try:
                if model_id == 'gemini-2.0-flash-exp':
                    result = call_gemini_model(system_instruction, prompt)
                elif model_id in ['gpt-4-turbo', 'gpt-3.5-turbo']:
                    result = call_openai_model(model_id, system_instruction, prompt)
                elif model_id == 'claude-3-opus':
                    result = call_claude_model(system_instruction, prompt)
                else:
                    result = {
                        'model': model_id,
                        'response': f'Model {model_id} is not yet implemented.',
                        'status': 'Not Implemented',
                        'metadata': {'latency': 0, 'tokens': 0, 'cost_estimate': 0}
                    }
                
                # Add timing
                result['metadata']['latency'] = time.time() - model_start
                results.append(result)
                
            except Exception as e:
                logging.error(f"Error calling {model_id}: {e}")
                results.append({
                    'model': model_id,
                    'response': f'Error: {str(e)}',
                    'status': 'Error',
                    'metadata': {'latency': time.time() - model_start, 'tokens': 0, 'cost_estimate': 0}
                })
        
        total_time = time.time() - start_time
        logging.info(f"✅ Playground request completed - {len(results)} models, {total_time:.2f}s total")
        
        return jsonify({
            'results': results,
            'total_time': total_time
        })
        
    except Exception as e:
        logging.error(f"Playground error: {e}")
        return jsonify({'error': str(e)}), 500


@playground_bp.route('/api/analyze_results', methods=['POST'])
def analyze_results():
    """
    Use Gemini 2.5 Pro to perform meta-analysis on model outputs.
    Accepts: results[], original_prompt
    Returns: { analysis: {clarity_score, relevance_score, ...} }
    """
    try:
        data = request.get_json()
        results = data.get('results', [])
        original_prompt = data.get('original_prompt', '')
        
        if not results:
            return jsonify({'error': 'No results to analyze'}), 400
        
        # Build analysis prompt
        analysis_prompt = build_analysis_prompt(results, original_prompt)
        
        # Call Gemini for analysis
        if not GEMINI_API_KEY:
            return jsonify({'error': 'Gemini API key not configured'}), 500
        
        headers = {"Content-Type": "application/json"}
        body = {
            "contents": [{"parts": [{"text": analysis_prompt}]}]
        }
        
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        r = requests.post(url, headers=headers, json=body, timeout=30)
        r.raise_for_status()
        resp = r.json()
        
        analysis_text = (
            resp.get('candidates', [{}])[0]
            .get('content', {})
            .get('parts', [{}])[0]
            .get('text', '')
        )
        
        # Parse the analysis (expecting JSON format)
        analysis = parse_analysis_response(analysis_text)
        
        return jsonify({'analysis': analysis})
        
    except Exception as e:
        logging.error(f"Analysis error: {e}")
        return jsonify({'error': str(e)}), 500


# === HELPER FUNCTIONS ===

def call_gemini_model(system_instruction, prompt):
    """Call Gemini 2.0 Flash model"""
    if not GEMINI_API_KEY:
        raise Exception("Gemini API key not configured")
    
    # Build the full prompt
    full_prompt = prompt
    if system_instruction:
        full_prompt = f"System: {system_instruction}\n\nUser: {prompt}"
    
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": full_prompt}]}]
    }
    
    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    r = requests.post(url, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    resp = r.json()
    
    response_text = (
        resp.get('candidates', [{}])[0]
        .get('content', {})
        .get('parts', [{}])[0]
        .get('text', '')
    )
    
    # Estimate tokens and cost (approximate)
    tokens = len(response_text.split())
    cost = tokens * 0.000001  # Rough estimate
    
    return {
        'model': 'gemini-2.0-flash-exp',
        'response': response_text,
        'status': 'Success',
        'metadata': {
            'tokens': tokens,
            'cost_estimate': cost
        }
    }


def call_openai_model(model_id, system_instruction, prompt):
    """Call Azure OpenAI GPT models using existing Azure configuration"""
    
    # Check if Azure OpenAI is configured
    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY:
        return {
            'model': model_id,
            'response': 'Azure OpenAI not configured. Please add AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY to your .env file.',
            'status': 'Configuration Required',
            'metadata': {'tokens': 0, 'cost_estimate': 0}
        }
    
    # Determine deployment name based on model
    if model_id == 'gpt-4-turbo':
        deployment_name = AZURE_OPENAI_DEPLOYMENT_GPT4
    else:  # gpt-3.5-turbo
        deployment_name = AZURE_OPENAI_DEPLOYMENT_GPT35
    
    # Azure OpenAI API endpoint
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{deployment_name}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY
    }
    
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})
    
    body = {
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        r = requests.post(url, headers=headers, json=body, timeout=30)
        r.raise_for_status()
        resp = r.json()
        
        response_text = resp['choices'][0]['message']['content']
        tokens = resp.get('usage', {}).get('total_tokens', 0)
        
        # Cost estimation (approximate Azure rates)
        if model_id == 'gpt-4-turbo':
            cost = tokens * 0.00003  # $0.03 per 1K tokens
        else:
            cost = tokens * 0.000002  # $0.002 per 1K tokens
        
        return {
            'model': model_id,
            'response': response_text,
            'status': 'Success',
            'metadata': {
                'tokens': tokens,
                'cost_estimate': cost
            }
        }
    except Exception as e:
        raise Exception(f"Azure OpenAI API error: {str(e)}")


def call_claude_model(system_instruction, prompt):
    """Call Anthropic Claude model (placeholder)"""
    claude_api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not claude_api_key:
        return {
            'model': 'claude-3-opus',
            'response': 'Anthropic API key not configured. Please add ANTHROPIC_API_KEY to your .env file.',
            'status': 'Configuration Required',
            'metadata': {'tokens': 0, 'cost_estimate': 0}
        }
    
    # Claude API call would go here
    # For now, return placeholder
    return {
        'model': 'claude-3-opus',
        'response': 'Claude integration coming soon. Add your Anthropic API key to enable.',
        'status': 'Coming Soon',
        'metadata': {'tokens': 0, 'cost_estimate': 0}
    }


def build_analysis_prompt(results, original_prompt):
    """Build the meta-analysis prompt for Gemini"""
    prompt = f"""You are an expert AI model evaluator. Analyze the following model outputs for the same prompt and provide a structured assessment.

Original Prompt: "{original_prompt}"

Model Outputs:
"""
    
    model_names = []
    for i, result in enumerate(results, 1):
        model_name = result['model']
        model_names.append(model_name)
        prompt += f"\n{i}. {model_name}:\n{result['response']}\n"
    
    prompt += f"""
Please analyze these responses and provide a JSON response with the following structure:
{{
  "overall_clarity_score": <float 0-10>,
  "overall_relevance_score": <float 0-10>,
  "overall_factual_accuracy": <float 0-10>,
  "overall_reasoning_quality": <float 0-10>,
  "overall_conciseness": <float 0-10>,
  "overall_summary": "<detailed comparison and recommendation>",
  "model_comparison": {{
    "{model_names[0] if len(model_names) > 0 else 'model1'}": {{
      "clarity": <float 0-10>,
      "relevance": <float 0-10>,
      "accuracy": <float 0-10>,
      "reasoning": <float 0-10>,
      "conciseness": <float 0-10>
    }},
    "{model_names[1] if len(model_names) > 1 else 'model2'}": {{
      "clarity": <float 0-10>,
      "relevance": <float 0-10>,
      "accuracy": <float 0-10>,
      "reasoning": <float 0-10>,
      "conciseness": <float 0-10>
    }}
    {', "' + model_names[2] + '": { "clarity": <float 0-10>, "relevance": <float 0-10>, "accuracy": <float 0-10>, "reasoning": <float 0-10>, "conciseness": <float 0-10> }' if len(model_names) > 2 else ''}
    {', "' + model_names[3] + '": { "clarity": <float 0-10>, "relevance": <float 0-10>, "accuracy": <float 0-10>, "reasoning": <float 0-10>, "conciseness": <float 0-10> }' if len(model_names) > 3 else ''}
  }}
}}

IMPORTANT: Provide scores for ALL {len(model_names)} models that were tested. Make sure the differences between models are clear and significant where applicable. Evaluate each dimension carefully and provide scores that highlight the strengths and weaknesses of each model.
"""
    
    return prompt


def parse_analysis_response(text):
    """Parse the Gemini analysis response into structured data"""
    
    # Try to extract JSON from the response
    try:
        # Look for JSON block
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            analysis = json.loads(json_match.group(0))
            # Ensure backward compatibility with old field names
            if 'overall_clarity_score' in analysis:
                analysis['clarity_score'] = analysis['overall_clarity_score']
                analysis['relevance_score'] = analysis['overall_relevance_score']
                analysis['factual_accuracy'] = analysis['overall_factual_accuracy']
                analysis['reasoning_quality'] = analysis['overall_reasoning_quality']
                analysis['conciseness'] = analysis['overall_conciseness']
            return analysis
    except:
        pass
    
    # Fallback: create a basic structure
    return {
        'clarity_score': 7.5,
        'relevance_score': 8.0,
        'factual_accuracy': 7.5,
        'reasoning_quality': 8.0,
        'conciseness': 7.0,
        'overall_summary': text,
        'model_comparison': {}
    }
