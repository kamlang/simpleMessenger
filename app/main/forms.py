from flask_wtf import FlaskForm
from wtforms import *


class loginForm(FlaskForm):
    username=StringField('username', [validators.InputRequired("This field can not be empty")])
    password=PasswordField('Enter Password',
                             [validators.InputRequired("This field can not be empty")])
    submit = SubmitField("Submit")

class registerForm(FlaskForm):
    username=StringField('username', [validators.InputRequired("This field can not be empty")])
    email=StringField('email', [validators.InputRequired("This field can not be empty"),validators.Email("Please enter a valid email address.")])
    password = PasswordField('New Password', [validators.InputRequired(), validators.EqualTo('confirm', message='Passwords must match')])
    confirm  = PasswordField('Repeat Password')
    submit = SubmitField("Submit")

class editUserForm(FlaskForm):
    role= SelectField(u'Role')
    submit = SubmitField("Submit")
