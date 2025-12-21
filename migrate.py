"""
Database Migration Script - Add new tables and columns
Run this once to update your database schema
"""
from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        # Add subject_id column to study_file if it doesn't exist
        try:
            db.session.execute(text("""
                ALTER TABLE study_file 
                ADD COLUMN IF NOT EXISTS subject_id INTEGER REFERENCES subject(id)
            """))
            print("✓ Added subject_id to study_file")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create subject table if it doesn't exist
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS subject (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES "user"(id),
                    name VARCHAR(100) NOT NULL,
                    color VARCHAR(20) DEFAULT '#8b5cf6',
                    icon VARCHAR(50) DEFAULT '📚',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✓ Created subject table")
        except Exception as e:
            print(f"Note: {e}")
        
        # Add iconoir_icon column to subject table if it doesn't exist
        try:
            db.session.execute(text("""
                ALTER TABLE subject 
                ADD COLUMN IF NOT EXISTS iconoir_icon VARCHAR(50) DEFAULT 'book-stack'
            """))
            print("✓ Added iconoir_icon to subject table")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create subject_progress table if it doesn't exist
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS subject_progress (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES "user"(id),
                    subject_id INTEGER NOT NULL REFERENCES subject(id),
                    questions_answered INTEGER DEFAULT 0,
                    correct_answers INTEGER DEFAULT 0,
                    study_minutes INTEGER DEFAULT 0,
                    sessions_count INTEGER DEFAULT 0,
                    last_studied TIMESTAMP
                )
            """))
            print("✓ Created subject_progress table")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create group_chat table if it doesn't exist
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS group_chat (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    creator_id INTEGER NOT NULL REFERENCES "user"(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    theme VARCHAR(20) DEFAULT 'purple',
                    avatar_url VARCHAR(500)
                )
            """))
            print("✓ Created group_chat table")
        except Exception as e:
            print(f"Note: {e}")
        
        # Add theme and avatar_url columns to group_chat if they don't exist
        try:
            db.session.execute(text("""
                ALTER TABLE group_chat 
                ADD COLUMN IF NOT EXISTS theme VARCHAR(20) DEFAULT 'purple'
            """))
            db.session.execute(text("""
                ALTER TABLE group_chat 
                ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)
            """))
            print("✓ Added theme and avatar_url to group_chat")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create group_members association table if it doesn't exist
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS group_members (
                    group_id INTEGER NOT NULL REFERENCES group_chat(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (group_id, user_id)
                )
            """))
            print("✓ Created group_members table")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create group_message table if it doesn't exist
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS group_message (
                    id SERIAL PRIMARY KEY,
                    group_id INTEGER NOT NULL REFERENCES group_chat(id) ON DELETE CASCADE,
                    sender_id INTEGER NOT NULL REFERENCES "user"(id),
                    content TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✓ Created group_message table")
        except Exception as e:
            print(f"Note: {e}")
        
        db.session.commit()
        print("\n✅ Migration complete!")

if __name__ == '__main__':
    migrate()
