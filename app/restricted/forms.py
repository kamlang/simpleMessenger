from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField

class editUserForm(FlaskForm):
    role = SelectField("Role")
    submit = SubmitField("Submit")
