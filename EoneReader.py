from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, Response
import os
import zipfile
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
import uuid
import mimetypes
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UNZIPPED_DIR = os.path.join(BASE_DIR, 'unzipped_books')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

os.makedirs(UNZIPPED_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UNZIPPED_DIR'] = UNZIPPED_DIR

DATABASE = os.path.join(BASE_DIR, 'usage.db')

# Database setup
DATABASE = 'usage.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_used TIMESTAMP,
                trial_start TIMESTAMP,
                access_status TEXT
            )
        ''')
        cursor.execute('''
            SELECT COUNT(*) FROM usage
        ''')
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute('''
                INSERT INTO usage (last_used, trial_start, access_status) VALUES (?, ?, ?)
            ''', (datetime.now(), datetime.now(), 'trial'))
        conn.commit()

def get_usage():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usage ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        logging.debug(f"get_usage result: {result}")  # Debug statement
        return result

def update_usage():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE usage SET last_used = ? WHERE id = (SELECT MAX(id) FROM usage)', (datetime.now(),))
        conn.commit()

def is_trial_expired():
    usage = get_usage()
    if usage:
        if len(usage) > 2:
            logging.debug(f"Checking trial expiry: {usage}")  # Debug statement
            trial_start = datetime.strptime(usage[2], '%Y-%m-%d %H:%M:%S.%f')
            if datetime.now() - trial_start > timedelta(days=14):  # 14 days trial
                return True
        else:
            logging.debug("Usage data is incomplete.")  # Debug statement
    return False

def update_access_status():
    if is_trial_expired():
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE usage SET access_status = ? WHERE id = (SELECT MAX(id) FROM usage)', ('full',))
            conn.commit()

def get_access_status():
    usage = get_usage()
    if usage and len(usage) > 3:
        return usage[3]  # access_status
    logging.debug("Usage data is incomplete or not found.")  # Debug statement
    return None

@app.route('/index')
def index():
    update_access_status()
    access_status = get_access_status()
    if access_status == 'trial' and is_trial_expired():
        return "Trial period has expired. Please purchase the full version.", 403
    elif access_status == 'full':
        return render_template('index.html')
    update_usage()
    return render_template('index.html')

def extract_epub(epub_path, output_folder):
    try:
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        return True
    except Exception as e:
        print(f"Error extracting EPUB: {str(e)}")
        return False

def create_html_from_epub(epub_path, output_html_path):
    try:
        book = epub.read_epub(epub_path)
        content = ""
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            content += item.content.decode('utf-8', errors='ignore')
        with open(output_html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(content)
        return True
    except Exception as e:
        return f"Error creating HTML from EPUB: {str(e)}"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'epub'

def list_files_and_directories(folder):
    directories = []
    files = []
    directory_files = {}
    for entry in os.listdir(folder):
        full_path = os.path.join(folder, entry)
        if os.path.isdir(full_path):
            directories.append(entry)
            directory_files[entry] = os.listdir(full_path)
        else:
            files.append(entry)
    return directories, files, directory_files

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        file_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id + '.epub')
        file.save(file_path)
        extract_dir = os.path.join(app.config['UNZIPPED_DIR'], file_id)
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        return redirect(url_for('read_epub', folder_name=file_id))
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/read_epub/<folder_name>')
def read_epub(folder_name):
    current_folder = os.path.join(app.config['UNZIPPED_DIR'], folder_name)
    directories, files, directory_files = list_files_and_directories(current_folder)
    return render_template('read_epub.html', folder_name=folder_name, directories=directories, files=files, directory_files=directory_files)

@app.route('/unzipped_books/<path:filename>')
def serve_unzipped_file(filename):
    filename = filename.replace('\\', '/')
    file_path = os.path.join(app.config['UNZIPPED_DIR'], filename)
    if filename.endswith('toc.ncx'):
        folder_name = os.path.dirname(filename)
        return parse_toc_ncx(file_path, folder_name)
    specific_files = ['docx.css', 'metadata.opf', 'mimetype', 'container.xml', 'content.opf']
    if os.path.basename(filename) in specific_files:
        mimetype, _ = mimetypes.guess_type(file_path)
        if not mimetype:
            mimetype = 'text/plain'
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return Response(content, mimetype=mimetype)
    return send_from_directory(app.config['UNZIPPED_DIR'], filename)

def parse_toc_ncx(toc_path, folder_name):
    with open(toc_path, 'r', encoding='utf-8') as file:
        content = file.read()
    soup = BeautifulSoup(content, 'xml')
    nav_map = soup.find('navMap')
    toc_html = '<ul>'
    for nav_point in nav_map.find_all('navPoint'):
        toc_html += parse_nav_point(nav_point, folder_name)
    toc_html += '</ul>'
    return toc_html

def parse_nav_point(nav_point, folder_name):
    toc_html = '<li>'
    nav_label = nav_point.find('navLabel').text
    content_src = nav_point.find('content')['src']
    toc_html += f'<a href="/unzipped_books/{folder_name}/{content_src}" target="contentFrame">{nav_label}</a>'
    if nav_point.find('navPoint'):
        toc_html += '<ul>'
        for child_nav_point in nav_point.find_all('navPoint'):
            toc_html += parse_nav_point(child_nav_point, folder_name)
        toc_html += '</ul>'
    toc_html += '</li>'
    return toc_html

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
