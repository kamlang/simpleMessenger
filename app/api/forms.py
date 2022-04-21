from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, StringField
from wtforms.validators import InputRequired, Length

class OauthClientForm(FlaskForm):
    client_name = StringField("Client Name",validators=[
        InputRequired(message="This field can not be empty."), 
        Length(4, 24, message="Client name length must be between 4 and 24 charcters"),])
    allowed_scope = SelectField("Scope",choices=[("readonly", "Read Only"),("modify", "Read and Write")])
    submit = SubmitField("Submit")

