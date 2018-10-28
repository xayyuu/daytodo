# -*- coding:utf-8 -*-
import os
from datetime import datetime
from threading import Thread

from flask import Flask, request, current_app
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
from flask_mail import Mail, Message
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from form import LoginForm, TaskForm, RegistrationForm

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.126.com'  # kidult1107@126.com，使用这个的
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['TODOLIST_MAIL_SUBJECT_PREFIX'] = '[TODOLIST]'
app.config['TODOLIST_MAIL_SENDER'] = 'TODOLIST Admin <kidult1107@126.com>'
app.config['TODOLIST_ADMIN'] = os.environ.get('TODOLIST_ADMIN')  # Admin管理者邮箱

manager = Manager(app)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
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
    msg = Message(app.config['TODOLIST_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['TODOLIST_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


class User(UserMixin, db.Model):
    """
    UserMixin 实现了使用flask_login插件所需要调用的方法。
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def __init__(self, email, username, password):
        self.email = email
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


@app.before_request
def before_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint \
            and request.endpoint != 'static':
        return redirect(url_for('unconfirmed'))


@app.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('index'))
    return render_template('unconfirmed.html')


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
        user = User.query.filter_by(email=form.email.data).first()
        # print("form username, form password:", form.username.data, form.password.data)
        # print("username, password", user.username, user.password_hash)
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
@login_required  # 有点疑问，此时从邮箱点击这个，能登录吗？
def confirm(token):
    if current_user.confirmed:  # 有点疑问，此时从邮箱点击这个，能登录吗？有current_user这个信息吗？
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
