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
    stream_with_context,
)
from flask_login import login_user, current_user, logout_user, login_required
from app.models import User, Role, Message, Conversation
from app.main.forms import editUser, sendReply, createConversation, addUserConversation
from app.auth import auth
from app.main import main
from app import db
from app.email import send_email
from app import red
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.urls import url_parse
from datetime import datetime
from werkzeug.utils import secure_filename
import time
from flask_wtf.csrf import validate_csrf

### Event loop

@stream_with_context
def event_stream(username):
    pubsub = red.pubsub()
    pubsub.subscribe(username)
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'retry:15000\ndata: %s\n\n' % message['data'].decode('utf-8')

def push_message(conversation,content):
    ## push message to each user channel
    users = conversation.users.all()
    participants = ' '.join([ user.username for user in users ])
    redis_message = {"event": "new_message", "from": current_user.username, "avatar_name":current_user.avatar,
        "conversation_id":conversation.id,"content":content,"participants":participants}
    try:
        [ red.publish(user.username, str(redis_message)) for user in users ]
    except:
        raise Exception("Pushing message to redis failed.")

### Defining view functions

@main.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.conversations'))
    return redirect(url_for("auth.login"))


@login_required
@main.route('/stream/<username>')
def stream(username): # edit so it's prettier
    if current_user.username == username:
       res = Response(event_stream(username),
                          mimetype="text/event-stream")
       #add custom headers to fix timeout with nginx
       res.headers['Cache-Control'] = 'no-cache'
       res.headers['X-Accel-Buffering'] = 'no'
       res.headers['Connection'] = 'keep-alive'
       return res
    abort(403)

@main.route("/create_conversation", methods=["GET", "POST"])
@login_required
def new_conversation():
    form = createConversation()
    if form.validate_on_submit():
        content = form.content.data
        username_list = form.usernames.data.split()

        new_conversation = Conversation.create_new(admin = current_user,
                message = Message(sender=current_user,content=content),
                username_list = username_list)
                
        push_message(new_conversation,content)
        return redirect(url_for("main.conversations"))
    return render_template("form.html", form=form)


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
        return redirect(url_for('main.conversations'))
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
        form=form,
        next_url=next_url,
        prev_url=prev_url,
    )


    
@main.route("/conversation/<int:conversation_id>", methods=["GET", "POST"])
@login_required
def conversation(conversation_id):
    form_add = addUserConversation()
    form_send = sendReply()
    page = request.args.get("page", 1, type=int)

    conversation = Conversation.query.get(conversation_id)
    if not current_user.is_allowed_to_access(conversation):
        abort(403)

    if form_add.validate_on_submit(): 
        # Adding a list of user to a conversation. Only admin of a conversation can add a user.
        username_list = form_add.usernames.data.split()
        try:
            conversation.add_users(username_list)
        except:
            abort(403)
        return redirect(url_for("main.conversation", conversation_id=conversation_id))

    if form_send.validate_on_submit(): # Adding message to a conversation
        content = form_send.content.data
        message = Message(sender=current_user,content=content)
        conversation.add_message(message)
        push_message(conversation,content)
    #    return Response(status=204)
        return redirect(url_for("main.conversation",conversation_id = conversation_id))


    users = conversation.users.all() # users ?
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

""" Route which take a username as parameter return a json response.
Response is used to populate popovers when mouseover event is triggered in conversations."""
@main.route("/getUserInfo/<username>")
@login_required
def get_user_info(username):
    csrf_token = request.headers.get('X-CSRFToken')
    try :
        validate_csrf(csrf_token)
    except Exception as e:
        raise e
    user = User.query.filter_by(username=username).first_or_404()
    return jsonify({ 'last_seen': user.last_seen,'about_me':user.about_me,'avatar':user.avatar})

@main.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
