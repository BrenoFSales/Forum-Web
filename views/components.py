
from typing import List, NewType
from flask import render_template
import app

Component = NewType('Component', str)

def post(post: app.Post, linkable: bool = False):
    return Component(render_template(
        'post.html',
        post=post,
        post_html_id=f'post-{post.id}',
        linkable=linkable
    ))

def base(content: Component):
    return Component(render_template('baseLayout.html', content=content))

def header(content: Component):
    return Component(render_template('headerLayout.html', content=content))

def subforum_index(threads: List[app.Post], subforum: app.Subforum):
    return Component(render_template(
        "subforum_index.html",
        recent=[post(t, linkable=True) for t in threads],
        subforum=subforum
    ))

def profile(user_posts: List[app.Post]):
    return Component(render_template(
        'perfil.html',
        recent=[post(i, linkable=True) for i in user_posts]
    ))

def thread(thread: app.Post, replies: List[app.Post]):
    return Component(render_template(
        'thread.html',
        thread=thread, thread_template=post(thread),
        replies=[post(i) for i in replies]
    ))
