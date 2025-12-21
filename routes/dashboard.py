"""
Dashboard Routes - Home, Stats, Progress
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, StudySession, Subject, SubjectProgress, ICONOIR_SUBJECT_ICONS
import random

dashboard_bp = Blueprint('dashboard', __name__)

MOTIVATIONS = [
    "Every expert was once a beginner. Keep going! 🚀",
    "Small progress is still progress. You've got this! 💪",
    "Your future self will thank you for studying today! 📚",
    "Believe in yourself - you're doing amazing! ⭐",
    "One page at a time, one concept at a time. You're building greatness! 🏗️",
    "The only bad study session is the one that didn't happen! 🎯",
    "You're not just studying, you're investing in yourself! 💎",
    "Champions are made when no one is watching. Keep grinding! 🏆"
]

MEMES = [
    "Me: I'll study for 5 minutes. *3 hours later* Still on the same page 😅",
    "Brain before exam: I know nothing. Brain at 3am: Here's a random memory from 2015 🧠",
    "Study tip: Crying counts as studying if it's about the material 📖😭",
    "Me: Opens textbook. Textbook: You dare approach me? 📚⚔️"
]

@dashboard_bp.route('/home')
@login_required
def home():
    # Get user's study stats
    total_sessions = StudySession.query.filter_by(user_id=current_user.id).count()
    
    # Calculate streak
    streak = calculate_streak(current_user.id)
    
    # Get today's motivation based on user history
    motivation = get_personalized_motivation(total_sessions, streak)
    meme = random.choice(MEMES)
    
    return render_template('home.html', 
        motivation=motivation,
        meme=meme,
        streak=streak,
        total_sessions=total_sessions
    )

@dashboard_bp.route('/dashboard')
@login_required
def stats():
    # Get detailed stats
    sessions = StudySession.query.filter_by(user_id=current_user.id)\
        .order_by(StudySession.started_at.desc()).limit(10).all()
    
    all_sessions = StudySession.query.filter_by(user_id=current_user.id).all()
    
    total_minutes = sum(s.duration_minutes or 0 for s in all_sessions)
    total_questions = sum(s.questions_answered or 0 for s in all_sessions)
    correct_answers = sum(s.correct_answers or 0 for s in all_sessions)
    accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Get weekly data for chart (last 7 days)
    weekly_data = get_weekly_chart_data(current_user.id)
    
    # Get user's subjects with progress
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    subject_data = []
    for subject in subjects:
        progress = SubjectProgress.query.filter_by(
            user_id=current_user.id, 
            subject_id=subject.id
        ).first()
        subject_data.append({
            'id': subject.id,
            'name': subject.name,
            'icon': subject.icon,
            'iconoir_icon': subject.iconoir_icon,
            'color': subject.color,
            'questions': progress.questions_answered if progress else 0,
            'correct': progress.correct_answers if progress else 0,
            'minutes': progress.study_minutes if progress else 0,
            'sessions': progress.sessions_count if progress else 0,
            'accuracy': round((progress.correct_answers / progress.questions_answered * 100), 1) if progress and progress.questions_answered > 0 else 0
        })
    
    return render_template('dashboard.html',
        sessions=sessions,
        total_minutes=total_minutes,
        total_questions=total_questions,
        accuracy=round(accuracy, 1),
        streak=calculate_streak(current_user.id),
        weekly_data=weekly_data,
        subjects=subject_data,
        default_subjects=Subject.DEFAULT_SUBJECTS
    )


def get_weekly_chart_data(user_id):
    """Get study data for the last 7 days"""
    today = datetime.utcnow().date()
    data = {
        'labels': [],
        'questions': [],
        'correct': [],
        'minutes': []
    }
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        sessions = StudySession.query.filter(
            StudySession.user_id == user_id,
            StudySession.started_at >= day_start,
            StudySession.started_at <= day_end
        ).all()
        
        data['labels'].append(day.strftime('%a'))
        data['questions'].append(sum(s.questions_answered or 0 for s in sessions))
        data['correct'].append(sum(s.correct_answers or 0 for s in sessions))
        data['minutes'].append(sum(s.duration_minutes or 0 for s in sessions))
    
    return data


@dashboard_bp.route('/subjects', methods=['GET'])
@login_required
def get_subjects():
    """Get user's subjects"""
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'icon': s.icon,
        'iconoir_icon': s.iconoir_icon,
        'color': s.color
    } for s in subjects])


@dashboard_bp.route('/subjects/add', methods=['POST'])
@login_required
def add_subject():
    """Add a new subject"""
    data = request.json
    name = data.get('name', '').strip()
    icon = data.get('icon', '📚')
    color = data.get('color', '#8b5cf6')
    # Get iconoir icon from mapping or use default
    iconoir_icon = data.get('iconoir', ICONOIR_SUBJECT_ICONS.get(name, ICONOIR_SUBJECT_ICONS['default']))
    
    if not name:
        return jsonify({'error': 'Subject name is required'}), 400
    
    # Check if subject already exists
    existing = Subject.query.filter_by(user_id=current_user.id, name=name).first()
    if existing:
        return jsonify({'error': 'Subject already exists'}), 400
    
    subject = Subject(
        user_id=current_user.id,
        name=name,
        icon=icon,
        iconoir_icon=iconoir_icon,
        color=color
    )
    db.session.add(subject)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'subject': {
            'id': subject.id,
            'name': subject.name,
            'icon': subject.icon,
            'iconoir_icon': subject.iconoir_icon,
            'color': subject.color
        }
    })


@dashboard_bp.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    """Delete a subject"""
    subject = Subject.query.get(subject_id)
    if not subject or subject.user_id != current_user.id:
        return jsonify({'error': 'Subject not found'}), 404
    
    # Delete associated progress
    SubjectProgress.query.filter_by(subject_id=subject_id).delete()
    db.session.delete(subject)
    db.session.commit()
    
    return jsonify({'success': True})

def calculate_streak(user_id):
    """Calculate consecutive days of studying"""
    sessions = StudySession.query.filter_by(user_id=user_id)\
        .order_by(StudySession.started_at.desc()).all()
    
    if not sessions:
        return 0
    
    streak = 0
    current_date = datetime.utcnow().date()
    
    # Check if studied today
    last_session_date = sessions[0].started_at.date()
    if last_session_date < current_date - timedelta(days=1):
        return 0
    
    checked_dates = set()
    for session in sessions:
        session_date = session.started_at.date()
        if session_date not in checked_dates:
            if session_date == current_date - timedelta(days=len(checked_dates)):
                streak += 1
                checked_dates.add(session_date)
            else:
                break
    
    return streak

def get_personalized_motivation(total_sessions, streak):
    """Get motivation based on user's history"""
    if total_sessions == 0:
        return "Welcome! Ready to start your learning journey? Let's go! 🎉"
    elif streak >= 7:
        return f"🔥 {streak} day streak! You're absolutely crushing it! Keep the momentum!"
    elif streak >= 3:
        return f"💪 {streak} days in a row! You're building great habits!"
    else:
        return random.choice(MOTIVATIONS)
