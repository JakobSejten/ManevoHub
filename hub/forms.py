import os
from hub import app
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    TextAreaField,
    SelectField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    Email,
    EqualTo,
    ValidationError,
    NoneOf,
)
from hub.models import User, Job


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=20)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "That username is taken. Please choose a different one."
            )

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError("That email is taken. Please use a different one.")


class LoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=20)]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")


class UpdateAccountForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=20)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    picture = FileField(
        "Update Profile Picture", validators=[FileAllowed(["jpg", "jpeg", "png"])]
    )
    submit = SubmitField("Update")

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    "That username is taken. Please choose a different one."
                )

    def validate_email(self, email):
        if email.data != current_user.email:
            email = User.query.filter_by(email=email.data).first()
            if email:
                raise ValidationError(
                    "That email is taken. Please use a different one."
                )


colorChoices = ["Black", "Red", "Green", "Blue"]
materialChoices = ["PLA", "ABS", "PETG"]


def uploaded_files():
    gcode_path = os.path.join(app.root_path, "static/gcode_files")
    used_files = os.listdir(gcode_path)
    return used_files


class JobForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    jobfile = FileField("Upload GCode File", validators=[FileAllowed(["gcode"])])
    color = SelectField(
        "Select Color", choices=colorChoices, validators=[DataRequired()]
    )
    material = SelectField(
        "Select Material", choices=materialChoices, validators=[DataRequired()]
    )
    comment = TextAreaField("Comment")
    qty = SelectField(
        "Select Quantity",
        validators=[DataRequired()],
        choices=range(1, 1000),
        coerce=int,
    )
    ignore_filename = BooleanField(
        "Override currently uploaded file with same filename.", default=False
    )
    submit = SubmitField("Submit")

    def validate_jobfile(self, jobfile):
        if self.jobfile.data is None:
            raise ValidationError("Choose a file to upload.")
        elif jobfile.data.filename in uploaded_files():
            if not self.ignore_filename.data:
                ignore_filename_message = "A file with this name is already in the queue. Do you wish to replace the existing file? This will also replace the file for jobs that have previously been queued."
                raise ValidationError(ignore_filename_message)


class WorkerForm(FlaskForm):
    name = StringField("Printer Name", validators=[DataRequired()])
    color = SelectField(
        "Select Color", choices=colorChoices, validators=[DataRequired()]
    )
    material = SelectField(
        "Select Material", choices=materialChoices, validators=[DataRequired()]
    )
    submit = SubmitField("Submit")
