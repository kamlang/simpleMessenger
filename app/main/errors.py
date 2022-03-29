from flask import render_template, request, jsonify, abort
from app.main import main
from app.models import db, UnauthorizedOperation
from werkzeug.exceptions import HTTPException,InternalServerError

@main.app_errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, UnauthorizedOperation) or isinstance(e,InternalServerError):
        db.session.rollback()

    if isinstance(e, HTTPException):
    # If user is trying to access an api endpoint return json
        if "/api/" in request.path[:5]:
            error_message = {
            "code": e.code,
            "name": e.name,
            "description": e.description,
            }
            return jsonify(error_message), e.code
        else:
            return render_template("error.html",error = e), e.code
