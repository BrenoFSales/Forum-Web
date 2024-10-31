from flask import Flask, render_template

app = Flask(__name__, static_folder='assets')

@app.route('/')
def index():
  user_authenticated = False;
  return render_template("index.html", user_authenticated=user_authenticated)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
