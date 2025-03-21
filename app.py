from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
import requests
import tempfile
import base64
from models import db, User, APIKey
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ocr.db'
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Initialize Flask extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
TESSERACT_URL = 'http://localhost:8180/api/ocr'

# Static API key for mohammed
STATIC_API_KEY = "mk_1234567890abcdef1234567890abcdef"
STATIC_API_NAME = "mohammed"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_api_key(api_key, name):
    if api_key == STATIC_API_KEY and name == STATIC_API_NAME:
        return True
    key = APIKey.query.filter_by(key=api_key, name=name).first()
    return key is not None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('خطأ في اسم المستخدم أو كلمة المرور', 'error')
    
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin():
    api_keys = APIKey.query.filter_by(user_id=current_user.id).all()
    # Add static API key to the list
    static_key = {
        'name': STATIC_API_NAME,
        'key': STATIC_API_KEY,
        'created_at': datetime.utcnow(),
        'is_static': True
    }
    return render_template('admin.html', api_keys=api_keys, static_key=static_key)

@app.route('/admin/add_key', methods=['POST'])
@login_required
def add_key():
    name = request.form.get('name')
    if name:
        api_key = APIKey(
            name=name,
            key=APIKey.generate_key(),
            user_id=current_user.id
        )
        db.session.add(api_key)
        db.session.commit()
        flash('تم إنشاء مفتاح API بنجاح', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete_key/<int:key_id>', methods=['POST'])
@login_required
def delete_key(key_id):
    api_key = APIKey.query.get_or_404(key_id)
    if api_key.user_id == current_user.id:
        db.session.delete(api_key)
        db.session.commit()
        flash('تم حذف مفتاح API بنجاح', 'success')
    return redirect(url_for('admin'))

@app.route('/ocr', methods=['POST'])
def ocr():
    # Check API key authentication
    api_key = request.headers.get('X-API-Key')
    api_name = request.headers.get('X-API-Name')
    
    if not api_key or not api_name or not verify_api_key(api_key, api_name):
        return jsonify({'error': 'مفتاح API غير صالح'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'لم يتم تقديم ملف'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'لم يتم اختيار ملف'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'نوع الملف غير صالح'}), 400

    try:
        # Send file directly to Tesseract container
        file_content = file.read()
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        response = requests.post(TESSERACT_URL, json={
            'image': file_base64,
            'language': 'ara+eng'
        })
        
        if response.status_code != 200:
            return jsonify({'error': 'حدث خطأ في معالجة الملف'}), 500
            
        return jsonify(response.json())

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def init_db():
    with app.app_context():
        db.create_all()
        # Create root user if it doesn't exist
        if not User.query.filter_by(username='root').first():
            root_user = User(
                username='root',
                password=generate_password_hash('rootroot')
            )
            db.session.add(root_user)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
