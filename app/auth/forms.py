from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    FileField,
    TextAreaField,
)
from wtforms.validators import (
    ValidationError,
    DataRequired,
    Email,
    EqualTo,
    Length,
    InputRequired,
    Regexp,
)
from flask_wtf.file import FileField, FileRequired, FileAllowed
from app.models import User


class login_form(FlaskForm):
    username = StringField(
        "Username", validators=[InputRequired(message="This field can not be empty")]
    )
    password = PasswordField(
        "Password", validators=[InputRequired(message="This field can not be empty")]
    )
    remember_me = BooleanField("Keep me logged in")
    submit = SubmitField("Submit")


class register_form(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            InputRequired(message="This field can not be empty"),
            Length(4, 24, message="Username must be at least 4 characters long."),
            Regexp("^[0-9A-Za-z_]+$", message="Special characters are not allowed."),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            InputRequired(message="This field can not be empty"),
            Email("Please enter a valid email address."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(message="This field can not be empty"),
            EqualTo("confirm", message="Passwords must match"),
        ],
    )
    confirm = PasswordField("Confirm Password")
    submit = SubmitField("Submit")
    
    """def validate_password(self,password):
        password_pattern = re.compile("^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$ %^&*-]).{8,}$")
        if not re.match(password_pattern,password.data):
            raise ValidationError("Please use a stronger password,\
            password must contains at least one uppercase letter,\
            one number, and one special character. It must be longer than 8 characters")"""


    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None: 
            raise ValidationError("Please use a different username.")


class password_reset_confirmation(FlaskForm):
    """  username = StringField(
        "Username",
        validators=[
            InputRequired(message="This field can not be empty"),
            Length(1, 48),
        ],
    )"""
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(message="This field can not be empty"),
            EqualTo("confirm", message="Passwords must match"),
        ],
    )
    confirm = PasswordField("Confirm Password")
    submit = SubmitField("Submit")

    """def validate_password(self,password):
        password_pattern = re.compile("^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$ %^&*-]).{8,}$")
        if not re.match(password_pattern,password.data):
            raise ValidationError("Please use a stronger password,\
            password must contains at least one uppercase letter,\
            one number, and one special character. It must be longer than 8 characters")"""




class confirm_username(
    FlaskForm
):  ##### After forgot password is pressed at login screen, asking for the username
    username = StringField(
        "Username",
        validators=[
            InputRequired(message="This field can not be empty"),
            Length(1, 48),
        ],
    )
    submit = SubmitField("Submit")
