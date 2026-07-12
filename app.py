import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from collections import Counter
from huggingface_hub import InferenceClient
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


def generate_roadmap(missing_skills, weeks_available=6):
    if not missing_skills:
        return "You already know all the required skills — no roadmap needed!"

    skills_text = ", ".join(missing_skills)
    prompt = f"""Create a simple {weeks_available}-week learning roadmap for a beginner to learn these skills: {skills_text}.
Format it as a numbered list, one line per week, mentioning which skill(s) to focus on that week. Keep it concise."""

    try:
        response = hf_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/Llama-3.1-8B-Instruct",
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Roadmap generation is temporarily unavailable ({e}). Here are the skills to focus on in order: {skills_text}"


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

    github_skills = get_github_skills(github_username) if github_username else []
    known_skills = list(set(manual_known + github_skills))

    skill_frequency = extract_skills_with_frequency(jd_texts)
    found_skills = list(skill_frequency.keys())
    missing_skills = [skill for skill in found_skills if skill not in known_skills]

    num_jds = len([t for t in jd_texts if t.strip()])

    roadmap = generate_roadmap(missing_skills)

    return render_template(
        'result.html',
        jd_texts=jd_texts,
        skill_frequency=skill_frequency,
        found_skills=found_skills,
        known_skills=known_skills,
        missing_skills=missing_skills,
        github_skills=github_skills,
        num_jds=num_jds,
        roadmap=roadmap
    )


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