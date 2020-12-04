import os
import secrets
from datetime import datetime
from PIL import Image
from flask import (
    render_template,
    url_for,
    flash,
    redirect,
    request,
    abort,
    send_from_directory,
)
from hub import app, db, bcrypt
from hub.forms import (
    RegistrationForm,
    LoginForm,
    UpdateAccountForm,
    JobForm,
    WorkerForm,
)
from hub.models import User, Job, Worker
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/jobs/queue")
def home():
    jobs = Job.query.filter_by(status="Queue").order_by(Job.queuePosition)
    return render_template("home.html", jobs=jobs, title="Queue")


@app.route("/jobs/current")
def jobs_current():
    jobs = Job.query.filter_by(status="Printing").order_by(Job.datePrintStart.desc())
    return render_template("home.html", jobs=jobs, title="Current Jobs")


@app.route("/jobs/completed")
def jobs_completed():
    jobs = Job.query.filter_by(status="Completed").order_by(Job.datePrintFinish.desc())
    return render_template("home.html", jobs=jobs, title="Completed Jobs")


@app.route("/about")
def about():
    return render_template("about.html", title="About")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash(f"Account created for {form.username.data}!", "success")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            flash(f"Logged in as {form.username.data}!", "success")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login unsuccessful. Please check username and password.", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, "static/profile_pics", picture_fn)

    output_size = (125, 125)
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
        flash("Your account has been updated!", "success")
        return redirect(url_for("account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for("static", filename="profile_pics/" + current_user.image_file)
    return render_template(
        "account.html", title="Account", image_file=image_file, form=form
    )


def save_gcode(form_gcode):
    gcode_fn = form_gcode.filename
    gcode_path = os.path.join(app.root_path, "static/gcode_files", gcode_fn)
    form_gcode.save(gcode_path)
    return gcode_fn


def remove_old_gcode():

    gcode_path = os.path.join(app.root_path, "static/gcode_files")

    good_files = [
        r.code
        for r in Job.query.filter(Job.status.in_(["Queue", "Printing"])).distinct()
    ]
    all_files = os.listdir(gcode_path)

    for file in all_files:
        if file not in good_files:
            os.remove(os.path.join(gcode_path, file))


@app.route("/job/new", methods=["GET", "POST"])
@login_required
def new_job():
    random_hex = secrets.token_hex(100)
    form = JobForm()
    if form.validate_on_submit():
        job = Job(
            title=form.title.data,
            comment=form.comment.data,
            code=save_gcode(form.jobfile.data),
            color=form.color.data,
            material=form.material.data,
            qty=form.qty.data,
            status="Queue",
            user=current_user,
            uploadID=random_hex,
            queuePosition=int(len(Job.query.filter_by(status="Queue").all())) + 1,
        )

        db.session.add(job)
        db.session.commit()
        flash("Job has been added to the queue.", "success")
        return redirect(url_for("new_job"))
    return render_template(
        "create_job.html", title="Create Job", form=form, legend="Create Job"
    )


@app.route("/job/<int:job_id>")
def job(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template("job.html", title="Edit " + job.title, job=job)


@app.route("/job/<int:job_id>/edit", methods=["GET", "POST"])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.user != current_user:
        abort(403)
    form = JobForm()
    if form.validate_on_submit():
        job.title = form.title.data
        job.comment = form.comment.data
        job.color = form.color.data
        job.material = form.material.data
        job.jobfile = form.jobfile.data
        job.qty = form.qty.data
        db.session.commit()
        flash("Your job has been edited.", "success")
        return redirect(url_for("job", job_id=job.id))
    elif request.method == "GET":
        form.title.data = job.title
        form.comment.data = job.comment
        form.color.data = job.color
        form.material.data = job.material
        form.jobfile.data = job.code
    return render_template(
        "create_job.html", title="Update Job", form=form, legend="Edit Job"
    )


@app.route("/job/<int:job_id>/delete", methods=["POST"])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.user != current_user:
        abort(403)
    qp = job.queuePosition
    for j in Job.query.filter(Job.queuePosition > qp).all():
        j.queuePosition = j.queuePosition - 1
    db.session.delete(job)
    db.session.commit()
    remove_old_gcode()
    flash("Your job has been deleted.", "info")
    return redirect(url_for("home"))


@app.route("/worker/new", methods=["GET", "POST"])
@login_required
def new_worker():
    form = WorkerForm()
    if form.validate_on_submit():
        worker = Worker(
            name=form.name.data,
            filamentColor=form.color.data,
            filamentMaterial=form.material.data,
            user=current_user,
        )
        db.session.add(worker)
        db.session.commit()
        flash("Worker has been created.", "success")
        return redirect(url_for("worker"))
    return render_template(
        "create_worker.html", form=form, title="Create Worker", legend="Create Worker"
    )


@app.route("/worker/<int:worker_id>/edit", methods=["GET", "POST"])
@login_required
def edit_worker(worker_id):
    form = WorkerForm()
    worker = Worker.query.get_or_404(worker_id)
    print(worker)
    if form.validate_on_submit():
        worker.name = form.name.data
        worker.filamentColor = form.color.data
        worker.filamentMaterial = form.material.data
        # worker.userID = current_user - FIX RELATIONSHIP CASCADES FOR THIS FEATURE
        db.session.commit()
        flash("Worker settings have been updated.", "success")
        return redirect(url_for("worker"))
    elif request.method == "GET":
        form.name.data = worker.name
        form.color.data = worker.filamentColor
        form.material.data = worker.filamentMaterial
    return render_template(
        "create_worker.html",
        form=form,
        title="Edit Worker Settings",
        legend="Edit Worker Settings",
    )


@app.route("/worker")
def worker():
    workers = Worker.query.all()
    jobs = Job.query.filter_by(status="Printing")
    return render_template("workers.html", workers=workers, title="Workers", jobs=jobs)


@app.route("/worker/<int:worker_id>/delete", methods=["GET", "POST"])
@login_required
def delete_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    db.session.delete(worker)
    db.session.commit()
    flash("Your worker has been deleted.", "info")
    return redirect(url_for("home"))


@app.route("/printer/getjob/<int:worker_id>")
def getjob(worker_id):
    # Get printer info for printer with given ID
    worker = Worker.query.get(worker_id)

    if worker != None:
        color = worker.filamentColor
        material = worker.filamentMaterial

        # Select first job that fulfills printer requirements
        job = (
            Job.query.filter_by(color=color, material=material, status="Queue")
            .order_by(Job.queuePosition)
            .first()
        )
        if job != None:

            if job.qty > 1:
                job.qty = job.qty - 1

                # Duplicate the job but with 'Printing' status
                printing_job = Job(
                    title=job.title,
                    comment=job.comment,
                    code=job.code,
                    color=job.color,
                    material=job.material,
                    qty=1,
                    status="Printing",
                    user=job.user,
                    uploadID=job.uploadID,
                    datePosted=job.datePosted,
                    datePrintStart=datetime.now(),
                    printerID=worker_id,
                )
                db.session.add(printing_job)
                worker.status = "Printing"
                db.session.commit()

            elif job.qty == 1:
                qp = job.queuePosition
                for j in Job.query.filter(Job.queuePosition > qp).all():
                    j.queuePosition = j.queuePosition - 1
                job.status = "Printing"
                job.datePrintStart = datetime.now()
                job.printerID = worker_id
                worker.status = "Printing"
                db.session.commit()

            filepath = os.path.join(app.root_path, "static/gcode_files")

            return send_from_directory(filepath, job.code, as_attachment=True)
        else:
            return "<h1>No Jobs For This Printer.</h1>"
    else:
        return "<h1>Printer Not Yet Configured, Contact Support.</h1>"


@app.route("/printer/completejob/<int:worker_id>")
def complete_job(worker_id):
    worker = Worker.query.get(worker_id)
    job = Job.query.filter_by(status="Printing", printerID=worker_id).first()

    if job != None:

        while job != None:
            job.status = "Completed"
            job.datePrintFinish = datetime.now()
            worker.status = "Available"
            db.session.commit()
            job = Job.query.filter_by(status="Printing", printerID=worker_id).first()

        worker.status = "Available"
        db.session.commit()

        remove_old_gcode()

        return "<h1> Print Completed </h1>"
    return "<h1> No jobs being printed </h1>"


@app.route("/queue_up/<int:job_id>")
def queue_up(job_id):

    jobs = Job.query.filter_by(status="Queue").order_by(Job.queuePosition).all()

    job1_index = jobs.index(Job.query.get_or_404(job_id))
    job2_index = job1_index - 1

    job1_id = jobs[job1_index].id
    job2_id = jobs[job2_index].id

    job1 = Job.query.get(job1_id)
    job2 = Job.query.get(job2_id)

    qp1 = job1.queuePosition
    qp2 = job2.queuePosition

    job1.queuePosition = qp2
    job2.queuePosition = qp1

    db.session.commit()

    return redirect(url_for("home"))


@app.route("/queue_down/<int:job_id>")
def queue_down(job_id):

    jobs = Job.query.filter_by(status="Queue").order_by(Job.queuePosition).all()

    job1_index = jobs.index(Job.query.get_or_404(job_id))
    job2_index = job1_index + 1

    job1_id = jobs[job1_index].id
    job2_id = jobs[job2_index].id

    job1 = Job.query.get(job1_id)
    job2 = Job.query.get(job2_id)

    qp1 = job1.queuePosition
    qp2 = job2.queuePosition

    job1.queuePosition = qp2
    job2.queuePosition = qp1

    db.session.commit()

    return redirect(url_for("home"))


@app.route("/queue_top/<int:job_id>")
def queue_top(job_id):

    jobs = Job.query.filter_by(status="Queue").order_by(Job.queuePosition).all()

    job1_index = jobs.index(Job.query.get_or_404(job_id))

    qp0 = jobs[0].queuePosition

    for i in range(job1_index):
        jobs[i].queuePosition = jobs[i].queuePosition + 1

    Job.query.get_or_404(job_id).queuePosition = qp0

    db.session.commit()

    return redirect(url_for("home"))


@app.route("/queue_bottom/<int:job_id>")
def queue_bottom(job_id):

    jobs = Job.query.filter_by(status="Queue").order_by(Job.queuePosition).all()

    job1_index = jobs.index(Job.query.get_or_404(job_id))

    qp0 = jobs[len(jobs) - 1].queuePosition

    for i in range(job1_index, len(jobs)):
        jobs[i].queuePosition = jobs[i].queuePosition - 1

    Job.query.get_or_404(job_id).queuePosition = qp0

    db.session.commit()

    return redirect(url_for("home"))
