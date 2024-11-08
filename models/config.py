from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship
from typing import List


db = SQLAlchemy()

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
