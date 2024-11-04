from flask import Flask, render_template, url_for, request, redirect

app = Flask(__name__, static_folder='assets')


@app.route('/')
def index():
  user_authenticated = False;
  return render_template("index.html", user_authenticated=user_authenticated)


@app.route('/login', methods=['GET', 'POST'])
def login():
  emailUser = "daniel@email.com"
  senhaUser = "123456"

  if request.method == 'POST':
      email = request.form.get('email')
      senha = request.form.get('senha')
      print(f"Recebido o forms: {email} e {senha}")

      if email == emailUser and senha == senhaUser:
        print("Redirecting to perfil")
        return redirect(url_for('perfil', email=emailUser, senha=senhaUser))
      
  return render_template('login.html')


@app.route('/perfil')
def perfil():
   username = "Daniel San"
   email = request.args.get('email')
   return render_template('perfil.html', username=username, email=email)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
