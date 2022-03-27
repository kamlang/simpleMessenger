from flask import Blueprint
import os

sse = Blueprint("sse", __name__)
from app.sse import views
