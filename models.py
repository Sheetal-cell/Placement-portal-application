from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))
    approved = db.Column(db.Boolean, default=False)

class CompanyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    company_name = db.Column(db.String(150))
    hr_contact = db.Column(db.String(50))
    website = db.Column(db.String(150))
    approval_status = db.Column(db.String(20), default="Pending")

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    roll_number = db.Column(db.String(50))
    course = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    resume_path = db.Column(db.String(200))

class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'))
    job_title = db.Column(db.String(150))
    job_description = db.Column(db.Text)
    eligibility = db.Column(db.String(200))
    deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'))
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'))
    status = db.Column(db.String(20), default="Applied")
    application_date = db.Column(db.DateTime, default=datetime.utcnow)

    drive = db.relationship('PlacementDrive', backref='applications')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='unique_application'),
    )