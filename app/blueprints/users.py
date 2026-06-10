from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from ..models import User, db
from functools import wraps

users = Blueprint('users', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin privileges required.')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@users.route('/manage_users')
@login_required
@admin_required
def manage_users():
    all_users = User.query.all()
    return render_template('manage_users.html', users=all_users)

@users.route('/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    is_admin = True if request.form.get('is_admin') else False
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists.')
    else:
        new_user = User(
            username=username,
            password=generate_password_hash(password, method='scrypt'),
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully.')
        
    return redirect(url_for('users.manage_users'))

@users.route('/reset_password/<int:id>', methods=['POST'])
@login_required
@admin_required
def reset_password(id):
    user = User.query.get_or_404(id)
    new_password = request.form.get('new_password')
    
    user.password = generate_password_hash(new_password, method='scrypt')
    db.session.commit()
    flash(f'Password reset for {user.username}.')
    
    return redirect(url_for('users.manage_users'))

@users.route('/delete_user/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    if current_user.id == id:
        flash('You cannot delete yourself.')
    else:
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} deleted.')
        
    return redirect(url_for('users.manage_users'))

@users.route('/toggle_admin/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(id):
    if current_user.id == id:
        flash('You cannot change your own admin status.')
    else:
        user = User.query.get_or_404(id)
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'Admin status updated for {user.username}.')
        
    return redirect(url_for('users.manage_users'))
