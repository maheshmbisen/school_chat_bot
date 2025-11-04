from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_from_directory
import pandas as pd
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# load .env if present
load_dotenv()

ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASS = os.getenv('ADMIN_PASS', 'password')
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-please')

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

FAQ_PATH = os.path.join(os.path.dirname(__file__), "faq.xlsx")

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4 MB limit

def load_faq(path=FAQ_PATH):
    try:
        df = pd.read_excel(path)
        df = df.fillna("")
        df['role'] = df['role'].str.strip().str.lower()
        df['keywords'] = df['keywords'].astype(str)
        return df
    except Exception as e:
        print("Failed to load FAQ:", e)
        return pd.DataFrame(columns=['role','keywords','answer'])

# initial load
faq_df = load_faq()

@app.context_processor
def inject_logged_in():
    return dict(admin_logged_in=session.get('admin_logged_in', False))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    role = (data.get('role') or '').strip().lower()
    query = (data.get('message') or '').strip().lower()

    if not role or not query:
        return jsonify({ 'error': 'role and message are required' }), 400

    for _, row in faq_df.iterrows():
        r = row['role']
        if r == role or r == 'common':
            for key in row['keywords'].split(','):
                if key.strip() and key.strip().lower() in query:
                    return jsonify({ 'answer': row['answer'] })

    return jsonify({ 'answer': "Sorry, I don't know that. Please contact the school office for more details." })

# ---------------- Admin routes ----------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['admin_logged_in'] = True
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out.', 'info')
    return redirect(url_for('admin_login'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ('xlsx', 'xls')

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    global faq_df
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        # single-file replace mode (Upload Mode 1)
        file = request.files.get('faq_file')
        if not file or file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('admin_dashboard'))
        if not allowed_file(file.filename):
            flash('Only Excel files (.xlsx/.xls) are allowed.', 'danger')
            return redirect(url_for('admin_dashboard'))

        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        # replace existing faq.xlsx
        try:
            # move to FAQ_PATH (overwrite)
            os.replace(save_path, FAQ_PATH)
            # reload faq_df
            faq_df = load_faq()
            flash('FAQ updated successfully. Replaced existing faq.xlsx.', 'success')
        except Exception as e:
            flash(f'Failed to update FAQ: {e}', 'danger')

        return redirect(url_for('admin_dashboard'))

    # show some basic stats
    rows = len(faq_df)
    return render_template('admin_dashboard.html', rows=rows)

# serve uploaded files for convenience (admin only)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if not session.get('admin_logged_in'):
        return 'Forbidden', 403
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
