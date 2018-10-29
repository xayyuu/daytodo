# -*- coding:utf-8 -*-
import os
from threading import Thread

from flask import Flask, request
from flask import redirect, url_for
from flask import flash
from flask import render_template

from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_bootstrap import Bootstrap
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_moment import Moment
from flask_mail import Mail, Message

from form import LoginForm, TaskForm, RegistrationForm
from models import db, User, Task


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.126.com'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[TODOLIST]'
app.config['FLASKY_MAIL_SENDER'] = 'Daytodo-Admin<kidult1107@126.com>'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')  # Admin管理者邮箱

manager = Manager(app)
bootstrap = Bootstrap(app)
db.init_app(app)
migrate = Migrate(app, db)
moment = Moment(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


# 无法使用这个，使用后会报错
# @app.before_request
# def before_request():
#     if not current_user.confirmed:
#         return redirect(url_for('unconfirmed'))


@app.route('/unconfirmed')
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('index'))
    return render_template('unconfirmed.html')


@app.route("/")
@login_required
def index():
    if not current_user.confirmed:
        return redirect(url_for('unconfirmed'))
    # 使用current_user.id查询到对应的task，并使用模版渲染
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", tasks=tasks)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if not current_user.confirmed:
        return redirect(url_for('unconfirmed'))
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
    if not current_user.confirmed:
        return redirect(url_for('unconfirmed'))
    task = Task.query.filter_by(id=article_id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash("Delete one task.")
    return redirect(url_for("index"))


@app.route("/change/<int:article_id>", methods=["GET", "POST"])
@login_required
def change(article_id):
    if not current_user.confirmed:
        return redirect(url_for('unconfirmed'))
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
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid email or password.")
        return redirect(url_for("login"))  # Post/重定向/Get模式，确保最后一个请求是get请求
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You had logout!!!")
    return redirect(url_for("login"))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account',
                   'email/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/confirm/<token>')
#@login_required
def confirm(token):
    if current_user.confirmed:  # 有点疑问，从邮箱点击这个，此时有current_user这个信息吗？
        return redirect(url_for('index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('index'))


@app.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('index'))


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
