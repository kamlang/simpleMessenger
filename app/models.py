from . import db,login_manager
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
import os
from datetime import datetime

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

class User(db.Model,UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(20),unique=True)
    password_hash=db.Column(db.String(100))
    email=db.Column(db.String(155))
    roles = db.relationship('Role', secondary='user_roles')
    confirmed = db.Column(db.Boolean, default=False)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_name = db.Column(db.String(32))
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    @property
    def role(self):
        pass
    @role.setter
    def role(self, role):
        try:
            self.roles.append(Role.query.filter_by(name=role).first())
        except:
            raise AttributeError('The role specified do not exists')
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def is_role(self,role):
        for r in self.roles:
            if r.name == role:
                return True
        return False
    def last_seen_clean(self):
       return self.last_seen.ctime()

    def set_avatar(self,avatar_data):
        import hashlib
        from PIL import Image
        image = Image.open(avatar_data)
        data = list(image.getdata())
        image2 = Image.new(image.mode, image.size)
        image2.putdata(data)
        filename = hashlib.md5(self.username.encode())
        self.avatar_name=filename.hexdigest()
        image2.thumbnail((128,128))
        image2.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename.hexdigest()),format='png')
    def get_avatar_path(self):
        return os.path.join('../static/avatars/',self.avatar_name)

class AnonymousUser(AnonymousUserMixin):
    def is_role(self,role):
        return False
login_manager.anonymous_user = AnonymousUser
