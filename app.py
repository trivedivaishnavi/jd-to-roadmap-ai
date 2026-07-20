import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from collections import Counter
from huggingface_hub import InferenceClient
import markdown
import pdfplumber
from skills_data import COMMON_SKILLS

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-later-to-something-random'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

hf_client = InferenceClient(token=os.environ.get("HF_TOKEN"))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    jd_summary = db.Column(db.String(300))
    missing_skills = db.Column(db.String(500))
    roadmap = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def extract_skills(text):
    text_lower = text.lower()
    found_skills = []
    for skill in COMMON_SKILLS:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    return found_skills


def extract_skills_with_frequency(jd_texts):
    skill_counter = Counter()
    for text in jd_texts:
        if text.strip():
            found = extract_skills(text)
            skill_counter.update(found)
    return skill_counter


LANGUAGE_TO_SKILL = {
    "Python": "Python", "JavaScript": "JavaScript", "HTML": "HTML",
    "CSS": "CSS", "Java": "Java", "C++": "C++", "TypeScript": "JavaScript",
    "Jupyter Notebook": "Python"
}


def get_github_skills(username):
    detected = set()
    try:
        repos_url = f"https://api.github.com/users/{username}/repos"
        response = requests.get(repos_url, timeout=5)
        if response.status_code == 200:
            for repo in response.json():
                lang_url = f"https://api.github.com/repos/{username}/{repo['name']}/languages"
                lang_response = requests.get(lang_url, timeout=5)
                if lang_response.status_code == 200:
                    for lang in lang_response.json():
                        if lang in LANGUAGE_TO_SKILL:
                            detected.add(LANGUAGE_TO_SKILL[lang])
    except Exception as e:
        print(f"GitHub fetch error: {e}")
    return list(detected)


def get_pdf_text(file):
    try:
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text
    except Exception as e:
        print(f"Resume parsing error: {e}")
        return ""


def extract_skills_from_resume(file):
    text = get_pdf_text(file)
    return extract_skills(text) if text else []


def generate_roadmap(missing_skills, weeks_available=6):
    if not missing_skills:
        return "You already know all the required skills — no roadmap needed! Focus on polishing your GitHub projects and LinkedIn profile instead."

    skills_text = ", ".join(missing_skills)
    prompt = f"""A student is preparing for a job that requires these skills they don't yet have: {skills_text}.
Create a detailed {weeks_available}-week learning roadmap for them. For each week, include:
- Which specific skill(s) to focus on
- 2-3 concrete sub-topics to cover that week
- A suggestion of where to learn it (type of resource, e.g. official docs, a course, practice platform)

After the week-by-week plan, add a short section called "Personalized Recommendations" with:
- One specific tip to improve their LinkedIn profile for this type of role
- One specific tip to improve their GitHub profile for this type of role
- One piece of general advice for someone at this stage

Keep the tone encouraging and practical. Use clear headers and numbered lists."""

    try:
        response = hf_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/Llama-3.1-8B-Instruct",
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Roadmap generation is temporarily unavailable ({e}). Here are the skills to focus on in order: {skills_text}"


def generate_resume_suggestions(missing_keywords, resume_text):
    if not missing_keywords:
        return "Your resume already covers all the key terms from this job description — nice!"

    keywords_text = ", ".join(missing_keywords)
    prompt = f"""Here is a student's resume text:
{resume_text[:2000]}

The job description they're applying to mentions these keywords/skills that are missing from their resume: {keywords_text}.

Give honest, practical suggestions for how they could naturally incorporate these missing keywords into their resume. If they seem to have relevant experience already (based on the resume text), suggest how to rephrase existing bullet points to include the terminology. Do NOT invent experience they don't have. If a skill seems genuinely absent from their background, say so honestly and suggest they either learn it first or avoid claiming it.

Format as a numbered list, one suggestion per missing keyword or group of related keywords. Keep it concise and actionable."""

    try:
        response = hf_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/Llama-3.1-8B-Instruct",
            max_tokens=1200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Suggestions temporarily unavailable ({e}). Missing keywords to consider adding: {keywords_text}"


@app.route('/')
def home():
    return render_template('home.html', all_skills=COMMON_SKILLS)


@app.route('/analyze', methods=['POST'])
def analyze():
    jd_texts = [
        request.form.get('jd_text_1', ''),
        request.form.get('jd_text_2', ''),
        request.form.get('jd_text_3', '')
    ]
    github_username = request.form.get('github_username', '').strip()
    manual_known = request.form.getlist('known_skills')

    resume_file = request.files.get('resume_file')
    resume_skills = extract_skills_from_resume(resume_file) if resume_file and resume_file.filename else []

    github_skills = get_github_skills(github_username) if github_username else []
    known_skills = list(set(manual_known + github_skills + resume_skills))

    skill_frequency = extract_skills_with_frequency(jd_texts)
    found_skills = list(skill_frequency.keys())
    missing_skills = [skill for skill in found_skills if skill not in known_skills]
    match_percentage = round((len(found_skills) - len(missing_skills)) / len(found_skills) * 100) if found_skills else 100

    num_jds = len([t for t in jd_texts if t.strip()])

    roadmap = generate_roadmap(missing_skills)
    roadmap_html = markdown.markdown(roadmap)

    if current_user.is_authenticated:
        new_analysis = Analysis(
            user_id=current_user.id,
            jd_summary=jd_texts[0][:200] if jd_texts[0] else "No JD provided",
            missing_skills=", ".join(missing_skills),
            roadmap=roadmap
        )
        db.session.add(new_analysis)
        db.session.commit()

    return render_template(
        'result.html',
        jd_texts=jd_texts,
        skill_frequency=skill_frequency,
        found_skills=found_skills,
        known_skills=known_skills,
        missing_skills=missing_skills,
        github_skills=github_skills,
        resume_skills=resume_skills,
        num_jds=num_jds,
        roadmap=roadmap_html,
        match_percentage=match_percentage
    )


@app.route('/tailor-resume', methods=['GET', 'POST'])
def tailor_resume():
    if request.method == 'POST':
        jd_text = request.form.get('jd_text', '')
        resume_file = request.files.get('resume_file')
        resume_text = get_pdf_text(resume_file) if resume_file and resume_file.filename else ""
        resume_skills = extract_skills(resume_text) if resume_text else []
        jd_skills = extract_skills(jd_text)
        missing_keywords = [s for s in jd_skills if s not in resume_skills]
        suggestions = generate_resume_suggestions(missing_keywords, resume_text)
        suggestions_html = markdown.markdown(suggestions)
        return render_template(
            'tailor_result.html',
            jd_skills=jd_skills,
            resume_skills=resume_skills,
            missing_keywords=missing_keywords,
            suggestions=suggestions_html
        )
    return render_template('tailor_resume.html')


@app.route('/history')
@login_required
def history():
    analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
    return render_template('history.html', analyses=analyses)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken.')
            return redirect(url_for('signup'))
        new_user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)