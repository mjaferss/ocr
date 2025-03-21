import os
import base64
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import secrets
import requests
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ocr.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
TESSERACT_URL = 'http://tesseract:5000/api/ocr'  # استخدام اسم الخدمة في شبكة Docker
STATIC_API_NAME = "mohammed"
STATIC_API_KEY = "mk_1234567890abcdef1234567890abcdef"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = generate_password_hash(password)

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    key = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, name, key, user_id):
        self.name = name
        self.key = key
        self.user_id = user_id

    @staticmethod
    def generate_key():
        return secrets.token_urlsafe(16)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_api_key(api_key, name):
    if api_key.strip() == STATIC_API_KEY and name.strip() == STATIC_API_NAME:
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
    print("=== DEBUG INFO ===")
    print("All Headers:")
    for header, value in request.headers.items():
        print(f"{header}: {value}")
    
    # التحقق من المصادقة
    api_key = None
    api_name = None
    
    # التحقق من Authorization header
    auth_header = request.headers.get('Authorization')
    print(f"Authorization header: {auth_header}")
    
    if auth_header:
        try:
            if ':' in auth_header:
                api_name, api_key = auth_header.split(':')
                api_name = api_name.strip()
                api_key = api_key.strip()
            else:
                try:
                    decoded = base64.b64decode(auth_header.replace('Basic ', '')).decode()
                    if ':' in decoded:
                        api_name, api_key = decoded.split(':')
                        api_name = api_name.strip()
                        api_key = api_key.strip()
                except:
                    pass
        except Exception as e:
            print(f"Error parsing Authorization header: {e}")
    
    # التحقق من X-API headers إذا لم نجد المصادقة في Authorization
    if not api_key or not api_name:
        api_key = request.headers.get('X-API-Key', '').strip()
        api_name = request.headers.get('X-API-Name', '').strip()
    
    print(f"Final API Name: {api_name}")
    print(f"Final API Key: {api_key}")
    
    if not api_key or not api_name:
        return jsonify({'error': 'مفتاح API مفقود', 'details': 'يجب توفير اسم المفتاح والمفتاح'}), 401
        
    if not verify_api_key(api_key, api_name):
        return jsonify({'error': 'مفتاح API غير صالح', 'details': 'المفتاح أو الاسم غير صحيح'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'لم يتم تقديم ملف'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'لم يتم اختيار ملف'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'نوع الملف غير مدعوم'}), 400

    try:
        # حفظ الملف مؤقتاً
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        # تحويل الملف إلى Base64
        with open(temp_path, 'rb') as f:
            file_content = f.read()
            file_base64 = base64.b64encode(file_content).decode('utf-8')

        # إرسال الطلب إلى خدمة Tesseract
        tesseract_response = requests.post(
            TESSERACT_URL,
            json={
                'image': file_base64,
                'language': 'ara+eng'  # دعم اللغتين العربية والإنجليزية
            }
        )

        # حذف الملف المؤقت
        os.remove(temp_path)

        if tesseract_response.status_code == 200:
            result = tesseract_response.json()
            return jsonify(result)
        else:
            print(f"Tesseract Error: {tesseract_response.text}")
            return jsonify({
                'error': 'فشل في معالجة الملف',
                'details': tesseract_response.text
            }), 500

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({
            'error': 'حدث خطأ أثناء معالجة الملف',
            'details': str(e)
        }), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def init_db():
    with app.app_context():
        db.create_all()
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
