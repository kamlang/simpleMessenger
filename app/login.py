from flask import request, jsonify, abort
from app import login_manager,basic_auth
from app.models import AnonymousUser,User

login_manager.anonymous_user = AnonymousUser
login_manager.session_protection = "strong"
login_manager.login_view = "auth.login"

@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Basic ', '', 1)
        user = User.query.filter_by(api_key=api_key).first_or_404()
        return user

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/api/"):
        message= { "message":"Please provide a valid API key." }
        return jsonify(message), 401
    else:
        abort(401)

@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first_or_404()
    if user and user.verify_password(password):
        return user

@basic_auth.error_handler
def basic_auth_error(status):
    abort(status)
