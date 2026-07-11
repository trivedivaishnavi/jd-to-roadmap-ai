# Progress Log — JD-to-Roadmap AI

## Week 1 — Flask Basics

- Jul 8: Set up Python, Git, GitHub. Built and pushed first "hello world" Flask route. Fixed a Python PATH issue (Windows Store alias) and a git push hang along the way.
- Jul 9 (Day 2): Learned Flask forms (POST requests) and Jinja2 variable rendering. Built a form that takes JD text input and displays it on a result page. Fixed a folder structure issue (nested templates folder) along the way.
- Jul 9 (Day 2): Added Bootstrap via CDN, styled the home and result pages with proper spacing, form styling, and a card layout.
- Learned Jinja2 template inheritance ({% extends %}, {% block %}), created a base template with navbar, refactored home and result pages to use it. Fixed an issue where unsaved files were blocking Flask from reflecting changes.
- Added user signup/login using Flask-SQLAlchemy (database) and Flask-Login (session management), with securely hashed passwords via Werkzeug. Fixed a template location issue (signup.html/login.html were outside the templates folder).
- Built the core skill-extraction feature: a curated skills list (skills_data.py) and a matching function that scans pasted job descriptions for known tech skills, displayed on the result page.
- Added skill-gap comparison: users can now check off skills they already know, and the app calculates which required skills (from the JD) are missing, shown in a separate highlighted card.
- Added GitHub API integration for automatic skill detection: users can enter their GitHub username, and the app fetches their public repos' languages to auto-detect known skills, shown in a dedicated card on the result page.
- Added multi-JD aggregation: users can paste up to 3 job descriptions for a target role, and the app counts how frequently each skill appears across them, displayed as a frequency badge (e.g., 3/3). Tested with sample AI/ML job postings.