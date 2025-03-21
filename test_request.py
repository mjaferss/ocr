import requests
import os

def test_ocr(file_path):
    url = 'http://localhost:5000/ocr'
    headers = {
        'Authorization': 'mohammed:mk_1234567890abcdef1234567890abcdef'
    }

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': ('test.pdf', f, 'application/pdf')
            }
            print("Sending request...")
            print(f"File size: {os.path.getsize(file_path)} bytes")
            response = requests.post(url, headers=headers, files=files)
            print("\nResponse Status:", response.status_code)
            print("\nResponse Headers:")
            for header, value in response.headers.items():
                print(f"{header}: {value}")
            print("\nResponse Body:")
            print(response.text)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    file_path = r"C:\Users\pr-mm\Documents\1.pdf"
    test_ocr(file_path)
