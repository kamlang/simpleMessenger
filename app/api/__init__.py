from flask import Blueprint
import os

from .build_doc import build_api_doc
api_doc_list = build_api_doc()

api = Blueprint("api", __name__)
from app.api import views
