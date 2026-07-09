from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    jd_text = request.form['jd_text']
    return render_template('result.html', jd_text=jd_text)

if __name__ == '__main__':
    app.run(debug=True)