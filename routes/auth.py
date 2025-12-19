"""
Authentication Routes - Login, Register, Logout, Email Verification, Password Reset
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from models import db, User
from datetime import datetime, timedelta
import secrets

auth_bp = Blueprint('auth', __name__)
mail = Mail()

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            if user.email_verified != True:
                flash('Please verify your email first. Check your inbox!', 'error')
                return render_template('login.html')
            login_user(user)
            return redirect(url_for('dashboard.home'))
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Generate verification token
        token = secrets.token_urlsafe(32)
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            verification_token=token,
            email_verified=True  # Auto-verify for now (Render blocks SMTP)
        )
        db.session.add(user)
        db.session.commit()
        
        # TODO: Re-enable email verification when using a proper email service
        # For now, auto-verify since Render free tier blocks SMTP
        flash('Registration successful! You can now login.', 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

def send_verification_email(user, token):
    """Send email verification link"""
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    
    msg = Message(
        'Verify your Study Buddy account',
        recipients=[user.email]
    )
    msg.html = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #8b5cf6;">Welcome to Study Buddy! 📚</h2>
        <p>Hey {user.username}!</p>
        <p>Thanks for signing up! Please verify your email by clicking the button below:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{verify_url}" style="background: linear-gradient(135deg, #8b5cf6, #6366f1); color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                Verify Email
            </a>
        </p>
        <p style="color: #666; font-size: 14px;">Or copy this link: {verify_url}</p>
        <p style="color: #666; font-size: 12px; margin-top: 30px;">If you didn't create this account, you can ignore this email.</p>
    </div>
    '''
    mail.send(msg)

@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Verify email with token"""
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('auth.login'))
    
    user.email_verified = True
    user.verification_token = None
    db.session.commit()
    
    flash('Email verified! You can now login.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    
    if user and not user.email_verified:
        token = secrets.token_urlsafe(32)
        user.verification_token = token
        db.session.commit()
        
        try:
            send_verification_email(user, token)
            flash('Verification email sent! Check your inbox.', 'success')
        except:
            flash('Could not send email. Try again later.', 'error')
    else:
        flash('Email not found or already verified.', 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            try:
                send_reset_email(user, token)
                flash('Password reset link sent to your email!', 'success')
            except Exception as e:
                print(f"Email error: {e}")
                flash('Could not send email. Try again later.', 'error')
        else:
            # Don't reveal if email exists
            flash('If that email exists, a reset link has been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('forgot_password.html')

def send_reset_email(user, token):
    """Send password reset link"""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    msg = Message(
        'Reset your Study Buddy password',
        recipients=[user.email]
    )
    msg.html = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #8b5cf6;">Password Reset 🔐</h2>
        <p>Hey {user.username}!</p>
        <p>We received a request to reset your password. Click the button below to set a new one:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background: linear-gradient(135deg, #8b5cf6, #6366f1); color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                Reset Password
            </a>
        </p>
        <p style="color: #666; font-size: 14px;">Or copy this link: {reset_url}</p>
        <p style="color: #666; font-size: 12px;">This link expires in 1 hour.</p>
        <p style="color: #666; font-size: 12px; margin-top: 30px;">If you didn't request this, you can ignore this email.</p>
    </div>
    '''
    mail.send(msg)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('reset_password.html', token=token)
        
        user.password_hash = generate_password_hash(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Password reset successful! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', token=token)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    data = request.form
    
    new_username = data.get('username', '').strip()
    if new_username and new_username != current_user.username:
        # Check if username is taken
        existing = User.query.filter_by(username=new_username).first()
        if existing:
            flash('Username already taken', 'error')
            return redirect(url_for('auth.profile'))
        current_user.username = new_username
    
    current_user.bio = data.get('bio', '')[:200]
    
    db.session.commit()
    flash('Profile updated!', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/profile/avatar', methods=['POST'])
@login_required
def update_avatar():
    data = request.json
    
    current_user.avatar_type = data.get('type', 'dicebear')
    current_user.avatar_style = data.get('style', 'avataaars')
    current_user.avatar_seed = data.get('seed', current_user.username)
    
    db.session.commit()
    return jsonify({'success': True, 'avatar_url': current_user.get_avatar_url()})

@auth_bp.route('/profile/theme', methods=['POST'])
@login_required
def update_theme():
    data = request.json
    theme = data.get('theme', 'purple')
    
    if theme in ['purple', 'blue', 'green', 'pink', 'orange', 'cyan']:
        current_user.chat_theme = theme
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid theme'}), 400
