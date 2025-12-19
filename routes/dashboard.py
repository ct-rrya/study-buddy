"""
Dashboard Routes - Home, Stats, Progress
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import StudySession
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
    
    total_minutes = sum(s.duration_minutes or 0 for s in 
        StudySession.query.filter_by(user_id=current_user.id).all())
    
    total_questions = sum(s.questions_answered or 0 for s in 
        StudySession.query.filter_by(user_id=current_user.id).all())
    
    correct_answers = sum(s.correct_answers or 0 for s in 
        StudySession.query.filter_by(user_id=current_user.id).all())
    
    accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    return render_template('dashboard.html',
        sessions=sessions,
        total_minutes=total_minutes,
        total_questions=total_questions,
        accuracy=round(accuracy, 1),
        streak=calculate_streak(current_user.id)
    )

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
