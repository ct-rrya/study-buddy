"""
Database Models
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class ChatTheme(db.Model):
    """Per-conversation chat theme for each user"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    theme = db.Column(db.String(20), default='purple')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'friend_id'),)

class FriendRequest(db.Model):
    """Friend request with pending/accepted/declined status"""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bio = db.Column(db.String(200), default='')
    avatar_type = db.Column(db.String(20), default='dicebear')  # 'dicebear' or 'custom'
    avatar_style = db.Column(db.String(30), default='avataaars')  # DiceBear style
    avatar_seed = db.Column(db.String(50))  # Seed for DiceBear or custom URL
    chat_theme = db.Column(db.String(20), default='purple')  # Chat bubble color theme
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    
    def get_avatar_url(self):
        """Get the avatar URL"""
        if self.avatar_type == 'custom' and self.avatar_seed:
            return self.avatar_seed
        # DiceBear avatar
        seed = self.avatar_seed or self.username
        style = self.avatar_style or 'avataaars'
        return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}"
    
    # Relationships
    study_sessions = db.relationship('StudySession', backref='user', lazy=True)
    uploaded_files = db.relationship('StudyFile', backref='user', lazy=True)

    def get_friends(self):
        """Get all accepted friends"""
        # Friends where I sent the request and they accepted
        sent_accepted = FriendRequest.query.filter_by(
            sender_id=self.id, status='accepted'
        ).all()
        # Friends where they sent the request and I accepted
        received_accepted = FriendRequest.query.filter_by(
            receiver_id=self.id, status='accepted'
        ).all()
        
        friend_ids = [r.receiver_id for r in sent_accepted] + [r.sender_id for r in received_accepted]
        return User.query.filter(User.id.in_(friend_ids)).all() if friend_ids else []
    
    def get_pending_requests(self):
        """Get pending friend requests received"""
        return FriendRequest.query.filter_by(receiver_id=self.id, status='pending').all()
    
    def get_sent_requests(self):
        """Get pending friend requests sent"""
        return FriendRequest.query.filter_by(sender_id=self.id, status='pending').all()
    
    def send_friend_request(self, user):
        """Send a friend request"""
        if self.id == user.id:
            return False
        # Check if request already exists
        existing = FriendRequest.query.filter(
            ((FriendRequest.sender_id == self.id) & (FriendRequest.receiver_id == user.id)) |
            ((FriendRequest.sender_id == user.id) & (FriendRequest.receiver_id == self.id))
        ).first()
        if existing:
            return False
        request = FriendRequest(sender_id=self.id, receiver_id=user.id)
        db.session.add(request)
        return True
    
    def is_friend(self, user):
        """Check if users are friends (accepted)"""
        return FriendRequest.query.filter(
            ((FriendRequest.sender_id == self.id) & (FriendRequest.receiver_id == user.id) & (FriendRequest.status == 'accepted')) |
            ((FriendRequest.sender_id == user.id) & (FriendRequest.receiver_id == self.id) & (FriendRequest.status == 'accepted'))
        ).count() > 0
    
    def get_request_status(self, user):
        """Get friendship status with another user"""
        request = FriendRequest.query.filter(
            ((FriendRequest.sender_id == self.id) & (FriendRequest.receiver_id == user.id)) |
            ((FriendRequest.sender_id == user.id) & (FriendRequest.receiver_id == self.id))
        ).first()
        if not request:
            return None
        return {
            'status': request.status,
            'is_sender': request.sender_id == self.id
        }
    
    def get_unread_message_count(self):
        """Get total unread messages"""
        return Message.query.filter_by(receiver_id=self.id, read=False).count()
    
    def get_pending_request_count(self):
        """Get pending friend request count"""
        return FriendRequest.query.filter_by(receiver_id=self.id, status='pending').count()
    
    def get_notification_count(self):
        """Get total notifications (requests + unread messages)"""
        return self.get_pending_request_count() + self.get_unread_message_count()

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(200))
    duration_minutes = db.Column(db.Integer, default=0)
    questions_answered = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

class StudyFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)  # Extracted text content
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    subject = db.relationship('Subject', backref='files')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

class BotConversation(db.Model):
    """Stores chat history between user and study bot"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('study_file.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='bot_conversations')
    file = db.relationship('StudyFile', backref='conversations')


# Subject icon mapping to Iconoir icon names
ICONOIR_SUBJECT_ICONS = {
    'Mathematics': 'calculator',
    'English': 'language',
    'Science': 'flask',
    'History': 'archive',
    'Geography': 'globe',
    'Physics': 'atom',
    'Chemistry': 'test-tube',
    'Biology': 'dna',
    'Computer Science': 'code',
    'Literature': 'book',
    'Art': 'palette',
    'Music': 'music-double-note',
    'default': 'book-stack'
}


class Subject(db.Model):
    """User's study subjects"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20), default='#8b5cf6')  # Hex color for charts
    icon = db.Column(db.String(50), default='📚')  # Emoji icon
    iconoir_icon = db.Column(db.String(50), default='book-stack')  # Iconoir icon name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='subjects')
    
    # Default subjects that users can choose from (with Iconoir icon names)
    DEFAULT_SUBJECTS = [
        {'name': 'Mathematics', 'icon': '📐', 'iconoir': 'calculator', 'color': '#3b82f6'},
        {'name': 'English', 'icon': '📝', 'iconoir': 'language', 'color': '#10b981'},
        {'name': 'Science', 'icon': '🔬', 'iconoir': 'flask', 'color': '#8b5cf6'},
        {'name': 'History', 'icon': '📜', 'iconoir': 'archive', 'color': '#f59e0b'},
        {'name': 'Geography', 'icon': '🌍', 'iconoir': 'globe', 'color': '#06b6d4'},
        {'name': 'Physics', 'icon': '⚛️', 'iconoir': 'atom', 'color': '#6366f1'},
        {'name': 'Chemistry', 'icon': '🧪', 'iconoir': 'test-tube', 'color': '#ec4899'},
        {'name': 'Biology', 'icon': '🧬', 'iconoir': 'dna', 'color': '#14b8a6'},
        {'name': 'Computer Science', 'icon': '💻', 'iconoir': 'code', 'color': '#64748b'},
        {'name': 'Literature', 'icon': '📖', 'iconoir': 'book', 'color': '#a855f7'},
        {'name': 'Art', 'icon': '🎨', 'iconoir': 'palette', 'color': '#f43f5e'},
        {'name': 'Music', 'icon': '🎵', 'iconoir': 'music-double-note', 'color': '#eab308'},
    ]


class SubjectProgress(db.Model):
    """Track progress per subject"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    questions_answered = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    study_minutes = db.Column(db.Integer, default=0)
    sessions_count = db.Column(db.Integer, default=0)
    last_studied = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='subject_progress')
    subject = db.relationship('Subject', backref='progress_records')


# Association table for group chat members
group_members = db.Table('group_members',
    db.Column('group_id', db.Integer, db.ForeignKey('group_chat.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)


class GroupChat(db.Model):
    """Group chat with multiple members"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    theme = db.Column(db.String(20), default='purple')  # Chat theme color
    avatar_url = db.Column(db.String(500))  # Group photo URL
    
    creator = db.relationship('User', foreign_keys=[creator_id])
    members = db.relationship('User', secondary=group_members, backref='group_chats')
    messages = db.relationship('GroupMessage', backref='group', lazy='dynamic', cascade='all, delete-orphan')


class GroupMessage(db.Model):
    """Messages in a group chat"""
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group_chat.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id])
