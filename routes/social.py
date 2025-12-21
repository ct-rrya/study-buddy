"""
Social Routes - Friends, Chat with Friend Requests
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, Message, FriendRequest, ChatTheme

social_bp = Blueprint('social', __name__)

# Get socketio instance (will be set after app initialization)
def get_socketio():
    from app import socketio
    return socketio

@social_bp.route('/friends')
@login_required
def friends_page():
    friends = current_user.get_friends()
    pending_requests = current_user.get_pending_requests()
    sent_requests = current_user.get_sent_requests()
    
    # Get unread message counts and last message per friend
    unread_counts = {}
    last_messages = {}
    for friend in friends:
        count = Message.query.filter_by(
            sender_id=friend.id, 
            receiver_id=current_user.id, 
            read=False
        ).count()
        unread_counts[friend.id] = count
        
        # Get last message between users
        last_msg = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == friend.id)) |
            ((Message.sender_id == friend.id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.sent_at.desc()).first()
        last_messages[friend.id] = last_msg
    
    return render_template('friends.html', 
        friends=friends, 
        pending_requests=pending_requests,
        sent_requests=sent_requests,
        unread_counts=unread_counts,
        last_messages=last_messages
    )

@social_bp.route('/friends/search', methods=['POST'])
@login_required
def search_users():
    query = request.json.get('query', '')
    users = User.query.filter(
        User.username.ilike(f'%{query}%'),
        User.id != current_user.id
    ).limit(10).all()
    
    results = []
    for u in users:
        status = current_user.get_request_status(u)
        results.append({
            'id': u.id,
            'username': u.username,
            'is_friend': current_user.is_friend(u),
            'request_status': status
        })
    
    return jsonify(results)

@social_bp.route('/friends/request/<int:user_id>', methods=['POST'])
@login_required
def send_request(user_id):
    user = User.query.get(user_id)
    if user and user.id != current_user.id:
        if current_user.send_friend_request(user):
            db.session.commit()
            # Send real-time notification
            from routes.sockets import notify_friend_request
            notify_friend_request(get_socketio(), user_id, current_user)
            return jsonify({'success': True, 'message': 'Friend request sent!'})
        return jsonify({'error': 'Request already exists'}), 400
    return jsonify({'error': 'User not found'}), 404

@social_bp.route('/friends/accept/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    friend_request = FriendRequest.query.get(request_id)
    if friend_request and friend_request.receiver_id == current_user.id:
        friend_request.status = 'accepted'
        db.session.commit()
        # Notify the sender that their request was accepted
        from routes.sockets import notify_request_accepted
        notify_request_accepted(get_socketio(), friend_request.sender_id, current_user)
        return jsonify({'success': True})
    return jsonify({'error': 'Request not found'}), 404

@social_bp.route('/friends/decline/<int:request_id>', methods=['POST'])
@login_required
def decline_request(request_id):
    friend_request = FriendRequest.query.get(request_id)
    if friend_request and friend_request.receiver_id == current_user.id:
        friend_request.status = 'declined'
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Request not found'}), 404

@social_bp.route('/friends/cancel/<int:request_id>', methods=['POST'])
@login_required
def cancel_request(request_id):
    friend_request = FriendRequest.query.get(request_id)
    if friend_request and friend_request.sender_id == current_user.id:
        db.session.delete(friend_request)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Request not found'}), 404

@social_bp.route('/friends/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_friend(user_id):
    # Find and delete the friend request (which represents the friendship)
    friend_request = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == current_user.id))
    ).first()
    
    if friend_request:
        db.session.delete(friend_request)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Friendship not found'}), 404

@social_bp.route('/chat/<int:friend_id>')
@login_required
def chat_page(friend_id):
    friend = User.query.get(friend_id)
    if not friend or not current_user.is_friend(friend):
        return redirect(url_for('social.friends_page'))
    
    # Get chat history
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.sent_at.asc()).all()
    
    # Mark messages as read
    Message.query.filter_by(sender_id=friend_id, receiver_id=current_user.id, read=False)\
        .update({'read': True})
    db.session.commit()
    
    # Get per-conversation chat theme
    chat_theme = ChatTheme.query.filter_by(
        user_id=current_user.id, friend_id=friend_id
    ).first()
    theme = chat_theme.theme if chat_theme else 'purple'
    
    return render_template('chat.html', friend=friend, messages=messages, chat_theme=theme)

@social_bp.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    data = request.json
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    receiver = User.query.get(receiver_id)
    if not receiver or not current_user.is_friend(receiver):
        return jsonify({'error': 'You can only message friends'}), 403
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'sent_at': message.sent_at.isoformat()
        }
    })

@social_bp.route('/chat/messages/<int:friend_id>')
@login_required
def get_messages(friend_id):
    """Get new messages for polling"""
    last_id = request.args.get('last_id', 0, type=int)
    
    messages = Message.query.filter(
        Message.id > last_id,
        ((Message.sender_id == current_user.id) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.sent_at.asc()).all()
    
    return jsonify([{
        'id': m.id,
        'content': m.content,
        'sender_id': m.sender_id,
        'sent_at': m.sent_at.isoformat()
    } for m in messages])

@social_bp.route('/chat/theme/<int:friend_id>', methods=['POST'])
@login_required
def set_chat_theme(friend_id):
    """Set chat theme for a specific conversation"""
    theme = request.json.get('theme', 'purple')
    valid_themes = ['purple', 'blue', 'green', 'pink', 'orange', 'cyan']
    
    if theme not in valid_themes:
        return jsonify({'error': 'Invalid theme'}), 400
    
    # Find or create chat theme for this conversation
    chat_theme = ChatTheme.query.filter_by(
        user_id=current_user.id, friend_id=friend_id
    ).first()
    
    if chat_theme:
        chat_theme.theme = theme
    else:
        chat_theme = ChatTheme(
            user_id=current_user.id,
            friend_id=friend_id,
            theme=theme
        )
        db.session.add(chat_theme)
    
    db.session.commit()
    return jsonify({'success': True, 'theme': theme})
