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


class editUser(FlaskForm):
    about_me = TextAreaField(
        "About me",
        validators=[
            Length(0, 140, message="Description should be shorter than 140 chars.")
        ],
        render_kw={"rows": 4, "cols": 30},
    )
    avatar = FileField("", validators=[FileAllowed(["jpg", "png"], "Images only!")])
    submit = SubmitField("Submit")


class sendReply(FlaskForm):
    content = TextAreaField(
        "",
        validators=[
            InputRequired(message="This field can not be empty"),
            Length(0, 280, message="Keep it short."),
        ],
        render_kw={"rows": 2, "cols": 45},
    )
    submit = SubmitField("Send")


class createConversation(FlaskForm):
    usernames = StringField(
        "Username(s) (if many have to be separated with a space.)",
        validators=[
            InputRequired(message="This field can not be empty"),
            Regexp("^[0-9A-Za-z_\s]+$", message="Special characters are not allowed."),
        ],
    )
    content = TextAreaField(
        "",
        validators=[
            InputRequired(message="This field can not be empty"),
            Length(0, 280, message="Keep it short."),
        ],
        render_kw={"rows": 2, "cols": 45},
    )
    submit = SubmitField("Submit")

    def validate_usernames(self, usernames):
        for username in str(usernames.data).split():
            user = User.query.filter_by(username=username).first()
            if user is None:
                raise ValidationError("Username {} do not exists.".format(username))


class addUserConversation(FlaskForm):
    usernames = StringField(
        "",
        validators=[
            InputRequired(message="This field can not be empty"),
            Regexp("^[0-9A-Za-z_\s]+$", message="Special characters are not allowed."),
        ],
    )
    submit = SubmitField("Add user(s)")

    def validate_usernames(self, usernames):
        for username in str(usernames.data).split():
            user = User.query.filter_by(username=username).first()
            if user is None:
                raise ValidationError("Username {} do not exists.".format(username))
