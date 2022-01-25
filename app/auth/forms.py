from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length,InputRequired

class loginForm(FlaskForm):
    username=StringField('Username',validators=[InputRequired(message="This field can not be empty")])
    password=PasswordField('Password',
                            validators= [InputRequired(message="This field can not be empty")])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField("Submit")

class registerForm(FlaskForm):
    username=StringField('Username',validators=[InputRequired(message="This field can not be empty"),Length(1,24) ])
    email=StringField('Email', validators=[InputRequired(message="This field can not be empty"),Email("Please enter a valid email address.")])
    password = PasswordField('Password', validators=[InputRequired(message="This field can not be empty"), EqualTo('confirm', message='Passwords must match')])
    confirm  = PasswordField('Confirm Password')
    submit = SubmitField("Submit")
