# -*- coding:utf-8 -*-
import os
from datetime import datetime

from flask import Flask
from flask import redirect, url_for
from flask import flash
from flask import render_template

from flask_login import login_user, LoginManager, UserMixin, login_required, logout_user, current_user
from flask_bootstrap import Bootstrap
from flask_script import Manager, Shell
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_moment import Moment

from form import LoginForm, TaskForm


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

manager = Manager(app)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
moment = Moment(app)
login_manager = LoginManager(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """
    UserMixin 实现了使用login_login插件所需要调用的方法。
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __init__(self, username, password):
        self.username = username
        self.password = generate_password_hash(password)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # user外键，关联User表，回头可通过userid，找到对应user的task
    title = db.Column(db.String(2048), nullable=False)
    status = db.Column(db.Integer, nullable=False)  # 标志该项任务是否完成， 0 代表未完成， 1代表完成
    create_time = db.Column(db.DateTime, nullable=False)  # 创建时间，使用datetime.datetime类型，可用于utc计时

    def __init__(self, user_id, title, status=0):
        self.user_id = user_id
        self.title = title
        self.status = status
        self.create_time = datetime.utcnow()


@app.route("/")
@login_required
def index():
    # 使用current_user.id查询到对应的task，并使用模版渲染
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", tasks=tasks)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(current_user.id, form.title.data, form.status.data)
        db.session.add(task)
        db.session.commit()
        flash("Add one task.")
        return redirect(url_for("index"))
    return render_template("add.html", form=form)


@app.route("/delete/<int:article_id>")
@login_required
def delete(article_id):
    task = Task.query.filter_by(id=article_id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash("Delete one task.")
    return redirect(url_for("index"))


@app.route("/change/<int:article_id>", methods=["GET", "POST"])
@login_required
def change(article_id):
    form = TaskForm()
    task = Task.query.filter_by(id=article_id).first_or_404()
    if form.validate_on_submit():
        task.title = form.title.data
        task.status = form.status.data
        db.session.add(task)
        db.session.commit()
        return redirect(url_for("index"))
    form.title.data = task.title
    form.status.data = task.status
    return render_template("modify.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # print("form username, form password:", form.username.data, form.password.data)
        # print("username, password", user.username, user.password_hash)
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid username or password.")
        return redirect(url_for("login"))  # Post/重定向/Get模式，确保最后一个请求是get请求
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You had logout!!!")
    return redirect(url_for("login"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


def make_shell_context():
    return dict(app=app, db=db, User=User, Task=Task)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


if __name__ == "__main__":
    manager.run()
