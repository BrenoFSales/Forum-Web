from datetime import datetime
from enum import unique
import flask
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, joinedload, relationship
from sqlalchemy.orm import Mapped, mapped_column
from typing import List
import flask_login
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.orm.scoping import Optional

login_manager = LoginManager()
app = Flask(__name__, static_folder='assets')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["SECRET_KEY"] = "foobar"
login_manager.init_app(app)


class Teste(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Teste)
db.init_app(app)

# SQLAlchemy não faz migrações por padrão. qualquer alteração feita à essas classes não vai ser
# refletida no banco imediatamente a não ser que delete ele

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str]
    password: Mapped[str] = mapped_column(nullable=False)
    country_code: Mapped[str] = mapped_column(nullable=False) # ISO 3166-1 alpha-2
    profile_picture: Mapped[str] = mapped_column(nullable=True) # url pra um recurso estático
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="user")

    def __init__(self, username: str, email: str, password: str, country_code: str) -> None:
        super().__init__()
        self.username = username
        self.email = email
        self.password = password
        self.country_code = country_code

    @staticmethod
    def get(user_id: str):
        return db.session.query(User).filter_by(id=user_id).first()

    def __repr__(self) -> str:
        return f'User({self.username}, {self.email})'

# threads e comentários em threads são ambos Post. na há necessidade de criar classes separadas para os dois.
class Post(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=True)
    content: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    attachment: Mapped[str] = mapped_column(nullable=True)
    subforum_id: Mapped[int] = mapped_column(ForeignKey("subforum.id"), nullable=False)

    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("post.id"), nullable=True)
    replies: Mapped[List["Post"]] = relationship("Post", back_populates="parent", cascade="all, delete-orphan")
    parent: Mapped[Optional["Post"]] = relationship("Post", back_populates="replies", remote_side=[id])

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="posts")

    def __init__(
        self, user_id: int, title: str, content: str, attachment: str, subforum_id: int,
            parent_id: Optional[int] = None) -> None:
        super().__init__()
        self.user_id = user_id
        self.title = title
        self.content = content
        self.attachment = attachment
        self.subforum_id = subforum_id
        self.parent_id = parent_id

    def __repr__(self) -> str:
        return f'Post(user="{self.user.username}", id={self.id}, replies={len(self.replies)}, \
title="{self.title}", content="{self.content})"'

class Subforum(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str] = mapped_column(nullable=False)
    posts: Mapped[List["Post"]] = relationship()

    def __init__(self, name: str, description: str) -> None:
        super().__init__()
        self.name = name
        self.description = description


# do mesmo modo, alterações feitas nessas entidades não vão alterar o banco. delete o banco e reinicie o projeto.
with app.app_context():
    db.create_all()
    try:
        db.session.add_all([
            Subforum("Games", "Subforum dedicado à jogos"),

            Subforum("Anime", "Subforum dedicado animações Japonesas \
(desenhos ocidentais são proibidos!)"),

            Subforum("Tecnologia", "Subforum dedicado à discussões de \
hardware e software"),

            Subforum("Livros", "Subforum dedicado à literatura de todos \
os generos e culturas (mangás não são livros. vire gente!)"),

            Subforum("Politica", "Subforum dedicado à discussões politicas e eventos atuais."),
            Subforum("Ciência", "Subforum dedicado à discussões intelectuais e grupo de estudos."),
            Subforum("Hentai", "XXX"),
        ])
        db.session.add(User("daniel", "daniel@email.com", "daniel", "br"))
        db.session.add(User("breno", "breno@email.com", "breno", "br"))

        db.session.add_all([
            Post(1, "teste pai", "essa é a thread pai", "", 1),
            Post(1, "teste filho 1", "post filho 2", "", 1, 1),
            Post(1, "teste filho 2", "post filho 3", "", 1, 1),
        ])
        db.session.commit()
    except Exception as e:
        pass

@login_manager.user_loader
def load_user(user_id: str):
    return User.get(user_id)

# preenche as informações do template de um post. também utilizado para renderizar um post pai.
def post_template(post: Post):
    return render_template('post.html', post=post)

@app.route('/')
def index():
    result = db.session.query(Post).filter(Post.parent_id == None).order_by(Post.id).limit(10).all()
    return render_template("index.html", recent=[post_template(i) for i in result])

@app.route('/signup', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    # country_code = request.form['country_code']
    country_code = "br"

    db.session.add(User(username, email, password, country_code))
    db.session.commit()

    return flask.redirect(flask.url_for("signin"))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    match request.method:
        case 'GET':
            return render_template('login.html')
        case 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            if email is None or password is None:
                flask.abort(400, "Incorrect form fields")

            result = db.session.query(User).filter_by(email=email, password=password).first()

            if result == None:
                flash('Senha incorreta. Tente novamente.') # Retorna mensagem de erro
                return render_template('login.html')


            if flask_login.login_user(result): # loga usuário caso true
                print("Logged in:", result)
                return flask.redirect(flask.url_for("index"))
            else:
                flask.abort(400, "Failed to log in user")

    # inutil, porém meu language server reclama sem isso.
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Recebe os dados do formulário de cadastro
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if username is None or email is None or password is None:
            flask.abort(400, "Incorrect form fields")
        
        user = User(username, email, password, "br") # Cria um novo objeto da classe 'user'
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
@login_required
def perfil():
    return render_template('perfil.html')

@app.route('/thread/<id>')
def thread(id):
    result = (db.session
        .query(Post)
        .options(
            joinedload(Post.user),
            joinedload(Post.replies).joinedload(Post.user))
        .filter(Post.id == id)
        .first())

    if result is None:
        flask.abort(400)

    return render_template(
        'thread.html',
        thread=post_template(result),
        replies=[post_template(i) for i in result.replies]
    )

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
