from flask import request, flash, url_for, redirect, render_template, current_app, session, g, abort
from flask_login import login_user, current_user, logout_user,login_required
from app.models import User,Role
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
import os

### Defining custom decorators:

def confirm_required(viewFunc): 
    @wraps(viewFunc)
    def is_confirmed(*args,**kwargs):
        if current_user.confirmed:
            return viewFunc(*args,**kwargs)
        flash('Current account has not been confirmed yet.')
        return redirect(url_for('auth.logout'))
    return is_confirmed

### Defining view functions

@main.route('/')
def home():
    return redirect(url_for('auth.login'))

@main.route('/profile')
@login_required
@confirm_required
def showprofile():
    return render_template('profile.html')

@main.route('/edit/<string:username>', methods=['GET', 'POST'])
@login_required
@confirm_required
def edit(username):
    form=editUser()
    if current_user.username != username:
        abort(403)
    if form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        if form.about_me.data:
            user.about_me = form.about_me.data
            db.session.add(user)
            db.session.commit()
        if form.avatar.data:
            user.set_avatar(form.avatar.data)
            db.session.add(user)
            db.session.commit()
        return redirect(url_for('main.showprofile'))
    return render_template("form.html", form=form,form_name='Edit your profile')

    ### save path to userdb

@main.route('/create_conversation', methods=['GET', 'POST'])
@login_required
@confirm_required
def new_conversation():
    form = createConversation()
    if form.validate_on_submit():
        usernames=form.usernames.data.split()
        content=form.content.data
        username_list = []
        for username in usernames:
            username_list.append(username)
        current_user.create_conversation(username_list,content)
        return redirect(url_for('main.conversations'))
    return render_template("form.html",form=form)

@main.route('/conversations')
@login_required
@confirm_required
def conversations():
    page = request.args.get('page', 1, type=int)
    conversations=current_user.get_conversations(page)
    next_url = url_for('main.conversations', page=conversations.next_num) \
        if conversations.has_next else None
    prev_url = url_for('main.conversations', page=conversations.prev_num) \
        if conversations.has_prev else None
    return render_template("display_conversations.html",conversations=conversations.items, 
            next_url=next_url, prev_url=prev_url)

@main.route('/conversation/<int:conversation_id>', methods=['GET', 'POST'])
@login_required
@confirm_required
def conversation(conversation_id):
    form_send = sendReply()
    form_add= addUserConversation()
    if form_add.validate_on_submit():
        usernames=form_add.usernames.data.split()
        username_list = []
        for username in usernames:
            username_list.append(username)
        try:
            current_user.add_users_conversation(conversation_id,username_list)
        except:
            flash('Only admin of a group can add a user.')
        return redirect(url_for('main.conversation',conversation_id=conversation_id))
    if form_send.validate_on_submit():
        content=form_send.content.data
        current_user.add_message_conversation(conversation_id,content)
        return redirect(url_for('main.conversation',conversation_id=conversation_id))

    page = request.args.get('page', 1, type=int)
    conversation = current_user.get_conversation(conversation_id)
    if not conversation is None:
        users=conversation.users.all()
        messages = conversation.messages.paginate(page,current_app.config['POSTS_PER_PAGE'],False)
        admin=conversation.admin.username
        next_url = url_for('main.conversation',conversation_id=conversation_id, page=messages.next_num) \
            if messages.has_next else None
        prev_url = url_for('main.conversation',conversation_id=conversation_id, page=messages.prev_num) \
            if messages.has_prev else None
        return render_template("display_conversation.html",messages=messages.items,users=users, 
                next_url=next_url, prev_url=prev_url,form_send=form_send,form_add=form_add,admin=admin,
                conversation=conversation)
    abort(403)


@main.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
