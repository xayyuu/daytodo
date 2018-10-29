# -*- coding:utf-8 -*-
from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


db = SQLAlchemy()


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
        self.password_hash = generate_password_hash(password)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # user外键，关联Task表，回头可通过userid，找到对应user的task
    title = db.Column(db.String(2048), nullable=False)
    status = db.Column(db.Integer, nullable=False)  # 标志该项任务是否完成， 0 代表未完成， 1代表完成
    create_time = db.Column(db.DateTime, nullable=False)  # 创建时间，使用datetime.datetime类型，可用于utc计时

    def __init__(self, user_id, title, status=0):
        self.user_id = user_id
        self.title = title
        self.status = status
        self.create_time = datetime.utcnow()


