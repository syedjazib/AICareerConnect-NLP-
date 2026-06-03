from flask import Flask, render_template, request, redirect, session, send_file
from pymongo import MongoClient
import os
from collections import Counter
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

from nlp_utils import (
    extract_text_from_pdf,
    extract_skills,
    match_jobs
)

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MongoDB
client = MongoClient("mongodb+srv://syedjazib456:12345@syedcluster.3llnx.mongodb.net/resume_db")
db = client["resume_db"]

users = db["users"]
jobs_collection = db["jobs"]
resumes_collection = db["resumes"]
# ---------------- APPLICATIONS COLLECTION ----------------
applications = db["applications"]

# ---------------- HOME ----------------
@app.route('/')
def index():
    return render_template('index.html')



@app.route('/register', methods=['GET', 'POST'])
def register():

    # STEP 1: Show form
    if request.method == 'GET':
        role = request.args.get('role', 'employee')
        return render_template('register.html', role=role)

    # STEP 2: Handle submission
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    if not role:
        role = 'employee'

    company_name = request.form.get('company_name', '')

    # Check existing user
    existing_user = users.find_one({"email": email})

    if existing_user:
        return "Email already registered"

    # Insert user
    users.insert_one({
        "name": name,
        "email": email,
        "password": password,
        "role": role,
        "company_name": company_name,
        "profile_completed": False,
        "created_at": datetime.now()
    })

    return redirect('/login')
# ---------------- UPLOAD RESUME ----------------
@app.route('/upload', methods=['POST'])
def upload_resume():

    if 'resume' not in request.files:
        return "No file uploaded"

    file = request.files['resume']

    if file.filename == '':
        return "No selected file"

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    resume_text = extract_text_from_pdf(filepath)

    extracted_skills = extract_skills(resume_text, jobs_collection)

    jobs = list(jobs_collection.find())

    results = match_jobs(resume_text, jobs, jobs_collection)

    # SAVE SESSION
    session["skills"] = extracted_skills
    session["results"] = results

    # SAVE TO DB (RESUME LOGS)
    resumes_collection.insert_one({
        "username": session.get("user", "guest"),
        "skills": extracted_skills,
        "results": results,
        "created_at": datetime.now()
    })

    return render_template("result.html",
                           skills=extracted_skills,
                           results=results)

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    # If already logged in, go to dashboard
    if 'user' in session:
        return redirect('/dashboard')

    # Show login page
    if request.method == 'GET':
        return render_template('login.html')

    # Get form data (email-based login)
    email = request.form.get('email')
    password = request.form.get('password')

    # Find user in MongoDB
    user = users.find_one({
        "email": email,
        "password": password
    })

    # If user exists
    if user:
        # Store session
        session['user'] = user['name']          # Display name
        session['email'] = user['email']        # Unique identity
        
        user_role = user.get("role")
        session['role'] = user_role if user_role else "employee"

        # Redirect based on role
        return redirect('/dashboard')

    return "Invalid Email or Password"


@app.route('/analyze_resume')
def analyze_resume():
    return render_template('analyze_resume.html')

# ---------------- DASHBOARD ROUTER ----------------
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/login')

    role = session.get('role')

    # Admin
    if role == 'admin':
        return redirect('/admin_dashboard')

    # Employer
    elif role == 'employer':
        return redirect('/employer_dashboard')

    # Employee (default)
    return redirect('/employee_dashboard')

# ---------------- EMPLOYEE DASHBOARD ----------------
@app.route('/employee_dashboard')
def employee_dashboard():

    if 'user' not in session or session.get('role') != 'employee':
        return redirect('/login')

    return render_template(
        'employee_dashboard.html',
        user=session['user']
    )
# ---------------- EMPLOYER DASHBOARD ----------------
@app.route('/employer_dashboard')
def employer_dashboard():

    if 'user' not in session or session.get('role') != 'employer':
        return redirect('/login')

    return render_template(
        'employer_dashboard.html',
        user=session['user']
    )

# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin_dashboard')
def admin_dashboard():

    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/login')

    total_jobs = jobs_collection.count_documents({})
    total_users = users.count_documents({})
    total_resumes = resumes_collection.count_documents({})

    # top skills
    all_jobs = jobs_collection.find()
    skills_list = []

    for job in all_jobs:
        skills_list.extend(job.get("skills", []))

    top_skills = Counter(skills_list).most_common(5)

    # top jobs
    job_titles = [job["title"] for job in jobs_collection.find()]
    top_jobs = Counter(job_titles).most_common(3)

    return render_template("admin_dashboard.html",
                           total_jobs=total_jobs,
                           total_users=total_users,
                           total_resumes=total_resumes,
                           top_skills=top_skills,
                           top_jobs=top_jobs)


# ---------------- ADD JOB ----------------
@app.route('/add_job', methods=['GET', 'POST'])
def add_job():

    if 'user' not in session or session.get('role') != 'employer':
        return redirect('/login')

    if request.method == 'GET':
        return render_template('add_jobs.html')

    title = request.form['title'].strip()

    skills = [
        skill.strip().lower()
        for skill in request.form['skills'].split(',')
        if skill.strip()
    ]

    jobs_collection.insert_one({
        "title": title,
        "skills": skills
    })

    return redirect('/admin_dashboard')


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------- PDF REPORT ----------------
def generate_pdf(skills, results):

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("AI Resume Report", styles['Title']))
    content.append(Spacer(1, 12))

    content.append(Paragraph("Skills:", styles['Heading2']))
    content.append(Paragraph(", ".join(skills), styles['Normal']))
    content.append(Spacer(1, 12))

    for job in results:
        text = f"""
        Job: {job['title']}  
        Match: {job['match']}%  
        Missing: {', '.join(job['missing_skills'])}
        """
        content.append(Paragraph(text, styles['Normal']))
        content.append(Spacer(1, 10))

    pdf.build(content)
    buffer.seek(0)

    return buffer


# ---------------- DOWNLOAD REPORT ----------------
@app.route('/download_report')
def download_report():

    if 'user' not in session:
        return redirect('/login')

    skills = session.get("skills", [])
    results = session.get("results", [])

    pdf_buffer = generate_pdf(skills, results)

    return send_file(pdf_buffer,
                     as_attachment=True,
                     download_name="AI_Resume_Report.pdf",
                     mimetype='application/pdf')

# =========================
# UPDATE APPLY JOB ROUTE (Prevent Duplicate Apply)
# =========================
@app.route('/apply_job/<job_title>')
def apply_job(job_title):

    # 🔐 Login check
    if 'user' not in session:
        return redirect('/login')

    email = session.get('email')
    role = session.get('role')

    # ❌ Only employees
    if role != 'employee':
        return "Only employees can apply for jobs"

    # 🚫 Check duplicate application
    existing_application = resumes_collection.find_one({
        "email": email,
        "job_title": job_title,
        "status": "applied"
    })

    if existing_application:
        return redirect('/matched_jobs')

    # 💾 Save new application
    resumes_collection.insert_one({
        "email": email,
        "job_title": job_title,
        "status": "applied",
        "created_at": datetime.now()
    })

    return redirect('/my_applications')

@app.route('/save_job/<job_title>')
def save_job(job_title):

    # 🔐 Login check
    if 'user' not in session:
        return redirect('/login')

    email = session.get('email')
    role = session.get('role')

    # ❌ Only employees can save jobs
    if role != 'employee':
        return "Only employees can save jobs"

    # 💾 Save job bookmark
    resumes_collection.insert_one({
        "email": email,
        "job_title": job_title,
        "status": "saved",
        "created_at": datetime.now()
    })

    return redirect('/employee_dashboard')

# =========================
# UPDATED MY APPLICATIONS ROUTE
# =========================
@app.route('/my_applications')
def my_applications():

    # 🔐 Login Required
    if 'user' not in session:
        return redirect('/login')

    # 👤 Only employee
    if session.get('role') != 'employee':
        return "Access Denied"

    email = session.get('email')

    # 📄 Fetch applied jobs from resumes_collection
    apps = list(
        resumes_collection.find({
            "email": email,
            "status": "applied"
        }).sort("created_at", -1)
    )

    # 🚫 No applications yet
    if not apps:
        return render_template(
            "my_applications.html",
            applications=[],
            no_applications=True
        )

    # ✅ Pass applications
    return render_template(
        "my_applications.html",
        applications=apps,
        no_applications=False
    )
@app.route('/saved_jobs')
def saved_jobs():

    if 'user' not in session:
        return redirect('/login')

    email = session.get('email')

    saved = list(resumes_collection.find({
        "email": email,
        "status": "saved"
    }))

    return render_template("saved_jobs.html", saved=saved)
    return render_template("my_applications.html", applications=applications)

@app.route('/view_applicants')
def view_applicants():

    if 'user' not in session:
        return redirect('/login')

    if session.get('role') != 'employer':
        return "Unauthorized"

    applicants = list(resumes_collection.find({
        "status": "applied"
    }))

    return render_template("view_applicants.html", applicants=applicants)
@app.route('/recent_applications')
def recent_applications():

    if 'user' not in session:
        return redirect('/login')

    if session.get('role') != 'employer':
        return "Unauthorized"

    recent = list(resumes_collection.find(
        {"status": "applied"}
    ).sort("created_at", -1).limit(10))

    return render_template("recent_applications.html", recent=recent)
# ---------------- RESUME LOGS (EMPLOYER / ADMIN) ----------------
@app.route('/resume_logs')
def resume_logs():

    # 🔐 Security Check
    if 'user' not in session:
        return redirect('/login')

    # Only employer/admin can access
    if session.get('role') not in ['employer', 'admin']:
        return "Access Denied"

    # 📄 Fetch all uploaded resumes (latest first)
    logs = list(
        resumes_collection.find().sort("created_at", -1)
    )

    # 📊 Dashboard Summary
    total_resumes = len(logs)

    # Render page
    return render_template(
        'resume_logs.html',
        logs=logs,
        total_resumes=total_resumes
    )

# =========================
# UPDATE YOUR matched_jobs ROUTE
# =========================
@app.route('/matched_jobs')
def matched_jobs():

    # 🔐 LOGIN CHECK
    if 'user' not in session:
        return redirect('/login')

    # 👤 ONLY EMPLOYEE ACCESS
    if session.get('role') != 'employee':
        return "Access Denied"

    user_email = session.get("email")

    # 📄 Get latest uploaded resume
    latest_resume = resumes_collection.find_one(
        {
            "username": session.get("user")
        },
        sort=[("created_at", -1)]
    )

    # 🚫 No resume
    if not latest_resume:
        return render_template(
            "matched_jobs.html",
            results=[],
            skills=[],
            applied_jobs=[],
            no_resume=True
        )

    # 📊 Resume Data
    results = latest_resume.get("results", [])
    skills = latest_resume.get("skills", [])

    # ✅ Fetch already applied jobs
    applied_records = resumes_collection.find({
        "email": user_email,
        "status": "applied"
    })

    applied_jobs = [job["job_title"] for job in applied_records]

    return render_template(
        "matched_jobs.html",
        results=results,
        skills=skills,
        applied_jobs=applied_jobs,
        no_resume=False
    )
if __name__ == "__main__":
    app.run(debug=True)