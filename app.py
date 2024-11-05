import flask
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from typing import List, override
import flask_login
from flask_login import LoginManager, UserMixin

login_manager = LoginManager()
app = Flask(__name__, static_folder='assets')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["SECRET_KEY"] = "foobar"
login_manager.init_app(app)


class Teste(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Teste)
db.init_app(app)

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str]
    def __init__(self, username: str, email: str) -> None:
        super().__init__()
        self.username = username
        self.email = email

    @staticmethod
    def get(user_id: str):
        return db.session.query(User).filter_by(id=user_id).first()

    def __repr__(self) -> str:
        return f'User({self.username}, {self.email})'

    # def is_authenticated(self):
    #     return True
    # def is_active(self):
    #     return True
    # def is_anonymous(self):
    #     return False
    # def get_id(self):
    #     return "foobar"

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id: str):
    return User.get(user_id)

@app.route('/')
def index():
    user_authenticated = False;
    return render_template("index.html", user_authenticated=user_authenticated)


@app.route('/signin', methods=['POST'])
def signin():
    emailUser = request.form['email']
    # passUser = request.form['senha']
    result = db.session.query(User).filter_by(email=emailUser).first()

    if result == None:
        flask.abort(400, "User was not found")

    if flask_login.login_user(result):
        print("Logged in:", result)
        return flask.redirect(flask.url_for("index"))
    else:
        flask.abort(400, "Failed to log in user")

@app.route('/login', methods=['GET'])
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
