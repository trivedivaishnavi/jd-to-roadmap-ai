# Progress Log — JD-to-Roadmap AI

## Day 1
Started today by setting up Python, Git, and GitHub — took a bit longer than expected because Windows kept saying "python not found" even after I installed it. Turned out Windows has this fake python shortcut that redirects to the Microsoft Store, had to go into settings and turn off "App execution aliases" for python.exe and python3.exe to fix it.

Built my first Flask app — just a "hello world" route. Felt small but it actually worked, which was exciting. Then figured out how to push it to GitHub. Git push got stuck the first time (just sat there doing nothing), turned out it was waiting for me to log in through a browser popup that I almost missed.

Also learned about Jinja2 templates — instead of returning plain text from Flask, you can return actual HTML pages. Made a `templates` folder and a `home.html` file. Messed up the folder structure at first (accidentally created a nested templates folder inside itself), took a bit to catch that.

## Day 2
Learned how to make a form that actually takes user input — used `request.form` in Flask to grab what someone types into a textarea, then show it back on a new page using Jinja2 variables (`{{ jd_text }}`). This is the whole point of the app really — letting someone paste a job description in.

Added Bootstrap to make the page look less bare. Just linking a CDN in the HTML head gives you actual styled buttons, cards, spacing — didn't have to write CSS myself.

Then learned about template inheritance — instead of copy-pasting the same navbar into every page, you make one `base.html` file and other pages "extend" it using `{% extends %}` and `{% block %}`. Took a minute to understand why this mattered until I actually had to update the navbar and realized I'd only have to change it in one place now.

Ran into the same "site can't be reached" error a bunch of times today — almost always because I forgot to actually save the file before running it again, or the server had stopped running in the background without me noticing.

## Day 2 (continued)
Added real user accounts — signup and login. This was a bigger jump than anything before. Learned about databases for the first time (used SQLite through something called SQLAlchemy, which lets you write Python classes instead of raw SQL). Learned that you're never supposed to store someone's actual password — you hash it instead (basically scrambles it in a way that can't be reversed), so even if the database got leaked, nobody could see the real passwords.

Fixed another folder mix-up — signup.html and login.html were sitting outside the templates folder by mistake, so Flask couldn't find them.

Also went down a small rabbit hole about GitHub's contribution graph — my commits weren't showing up as "contributions" even though they were clearly on the repo. Turned out the email in my Git config didn't match my verified GitHub email. Fixed that so future commits count properly.

## Skill extraction feature
Built the actual core feature — pasting a job description and having the app pull out which skills are mentioned. Kept it simple: a list of common tech skills, and just checking if each one shows up in the text (case-insensitive). Not fancy AI, just string matching, but it's a real starting point.

## Skill-gap comparison
Added checkboxes so I can mark which skills I already know, then the app compares that against what's required in the JD and shows me what I'm actually missing. This felt like the app finally "doing something" instead of just displaying text back.

## GitHub auto-detection
Wanted the app to stand out, so instead of only self-reporting skills via checkboxes, I added a feature where you type in your GitHub username and it calls GitHub's public API to check what languages your repos actually use — then marks those as "known" automatically. No login needed for this since it's public data. Felt pretty cool seeing it correctly detect Python and HTML from my own repo.

## Multi-JD aggregation
Realized comparing against just one job posting isn't that useful — so I added the option to paste up to 3 similar job descriptions at once, and the app counts how often each skill shows up across all of them (like "Python: 3/3", "SQL: 1/3"). Used Python's `Counter` for this, which made the counting part pretty easy once I found it.

## AI roadmap generation
This was the hardest part so far. Wanted the app to actually generate a personalized learning plan based on my missing skills, using a real AI model instead of me hardcoding a template. Signed up for Hugging Face (free), got an API token, and hit a bunch of errors where specific models weren't supported ("model not supported by provider" a few times in a row). Eventually figured out that Hugging Face routes requests through different providers behind the scenes, and not all of them support the models I was trying to use — switching to letting it auto-pick a provider instead of forcing one fixed it. First time I saw an actual AI-generated week-by-week roadmap show up based on my real skill gaps, genuinely felt like a big milestone.

## General notes on debugging this whole project
A recurring theme: most of my errors weren't really about the "hard" concepts — they were things like unsaved files, wrong folder locations, or a server that quietly stopped running. Learning to actually read error messages in the terminal (instead of panicking) and checking the obvious stuff first (is it saved? is the server running? is the file in the right folder?) probably taught me as much as the actual features did.