from flask import redirect, jsonify, request, abort, Response, url_for
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf
from functools import wraps
from app.models import User, Conversation
from app.xhr import xhr
from html import escape

def with_csrf_validation(view_func):
    # Added to handle csrf validation for xhr request
    @wraps(view_func)
    def validating_csrf(*args, **kwargs):
        csrf_token = request.headers.get("X-CSRFToken")
        try:
            validate_csrf(csrf_token)
            return view_func(*args, **kwargs)
        except Exception as e:
            raise e
        redirect("/")
    return validating_csrf


@xhr.route("/getUserInfo/<username>")
@login_required
@with_csrf_validation
def get_user_info(username):
    # This is used to populate popovers when mouseover event is triggered in conversations.
    user = User.query.filter_by(username=username).first_or_404()
    # Has this will be injected directly into an html string we have to escape about_me which is an untrusted user input.
    return jsonify(
        {
            "last_seen": user.last_seen,
            "about_me": escape(user.about_me),
            "avatar": user.avatar,
        }
    )

@xhr.route("/conversation/<uuid:conversation_uuid>/delete")
@login_required
@with_csrf_validation
def delete_conversation(conversation_uuid):
    # Accessed via xhr to delete a conversation.
    conversation = current_user.get_conversation_by_uuid(conversation_uuid)
    try:
        current_user.delete_conversation(conversation)
    except:
        abort(403)


@xhr.route("/conversation/<uuid:conversation_uuid>/leave")
@login_required
@with_csrf_validation
def leave_conversation(conversation_uuid):
    # Accessed via xhr to leave a conversation.
    conversation = current_user.get_conversation_by_uuid(conversation_uuid)
    try:
        current_user.leave_conversation(conversation)
    except:
        abort(403)


@xhr.route("/conversation/<uuid:conversation_uuid>/mark_as_read")
@login_required
@with_csrf_validation
def mark_as_read(conversation_uuid):
    """Accessed via xhr to mark the conversation as read when user is currently browsing it
    also reset unread message count"""
    conversation = current_user.get_conversation_by_uuid(conversation_uuid)
    try:
        conversation.reset_unread_messages(current_user)
        return Response(status=204)
    except:
        abort(403)

