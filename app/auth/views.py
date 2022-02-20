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
)
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.urls import url_parse
from datetime import datetime
from werkzeug.utils import secure_filename
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import os
from app.models import User, Role
from app.auth.forms import register_form, login_form, password_reset_confirmation, confirm_username
from app.auth import auth
from app import db
from app.email import send_email


###### Definig some custom decorator

def unauthenticated_required(viewFunc):
    @wraps(viewFunc)
    def is_unauthenticated(*args, **kwargs):
        if current_user.is_anonymous:
            return viewFunc(*args, **kwargs)
        return redirect("/")
    return is_unauthenticated


###### Defining views

@auth.route("/login", methods=["GET", "POST"])
@unauthenticated_required
def login():  ### Restrict to unauthenticate user
    form = login_form()
    if form.validate_on_submit():
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        next_page = request.args.get("next")
        if user is not None and user.verify_password(password) and user.confirmed == True:
            login_user(user, form.remember_me.data)
            if not next_page or url_parse(next_page).netloc != "":
                return redirect(url_for("main.conversations"))
            return redirect(next_page)
        else:
            flash("User do not exist or password is incorrect")
            return redirect(url_for("main.conversations"))
    return render_template("form.html", form=form, form_name="Login")

@auth.route("/logout")
@login_required
def logout():
    flash("See you soon {}".format(current_user.username))
    logout_user()
    return redirect("/")

@auth.route("/register", methods=["GET", "POST"])  ### Restrict to unauthenticate user
@unauthenticated_required
def register():
    form = register_form()
    if form.validate_on_submit():
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        user = User(username=username, password=password, email=email, role="User")
        db.session.add(user)
        db.session.commit()
        send_email_token('confirmation',username)
        flash("Please check you emails and click on registration link.")
        return redirect("/")
    return render_template("form.html", form=form, form_name="Register")


@auth.route("/password_reset/<token>", methods=["GET", "POST"])
@unauthenticated_required
def reset(token):
    form = password_reset_confirmation()
    if form.validate_on_submit():
        new_password = request.form["password"]
        try:
            username = get_username_from_token(token)
        except:
            flash(
                "Verification failed. Either the username is invalid or link as expired."
            )
            return redirect(url_for('auth.failed'))
        user = User.query.filter_by(username=username).first_or_404()
        user.password = new_password
        db.session.add(user)
        db.session.commit()
        flash("Password updated successfully.")
        return redirect(url_for("auth.login"))
    return render_template("form.html", form=form, form_name="Reset password")

@auth.route("/confirm/<token>")
@unauthenticated_required
def confirm(token):
    try:
        username = get_username_from_token(token)
    except:
        flash(
                "Verification failed. Either the username is invalid or link as expired."
            )
        return redirect(url_for('auth.failed'))
    user = User.query.filter_by(username=username).first_or_404()
    if not user.confirmed:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        flash("Your account has been activated successfully.")
    return redirect(url_for("auth.login"))


@auth.route("/send_link/<choice>", methods=["GET", "POST"])
@unauthenticated_required
def send_link(choice):
    form = confirm_username()
    form_name = {'password_reset':'Reset password','confirmation':'Resend confirmation link'}
    if form.validate_on_submit():
        username = request.form["username"]
        user = User.query.filter_by(username=username).first_or_404()
        send_email_token(choice,username)
        return redirect(url_for("auth.login"))
    return render_template("form.html", form=form, form_name=form_name[choice])


@auth.route("/problem_to_login")
@unauthenticated_required
def failed():
    return render_template("failed.html")

def get_username_from_token(token):
    s = Serializer(current_app.config["SECRET_KEY"])
    try:
        data = s.loads(token)
    except:
        raise Exception("Token is invalid.")
    return data.get("username")

def generate_confirmation_token(username, expiration=3600):
    s = Serializer(current_app.config["SECRET_KEY"], expiration)
    return s.dumps({"username": username})

email_argument = {
    'confirmation': { 'subject': 'Confirm your Account', 'template':'/email/confirm' },
    'password_reset': { 'subject': 'Password reset', 'template':'/email/reset' } 
    }

def send_email_token(context,username):
    user = User.query.filter_by(username=username).first_or_404()
    token = generate_confirmation_token(username)
    send_email(
        user.email,
        email_argument[context]['subject'],
        email_argument[context]['template'],
        username=username,
        token=token,
    )
    flash("Please check your emails and click on the link provided.")
