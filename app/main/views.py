from flask import (
    request,
    flash,
    url_for,
    redirect,
    render_template,
    current_app,
    session,
    g,
    jsonify,
    abort,
    Response,
)
from flask_login import login_user, current_user, logout_user, login_required
from html import escape
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.urls import url_parse
from datetime import datetime
from werkzeug.utils import secure_filename
import time
from flask_wtf.csrf import validate_csrf
from app.models import User, Role, Message, Conversation
from app.main.forms import editUser, sendReply, createConversation, addUserConversation
from app.auth import auth
from app.main import main
from app.sse.views import push_message_to_redis
from app import db

@main.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("main.conversations"))
    return redirect(url_for("auth.login"))


@main.route("/create_conversation")
@login_required
def new_conversation():
    new_conversation = Conversation()
    return redirect(
        url_for(
            "main.conversation", conversation_uuid=new_conversation.conversation_uuid
        )
    )


@main.route("/conversations", methods=["GET", "POST"])
@login_required
def conversations():
    form = editUser()
    if form.validate_on_submit():
        if form.about_me.data:
            current_user.about_me = form.about_me.data
            db.session.commit()
        if form.avatar.data:
            current_user.avatar = form.avatar.data
            db.session.commit()
        return redirect(url_for("main.conversations"))
    page = request.args.get("page", 1, type=int)
    conversations = current_user.get_all_conversations(page)

    next_url = (
        url_for("main.conversations", page=conversations.next_num)
        if conversations.has_next
        else None
    )
    prev_url = (
        url_for("main.conversations", page=conversations.prev_num)
        if conversations.has_prev
        else None
    )
    return render_template(
        "display_conversations.html",
        conversations=conversations.items,
        form=form,
        next_url=next_url,
        prev_url=prev_url,
    )


@main.route("/conversation/<uuid:conversation_uuid>", methods=["GET", "POST"])
@login_required
def conversation(conversation_uuid):
    form_add = addUserConversation()
    form_send = sendReply()
    page = request.args.get("page", 1, type=int)

    conversation = Conversation.get_conversation_by_uuid(conversation_uuid)
    if not current_user in conversation.users:
        abort(403)

    if form_add.validate_on_submit():
        # Add a list of user to a conversation. Only admin of a conversation can add a user.
        username_list = form_add.usernames.data.split()
        try:
            conversation.add_users(username_list)
        except:
            abort(403)
        return redirect(
            url_for("main.conversation", conversation_uuid=conversation_uuid)
        )

    if form_send.validate_on_submit():  # Adding message to a conversation
        content = form_send.content.data
        message = Message(sender=current_user, content=content)
        conversation.add_message(message)
        push_message_to_redis(conversation, content)
        #    return Response(status=204)
        return redirect(
            url_for("main.conversation", conversation_uuid=conversation_uuid)
        )

    conversation.reset_unread_messages()
    users = conversation.users.all() 
    messages = conversation.messages.paginate(
        page, current_app.config["POSTS_PER_PAGE"], False
    )
    admin = conversation.admin.username
    # TODO: fix duplicate code
    next_url = (
        url_for(
            "main.conversation",
            conversation_uuid=conversation_uuid,
            page=messages.next_num,
        )
        if messages.has_next
        else None
    )
    prev_url = (
        url_for(
            "main.conversation",
            conversation_uuid=conversation_uuid,
            page=messages.prev_num,
        )
        if messages.has_prev
        else None
    )
    return render_template(
        "display_conversation.html",
        messages=messages.items,
        users=users,
        next_url=next_url,
        prev_url=prev_url,
        form_send=form_send,
        form_add=form_add,
        admin=admin,
        conversation=conversation,
    )

### XHR views

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


@main.route("/getUserInfo/<username>")
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

@main.route("/conversation/<uuid:conversation_uuid>/delete")
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


@main.route("/conversation/<uuid:conversation_uuid>/leave")
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


@main.route("/conversation/<uuid:conversation_uuid>/mark_as_read")
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

@main.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@main.after_request
def add_header_no_cache(response):
    # Disabling cache so conversations page is refreshed when user is pressing the back button.
    response.headers["Cache-Control"] = "no-store"
    return response
