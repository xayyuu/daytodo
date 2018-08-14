from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


class Todolist(db.Model):
    __tablename__ = "todolist"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.text())
    isdone = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __init__(self, user_id, body, isdone):
        self.user_id = user_id
        self.body = body
        self.isdone = isdone
        self.timestamp = datetime.utcnow()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    todolists = db.relationship('Todolist', backref='todolist', lazy='dynamic') # 意义不大，目前不存在根据用户来处理不同todo的情况，只有admin账号

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_admin(self, username='admin'):
        """增加admin用户"""
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user is None:
            admin_passwd = os.getenv('TODO_ADMIN_PASSWORD', 'admin123456')
            admin_user = User(username, admin_password)
            db.session.add(admin_user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

