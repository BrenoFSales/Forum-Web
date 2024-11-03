from flask import Flask, render_template, url_for

app = Flask(__name__, static_folder='assets')

@app.route('/')
def index():
  user_authenticated = False;
  return render_template("index.html", user_authenticated=user_authenticated)

@app.route('/login')
def login():
  return render_template('login.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
