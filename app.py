from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    # Example data that could be used in Jinja loops
    files = [f"File {i}" for i in range(1, 6)]
    return render_template('index.html', files=files)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    message = data.get("message", "")
    reply = f"You asked: {message}"  # mock AI response
    return jsonify({"reply": reply})


@app.route('/home')
def home():
    return render_template('home.html')


if __name__ == "__main__":
    app.run(debug=True)
