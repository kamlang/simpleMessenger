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


@restricted.route("/showall")  ### Admin
@login_required
@admin_required
def showall():
    users = User.query.all()
    return render_template("showall.html", users=users)


@restricted.route("/edit/<username>", methods=["GET", "POST"])  ###Admin
@login_required
@admin_required
def edit(username):
    form = editUserForm()
    form.role.choices = getRolesList()
    if form.validate() == True:
        role = request.form["role"]
        user = User.query.filter_by(username=username).first()
        role = Role.query.filter_by(name=role).first()
        if user is not None:
            user.roles = [role]
            try:
                db.session.commit()
                flash(successMessage)
                return redirect(url_for("restricted.showall"))
            except Exception as e:
                db.session.rollback()
                flash("error in UPDATE operation")
                return redirect(url_for("restricted.showall"))
    return render_template("edit.html", form=form, user=username)


@restricted.route("/delete/<username>")  ###Admin
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
    return redirect(url_for("restricted.showall"))


def getRolesList():
    rolesList = []
    q = Role.query.all()
    for role in q:
        rolesList.append(role.name)
    return rolesList
