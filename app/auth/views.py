from flask import (
    request,
    flash,
    url_for,
    redirect,
    render_template,
    current_app,
)
from flask_login import login_user, current_user, logout_user, login_required
from functools import wraps
from werkzeug.security import gen_salt
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from authlib.oauth2 import OAuth2Error
import time
from app import db
from app.auth.forms import (
    register_form,
    login_form,
    password_reset_confirmation,
    confirm_username,
    OauthClientForm,
    OAuthConfirm,
)
from app import csrf
from app.auth import auth
from app.main import main
#from app.email import send_email
from app.gmail import send_email
from app.models import User, Role

from .oauth2 import authorization

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
def login():  # Restrict to unauthenticate user
    form = login_form()
    if form.validate_on_submit():
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        next_page = request.args.get("next")
        if (
            user is not None
            and user.verify_password(password)
            and user.confirmed == True
        ):
            login_user(user, form.remember_me.data)
            if not next_page or url_parse(next_page).netloc != "":
                return redirect(url_for("main.conversations"))
            return redirect(next_page)
        else:
            flash("User does not exist or password is incorrect")
            return redirect(url_for("auth.login"))
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
        try:
            user = User(username=username, password=password, email=email) 
            db.session.add(user)
            db.session.commit()
            send_email_token("confirmation", username)
            flash("Please check you emails and click on registration link.")
            return redirect(url_for("auth.login"))
        except Exception as e:
            print(e)
            return redirect(url_for("auth.register"))
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
            return redirect(url_for("auth.failed"))
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
        flash("Verification failed. Either the username is invalid or link as expired.")
        return redirect(url_for("auth.failed"))
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
    form_name = {
        "password_reset": "Reset password",
        "confirmation": "Send a new confirmation link",
    }
    if form.validate_on_submit():
        username = request.form["username"]
        user = User.query.filter_by(username=username).first_or_404()
        send_email_token(choice, username)
        return redirect(url_for("auth.login"))
    return render_template("form.html", form=form, form_name=form_name[choice])


@auth.route("/problem_to_login")
@unauthenticated_required
def failed():
    return render_template("failed.html")

### OAuth stuff

@auth.route("/oauth/register", methods = ["GET","POST"])
@login_required
def register_oauth():
    """ Here a user can create a new Oauth client that he can use to access his data. """
    form = OauthClientForm()
    if form.validate_on_submit():
        client_name = request.form["client_name"],
        client_scope = request.form["allowed_scope"],
        print(type(client_name))
        try:
            current_user.create_oauth2_client(client_name[0],client_scope)
        except Exception as e:
            db.session.rollback()
            raise Exception(e)
        finally:
            return redirect(url_for("auth.get_oauth_clients"))
    return render_template("form.html", form=form, form_name="Register a Client App")

@auth.route("/oauth/clients", methods = ["GET"])
@login_required
def get_oauth_clients():
    clients = current_user.get_oauth2_clients()
    return render_template("show_clients.html",clients=clients)


@auth.route("/oauth/authorize", methods = ["GET", "POST"])
@login_required
def oauth_authorize():
    user = current_user._get_current_object()
    form = OAuthConfirm()
    if request.method == 'GET':
        try:
            grant = authorization.validate_consent_request(end_user=user)
        except OAuth2Error as error:
            return error.error
        return render_template('authorize.html', form=form, user=user, grant=grant)
    if form.validate_on_submit():
        grant_user = user
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)

@auth.route('/oauth/token', methods=['POST'])
@csrf.exempt
def issue_token():
    return authorization.create_token_response()


@auth.route('/oauth/revoke', methods=['POST'])
@csrf.exempt
def revoke_token():
    return authorization.create_endpoint_response('revocation')

@auth.route('/oauth/delete/<client_id>', methods=["GET"])
@login_required
def delete_client(client_id):
    current_user.delete_oauth2_client()
    return redirect(url_for("auth.get_oauth_clients"))

@auth.route('/oauth', methods=["GET"])
@login_required
def get_code():
    code = request.args.get("code")
    client = get_oauth2_client_from_code(code)
    return render_template("oauth_code.html",code=code,client=client)


def get_username_from_token(token):
    s = Serializer(current_app.config["SECRET_KEY"])
    try:
        data = s.loads(token)
    except:
        raise Exception("Token is invalid.")
    return data.get("username")


def generate_confirmation_token(username, expiration=300):
    s = Serializer(current_app.config["SECRET_KEY"], expiration)
    return s.dumps({"username": username})


email_argument = {
    "confirmation": {"subject": "Confirm your Account", "template": "/email/confirm"},
    "oauth_confirmation": {"subject": "Allow access", "template": "/email/confirm_oauth"},
    "password_reset": {"subject": "Password reset", "template": "/email/reset"},
}


def send_email_token(context, username):
    user = User.query.filter_by(username=username).first_or_404()
    token = generate_confirmation_token(username)
    send_email(
        user.email,
        email_argument[context]["subject"],
        email_argument[context]["template"],
        username=username,
        token=token,
    )
