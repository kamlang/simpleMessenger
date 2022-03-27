from flask import jsonify, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from app import login_manager, basic_auth
from app.api import api
from app.models import User, Conversation
from app.sse.views import push_message_to_redis

error_message = {"message":"An error happened, please verify synthax."}

@api.route("/user/getUnreadMessages",methods = ["GET"])
@login_required
def get_unread_messages():
    # Get a list of unread messages
    data = current_user.api_get_unread_messages()
    return jsonify(data)

@api.route("/user/setStatus",methods = ["POST"])
@login_required
def set_about_me():
    # Set status, POST request must have "about_me" parameter
    content = request.form.get('about_me')
    if content:
        data = current_user.api_set_about_me(content)
        return jsonify(data)
    else:
        return jsonify(error_message)


@api.route("/user/setAvatar",methods = ["POST"])
@login_required
def set_avatar():
    pass

@api.route("/user/getConversations", methods = ["GET"])
def get_conversation():
    """ Get all conversations of a user, you can specify then number of messages returned per conversationin query string:
    ie ?/messages=3 """
    message_number = request.args.get("messages", 10, type=int)
    data = current_user.api_get_conversations(message_number)
    return jsonify(data)

@api.route("/conversation/<uuid:conversation_uuid>/addMessage",methods = ["POST"])
@login_required
def add_message(conversation_uuid):
    # Add a message to a conversation POST request must have "message" parameter
    message_content = request.form.get('message')
    if message_content:
        data = current_user.api_add_message_to_conversation(conversation_uuid,message_content)
        return jsonify(data)
    else:
        return jsonify(error_message)


@api.route("/conversation/<uuid:conversation_uuid>/getMessages",methods = ["GET"])
@login_required
def get_messages(conversation_uuid):
    page = request.args.get("page", 1, type=int)
    data = current_user.api_get_messages(conversation_uuid,page)
    return jsonify(data)

@api.route("/conversation/<uuid:conversation_uuid>/delete",methods = ["DELETE"])
@login_required
def delete_conversation(conversation_uuid):
    data = current_user.api_delete_message(conversation_uuid)
    return jsonify(data)


@api.route("/conversation/<uuid:conversation_uuid>/addUsers",methods = ["POST"])
@login_required
def add_users_conversation(conversation_uuid):
    username_list = request.form.get('users').split()
    if username_list:
        data = current_user.api_add_users(conversation_uuid,username_list)
        return jsonify(data)
    else:
        return jsonify(error_message)
        

@api.route("/conversation/<uuid:conversation_uuid>/leave",methods = ["PUT"])
@login_required
def leave_conversation(conversation_uuid):
    data = current_user.api_leave_conversation(conversation_uuid)
    return jsonify(data)


@api.route('/getAPIkey', methods=['GET'])
@basic_auth.login_required
def get_api_key():
    # Return an api key if http basic auth succeed
    # curl --basic --user username:password /endpoint
    api_key = basic_auth.current_user().get_api_key()
    return jsonify({'API key': api_key})