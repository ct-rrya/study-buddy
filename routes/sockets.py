"""
Socket.IO Events - Real-time communication
"""
from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from models import db, Message, User

# Store connected users: {user_id: sid}
connected_users = {}

def register_socket_events(socketio):
    
    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            connected_users[current_user.id] = request.sid
            # Join a personal room for notifications
            join_room(f'user_{current_user.id}')
            emit('connected', {'user_id': current_user.id})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            connected_users.pop(current_user.id, None)
            leave_room(f'user_{current_user.id}')
    
    @socketio.on('join_chat')
    def handle_join_chat(data):
        """Join a chat room with a friend"""
        friend_id = data.get('friend_id')
        if current_user.is_authenticated and friend_id:
            # Create a unique room for this conversation
            room = get_chat_room(current_user.id, friend_id)
            join_room(room)
            emit('joined_chat', {'room': room})
    
    @socketio.on('leave_chat')
    def handle_leave_chat(data):
        """Leave a chat room"""
        friend_id = data.get('friend_id')
        if current_user.is_authenticated and friend_id:
            room = get_chat_room(current_user.id, friend_id)
            leave_room(room)
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle real-time message sending"""
        if not current_user.is_authenticated:
            return
        
        receiver_id = data.get('receiver_id')
        content = data.get('content', '').strip()
        
        if not content or not receiver_id:
            return
        
        receiver = User.query.get(receiver_id)
        if not receiver or not current_user.is_friend(receiver):
            return
        
        # Save message to database
        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        
        # Prepare message data
        msg_data = {
            'id': message.id,
            'content': message.content,
            'sender_id': current_user.id,
            'sender_username': current_user.username,
            'sent_at': message.sent_at.isoformat(),
            'sent_at_formatted': message.sent_at.strftime('%H:%M')
        }
        
        # Send to the chat room (both users will receive it)
        room = get_chat_room(current_user.id, receiver_id)
        emit('new_message', msg_data, room=room)
        
        # Also notify the receiver if they're not in the chat room
        emit('message_notification', {
            'from_user': current_user.username,
            'from_id': current_user.id,
            'preview': content[:50] + ('...' if len(content) > 50 else '')
        }, room=f'user_{receiver_id}')
    
    @socketio.on('typing')
    def handle_typing(data):
        """Broadcast typing indicator"""
        if not current_user.is_authenticated:
            return
        
        friend_id = data.get('friend_id')
        if friend_id:
            room = get_chat_room(current_user.id, friend_id)
            emit('user_typing', {
                'user_id': current_user.id,
                'username': current_user.username
            }, room=room, include_self=False)
    
    @socketio.on('stop_typing')
    def handle_stop_typing(data):
        """Broadcast stop typing indicator"""
        if not current_user.is_authenticated:
            return
        
        friend_id = data.get('friend_id')
        if friend_id:
            room = get_chat_room(current_user.id, friend_id)
            emit('user_stop_typing', {
                'user_id': current_user.id
            }, room=room, include_self=False)


def get_chat_room(user1_id, user2_id):
    """Generate a consistent room name for two users"""
    ids = sorted([user1_id, user2_id])
    return f'chat_{ids[0]}_{ids[1]}'


def notify_friend_request(socketio, receiver_id, sender):
    """Send real-time friend request notification"""
    socketio.emit('friend_request', {
        'sender_id': sender.id,
        'sender_username': sender.username,
        'sender_avatar': sender.get_avatar_url()
    }, room=f'user_{receiver_id}')


def notify_request_accepted(socketio, sender_id, accepter):
    """Notify when friend request is accepted"""
    socketio.emit('request_accepted', {
        'friend_id': accepter.id,
        'friend_username': accepter.username,
        'friend_avatar': accepter.get_avatar_url()
    }, room=f'user_{sender_id}')
