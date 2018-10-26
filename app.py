# -*- coding:utf-8 -*-


import os

from flask import Flask
from flask import redirect, url_for
from flask import flash
from flask_login import login_required, logout_user
from form import LoginForm

from flask_login import login_user, LoginManager, UserMixin
from flask import render_template
from flask_bootstrap import Bootstrap
from flask_script import Manager, Shell
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand

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

    # 产生admin/admin这个账号


# class TodoList(db.Model):
#     __tablename__ = 'todolists'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, nullable=False)
#     title = db.Column(db.String(1024), nullable=False)
#     status = db.Column(db.Integer, nullable=False)
#     create_time = db.Column(db.Integer, nullable=False)
#
#     def __init__(self, user_id, title, status):
#         self.user_id = user_id
#         self.title = title
#         self.status = status
#         self.create_time = time.time()

def make_shell_context():
    return dict(app=app, db=db, User=User)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/add/<int:article_id>", methods=["GET", "POST"])
def add():
    pass


@app.route("/delete/<int:article_id>")
def delete():
    pass


@app.route("/change/<int:article_id>", methods=["GET", "POST"])
def change():
    pass


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


if __name__ == "__main__":
    manager.run()
