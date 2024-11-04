from flask import Flask, render_template, url_for, request, redirect
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column

app = Flask(__name__, static_folder='assets')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"


class Teste(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Teste)
db.init_app(app)

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str]
    def __init__(self, username: str, email: str) -> None:
        super().__init__()
        self.username = username
        self.email = email

with app.app_context():
    db.create_all()

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
