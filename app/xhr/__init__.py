from flask import Blueprint
import os

xhr = Blueprint("xhr", __name__)
from app.xhr import views
