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
        
        # Safely add 'progress' column if it doesn't exist (to avoid drop_all)
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('meetings')]
            if 'progress' not in columns:
                print("Adding 'progress' column to meetings table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE meetings ADD progress INT DEFAULT 0"))
                    conn.commit()
                print("Column added successfully.")
        except Exception as e:
            print(f"Note: Could not automatically update schema: {e}")
            print("If the progress bar doesn't work, you may need to manually add the 'progress' column.")
        
        # Create a default user if none exists
        if User.query.filter_by(username='admin').first() is None:
            admin = User(
                username='admin',
                password=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin / admin123")
            
    app.run(debug=True, port=5000)
