import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from hub import app, db, bcrypt
from hub.forms import RegistrationForm, LoginForm, UpdateAccountForm, JobForm
from hub.models import User, Job, Worker
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
@app.route("/home")
def home():
    jobs = Job.query.all()
    return render_template("home.html", jobs=jobs)

@app.route("/about")
def about():
    return render_template("about.html", title='About')

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template("register.html", title='Register', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Logged in as {form.username.data}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template("login.html", title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return (redirect(url_for('home')))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    i.save(picture_path)
    return picture_fn


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route("/job/new", methods=['GET', 'POST'])
@login_required
def new_job():
    form = JobForm()
    if form.validate_on_submit():
        job = Job(title=form.title.data, comment=form.comment.data, code='job.gcode', color='Black', material='PLA', qty=1, status='Queue', user=current_user)
        db.session.add(job)
        db.session.commit()
        flash('Job has been added to the queue.', 'success')
        return redirect(url_for('new_job'))
    return render_template('create_job.html', title = 'New Job', form=form, legend='Create Job')


@app.route("/job/<int:job_id>")
def job(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job.html', title=job.title, job=job)

@app.route("/job/<int:job_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.user != current_user:
        abort(403)
    form = JobForm()
    if form.validate_on_submit():
        job.title = form.title.data
        job.comment = form.comment.data
        db.session.commit()
        flash('Your job has been edited.', 'success')
        return redirect(url_for('job', job_id=job.id))
    elif request.method == "GET":
        form.title.data = job.title
        form.comment.data = job.comment
    return render_template('create_job.html', title = 'Update Job', form=form, legend='Edit Job')


@app.route("/job/<int:job_id>/delete", methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.user != current_user:
        abort(403)
    db.session.delete(job)
    db.session.commit()
    flash('Your job has been deleted.', 'info')
    return redirect(url_for('home'))