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
import logging
from flask_login import login_user, current_user, logout_user, login_required

# from .. import login_manager
from functools import wraps
from app import db
from app.models import User, Role
from app.restricted.forms import editUserForm
from app.restricted import restricted

errorMessage = "An error happened!"
successMessage = "Operation succeed !"


def admin_required(f):
    @wraps(f)
    def is_admin(**args):
        if current_user.is_role(role="Admin"):
            return f(**args)
        abort(403)

    return is_admin


@restricted.route("/showall")
@login_required
@admin_required
def showall():
    all_users = User.query.all()
    return render_template("showall.html", users=all_users)


@restricted.route("/edit/<username>", methods=["GET", "POST"])  ###Admin
@login_required
@admin_required
def edit(username):
    form = editUserForm()
    form.role.choices = get_roles_list()
    if form.validate_on_submit():
        role = request.form["role"]
        user = User.query.filter_by(username=username).first()
        role = Role.query.filter_by(name=role).first()
        if user:
            user.roles = [role]
            try:
                db.session.commit()
                flash(successMessage)
                return redirect(url_for("restricted.showall"))
            except Exception as e:
                db.session.rollback()
                flash(errorMessage)
                return redirect(url_for("restricted.showall"))
    return render_template("edit.html", form=form, user=username)


@restricted.route("/delete/<username>") 
@login_required
@admin_required
def delete(username):
    user = User.query.filter_by(username=username).first()
    if user:
        try:
            db.session.delete(user)
            db.session.commit()
            flash(successMessage)
        except Exception as e:
            logging.debug(e)
            db.session.rollback()
            flash(errorMessage)
    return redirect(url_for("restricted.showall"))


def get_roles_list():
    roles_list = []
    existing_roles = Role.query.all()
    for role in existing_roles:
        roles_list.append(role.name)
    return roles_list
