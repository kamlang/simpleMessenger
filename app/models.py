from . import db
from flask_login import UserMixin

ACCESS = {
    'guest': 0,
    'user': 1,
    'admin': 2
}

def getRolesList(): # to be used for generate drop down menu in WTForms.
    rolesList = []
    for role in ACCESS:
        t = (ACCESS[role],role)
        rolesList.append(t)
    return rolesList

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
    password=db.Column(db.String(20))
    email=db.Column(db.String(155))
    roles = db.relationship('Role', secondary='user_roles')
    def __init__(self,username,password,email):
        self.username = username
        self.password = password
        self.email = email
