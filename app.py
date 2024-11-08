from datetime import datetime
from enum import unique
import os
from re import sub
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
from werkzeug.wrappers import response

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
    attachment: Mapped[Optional[str]] = mapped_column(nullable=True)

    subforum_id: Mapped[int] = mapped_column(ForeignKey("subforum.id"), nullable=False)
    subforum: Mapped["Subforum"] = relationship("Subforum", back_populates="posts")

    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("post.id"), nullable=True)
    replies: Mapped[List["Post"]] = relationship("Post", back_populates="parent", cascade="all, delete-orphan")
    parent: Mapped[Optional["Post"]] = relationship("Post", back_populates="replies", remote_side=[id])

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="posts")

    def __init__(
        self, user_id: int, title: str, content: str, subforum_id: int, attachment: Optional[str] = None, 
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
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="subforum")

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
            Post(1, "teste pai", "essa é a thread pai", 1, ""),
            Post(2, "teste filho 1", "post filho 2",    1, "", 1),
            Post(2, "teste filho 2", "post filho 3",    1, "", 1),

            Post(2, "teste pai2", "essa é a thread pai", 1, ""),
            Post(1, "teste filho 3", "post filho 2",    1, "", 4),
            Post(1, "teste filho 4", "post filho 3",    1, "", 4),
        ])
        db.session.commit()
    except Exception as e:
        pass

@login_manager.user_loader
def load_user(user_id: str):
    return User.get(user_id)

# preenche as informações do template de um post. também utilizado para renderizar um post pai.
def post_template(post: Post, linkable: bool = False):
    return render_template('post.html', post=post, post_html_id=f'post-{post.id}', linkable=linkable)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/subforum/<name>')
def subforum_index(name: str):
    subforum = db.session.query(Subforum).filter_by(name=name).first()
    if subforum is None:
        flask.abort(400, 'Subforum nao pode ser encontrado')
    result = (db.session
        .query(Post)
        .filter(Post.parent_id == None)
        .filter(Post.subforum_id == subforum.id)
        .order_by(0 - Post.id) #lmao
        .limit(10)
        .all())
    return render_template(
        "subforum_index.html",
        recent=[post_template(i, linkable=True) for i in result],
        subforum=subforum
    )

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
                flask.abort(400, "email ou senha inexistentes")

            result = db.session.query(User).filter_by(email=email, password=password).first()

            if result == None:
                flash('Senha incorreta. Tente novamente.') # Retorna mensagem de erro
                return render_template('login.html')


            if flask_login.login_user(result): # loga usuário caso true
                print("Logged in:", result)
                return flask.redirect(flask.url_for("index"))
            else:
                flask.abort(400, "falha ao logar usuário")

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
            flask.abort(400, "usuário, email ou senha inexistentes")
        
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
    result = (db.session
        .query(Post)
        .filter(Post.user_id == current_user.id)
        .order_by(Post.id)
        .limit(10)
        .all())
    return render_template('perfil.html',recent=[post_template(i, linkable=True) for i in result])

@app.route('/thread/<id>', methods=['GET'])
def thread(id):
    result = (db.session
        .query(Post)
        .options(
            joinedload(Post.user),
            joinedload(Post.replies).joinedload(Post.user))
        .filter(Post.id == id)
        .first())

    if result is None or result.parent_id != None:
        flask.abort(400, "thread não encontrada")

    return render_template(
        'thread.html',
        thread=result,
        thread_template=post_template(result),
        replies=[post_template(i) for i in result.replies]
    )


def make_new_post_from_form(subforum: str, request: flask.Request, parent_id: int | None = None):
    user = flask_login.current_user

    subforum_ = db.session.query(Subforum).filter(Subforum.name == subforum).first()
    if subforum_ is None:
        flask.abort(400, "subforum não encontrado")
    subforum_id = subforum_.id

    title = request.form.get('title')
    content = request.form.get('content')
    uploaded_file = request.files.get('attachment')

    if title is None or content is None or title is None or uploaded_file is None:
        flask.abort(400, "Algum desses inexistente: 'content', 'title' ou 'uploaded_file'")

    saved = None
    if uploaded_file.filename != '' and uploaded_file.filename != None:
        saved = os.path.join('images', uploaded_file.filename)
        uploaded_file.save(os.path.join('assets', saved))

    # breakpoint()
    post = Post(
        user_id     = user.id,
        title       = title,
        content     = content,
        subforum_id = subforum_id,
        attachment  = saved,
        parent_id   = parent_id
    )
    db.session.add(post)
    db.session.commit()
    return post

@app.route('/<subforum>/newthread', methods=['POST'])
def new_thread(subforum: str):
    thread = make_new_post_from_form(subforum, request)
    return flask.redirect(flask.url_for('thread', id=thread.id))

@app.route('/editarThread/<id>', methods=['POST'])
def editarThread(id):
    novo_conteudo = request.form.get('content')
    novo_title = request.form.get('title')
    if novo_conteudo is None or novo_title is None:
        flask.abort(400, "'content' ou 'title' em form não pode ser encontrado")

    result = (db.session
        .query(Post)
        .filter(Post.id == id)
        .first())
    if result is None:
        flask.abort(400, "Post não pode ser encontrado")

    result.content = novo_conteudo
    result.title = novo_title
    db.session.commit()
    return flask.redirect(flask.url_for('thread', id=result.id))
    
@app.route('/excluirThread/<id>', methods=['POST'])
def excluirThread(id):
    result = (db.session
        .query(Post)
        .options(joinedload(Post.replies))
        .filter(Post.id == id)
        .first())

    db.session.delete(result)
    db.session.commit()

    return ""
    # return flask.redirect(flask.url_for('perfil'))

@app.route('/thread/<int:id>', methods=['POST'])
def new_reply(id: int):
    thread = db.session.query(Post).options(joinedload(Post.subforum)).filter(Post.id == id).first()
    if thread is None or thread.id is None:
        flask.abort(400, "Thread não pode ser encontrada")
    if thread.subforum is None:
        flask.abort(400, "Subforum de thread não pode ser encontrado")
    make_new_post_from_form(thread.subforum.name, request, parent_id=thread.id)
    return flask.redirect(flask.url_for('thread', id=thread.id))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
