"""
Jira Task Creator - Python Backend Server
Bu server HTML frontend ile Jira API arasında köprü görevi görür.
XSRF/CORS sorunlarını bypass eder.

Kullanım:
1. pip install flask requests flask-cors
2. python server.py
3. Tarayıcıda http://localhost:5000 aç
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)  # Tüm CORS isteklerine izin ver

# Ana sayfa - HTML dosyasını serve et
@app.route('/')
def index():
    return send_file('jira_app.html')

# Jira API Proxy - tüm istekleri Jira'ya ilet
@app.route('/api/jira/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def jira_proxy(endpoint):
    """Jira API proxy - tarayıcıdan gelen istekleri Jira'ya iletir"""

    # Header'lardan Jira bilgilerini al
    jira_url = request.headers.get('X-Jira-Url', '').rstrip('/')
    auth_header = request.headers.get('Authorization', '')

    if not jira_url or not auth_header:
        return jsonify({'error': 'Jira URL ve Authorization header gerekli'}), 400

    # Jira'ya istek yap
    jira_endpoint = f"{jira_url}/rest/api/2/{endpoint}"

    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Atlassian-Token': 'no-check'
    }

    try:
        if request.method == 'GET':
            # Query string'i de ilet
            resp = requests.get(jira_endpoint, headers=headers, params=request.args, verify=False)
        elif request.method == 'POST':
            resp = requests.post(jira_endpoint, headers=headers, json=request.json, verify=False)
        elif request.method == 'PUT':
            resp = requests.put(jira_endpoint, headers=headers, json=request.json, verify=False)
        elif request.method == 'DELETE':
            resp = requests.delete(jira_endpoint, headers=headers, verify=False)

        # Jira'dan gelen yanıtı döndür
        try:
            return jsonify(resp.json()), resp.status_code
        except:
            return resp.text, resp.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

# Issue Link endpoint
@app.route('/api/jira-link', methods=['POST'])
def jira_issue_link():
    """Issue link oluştur"""

    jira_url = request.headers.get('X-Jira-Url', '').rstrip('/')
    auth_header = request.headers.get('Authorization', '')

    if not jira_url or not auth_header:
        return jsonify({'error': 'Jira URL ve Authorization header gerekli'}), 400

    jira_endpoint = f"{jira_url}/rest/api/2/issueLink"

    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json',
        'X-Atlassian-Token': 'no-check'
    }

    try:
        resp = requests.post(jira_endpoint, headers=headers, json=request.json, verify=False)
        if resp.status_code == 201 or resp.status_code == 204:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': resp.text}), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500


# Attachment upload endpoint
@app.route('/api/jira-attachment/<issue_key>', methods=['POST'])
def jira_attachment(issue_key):
    """Issue'ya dosya ekle"""

    jira_url = request.headers.get('X-Jira-Url', '').rstrip('/')
    auth_header = request.headers.get('Authorization', '')

    if not jira_url or not auth_header:
        return jsonify({'error': 'Jira URL ve Authorization header gerekli'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'Dosya bulunamadı'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400

    jira_endpoint = f"{jira_url}/rest/api/2/issue/{issue_key}/attachments"

    headers = {
        'Authorization': auth_header,
        'X-Atlassian-Token': 'no-check'
    }

    try:
        # Multipart form-data olarak gönder
        files = {'file': (file.filename, file.stream, file.content_type)}
        resp = requests.post(jira_endpoint, headers=headers, files=files, verify=False)

        if resp.status_code == 200:
            return jsonify(resp.json()), 200
        else:
            return jsonify({'error': resp.text}), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("Jira Task Creator Server")
    print("=" * 50)
    print("Server başlatılıyor...")
    print("Tarayıcıda aç: http://localhost:5000")
    print("Durdurmak için: Ctrl+C")
    print("=" * 50)

    # SSL uyarılarını kapat
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    app.run(host='0.0.0.0', port=5000, debug=True)
