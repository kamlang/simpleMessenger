from flask import Flask, request, flash, url_for, redirect, render_template, current_app, session, g, abort
import logging
from flask_login import login_user, current_user, logout_user,login_required
from functools import wraps
from . import main
from .forms import registerForm,loginForm, editUserForm
from .. import db
from .. import login_manager
from ..models import User,Role
from ..email import sendEmailToAdmin

errorMessage="An error happened!"
successMessage="Operation succeed !"

def admin_required(viewFunc):
    @wraps(viewFunc)
    def isadmin(username):
        if g.userIsAdmin:
            return viewFunc(username)
        abort(403)
    return isadmin

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST']) ### Restrict to unauthenticate user 
def register():
    form=registerForm()
    if request.method == 'POST':
        if form.validate() == True:
            username = request.form['username']
            password = request.form['password']
            email= request.form['email']
            if usernameExist(username):
                flash("username already exist.")
                return redirect('/register')
            user = User(username=username,password=password,email=email)
            user.roles = Role.query.filter_by(name='User')
            db.session.add(user)
            try:
                db.session.commit()
                flash("You're registered. You can now login.")
                subject ="A new user has registered."
                sendEmailToAdmin(subject, 'mail/new_user',user=username)
            except Exception as e:
                db.session.rollback()
                flash("error in UPDATE operation")
            return redirect('/')
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login(): ### Restrict to unauthenticate user 
    form=loginForm()
    if request.method=='POST':
        if form.validate() == True:
            username=request.form['username']
            password=request.form['password']
            user=User.query.filter_by(username=username).first()
            if user is not None and user.password==password:
                try:
                    login_user(user)
                    return redirect(url_for('.showprofile', username=user.username))
                except:
                    flash(errorMessage)
            else:
                flash("Login failed.")
    return render_template("login.html", form=form)

@main.route('/showall') ### Admin
def showall():
    if not g.userIsAdmin:
        abort(403)
    users=User.query.all()
    return render_template('showall.html', users=users)

@main.route('/profile/<username>')
def showprofile(username):
    if not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()
    elif current_user.username == username:
        return render_template('profile.html',user=username)
    abort(403)

@main.route("/logout")
def logout():
    if not current_user.is_authenticated:
        flash(errorMessage)
        return redirect('/')
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

@main.route('/edit/<username>',methods=['GET', 'POST']) ###Admin
@login_required
@admin_required
def edit(username):
    form=editUserForm()
    form.role.choices=getRolesList()
    if form.validate() == True:
        role=request.form['role']
        user=User.query.filter_by(username=username).first()
        role=Role.query.filter_by(name=role).first()
        if user is not None:
            user.roles = [role]
            try:
                db.session.commit()
                flash(successMessage)
                return redirect('/showall')
            except Exception as e:
                db.session.rollback()
                flash("error in UPDATE operation")
                return redirect('/showall')
    return render_template('edit.html',form=form,user=username)

@main.route("/delete/<username>") ###Admin
@login_required
@admin_required
def delete(username):
    q = User.query.filter_by(username=username).first()
    if q is not None:
        try:
            db.session.delete(q)
            db.session.commit()
            flash(successMessage)
        except Exception as e:
            logging.debug(e)
            db.session.rollback()
            flash(errorMessage)
    return redirect('/showall')

@main.before_request
def getUserRoles():
    if current_user.is_authenticated:
        g.userIsAdmin = False
        u=User.query.filter_by(username=current_user.username).first()
        userRoles = u.roles
        for userRole in userRoles:
            if userRole.name == 'Admin':
                g.userIsAdmin = True


def getRolesList():
    rolesList=[]
    q=Role.query.all()
    for role in q:
        rolesList.append(role.name)
    return rolesList

