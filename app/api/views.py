from flask import jsonify, request, abort,url_for, render_template, redirect, flash
from app import login_manager, db
from app.api import api, api_doc_list
from app import main
from app.models import User, Conversation
from app.sse.views import push_message_to_redis
from app.auth.oauth2 import require_oauth
from authlib.integrations.flask_oauth2 import current_token

@api.route("/help")
def help_api():
    return render_template("help_api.html",
            api_doc = api_doc_list)


@api.route("/user/getUnreadMessages", methods=["GET"])
@require_oauth(['read','modify'],operator='OR')
def get_unread_messages():
    """Get a list of all conversations containing unread messages. 
    You can choose the number of conversations returned per page. ?conversations=3 default is 10"""
    page = request.args.get("page", 1, type=int)
    conversations_per_page = request.args.get("conversations", 10, type=int)
    data = current_token.user.api_get_unread_messages(page,conversations_per_page)
    return jsonify(data)


@api.route("/user/setStatus", methods=["POST"])
@require_oauth('modify')
def set_about_me():
    """Set status, use parameter "about_me". """
    content = request.form.get("about_me")
    if content:
        data = current_token.user.api_set_about_me(content)
        return jsonify(data)
    abort(400)

@api.route("/user/getConversations", methods=["GET"])
@require_oauth(['read','modify'],operator='OR')
def get_conversations():
    """Returns all conversations of a user, you can specify the number of conversations to return per page
    and also the number of messages returned per conversations.
    Use a GET request with query string: 
        ?messages=3 default is 1.
        ?conversations=3 default is 10."""
    page = request.args.get("page", 1, type=int)
    conversations_per_page = request.args.get("conversations", 10, type=int)
    messages_per_page = request.args.get("messages", 1, type=int)
    data = current_token.user.api_get_conversations(page,conversations_per_page,messages_per_page)
    return jsonify(data)


@api.route("/conversation/<uuid:conversation_uuid>/getConversation", methods=["GET"])
@require_oauth(['read','modify'],operator='OR')
def get_conversation(conversation_uuid):
    """Returns messages of a specific conversation, you can specify the number of messages to return per page.
    Use query string parameter "messages" i.e /?messages=3 default is 10."""
    page = request.args.get("page", 1, type=int)
    messages_per_page  = request.args.get("messages", 10, type=int)
    data = current_token.user.api_get_conversation(conversation_uuid,page,messages_per_page)
    return jsonify(data)


@api.route("/conversation/<uuid:conversation_uuid>/addMessage", methods=["POST"])
@require_oauth('modify')
def add_message(conversation_uuid):
    """Add a message to a conversation, Use parameter "message"."""
    message_content = request.form.get("message")
    if message_content:
        data = current_token.user.api_add_message_to_conversation(
            conversation_uuid, message_content
        )
        return jsonify(data)
    abort(400)


@api.route("/conversation/<uuid:conversation_uuid>/delete", methods=["DELETE"])
@require_oauth('modify')
def delete_conversation(conversation_uuid):
    """Simply delete the conversation. Everything will be removed from the database."""
    data = current_token.user.api_delete_conversation(conversation_uuid)
    return jsonify(data)


@api.route("/conversation/<uuid:conversation_uuid>/addUsers", methods=["POST"])
@require_oauth('modify')
def add_users_conversation(conversation_uuid):
    """Add a list of user. Use parameter "username_list" username should be separated by space."""
    username_list = request.form.get("users").split()
    if username_list:
        data = current_token.user.api_add_users(conversation_uuid, username_list)
        return jsonify(data)
    abort(400)


@api.route("/conversation/<uuid:conversation_uuid>/leave", methods=["PUT"])
@require_oauth('modify')
def leave_conversation(conversation_uuid):
    """Simply leave a conversation."""
    data = current_token.user.api_leave_conversation(conversation_uuid)
    return jsonify(data)


@api.route("/user/getHelp", methods=["GET"])
def get_help():
    """Returns a list of API endpoint with their description."""
    data = api_doc_list
    return jsonify(data)


@api.route("/user/setAvatar", methods=["POST"])
@require_oauth('modify')
def set_avatar():
    pass
