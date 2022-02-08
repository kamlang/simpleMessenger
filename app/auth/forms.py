from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField,TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length,InputRequired, Regexp
from flask_wtf.file import FileField, FileRequired,FileAllowed
from ..models import User

class loginForm(FlaskForm):
    username=StringField('Username',validators=[InputRequired(message="This field can not be empty")])
    password=PasswordField('Password',
                            validators= [InputRequired(message="This field can not be empty")])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField("Submit")

class registerForm(FlaskForm):
    username=StringField('Username',validators=[InputRequired(message="This field can not be empty"),Length(4,24,message='Username must be at least 4 characters long.'),Regexp('^[0-9A-Za-z_]+$',message='Special characters are not allowed.') ])
    email=StringField('Email', validators=[InputRequired(message="This field can not be empty"),Email("Please enter a valid email address.")])
    password = PasswordField('Password', validators=[InputRequired(message="This field can not be empty"), EqualTo('confirm', message='Passwords must match')])
    confirm  = PasswordField('Confirm Password')
    submit = SubmitField("Submit")
    
    def validate_username(self,username):
        user=User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    
#    def validate_email(self,email):
#        user=User.query.filter_by(email=email.data).first()
#        if user is not None:
#            raise ValidationError('Please use a different email.')


class passwordReset(FlaskForm):
    username=StringField('Username',validators=[InputRequired(message="This field can not be empty"),Length(1,48) ])
    password = PasswordField('Password', validators=[InputRequired(message="This field can not be empty"), EqualTo('confirm', message='Passwords must match')])
    confirm  = PasswordField('Confirm Password')
    submit = SubmitField("Submit")

class usernameReset(FlaskForm):##### After forgot password is pressed at login screen, asking for the username
    username = StringField('Username',validators=[InputRequired(message="This field can not be empty"),Length(1,48) ])
    submit = SubmitField("Submit")

class editUser(FlaskForm):
    about_me = TextAreaField('About me',validators=[Length(0,140,message="Description should be shorter than 140 chars.")], render_kw={"rows": 4, "cols": 30})
    avatar = FileField('', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField("Submit")

class sendReply(FlaskForm):
    content= TextAreaField('',validators=[Length(0,280,message='Keep it short.')], render_kw={"rows": 2, "cols": 45})
    submit = SubmitField("Submit")

class sendTo(FlaskForm):
    recipient = StringField('To: ',validators=[InputRequired(message="This field can not be empty"),Length(4,24,message='Username must be at least 4 characters long.'),Regexp('^[0-9A-Za-z_]+$',message='Special characters are not allowed.') ])
    submit = SubmitField('Submit')
    def validate_recipient(self,recipient):
        user=User.query.filter_by(username=recipient.data).first()
        if user is None:
            raise ValidationError('This user do not exists.')
