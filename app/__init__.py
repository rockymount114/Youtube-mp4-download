import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
from .models import db, User

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
    
    # MSSQL Connection String
    # Format: mssql+pyodbc://username:password@server:port/database?driver=ODBC+Driver+17+for+SQL+Server
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, '..', 'uploads', 'audio')
    app.config['POLLING_INTERVAL'] = int(os.getenv('POLLING_INTERVAL', 10))

    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from .blueprints.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .blueprints.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .blueprints.users import users as users_blueprint
    app.register_blueprint(users_blueprint)

    return app
