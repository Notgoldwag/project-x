from flask import Flask, render_template, request, jsonify, redirect, url_for



app = Flask(__name__)

@app.route('/')
def root():
    # Redirect to /login_signup when the app starts
    return redirect(url_for('index'))

@app.route('/login_signup')
def index():
    files = [f"File {i}" for i in range(1, 6)]
    return render_template('index.html', files=files)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    message = data.get("message", "")
    reply = f"You asked: {message}"
    return jsonify({"reply": reply})

@app.route('/home')
def home():
    return render_template('home.html')



if __name__ == "__main__":
    app.run(debug=True)
