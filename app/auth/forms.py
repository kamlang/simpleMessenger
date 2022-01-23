from flask_wtf import FlaskForm
from wtforms import *

class loginForm(FlaskForm):
    username=StringField('Username', [validators.InputRequired("This field can not be empty")])
    password=PasswordField('Password',
                             [validators.InputRequired("This field can not be empty")])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField("Submit")

class registerForm(FlaskForm):
    username=StringField('Username', [validators.InputRequired("This field can not be empty"),validators.Length(1,24) ])
    email=StringField('Email', [validators.InputRequired("This field can not be empty"),validators.Email("Please enter a valid email address.")])
    password = PasswordField('Password', [validators.InputRequired(), validators.EqualTo('confirm', message='Passwords must match')])
    confirm  = PasswordField('Confirm Password')
    submit = SubmitField("Submit")
