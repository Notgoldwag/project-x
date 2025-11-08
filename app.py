from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import requests
import time
import logging
import os

# === Load environment variables ===
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv(
    "GEMINI_API_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
)

# === Initialize Flask ===
app = Flask(__name__, static_folder="static", template_folder=".")

# === Vercel-Safe Logging (NO file writes allowed) ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# === Disable ML Model Loading for Vercel ===
print("🔍 Vercel deployment detected — ML model disabled.")
tokenizer = None
model = None


# ==========================
#         ROUTES
# ==========================

@app.route("/")
def root():
    return send_from_directory(".", "index.html")


@app.route("/login_signup")
def index():
    return render_template("login_signup.html")


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/api-test")
def api_test():
    return send_from_directory(".", "api_test.html")


@app.route("/webhook-test")
def webhook_test():
    return send_from_directory(".", "webhook-test.html")


@app.route("/prompt-injections")
def prompt_injections():
    return render_template("promptinjections.html")


# ==========================
#   AI CHAT — LangChain
# ==========================

@app.route("/api/chat", methods=["POST"])
def ai_chat():
    """Chat endpoint that invokes your LangChain 3-agent orchestration."""
    start = time.time()

    try:
        data = request.get_json() or {}
        message = data.get("message", "").strip()
        session_id = data.get("session_id")

        if not message:
            return jsonify({
                "error": "Message cannot be empty",
                "reply": "Please enter a message to continue."
            }), 400

        # Dynamically import orchestration.py
        try:
            import sys
            import importlib.util

            langchain_dir = os.path.join(os.path.dirname(__file__), "langchain-implement")
            if langchain_dir not in sys.path:
                sys.path.insert(0, langchain_dir)

            spec = importlib.util.spec_from_file_location(
                "orchestration",
                os.path.join(langchain_dir, "orchestration.py")
            )
            orchestration = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(orchestration)

            process_prompt_engineering_sync = orchestration.process_prompt_engineering
            logging.info("✅ LangChain orchestration imported.")

        except Exception as err:
            logging.error(f"❌ LangChain import failed: {err}", exc_info=True)
            return jsonify({
                "error": "LangChain unavailable",
                "reply": "AI orchestration is not fully configured.",
            }), 503

        # Execute orchestration
        result = process_prompt_engineering_sync(message, session_id)

        final_output = result.get("final_output", {})
        if isinstance(final_output, dict):
            ai_response = final_output.get(
                "final_prompt_template",
                final_output.get("response", final_output.get("text", str(final_output)))
            )
        else:
            ai_response = str(final_output)

        total_ms = (time.time() - start) * 1000

        return jsonify({
            "reply": ai_response,
            "session_id": result.get("session_id"),
            "status": result.get("status", "completed"),
            "execution_time_ms": result.get("total_execution_time_ms", 0),
            "immediate_response": result.get("immediate_response"),
            "workflow_id": result.get("workflow_id"),
            "latency_ms": total_ms
        })

    except Exception as e:
        logging.error(f"Chat error: {e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "reply": "Something unexpected happened."
        }), 500


# ==========================
#    N8N WEBHOOK PROXY
# ==========================

@app.route("/api/chat/webhook", methods=["POST"])
def chat_proxy():
    """Proxy to n8n webhook."""
    try:
        data = request.get_json() or {}
        message = data.get("message", "").strip()

        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400

        n8n_url = "https://jkathila.app.n8n.cloud/webhook/dd754342-79d4-4d96-9805-1a46e97cbca3"

        resp = requests.post(
            n8n_url,
            json={"message": message},
            headers={"Content-Type": "application/json"},
            timeout=25
        )

        try:
            j = resp.json()
            if "reply" not in j:
                return jsonify({"reply": j.get("response") or j.get("text") or str(j)})
            return jsonify(j)
        except:
            return jsonify({"reply": resp.text})

    except Exception as e:
        return jsonify({"error": "Webhook error", "detail": str(e)}), 500


# ==========================
#   HEURISTIC SCORING ONLY
# ==========================

@app.route("/api/score_prompt", methods=["POST"])
def score_prompt():
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    protection = data.get("protectionLevel", "basic")

    if not prompt.strip():
        return jsonify({"error": "Prompt cannot be empty"}), 400

    suspicious = [
        "ignore previous", "override", "forget everything", "disregard",
        "new instructions", "system prompt", "admin", "root", "sudo",
        "delete", "bypass", "hack", "exploit"
    ]

    score = sum(p in prompt.lower() for p in suspicious) * 25
    score = min(100, score)
    if protection == "strict":
        score = min(100, score * 1.2)

    return jsonify({
        "score": score,
        "label": "Prompt Injection Detected" if score > 50 else "Safe",
        "heuristics": [f"Contains '{p}'" for p in suspicious if p in prompt.lower()],
        "model_available": False
    })


# ==========================
#    GEMINI EXPLANATION
# ==========================

@app.route("/api/analyze_prompt", methods=["POST"])
def analyze_prompt():
    data = request.get_json() or {}
    prompt = data.get("prompt", "")

    if not prompt.strip():
        return jsonify({"error": "Prompt cannot be empty"}), 400

    explanation = "Gemini API key not configured."
    if GEMINI_API_KEY:
        try:
            body = {
                "contents": [
                    {"parts": [{"text": f"Explain if this is prompt injection:\n{prompt}"}]}
                ]
            }
            resp = requests.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json=body, timeout=15
            )
            data = resp.json()
            explanation = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
        except:
            pass

    return jsonify({
        "score": 0,
        "label": "Heuristic only",
        "heuristics": [],
        "explanation": explanation,
        "model_available": False
    })


# ===========================================================
#   NO app.run() — Vercel uses serverless function handler
# ===========================================================

# END OF FILE
