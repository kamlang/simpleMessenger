from flask import render_template, request, jsonify
from app.main import main
from app.models import db
from werkzeug.exceptions import HTTPException

@main.app_errorhandler(HTTPException)
def handle_exception(e):
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
