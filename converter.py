import os
import re
from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename
from docx import Document
from ebooklib import epub

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with your secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
ALLOWED_EXTENSIONS = {'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_color(run):
    color = run.font.color.rgb
    if color:
        return f"#{color}"
    return None

def docx_to_epub(docx_path, epub_path, html_path, metadata=None):
    if metadata is None or not isinstance(metadata, dict):
        metadata = {}
    print(f"Metadata received: {metadata}")

    doc = Document(docx_path)
    content = ""
    image_count = 0
    heading_counter = []
    heading_list = []
    toc_map = {}
    current_map_stack = [toc_map]

    image_folder = os.path.join(os.path.dirname(html_path), 'images')
    os.makedirs(image_folder, exist_ok=True)

    def get_color(run):
        if run.font.color and run.font.color.rgb:
            return run.font.color.rgb
        return None

    def add_color_span(text, color):
        if color:
            return f'<span style="color:#{color};">{text}</span>'
        return text

    for para in doc.paragraphs:
        if para.style.name.startswith('Heading'):
            level = int(re.search(r'\d+', para.style.name).group())

            while len(heading_counter) <= level:
                heading_counter.append(0)
            heading_counter[level] += 1

            for i in range(level + 1, len(heading_counter)):
                heading_counter[i] = 0

            section_id = f"sec_{'_'.join(map(str, heading_counter[:level + 1]))}"
            heading_list.append(section_id)

            while len(current_map_stack) <= level:
                current_map_stack.append({})

            current_map = current_map_stack[level - 1]
            current_map[para.text] = {'id': section_id, 'sub': {}}
            current_map_stack[level] = current_map[para.text]['sub']

            heading_text = "".join(add_color_span(run.text, get_color(run)) for run in para.runs)
            content += f'<h{level} id="{section_id}">{heading_text}</h{level}>'
        else:
            para_text = "".join(add_color_span(run.text, get_color(run)) for run in para.runs)
            content += f'<p>{para_text}</p>'

        for run in para.runs:
            if run.element.xpath(".//a:blip"):
                for blip in run.element.xpath(".//a:blip"):
                    rId = blip.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"]
                    image = doc.part.related_parts[rId]
                    image_count += 1
                    image_name = f'image_{image_count}.png'
                    image_path = os.path.join(image_folder, image_name)
                    with open(image_path, "wb") as img_file:
                        img_file.write(image.blob)
                    content += f'<img src="images/{image_name}" alt="Image {image_count}"/>'

    toc_html = '<nav epub:type="toc" id="toc" style="display:block;"><h2>Table of Contents</h2><ul>'

    def build_toc_map(toc_map, html_filename, level=1):
        html = ''
        for heading, data in toc_map.items():
            html += f'<li><a href="{html_filename}#{data["id"]}">{heading}</a>'
            if data['sub']:
                html += '<ul>' + build_toc_map(data['sub'], html_filename, level + 1) + '</ul>'
            html += '</li>'
        return html

    html_filename = os.path.basename(html_path)
    toc_html += build_toc_map(toc_map, html_filename)
    toc_html += '</ul></nav>'

    full_content = toc_html + content

    with open(html_path, 'w', encoding='utf-8') as html_file:
        html_file.write(full_content)

    book = epub.EpubBook()
    book.set_title(metadata.get('title', 'Sample eBook'))
    book.set_language(metadata.get('language', 'en'))
    book.add_author(metadata.get('author', 'Unknown'))
    book.add_metadata('DC', 'description', metadata.get('description', ''))

    # Add custom metadata for generator
    generator_metadata = f'Vareshwar&Humisha. Hisar 125001.India - Credit: Ebook-lib {metadata.get("ebooklib_version", "0.18.1")}'
    book.add_metadata('DC', 'creator', generator_metadata)

    chapter = epub.EpubHtml(title='Content', file_name=html_filename, lang='en')
    chapter.content = full_content
    book.add_item(chapter)

    for i in range(1, image_count + 1):
        image_name = f'image_{i}.png'
        image_path = os.path.join(image_folder, image_name)
        if os.path.exists(image_path):
            epub_image = epub.EpubImage()
            epub_image.file_name = f'images/{image_name}'
            epub_image.media_type = 'image/png'
            with open(image_path, 'rb') as img_file:
                epub_image.content = img_file.read()
            book.add_item(epub_image)

    toc = []

    def add_to_toc(toc_map):
        for heading, data in toc_map.items():
            toc.append(epub.Link(f'{html_filename}#{data["id"]}', heading, data["id"]))
            add_to_toc(data['sub'])

    add_to_toc(toc_map)
    
    book.toc = toc

    toc_chapter = epub.EpubHtml(title='Table of Contents', file_name='toc.xhtml', lang='en', content=toc_html)
    book.add_item(toc_chapter)

    style = '''
    nav[toc] ul { list-style-type: none; }
    nav[toc] ul ul { margin-left: 20px; }
    nav[toc] li { margin: 0.5em 0; }
    nav[toc] a { text-decoration: none; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    book.spine = ['nav', toc_chapter, chapter]

    epub.write_epub(epub_path, book, {})

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert DOCX to EPUB")
    parser.add_argument("docx_path", help="Path to the DOCX file")
    parser.add_argument("epub_path", help="Path to the output EPUB file")
    parser.add_argument("html_path", help="Path to the temporary HTML file")
    parser.add_argument("--title", help="Title of the eBook", default="Sample eBook")
    parser.add_argument("--author", help="Author of the eBook", default="Unknown")
    parser.add_argument("--language", help="Language of the eBook", default="en")
    parser.add_argument("--description", help="Description of the eBook", default="")
    parser.add_argument("--creator", help="Creator of the eBook", default="HumishaMakeGro")
    args = parser.parse_args()

    metadata = {
        'title': args.title,
        'author': args.author,
        'language': args.language,
        'description': args.description,
        'creator': args.creator
    }

    docx_to_epub(docx_path, epub_path, html_path, metadata, cover_image_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        docx_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(docx_path)

        title = request.form.get('title', 'Sample eBook')
        author = request.form.get('author', 'Unknown')
        language = request.form.get('language', 'en')
        description = request.form.get('description', '')

        metadata = {
            'title': title,
            'author': author,
            'language': language,
            'description': description
        }

        epub_filename = f"{os.path.splitext(filename)[0]}.epub"
        html_filename = f"{os.path.splitext(filename)[0]}.html"
        epub_path = os.path.join(app.config['OUTPUT_FOLDER'], epub_filename)
        html_path = os.path.join(app.config['OUTPUT_FOLDER'], html_filename)

        docx_to_epub(docx_path, epub_path, html_path, metadata)

        flash(f'EPUB created: {epub_filename}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    app.run(debug=True)