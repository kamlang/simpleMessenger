from flask import (
    request,
    flash,
    url_for,
    redirect,
    render_template,
    current_app,
    session,
    g,
    abort,
    Response,
)
from flask_login import login_user, current_user, logout_user, login_required
from app.models import User, Role
from app.main.forms import editUser, sendReply, createConversation, addUserConversation
from app.auth import auth
from app.main import main
from app import db
from app.email import send_email
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.urls import url_parse
from datetime import datetime
from werkzeug.utils import secure_filename
from app import red
import time

### Event loop

def event_stream(username):
    pubsub = red.pubsub()
    pubsub.subscribe(username)
    # TODO: handle client disconnection.
    # if user inactive ?
    for message in pubsub.listen():
        print (message)
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode('utf-8')

def push_message(conversation_id,content):
    ## push message to each user channel
    users = current_user.get_conversation(conversation_id).users.all()

    participants = ' '.join([user.username for user in users])
    redis_message= {"event": "new_messages", "from": current_user.username,
        "conversation_id":conversation_id,"content":content,"participants":participants}

    [ red.publish(user.username,str(redis_message)) for user in users ]

### Defining view functions

@main.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.conversations'))
    return redirect(url_for("auth.login"))


@login_required
@main.route('/stream/<username>')
def stream(username):
    if current_user.username == username:
       res = Response(event_stream(username),
                          mimetype="text/event-stream")
    #add custom headers to fix timeout with nginx
       res.headers['Cache-Control'] = 'no-cache'
       res.headers['X-Accel-Buffering'] = 'no'
       res.headers['Connection'] = 'keep-alive'
       return res
    abort(403)

@main.route("/myprofile")
@login_required
def showprofile():
    return render_template("profile.html")

@main.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit():
    form = editUser()
    if form.validate_on_submit():
        if form.about_me.data:
            current_user.about_me = form.about_me.data
            db.session.add(current_user)
            db.session.commit()
        if form.avatar.data:
            current_user.set_avatar(form.avatar.data)
            db.session.add(current_user)
            db.session.commit()
        return redirect(url_for("main.showprofile"))
    return render_template("form.html", form=form, form_name="Edit your profile")


@main.route("/create_conversation", methods=["GET", "POST"])
@login_required
def new_conversation():
    form = createConversation()
    if form.validate_on_submit():
        usernames = form.usernames.data.split()
        content = form.content.data
        username_list = []
        for username in usernames:
            username_list.append(username)
        conversation_id = current_user.create_conversation(username_list, content)
        push_message(conversation_id,content)
        return redirect(url_for("main.conversations"))
    return render_template("form.html", form=form)


@main.route("/conversations")
@login_required
def conversations():
    page = request.args.get("page", 1, type=int)
    conversations = current_user.get_conversations(page)
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
        next_url=next_url,
        prev_url=prev_url,
    )


    
@main.route("/conversation/<int:conversation_id>", methods=["GET", "POST"])
@login_required
def conversation(conversation_id):
    form_add = addUserConversation()
    form_send = sendReply()
    page = request.args.get("page", 1, type=int)
    conversation = current_user.get_conversation(conversation_id)

    if conversation is None:
        abort(403)

    if form_add.validate_on_submit():
        usernames = form_add.usernames.data.split()
        username_list = []
        for username in usernames:
            username_list.append(username)
        try:
            current_user.add_users_conversation(conversation_id, username_list)
        except:
            flash("Only admin of a conversation can add a user.")
        return redirect(url_for("main.conversation", conversation_id=conversation_id))

    if form_send.validate_on_submit():
            content = form_send.content.data
            try:
                current_user.add_message_conversation(conversation_id, content)
                push_message(conversation_id,content)
            except:
                raise Exception("An error happened when user submited a message")
            return Response(status=204)

    users = conversation.users.all()
    messages = conversation.messages.paginate(
    page, current_app.config["POSTS_PER_PAGE"], False
    )
    admin = conversation.admin.username
    next_url = (
    url_for(
        "main.conversation",
            conversation_id=conversation_id,
            page=messages.next_num,
        )
        if messages.has_next
        else None
    )
    prev_url = (
        url_for(
            "main.conversation",
            conversation_id=conversation_id,
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


@main.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
