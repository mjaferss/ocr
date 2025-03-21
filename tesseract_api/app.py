from flask import Flask, request, jsonify
import pytesseract
from PIL import Image
import io
import base64
from pdf2image import convert_from_bytes

app = Flask(__name__)

def process_image(image, lang='ara+eng'):
    """Process a single image with Tesseract OCR"""
    try:
        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return ""

@app.route('/api/ocr', methods=['POST'])
def ocr():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400

        # Decode base64 data
        image_data = base64.b64decode(data['image'])
        
        # Get language from request or default to Arabic + English
        lang = data.get('language', 'ara+eng')
        
        # Check if it's a PDF by looking at the magic numbers
        is_pdf = image_data[:4] == b'%PDF'
        
        if is_pdf:
            # Convert PDF to images
            try:
                pdf_images = convert_from_bytes(image_data)
                texts = []
                for img in pdf_images:
                    text = process_image(img, lang)
                    if text:
                        texts.append(text)
                
                if not texts:
                    return jsonify({'error': 'لم يتم العثور على نص في ملف PDF'}), 400
                
                return jsonify({
                    'text': '\n---\n'.join(texts),
                    'language': lang,
                    'pages': len(pdf_images),
                    'confidence': 100  # Simplified confidence score
                })
            
            except Exception as e:
                print(f"PDF processing error: {str(e)}")
                return jsonify({'error': 'حدث خطأ في معالجة ملف PDF'}), 500
        else:
            # Process as regular image
            try:
                image = Image.open(io.BytesIO(image_data))
                text = process_image(image, lang)
                
                if not text:
                    return jsonify({'error': 'لم يتم العثور على نص في الصورة'}), 400
                
                return jsonify({
                    'text': text,
                    'language': lang,
                    'pages': 1,
                    'confidence': 100  # Simplified confidence score
                })
            
            except Exception as e:
                print(f"Image processing error: {str(e)}")
                return jsonify({'error': 'حدث خطأ في معالجة الصورة'}), 500

    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
