# OCR Web Application | تطبيق التعرف على النصوص

[English](#english) | [العربية](#arabic)

## English

### Overview
This is a web-based OCR (Optical Character Recognition) application that supports both Arabic and English text recognition. It processes PDF files and images (PNG, JPG, JPEG) using Tesseract OCR engine.

### Features
- PDF and image file processing
- Multi-language support (Arabic + English)
- API key authentication system
- Admin interface for API key management
- Secure file handling with base64 encoding
- Docker containerization
- Integration with n8n for automation

### Installation
1. Clone the repository:
```bash
git clone https://github.com/mjaferss/ocr.git
cd ocr
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the application using Docker Compose:
```bash
docker-compose up -d
```

### Usage
1. Access the admin interface at `http://localhost:5000/login`
   - Username: `root`
   - Password: `rootroot`

2. Use the static API key:
   - Name: `mohammed`
   - Key: `mk_1234567890abcdef1234567890abcdef`

3. Send OCR requests:
```bash
curl -X POST \
  http://localhost:5000/ocr \
  -H 'X-API-Key: mk_1234567890abcdef1234567890abcdef' \
  -H 'X-API-Name: mohammed' \
  -F 'file=@/path/to/your/file.pdf'
```

### Integration with n8n
You can use the application with n8n by:

1. Using the following cURL command:
```bash
curl -X POST 'http://[docker-ip]:5000/ocr' \
-H 'X-API-Name: mohammed' \
-H 'X-API-Key: mk_1234567890abcdef1234567890abcdef' \
-F 'file=@/path/to/file.pdf'
```

2. Or using HTTP Request in n8n:
- Method: POST
- URL: http://[docker-ip]:5000/ocr
- Headers:
  - X-API-Name: mohammed
  - X-API-Key: mk_1234567890abcdef1234567890abcdef
- Body: Form-data with 'file' field

### Technical Stack
- Flask web framework
- SQLite database
- Tesseract OCR engine
- Docker & Docker Compose
- Bootstrap UI framework

---

## Arabic <a name="arabic"></a>

### نظرة عامة
هذا تطبيق ويب للتعرف على النصوص (OCR) يدعم التعرف على النصوص العربية والإنجليزية. يقوم بمعالجة ملفات PDF والصور (PNG, JPG, JPEG) باستخدام محرك Tesseract OCR.

### المميزات
- معالجة ملفات PDF والصور
- دعم متعدد اللغات (العربية + الإنجليزية)
- نظام مصادقة بمفاتيح API
- واجهة إدارة لمفاتيح API
- معالجة آمنة للملفات باستخدام ترميز base64
- حاويات Docker
- تكامل مع n8n للأتمتة

### التثبيت
1. استنساخ المستودع:
```bash
git clone https://github.com/mjaferss/ocr.git
cd ocr
```

2. تثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

3. تشغيل التطبيق باستخدام Docker Compose:
```bash
docker-compose up -d
```

### الاستخدام
1. الوصول إلى واجهة الإدارة على `http://localhost:5000/login`
   - اسم المستخدم: `root`
   - كلمة المرور: `rootroot`

2. استخدام مفتاح API الثابت:
   - الاسم: `mohammed`
   - المفتاح: `mk_1234567890abcdef1234567890abcdef`

3. إرسال طلبات OCR:
```bash
curl -X POST \
  http://localhost:5000/ocr \
  -H 'X-API-Key: mk_1234567890abcdef1234567890abcdef' \
  -H 'X-API-Name: mohammed' \
  -F 'file=@/path/to/your/file.pdf'
```

### التكامل مع n8n
يمكن استخدام التطبيق مع n8n عن طريق:

1. استخدام أمر cURL التالي:
```bash
curl -X POST 'http://[docker-ip]:5000/ocr' \
-H 'X-API-Name: mohammed' \
-H 'X-API-Key: mk_1234567890abcdef1234567890abcdef' \
-F 'file=@/path/to/file.pdf'
```

2. أو استخدام HTTP Request في n8n:
- Method: POST
- URL: http://[docker-ip]:5000/ocr
- Headers:
  - X-API-Name: mohammed
  - X-API-Key: mk_1234567890abcdef1234567890abcdef
- Body: Form-data with 'file' field

### التقنيات المستخدمة
- إطار عمل Flask
- قاعدة بيانات SQLite
- محرك Tesseract OCR
- Docker و Docker Compose
- إطار عمل Bootstrap للواجهة
