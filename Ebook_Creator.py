from flask import Flask, request, redirect, url_for, flash, render_template, send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email
from flask_mail import Mail, Message
from converter import docx_to_epub
from dotenv import load_dotenv




# Load environment variables from .env file
load_dotenv()

# Flask app configuration
app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///D:/EbookCreator/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
ALLOWED_EXTENSIONS = {'docx'}

# Database setup
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
mail = Mail(app)

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    trial_start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    trial_end_date = db.Column(db.DateTime, nullable=False)

    def __init__(self, username, email, password, trial_days=14):
        self.username = username
        self.email = email
        self.password = password
        self.trial_start_date = datetime.utcnow()
        self.trial_end_date = self.trial_start_date + timedelta(days=trial_days)

# Define the eBook model
class Ebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    filepath = db.Column(db.String(150), nullable=False)
    created_by = db.Column(db.String(150), nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Utility function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# WTForms setup
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Route: Index page
@app.route('/index')
def index():
    return render_template('index.html')
# Route: Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You can now log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Route: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)
# Route: Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
	
# Route: Display eBooks
@app.route('/ebooks')
def display_ebooks():
    ebooks = Ebook.query.all()
    return render_template('ebooks.html', ebooks=ebooks)

# Route: File upload
@app.route('/upload', methods=['POST'])
@login_required
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

        # Save eBook details to the database
        new_ebook = Ebook(
            title=title,
            author=author,
            language=language,
            description=description,
            filepath=epub_filename,
            created_by=current_user.username
        )
        db.session.add(new_ebook)
        db.session.commit()

        flash(f'EPUB created: {epub_filename}')
        return redirect(url_for('index'))
    else:
        flash('File type not allowed')
        return redirect(url_for('index'))

# Route to download eBooks
@app.route('/download/<ebook_id>/<filename>')
@login_required
def download_ebook(filename):
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

# Route to preview eBooks (for HTML files)
@app.route('/preview/<filename>')
@login_required
def preview_ebook(filename):
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if filename.endswith('.html'):
        return send_file(filepath, mimetype='text/html')
    else:
        return send_file(filepath)

# Ensure the uploads and output directories exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['OUTPUT_FOLDER']):
    os.makedirs(app.config['OUTPUT_FOLDER'])

if __name__ == "__main__":
    app.run(debug=False) 

