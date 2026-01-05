from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Get project root (parent of src directory)
basedir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.dirname(basedir)

# Initialize Flask with correct template and static paths
app = Flask(
    __name__,
    template_folder=os.path.join(project_root, 'public', 'templates'),
    static_folder=os.path.join(project_root, 'public', 'static')
)

# Configuration
db_path = os.path.join(project_root, 'todo.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Initialize database
db = SQLAlchemy(app)

# Database Model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Note {self.title}>'

# Create tables - drop old schema and recreate with new columns
with app.app_context():
    db.drop_all()
    db.create_all()

# Routes
@app.route("/")
def index():
    """Display all notes"""
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return render_template('index.html', notes=notes)

@app.route("/add", methods=['GET', 'POST'])
def add_note():
    """Add a new note"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            flash('Title and content are required!', 'error')
            return redirect(url_for('add_note'))
        
        note = Note(title=title, content=content)
        db.session.add(note)
        db.session.commit()
        flash('Note created successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_note.html')

@app.route("/edit/<int:id>", methods=['GET', 'POST'])
def edit_note(id):
    """Edit an existing note"""
    note = Note.query.get_or_404(id)
    
    if request.method == 'POST':
        note.title = request.form.get('title', '').strip()
        note.content = request.form.get('content', '').strip()
        
        if not note.title or not note.content:
            flash('Title and content are required!', 'error')
            return redirect(url_for('edit_note', id=id))
        
        db.session.commit()
        flash('Note updated successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_note.html', note=note)

@app.route("/delete/<int:id>")
def delete_note(id):
    """Delete a note"""
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route("/toggle/<int:id>", methods=['POST'])
def toggle_todo(id):
    """Toggle todo completion status"""
    note = Note.query.get_or_404(id)
    note.is_completed = not note.is_completed
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "app": "Todo Application"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
