from flask import Blueprint
import os

from .build_doc import build_api_doc
api_doc_list = build_api_doc()
templates_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
api = Blueprint("api", __name__, template_folder=templates_folder)
from app.api import views
