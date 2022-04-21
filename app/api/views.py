from flask import jsonify, request, abort,url_for, render_template, redirect, flash
from flask_login import login_user, current_user, logout_user, login_required
from app import login_manager, basic_auth, db
from app.api import api, api_doc_list
from app import main
from app.models import User, Conversation
from app.sse.views import push_message_to_redis
from app.auth.oauth2 import require_oauth
from authlib.integrations.flask_oauth2 import current_token


@api.route("/help")
@require_oauth('readonly')
def help_api():
    return render_template("help_api.html",
            url_root = request.url_root,
            api_doc = api_doc_list)


@api.route("/user/getUnreadMessages", methods=["GET"])
@login_required
@require_oauth('readonly')
def get_unread_messages():
    """Get a list of all unread messages"""
    data = current_user.api_get_unread_messages()
    return jsonify(data)


@api.route("/user/setStatus", methods=["POST"])
@login_required
def set_about_me():
    """Set status, use parameter "about_me". """
    content = request.form.get("about_me")
    if content:
        data = current_user.api_set_about_me(content)
        return jsonify(data)
    abort(400)


@api.route("/user/getAPIkey", methods=["GET"])
@basic_auth.login_required
def get_api_key():
    # To remove
    """Returns an api key if http basic auth succeed."""
    data = basic_auth.current_user().get_api_key()
    return jsonify(data)


@api.route("/user/getConversations", methods=["GET"])
@login_required
def get_conversations():
    """Returns all conversations of a user, you can specify the number of messages to return per conversation.
    Use a GET request with query string: ?messages=3 default is 10."""
    message_number = request.args.get("messages", 10, type=int)
    data = current_user.api_get_conversations(message_number)
    return jsonify(data)


@api.route("/conversation/<uuid:conversation_uuid>/getConversation", methods=["GET"])
@login_required
def get_conversation(conversation_uuid):
    """Returns messages of a specific conversation, you can specify the number of messages to return per conversation.
    Use query string parameter "messages" i.e /?messages=3 default is 10."""
    message_number = request.args.get("messages", 10, type=int)
    data = current_user.api_get_conversation(conversation_uuid, message_number)
    return jsonify(data)


@api.route("/conversation/<uuid:conversation_uuid>/addMessage", methods=["POST"])
@login_required
def add_message(conversation_uuid):
    """Add a message to a conversation, Use parameter "message"."""
    message_content = request.form.get("message")
    if message_content:
        data = current_user.api_add_message_to_conversation(
            conversation_uuid, message_content
        )
        return jsonify(data)
    abort(400)


@api.route("/conversation/<uuid:conversation_uuid>/delete", methods=["DELETE"])
@login_required
def delete_conversation(conversation_uuid):
    """Simply delete the conversation. Everything will be removed from the database."""
    data = current_user.api_delete_conversation(conversation_uuid)
    return jsonify(data)


@api.route("/conversation/<uuid:conversation_uuid>/addUsers", methods=["POST"])
@login_required
def add_users_conversation(conversation_uuid):
    """Add a list of user. Use parameter "username_list" username should be separated by space."""
    username_list = request.form.get("users").split()
    if username_list:
        data = current_user.api_add_users(conversation_uuid, username_list)
        return jsonify(data)
    abort(400)


@api.route("/conversation/<uuid:conversation_uuid>/leave", methods=["PUT"])
@login_required
def leave_conversation(conversation_uuid):
    """Simply leave a conversation."""
    data = current_user.api_leave_conversation(conversation_uuid)
    return jsonify(data)


@api.route("/user/getHelp", methods=["GET"])
def get_help():
    """Returns a list of API endpoint with their description."""
    data = api_doc_list
    return jsonify(data)


@api.route("/user/setAvatar", methods=["POST"])
@login_required
def set_avatar():
    pass
