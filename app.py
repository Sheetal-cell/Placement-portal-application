from flask import Flask, render_template, redirect, url_for, request, flash
from config import Config
from extensions import db, login_manager
from models import User, CompanyProfile, StudentProfile, PlacementDrive, Application
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

# -------------------------
# Create Database Tables
# -------------------------
with app.app_context():
    db.create_all()

    # Create Admin if not exists
    if not User.query.filter_by(role="admin").first():
        admin = User(
            name="Admin",
            email="admin@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin",
            approved=True
        )
        db.session.add(admin)
        db.session.commit()


# -------------------------
# USER LOADER
# -------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------------
# HOME
# -------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            if user.role == "company" and not user.approved:
                flash("Company not approved yet")
                return redirect(url_for("login"))

            login_user(user)

            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user.role == "company":
                return redirect(url_for("company_dashboard"))
            else:
                return redirect(url_for("student_dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# -------------------------
# REGISTER STUDENT
# -------------------------
@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":

        # ✅ CHECK IF EMAIL ALREADY EXISTS
        existing_user = User.query.filter_by(
            email=request.form["email"]
        ).first()

        if existing_user:
            flash("Email already registered. Please login.")
            return redirect(url_for("register_student"))

        # Create user
        user = User(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            role="student",
            approved=True
        )
        db.session.add(user)
        db.session.commit()

        # Create student profile
        student = StudentProfile(
            user_id=user.id,
            course=request.form["course"],
            cgpa=request.form["cgpa"]
        )
        db.session.add(student)
        db.session.commit()

        flash("Student registered successfully")
        return redirect(url_for("login"))

    return render_template("register_student.html")


@app.route("/register/company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":

        # 🔎 CHECK IF EMAIL ALREADY EXISTS
        existing_user = User.query.filter_by(
            email=request.form["email"]
        ).first()

        if existing_user:
            flash("Email already registered. Please login.")
            return redirect(url_for("register_company"))

        user = User(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            role="company",
            approved=False
        )
        db.session.add(user)
        db.session.commit()

        company = CompanyProfile(
            user_id=user.id,
            company_name=request.form["company_name"],
            hr_contact=request.form["hr_contact"],
            website=request.form["website"],
            approval_status="Pending"
        )
        db.session.add(company)
        db.session.commit()

        flash("Company registered. Await admin approval.")
        return redirect(url_for("login"))

    return render_template("register_company.html")


# -------------------------
# ADMIN DASHBOARD
# -------------------------
@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    students = User.query.filter_by(role="student").count()
    companies = User.query.filter_by(role="company").count()
    drives = PlacementDrive.query.count()
    applications = Application.query.count()

    pending_companies = User.query.filter_by(
        role="company",
        approved=False
    ).all()

    pending_drives = PlacementDrive.query.filter_by(
        status="Pending"
    ).all()

    return render_template("admin_dashboard.html",
                           students=students,
                           companies=companies,
                           drives=drives,
                           applications=applications,
                           pending_companies=pending_companies,
                           pending_drives=pending_drives)
# -------------------------
# APPROVE COMPANY
# -------------------------
@app.route("/approve_company/<int:user_id>")
@login_required
def approve_company(user_id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    user = User.query.get(user_id)
    user.approved = True

    company = CompanyProfile.query.filter_by(user_id=user.id).first()
    company.approval_status = "Approved"

    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/approve_drive/<int:drive_id>")
@login_required
def approve_drive(drive_id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "Approved"
    db.session.commit()

    flash("Drive approved successfully.")
    return redirect(url_for("admin_dashboard"))

# -------------------------
# COMPANY DASHBOARD
# -------------------------
@app.route("/company")
@login_required
def company_dashboard():
    if current_user.role != "company":
        return redirect(url_for("index"))

    drives = PlacementDrive.query.filter_by(company_id=current_user.id).all()
    return render_template("company_dashboard.html", drives=drives)


# -------------------------
# CREATE DRIVE
# -------------------------
@app.route("/create_drive", methods=["GET", "POST"])
@login_required
def create_drive():
    if current_user.role != "company":
        return redirect(url_for("index"))

    if request.method == "POST":
        drive = PlacementDrive(
            company_id=current_user.id,
            job_title=request.form["job_title"],
            job_description=request.form["job_description"],
            eligibility=request.form["eligibility"],
            deadline=datetime.strptime(request.form["deadline"], "%Y-%m-%d"),
            status="Pending"
        )
        db.session.add(drive)
        db.session.commit()

        flash("Drive created. Await admin approval.")
        return redirect(url_for("company_dashboard"))

    return render_template("create_drive.html")


# -------------------------
# VIEW APPLICATIONS (COMPANY)
# -------------------------
@app.route("/view_applications/<int:drive_id>")
@login_required
def view_applications(drive_id):
    if current_user.role != "company":
        return redirect(url_for("index"))

    drive = PlacementDrive.query.get_or_404(drive_id)
    applications = Application.query.filter_by(drive_id=drive_id).all()

    return render_template("view_applications.html",
                           drive=drive,
                           applications=applications,
                           User=User,
                           StudentProfile=StudentProfile)


# -------------------------
# UPDATE APPLICATION STATUS
# -------------------------
@app.route("/update_status/<int:app_id>/<new_status>")
@login_required
def update_status(app_id, new_status):
    if current_user.role != "company":
        return redirect(url_for("index"))

    application = Application.query.get_or_404(app_id)
    application.status = new_status
    db.session.commit()

    return redirect(url_for("view_applications",
                            drive_id=application.drive_id))


# -------------------------
# STUDENT DASHBOARD
# -------------------------
@app.route("/student")
@login_required
def student_dashboard():
    if current_user.role != "student":
        return redirect(url_for("index"))

    drives = PlacementDrive.query.filter_by(status="Approved").all()
    applications = Application.query.filter_by(student_id=current_user.id).all()

    return render_template("student_dashboard.html",
                           drives=drives,
                           applications=applications)


# -------------------------
# APPLY FOR DRIVE
# -------------------------
@app.route("/apply/<int:drive_id>")
@login_required
def apply(drive_id):
    if current_user.role != "student":
        return redirect(url_for("index"))

    existing = Application.query.filter_by(
        student_id=current_user.id,
        drive_id=drive_id
    ).first()

    if existing:
        flash("Already applied for this drive")
        return redirect(url_for("student_dashboard"))

    application = Application(
        student_id=current_user.id,
        drive_id=drive_id,
        application_date=datetime.utcnow(),
        status="Applied"
    )
    db.session.add(application)
    db.session.commit()

    flash("Application submitted")
    return redirect(url_for("student_dashboard"))


# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)