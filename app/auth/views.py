from flask import request, flash, url_for, redirect, render_template, current_app, session, g, abort
from flask_login import login_user, current_user, logout_user,login_required
from ..models import User,Role
from .forms import registerForm,loginForm, passwordReset,usernameReset,editUser, sendMessage
from . import auth
from .. import db
from .. import login_manager
from ..email import send_email
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.urls import url_parse
from datetime import datetime
from werkzeug.utils import secure_filename
import os

errorMessage="An error happened!"
successMessage="Operation succeed !"

###### Defining some custom decorator

def confirm_required(viewFunc): 
    @wraps(viewFunc)
    def isConfirmed(*args,**kwargs):
        if current_user.confirmed:
            return viewFunc(*args,**kwargs)
        flash('Current account has not been confirmed yet.')
        return redirect(url_for('auth.logout'))
    return isConfirmed

def unauthenticated_required(viewFunc):
    @wraps(viewFunc)
    def isUnauthenticated(*args,**kwargs):
        if current_user.is_anonymous:
            return viewFunc(*args,**kwargs)
        return redirect('/')
    return isUnauthenticated

###### Defining views

@auth.route('/login', methods=['GET', 'POST'])
@unauthenticated_required
def login(): ### Restrict to unauthenticate user 
    form=loginForm()
    if form.validate_on_submit():
        username=request.form['username']
        password=request.form['password']
        user=User.query.filter_by(username=username).first()
        next_page = request.args.get('next')
        if user is not None and user.verify_password(password):
            login_user(user,form.remember_me.data)
            if not next_page or url_parse(next_page).netloc != '':
                return redirect(url_for('auth.showprofile'))
            return redirect(next_page)
        else:
            flash("User do not exist or password is incorrect")
            return redirect(url_for('auth.showprofile'))

    return render_template("form.html", form=form,form_name='Login')

@auth.route('/register', methods=['GET', 'POST']) ### Restrict to unauthenticate user 
@unauthenticated_required
def register():
    form=registerForm()
    if form.validate_on_submit():
        username = request.form['username']
        password = request.form['password']
        email= request.form['email']
        user=User(username=username,password=password,email=email, role='User')
        db.session.add(user)
        db.session.commit()
        send_token_confirm(user)
        return redirect('/')
    return render_template('form.html', form=form, form_name='Register')

@auth.route("/reset/<token>", methods=['GET', 'POST'])
@unauthenticated_required
def reset(token):
    form=passwordReset()
    if form.validate_on_submit():
        new_password = request.form['password']
        username = request.form['username']
        user=User.query.filter_by(username=username).first()
        if not user is None:
            if user.confirm(token):
                user.password = new_password
                db.session.add(user)
                db.session.commit()
                flash("Password updated successfully.")
            else:
                flash("Verification failed. Either the username is invalid or link as expired.")
        else:
            flash("Username do not exists")
        return redirect(url_for('auth.login'))
    return render_template('form.html', form=form,form_name='Reset password')
        

@auth.route("/reset_request", methods=['GET', 'POST'])
@unauthenticated_required
def reset_request():
    form=usernameReset()
    if form.validate_on_submit():
        username=request.form['username']
        user = User.query.filter_by(username=username).first()
        if not user is None:
            send_token_reset(user)
    return render_template("form.html", form=form,form_name='Reset password')

@auth.route("/confirm/<token>")
@login_required
def confirm(token):
    if current_user.confirm(token):
        flash("You're account is now active")
        return redirect(url_for('auth.showprofile'))
    else: 
        flash(errorMessage)
        return redirect('auth.failed',username=current_user.username)

@auth.route("/failed/<username>")
@login_required
def failed(username):
    if not current_user.confirmed:
        return render_template('failed.html',username=current_user.username)    
    return redirect('/')

@auth.route("/logout")
@login_required
def logout():
    flash("See you soon {}".format(current_user.username))
    logout_user()
    return redirect('/')

@auth.route('/profile')
@login_required
@confirm_required
def showprofile():
    return render_template('profile.html')

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

@auth.route('/resend_token')
@login_required
def resend_token():
    if not current_user.confirmed:
        send_token_confirm(current_user)
    return redirect('/')

@auth.route('/edit/<username>', methods=['GET', 'POST'])
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
        return redirect(url_for('auth.showprofile'))
    return render_template("form.html", form=form,form_name='Edit your profile')

    ### save path to userdb

@auth.route('/messages')
@login_required
def messages():
# if form.validate_on_submit():
    page = request.args.get('page', 1, type=int)
    messages = current_user.get_all_messages(page)
    next_url = url_for('auth.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('auth.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template("display_messages.html",messages=messages.items, next_url=next_url, prev_url=prev_url)

@auth.route('/send/<username>', methods=['GET', 'POST'])
@login_required
def send_message(username):
    form=sendMessage()
    form_name = 'Send a message to: ' + username
    if form.validate_on_submit():
        recipient = User.query.filter_by(username=username).first()
        content = request.form['content']
        current_user.send_message(recipient,content)
        return redirect(url_for('auth.messages'))
    return render_template('form.html',form_name=form_name,form=form)

def send_token_confirm(user):
    token = user.generate_confirmation_token()
    try:
        send_email(user.email, 'Confirm Your Account','/email/confirm', username=user.username, token=token)
        flash("You're registered. Please check you emails.")
    except Exception as e:
        flash("Email was not sent")

def send_token_reset(user):
    token = user.generate_confirmation_token()
    try:
        send_email(user.email, 'Password reset','/email/reset', username=user.username, token=token)
        flash("An email has been sent to you.")
    except Exception as e:
        flash("Email was not sent")

@auth.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
