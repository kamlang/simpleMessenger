from flask import Blueprint
import os

templates_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
auth = Blueprint("auth", __name__, template_folder=templates_folder)
from . import views
