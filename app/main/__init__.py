from flask import Blueprint
import os

templates_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
main = Blueprint("main", __name__, template_folder=templates_folder, static_folder = "static")
from app.main import views, errors
