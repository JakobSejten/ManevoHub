from datetime import datetime
from hub import db

class User(db.Model):
    userID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    jobs = db.relationship('jobs', backref='user')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class jobs(db.Model):
    jobID = db.Column(db.Integer, primary_key=True) # Primary key for job
    uploadID = db.Column(db.Integer, unique=False) # ID for uploads - used for quantity settings
    groupID = db.Column(db.Integer, unique=False) # ID to group different jobs
    queuePosition = db.Column(db.Integer, unique=True) # Number used to sort job queue positions
    name = db.Column(db.String, nullable=False) # Arbitrary name of the job given by user
    code = db.Column(db.String, nullable=False) # Filename of uploaded GCode
    color = db.Column(db.String, nullable=False) # Color of filament used
    material = db.Column(db.String, nullable=False) # Filament material
    datePosted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # Date job is posted
    datePrintStart = db.Column(db.DateTime, nullable=True) # Date job is initiated
    datePrintFinish = db.Column(db.DateTime, nullable=True) # Date job is completed
    qty = db.Column(db.Integer, nullable=False) # Job multiplier - this column will be deleted in later versions
    comment = db.Column(db.Text, nullable=True) # Comment by user regarding job
    status = db.Column(db.String, nullable=False) # Status of print - In queue, printed, completed, ect.
    printerID = db.Column(db.Integer, db.ForeignKey('worker.workerID')) # ID used to assign job or refer job to the used printer
    userID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False) # ID used to assign job or refer job to the used printer

    def __repr__(self):
        return "jobs({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(self.jobID, self.uploadID,
                                                                                     self.groupID, self.name, self.code,
                                                                                     self.color, self.material,
                                                                                     self.datePosted,
                                                                                     self.datePrintStart,
                                                                                     self.datePrintFinish, self.qty,
                                                                                     self.comment, self.status,
                                                                                     self.printerID)

class Worker(db.Model):
    workerID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    filamentColor = db.Column(db.String, nullable=False)
    filamentMaterial = db.Column(db.String, nullable=False)
    # status = db.Column(db.String, nullable=False)
    assignedJobs = db.relationship('jobs', backref='worker')

    def __repr__(self):
        return "Worker({}, {}, {}, {})".format(self.workerID, self.name, self.filamentColor, self.filamentMaterial)
