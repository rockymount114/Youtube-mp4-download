import os
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Ensure tables exist
        print("Initializing database...")
        db.create_all()
        
        # Safely add columns if they don't exist
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            
            # Check meetings table
            meeting_cols = [c['name'] for c in inspector.get_columns('meetings')]
            if 'progress' not in meeting_cols:
                print("Adding 'progress' column to meetings table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE meetings ADD progress INT DEFAULT 0"))
                    conn.commit()
            
            # Check user table for is_admin
            user_cols = [c['name'] for c in inspector.get_columns('user')]
            if 'is_admin' not in user_cols:
                print("Adding 'is_admin' column to user table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE [user] ADD is_admin BIT DEFAULT 0"))
                    conn.commit()
                print("Column added successfully.")
        except Exception as e:
            print(f"Note: Could not automatically update schema: {e}")
        
        # Create a default user if none exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user is None:
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin / admin123")
        elif not admin_user.is_admin:
            # Ensure the default 'admin' user actually has admin rights
            admin_user.is_admin = True
            db.session.commit()
            print("Admin rights granted to existing 'admin' user.")
            
    app.run(debug=True, port=5500)
