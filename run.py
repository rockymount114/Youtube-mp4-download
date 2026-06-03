import os
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Refresh schema to fix column length issues
        print("Refreshing database schema...")
        db.drop_all()
        db.create_all()
        
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
