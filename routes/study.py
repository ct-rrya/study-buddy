"""
Study Routes - File upload, Quiz, Bot interaction
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from models import db, StudyFile, StudySession, BotConversation
from services.bot import StudyBot
import os

study_bp = Blueprint('study', __name__)
ALLOWED_EXTENSIONS = {'txt', 'md', 'pptx', 'docx', 'xlsx', 'pdf'}

def extract_text_from_file(file, filename):
    """Extract text content from various file types"""
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext in ['txt', 'md']:
        return file.read().decode('utf-8')
    
    elif ext == 'pptx':
        from pptx import Presentation
        from io import BytesIO
        prs = Presentation(BytesIO(file.read()))
        text_parts = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text_parts.append(shape.text)
        return '\n\n'.join(text_parts)
    
    elif ext == 'docx':
        from docx import Document
        from io import BytesIO
        doc = Document(BytesIO(file.read()))
        text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
        return '\n\n'.join(text_parts)
    
    elif ext == 'xlsx':
        import openpyxl
        from io import BytesIO
        wb = openpyxl.load_workbook(BytesIO(file.read()))
        text_parts = []
        for sheet in wb.worksheets:
            text_parts.append(f"Sheet: {sheet.title}")
            for row in sheet.iter_rows(values_only=True):
                row_text = ' | '.join([str(cell) for cell in row if cell is not None])
                if row_text.strip():
                    text_parts.append(row_text)
        return '\n'.join(text_parts)
    
    elif ext == 'pdf':
        from PyPDF2 import PdfReader
        from io import BytesIO
        reader = PdfReader(BytesIO(file.read()))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return '\n\n'.join(text_parts)
    
    return ""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@study_bp.route('/study')
@login_required
def study_page():
    files = StudyFile.query.filter_by(user_id=current_user.id).all()
    return render_template('study.html', files=files)

@study_bp.route('/chat/history/<int:file_id>')
@login_required
def get_chat_history(file_id):
    """Get chat history for a specific file"""
    conversations = BotConversation.query.filter_by(
        user_id=current_user.id,
        file_id=file_id
    ).order_by(BotConversation.sent_at.asc()).all()
    
    return jsonify([{
        'role': c.role,
        'content': c.content,
        'sent_at': c.sent_at.isoformat()
    } for c in conversations])

@study_bp.route('/chat/save', methods=['POST'])
@login_required
def save_chat_message():
    """Save a chat message"""
    data = request.json
    
    conversation = BotConversation(
        user_id=current_user.id,
        file_id=data.get('file_id'),
        role=data.get('role'),
        content=data.get('content')
    )
    db.session.add(conversation)
    db.session.commit()
    
    return jsonify({'success': True})

@study_bp.route('/chat/clear/<int:file_id>', methods=['POST'])
@login_required
def clear_chat_history(file_id):
    """Clear chat history for a file"""
    BotConversation.query.filter_by(
        user_id=current_user.id,
        file_id=file_id
    ).delete()
    db.session.commit()
    
    return jsonify({'success': True})

@study_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        try:
            content = extract_text_from_file(file, filename)
            
            if not content or len(content.strip()) < 10:
                return jsonify({'error': 'Could not extract text from file or file is empty'}), 400
            
            study_file = StudyFile(
                user_id=current_user.id,
                filename=filename,
                original_name=file.filename,
                content=content
            )
            db.session.add(study_file)
            db.session.commit()
            
            return jsonify({'success': True, 'file_id': study_file.id, 'filename': filename})
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 400
    
    return jsonify({'error': 'File type not allowed. Use .txt, .md, .docx, .pptx, .xlsx, or .pdf files'}), 400

from flask import session as flask_session

@study_bp.route('/bot/action', methods=['POST'])
@login_required
def bot_action():
    data = request.json
    file_id = data.get('file_id')
    action = data.get('action')  # 'quiz', 'question', 'ask'
    user_input = data.get('input', '')
    
    study_file = StudyFile.query.get(file_id)
    if not study_file or study_file.user_id != current_user.id:
        return jsonify({'error': 'File not found'}), 404
    
    # Get or create conversation history for this file
    history_key = f'bot_history_{current_user.id}_{file_id}'
    conversation_history = flask_session.get(history_key, [])
    
    # Create bot with history
    bot = StudyBot(study_file.content, conversation_history)
    
    if action == 'quiz':
        result = bot.generate_quiz()
    elif action == 'flashcards':
        result = bot.generate_flashcards()
    elif action == 'question':
        result = bot.ask_question()
    elif action == 'ask':
        result = bot.answer_question(user_input)
    elif action == 'check_answer':
        question = data.get('question', '')
        result = bot.check_answer(question, user_input)
    else:
        return jsonify({'error': 'Invalid action'}), 400
    
    # Save updated history back to session
    flask_session[history_key] = bot.get_history()
    
    return jsonify(result)

@study_bp.route('/bot/clear-memory/<int:file_id>', methods=['POST'])
@login_required
def clear_bot_memory(file_id):
    """Clear bot's conversation memory for a file"""
    history_key = f'bot_history_{current_user.id}_{file_id}'
    if history_key in flask_session:
        del flask_session[history_key]
    return jsonify({'success': True})

@study_bp.route('/track/quiz', methods=['POST'])
@login_required
def track_quiz():
    """Track quiz results for dashboard stats"""
    data = request.json
    file_id = data.get('file_id')
    total = data.get('total', 0)
    correct = data.get('correct', 0)
    
    study_file = StudyFile.query.get(file_id)
    topic = study_file.original_name if study_file else 'Quiz'
    
    # Create a study session record
    session = StudySession(
        user_id=current_user.id,
        topic=topic,
        duration_minutes=5,  # Estimate 5 mins per quiz
        questions_answered=total,
        correct_answers=correct,
        ended_at=datetime.utcnow()
    )
    db.session.add(session)
    db.session.commit()
    
    return jsonify({'success': True})

@study_bp.route('/session/start', methods=['POST'])
@login_required
def start_session():
    data = request.json
    session = StudySession(
        user_id=current_user.id,
        topic=data.get('topic', 'General Study')
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({'session_id': session.id})

@study_bp.route('/session/end', methods=['POST'])
@login_required
def end_session():
    data = request.json
    session = StudySession.query.get(data.get('session_id'))
    
    if session and session.user_id == current_user.id:
        session.ended_at = datetime.utcnow()
        session.duration_minutes = data.get('duration', 0)
        session.questions_answered = data.get('questions', 0)
        session.correct_answers = data.get('correct', 0)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Session not found'}), 404
