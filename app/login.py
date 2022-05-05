from flask import request, jsonify, abort
from app import login_manager
from app.models import AnonymousUser,User

login_manager.anonymous_user = AnonymousUser
login_manager.session_protection = "strong"
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)
