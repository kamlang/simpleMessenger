from flask import request, flash, url_for, redirect, render_template, current_app, session, g, abort
from flask_login import login_user, current_user, logout_user,login_required
from ..models import User,Role
from .forms import registerForm,loginForm
from . import auth
from .. import db
from .. import login_manager
from ..email import sendEmailToAdmin
from werkzeug.security import generate_password_hash, check_password_hash

errorMessage="An error happened!"
successMessage="Operation succeed !"

@auth.route('/login', methods=['GET', 'POST'])
def login(): ### Restrict to unauthenticate user 
    form=loginForm()
    if request.method=='POST':
        if form.validate() == True:
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
        return redirect(url_for('.login'))
    return render_template("form.html", form=form,form_name='Login')

@auth.route('/register', methods=['GET', 'POST']) ### Restrict to unauthenticate user 
def register():
    form=registerForm()
    if request.method == 'POST':
        if form.validate() == True:
            username = request.form['username']
            password = request.form['password']
            email= request.form['email']
            user=User(username=username,password=password,email=email,role='User')
            if usernameExist(username):
                flash("username already exist.")
                return redirect('/register')
            db.session.add(user)
            try:
                db.session.commit()
                flash("You're registered. You can now login.")
                subject ="A new user has registered."
#                sendEmailToAdmin(subject, 'mail/new_user',user=username)
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                flash("error in UPDATE operation")
        return redirect(url_for('auth.register'))
    return render_template('form.html', form=form, form_name='Register')

@auth.route("/logout")
@login_required
def logout():
    flash("See you soon {}".format(current_user.username))
    logout_user()
    return redirect('/')

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

def usernameExist(username):
    q=User.query.filter_by(username=username).first()
    if q is None:
        return False
    return True
