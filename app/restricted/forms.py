from flask_wtf import FlaskForm
from wtforms import *

class editUserForm(FlaskForm):
    role= SelectField(u'Role')
    submit = SubmitField("Submit")
