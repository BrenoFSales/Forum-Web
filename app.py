import flask
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from typing import List, override
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

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
    password: Mapped[str] = mapped_column()
    def __init__(self, username: str, email: str, password: str) -> None:
        super().__init__()
        self.username = username
        self.email = email
        self.password = password

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
    return render_template("index.html")


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    # Recebe os dados do formulário de login e verifica se os dados são válidos e existem no banco de dados
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        user = db.session.query(User).filter_by(email=email).first()
        if (user and user.password == senha):  # Verificação direta da senha
                login_user(user) # Realiza o login do usuário na sessão
                return redirect(url_for('perfil'))
        else:
                flash('Senha incorreta. Tente novamente.') # Retorna mensagem de erro ao logar para a tela de login
    
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Recebe os dados do formulário de cadastro
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User(username=username, email=email, password=password) # Cria um novo objeto da classe 'user'
        db.session.add(user) # Adiciona o ojeto a classe
        db.session.commit()  # Faz o commit registrando o novo usuário no banco 

        return redirect(url_for('signin'))

    return render_template('cadastro.html')


# Rota para logout do Usuário que está atualmente logado
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/perfil')
def perfil():
    return render_template('perfil.html')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
