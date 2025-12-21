"""
Social Routes - Friends, Chat with Friend Requests
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import db, User, Message, FriendRequest, ChatTheme, GroupChat, GroupMessage

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
    
    # Get user's group chats
    group_chats = GroupChat.query.filter(
        GroupChat.members.any(id=current_user.id)
    ).all()
    
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
        last_messages=last_messages,
        group_chats=group_chats
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
        return jsonify({
            'success': True,
            'friend_id': friend_request.sender_id
        })
    return jsonify({'error': 'Request not found'}), 404


@social_bp.route('/friends/get-friend-card/<int:friend_id>')
@login_required
def get_friend_card(friend_id):
    """Get friend data for dynamic card creation"""
    friend = User.query.get(friend_id)
    if not friend or not current_user.is_friend(friend):
        return jsonify({'error': 'Friend not found'}), 404
    
    return jsonify({
        'success': True,
        'friend': {
            'id': friend.id,
            'username': friend.username,
            'avatar_url': friend.get_avatar_url()
        }
    })

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


# Group Chat Routes
@social_bp.route('/groups/create', methods=['POST'])
@login_required
def create_group():
    """Create a new group chat"""
    data = request.json
    name = data.get('name', '').strip()
    member_ids = data.get('member_ids', [])
    
    if not name:
        return jsonify({'error': 'Group name is required'}), 400
    
    if len(member_ids) < 2:
        return jsonify({'error': 'Select at least 2 friends'}), 400
    
    # Verify all members are friends
    friends = current_user.get_friends()
    friend_ids = [f.id for f in friends]
    
    for member_id in member_ids:
        if member_id not in friend_ids:
            return jsonify({'error': 'You can only add friends to groups'}), 400
    
    # Create the group
    group = GroupChat(
        name=name,
        creator_id=current_user.id
    )
    
    # Add creator and selected members
    group.members.append(current_user)
    for member_id in member_ids:
        member = User.query.get(member_id)
        if member:
            group.members.append(member)
    
    db.session.add(group)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'group_id': group.id,
        'name': group.name,
        'member_count': len(group.members)
    })


@social_bp.route('/groups/<int:group_id>')
@login_required
def group_chat_page(group_id):
    """Group chat page"""
    group = GroupChat.query.get(group_id)
    
    if not group or current_user not in group.members:
        return redirect(url_for('social.friends_page'))
    
    # Get messages
    messages = GroupMessage.query.filter_by(group_id=group_id)\
        .order_by(GroupMessage.sent_at.asc()).all()
    
    return render_template('group_chat.html', group=group, messages=messages)


@social_bp.route('/groups/<int:group_id>/send', methods=['POST'])
@login_required
def send_group_message(group_id):
    """Send a message to a group"""
    group = GroupChat.query.get(group_id)
    
    if not group or current_user not in group.members:
        return jsonify({'error': 'Not a member of this group'}), 403
    
    content = request.json.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    message = GroupMessage(
        group_id=group_id,
        sender_id=current_user.id,
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender_id,
            'sender_name': current_user.username,
            'sender_avatar': current_user.get_avatar_url(),
            'sent_at': message.sent_at.isoformat()
        }
    })


@social_bp.route('/groups/<int:group_id>/messages')
@login_required
def get_group_messages(group_id):
    """Get new group messages for polling"""
    group = GroupChat.query.get(group_id)
    
    if not group or current_user not in group.members:
        return jsonify({'error': 'Not a member'}), 403
    
    last_id = request.args.get('last_id', 0, type=int)
    
    messages = GroupMessage.query.filter(
        GroupMessage.group_id == group_id,
        GroupMessage.id > last_id
    ).order_by(GroupMessage.sent_at.asc()).all()
    
    return jsonify([{
        'id': m.id,
        'content': m.content,
        'sender_id': m.sender_id,
        'sender_name': m.sender.username,
        'sender_avatar': m.sender.get_avatar_url(),
        'sent_at': m.sent_at.isoformat()
    } for m in messages])


@social_bp.route('/groups/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    """Leave a group chat"""
    group = GroupChat.query.get(group_id)
    
    if not group or current_user not in group.members:
        return jsonify({'error': 'Not a member'}), 403
    
    group.members.remove(current_user)
    
    # If no members left, delete the group
    if len(group.members) == 0:
        db.session.delete(group)
    
    db.session.commit()
    return jsonify({'success': True})


@social_bp.route('/groups/<int:group_id>/settings', methods=['POST'])
@login_required
def update_group_settings(group_id):
    """Update group settings (theme, avatar, name)"""
    import base64
    import os
    import uuid
    
    group = GroupChat.query.get(group_id)
    
    if not group or current_user not in group.members:
        return jsonify({'error': 'Not a member'}), 403
    
    data = request.json
    print(f"[DEBUG] Received settings update for group {group_id}")
    print(f"[DEBUG] Keys in data: {list(data.keys())}")
    
    # Update theme if provided
    theme = data.get('theme')
    if theme:
        valid_themes = ['purple', 'blue', 'green', 'pink', 'orange', 'cyan']
        if theme in valid_themes:
            group.theme = theme
            print(f"[DEBUG] Theme updated to: {theme}")
    
    # Handle base64 image upload
    avatar_data = data.get('avatar_data')
    if avatar_data:
        print(f"[DEBUG] Received avatar_data, length: {len(avatar_data)}")
        try:
            # Parse base64 data URL
            if ',' in avatar_data:
                header, encoded = avatar_data.split(',', 1)
                print(f"[DEBUG] Header: {header[:50]}...")
                
                # Get file extension from header
                ext = 'png'
                if 'jpeg' in header or 'jpg' in header:
                    ext = 'jpg'
                elif 'gif' in header:
                    ext = 'gif'
                elif 'webp' in header:
                    ext = 'webp'
                
                # Decode and save
                image_data = base64.b64decode(encoded)
                print(f"[DEBUG] Decoded image size: {len(image_data)} bytes")
                
                # Create uploads directory if needed
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'groups')
                os.makedirs(upload_dir, exist_ok=True)
                print(f"[DEBUG] Upload dir: {upload_dir}")
                
                # Generate unique filename
                filename = f"group_{group_id}_{uuid.uuid4().hex[:8]}.{ext}"
                filepath = os.path.join(upload_dir, filename)
                
                # Delete old avatar if exists
                if group.avatar_url and 'uploads/groups/' in group.avatar_url:
                    old_path = os.path.join(current_app.root_path, 'static', group.avatar_url.replace('/static/', ''))
                    if os.path.exists(old_path):
                        os.remove(old_path)
                        print(f"[DEBUG] Deleted old avatar: {old_path}")
                
                # Save new image
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                print(f"[DEBUG] Saved new avatar: {filepath}")
                
                group.avatar_url = f"/static/uploads/groups/{filename}"
                print(f"[DEBUG] Set avatar_url to: {group.avatar_url}")
        except Exception as e:
            print(f"[ERROR] Error saving group avatar: {e}")
            import traceback
            traceback.print_exc()
    elif data.get('avatar_url') == '':
        # Clear avatar
        print("[DEBUG] Clearing avatar")
        if group.avatar_url and 'uploads/groups/' in group.avatar_url:
            old_path = os.path.join(current_app.root_path, 'static', group.avatar_url.replace('/static/', ''))
            if os.path.exists(old_path):
                os.remove(old_path)
        group.avatar_url = None
    
    # Update name if provided
    name = data.get('name', '').strip()
    if name:
        group.name = name
        print(f"[DEBUG] Name updated to: {name}")
    
    db.session.commit()
    print(f"[DEBUG] Committed. Final avatar_url: {group.avatar_url}")
    
    return jsonify({
        'success': True,
        'theme': group.theme,
        'avatar_url': group.avatar_url,
        'name': group.name
    })
