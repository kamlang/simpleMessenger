from flask import request, flash, url_for, redirect, render_template, current_app, session, g, abort
from flask_login import login_user, current_user, logout_user,login_required
from ..models import User,Role
from .forms import registerForm,loginForm
from . import auth
from .. import db
from .. import login_manager
from ..email import send_email
from werkzeug.security import generate_password_hash, check_password_hash

errorMessage="An error happened!"
successMessage="Operation succeed !"

@auth.route('/login', methods=['GET', 'POST'])
def login(): ### Restrict to unauthenticate user 
    form=loginForm()
    if form.validate_on_submit():
        username=request.form['username']
        password=request.form['password']
        user=User.query.filter_by(username=username).first()
        if user is not None and user.verify_password(password):
            try:
                login_user(user,form.remember_me.data)
                return redirect(url_for('restricted.showprofile', username=user.username))
            except:
                    flash(errorMessage)
        else:
            flash("User do not exist or password is incorrect")
    return render_template("form.html", form=form,form_name='Login')

@auth.route('/register', methods=['GET', 'POST']) ### Restrict to unauthenticate user 
def register():
    form=registerForm()
    if form.validate_on_submit():
        username = request.form['username']
        password = request.form['password']
        email= request.form['email']
        user=User.query.filter_by(username=username).first()
        if user is None:
            user=User(username=username,password=password,email=email, role='User')
            db.session.add(user)
            db.session.commit()
            send_token(user)
        else:
            flash("username already exist.")
            return redirect('/register')
        try:
            #            subject ="A new user has registered."
#                sendEmailToAdmin(subject, 'mail/new_user',user=username)
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash("error in UPDATE operation")
    return render_template('form.html', form=form, form_name='Register')

@auth.route("/confirm/<token>")
@login_required
def confirm(token):
    if current_user.confirm(token):
        flash("You're account is now active")
        return redirect(url_for('restricted.profile',username=current_user.username))
    else: 
        flash(errorMessage)
        return redirect('auth.failed',username=current_user.username)

@auth.route("/failed")
@login_required
def notconfirmed(username):
    return rendertemplate('failed.html',username=current_user.username)    
    
@auth.route("/logout")
@login_required
def logout():
    flash("See you soon {}".format(current_user.username))
    logout_user()
    return redirect('/')

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

@auth.route('/resendtoken')
@login_required
def resend_token():
    send_token(current_user)

def send_token(user):
    token = user.generate_confirmation_token()
    try:
        send_email(user.email, 'Confirm Your Account','/email/confirm', user=user, token=token)
        flash("You're registered. Please check you emails.")
    except Exception as e:
        flash("Email was not sent")

