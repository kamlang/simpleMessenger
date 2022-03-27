from flask import redirect, jsonify, request, abort, Response
from flask_login import login_required
from flask_wtf.csrf import validate_csrf
from functools import wraps
from app.models import User, Conversation
from app.xhr import xhr
from html import escape

def with_csrf_validation(view_func):
    # Added to handle request send via xhr
    @wraps(view_func)
    def validating_csrf(*args, **kwargs):
        csrf_token = request.headers.get("X-CSRFToken")
        try:
            validate_csrf(csrf_token)
        except Exception as e:
            raise e
        return view_func(*args, **kwargs)

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
    conversation = Conversation.get_conversation_by_uuid(conversation_uuid)
    try:
        conversation.delete()
        return redirect(url_for("main.conversations"))
    except:
        abort(403)


@xhr.route("/conversation/<uuid:conversation_uuid>/leave")
@login_required
@with_csrf_validation
def leave_conversation(conversation_uuid):
    # Accessed via xhr to leave a conversation.
    conversation = Conversation.get_conversation_by_uuid(conversation_uuid)
    try:
        conversation.remove_user()
        return redirect(url_for("main.conversations"))
    except:
        abort(403)


@xhr.route("/conversation/<uuid:conversation_uuid>/mark_as_read")
@login_required
@with_csrf_validation
def mark_as_read(conversation_uuid):
    """Accessed via xhr to mark the conversation as read when user is currently browsing it
    also reset unread message count"""
    conversation = Conversation.get_conversation_by_uuid(conversation_uuid)
    try:
        conversation.reset_unread_messages()
        return Response(status=204)
    except:
        abort(403)

