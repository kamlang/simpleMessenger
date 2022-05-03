from flask import jsonify, request, abort,url_for, render_template, redirect, _app_ctx_stack
from flask_login import current_user
from authlib.integrations.flask_oauth2 import current_token
from functools import wraps
from flask_wtf.csrf import validate_csrf,CSRFError,ValidationError
from app import login_manager, db
from app.api import api, api_doc_list
from app import main
from app.models import User, Conversation
from app.auth.oauth2 import require_oauth
from werkzeug.local import LocalProxy

class login_or_oauth_required():
    """ We want the API to be accessible from js and by oauth user.
    So here we're checking if user is authenticated via classic method,
    if so we're checking if csrf token is valid.
    If not we're checking if the oauth token is acceptable to access this ressource.
    We're also creating a new current_api_user proxy so view function doesn't have to switch
    between current_user and current_token proxy."""

    def __init__(self, scope, operator = "AND"):
        self.scope = scope
        self.operator = operator

    def _set_current_api_user(self, user):
        ctx = _app_ctx_stack.top
        ctx.current_api_user = user

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args,**kwargs):
            if current_user.is_authenticated:
                csrf_token = request.headers.get("X-CSRFToken")
                try:
                    validate_csrf(csrf_token)
                except ValidationError as error:
                    raise CSRFError
                self._set_current_api_user(current_user)
                return f(*args,**kwargs)
            try:
                require_oauth.acquire_token(self.scope,self.operator)
            except Exception as error:
                raise require_oauth.raise_error_response(error)
            self._set_current_api_user(current_token.user)
            return f(*args,**kwargs)
        return wrapper

def _get_current_api_user():
    ctx = _app_ctx_stack.top
    return getattr(ctx, 'current_api_user', None)

current_api_user = LocalProxy(_get_current_api_user)

@api.route("/help")
def help_api():
    return render_template("help_api.html",
            api_doc = api_doc_list)

@api.route("/user/getUnreadMessages", methods=["GET"])
@login_or_oauth_required(['read','modify'],operator='OR')
def get_unread_messages():
    """Returns a list of all conversations containing unread messages.
    You can choose the number of conversations returned per page.
    Use a GET request with query string:
    ?conversations=3 default is 10. """

    page = request.args.get("page", 1, type=int)
    conversations_per_page = request.args.get("conversations", 10, type=int)
    data = current_api_user.api_get_unread_messages(page,conversations_per_page)
    return jsonify(data)


@api.route("/user/setStatus", methods=["POST"])
@login_or_oauth_required('modify')
def set_about_me():
    """Set status, use parameter "about_me". """
    content = request.form.get("about_me")
    if content:
        data = current_api_user.api_set_about_me(content)
        return jsonify(data)
    abort(400)

@api.route("/user/getConversations", methods=["GET"])
@login_or_oauth_required(['read','modify'],operator='OR')
def get_conversations():
    """Returns all conversations of a user, you can specify the number of conversations returned per page
    and also the number of messages returned per conversations.
    Use a GET request with query string:
    ?messages=3 default is 1.
    ?conversations=3 default is 10."""
    page = request.args.get("page", 1, type=int)
    conversations_per_page = request.args.get("conversations", 10, type=int)
    messages_per_page = request.args.get("messages", 1, type=int)
    print("coucou")
    print(current_api_user)
    data = current_api_user.api_get_conversations(page,conversations_per_page,messages_per_page)
    return jsonify(data)


@api.route("/conversation/<uuid:conversation_uuid>/getConversation", methods=["GET"])
@login_or_oauth_required(['read','modify'],operator='OR')
def get_conversation(conversation_uuid):
    """Returns messages of a specific conversation, you can specify the number of messages to return per page.
    Use a GET request with query string:
    ?messages=3 default is 10."""
    page = request.args.get("page", 1, type=int)
    messages_per_page  = request.args.get("messages", 10, type=int)
    data = current_api_user.api_get_conversation(conversation_uuid,page,messages_per_page)
    return jsonify(data)


@api.route("/conversation/<uuid:conversation_uuid>/addMessage", methods=["POST"])
@login_or_oauth_required('modify')
def add_message(conversation_uuid):
    """Add a message to a conversation, Use parameter "message" to specify message content."""
    message_content = request.form.get("message")
    if message_content:
        data = current_api_user.api_add_message_to_conversation(
            conversation_uuid, message_content
        )
        return jsonify(data)
    abort(400)


@api.route("/conversation/<uuid:conversation_uuid>/delete", methods=["DELETE"])
@login_or_oauth_required('modify')
def delete_conversation(conversation_uuid):
    """Simply delete the conversation. Everything will be removed from the database."""
    data = current_api_user.api_delete_conversation(conversation_uuid)
    return jsonify(data)


@api.route("/conversation/<uuid:conversation_uuid>/addUsers", methods=["POST"])
@login_or_oauth_required('modify')
def add_users_conversation(conversation_uuid):
    """Add a list of user. Use parameter "username_list" username should be separated by space."""
    username_list = request.form.get("users").split()
    if username_list:
        data = current_api_user.api_add_users(conversation_uuid, username_list)
        return jsonify(data)
    abort(400)


@api.route("/conversation/<uuid:conversation_uuid>/leave", methods=["PUT"])
@login_or_oauth_required('modify')
def leave_conversation(conversation_uuid):
    """Simply leave a conversation."""
    data = current_api_user.api_leave_conversation(conversation_uuid)
    return jsonify(data)


@api.route("/user/getHelp", methods=["GET"])
@login_or_oauth_required('modify')
def get_help():
    """Returns a list of API endpoint with their description."""
    data = api_doc_list
    return jsonify(data)


@api.route("/user/setAvatar", methods=["POST"])
@login_or_oauth_required('modify')
def set_avatar():
    pass
