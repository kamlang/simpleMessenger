from flask import render_template, request, jsonify
from app.main import main
from app.models import db
from werkzeug.exceptions import HTTPException

@main.app_errorhandler(HTTPException)
def handle_exception(e):
    if "api" in request.blueprints:
        error_message = {
        "code": e.code,
        "name": e.name,
        "description": e.description,
        }
        return jsonify(error_message), e.code
    else:
        return render_template("error.html",error = e), e.code
