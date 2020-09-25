from flask import render_template, url_for, flash, redirect
from hub import app
from hub.forms import RegistrationForm, LoginForm
from hub.models import User, jobs, Worker

jobs = [
    {
        'author': 'Jakob Sejten',
        'title': 'Print job 1',
        'code':'fil1.gcode',
        'date_posted': '25 Sep, 2020'
    },
    {
        'author': 'Åge Mogensen',
        'title': 'Print job 2',
        'code':'fil2.gcode',
        'date_posted': '26 Sep, 2020'
    }
]

@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", jobs=jobs)

@app.route("/about")
def about():
    return render_template("about.html", title='About')

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))
    else:
        return render_template("register.html", title='Register', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'admin' and form.password.data == 'admin':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template("login.html", title='Login', form=form)